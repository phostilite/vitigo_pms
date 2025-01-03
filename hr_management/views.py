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

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .models import Employee, Department, Leave, Training, Grievance
from .forms import EmployeeCreationForm, DepartmentForm

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
        return get_template_path('dashboard/dashboard.html', self.request.user.role, 'hr_management')

    def get_dashboard_stats(self):
        """Get key statistics for HR dashboard"""
        try:
            from .models import Employee, Department, Leave, Training, Grievance
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
            from .models import Department
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
            from .models import Employee, Leave, Training, Grievance
            
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
            from .models import Leave
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

class LeaveListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('leaves/leave_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        type_filter = request.GET.get('type', '')

        leaves = Leave.objects.select_related(
            'employee__user', 
            'employee__department'
        ).all().order_by('-created_at')

        # Apply filters
        if search_query:
            leaves = leaves.filter(
                Q(employee__user__first_name__icontains=search_query) |
                Q(employee__user__last_name__icontains=search_query) |
                Q(employee__employee_id__icontains=search_query)
            )

        if status_filter:
            leaves = leaves.filter(status=status_filter)

        if type_filter:
            leaves = leaves.filter(leave_type=type_filter)

        # Pagination
        paginator = Paginator(leaves, 10)
        page = request.GET.get('page', 1)
        try:
            leaves_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            leaves_page = paginator.page(1)

        context = {
            'leaves': leaves_page,
            'search_query': search_query,
            'status_filter': status_filter,
            'type_filter': type_filter
        }

        return render(request, self.get_template_name(), context)

class TrainingListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('trainings/training_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date_filter', '')

        trainings = Training.objects.prefetch_related('participants').all()
        today = timezone.now().date()

        # Apply filters
        if search_query:
            trainings = trainings.filter(
                Q(title__icontains=search_query) |
                Q(trainer__icontains=search_query)
            )

        if status_filter:
            trainings = trainings.filter(status=status_filter)

        if date_filter:
            if date_filter == 'upcoming':
                trainings = trainings.filter(start_date__gt=today)
            elif date_filter == 'ongoing':
                trainings = trainings.filter(start_date__lte=today, end_date__gte=today)
            elif date_filter == 'past':
                trainings = trainings.filter(end_date__lt=today)

        # Ordering
        trainings = trainings.order_by('-start_date')

        # Pagination
        paginator = Paginator(trainings, 10)
        page = request.GET.get('page', 1)
        try:
            trainings_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            trainings_page = paginator.page(1)

        context = {
            'trainings': trainings_page,
            'search_query': search_query,
            'status_filter': status_filter,
            'date_filter': date_filter,
        }

        return render(request, self.get_template_name(), context)