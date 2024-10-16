from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TimeSlot, Appointment, AppointmentReminder, CancellationReason


class AppointmentReminderInline(admin.TabularInline):
    model = AppointmentReminder
    extra = 1


class CancellationReasonInline(admin.StackedInline):
    model = CancellationReason
    extra = 0
    max_num = 1


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')
    ordering = ('start_time',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_link', 'doctor_link', 'appointment_type', 'date', 'time_slot', 'status', 'priority')
    list_filter = ('appointment_type', 'status', 'priority', 'date', 'doctor')
    search_fields = ('patient__email', 'patient__first_name', 'patient__last_name', 'doctor__email', 'notes')
    date_hierarchy = 'date'
    inlines = [AppointmentReminderInline, CancellationReasonInline]

    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor', 'appointment_type', 'date', 'time_slot', 'status', 'priority')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def patient_link(self, obj):
        url = reverse("admin:user_management_customuser_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.get_full_name())

    patient_link.short_description = 'Patient'

    def doctor_link(self, obj):
        url = reverse("admin:user_management_customuser_change", args=[obj.doctor.id])
        return format_html('<a href="{}">{}</a>', url, obj.doctor.get_full_name())

    doctor_link.short_description = 'Doctor'


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'reminder_date', 'sent')
    list_filter = ('sent', 'reminder_date')
    search_fields = (
    'appointment__patient__email', 'appointment__patient__first_name', 'appointment__patient__last_name')


@admin.register(CancellationReason)
class CancellationReasonAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'cancelled_by', 'cancelled_at')
    list_filter = ('cancelled_at',)
    search_fields = (
    'appointment__patient__email', 'appointment__patient__first_name', 'appointment__patient__last_name', 'reason')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('appointment', 'cancelled_by', 'cancelled_at')
        return self.readonly_fields