from django.db import models
from django.conf import settings
from patient_management.models import Patient, Medication
from django.contrib.auth import get_user_model

User = get_user_model()

class Consultation(models.Model):
    CONSULTATION_TYPE_CHOICES = [
        ('INITIAL', 'Initial Consultation'),
        ('FOLLOW_UP', 'Follow-up Consultation'),
        ('EMERGENCY', 'Emergency Consultation'),
        ('TELE', 'Tele-consultation'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations', limit_choices_to={'role': 'PATIENT'}, null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_consultations', limit_choices_to={'role': 'DOCTOR'})
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES)
    date_time = models.DateTimeField()
    chief_complaint = models.TextField()
    vitals = models.JSONField(null=True, blank=True)  # Store vitals as JSON
    notes = models.TextField()
    diagnosis = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            patient_name = self.patient.get_full_name() if self.patient else "Unknown Patient"
            date_str = self.date_time.date() if self.date_time else "Unscheduled Date"
            return f"Consultation for {patient_name} on {date_str}"
        except AttributeError:
            return f"Consultation #{self.id if hasattr(self, 'id') else 'New'}"

class Prescription(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField()

    def __str__(self):
        return f"{self.medication.name} for {self.consultation.patient.user.get_full_name()}"

class TreatmentInstruction(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='treatment_instruction')
    lifestyle_changes = models.TextField(blank=True)
    dietary_instructions = models.TextField(blank=True)
    skincare_routine = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Treatment Instructions for {self.consultation.patient.user.get_full_name()} on {self.consultation.date_time.date()}"

class ConsultationAttachment(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='consultation_attachments/')
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.consultation.patient.user.get_full_name()}'s consultation on {self.consultation.date_time.date()}"

class FollowUpPlan(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='follow_up_plan')
    follow_up_date = models.DateField()
    reason = models.TextField()
    tests_required = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Follow-up Plan for {self.consultation.patient.user.get_full_name()} on {self.follow_up_date}"