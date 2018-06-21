from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def once_twice_xtimes(value):
    if value == '1':
        return 'once'
    elif value == '2':
        return 'twice'
    elif value == '3':
        return 'three times'
    elif value == '4':
        return 'four times'
    elif value == '5':
        return 'five times'
    elif value == '6':
        return 'six times'
    elif value == '7':
        return 'seven times'
    elif value == '8':
        return 'eight times'
    elif value == '9':
        return 'nine times'
    else:
        return value + ' times'