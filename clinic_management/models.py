# Standard library imports
import logging
from datetime import timedelta

# Django imports
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

# Get the user model and setup logging
User = get_user_model()
logger = logging.getLogger(__name__)

class ClinicArea(models.Model):
    """Different areas/departments within the clinic"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(help_text="Maximum number of patients that can be accommodated")
    requires_doctor = models.BooleanField(default=False)
    requires_appointment = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['code', 'is_active'])]

class ClinicStation(models.Model):
    """Individual stations within clinic areas (e.g., consultation rooms, procedure rooms)"""
    area = models.ForeignKey(ClinicArea, on_delete=models.CASCADE, related_name='stations')
    name = models.CharField(max_length=100)
    station_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    current_status = models.CharField(
        max_length=20,
        choices=[
            ('AVAILABLE', 'Available'),
            ('OCCUPIED', 'Occupied'),
            ('MAINTENANCE', 'Under Maintenance'),
            ('RESERVED', 'Reserved'),
        ],
        default='AVAILABLE'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['area', 'station_number']
        ordering = ['area', 'station_number']

    def __str__(self):
        return f"{self.area.name} - Station {self.station_number}"

class VisitType(models.Model):
    """Different types of clinic visits"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    default_duration = models.PositiveIntegerField(help_text="Default duration in minutes")
    requires_doctor = models.BooleanField(default=True)
    requires_appointment = models.BooleanField(default=True)
    standard_procedures = models.TextField(blank=True, help_text="Standard procedures for this visit type")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClinicVisit(models.Model):
    """Record of patient visits to the clinic"""
    PRIORITY_CHOICES = [
        ('A', 'Blue A - High Priority'),
        ('B', 'Green B - Medium Priority'),
        ('C', 'Red C - Low Priority')
    ]

    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('WAITING', 'Waiting'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show')
    ]

    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='clinic_visits',
        limit_choices_to={'role__name': 'PATIENT'}
    )
    visit_type = models.ForeignKey(VisitType, on_delete=models.PROTECT)
    appointment = models.OneToOneField(
        'appointment_management.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='B')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    
    # Timing information
    registration_time = models.DateTimeField(auto_now_add=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Location tracking
    current_area = models.ForeignKey(
        ClinicArea,
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_visits'
    )
    current_station = models.ForeignKey(
        ClinicStation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_visits'
    )
    
    # Visit details
    chief_complaint = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_visits'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-registration_time']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['patient', 'registration_time']),
        ]

    def __str__(self):
        return f"Visit for {self.patient.get_full_name()} on {self.registration_time.date()}"

    def get_wait_time(self):
        """Calculate patient wait time"""
        if self.start_time and self.check_in_time:
            return self.start_time - self.check_in_time
        return None

    def get_total_duration(self):
        """Calculate total visit duration"""
        if self.end_time and self.check_in_time:
            return self.end_time - self.check_in_time
        return None

class VisitChecklist(models.Model):
    """Checklist items for different visit types"""
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, related_name='checklist_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    responsible_role = models.ForeignKey(
        'access_control.Role',
        on_delete=models.SET_NULL,
        null=True
    )
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes", null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['visit_type', 'order']

    def __str__(self):
        return f"{self.visit_type.name} - {self.name}"

class VisitChecklistCompletion(models.Model):
    """Track completion of checklist items for each visit"""
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE, related_name='checklist_completions')
    checklist_item = models.ForeignKey(VisitChecklist, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('SKIPPED', 'Skipped'),
        ],
        default='PENDING'
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='completed_checklist_items'
    )
    completed_at = models.DateTimeField(null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['visit', 'checklist_item']
        ordering = ['checklist_item__order']

    def __str__(self):
        return f"{self.checklist_item.name} for {self.visit}"

class ClinicFlow(models.Model):
    """Track patient movement through different clinic areas"""
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE, related_name='flow_records')
    area = models.ForeignKey(ClinicArea, on_delete=models.CASCADE)
    station = models.ForeignKey(ClinicStation, on_delete=models.SET_NULL, null=True)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('WAITING', 'Waiting'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('SKIPPED', 'Skipped')
        ],
        default='WAITING'
    )
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handled_flows'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['visit', 'entry_time']
        indexes = [
            models.Index(fields=['visit', 'area']),
            models.Index(fields=['entry_time']),
        ]

    def __str__(self):
        return f"{self.visit} - {self.area.name}"

    def get_duration(self):
        """Calculate duration spent in this area"""
        if self.exit_time:
            return self.exit_time - self.entry_time
        return None

