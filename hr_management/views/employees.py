# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.models import Department, Employee, Document, Leave, TrainingParticipant, PerformanceReview
from hr_management.forms import EmployeeCreationForm, EmployeeEditForm
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

class EmployeeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Employee
    template_name = 'administrator/hr_management/employees/employee_detail.html'
    context_object_name = 'employee'
    permission_required = 'hr_management.view_employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        
        try:
            # Get documents with error handling
            documents = Document.objects.filter(employee=employee)
            context['documents'] = documents
            context['has_documents'] = documents.exists()
            
            # Get leaves with error handling
            leaves = Leave.objects.filter(employee=employee).order_by('-created_at')[:5]
            context['leaves'] = leaves
            context['has_leaves'] = leaves.exists()
            
            # Get trainings with error handling
            trainings = TrainingParticipant.objects.filter(employee=employee)
            context['trainings'] = trainings
            context['has_trainings'] = trainings.exists()
            
            # Get performance reviews with error handling
            performance_reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')[:3]
            context['performance_reviews'] = performance_reviews
            context['has_performance_reviews'] = performance_reviews.exists()
            
        except Exception as e:
            logger.error(f"Error fetching employee details for {employee.id}: {str(e)}")
            messages.error(self.request, "Some employee data could not be loaded")
        
        return context

class EmployeeEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'hr_management.change_employee'
    template_name = 'administrator/hr_management/employees/employee_edit.html'

    def get_employee(self, pk):
        return get_object_or_404(Employee, pk=pk)

    def get(self, request, pk):
        employee = self.get_employee(pk)
        form = EmployeeEditForm(instance=employee)
        return render(request, self.template_name, {
            'form': form,
            'employee': employee
        })

    def post(self, request, pk):
        employee = self.get_employee(pk)
        form = EmployeeEditForm(request.POST, instance=employee)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Employee details updated successfully")
                return redirect('employee_detail', pk=pk)
            except Exception as e:
                logger.error(f"Error updating employee {pk}: {str(e)}")
                messages.error(request, "Error updating employee details")
        
        return render(request, self.template_name, {
            'form': form,
            'employee': employee
        })