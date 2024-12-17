from django.contrib import admin
from .models import (
    ClinicArea, ClinicStation, VisitType, ClinicVisit, VisitChecklist,
    VisitChecklistCompletion, PaymentTerminal, VisitPaymentTransaction,
    ClinicFlow, WaitingList, ClinicDaySheet, StaffAssignment,
    ResourceAllocation, ClinicNotification, OperationalAlert, ClinicMetrics
)

@admin.register(ClinicArea)
class ClinicAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'capacity', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active', 'requires_doctor', 'requires_appointment')
    fields = ('name', 'code', 'description', 'is_active', 'capacity', 
              'requires_doctor', 'requires_appointment', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ClinicStation)
class ClinicStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'area', 'station_number', 'current_status', 'is_active')
    search_fields = ('name', 'station_number')
    list_filter = ('area', 'current_status', 'is_active')
    fields = ('area', 'name', 'station_number', 'is_active', 'current_status',
              'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VisitType)
class VisitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'default_duration', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('requires_doctor', 'requires_appointment', 'is_active')
    fields = ('name', 'code', 'description', 'default_duration', 'requires_doctor',
              'requires_appointment', 'standard_procedures', 'is_active', 
              'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ClinicVisit)
class ClinicVisitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'visit_type', 'status', 'priority', 'registration_time')
    search_fields = ('patient__first_name', 'patient__last_name', 'chief_complaint')
    list_filter = ('status', 'priority', 'visit_type')
    date_hierarchy = 'registration_time'
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'visit_type', 'appointment', 'priority', 'status')
        }),
        ('Timing Information', {
            'fields': ('registration_time', 'check_in_time', 'start_time', 'end_time')
        }),
        ('Location', {
            'fields': ('current_area', 'current_station')
        }),
        ('Visit Details', {
            'fields': ('chief_complaint', 'notes', 'cancellation_reason', 
                      'follow_up_required', 'follow_up_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'registration_time')

@admin.register(VisitChecklist)
class VisitChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'visit_type', 'is_mandatory', 'order', 'is_active')
    search_fields = ('name',)
    list_filter = ('visit_type', 'is_mandatory', 'is_active')
    fields = ('visit_type', 'name', 'description', 'is_mandatory', 'order',
              'responsible_role', 'estimated_duration', 'is_active', 
              'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VisitChecklistCompletion)
class VisitChecklistCompletionAdmin(admin.ModelAdmin):
    list_display = ('visit', 'checklist_item', 'status', 'completed_by', 'completed_at')
    search_fields = ('visit__patient__first_name', 'checklist_item__name')
    list_filter = ('status',)
    fields = ('visit', 'checklist_item', 'status', 'completed_by', 
              'completed_at', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PaymentTerminal)
class PaymentTerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'terminal_id', 'terminal_type', 'location', 'is_active')
    search_fields = ('name', 'terminal_id')
    list_filter = ('terminal_type', 'is_active')
    fields = ('name', 'terminal_id', 'location', 'terminal_type', 'is_active',
              'last_maintenance', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VisitPaymentTransaction)
class VisitPaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('visit', 'amount', 'payment_method', 'status', 'processed_at')
    search_fields = ('receipt_number', 'transaction_id')
    list_filter = ('payment_method', 'status')
    fields = ('visit', 'amount', 'payment_method', 'terminal', 'transaction_id',
              'status', 'receipt_number', 'notes', 'processed_by', 'processed_at',
              'updated_at')
    readonly_fields = ('processed_at', 'updated_at')

@admin.register(ClinicFlow)
class ClinicFlowAdmin(admin.ModelAdmin):
    list_display = ('visit', 'area', 'station', 'status', 'entry_time')
    search_fields = ('visit__patient__first_name',)
    list_filter = ('status', 'area')
    fields = ('visit', 'area', 'station', 'entry_time', 'exit_time', 'status',
              'handled_by', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ('visit', 'area', 'priority', 'status', 'join_time')
    search_fields = ('visit__patient__first_name',)
    list_filter = ('priority', 'status', 'area')
    fields = ('area', 'visit', 'priority', 'join_time', 'estimated_wait_time',
              'status', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'join_time')

@admin.register(ClinicDaySheet)
class ClinicDaySheetAdmin(admin.ModelAdmin):
    list_display = ('date', 'status', 'total_patients', 'total_appointments', 'total_walk_ins')
    list_filter = ('status',)
    date_hierarchy = 'date'
    fields = ('date', 'status', 'total_appointments', 'total_walk_ins',
              'total_patients', 'notes', 'opened_by', 'closed_by',
              'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ('staff', 'area', 'date', 'start_time', 'end_time', 'status')
    search_fields = ('staff__first_name', 'staff__last_name')
    list_filter = ('status', 'area', 'is_primary')
    date_hierarchy = 'date'
    fields = ('staff', 'area', 'station', 'date', 'start_time', 'end_time',
              'is_primary', 'status', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ResourceAllocation)
class ResourceAllocationAdmin(admin.ModelAdmin):
    list_display = ('visit', 'resource_type', 'resource_id', 'allocated_at', 'released_at')
    search_fields = ('resource_id',)
    list_filter = ('resource_type',)
    fields = ('visit', 'resource_type', 'resource_id', 'allocated_at',
              'released_at', 'allocated_by', 'notes', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'allocated_at')

@admin.register(ClinicNotification)
class ClinicNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'status', 'send_at', 'expires_at')
    search_fields = ('title', 'message')
    list_filter = ('priority', 'status')
    fields = ('title', 'message', 'priority', 'recipient_roles', 'recipient_users',
              'status', 'send_at', 'expires_at', 'created_by', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(OperationalAlert)
class OperationalAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'priority', 'status', 'area')
    search_fields = ('title', 'description')
    list_filter = ('alert_type', 'priority', 'status')
    fields = ('title', 'description', 'alert_type', 'priority', 'status',
              'area', 'affected_services', 'resolution_notes', 'resolved_by',
              'resolved_at', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ClinicMetrics)
class ClinicMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'area', 'total_patients', 'avg_wait_time', 'capacity_utilization')
    list_filter = ('area',)
    date_hierarchy = 'date'
    fields = ('date', 'area', 'total_patients', 'avg_wait_time', 'max_wait_time',
              'total_no_shows', 'capacity_utilization', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
