from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='service-index'),
    path('<int:qa_id>', views.qa_detail, name='service-detail')
]