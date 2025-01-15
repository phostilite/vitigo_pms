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
from ..models import Report, ReportCategory, ReportExport

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
        return get_template_path('dashboard/dashboard.html', self.request.user.role, 'reporting_and_analytics')

    def get(self, request):
        try:
            # Get reports data
            report_categories = ReportCategory.objects.select_related('module').all()
            total_categories = report_categories.count()
            total_reports = Report.objects.count()
            total_exports = ReportExport.objects.count()

            # Group categories by module
            categories_by_module = {}
            for category in report_categories:
                module_name = category.module.display_name
                if module_name not in categories_by_module:
                    categories_by_module[module_name] = []
                categories_by_module[module_name].append(category)

            context = {
                'categories_by_module': categories_by_module,
                'total_categories': total_categories,
                'total_reports': total_reports,
                'total_exports': total_exports,
            }

            template_name = self.get_template_name()
            return render(request, template_name, context)

        except Exception as e:
            logger.error(f"Error in ReportsAnalyticsManagementView: {str(e)}")
            messages.error(request, "An error occurred while fetching reports data.")
            return redirect('reporting_and_analytics:reports_analytics_management')

class CategoryReportsView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'reporting_and_analytics'):
            messages.error(request, "You don't have permission to access Reports & Analytics")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('reports/category_reports.html', self.request.user.role, 'reporting_and_analytics')

    def get(self, request, category_id):
        try:
            category = get_object_or_404(ReportCategory, id=category_id)
            reports = Report.objects.filter(category=category).order_by('order')
            
            context = {
                'category': category,
                'reports': reports,
            }
            
            template_name = self.get_template_name()
            return render(request, template_name, context)

        except Exception as e:
            logger.error(f"Error in CategoryReportsView: {str(e)}")
            messages.error(request, "An error occurred while fetching category reports.")
            return redirect('reporting_and_analytics:reports_analytics_management')