import importlib

import os
import sys
import click
import numpy as np
import tensorflow as tf

from experiment.config import load_config
from experiment.run_util import setup_logger, sess_config
from experiment.qa.data.models import Token, TextItem


# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

def convert_input(tokens_all, vocab):
    # input convert
    tokens_all = [Token(token) for token in tokens_all if token in vocab]
    sent_ti = TextItem(' '.join(t.text for t in tokens_all), tokens_all)
    return sent_ti

@click.command()
@click.argument('config_file')
def run(config_file):
    """This program is the starting point for every experiment. It pulls together the configuration and all necessary
    experiment classes to load

    """
    config = load_config(config_file)
    config_global = config['global']

    # setup a logger
    logger = setup_logger(config['logger'], name='service')

    # we allow to set the random seed in the config file for reproducibility. However, when running on GPU, results
    # will still be nondeterministic (due to nondeterministic behavior of tensorflow)
    if 'random_seed' in config_global:
        seed = config_global['random_seed']
        logger.info('Using fixed random seed'.format(seed))
        np.random.seed(seed)
        tf.set_random_seed(seed)

    with tf.Session(config=sess_config) as sess:
        # We are now fetching all relevant modules. It is strictly required that these module contain a variable named
        # 'component' that points to a class which inherits from experiment.Data, experiment.Experiment,
        # experiment.Trainer or experiment.Evaluator
        data_module = config['data-module']
        model_module = config['model-module']

        # The modules are now dynamically loaded
        DataClass = importlib.import_module(data_module).component
        ModelClass = importlib.import_module(model_module).component

        # We then wire together all the modules and start training
        data = DataClass(config['data'], config_global, logger)
        model = ModelClass(config['model'], config_global, logger)

        # setup the data (validate, create generators, load data, or else)
        logger.info('Setting up the data')
        data.setup()
        # build the model (e.g. compile it)
        logger.info('Building the model')
        model.build(data, sess)

        # restore the model
        logger.info('Restoring the model')
        saver = tf.train.Saver()
        saver.restore(sess, tf.train.latest_checkpoint(config['training']['save_folder']))
        logger.info('Restored the model')

        # serve service
        while True:
            line = sys.stdin.readline().strip()
            if line == 'START QUERY':
                question = sys.stdin.readline()
                q_tokens = question.strip().split()
                question = convert_input(q_tokens, data.vocab_to_index)

                n_answer = int(sys.stdin.readline().strip())
                answers = []
                for _ in range(n_answer):
                    answer = sys.stdin.readline()
                    a_tokens = answer.strip().split()
                    answer = convert_input(a_tokens, data.vocab_to_index)
                    answers.append(answer)

                question = np.array([data.get_item_vector(question, 150) for _ in range(len(answers))])
                answers = np.array([data.get_item_vector(answer, 300) for answer in answers])

                # run model
                scores, = sess.run([model.predict], feed_dict={
                    model.input_question: question,
                    model.input_answer: answers,
                    model.dropout_keep_prob: 1.0,
                })

                selected = np.argsort(-scores)[:5]

                enablePrint()
                sys.stdout.write((' '.join([str(idx) for idx in selected]) + '\n'))
                sys.stdout.flush()
                blockPrint()


if __name__ == '__main__':
    blockPrint()
    run()
