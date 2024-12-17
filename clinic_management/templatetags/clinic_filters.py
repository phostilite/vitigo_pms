from django import template
from datetime import timedelta
from django.utils.dateparse import parse_date

register = template.Library()

@register.filter
def divideby(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
    
@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key in template"""
    if not dictionary:
        return []
    return dictionary.get(key, [])

@register.filter
def date_offset(value, days):
    """Add days to a date string"""
    date = parse_date(value) if isinstance(value, str) else value
    return (date + timedelta(days=int(days))).strftime('%Y-%m-%d')

@register.filter
def abs_value(value):
    """Return absolute value"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0