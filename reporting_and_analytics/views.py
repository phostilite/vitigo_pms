# views.py

# Python Standard Library imports
import logging
from datetime import timedelta, datetime

# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db import transaction

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog

# Configure logging
logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module='reporting_and_analytics'):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'{role_folder}/{module}/{base_template}'
    return f'{role_folder}/{base_template}'

class ReportsAnalyticsManagementView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'reporting_and_analytics'):
            messages.error(request, "You don't have permission to access Reports & Analytics")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('reports_analytics_dashboard.html', self.request.user.role, 'reporting_and_analytics')

    def get(self, request):
        try:
            template_path = self.get_template_name()
            if not template_path:
                return handler403(request, exception="Unauthorized access")

            # Fetch data with try-except blocks
            try:
                reports = Report.objects.all()
                report_executions = ReportExecution.objects.all()
                dashboards = Dashboard.objects.all()
                dashboard_widgets = DashboardWidget.objects.all()
                analytics_logs = AnalyticsLog.objects.all()
            except Exception as e:
                logger.error(f"Error fetching reports data: {str(e)}")
                return handler500(request, exception="Error fetching reports data")

            # Calculate statistics
            context = {
                'reports': reports,
                'report_executions': report_executions,
                'dashboards': dashboards,
                'dashboard_widgets': dashboard_widgets,
                'analytics_logs': analytics_logs,
                'total_reports': reports.count(),
                'total_executions': report_executions.count(),
                'total_dashboards': dashboards.count(),
                'total_widgets': dashboard_widgets.count(),
                'total_logs': analytics_logs.count(),
                'user_role': request.user.role,
            }

            # Handle pagination
            try:
                paginator = Paginator(reports, 10)
                page = request.GET.get('page')
                context['reports'] = paginator.page(page)
                context['paginator'] = paginator
                context['page_obj'] = context['reports']
            except PageNotAnInteger:
                context['reports'] = paginator.page(1)
            except EmptyPage:
                context['reports'] = paginator.page(paginator.num_pages)
            except Exception as e:
                logger.error(f"Pagination error: {str(e)}")
                messages.warning(request, "Error in pagination. Showing all results.")

            return render(request, template_path, context)

        except Exception as e:
            logger.exception(f"Unexpected error in ReportsAnalyticsManagementView: {str(e)}")
            return handler500(request, exception="An unexpected error occurred")