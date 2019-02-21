from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .utils import pre_train_step, post_train_step

import os
from functools import partial
import pandas as pd

from ..models import Dataset
from ..train_utils.split import split_series
from ..train_utils.preprocess import Preprocessor, cleanse_white_space, cleanse_incomplete_syll, \
    partial_cleanse_nickname, tokenize_kmat
from ..constants import SPLIT, KMAT_DIR


@shared_task
def build_preprocessor(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 1)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        # split dataset
        df = pd.read_excel(dataset.original_file.path)

        q_df = split_series(df['Question'][df['Question'].map(lambda x: isinstance(x, str))], SPLIT[dataset.q_split])
        a_df = split_series(df['Answer'][df['Answer'].map(lambda x: isinstance(x, str))], SPLIT[dataset.a_split])

        sents = q_df['sent'].append(a_df['sent'])

        # set cleanse functions
        cleanse_functs = [cleanse_white_space]

        if dataset.removed_incomplete_sylls:
            cleanse_functs.append(cleanse_incomplete_syll)

        if dataset.removed_nicknames:
            cleanse_nickname = partial_cleanse_nickname(sents, dataset.removed_nicknames_keywords.split(','), 5)
            cleanse_functs.append(cleanse_nickname)

        # set toknization function
        tokenize_funct = partial(tokenize_kmat, kmat_dir=KMAT_DIR, tag_filter=dataset.selected_poses.split(','))

        preprocessor = Preprocessor(cleanse_functs, tokenize_funct)
        preprocessor.phrase(sents)

        preprocessor.save(os.path.join(dataset.result_dir, 'preprocessor.pkl'))

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 2, logger)
    return dataset.id
