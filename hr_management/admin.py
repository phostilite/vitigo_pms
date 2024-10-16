from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Employee, Attendance, LeaveType, LeaveRequest, PerformanceReview, Training, TrainingAttendance


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user_full_name', 'department', 'position', 'date_of_joining', 'is_active')
    list_filter = ('department', 'is_active', 'date_of_joining')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'employee_id')
    readonly_fields = ('user_link',)

    fieldsets = (
        ('Personal Information', {
            'fields': ('user_link', 'employee_id', 'date_of_birth', 'gender', 'address', 'phone_number')
        }),
        ('Employment Details', {
            'fields': ('department', 'position', 'date_of_joining', 'is_active')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number')
        }),
        ('Bank Details', {
            'fields': ('bank_account_number', 'bank_name')
        }),
    )

    def user_full_name(self, obj):
        return obj.user.get_full_name()

    user_full_name.short_description = 'Name'

    def user_link(self, obj):
        url = reverse("admin:user_management_customuser_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    user_link.short_description = 'User Account'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'time_in', 'time_out', 'status')
    list_filter = ('status', 'date')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'employee__employee_id')
    date_hierarchy = 'date'


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year')
    search_fields = ('name',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'employee__employee_id')
    date_hierarchy = 'start_date'

    def save_model(self, request, obj, form, change):
        if obj.status == 'APPROVED' and not obj.approved_by:
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_date', 'performance_score')
    list_filter = ('review_date', 'performance_score')
    search_fields = (
    'employee__user__first_name', 'employee__user__last_name', 'employee__employee_id', 'reviewer__email')
    date_hierarchy = 'review_date'


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'trainer', 'start_date', 'end_date', 'location', 'max_participants')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'description', 'trainer')
    date_hierarchy = 'start_date'


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'training', 'status')
    list_filter = ('status', 'training')
    search_fields = (
    'employee__user__first_name', 'employee__user__last_name', 'employee__employee_id', 'training__title')


# Customize admin site
admin.site.site_header = "VitiGo HR Management"
admin.site.site_title = "VitiGo HR Admin"
admin.site.index_title = "Welcome to VitiGo HR Management System"