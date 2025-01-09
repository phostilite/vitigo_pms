from django import template
from django.utils.html import format_html
from django.utils import timezone
from ..models import ComplianceSchedule

register = template.Library()

@register.filter
def format_schedule_status(status):
    status_classes = {
        'COMPLETED': 'bg-green-100 text-green-800',
        'MISSED': 'bg-red-100 text-red-800',
        'IN_PROGRESS': 'bg-blue-100 text-blue-800',
        'SCHEDULED': 'bg-yellow-100 text-yellow-800',
        'RESCHEDULED': 'bg-purple-100 text-purple-800',
        'CANCELLED': 'bg-gray-100 text-gray-800',
    }
    css_class = status_classes.get(status, 'bg-gray-100 text-gray-800')
    return format_html('<span class="px-2 py-1 text-xs rounded-full {}">{}</span>',
                      css_class, status.title())

@register.filter
def format_priority(priority):
    priority_classes = {
        'A': 'bg-red-100 text-red-800',
        'B': 'bg-yellow-100 text-yellow-800',
        'C': 'bg-blue-100 text-blue-800',
    }
    css_class = priority_classes.get(priority, 'bg-gray-100 text-gray-800')
    priority_display = dict(ComplianceSchedule.PRIORITY_CHOICES).get(priority, priority)
    return format_html('<span class="px-2 py-1 text-xs rounded-full {}">{}</span>',
                      css_class, priority_display)

@register.filter
def replace_underscore(value):
    return value.replace('_', ' ')
