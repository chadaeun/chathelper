import os
import pickle
import subprocess
import re
from copy import deepcopy
from functools import partial
from collections import OrderedDict, Counter

import konlpy.tag
from konlpy.tag import Kkma
from gensim.models.phrases import Phraser, Phrases

class Preprocessor:
    def __init__(self, cleanse_functs, tokenize_funct):
        """
        :param cleanse_functs: list of cleansing functions.
                                each function should return cleansed sentence as str type.
                                last output will be used as question or answer candidates.
        :param tokenize_funct: tokenization function.
                                should return tokens as list of str type.
                                output will be used to TF-IDF feature.
        """
        self.cleanse_functs = cleanse_functs
        self.tokenize_funct = tokenize_funct
        self.phraser = None

    def cleanse(self, sent):
        for funct in self.cleanse_functs:
            sent = funct(sent)
        return sent

    def tokenize(self, sent, phrase=True, *args, **kwargs):
        tokens = self.tokenize_funct(sent, *args, **kwargs)
        if phrase:
            if self.phraser:
                tokens = self.phraser[tokens]
            else:
                raise NotImplementedError('You should run phrase() or set self.phraser first')

        return tokens

    def preprocess(self, sent, phrase=True):
        return ' '.join(self.tokenize(self.cleanse(sent), phrase=phrase))

    def phrase(self, sents, **kwargs):
        tokens = [self.tokenize(sent, phrase=False) for sent in sents]
        self.phraser = Phraser(Phrases(tokens, **kwargs))

    def save(self, save_path):
        save_dict = {}

        cleanse_functs = self.cleanse_functs
        for i, funct in enumerate(cleanse_functs):
            if isinstance(funct, partial) and 'tagger' in funct.keywords:
                save_dict['cleanse_functs[%d].tagger_cls' % i] = type(funct.keywords['tagger']).__name__
                funct.keywords['tagger'] = None
        save_dict['cleanse_functs'] = cleanse_functs

        save_dict['tokenize_funct'] = self.tokenize_funct
        save_dict['phraser'] = self.phraser

        save_dir = os.path.split(save_path)[0]
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        with open(save_path, 'wb') as fwrite:
            pickle.dump(save_dict, fwrite)

        for i, funct in enumerate(cleanse_functs):
            if isinstance(funct, partial) and ('cleanse_functs[%d].tagger_cls' % i) in save_dict:
                funct.keywords['tagger'] = getattr(konlpy.tag, save_dict['cleanse_functs[%d].tagger_cls' % i])()

    @classmethod
    def load(cls, load_path):
        with open(load_path, 'rb') as fread:
            load_dict = pickle.load(fread)

        cleanse_functs = load_dict['cleanse_functs']
        for i, funct in enumerate(cleanse_functs):
            if isinstance(funct, partial) and ('cleanse_functs[%d].tagger_cls' % i) in load_dict:
                funct.keywords['tagger'] = getattr(konlpy.tag, load_dict['cleanse_functs[%d].tagger_cls' % i])()

        preprocessor = cls(cleanse_functs, load_dict['tokenize_funct'])
        preprocessor.phraser = load_dict['phraser']
        return preprocessor


# cleansing functions

def cleanse_white_space(sent):
    return re.sub(r'\s+', ' ', sent.strip())


def cleanse_incomplete_syll(sent):
    return re.sub(r'[\u3131-\u3163]', '', sent) # delete 'ㄱ'-'ㅣ'


def cleanse_nickname(sent, nickname_keywords, token_counter, tagger, min_cnt):
    # 기존 답변에서 닉네임 제거
    # Konlpy의 형태 분석기들과 kmat 비교 결과 '님'이 들어간 어절에 대한 형태 분석 결과가 가장 우수했던 꼬꼬마 형태 분석기 사용
    # '님'이 포함된 어절을 형태 분석하여 '님'이라고 단독으로 분석되는 형태소가 있거나 'UN' tag가 있을 경우 해당 어절 삭제
    # 위의 조건 충족할 때 앞 어절이 자주 등장하는 단어가 아닐 경우 앞 어절도 삭제 ('담당자님'은 보존하되 '홍길동님'은 삭제하기 위함)
    words = []

    for word in sent.split():
        result = tagger.pos(word)

        keep = True
        for morph, tag in result:
            if morph in nickname_keywords or tag == 'UN':
                keep = False
                break

        if keep:
            words.append(word)
        elif len(words) > 0 and token_counter[words[-1]] < min_cnt:
            del words[-1]

    return ' '.join(words)


def partial_cleanse_nickname(sents, nickname_keywords, min_cnt):
    """
    get partial function of cleanse_nickname
    :param sents: list of str. all sentences
    :param nickname_keywords: str. keyword for detecting nickname
    :param min_cnt: Counter. minimum occurrence of word to preserve when it is before nickname keyword
    :return: partial function
    """
    kkma = Kkma()
    tokens = [token for sent in sents for token, _ in kkma.pos(sent)]
    counter = Counter(tokens)
    return partial(cleanse_nickname, nickname_keywords=nickname_keywords,
                   token_counter=counter, tagger=kkma, min_cnt=min_cnt)

# tokenization functions

def get_mor_result_v2(sentence, kmat_dir):
    # korea univ morpheme analyzer
    # dict 에 두번 들어가는 경우.
    # 문장에 + 들어가는 경우도 처리해줘야 함.
    # 문장에 '' < 있는 경우도 처리해 줘야함.

    sentence = sentence.replace('\'', '`')

    try:
        m_command = "cd " +  kmat_dir + ";./kmat <<<\'" + sentence + "\' 2>/dev/null"
        with open(os.devnull, 'w') as devnull:
            result = subprocess.check_output(m_command.encode(encoding='cp949', errors='ignore'), shell=True,
                                            executable='/bin/bash', stderr=devnull)
    except:
        return None

    mor_name_lists = []
    mor_tags_lists = []
    mor_dict = OrderedDict()

    count = 0
    for each in result.decode(encoding='cp949', errors='ignore').split('\n'):
        if len(each) > 0:
            try:
                ori_text = each.split('\t')[0].replace('`', '\'')
                mor_texts = each.split('\t')[1].replace('`', '\'')
                mor_results = mor_texts.split('+')

                count += 1

                dict_key = ori_text
                if dict_key in mor_dict:
                    dict_key = dict_key + '||' + str(count)
                mor_dict[dict_key] = []
                for each_mor in mor_results:
                    try:
                        if not each_mor.strip():
                            del mor_dict[dict_key]
                            break

                        mor_name = each_mor.split('/')[0]
                        mor_tags = each_mor.split('/')[1]

                        if not mor_name or not mor_tags:
                            del mor_dict[dict_key]
                            break

                        mor_name_lists.append(mor_name)
                        mor_tags_lists.append(mor_tags)
                        each_mor_dict = {}
                        each_mor_dict[mor_name] = mor_tags

                        mor_dict[dict_key].append(each_mor_dict)
                    except Exception as e:
                        print(e)
                        print(each_mor)
            except:
                print(each)

    return mor_dict


def tokenize_kmat(sent, kmat_dir, tag_filter=None, all_tokens=False):
    mor_result = get_mor_result_v2(sent, kmat_dir)
    morphs = []
    filtered_morphs = []

    for morph_list in mor_result.values():
        for morph_result in morph_list:
            morph = list(morph_result.keys())[0]
            tag = list(morph_result.values())[0]

            morphs.append(morph)
            if tag_filter is None or tag in tag_filter:
                filtered_morphs.append(morph)

    if all_tokens:
        return filtered_morphs, morphs

    return filtered_morphs
