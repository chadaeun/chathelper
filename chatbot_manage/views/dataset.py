import os
import requests

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import FieldDoesNotExist
from django.db import DatabaseError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _

from ..tasks import train_task, run_service_task
from ..admin import get_has_permission
from ..models import Dataset
from ..forms import DatasetForm
from ..constants import POS_TO_DESC


@user_passes_test(lambda u: get_has_permission(u), login_url='/admin/login')
def dataset(request):
    context = {}

    # delete
    if request.method == 'POST':
        if 'action' in request.POST:
            if int(request.POST['action']) == 0:
                if '_selected_action' in request.POST:
                    selected = request.POST.getlist('_selected_action')
                    try:
                        Dataset.objects.filter(pk__in=selected).delete()
                    except DatabaseError:
                        messages.error(request, _('Delete action failed.'))
                    else:
                        messages.info(request, _('Successfully deleted selected datasets.'))

                else:
                    messages.warning(request, _('No dataset selected. Nothing changed.'))

    # results
    datasets = Dataset.objects.all()

    # search
    search_var = 'name'
    context['search_var'] = search_var

    if request.method == 'GET':
        if search_var in request.GET:
            query = request.GET[search_var]
            datasets = Dataset.objects.filter(name__contains=query)

            context['query'] = query
            context['show_result_count'] = True
            context['full_result_count'] = Dataset.objects.all().count()
            context['result_count'] = datasets.count()

    context['results'] = datasets.values()
    header_keys = ['name', 'date', 'status', 'status_training', 'status_service']
    result_headers = [Dataset._meta.get_field(k).verbose_name for k in header_keys]
    context['result_headers'] = result_headers

    return render(request, 'dataset.html', context)


@user_passes_test(lambda u: get_has_permission(u), login_url='/admin/login')
def dataset_create(request):
    if request.method == "POST":
        form = DatasetForm(request.POST, request.FILES)

        if form.is_valid():
            dataset_obj = form.save()
            dataset_obj.result_dir = os.path.split(dataset_obj.original_file.path)[0]
            dataset_obj.save()
            return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

        else:
            for field, msg_list in form.errors.items():
                for msg in msg_list:
                    try:
                        messages.warning(request, '%s: %s' % (Dataset._meta.get_field(field).verbose_name, msg))
                    except FieldDoesNotExist:
                        messages.warning(request, '%s' % msg)

                messages.warning(request, _('Please select your original dataset file again'))

            return render(request, 'dataset_create.html', {'form': form})

    else:
        return render(request, 'dataset_create.html', {'form': DatasetForm})


def dataset_add_data():
    pass


@user_passes_test(lambda u: get_has_permission(u), login_url='/admin/login')
def dataset_detail(request, dataset_id):
    context = {}

    dataset_obj = get_object_or_404(Dataset, pk=dataset_id)
    context['dataset'] = dataset_obj

    pos_list = dataset_obj.selected_poses.split()
    pos_list = [POS_TO_DESC[pos] for pos in pos_list]
    context['pos_list'] = pos_list

    if request.method == 'POST':
        if '_delete' in request.POST:  # delete
            dataset_obj.delete()
            return HttpResponseRedirect(reverse('manage-dataset'))

        elif '_train' in request.POST:
            if dataset_obj.status == 1:
                messages.error(request, _('Your chatbot is already traning now.'))
                return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

            if dataset_obj.status == 3:
                messages.error(request, _('Your chatbot has already traned now.'))
                return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

            dataset_obj.status = 1
            dataset_obj.save()

            train_task.delay(dataset_obj.id)
            messages.info(request, _('Your chatbot started to train successfully.'))
            return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id, )))

        elif '_service' in request.POST:
            if dataset_obj.status != 3:
                messages.error(request, _('You cannot run chatbot service with not trained chatbot.'))
                return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

            if Dataset.objects.filter(status_service=True).count() != 0:
                messages.error(request, _('There is running chatbot now. Please retry after stop it.'))
                return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

            dataset_obj.status_service = True
            dataset_obj.save()
            run_service_task.delay(dataset_obj.id)
            messages.info(request, _('Your chatbot started to service successfully.'))
            return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

        elif '_stop' in request.POST:
            try:
                requests.post('http://127.0.0.1:32284/stop')
            except Exception as e:
                messages.warning(request, _('Failed to send stop signal'))
                raise e
            else:
                messages.info(request, _('Successfully sended stop signal'))
                dataset_obj.status_service = False
                dataset_obj.save()

            return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

    form = DatasetForm(instance=dataset_obj)
    context['form'] = form

    return render(request, 'dataset_detail.html', context)


@user_passes_test(lambda u: get_has_permission(u), login_url='/admin/login')
def dataset_edit(request, dataset_id):
    dataset_obj = get_object_or_404(Dataset, pk=dataset_id)

    if dataset_obj.status != 0:
        return render(request, 'dataset_create.html',
                      {'dataset': dataset_obj, 'not_editable':True, 'form': DatasetForm(instance=dataset_obj)})

    if request.method == "POST":
        form = DatasetForm(request.POST, request.FILES, instance=dataset_obj)

        if form.is_valid():
            dataset_obj = form.save()
            dataset_obj.result_dir = os.path.split(dataset_obj.original_file.path)[0]
            dataset_obj.save()

            messages.info(request, _('Changes are saved successfully.'))
            return HttpResponseRedirect(reverse('manage-dataset-detail', args=(dataset_obj.id,)))

        else:
            for field, msg_list in form.errors.items():
                for msg in msg_list:
                    try:
                        messages.warning(request, '%s: %s' % (Dataset._meta.get_field(field).verbose_name, msg))
                    except FieldDoesNotExist:
                        messages.warning(request, '%s' % msg)

                messages.warning(request, _('Please select your original dataset file again'))

            return render(request, 'dataset_create.html', {'form': form})

    else:
        return render(request, 'dataset_create.html', {'form': DatasetForm(instance=dataset_obj)})
