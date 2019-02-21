from django.db import models
from django.utils.translation import ugettext_lazy as _

from .qa import QA


class Answer(models.Model):
    """
    Answer model. includes cleansed answer data and its informations.
    """
    # id of answer. PRIMARY KEY
    id = models.AutoField(_('ID'), help_text=_('ID of answer'), primary_key=True)

    # answer sentence.
    answer = models.TextField(_('answer'), help_text=_('Answer sentence'))

    # qa id.
    qa = models.ForeignKey(QA, on_delete=models.CASCADE,
                              verbose_name=_('question-answer ID'), help_text=_('Original question-answer pair'))

    # idx (in dataset)
    idx = models.IntegerField(_('index'), help_text=_('Index of answer in result_dir'))

    # tokens.
    tokens = models.TextField(_('tokens'), help_text=_('Tokens'))

    # tokens_all.
    tokens_all = models.TextField(_('all tokens'), help_text=_('All tokens'))
