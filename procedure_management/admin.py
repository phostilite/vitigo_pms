from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ProcedureType, Procedure, ConsentForm, ProcedureResult, ProcedureImage

@admin.register(ProcedureType)
class ProcedureTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class ConsentFormInline(admin.StackedInline):
    model = ConsentForm
    extra = 0

class ProcedureResultInline(admin.StackedInline):
    model = ProcedureResult
    extra = 0

class ProcedureImageInline(admin.TabularInline):
    model = ProcedureImage
    extra = 1

@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('procedure_type', 'patient_link', 'scheduled_date', 'status', 'performed_by')
    list_filter = ('status', 'scheduled_date', 'procedure_type')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'procedure_type__name')
    inlines = [ConsentFormInline, ProcedureResultInline, ProcedureImageInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('patient', 'procedure_type', 'scheduled_date', 'status', 'performed_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())
    patient_link.short_description = 'Patient'

@admin.register(ConsentForm)
class ConsentFormAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'signed_by_patient', 'signed_date')
    list_filter = ('signed_by_patient', 'signed_date')
    search_fields = ('procedure__patient__user__first_name', 'procedure__patient__user__last_name', 'procedure__procedure_type__name')

@admin.register(ProcedureResult)
class ProcedureResultAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'follow_up_required')
    list_filter = ('follow_up_required',)
    search_fields = ('procedure__patient__user__first_name', 'procedure__patient__user__last_name', 'procedure__procedure_type__name')

@admin.register(ProcedureImage)
class ProcedureImageAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('procedure__patient__user__first_name', 'procedure__patient__user__last_name', 'procedure__procedure_type__name', 'caption')

# Customize admin site
admin.site.site_header = "VitiGo Procedure Management"
admin.site.site_title = "VitiGo Procedure Admin"
admin.site.index_title = "Welcome to VitiGo Procedure Management System"