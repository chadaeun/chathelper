from django.forms import ModelForm

from ..models import QA


class QAForm(ModelForm):
    class Meta:
        model = QA
        fields = ['date', 'original_answer', 'original_question']