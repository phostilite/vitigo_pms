from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Query, QueryUpdate, QueryTag, QueryAttachment


class QueryUpdateInline(admin.TabularInline):
    model = QueryUpdate
    extra = 1


class QueryAttachmentInline(admin.TabularInline):
    model = QueryAttachment
    extra = 1


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'subject', 'priority', 'status', 'source', 'created_at', 'assigned_to', 'patient_link')
    list_filter = ('priority', 'status', 'source', 'created_at')
    search_fields = ('query_id', 'subject', 'description', 'patient__email', 'assigned_to__email')
    readonly_fields = ('query_id', 'created_at', 'updated_at')
    inlines = [QueryUpdateInline, QueryAttachmentInline]
    autocomplete_fields = ['patient', 'assigned_to', 'tags']

    fieldsets = (
        (None, {
            'fields': ('subject', 'description', 'priority', 'status', 'source')
        }),
        (_('Contacts'), {
            'fields': ('patient', 'assigned_to', 'is_anonymous', 'contact_email', 'contact_phone')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        }),
        (_('Categorization'), {
            'fields': ('tags',)
        }),
    )

    def patient_link(self, obj):
        if obj.patient:
            url = reverse("admin:user_management_customuser_change", args=[obj.patient.id])
            return format_html('<a href="{}">{}</a>', url, obj.patient.email)
        return "N/A"

    patient_link.short_description = 'Patient'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'assigned_to')


@admin.register(QueryTag)
class QueryTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(QueryUpdate)
class QueryUpdateAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query__subject', 'content', 'user__email')
    autocomplete_fields = ['query', 'user']


@admin.register(QueryAttachment)
class QueryAttachmentAdmin(admin.ModelAdmin):
    list_display = ('query', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('query__subject', 'file')
    autocomplete_fields = ['query']

