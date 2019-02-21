from django.db import models
from django.utils.translation import ugettext_lazy as _

from .qa import QA


class Question(models.Model):
    """
    Question model. includes cleansed question data and its informations.
    """
    # id of question. PRIMARY KEY
    id = models.AutoField(_('ID'), help_text=_('ID of question'), primary_key=True)

    # question sentence.
    question = models.TextField(_('question'), help_text=_('Question sentence'))

    # qa_id
    qa = models.ForeignKey(QA, on_delete=models.CASCADE,
                              verbose_name=_('question-answer ID'), help_text=_('Original question-answer pair'))

    # idx (in dataset)
    idx = models.IntegerField(_('index'), help_text=_('Index of question in result_dir'))

    # tokens.
    tokens = models.TextField(_('tokens'), help_text=_('Tokens'))

    # tokens_all.
    tokens_all = models.TextField(_('all tokens'), help_text=_('All tokens'))
