from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from chatbot_manage.models import QA
from chatbot_manage.forms import QAForm

# Create your views here.
def index(request):
    return render(request, 'service_index.html')

def qa_detail(request, qa_id):
    qa = get_object_or_404(QA, pk=qa_id)
    form = QAForm(instance=qa)
    return render(request, 'service_detail.html', context={'qa':qa, 'form':form})
