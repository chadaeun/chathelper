from __future__ import absolute_import, unicode_literals

import os
import logging

from ..models import Dataset


def pre_train_step(dataset_id, start_status):
    # get dataset
    dataset = Dataset.objects.get(pk=dataset_id)

    # set log file
    logger = logging.getLogger('training')
    if len(logger.handlers) == 0:
        logger.setLevel(logging.INFO)
        log_path = os.path.join(dataset.result_dir, 'log.txt')
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    logger.info('train_step: start_status %d' % start_status)

    # check enter or not
    if dataset.status_training > start_status:
        logger.info('jumped to next step: training status %d' % dataset.status_training)
        return None

    dataset.status_training = start_status
    dataset.save()

    return logger


def post_train_step(dataset_id, end_status, logger):
    dataset = Dataset.objects.get(pk=dataset_id)

    dataset.status_training = end_status
    dataset.save()

    logger.info('successfully completed step: training status %d' % dataset.status_training)


# Bellow decorator is not working in celery
# def train_step(start_status, end_status):
#     def decorate(func):
#         """
#         decorator for train_task's each step
#         update DB status_training, handle exceptions, write log file
#         :param func: shared_task used to train_task
#         """
#         def wrapper(*args, **kwargs):
#             dataset_id = args[0]
#
#             # get dataset
#             dataset = Dataset.objects.get(pk=dataset_id)
#
#             # set log file
#             logger = logging.getLogger('training')
#             logger.setLevel(logging.INFO)
#             log_path = os.path.join(dataset.result_dir, 'log.txt')
#             fh = logging.FileHandler(log_path)
#             fh.setLevel(logging.INFO)
#             logger.addHandler(fh)
#
#             logger.info('train_step: start_status %d, end_status %d' % (start_status, end_status))
#
#             # check enter or not
#             if dataset.status_training > start_status:
#                 logger.info('jumped to next step: training status %d' % dataset.status_training)
#                 return dataset.id
#
#             # run function
#             try:
#                 dataset.status_training = start_status
#                 dataset.save()
#
#                 func(dataset_id)
#
#                 dataset.status_training = end_status
#                 dataset.save()
#             except Exception as e:
#                 logger.exception(e)
#                 dataset.status = 2
#                 dataset.save()
#                 raise e
#
#             logging.info('successfully completed step: training status %d' % dataset.status_training)
#             return dataset.id
#         return wrapper
#     return decorate
