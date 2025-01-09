from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import ComplianceSchedule, ComplianceIssue, ComplianceMetric, ComplianceReminder, ComplianceAlert, ComplianceReport
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

class ComplianceMetricForm(forms.ModelForm):
    """Form for creating and updating compliance metrics"""
    
    class Meta:
        model = ComplianceMetric
        fields = [
            'patient', 'metric_type', 'compliance_score',
            'evaluation_period_start', 'evaluation_period_end',
            'notes'
        ]
        widgets = {
            'evaluation_period_start': forms.DateInput(attrs={'type': 'date'}),
            'evaluation_period_end': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'patient': 'Select the patient for this compliance metric',
            'metric_type': 'Type of compliance being measured',
            'compliance_score': 'Score between 0 and 100',
            'evaluation_period_start': 'Start date of evaluation period',
            'evaluation_period_end': 'End date of evaluation period',
            'notes': 'Additional notes about the evaluation'
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('evaluation_period_start')
        end = cleaned_data.get('evaluation_period_end')
        score = cleaned_data.get('compliance_score')

        if start and end and start > end:
            raise ValidationError({
                'evaluation_period_end': 'End date must be after start date'
            })

        if score and (score < 0 or score > 100):
            raise ValidationError({
                'compliance_score': 'Score must be between 0 and 100'
            })

        return cleaned_data

class ComplianceReminderForm(forms.ModelForm):
    """Form for creating and updating compliance reminders"""
    
    class Meta:
        model = ComplianceReminder
        fields = [
            'patient', 'reminder_type', 'scheduled_datetime',
            'message', 'status'
        ]
        widgets = {
            'scheduled_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'message': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'patient': 'Select the patient for this reminder',
            'reminder_type': '''Type of reminder:
                            - Medication: Medication intake reminders
                            - Appointment: Upcoming appointment reminders
                            - Follow-up: Follow-up call reminders
                            - Phototherapy: Session reminders
                            - General: Other general reminders''',
            'scheduled_datetime': 'When should this reminder be sent?',
            'message': 'The message content of the reminder',
            'status': '''Current status of the reminder:
                     - Pending: Not yet sent
                     - Sent: Successfully delivered
                     - Failed: Delivery failed
                     - Cancelled: Reminder cancelled'''
        }
        labels = {
            'patient': 'Patient Name',
            'reminder_type': 'Reminder Type',
            'scheduled_datetime': 'Schedule Date & Time',
            'message': 'Reminder Message',
            'status': 'Reminder Status'
        }

    def clean_scheduled_datetime(self):
        """Validate that scheduled datetime is not in the past"""
        scheduled_datetime = self.cleaned_data.get('scheduled_datetime')
        if scheduled_datetime and scheduled_datetime < timezone.now():
            raise ValidationError('Scheduled datetime cannot be in the past')
        return scheduled_datetime

    def clean(self):
        """Additional validation for the entire form"""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        scheduled_datetime = cleaned_data.get('scheduled_datetime')

        if status == 'SENT' and scheduled_datetime > timezone.now():
            raise ValidationError({
                'status': 'Cannot mark a future reminder as sent'
            })

        return cleaned_data

    def __init__(self, *args, **kwargs):
        """Initialize form with custom modifications"""
        super().__init__(*args, **kwargs)
        
        # Make some fields required
        self.fields['message'].required = True
        
        # Add CSS classes for styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

        # If this is an existing reminder, disable certain fields
        if self.instance and self.instance.pk:
            if self.instance.status == 'SENT':
                self.fields['scheduled_datetime'].disabled = True
                self.fields['message'].disabled = True

class ComplianceAlertForm(forms.ModelForm):
    """Form for creating and updating compliance alerts"""
    
    class Meta:
        model = ComplianceAlert
        fields = [
            'patient', 'alert_type', 'severity', 'message',
            'is_resolved', 'resolution_notes'
        ]
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'resolution_notes': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'patient': 'Select the patient this alert is for',
            'alert_type': '''Type of alert:
                         - Missed Appointment: Patient missed scheduled appointment
                         - Low Compliance: Compliance score below threshold
                         - Missed Medication: Medication adherence issue
                         - Follow-up Required: Patient needs follow-up
                         - Critical Issue: Urgent attention needed''',
            'severity': '''Urgency level:
                       - High: Immediate attention required
                       - Medium: Address within 24 hours
                       - Low: Handle during routine follow-up''',
            'message': 'Detailed description of the alert',
            'is_resolved': 'Mark if the alert has been addressed',
            'resolution_notes': 'Notes about how the alert was resolved'
        }
        labels = {
            'patient': 'Patient Name',
            'alert_type': 'Alert Type',
            'severity': 'Alert Severity',
            'message': 'Alert Message',
            'is_resolved': 'Resolved',
            'resolution_notes': 'Resolution Details'
        }

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        is_resolved = cleaned_data.get('is_resolved')
        resolution_notes = cleaned_data.get('resolution_notes')

        # If alert is marked as resolved, require resolution notes
        if is_resolved and not resolution_notes:
            raise ValidationError({
                'resolution_notes': 'Resolution notes are required when marking an alert as resolved'
            })

        return cleaned_data

    def __init__(self, *args, **kwargs):
        """Initialize form with custom modifications"""
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['message'].required = True
        
        # Add CSS classes for styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            
        # If this is an existing alert that's already resolved,
        # make certain fields read-only
        if self.instance and self.instance.pk and self.instance.is_resolved:
            self.fields['alert_type'].disabled = True
            self.fields['severity'].disabled = True
            self.fields['message'].disabled = True

class ComplianceReportForm(forms.ModelForm):
    """Form for creating and updating compliance reports"""
    
    class Meta:
        model = ComplianceReport
        fields = [
            'report_type', 'title', 'description', 'parameters',
            'period_start', 'period_end'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'parameters': forms.JSONField(),
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'report_type': '''Type of report:
                          - Individual: Single patient report
                          - Group: Multiple patients report
                          - Summary: Overall compliance summary
                          - Trend: Compliance trend analysis''',
            'title': 'Clear, descriptive title for the report',
            'description': 'Detailed description of report contents and purpose',
            'parameters': 'JSON parameters used to generate the report',
            'period_start': 'Start date for the reporting period',
            'period_end': 'End date for the reporting period'
        }
        labels = {
            'report_type': 'Report Type',
            'title': 'Report Title',
            'description': 'Report Description',
            'parameters': 'Report Parameters',
            'period_start': 'Period Start Date',
            'period_end': 'Period End Date'
        }

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')

        # Validate date range
        if period_start and period_end and period_start > period_end:
            raise ValidationError({
                'period_end': 'End date must be after start date'
            })

        # Validate parameters JSON
        parameters = cleaned_data.get('parameters')
        if parameters:
            try:
                if not isinstance(parameters, dict):
                    raise ValidationError({
                        'parameters': 'Parameters must be a valid JSON object'
                    })
            except Exception as e:
                raise ValidationError({
                    'parameters': f'Invalid JSON format: {str(e)}'
                })

        return cleaned_data

    def __init__(self, *args, **kwargs):
        """Initialize form with custom modifications"""
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['period_start'].required = True
        self.fields['period_end'].required = True
        
        # Add CSS classes for styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })