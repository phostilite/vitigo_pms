from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import BodyPart, ImageTag, PatientImage, ImageComparison, ComparisonImage, ImageAnnotation

@admin.register(BodyPart)
class BodyPartAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(ImageTag)
class ImageTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ImageAnnotationInline(admin.TabularInline):
    model = ImageAnnotation
    extra = 1

@admin.register(PatientImage)
class PatientImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'patient_link', 'body_part', 'image_type', 'date_taken', 'uploaded_by', 'is_private')
    list_filter = ('image_type', 'body_part', 'date_taken', 'is_private')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'notes')
    readonly_fields = ('width', 'height', 'file_size', 'uploaded_at')
    filter_horizontal = ('tags',)
    inlines = [ImageAnnotationInline]

    fieldsets = (
        (None, {
            'fields': ('patient', 'image_file', 'body_part', 'image_type', 'date_taken', 'notes', 'tags')
        }),
        ('Metadata', {
            'fields': ('width', 'height', 'file_size', 'uploaded_at', 'uploaded_by', 'is_private')
        }),
    )

    def thumbnail(self, obj):
        return format_html('<img src="{}" width="50" height="50" />', obj.image_file.url)
    thumbnail.short_description = 'Thumbnail'

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())
    patient_link.short_description = 'Patient'

class ComparisonImageInline(admin.TabularInline):
    model = ComparisonImage
    extra = 1

@admin.register(ImageComparison)
class ImageComparisonAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ComparisonImageInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_by', 'created_at')
        return self.readonly_fields

@admin.register(ImageAnnotation)
class ImageAnnotationAdmin(admin.ModelAdmin):
    list_display = ('image', 'text', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('image__patient__user__first_name', 'image__patient__user__last_name', 'text')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('image', 'created_by', 'created_at')
        return self.readonly_fields
