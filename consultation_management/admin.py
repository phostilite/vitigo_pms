from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Consultation, 
    Prescription, 
    TreatmentInstruction, 
    ConsultationAttachment, 
    FollowUpPlan
)

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    fields = ('medication', 'dosage', 'frequency', 'duration', 'instructions')

class TreatmentInstructionInline(admin.StackedInline):
    model = TreatmentInstruction
    can_delete = False
    fields = ('lifestyle_changes', 'dietary_instructions', 'skincare_routine', 'additional_notes')

class ConsultationAttachmentInline(admin.TabularInline):
    model = ConsultationAttachment
    extra = 1
    fields = ('file', 'description')

class FollowUpPlanInline(admin.StackedInline):
    model = FollowUpPlan
    can_delete = False
    fields = ('follow_up_date', 'reason', 'tests_required', 'additional_notes')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'doctor_name', 'consultation_type', 
                   'date_time', 'follow_up_date', 'created_at')
    list_filter = ('consultation_type', 'date_time', 'doctor', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 
                    'doctor__first_name', 'doctor__last_name',
                    'chief_complaint', 'diagnosis')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PrescriptionInline, TreatmentInstructionInline, 
               ConsultationAttachmentInline, FollowUpPlanInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'consultation_type', 'date_time')
        }),
        ('Consultation Details', {
            'fields': ('chief_complaint', 'vitals', 'diagnosis', 'notes')
        }),
        ('Follow-up', {
            'fields': ('follow_up_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.get_full_name()}"
        return "Unknown Patient"
    patient_name.short_description = "Patient"

    def doctor_name(self, obj):
        return f"{obj.doctor.get_full_name()}"
    doctor_name.short_description = "Doctor"

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'medication', 'dosage', 'frequency', 'duration')
    list_filter = ('medication', 'consultation__date_time')
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name',
                    'medication__name', 'instructions')

    def get_patient(self, obj):
        return obj.consultation.patient.get_full_name()
    get_patient.short_description = "Patient"

@admin.register(TreatmentInstruction)
class TreatmentInstructionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'get_consultation_date')
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name',
                    'lifestyle_changes', 'dietary_instructions')

    def get_patient(self, obj):
        return obj.consultation.patient.get_full_name()
    get_patient.short_description = "Patient"

    def get_consultation_date(self, obj):
        return obj.consultation.date_time.date()
    get_consultation_date.short_description = "Consultation Date"

@admin.register(ConsultationAttachment)
class ConsultationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'description', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name',
                    'description')

    def get_patient(self, obj):
        return obj.consultation.patient.get_full_name()
    get_patient.short_description = "Patient"

@admin.register(FollowUpPlan)
class FollowUpPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'follow_up_date', 'reason')
    list_filter = ('follow_up_date',)
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name',
                    'reason', 'tests_required')

    def get_patient(self, obj):
        return obj.consultation.patient.get_full_name()
    get_patient.short_description = "Patient"