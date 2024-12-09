# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

# Get user model
User = get_user_model()

class ProcedureType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.DurationField(help_text="Expected duration of the procedure")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Procedure(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='procedures', null=True, blank=True)
    procedure_type = models.ForeignKey(ProcedureType, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_procedures')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            procedure_name = self.procedure_type.name if self.procedure_type else "Unknown Procedure"
            patient_name = self.user.get_full_name() if self.user else "Unknown Patient"
            date_str = self.scheduled_date.strftime("%Y-%m-%d %H:%M") if self.scheduled_date else "Unscheduled"
            
            return f"{procedure_name} for {patient_name} on {date_str}"
        except Exception:
            return f"Procedure #{self.id if hasattr(self, 'id') else 'New'}"
        
class ConsentForm(models.Model):
    procedure = models.OneToOneField(Procedure, on_delete=models.CASCADE, related_name='consent_form')
    signed_by_patient = models.BooleanField(default=False)
    signed_date = models.DateTimeField(null=True, blank=True)
    form_file = models.FileField(upload_to='consent_forms/')
    additional_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Consent Form for {self.procedure}"

class ProcedureResult(models.Model):
    procedure = models.OneToOneField(Procedure, on_delete=models.CASCADE, related_name='result')
    result_summary = models.TextField()
    complications = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Result for {self.procedure}"

class ProcedureImage(models.Model):
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='procedure_images/')
    caption = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.procedure} - {self.caption}"