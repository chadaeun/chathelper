from __future__ import absolute_import, unicode_literals

import shutil

import yaml
from celery import shared_task

import os
import scipy.sparse
import numpy as np
import gzip
import subprocess
import re

from .utils import pre_train_step, post_train_step
from ..models import Dataset, Answer, Question
from ..constants import COALA_DIR

@shared_task
def prepare_coala(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 9)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        result_dir = os.path.join(dataset.result_dir, 'coala')

        data_dir = os.path.join(result_dir, 'data')
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        config_dir = os.path.join(result_dir, 'configs')
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)

        # read & copy vocab
        vocab = {}
        vocab_path = os.path.join(COALA_DIR, 'glove/vocab.tsv.gz')
        with gzip.open(vocab_path) as fread:
            for line in fread:
                idx, word = line.decode('utf-8').strip().split()
                idx = int(idx[4:])
                vocab[word] = idx

        shutil.copy(vocab_path, os.path.join(data_dir, 'vocab.tsv.gz'))

        # write answer
        answers = Answer.objects.filter(qa__dataset__id=dataset.id).values_list('idx', 'tokens_all')
        with gzip.open(os.path.join(data_dir, 'answers.tsv.gz'), 'wb') as fwrite:
            for i, sent in answers:
                words = ' '.join(['idx_%d' % vocab[word] for word in sent.split() if word in vocab])
                if len(words.strip()):
                    fwrite.write(('%d\t%s\n' % (i, words)).encode('utf-8'))

        # write question
        questions = Question.objects.filter(qa__dataset__id=dataset.id).values_list('idx', 'tokens_all')
        with gzip.open(os.path.join(data_dir, 'questions.tsv.gz'), 'wb') as fwrite:
            for i, sent in questions:
                words = ' '.join(['idx_%d' % vocab[word] for word in sent.split() if word in vocab])
                if len(words.strip()):
                    fwrite.write(('%d\t%s\n' % (i, words)).encode('utf-8'))

        # write train & validation
        q_X = scipy.sparse.load_npz(os.path.join(dataset.result_dir, 'tfidf', 'q_X.npz'))
        a_X = scipy.sparse.load_npz(os.path.join(dataset.result_dir, 'tfidf', 'a_X.npz'))
        tfidf_qa_mat = np.matmul(q_X.toarray(), a_X.toarray().T)
        tfidf_qq_mat = np.matmul(q_X.toarray(), q_X.toarray().T)
        threshold = 0.2

        def write_coala_dataset(q_idx_list, dst_path):
            with gzip.open(dst_path, 'wb') as fwrite:
                for q_idx in q_idx_list:
                    gt_a_list = Answer.objects.filter(qa__dataset__id=dataset.id, qa__question__idx=q_idx).values_list('idx')
                    ground_truth = [a_idx for a_idx, in gt_a_list if tfidf_qa_mat[q_idx, a_idx] > 0.2]
                    if len(ground_truth) == 0:
                        continue
                    ground_truth = ' '.join([str(gt) for gt in ground_truth])

                    pool = []
                    for pool_q in np.argsort(-tfidf_qq_mat[q_idx]):
                        pool_a_list = Answer.objects.filter(qa__dataset__id=dataset.id, qa__question__idx=pool_q).values_list('idx')
                        pool += [pool_a for pool_a, in pool_a_list if tfidf_qa_mat[pool_q, pool_a] > 0.2]
                        if len(pool) > 50:
                            break

                    pool = ' '.join([str(p) for p in pool][:50])

                    fwrite.write(('%d\t%s\t%s\n' % (q_idx, ground_truth, pool)).encode('utf-8'))

        q_idxs = Question.objects.filter(qa__dataset__id=dataset.id).values_list('idx')
        len_q = len(q_idxs)
        n_train = int(len_q * 0.8)
        n_valid = int(len_q * 0.1)
        shuffle_ids = np.array([q[0] for q in q_idxs])
        np.random.shuffle(shuffle_ids)

        train_q_ids = shuffle_ids[:n_train]
        valid_q_ids = shuffle_ids[n_train:n_train+n_valid]
        test_q_ids = shuffle_ids[n_train+n_valid:]

        write_coala_dataset(train_q_ids, os.path.join(data_dir, 'train.tsv.gz'))
        write_coala_dataset(valid_q_ids, os.path.join(data_dir, 'valid.tsv.gz'))
        write_coala_dataset(test_q_ids, os.path.join(data_dir, 'test.tsv.gz'))

        # write config
        with open(os.path.join(COALA_DIR, 'configs/example_random_search.yaml')) as fread:
            config = yaml.load(fread)
            config['logger']['path'] = os.path.join('/data', config['logger']['path'])
            config['data']['train_data'] = ['/data/data']
            config['data']['embeddings_path'] = '/coala/glove/glove.840B.300d.txt'
            config['training']['save_folder'] = os.path.join('/data', config['training']['save_folder'])
            config['random_search']['output_path'] = os.path.join('/data', config['random_search']['output_path'])

        with open(os.path.join(config_dir, 'random_search.yaml'), 'w') as fwrite:
            yaml.dump(config, fwrite)

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 10, logger)
    return dataset.id


