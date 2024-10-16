from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Consultation, Prescription, TreatmentInstruction, ConsultationAttachment, FollowUpPlan

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1

class TreatmentInstructionInline(admin.StackedInline):
    model = TreatmentInstruction

class ConsultationAttachmentInline(admin.TabularInline):
    model = ConsultationAttachment
    extra = 1

class FollowUpPlanInline(admin.StackedInline):
    model = FollowUpPlan

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient_link', 'doctor_link', 'consultation_type', 'date_time', 'diagnosis')
    list_filter = ('consultation_type', 'date_time', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'patient__user__email', 'doctor__first_name', 'doctor__last_name', 'doctor__email', 'diagnosis')
    date_hierarchy = 'date_time'
    inlines = [PrescriptionInline, TreatmentInstructionInline, ConsultationAttachmentInline, FollowUpPlanInline]

    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor', 'consultation_type', 'date_time')
        }),
        ('Consultation Details', {
            'fields': ('chief_complaint', 'vitals', 'notes', 'diagnosis', 'follow_up_date')
        }),
    )

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())
    patient_link.short_description = 'Patient'

    def doctor_link(self, obj):
        url = reverse("admin:user_management_customuser_change", args=[obj.doctor.id])
        return format_html('<a href="{}">{}</a>', url, obj.doctor.get_full_name())
    doctor_link.short_description = 'Doctor'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medication', 'consultation_link', 'dosage', 'frequency', 'duration')
    list_filter = ('consultation__date_time', 'medication')
    search_fields = ('consultation__patient__user__first_name', 'consultation__patient__user__last_name', 'medication__name')

    def consultation_link(self, obj):
        url = reverse("admin:consultation_management_consultation_change", args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation)
    consultation_link.short_description = 'Consultation'

@admin.register(TreatmentInstruction)
class TreatmentInstructionAdmin(admin.ModelAdmin):
    list_display = ('consultation_link', 'lifestyle_changes', 'dietary_instructions')
    search_fields = ('consultation__patient__user__first_name', 'consultation__patient__user__last_name', 'lifestyle_changes', 'dietary_instructions')

    def consultation_link(self, obj):
        url = reverse("admin:consultation_management_consultation_change", args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation)
    consultation_link.short_description = 'Consultation'

@admin.register(ConsultationAttachment)
class ConsultationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('consultation_link', 'description', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('consultation__patient__user__first_name', 'consultation__patient__user__last_name', 'description')

    def consultation_link(self, obj):
        url = reverse("admin:consultation_management_consultation_change", args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation)
    consultation_link.short_description = 'Consultation'

@admin.register(FollowUpPlan)
class FollowUpPlanAdmin(admin.ModelAdmin):
    list_display = ('consultation_link', 'follow_up_date', 'reason')
    list_filter = ('follow_up_date',)
    search_fields = ('consultation__patient__user__first_name', 'consultation__patient__user__last_name', 'reason')

    def consultation_link(self, obj):
        url = reverse("admin:consultation_management_consultation_change", args=[obj.consultation.id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation)
    consultation_link.short_description = 'Consultation'