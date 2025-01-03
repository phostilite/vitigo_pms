# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.models import Department, Employee
from hr_management.forms import EmployeeCreationForm
from hr_management.utils import get_template_path

# Get user model
User = get_user_model()

# Initialize logger
logger = logging.getLogger(__name__)

class NewEmployeeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('employees/new_employee.html', self.request.user.role, 'hr_management')

    def get(self, request):
        form = EmployeeCreationForm()
        return render(request, self.get_template_name(), {'form': form})

    def post(self, request):
        form = EmployeeCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create User account
                User = get_user_model()
                user = User.objects.create_user(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )

                # Create Employee profile
                employee = form.save(commit=False)
                employee.user = user
                employee.save()

                messages.success(request, "Employee created successfully")
                return redirect('hr_management')

            except Exception as e:
                logger.error(f"Error creating employee: {str(e)}")
                messages.error(request, "Error creating employee")
                return render(request, self.get_template_name(), {'form': form})

        return render(request, self.get_template_name(), {'form': form})

class EmployeeListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('employees/employee_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        search_query = request.GET.get('search', '')
        department_filter = request.GET.get('department', '')
        status_filter = request.GET.get('status', '')

        employees = Employee.objects.select_related('user', 'department', 'position').all()

        # Apply filters
        if search_query:
            employees = employees.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )

        if department_filter:
            employees = employees.filter(department_id=department_filter)

        if status_filter:
            employees = employees.filter(employment_status=status_filter)

        # Pagination
        paginator = Paginator(employees, 10)
        page = request.GET.get('page', 1)
        try:
            employees_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            employees_page = paginator.page(1)

        departments = Department.objects.filter(is_active=True)
        employment_statuses = dict(Employee.EMPLOYMENT_STATUS)

        context = {
            'employees': employees_page,
            'departments': departments,
            'employment_statuses': employment_statuses,
            'search_query': search_query,
            'department_filter': department_filter,
            'status_filter': status_filter
        }

        return render(request, self.get_template_name(), context)

class BulkActionsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('employees/bulk_actions.html', self.request.user.role, 'hr_management')

    def get(self, request):
        employees = Employee.objects.select_related('user', 'department', 'position').all()
        departments = Department.objects.filter(is_active=True)
        
        context = {
            'employees': employees,
            'departments': departments,
            'employment_statuses': dict(Employee.EMPLOYMENT_STATUS),
        }
        return render(request, self.get_template_name(), context)

    def post(self, request):
        action = request.POST.get('action')
        employee_ids = request.POST.getlist('employee_ids')
        
        if not employee_ids:
            messages.error(request, "No employees selected")
            return redirect('employee_bulk_actions')
            
        try:
            employees = Employee.objects.filter(id__in=employee_ids)
            
            if action == 'update_department':
                department_id = request.POST.get('department')
                if department_id:
                    department = Department.objects.get(id=department_id)
                    employees.update(department=department)
                    messages.success(request, f"Updated department for {len(employees)} employees")
                    
            elif action == 'update_status':
                status = request.POST.get('status')
                if status in dict(Employee.EMPLOYMENT_STATUS):
                    employees.update(employment_status=status)
                    messages.success(request, f"Updated status for {len(employees)} employees")
                    
            elif action == 'deactivate':
                employees.update(is_active=False)
                User.objects.filter(employee_profile__in=employees).update(is_active=False)
                messages.success(request, f"Deactivated {len(employees)} employees")
                
            else:
                messages.error(request, "Invalid action")
                
        except Exception as e:
            logger.error(f"Bulk action error: {str(e)}")
            messages.error(request, "Error performing bulk action")
            
        return redirect('employee_bulk_actions')