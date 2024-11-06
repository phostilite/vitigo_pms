from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Employee, Attendance, LeaveType, LeaveRequest, PerformanceReview, Training, TrainingAttendance

class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ['date', 'time_in', 'time_out', 'status', 'notes']

class LeaveRequestInline(admin.TabularInline):
    model = LeaveRequest
    extra = 0
    fields = ['leave_type', 'start_date', 'end_date', 'status']

class TrainingAttendanceInline(admin.TabularInline):
    model = TrainingAttendance
    extra = 0
    fields = ['training', 'status', 'feedback']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'department', 'position', 'phone_number', 'is_active']
    list_filter = ['department', 'is_active', 'date_of_joining']
    search_fields = ['employee_id', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    inlines = [AttendanceInline, LeaveRequestInline, TrainingAttendanceInline]
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'time_in', 'time_out', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_id']
    date_hierarchy = 'date'

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_days_per_year']
    search_fields = ['name']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_id']
    date_hierarchy = 'start_date'
    actions = ['approve_leave', 'reject_leave']

    def approve_leave(self, request, queryset):
        queryset.update(status='APPROVED', approved_by=request.user)
    approve_leave.short_description = "Approve selected leave requests"

    def reject_leave(self, request, queryset):
        queryset.update(status='REJECTED', approved_by=request.user)
    reject_leave.short_description = "Reject selected leave requests"

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'reviewer', 'review_date', 'performance_score']
    list_filter = ['review_date', 'performance_score']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_id']
    date_hierarchy = 'review_date'

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'trainer', 'start_date', 'end_date', 'location', 'max_participants']
    list_filter = ['start_date', 'location']
    search_fields = ['title', 'trainer', 'description']
    date_hierarchy = 'start_date'

@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = ['training', 'employee', 'status']
    list_filter = ['status', 'training']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'training__title']
    actions = ['mark_as_attended', 'mark_as_completed']

    def mark_as_attended(self, request, queryset):
        queryset.update(status='ATTENDED')
    mark_as_attended.short_description = "Mark selected entries as attended"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_as_completed.short_description = "Mark selected entries as completed"


