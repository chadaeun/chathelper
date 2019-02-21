from __future__ import absolute_import, unicode_literals

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from celery import shared_task

import os
import scipy.sparse
import pickle
import numpy as np
import threading

from ..constants import COALA_DIR

from ..train_utils.preprocess import Preprocessor
from ..models import Dataset, Answer


class ChatbotService:
    def __init__(self, dataset):
        self.dataset = dataset
        self.result_dir = dataset.result_dir
        self.load_preprocessor()
        self.load_tfidf()
        self.load_coala()

    def load_preprocessor(self):
        self.preprocessor = Preprocessor.load(os.path.join(self.result_dir, 'preprocessor.pkl'))

    def load_tfidf(self):
        tfidf_dir = os.path.join(self.result_dir, 'tfidf')
        self.a_X = scipy.sparse.load_npz(os.path.join(tfidf_dir, 'a_X.npz')).toarray()
        self.q_X = scipy.sparse.load_npz(os.path.join(tfidf_dir, 'q_X.npz')).toarray()
        self.tfidf_qa_mat = np.matmul(self.q_X, self.a_X.T)

        with open(os.path.join(tfidf_dir, 'tfidf.pkl'), 'rb') as fread:
            self.tfidf = pickle.load(fread)

    def load_coala(self):
        command = ['sudo', 'docker', 'run', '--rm', '-i', '-a', 'stdin', '-a', 'stdout', '-a', 'stderr',
                   '-v', '%s:/coala' % os.path.abspath(COALA_DIR),
                   '-v', '%s:/data' % os.path.abspath(os.path.join(self.dataset.result_dir, 'coala')), 'coala:latest',
                   'python /coala/run_service.py /data/configs/selected_config.yaml']

        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.proc = proc

    def get_answers(self, sentence):
        a_idxes = self.select_answer(sentence)

        results = []

        for a_idx in a_idxes:
            answer = Answer.objects.get(qa__dataset__id=self.dataset.id, idx=a_idx)
            result = {
                'qa_id': answer.qa.id,
                'answer': answer.answer,
                'date': answer.qa.date.strftime('%Y.%m.%d'),
            }

            results.append(result)

        return results

    def select_answer(self, sentence):
        tokens, tokens_all = self.preprocessor.tokenize(sentence, all_tokens=True)
        sorted_q_idxes = self.tfidf_filter(tokens)
        selected_a_idxes = self.coala_select(tokens_all, sorted_q_idxes)
        return selected_a_idxes

    def tfidf_filter(self, tokens):
        X = self.tfidf.transform([' '.join(tokens)]).toarray()
        matmul_result = np.matmul(self.q_X, X.T).flatten()
        sorted_q_idxes = np.argsort(-matmul_result)
        return sorted_q_idxes

    def coala_select(self, tokens_all, sorted_q_idxes):
        n_cand = 50

        if self.proc.returncode is not None:
            raise NotImplementedError('Docker closed')

        self.proc.stdin.write(('START QUERY\n').encode('utf-8'))
        self.proc.stdin.write((' '.join(tokens_all) + '\n').encode('utf-8'))
        self.proc.stdin.write((str(n_cand) + '\n').encode('utf-8'))
        self.proc.stdin.flush()

        answer_idx_map = []
        for q_idx in sorted_q_idxes:
            answers = Answer.objects.filter(qa__dataset__id=self.dataset.id, qa__question__idx=q_idx).values_list('idx', 'tokens_all')
            for a_idx, a_tokens_all in answers:
                if self.tfidf_qa_mat[q_idx, a_idx] > 0.2:
                    self.proc.stdin.write((' '.join(a_tokens_all) + '\n').encode('utf-8'))
                    self.proc.stdin.flush()
                    answer_idx_map.append(a_idx)

                    if len(answer_idx_map) >= n_cand:
                        break

            if len(answer_idx_map) >= n_cand:
                break

        selected_a_idxes = [answer_idx_map[int(idx)] for idx in self.proc.stdout.readline().decode('utf-8').strip().split()]
        return selected_a_idxes


class ChatbotHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, handler_class, chatbot):
        super(ChatbotHTTPServer, self).__init__(server_address, handler_class)
        self._chatbot = chatbot

class ChatbotHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not isinstance(self.server, ChatbotHTTPServer):
            self.send_response(404)
            return

        if self.path == '/sent':
            self.do_post_sent()
        elif self.path == '/check':
            self.do_post_check()
        elif self.path == '/stop':
            self.do_post_stop()
        else:
            self.send_response(404)

    def do_post_sent(self):
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(data_string)
        sentence = data.strip()

        try:
            result = self.server._chatbot.get_answers(sentence)
            result = json.dumps(result)
        except Exception as e:
            self.send_response(404)
            raise e

        self.send_result(result)

    def do_post_check(self):
        response_msg = '%s 챗봇입니다. 무엇을 도와드릴까요?' % self.server._chatbot.dataset.name
        result = json.dumps({'response_msg': response_msg})
        self.send_result(result)

    def do_post_stop(self):
        try:
            result = json.dumps('stopping')
            self.send_result(result)
            self.server.shutdown()
            self.server.server_close()
            # thr = threading.Thread(target=self.server.shutdown)
            # thr.daemon = True
            # thr.start()
        except Exception as e:
            self.send_response(404)
            raise e

    def send_result(self, result):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(result.encode('utf-8'))
        self.wfile.flush()


@shared_task
def run_service_task(dataset_id):
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        chatbot = ChatbotService(dataset)
        server = ChatbotHTTPServer(('0.0.0.0', 32284), ChatbotHTTPRequestHandler, chatbot)
        server.serve_forever()
    except Exception as e:
        raise e
    finally:
        dataset.status_service = False
        dataset.save()
