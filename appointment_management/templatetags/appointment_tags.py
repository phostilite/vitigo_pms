from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
