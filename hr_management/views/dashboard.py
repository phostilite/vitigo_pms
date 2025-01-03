# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from django.views import View

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.utils import get_template_path

# Initialize logger
logger = logging.getLogger(__name__)

class HRManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to access HR Management")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('dashboard/dashboard.html', self.request.user.role, 'hr_management')

    def get_dashboard_stats(self):
        """Get key statistics for HR dashboard"""
        try:
            from hr_management.models import Employee, Department, Leave, Training, Grievance
            current_date = timezone.now().date()

            stats = {
                'total_employees': Employee.objects.filter(is_active=True).count(),
                'departments': Department.objects.filter(is_active=True).count(),
                'pending_leaves': Leave.objects.filter(status='PENDING').count(),
                'active_trainings': Training.objects.filter(
                    status='IN_PROGRESS',
                    start_date__lte=current_date,
                    end_date__gte=current_date
                ).count(),
                'open_grievances': Grievance.objects.filter(
                    status__in=['OPEN', 'IN_PROGRESS']
                ).count(),
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {}

    def get_department_stats(self):
        """Get department-wise employee distribution"""
        try:
            from hr_management.models import Department
            dept_stats = Department.objects.annotate(
                employee_count=Count('employees', filter=Q(employees__is_active=True))
            ).filter(is_active=True).values('name', 'employee_count')
            return list(dept_stats)
        except Exception as e:
            logger.error(f"Error getting department stats: {str(e)}")
            return []

    def get_recent_activities(self):
        """Get recent HR activities"""
        try:
            from hr_management.models import Employee, Leave, Training, Grievance
            
            # Get last 5 activities of each type
            recent_employees = Employee.objects.filter(
                is_active=True
            ).order_by('-created_at')[:5]
            
            recent_leaves = Leave.objects.filter(
                start_date__gte=timezone.now().date()
            ).order_by('start_date')[:5]
            
            recent_trainings = Training.objects.filter(
                status__in=['PLANNED', 'IN_PROGRESS']
            ).order_by('-created_at')[:5]
            
            recent_grievances = Grievance.objects.exclude(
                status='CLOSED'
            ).order_by('-filed_date')[:5]

            return {
                'recent_employees': recent_employees,
                'recent_leaves': recent_leaves,
                'recent_trainings': recent_trainings,
                'recent_grievances': recent_grievances
            }
        except Exception as e:
            logger.error(f"Error getting recent activities: {str(e)}")
            return {}

    def get_leave_stats(self):
        """Get leave statistics"""
        try:
            from hr_management.models import Leave
            current_month = timezone.now().month
            
            leave_stats = Leave.objects.filter(
                start_date__month=current_month
            ).aggregate(
                approved=Count('id', filter=Q(status='APPROVED')),
                pending=Count('id', filter=Q(status='PENDING')),
                rejected=Count('id', filter=Q(status='REJECTED'))
            )
            return leave_stats
        except Exception as e:
            logger.error(f"Error getting leave stats: {str(e)}")
            return {}

    def get(self, request):
        try:
            template_path = self.get_template_name()
            if not template_path:
                return handler403(request, exception="Unauthorized access")

            # Prepare context with all dashboard data
            context = {
                'dashboard_stats': self.get_dashboard_stats(),
                'department_stats': self.get_department_stats(),
                'recent_activities': self.get_recent_activities(),
                'leave_stats': self.get_leave_stats(),
                'user_role': request.user.role.name if request.user.role else None,
                'module_name': 'HR Management',
                'page_title': 'HR Dashboard',
            }

            return render(request, template_path, context)
            
        except Exception as e:
            logger.exception(f"Error in HRManagementView: {str(e)}")
            messages.error(request, "An error occurred while loading the HR dashboard.")
            return handler500(request, exception=str(e))