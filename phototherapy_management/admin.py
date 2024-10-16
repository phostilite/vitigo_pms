from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import PhototherapyType, PhototherapyProtocol, PhototherapyPlan, PhototherapySession, PhototherapyDevice, HomePhototherapyLog

@admin.register(PhototherapyType)
class PhototherapyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(PhototherapyProtocol)
class PhototherapyProtocolAdmin(admin.ModelAdmin):
    list_display = ('name', 'phototherapy_type', 'initial_dose', 'max_dose', 'frequency', 'duration_weeks')
    list_filter = ('phototherapy_type', 'frequency')
    search_fields = ('name', 'description')

class PhototherapySessionInline(admin.TabularInline):
    model = PhototherapySession
    extra = 1

class HomePhototherapyLogInline(admin.TabularInline):
    model = HomePhototherapyLog
    extra = 1

@admin.register(PhototherapyPlan)
class PhototherapyPlanAdmin(admin.ModelAdmin):
    list_display = ('patient_link', 'protocol', 'start_date', 'end_date', 'current_dose', 'is_active')
    list_filter = ('protocol__phototherapy_type', 'start_date', 'is_active')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'protocol__name')
    inlines = [PhototherapySessionInline, HomePhototherapyLogInline]

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())
    patient_link.short_description = 'Patient'

@admin.register(PhototherapySession)
class PhototherapySessionAdmin(admin.ModelAdmin):
    list_display = ('plan_patient', 'session_date', 'actual_dose', 'compliance', 'administered_by')
    list_filter = ('compliance', 'session_date')
    search_fields = ('plan__patient__user__first_name', 'plan__patient__user__last_name', 'administered_by__email')

    def plan_patient(self, obj):
        return obj.plan.patient.user.get_full_name()
    plan_patient.short_description = 'Patient'

@admin.register(PhototherapyDevice)
class PhototherapyDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'serial_number', 'phototherapy_type', 'location', 'is_active', 'next_maintenance_date')
    list_filter = ('phototherapy_type', 'is_active', 'location')
    search_fields = ('name', 'model', 'serial_number')

@admin.register(HomePhototherapyLog)
class HomePhototherapyLogAdmin(admin.ModelAdmin):
    list_display = ('plan_patient', 'date', 'duration', 'reported_by')
    list_filter = ('date',)
    search_fields = ('plan__patient__user__first_name', 'plan__patient__user__last_name', 'reported_by__email')

    def plan_patient(self, obj):
        return obj.plan.patient.user.get_full_name()
    plan_patient.short_description = 'Patient'

