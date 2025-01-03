# Standard library imports
import logging
from datetime import date, datetime
from calendar import monthrange

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
from django.core.exceptions import ValidationError
from django.utils.timezone import timedelta

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.models import Training, Department, EmployeeSkill, Employee
from hr_management.utils import get_template_path

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

class TrainingScheduleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('trainings/training_schedule.html', self.request.user.role, 'hr_management')

    def get(self, request):
        # Get current year and month
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        
        # Get first and last day of month
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        # Get all trainings for the month
        trainings = Training.objects.filter(
            (Q(start_date__range=[start_date, end_date]) | 
             Q(end_date__range=[start_date, end_date])) &
            Q(status__in=['PLANNED', 'IN_PROGRESS', 'COMPLETED'])
        )

        # Organize trainings by date
        calendar_data = {}
        current_date = start_date
        while current_date <= end_date:
            calendar_data[current_date] = []
            for training in trainings:
                if training.start_date <= current_date <= training.end_date:
                    calendar_data[current_date].append(training)
            current_date += timedelta(days=1)

        context = {
            'calendar_data': calendar_data,
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'prev_month': (datetime(year, month, 1) - timedelta(days=1)).strftime('%Y-%m'),
            'next_month': (datetime(year, month, last_day) + timedelta(days=1)).strftime('%Y-%m'),
            'today': timezone.now().date()
        }

        return render(request, self.get_template_name(), context)

class SkillMatrixView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('trainings/skill_matrix.html', self.request.user.role, 'hr_management')

    def get(self, request):
        department_id = request.GET.get('department')
        skill_filter = request.GET.get('skill')

        # Get all departments for filtering
        departments = Department.objects.filter(is_active=True)
        
        # Base queryset for employees
        employees = Employee.objects.filter(is_active=True).select_related('department')
        
        if department_id:
            employees = employees.filter(department_id=department_id)

        # Get all unique skills
        all_skills = EmployeeSkill.objects.values_list('skill_name', flat=True).distinct()
        
        # Create skill matrix data
        skill_matrix = []
        for employee in employees:
            skills = {skill.skill_name: skill.proficiency_level for skill in employee.skills.all()}
            
            # Filter by skill if specified
            if not skill_filter or skill_filter in skills:
                skill_matrix.append({
                    'employee': employee,
                    'skills': skills
                })

        context = {
            'departments': departments,
            'all_skills': all_skills,
            'skill_matrix': skill_matrix,
            'selected_department': department_id,
            'selected_skill': skill_filter
        }

        return render(request, self.get_template_name(), context)