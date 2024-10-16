from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from patient_management.models import Patient

class PhototherapyType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PhototherapyProtocol(models.Model):
    phototherapy_type = models.ForeignKey(PhototherapyType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    initial_dose = models.FloatField(help_text="Initial dose in mJ/cm²")
    max_dose = models.FloatField(help_text="Maximum dose in mJ/cm²")
    increment_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                             help_text="Percentage to increase dose each session")
    frequency = models.CharField(max_length=50, help_text="e.g., '3 times per week'")
    duration_weeks = models.PositiveIntegerField(help_text="Recommended duration in weeks")

    def __str__(self):
        return f"{self.phototherapy_type.name} - {self.name}"

class PhototherapyPlan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='phototherapy_plans')
    protocol = models.ForeignKey(PhototherapyProtocol, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    current_dose = models.FloatField(help_text="Current dose in mJ/cm²")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Phototherapy Plan for {self.patient.user.get_full_name()} - {self.protocol.phototherapy_type.name}"

class PhototherapySession(models.Model):
    COMPLIANCE_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    plan = models.ForeignKey(PhototherapyPlan, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    actual_dose = models.FloatField(help_text="Actual dose administered in mJ/cm²")
    duration = models.PositiveIntegerField(help_text="Duration of session in seconds")
    compliance = models.CharField(max_length=20, choices=COMPLIANCE_CHOICES)
    side_effects = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    administered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Session for {self.plan.patient.user.get_full_name()} on {self.session_date}"

class PhototherapyDevice(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    phototherapy_type = models.ForeignKey(PhototherapyType, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.model} ({self.serial_number})"

class HomePhototherapyLog(models.Model):
    plan = models.ForeignKey(PhototherapyPlan, on_delete=models.CASCADE, related_name='home_logs')
    date = models.DateField()
    duration = models.PositiveIntegerField(help_text="Duration of session in seconds")
    notes = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Home Session for {self.plan.patient.user.get_full_name()} on {self.date}"