@shared_task
def coala_random_search(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 11)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        command = ['sudo', 'nvidia-docker', 'run', '--rm', '-v', '%s:/coala' % os.path.abspath(COALA_DIR),
                   '-v', '%s:/data' % os.path.abspath(os.path.join(dataset.result_dir, 'coala')), 'coala:latest',
                   'python /coala/run_random_search.py /data/configs/random_search.yaml']
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            line = proc.stderr.readline().decode('utf-8')
            if line:
                logger.info('[Log from subprocess] ' + line)

            with open(os.path.join(dataset.result_dir, '<path-to-log-output.txt>')) as fread:
                fread.seek(1024, os.SEEK_END)

                if 'Now stopping' in line:
                    logger.info('[Log from subprocess] ' + line)

                    for _ in range(2):
                        logger.info('[Log from subprocess] ' + proc.stderr.readline().decode('utf-8'))

                    proc.terminate()
                    break

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 12, logger)
    return dataset.id


@shared_task
def coala_train(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 13)
    if not logger:
        # train ended
        dataset = Dataset.objects.get(pk=dataset_id)
        dataset.status = 3
        dataset.save()
        return dataset_id

    dataset = Dataset.objects.get(pk=dataset_id)

    # main
    try:
        result_dir = os.path.join(dataset.result_dir, 'coala')
        config_path = os.path.join(result_dir, 'configs', 'selected_config.yaml')

        if not os.path.isfile(config_path):
            id = -1
            with open(os.path.join(result_dir, '<path-to-log-output.txt>')) as fread:

                for line in fread:
                    start_idx = line.find('Best run')
                    if start_idx != -1:
                        msg = line[start_idx:].strip()
                        pattern = re.compile('Best run: id=(\d+) with score .+?')
                        id = int(pattern.match(msg)[1])
                        break

            if id == -1:
                raise NotImplementedError('Cannot find best run id from COALA random search log')

            shutil.copy(os.path.join(result_dir, '<random-search-log-path>', 'run-%d.yaml' % id), config_path)

        command = ['sudo', 'nvidia-docker', 'run', '--rm', '-v', '%s:/coala' % os.path.abspath(COALA_DIR),
                   '-v', '%s:/data' % os.path.abspath(os.path.join(dataset.result_dir, 'coala')), 'coala:latest',
                   'python /coala/run_experiment.py /data/configs/selected_config.yaml']
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()

        while True:
            line = proc.stderr.readline().decode('utf-8')
            if line:
                logger.info('[Log from subprocess] ' + line)

            with open(os.path.join(dataset.result_dir, '<path-to-log-output.txt>')) as fread:
                fread.seek(1024, os.SEEK_END)

                if 'Done' in line:
                    logger.info('[Log from subprocess] ' + line)

                    proc.terminate()
                    break

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset_id, 12, logger)

    # train ended
    dataset.status=3
    dataset.save()
    return dataset.id
