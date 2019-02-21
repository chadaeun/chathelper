from django.http import HttpResponseRedirect
from django.urls import path, include, resolve, reverse

from . import views

urlpatterns = [
    path('', views.dataset, name='manage-dataset'),
    path('create/', views.dataset_create, name='manage-dataset-create'),
    path('<int:dataset_id>/edit/', views.dataset_edit, name='manage-dataset-edit'),
    path('<int:dataset_id>/add_data/', views.dataset_add_data, name='manage-dataset-add-data'),
    path('<int:dataset_id>', views.dataset_detail, name='manage-dataset-detail'),
]
