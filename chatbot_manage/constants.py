from django.utils.translation import ugettext_lazy as _


KMAT_DIR = 'chatbot_manage/kmat/bin'
COALA_DIR = 'chatbot_manage/coala'

TOKEN_POS = {
    # spacy pos for English: see spacy.lang.en.tag_map.TAG_MAP
    'en': [
        ('-LRB-', _('left round bracket')),
        ('-RRB-', _('right round bracket')),
        (',', _('punctuation mark, comma')),
        (':', _('punctuation mark, colon or ellipsis')),
        ('.', _('punctuation mark, sentence closer')),
        ('\'\'', _('closing quotation mark')),
        ('""', _('closing quotation mark')),
        ('#', _('symbol, number sign')),
        ('``', _('opening quotation mark')),
        ('$', _('symbol, currency')),
        ('ADD', _('email')),
        ('AFX', _('affix')),
        ('BES', _('auxiliary "be"')),
        ('CC', _('conjunction, coordinating')),
        ('CD', _('cardinal number')),
        ('DT', _('determiner')),
        ('EX', _('existential there')),
        ('FW', _('foreign word')),
        ('GW', _('additional word in multi-word expression')),
        ('HVS', _('forms of "have"')),
        ('HYPH', _('punctuation mark, hyphen')),
        ('IN', _('conjunction, subordinating or preposition')),
        ('JJ', _('adjective')),
        ('JJR', _('adjective, comparative')),
        ('JJS', _('adjective, superlative')),
        ('LS', _('list item marker')),
        ('MD', _('verb, modal auxiliary')),
        ('NFP', _('superfluous punctuation')),
        ('NIL', _('missing tag')),
        ('NN', _('noun, singular or mass')),
        ('NNP', _('noun, proper singular')),
        ('NNPS', _('noun, proper plural')),
        ('NNS', _('noun, plural')),
        ('PDT', _('predeterminer')),
        ('POS', _('possessive ending')),
        ('PRP', _('pronoun, personal')),
        ('PRP$', _('pronoun, possessive')),
        ('RB', _('adverb')),
        ('RBR', _('adverb, comparative')),
        ('RBS', _('adverb, superlative')),
        ('RP', _('adverb, particle')),
        ('_SP', _('space')),
        ('SYM', _('symbol')),
        ('TO', _('infinitival to')),
        ('UH', _('interjection')),
        ('VB', _('verb, base form')),
        ('VBD', _('verb, past tense')),
        ('VBG', _('verb, gerund or present participle')),
        ('VBN', _('verb, past participle')),
        ('VBP', _('verb, non-3rd person singular present')),
        ('VBZ', _('verb, 3rd person singular present')),
        ('WDT', _('wh-determiner')),
        ('WP', _('wh-pronoun, personal')),
        ('WP$', _('wh-pronoun, possessive')),
        ('WRB', _('wh-adverb')),
        ('XX', _('unknown')),
    ],
    # kmat pos for Korean
    'ko': [
        ('EM', _('어말 어미')),
         ('EP', _('선어말 어미')),
         ('ETM', _('관형형 전성 어미')),
         ('IC', _('감탄사')),
         ('JKB', _('부사격 조사')),
         ('JKG', _('관형격 조사')),
         ('JKO', _('목적격 조사')),
         ('JKQ', _('인용격 조사')),
         ('JKS', _('주격 조사')),
         ('JX', _('보조사')),
         ('MAG', _('일반 부사')),
         ('MAJ', _('접속 부사')),
         ('MM', _('관형사')),
         ('NA', _('분석불능범주')),
         ('NNB', _('의존 명사')),
         ('NNG', _('일반 명사')),
         ('NNP', _('고유 명사')),
         ('NP', _('대명사')),
         ('NR', _('수사')),
         ('SE', _('줄임표')),
         ('SF', _('마침표,물음표,느낌표')),
         ('SH', _('한자')),
         ('SL', _('외국어')),
         ('SN', _('숫자')),
         ('SO', _('붙임표(물결,숨김,빠짐)')),
         ('SP', _('쉼표,가운뎃점,콜론,빗금')),
         ('SS', _('따옴표,괄호표,줄표')),
         ('SW', _('기타기호 (논리수학기호,화폐기호)')),
         ('VA', _('형용사')),
         ('VCP', _('긍정 지정사 (서술격 조사 \'이다\')')),
         ('VV', _('동사')),
         ('VX', _('보조 용언')),
         ('XPN', _('체언 접두사')),
         ('XSA', _('형용사 파생 접미사')),
         ('XSN', _('명사 파생 접미사')),
         ('XSV', _('동사 파생 접미사')),
    ]
}

POS_TO_DESC = {pos:desc for pos, desc in TOKEN_POS['ko']}

SPLIT = ['[.!?]+', '\n+', '\n{2,}']

DEFINED_SPLIT = [
    (0, _('Sentence')),
    (1, _('Line break')),
    (2, _('Paragraph')),
]

DEFINED_STATUS = [
    (0, _('Not trained yet')),
    (1, _('Training')),
    (2, _('Training Failed - see log.txt in result directory')),
    (3, _('Trained')),
]

STATUS_DETAIL = [
    'Pending',
    'Building Preprocessor',
    'Built Preprocessor; Before Saving data to DB',
    'Saving data to DB',
    'Saved data to DB; Before running TextRank',
    'Running TextRank',
    'Ran TextRank; Before running TF-IDF',
    'Running TF-IDF',
    'Ran TF-IDF; Before preparing COALA',
    'Preparing COALA',
    'Prepared COALA; Before random searching COALA',
    'Random searching COALA',
    'Done random searching; before training COALA',
    'Training COALA',
    'Traninig Complete'
]

DEFINED_STATUS_DETAIL = [(i, _(desc),) for i, desc in enumerate(STATUS_DETAIL)]