class WaitingList(models.Model):
    """Manage waiting lists for different clinic areas"""
    area = models.ForeignKey(ClinicArea, on_delete=models.CASCADE, related_name='waiting_list')
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE)
    priority = models.CharField(max_length=1, choices=ClinicVisit.PRIORITY_CHOICES)
    join_time = models.DateTimeField(auto_now_add=True)
    estimated_wait_time = models.PositiveIntegerField(help_text="Estimated wait time in minutes")
    status = models.CharField(
        max_length=20,
        choices=[
            ('WAITING', 'Waiting'),
            ('CALLED', 'Called'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='WAITING'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'join_time']
        indexes = [
            models.Index(fields=['area', 'status']),
            models.Index(fields=['priority', 'join_time']),
        ]

    def __str__(self):
        return f"{self.visit.patient.get_full_name()} - {self.area.name}"

    def calculate_wait_time(self):
        """Calculate actual wait time so far"""
        return timezone.now() - self.join_time

class ClinicDaySheet(models.Model):
    """Daily clinic operation sheet"""
    date = models.DateField(unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PLANNED', 'Planned'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CLOSED', 'Closed')
        ],
        default='PLANNED'
    )
    total_appointments = models.PositiveIntegerField(default=0)
    total_walk_ins = models.PositiveIntegerField(default=0)
    total_patients = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    opened_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opened_daysheets'
    )
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='closed_daysheets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Clinic Day Sheet - {self.date}"

class StaffAssignment(models.Model):
    """Staff assignments to different clinic areas"""
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clinic_assignments'
    )
    area = models.ForeignKey(ClinicArea, on_delete=models.CASCADE)
    station = models.ForeignKey(
        ClinicStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary assignment for the staff member"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('SCHEDULED', 'Scheduled'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='SCHEDULED'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['area', 'date']),
        ]

    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.area.name} ({self.date})"

class ResourceAllocation(models.Model):
    """Track allocation of clinic resources"""
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE, related_name='resource_allocations')
    resource_type = models.CharField(
        max_length=20,
        choices=[
            ('ROOM', 'Treatment Room'),
            ('EQUIPMENT', 'Medical Equipment'),
            ('STAFF', 'Staff Member'),
            ('OTHER', 'Other Resource')
        ]
    )
    resource_id = models.CharField(max_length=50)
    allocated_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True)
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resource_allocations'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-allocated_at']
        indexes = [
            models.Index(fields=['visit', 'resource_type']),
            models.Index(fields=['resource_id']),
        ]

    def __str__(self):
        return f"{self.get_resource_type_display()} allocation for {self.visit}"

class ClinicNotification(models.Model):
    """Notifications related to clinic operations"""
    PRIORITY_CHOICES = [
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority')
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    recipient_roles = models.ManyToManyField('access_control.Role', related_name='clinic_notifications')
    recipient_users = models.ManyToManyField(User, related_name='clinic_notifications', blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('SENT', 'Sent'),
            ('READ', 'Read'),
            ('ACTIONED', 'Actioned')
        ],
        default='PENDING'
    )
    send_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clinic_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-send_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['send_at']),
        ]

    def __str__(self):
        return self.title

class OperationalAlert(models.Model):
    """System for managing clinic operational alerts"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(
        max_length=20,
        choices=[
            ('CAPACITY', 'Capacity Alert'),
            ('WAIT_TIME', 'Wait Time Alert'),
            ('RESOURCE', 'Resource Alert'),
            ('EMERGENCY', 'Emergency Alert'),
            ('OTHER', 'Other Alert')
        ]
    )
    priority = models.CharField(
        max_length=10,
        choices=ClinicNotification.PRIORITY_CHOICES,
        default='MEDIUM'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('ACKNOWLEDGED', 'Acknowledged'),
            ('RESOLVED', 'Resolved'),
            ('DISMISSED', 'Dismissed')
        ],
        default='ACTIVE'
    )
    area = models.ForeignKey(
        ClinicArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    affected_services = models.ManyToManyField(VisitType, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['alert_type']),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"

class ClinicMetrics(models.Model):
    """Track key clinic operational metrics"""
    date = models.DateField()
    area = models.ForeignKey(ClinicArea, on_delete=models.CASCADE)
    total_patients = models.PositiveIntegerField(default=0)
    avg_wait_time = models.FloatField(help_text="Average wait time in minutes")
    max_wait_time = models.FloatField(help_text="Maximum wait time in minutes")
    total_no_shows = models.PositiveIntegerField(default=0)
    capacity_utilization = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Capacity utilization percentage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['date', 'area']
        ordering = ['-date', 'area']
        indexes = [models.Index(fields=['date', 'area'])]

    def __str__(self):
        return f"Metrics for {self.area.name} on {self.date}"