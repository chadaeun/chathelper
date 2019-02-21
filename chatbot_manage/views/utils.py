from collections import namedtuple

# struct for filter_spec in changelist-filter
FILTER_SPEC_STRUCT = namedtuple('filter_spec', ['title', 'choices'])
# struct for choice in changelist-filter
FILTER_CHOICES_STRUCT = namedtuple('filter_choices_struct', ['selected', 'query_string', 'display'])