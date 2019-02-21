from __future__ import absolute_import, unicode_literals

from celery import shared_task

from sklearn.feature_extraction.text import TfidfVectorizer
import os
import pickle
import scipy.sparse
import numpy as np

from .utils import pre_train_step, post_train_step
from ..models import Dataset, Answer, Question, QA

@shared_task
def run_tfidf(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 7)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        # get sents & build old_new_idx_map
        def get_sents_and_map(model_cls):
            values = model_cls.objects.filter(qa__dataset__id=dataset.id).values_list('idx', 'tokens')
            sent_tokens = []
            sent_map = {}
            for i, (idx, sent_token) in enumerate(values):
                sent_tokens.append(sent_token)
                sent_map[idx] = i

            return sent_tokens, sent_map

        q_tokens, q_map = get_sents_and_map(Question)
        a_tokens, a_map = get_sents_and_map(Answer)
        tokens = q_tokens + a_tokens

        result_dir = os.path.join(dataset.result_dir, 'tfidf')
        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)

        tfidf = TfidfVectorizer()
        tfidf.fit(tokens)
        with open(os.path.join(result_dir, 'tfidf.pkl'), 'wb') as fwrite:
            pickle.dump(tfidf, fwrite)

        q_X = tfidf.transform(q_tokens)
        a_X = tfidf.transform(a_tokens)

        scipy.sparse.save_npz(os.path.join(result_dir, 'q_X.npz'), q_X)
        scipy.sparse.save_npz(os.path.join(result_dir, 'a_X.npz'), a_X)

        # reindex to tfidf
        for old_idx, new_idx in q_map.items():
            question = Question.objects.get(qa__dataset__id=dataset.id, idx=old_idx)
            question.idx = new_idx
            question.save()

        for old_idx, new_idx in a_map.items():
            answer = Answer.objects.get(qa__dataset__id=dataset.id, idx=old_idx)
            answer.idx = new_idx
            answer.save()

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 8, logger)
    return dataset.id
