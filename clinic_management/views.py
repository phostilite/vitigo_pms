import logging
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count
from datetime import datetime, timedelta
from .utils import get_template_path
from django.db.models import Q

from clinic_management.models import ClinicVisit, VisitStatus, VisitStatusLog, ClinicChecklist, VisitChecklist
from access_control.utils import PermissionManager
from error_handling.views import handler403, handler500

logger = logging.getLogger(__name__)

class ClinicManagementDashboardView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        try:
            return [get_template_path(
                'dashboard/clinic_dashboard.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/dashboard/clinic_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        try:
            # Key Metrics
            context['active_visits_count'] = ClinicVisit.objects.filter(
                visit_date=today,
                current_status__name__in=['REGISTERED', 'IN_WAITING', 'WITH_NURSE', 'WITH_DOCTOR']
            ).count()
            
            context['active_checklists'] = ClinicChecklist.objects.filter(
                is_active=True
            ).count()
            
            context['status_types_count'] = VisitStatus.objects.filter(
                is_active=True
            ).count()
            
            context['completed_today'] = ClinicVisit.objects.filter(
                visit_date=today,
                current_status__name='COMPLETED'
            ).count()

            # Status Management
            context['visit_statuses'] = VisitStatus.objects.filter(
                is_active=True
            ).order_by('order').annotate(
                active_visits=Count('visits', filter=Q(visits__visit_date=today))
            )

            # Recent Activity Logs
            context['recent_logs'] = VisitStatusLog.objects.select_related(
                'visit', 'status', 'changed_by'
            ).order_by('-timestamp')[:5]

            # Additional Statistics
            context['checklist_completion_stats'] = self.get_checklist_completion_stats()
            context['visit_status_distribution'] = self.get_visit_status_distribution()
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            messages.error(self.request, "Error loading some dashboard data")

        return context

    def get_checklist_completion_stats(self):
        """Calculate checklist completion statistics"""
        try:
            today = timezone.now().date()
            total_checklists = VisitChecklist.objects.filter(
                visit__visit_date=today
            ).count()
            
            completed_checklists = VisitChecklist.objects.filter(
                visit__visit_date=today
            ).annotate(
                items_completed=Count('items', filter=Q(items__is_completed=True))
            ).filter(items_completed__gt=0).count()
            
            return {
                'total': total_checklists,
                'completed': completed_checklists,
                'completion_rate': (completed_checklists / total_checklists * 100) if total_checklists > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating checklist stats: {str(e)}")
            return {'total': 0, 'completed': 0, 'completion_rate': 0}

    def get_visit_status_distribution(self):
        """Get distribution of visits across different statuses"""
        try:
            today = timezone.now().date()
            return ClinicVisit.objects.filter(
                visit_date=today
            ).values(
                'current_status__name',
                'current_status__display_name'
            ).annotate(
                count=Count('id')
            ).order_by('current_status__order')
        except Exception as e:
            logger.error(f"Error calculating visit distribution: {str(e)}")
            return []

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
