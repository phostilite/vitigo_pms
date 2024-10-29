from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from doctor_management.models import TreatmentMethodSpecialization, BodyAreaSpecialization
from doctor_management.models import DoctorProfile


class TimeSlotConfig(models.Model):
    """Configuration for clinic's standard time slots"""
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.start_time} - {self.end_time} ({self.duration} mins)"

    class Meta:
        ordering = ['start_time']

class DoctorTimeSlot(models.Model):
    """Available time slots for each doctor"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}"

    def clean(self):
        # Check if the time slot falls within doctor's availability
        day_of_week = self.date.weekday()
        availability = self.doctor.availability.filter(
            day_of_week=day_of_week,
            start_time__lte=self.start_time,
            end_time__gte=self.end_time,
            is_available=True
        ).exists()
        
        if not availability:
            raise ValidationError("Time slot is outside doctor's availability hours")



class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('CONSULTATION', 'Consultation'),
        ('FOLLOW_UP', 'Follow-up'),
        ('PROCEDURE', 'Procedure'),
        ('PHOTOTHERAPY', 'Phototherapy'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]

    PRIORITY_CHOICES = [
        ('A', 'High'),
        ('B', 'Medium'),
        ('C', 'Low'),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments',
                               limit_choices_to={'role': 'DOCTOR'})
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default='CONSULTATION')
    date = models.DateField()
    time_slot = models.ForeignKey(DoctorTimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='B')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Prevent scheduling appointments more than 30 days in advance
        if self.date > timezone.now().date() + timezone.timedelta(days=30):
            raise ValidationError("Appointments cannot be scheduled more than 30 days in advance.")

    def __str__(self):
        return f"Appointment for {self.patient} on {self.date} at {self.time_slot}"


class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_date = models.DateTimeField()
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder for {self.appointment} on {self.reminder_date}"


class CancellationReason(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='cancellation_reason')
    reason = models.TextField()
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    cancelled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cancellation reason for {self.appointment}"