from django.db import models
from django.utils.translation import ugettext_lazy as _


class QA(models.Model):
    """
    QA model. includes original qa data.
    """
    # id of qa. PRIMARY KEY
    id = models.AutoField(_('ID'), help_text=('ID of questoin-answer pair'), primary_key=True)

    # dataset. FOREIGN KEY
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE,
                                verbose_name=_('dataset'), help_text=_('Connected dataset'))

    # answer sentence.
    original_answer = models.TextField(_('answer'), help_text=_('Original answer text'))

    # question sentence.
    original_question = models.TextField(_('question'), help_text=_('Original question text'))

    # date.
    date = models.DateField(_('date'), help_text=_('Date created'), null=True)

    # idx in dataset.
    idx = models.IntegerField(_('index in dataset'), help_text=_('Index in dataset'))

    class Meta:
        unique_together = ('dataset', 'idx',)
