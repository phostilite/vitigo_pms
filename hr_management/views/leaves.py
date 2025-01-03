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