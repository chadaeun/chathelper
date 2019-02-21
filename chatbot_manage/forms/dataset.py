import os

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.forms import ModelForm, MultipleChoiceField

from django.utils.translation import ugettext_lazy as _

import pandas as pd
from xlrd.biffh import XLRDError

from ..models import Dataset
from ..constants import TOKEN_POS


class DatasetForm(ModelForm):
    selected_poses = MultipleChoiceField(choices=TOKEN_POS['ko'], widget=FilteredSelectMultiple(is_stacked=False, verbose_name=_('POS')))

    def __init__(self, *args, **kwargs):
        super(DatasetForm, self).__init__(*args, **kwargs)

        self.fields['removed_nicknames_keywords'].required = False
        self.fields['date'].required = False
        self.fields['result_dir'].required = False
        self.fields['status'].required = False
        self.fields['status_training'].required = False

        self.fields['selected_poses'].label = _('Selected POS')

    def clean_original_file(self):
        original_file = self.cleaned_data['original_file']

        try:
            df = pd.read_excel(original_file, index_col=0)
        except FileNotFoundError:
            raise ValidationError(_('File not found'), code='invalid')
        except PermissionError:
            raise ValidationError(_('Permission denied'), code='invalid')
        except XLRDError:
            raise ValidationError(_('Wrong format - please upload excel file'), code='invalid')

        if len(df.columns) != 3 or df.columns[0] != 'Date' or df.columns[1] != 'Question' or df.columns[2] != 'Answer':
            raise ValidationError(_('Wrong format - please check header in your dataset'), code='invalid')

        if not len(df):
            raise ValidationError(_('Your dataset file is empty'), code='invalid')

        return original_file

    def clean_selected_poses(self):
        selected_poses = self.cleaned_data['selected_poses']
        pos_list = [key for key, value in TOKEN_POS['ko']]

        for pos in selected_poses:
            if pos not in pos_list:
                raise ValidationError(_('Wrong value - %(pos)s is not a valid POS'), params={'pos': pos})

        return ','.join(selected_poses)

    def clean_removed_nicknames_keywords(self):
        raw_value = self.cleaned_data['removed_nicknames_keywords']
        keywords = []

        for word in raw_value.split(','):
            keywords.append(word.strip())

        return ','.join(keywords)

    class Meta:
        model = Dataset
        exclude = []
