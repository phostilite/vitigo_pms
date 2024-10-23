# doctor_management/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Specialization,
    TreatmentMethodSpecialization,
    BodyAreaSpecialization,
    AssociatedConditionSpecialization,
    DoctorProfile,
    DoctorAvailability,
    DoctorReview
)

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20

@admin.register(TreatmentMethodSpecialization)
class TreatmentMethodSpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20

@admin.register(BodyAreaSpecialization)
class BodyAreaSpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20

@admin.register(AssociatedConditionSpecialization)
class AssociatedConditionSpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20

class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 1
    fields = ('day_of_week', 'start_time', 'end_time', 'is_available')

class DoctorReviewInline(admin.TabularInline):
    model = DoctorReview
    extra = 0
    readonly_fields = ('patient', 'rating', 'review', 'created_at')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'registration_number', 'qualification', 'experience', 
                   'consultation_fee', 'rating', 'is_available', 'city', 'created_at')
    list_filter = ('is_available', 'experience', 'city', 'state', 'country')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 
                    'registration_number', 'qualification')
    readonly_fields = ('rating',)
    filter_horizontal = ('specializations', 'treatment_methods', 'body_areas', 
                        'associated_conditions')
    inlines = [DoctorAvailabilityInline, DoctorReviewInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'registration_number', 'qualification', 'experience')
        }),
        ('Specializations', {
            'fields': ('specializations', 'treatment_methods', 'body_areas', 
                      'associated_conditions')
        }),
        ('Practice Details', {
            'fields': ('consultation_fee', 'about', 'is_available')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country')
        }),
        ('Statistics', {
            'fields': ('rating',),
            'classes': ('collapse',)
        })
    )
    list_per_page = 20

    def doctor_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    doctor_name.short_description = 'Doctor Name'

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')
    ordering = ('doctor', 'day_of_week', 'start_time')
    list_per_page = 20

    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"
    doctor_name.short_description = 'Doctor Name'

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'patient_name', 'rating', 'created_at', 'review_excerpt')
    list_filter = ('rating', 'created_at')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name', 
                    'patient__first_name', 'patient__last_name', 'review')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20

    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"
    doctor_name.short_description = 'Doctor Name'

    def patient_name(self, obj):
        return obj.patient.get_full_name()
    patient_name.short_description = 'Patient Name'

    def review_excerpt(self, obj):
        return obj.review[:100] + '...' if len(obj.review) > 100 else obj.review
    review_excerpt.short_description = 'Review'

    def has_add_permission(self, request):
        return False  