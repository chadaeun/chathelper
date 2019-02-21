from __future__ import absolute_import, unicode_literals

import summa
from celery import shared_task

from .utils import pre_train_step, post_train_step
from ..models import Dataset, Answer


@shared_task
def run_textrank(dataset_id):
    # pre
    logger = pre_train_step(dataset_id, 5)
    if not logger:
        return dataset_id

    # main
    dataset = Dataset.objects.get(pk=dataset_id)

    try:
        sents = Answer.objects.filter(qa__dataset__id=dataset.id).values_list('tokens')
        sents = [sent[0] for sent in sents]

        graph = summa.summarizer._build_graph(sents)
        summa.summarizer._set_graph_edge_weights(graph)
        summa.summarizer._remove_unreachable_nodes(graph)
        pagerank_scores = summa.summarizer._pagerank(graph)
        text_rank = [pagerank_scores.get(x, 0) for x in sents]

        threshold = max(text_rank) * 0.08
        delete_sents = Answer.objects.filter(idx__in=[i for i, score in enumerate(text_rank) if score < threshold])
        delete_sents.delete()

    except Exception as e:
        logger.exception(e)
        dataset.status = 2
        dataset.save()
        raise e

    # post
    post_train_step(dataset.id, 6, logger)
    return dataset.id
