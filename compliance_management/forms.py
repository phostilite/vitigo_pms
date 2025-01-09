from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import ComplianceSchedule
from datetime import datetime
from django.utils import timezone

class ComplianceScheduleForm(forms.ModelForm):
    """Form for creating and updating compliance schedules"""
    
    class Meta:
        model = ComplianceSchedule
        fields = [
            'patient', 'assigned_to', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'priority', 'status', 'schedule_notes'
        ]
        help_texts = {
            'patient': 'Select the patient for this compliance schedule',
            'assigned_to': 'Choose the staff member responsible for this schedule',
            'scheduled_date': 'Select the date for the scheduled compliance activity',
            'scheduled_time': 'Specify the time for the scheduled activity (24-hour format)',
            'duration_minutes': 'Enter the expected duration in minutes (minimum 15 minutes)',
            'priority': '''Priority levels:
                         - A (High): Immediate attention required
                         - B (Medium): Standard priority
                         - C (Low): Routine follow-up''',
            'status': '''Current state of the schedule:
                     - Scheduled: Upcoming appointment
                     - In Progress: Currently ongoing
                     - Completed: Successfully finished
                     - Missed: Patient did not attend
                     - Rescheduled: Moved to new date/time
                     - Cancelled: No longer happening''',
            'schedule_notes': 'Add any relevant notes, special instructions, or requirements'
        }
        labels = {
            'patient': 'Patient Name',
            'assigned_to': 'Assigned Staff Member',
            'scheduled_date': 'Schedule Date',
            'scheduled_time': 'Schedule Time',
            'duration_minutes': 'Duration (minutes)',
            'priority': 'Priority Level',
            'status': 'Schedule Status',
            'schedule_notes': 'Additional Notes'
        }