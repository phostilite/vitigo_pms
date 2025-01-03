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
from hr_management.models import Leave
from hr_management.utils import get_template_path

from datetime import datetime, timedelta
from calendar import monthrange

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

class PendingLeaveRequestsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('leaves/pending_requests.html', self.request.user.role, 'hr_management')

    def get(self, request):
        pending_leaves = Leave.objects.select_related(
            'employee__user', 
            'employee__department'
        ).filter(status='PENDING').order_by('-created_at')

        # Get pending count for badge
        pending_count = pending_leaves.count()

        context = {
            'pending_leaves': pending_leaves,
            'pending_count': pending_count
        }

        return render(request, self.get_template_name(), context)

class LeaveCalendarView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('leaves/leave_calendar.html', self.request.user.role, 'hr_management')

    def get(self, request):
        # Get current year and month
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        
        # Get first and last day of month
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        # Get all leaves for the month
        leaves = Leave.objects.select_related(
            'employee__user'
        ).filter(
            (Q(start_date__range=[start_date, end_date]) | 
             Q(end_date__range=[start_date, end_date])) &
            Q(status__in=['APPROVED', 'PENDING'])
        )

        # Organize leaves by date
        calendar_data = {}
        current_date = start_date
        while current_date <= end_date:
            calendar_data[current_date] = []
            for leave in leaves:
                if leave.start_date <= current_date <= leave.end_date:
                    calendar_data[current_date].append(leave)
            current_date += timedelta(days=1)

        context = {
            'calendar_data': calendar_data,
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'prev_month': (datetime(year, month, 1) - timedelta(days=1)).strftime('%Y-%m'),
            'next_month': (datetime(year, month, last_day) + timedelta(days=1)).strftime('%Y-%m'),
        }

        return render(request, self.get_template_name(), context)