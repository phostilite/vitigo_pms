# Python Standard Library imports
import logging
from datetime import datetime

# Django core imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import (
    Employee, 
    Attendance, 
    LeaveType, 
    LeaveRequest, 
    PerformanceReview, 
    Training, 
    TrainingAttendance
)

# Logger configuration
logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module=''):
    """Resolves template path based on user role"""
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class HRManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to access HR Management")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('hr_dashboard.html', self.request.user.role, 'hr_management')

    def get(self, request):
        try:
            template_path = self.get_template_name()
            
            if not template_path:
                return handler403(request, exception="Unauthorized access")

            # Get filter parameters from URL
            filters = {}
            department = request.GET.get('department')
            status = request.GET.get('status')
            date = request.GET.get('date')
            search = request.GET.get('search')

            # Base queryset - only select_related 'user' since department is a CharField
            employees = Employee.objects.select_related('user')
            
            # Apply filters - fix department filter
            if department:
                filters['department'] = department  # Changed from department_id to department
            if status:
                filters['status'] = status
            if date:
                filters['date_joined'] = date

            # Apply search
            if search:
                employees = employees.filter(
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search) |
                    Q(user__email__icontains=search) |
                    Q(employee_id__icontains=search)
                )

            employees = employees.filter(**filters)

            # Fetch related data
            attendance_records = Attendance.objects.all()
            leave_requests = LeaveRequest.objects.all()
            performance_reviews = PerformanceReview.objects.all()
            trainings = Training.objects.all()

            # Calculate statistics
            total_employees = employees.count()
            total_attendance = attendance_records.count()
            total_leave_requests = leave_requests.count()
            total_performance_reviews = performance_reviews.count()
            total_trainings = trainings.count()

            # Pagination for employees
            paginator = Paginator(employees, 10)
            page = request.GET.get('page')
            try:
                employees = paginator.page(page)
            except PageNotAnInteger:
                employees = paginator.page(1)
            except EmptyPage:
                employees = paginator.page(paginator.num_pages)

            context = {
                'employees': employees,
                'attendance_records': attendance_records,
                'leave_requests': leave_requests,
                'performance_reviews': performance_reviews,
                'trainings': trainings,
                'total_employees': total_employees,
                'total_attendance': total_attendance,
                'total_leave_requests': total_leave_requests,
                'total_performance_reviews': total_performance_reviews,
                'total_trainings': total_trainings,
                'paginator': paginator,
                'page_obj': employees,
                'current_filters': {
                    'department': department,
                    'status': status,
                    'date': date,
                    'search': search
                },
                'user_role': request.user.role,
            }

            return render(request, template_path, context)

        except Exception as e:
            logger.exception(f"Error in HRManagementView: {str(e)}")
            return handler500(request, exception=str(e))