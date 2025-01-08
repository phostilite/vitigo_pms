# Standard library imports
import logging
from datetime import timedelta

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from ..models import MaintenanceSchedule
from ..utils import get_template_path
from ..forms import MaintenanceScheduleForm

# Initialize logger
logger = logging.getLogger(__name__)

class MaintenanceScheduleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'asset_management')

    def get_template_name(self):
        return get_template_path('maintenance/maintenance_schedule.html', self.request.user.role, 'asset_management')

    def get(self, request):
        try:
            # Get filter parameters
            search_query = request.GET.get('search', '')
            status = request.GET.get('status', '')
            priority = request.GET.get('priority', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')

            # Base queryset
            schedules = MaintenanceSchedule.objects.select_related('asset').order_by('scheduled_date')

            # Apply filters
            if search_query:
                schedules = schedules.filter(
                    Q(asset__name__icontains=search_query) |
                    Q(asset__asset_id__icontains=search_query) |
                    Q(maintenance_type__icontains=search_query)
                )
            if status:
                schedules = schedules.filter(status=status)
            if priority:
                schedules = schedules.filter(priority=priority)
            if date_from:
                schedules = schedules.filter(scheduled_date__gte=date_from)
            if date_to:
                schedules = schedules.filter(scheduled_date__lte=date_to)

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(schedules, 10)
            try:
                schedules = paginator.page(page)
            except PageNotAnInteger:
                schedules = paginator.page(1)
            except EmptyPage:
                schedules = paginator.page(paginator.num_pages)

            context = {
                'schedules': schedules,
                'search_query': search_query,
                'selected_status': status,
                'selected_priority': priority,
                'date_from': date_from,
                'date_to': date_to,
                'status_choices': MaintenanceSchedule.STATUS_CHOICES,
                'priority_choices': MaintenanceSchedule.PRIORITY_CHOICES,
                'has_filters': bool(search_query or status or priority or date_from or date_to),
            }

            return render(request, self.get_template_name(), context)
        except Exception as e:
            logger.error(f"Error in maintenance schedule view: {str(e)}")
            messages.error(request, "An error occurred while loading maintenance schedules")
            return redirect('asset_dashboard')

class CreateMaintenanceScheduleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'asset_management')

    def get(self, request):
        form = MaintenanceScheduleForm()
        return render(request, 'administrator/asset_management/maintenance/maintenance_schedule_form.html', {
            'form': form
        })

    def post(self, request):
        form = MaintenanceScheduleForm(request.POST)
        if form.is_valid():
            try:
                maintenance = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Maintenance scheduled successfully',
                    'data': {
                        'id': maintenance.id,
                        'asset': maintenance.asset.name,
                        'scheduled_date': maintenance.scheduled_date.strftime('%Y-%m-%d')
                    }
                })
            except Exception as e:
                logger.error(f"Error creating maintenance schedule: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to schedule maintenance'
                }, status=500)
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid form data',
            'errors': form.errors
        }, status=400)