from django.contrib import admin
from django.urls import resolve

from django.utils.translation import ugettext_lazy as _

from chatbot_manage import models

# Register your models here.

def get_has_permission(user):
    """
    Function for check permission.
    This is only for superuser now, but might be needed to be changed
    to allow multiple administrator
    :param user: request.user
    :return: has_permission
    """
    return user.is_superuser

VIEW_TITLE = {
    'chatbot_manage.views.index.index': _('Dashboard'),
    'chatbot_manage.views.dataset.dataset': _('Chatbot Management'),
    'chatbot_manage.views.dataset.dataset_create': _('Create Chatbot'),
    'chatbot_manage.views.dataset.dataset_edit': _('Edit Chatbot'),
    'chatbot_manage.views.dataset.dataset_detail': _('Chatbot Detail'),
}

# context_processor
def chatbot_manage_context_processor(request):
    app_name = request.resolver_match._func_path.split('.', maxsplit=1)[0]
    if app_name != 'chatbot_manage':
        return {}

    context_dict = {
        # header
        'site_header': _('ChatHelper - ChatBot Management'),
        'site_title': _('ChatBot Management'),
        # footer
        'github_url': 'https://github.com/',  # TODO add github public repo
        'email': 'chadaeun57@gmail.com',
        # authentication
        'has_permission': get_has_permission(request.user),
        'site_url': '/service',
    }

    title_key = resolve(request.path)._func_path
    if title_key in VIEW_TITLE:
        context_dict['title'] = VIEW_TITLE[title_key]

    return context_dict
