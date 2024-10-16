from django.db import models
from django.conf import settings
from patient_management.models import Patient

class MobileDeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_tokens')
    device_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=[('IOS', 'iOS'), ('ANDROID', 'Android')])
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_type} Token"

class PatientEducationMaterial(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class MobileAppointmentRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='mobile_appointment_requests')
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment Request for {self.patient.user.get_full_name()} on {self.preferred_date}"

class PatientQuery(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='mobile_queries')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Query from {self.patient.user.get_full_name()}: {self.subject}"

class PatientQueryResponse(models.Model):
    query = models.ForeignKey(PatientQuery, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.query.subject} by {self.responder.get_full_name()}"

class MobileNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.get_full_name()}: {self.title}"