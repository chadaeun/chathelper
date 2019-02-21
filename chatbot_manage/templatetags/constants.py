from django import template

from ..constants import DEFINED_SPLIT, DEFINED_STATUS, DEFINED_STATUS_DETAIL

register = template.Library()

@register.filter()
def to_split_str(value):
    return DEFINED_SPLIT[value][1]

@register.filter()
def to_status_str(value):
    return DEFINED_STATUS[value][1]

@register.filter()
def to_status_training_str(value):
    return DEFINED_STATUS_DETAIL[value][1]