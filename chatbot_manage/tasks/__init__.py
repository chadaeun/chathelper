from __future__ import absolute_import, unicode_literals

from celery import chain

from .preprocess import build_preprocessor
from .save_qa import save_qa
from .textrank import run_textrank
from .tfidf import run_tfidf
from .coala import prepare_coala, coala_random_search, coala_train

from .service import run_service_task

train_task = chain(
    build_preprocessor.s() | save_qa.s() | run_textrank.s() | run_tfidf.s() | prepare_coala.s() | coala_random_search.s() | coala_train.s()
)
