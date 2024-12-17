from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
import logging
from django.db.models.functions import Coalesce
from django.db.models import FloatField, IntegerField

from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import (
    ClinicArea, ClinicStation, VisitType, ClinicVisit, VisitChecklist,
    VisitChecklistCompletion, WaitingList, ClinicDaySheet, StaffAssignment,
    ResourceAllocation, ClinicNotification, OperationalAlert, ClinicMetrics
)
from .utils import get_template_path

logger = logging.getLogger(__name__)

class ClinicManagementView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Clinic Management")
                return handler403(request, exception="Access denied to clinic management")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in clinic management dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing clinic management")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('dashboard/clinic_dashboard.html', request.user.role, 'clinic_management')
            context = self.get_context_data()
            
            # Handle pagination for visits
            if 'current_visits' in context:
                page = request.GET.get('page', 1)
                paginator = Paginator(context['current_visits'], 10)
                try:
                    visits_page = paginator.page(page)
                except (PageNotAnInteger, EmptyPage):
                    visits_page = paginator.page(1)
                context['current_visits'] = visits_page
                context['paginator'] = paginator

            return render(request, template_path, context)
        except Exception as e:
            logger.error(f"Error in clinic management view: {str(e)}")
            messages.error(request, "An error occurred while loading clinic data")
            return handler500(request, exception=str(e))

    def get_context_data(self):
        try:
            today = timezone.now().date()
            yesterday = today - timezone.timedelta(days=1)
            
            # Get current day sheet with default
            day_sheet = ClinicDaySheet.objects.filter(date=today).first() or {
                'date': today,
                'total_patients': 0,
                'total_appointments': 0,
                'total_walk_ins': 0
            }

            # Calculate metrics first
            metrics = {
                'total_visits': ClinicVisit.objects.filter(
                    registration_time__date=today
                ).count(),
                'completed_visits': ClinicVisit.objects.filter(
                    status='COMPLETED',
                    registration_time__date=today
                ).count(),
                'waiting_count': WaitingList.objects.filter(
                    status='WAITING'
                ).count(),
                'average_wait_time': WaitingList.objects.filter(
                    status='WAITING'
                ).aggregate(avg=Avg('estimated_wait_time'))['avg'] or 0
            }

            # Calculate yesterday's metrics for comparison
            yesterday_metrics = {
                'total_visits': ClinicVisit.objects.filter(
                    registration_time__date=yesterday
                ).count()
            }

            # Calculate growth percentage
            visit_growth = 0
            if yesterday_metrics['total_visits'] > 0:
                visit_growth = ((metrics['total_visits'] - yesterday_metrics['total_visits']) 
                              / yesterday_metrics['total_visits'] * 100)

            context = {
                'day_sheet': day_sheet,
                'metrics': metrics,
                'yesterday_metrics': yesterday_metrics,
                'visit_growth': round(visit_growth, 1),
                
                'current_visits': ClinicVisit.objects.select_related(
                    'patient', 'current_area'
                ).filter(
                    status__in=['REGISTERED', 'WAITING', 'IN_PROGRESS']
                ) or [],
                
                'waiting_lists': WaitingList.objects.select_related(
                    'area', 'visit'
                ).filter(status='WAITING').order_by('priority', 'join_time') or [],
                
                'staff_assignments': StaffAssignment.objects.select_related(
                    'staff', 'area'
                ).filter(
                    date=today,
                    status='IN_PROGRESS'
                ) or [],
                
                'area_stats': ClinicArea.objects.annotate(
                    current_patients=Count(
                        'current_visits',
                        filter=Q(current_visits__status__in=['WAITING', 'IN_PROGRESS']),
                        output_field=IntegerField()
                    ),
                    waiting_count=Count(
                        'waiting_list',
                        filter=Q(waiting_list__status='WAITING'),
                        output_field=IntegerField()
                    ),
                    avg_wait_time=Coalesce(
                        Avg('waiting_list__estimated_wait_time'),
                        0,
                        output_field=FloatField()
                    )
                ) or [],
                
                'active_alerts': OperationalAlert.objects.select_related('area').filter(
                    status='ACTIVE'
                ).order_by('-priority', '-created_at')[:5] or [],
                
                'priority_stats': ClinicVisit.objects.filter(
                    registration_time__date=today
                ).values('priority').annotate(
                    count=Count('id')
                ) or []
            }
            
            return context

        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            # Return comprehensive default context
            return {
                'day_sheet': {'date': timezone.now().date()},
                'metrics': {
                    'total_visits': 0,
                    'completed_visits': 0,
                    'waiting_count': 0,
                    'average_wait_time': 0
                },
                'yesterday_metrics': {'total_visits': 0},
                'visit_growth': 0,
                'current_visits': [],
                'waiting_lists': [],
                'staff_assignments': [],
                'area_stats': [],
                'active_alerts': [],
                'priority_stats': []
            }