from django.db import models
from django.conf import settings
from django.db.models import JSONField  # Use this instead of django.contrib.postgres.fields.JSONField


class Report(models.Model):
    REPORT_TYPES = [
        ('PATIENT', 'Patient Statistics'),
        ('FINANCIAL', 'Financial Summary'),
        ('APPOINTMENT', 'Appointment Analytics'),
        ('TREATMENT', 'Treatment Outcomes'),
        ('INVENTORY', 'Inventory Status'),
        ('HR', 'Human Resources'),
        ('CUSTOM', 'Custom Report'),
    ]

    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('ONE_TIME', 'One-time'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    query = models.TextField(help_text="SQL query or aggregation logic for the report")
    parameters = JSONField(default=dict, blank=True, help_text="JSON object of report parameters")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Fields for scheduled reports
    is_scheduled = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class ReportExecution(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='executions')
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('IN_PROGRESS', 'In Progress'),
    ])
    result_file = models.FileField(upload_to='report_results/', null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Execution of {self.report.name} at {self.executed_at}"


class Dashboard(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_dashboards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    WIDGET_TYPES = [
        ('CHART', 'Chart'),
        ('TABLE', 'Table'),
        ('METRIC', 'Metric'),
        ('CUSTOM', 'Custom'),
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    name = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    data_source = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    config = JSONField(default=dict, help_text="JSON configuration for the widget")
    position = models.PositiveIntegerField(help_text="Position of the widget in the dashboard")

    def __str__(self):
        return f"{self.name} in {self.dashboard.name}"


class AnalyticsLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    details = JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} at {self.timestamp}"