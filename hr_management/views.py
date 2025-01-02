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
        return f'{role_folder}/{module}/{base_template}'
    return f'{role_folder}/{base_template}'

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

            context = {
            }

            return render(request, template_path, context)

        except Exception as e:
            logger.exception(f"Error in HRManagementView: {str(e)}")
            return handler500(request, exception=str(e))