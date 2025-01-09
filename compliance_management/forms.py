from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import ComplianceSchedule, ComplianceIssue
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

class ComplianceIssueForm(forms.ModelForm):
    """Form for creating and updating compliance issues"""
    
    class Meta:
        model = ComplianceIssue
        fields = [
            'patient', 'title', 'description', 'severity', 
            'status', 'assigned_to', 'resolution'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'resolution': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'patient': 'Select the patient this issue relates to',
            'title': 'Brief title describing the issue',
            'description': 'Detailed description of the compliance issue',
            'severity': '''Severity levels:
                       - High: Immediate attention required
                       - Medium: Requires attention soon
                       - Low: Routine follow-up needed''',
            'status': '''Current state of the issue:
                     - Open: New issue
                     - In Progress: Being addressed
                     - Resolved: Issue has been resolved
                     - Closed: No further action needed''',
            'assigned_to': 'Staff member responsible for handling this issue',
            'resolution': 'Description of how the issue was resolved (required for Resolved/Closed status)'
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        resolution = cleaned_data.get('resolution')

        if status in ['RESOLVED', 'CLOSED'] and not resolution:
            raise ValidationError({
                'resolution': 'Resolution is required when marking an issue as resolved or closed'
            })

        return cleaned_data