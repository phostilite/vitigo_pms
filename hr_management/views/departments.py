# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.models import Department
from hr_management.forms import DepartmentForm
from hr_management.utils import get_template_path

# Initialize logger
logger = logging.getLogger(__name__)

class DepartmentListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('departments/department_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')

        departments = Department.objects.annotate(
            employee_count=Count('employees', filter=Q(employees__is_active=True))
        )

        # Apply filters
        if search_query:
            departments = departments.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query)
            )

        if status_filter:
            departments = departments.filter(is_active=(status_filter == 'active'))

        # Pagination
        paginator = Paginator(departments, 10)
        page = request.GET.get('page', 1)
        try:
            departments_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            departments_page = paginator.page(1)

        context = {
            'departments': departments_page,
            'search_query': search_query,
            'status_filter': status_filter,
        }

        return render(request, self.get_template_name(), context)

class NewDepartmentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('departments/new_department.html', self.request.user.role, 'hr_management')

    def get(self, request):
        form = DepartmentForm()
        return render(request, self.get_template_name(), {'form': form})

    def post(self, request):
        form = DepartmentForm(request.POST)
        if form.is_valid():
            try:
                department = form.save()
                messages.success(request, "Department created successfully")
                return redirect('department_list')
            except Exception as e:
                logger.error(f"Error creating department: {str(e)}")
                messages.error(request, "Error creating department")
                return render(request, self.get_template_name(), {'form': form})
        
        return render(request, self.get_template_name(), {'form': form})