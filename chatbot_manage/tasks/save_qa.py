from __future__ import absolute_import, unicode_literals

from celery import shared_task

from ..constants import SPLIT
from ..train_utils.preprocess import Preprocessor
from ..models import Question, Answer, QA, Dataset
from ..train_utils.split import split_series
from .utils import pre_train_step, post_train_step

import os
import pandas as pd
import numpy as np
import datetime


@shared_task
def save_qa(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 3)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        preprocessor = Preprocessor.load(os.path.join(dataset.result_dir, 'preprocessor.pkl'))

        # save original question answer pair
        df = pd.read_excel(dataset.original_file)
        df.replace('', np.nan, inplace=True)
        df.dropna(inplace=True)


        def save_qa_row(row):
            answer = preprocessor.cleanse(row['Answer'])
            question = preprocessor.cleanse(row['Question'])
            date = datetime.datetime.strptime(row['Date'], '%Y.%m.%d')

            qa = QA(original_answer=answer, original_question=question, dataset=dataset, date=date, idx=row.name)
            qa.save()

        df.apply(save_qa_row, axis=1)

        def save_sent_row(row, type='q'):
            sent = preprocessor.cleanse(row['sent'])
            tokens, tokens_all = preprocessor.tokenize(row['sent'], all_tokens=True)

            tokens = ' '.join(tokens)
            tokens_all = ' '.join(tokens_all)

            if sent.strip() and tokens.strip() and tokens_all.strip():
                if type == 'q':
                    question = Question(question=sent, qa=QA.objects.get(idx=int(row['qa_idx'])), idx=row.name, tokens=tokens,
                                        tokens_all=tokens_all)
                    question.save()

                else:
                    question = Answer(answer=sent, qa=QA.objects.get(idx=int(row['qa_idx'])), idx=row.name, tokens=tokens,
                                        tokens_all=tokens_all)
                    question.save()

        q_df = split_series(df['Question'], SPLIT[dataset.q_split])
        q_df.apply(lambda x: save_sent_row(x, type='q'), axis=1)

        a_df = split_series(df['Answer'], SPLIT[dataset.a_split])
        a_df.apply(lambda x: save_sent_row(x, type='a'), axis=1)

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 4, logger)
    return dataset.id
