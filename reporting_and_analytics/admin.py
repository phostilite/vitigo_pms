from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_by', 'is_active', 'is_scheduled', 'frequency', 'next_run')
    list_filter = ('report_type', 'is_active', 'is_scheduled', 'frequency')
    search_fields = ('name', 'description', 'created_by__email')
    readonly_fields = ('created_by', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'report_type', 'query', 'parameters', 'is_active')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'frequency', 'next_run')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ('report', 'executed_at', 'executed_by', 'status', 'result_file_link')
    list_filter = ('status', 'executed_at')
    search_fields = ('report__name', 'executed_by__email')
    readonly_fields = ('executed_at', 'executed_by', 'status', 'error_message')

    def result_file_link(self, obj):
        if obj.result_file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.result_file.url)
        return "N/A"
    result_file_link.short_description = 'Result File'

class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 1

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'created_by__email')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    inlines = [DashboardWidgetInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'dashboard', 'widget_type', 'data_source', 'position')
    list_filter = ('widget_type', 'dashboard')
    search_fields = ('name', 'dashboard__name', 'data_source__name')

@admin.register(AnalyticsLog)
class AnalyticsLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__email', 'action', 'details')
    readonly_fields = ('user', 'action', 'details', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
