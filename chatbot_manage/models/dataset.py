import os
import shutil

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import rebus

from ..constants import DEFINED_SPLIT, DEFINED_STATUS, DEFINED_STATUS_DETAIL


def get_original_file_upload_to(instance, filename):
    return 'datasets/{year}_{month}_{day}_{name}/original_dataset{ext}'.format(
        year=instance.date.year,
        month=instance.date.month,
        day=instance.date.day,
        name=rebus.urlsafe_b64encode(instance.name).rstrip().decode('utf-8'),
        ext=os.path.splitext(filename)[-1],
    )

class Dataset(models.Model):
    """
    Dataset model. includes dataset building configurations.
    FOREIGN KEY of Filter, Question, and Answer.
    """
    # id of dataset. PRIMARY KEY
    id = models.AutoField(_('ID'), help_text=_('ID of dataset'), primary_key=True)

    # name of dataset
    name = models.CharField(_('name'), help_text=_('Name of dataset'), max_length=100, unique=True)

    # date created
    date = models.DateField(_('date'), help_text=_('Date created'), default=timezone.now)

    # # language of dataset  # English is not available now
    # lang = LanguageField(_('language'), help_text=_('Language of dataset\n("%(Korean)s" or "%(English)s")') % {'Korean': _('Korean'), 'English': _('English')},
    #                      choices=[("ko", _(u"Korean")), ("en", _(u"English")),])

    # path of original dataset excel file. NOT MODIFIABLE AFTER DATASET BUILDING
    original_file = models.FileField(_('original dataset file'), help_text=_('Original dataset file'),
                                     upload_to=get_original_file_upload_to)

    # question split regex pattern. NOT MODIFIABLE AFTER DATASET BUILDING
    q_split = models.IntegerField(_('question split regular expression pattern'), help_text=_('Regular expression pattern used to splitting question text'),
                                  default=0, choices=DEFINED_SPLIT)

    # answer split regex. NOT MODIFIABLE AFTER DATASET BUILDING
    a_split = models.IntegerField(_('answer split regular expression pattern'),
                                  help_text=_('Regular expression pattern used to splitting answer text'),
                                  default=2, choices=DEFINED_SPLIT)

    # cleanse incomplete syllables.
    removed_incomplete_sylls = models.BooleanField(_('removed incomplete syllables'), help_text=_('Whether incomplete syllables (eg. ㅠㅠ, ㅋㅋ) have been removed from dataset\n(Only available in Korean)'),
                                                   default=False)

    # cleanse nicknames.
    removed_nicknames = models.BooleanField(_('removed nicknames'), help_text=_('Whether nicknames have been removed from dataset\n(Only available in Korean)'),
                                            default=False)

    # nicknames keywords. comma seperated
    removed_nicknames_keywords = models.TextField(_('keywords for removing nicknames'), help_text=_('Comma seperated keywords for detecting and removing nicknames'),
                                                  max_length=1024, default='')

    # selected poses. comma seperated
    selected_poses = models.TextField(_('selected part of speeches'), help_text=_('Selected part of speeches'), max_length=1024)

    # result directory contains copy of original dataset file, dataset configs, preprocessor, tfidf
    result_dir = models.FilePathField(_('prepared dataset directory path'), help_text=_('Path of prepared dataset directory'),
                                      allow_files=False, allow_folders=True, unique=True, default=None, null=True)

    # status
    status = models.IntegerField(_('status'), help_text=_('Training status'), choices=DEFINED_STATUS, default=0)

    # status_trainig
    status_training = models.IntegerField(_('training status'), help_text=_('Detailed training status'), default=0,
                                          choices=DEFINED_STATUS_DETAIL)

    # status_service
    status_service = models.BooleanField(_('service status'), help_text=('Chatbot service status'), default=False)

    class Meta:
        verbose_name = 'chatbot'


@receiver(pre_delete, sender=Dataset)
def delete_result_dir(sender, instance, using, **kwargs):
    result_dir = instance.result_dir
    shutil.rmtree(result_dir, ignore_errors=True)
