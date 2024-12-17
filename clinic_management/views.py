# Standard library imports
from datetime import datetime, timedelta
from collections import defaultdict

# Django imports
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Max, Q, Sum, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.contrib import messages
from django.db import transaction

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from .models import (
    ClinicVisit, ClinicArea, ClinicStation, VisitType,
    ClinicFlow, WaitingList, ClinicDaySheet, 
    StaffAssignment, OperationalAlert, ClinicMetrics,
    PaymentTerminal, VisitPaymentTransaction
)
from .utils import get_template_path
from .dashboard_components.get_quick_stats import get_quick_stats
from user_management.models import CustomUser
import logging

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            today = timezone.now().date()
            
            # Quick Statistics
            context.update(get_quick_stats(today))
            
            # Current Clinic Status
            context.update(self.get_clinic_status())
            
            # Visit Analytics
            context.update(self.get_visit_analytics(today))
            
            # Waiting List Information
            context.update(self.get_waiting_list_info())
            
            # Resource Utilization
            context.update(self.get_resource_utilization())
            
            # Staff Assignments
            context.update(self.get_staff_assignments(today))
            
            # Financial Overview
            context.update(self.get_financial_overview(today))
            
            # Alerts and Notifications
            context.update(self.get_alerts_and_notifications())
            
            # Performance Metrics
            context.update(self.get_performance_metrics(today))

        except Exception as e:
            logger.error(f"Error getting clinic dashboard context: {str(e)}")
            messages.error(self.request, "Some dashboard data may be incomplete")
            
        return context

    def get_clinic_status(self):
        try:
            areas = ClinicArea.objects.filter(is_active=True)
            area_status = []
            
            for area in areas:
                area_status.append({
                    'name': area.name,
                    'current_capacity': area.current_visits.count(),
                    'max_capacity': area.capacity,
                    'utilization': (area.current_visits.count() / area.capacity * 100) if area.capacity > 0 else 0,
                    'available_stations': area.stations.filter(
                        current_status='AVAILABLE'
                    ).count()
                })
                
            return {
                'area_status': area_status,
                'total_active_stations': ClinicStation.objects.filter(
                    is_active=True
                ).count(),
                'occupied_stations': ClinicStation.objects.filter(
                    current_status='OCCUPIED'
                ).count()
            }
        except Exception as e:
            logger.error(f"Error getting clinic status: {str(e)}")
            return {}

    def get_visit_analytics(self, today):
        try:
            visit_types = VisitType.objects.filter(is_active=True)
            visit_distribution = []
            
            for visit_type in visit_types:
                visit_distribution.append({
                    'type': visit_type.name,
                    'count': ClinicVisit.objects.filter(
                        visit_type=visit_type,
                        registration_time__date=today
                    ).count()
                })
            
            return {
                'visit_distribution': visit_distribution,
                'priority_distribution': {
                    'high': ClinicVisit.objects.filter(
                        priority='A',
                        registration_time__date=today
                    ).count(),
                    'medium': ClinicVisit.objects.filter(
                        priority='B',
                        registration_time__date=today
                    ).count(),
                    'low': ClinicVisit.objects.filter(
                        priority='C',
                        registration_time__date=today
                    ).count()
                }
            }
        except Exception as e:
            logger.error(f"Error getting visit analytics: {str(e)}")
            return {}

    def get_waiting_list_info(self):
        try:
            waiting_lists = WaitingList.objects.filter(
                status='WAITING'
            ).select_related(
                'area',
                'visit',
                'visit__patient'
            ).order_by('priority', 'join_time')

            # Format queue data for the template
            queue = []
            for waiting in waiting_lists:
                queue.append({
                    'token_number': f"{waiting.priority}{waiting.id}",  # Format: A123, B456, etc.
                    'priority': waiting.priority,
                    'name': waiting.visit.patient.get_full_name(),
                    'id': waiting.visit.patient.id,
                    'profile_picture': waiting.visit.patient.profile_picture if hasattr(waiting.visit.patient, 'profile_picture') else None,
                    'visit_type': waiting.visit.visit_type.name,
                    'status': waiting.status,
                    'wait_time': int((timezone.now() - waiting.join_time).total_seconds() / 60),  # in minutes
                    'area': waiting.area.name
                })

            # Calculate average wait time
            if queue:
                avg_wait_time = sum(item['wait_time'] for item in queue) / len(queue)
            else:
                avg_wait_time = 0

            # Count high priority patients
            high_priority_count = sum(1 for item in queue if item['priority'] == 'A')

            return {
                'queue': queue,
                'avg_wait_time': round(avg_wait_time, 1),
                'high_priority_count': high_priority_count,
                'total_waiting': len(queue)
            }
        except Exception as e:
            logger.error(f"Error getting waiting list info: {str(e)}")
            return {
                'queue': [],
                'avg_wait_time': 0,
                'high_priority_count': 0,
                'total_waiting': 0
            }

    def get_resource_utilization(self):
        try:
            return {
                'room_utilization': self.calculate_resource_utilization('ROOM'),
                'equipment_utilization': self.calculate_resource_utilization('EQUIPMENT'),
                'staff_utilization': self.calculate_resource_utilization('STAFF')
            }
        except Exception as e:
            logger.error(f"Error getting resource utilization: {str(e)}")
            return {}

    def get_staff_assignments(self, today):
        try:
            assignments = StaffAssignment.objects.filter(
                date=today,
                status__in=['SCHEDULED', 'IN_PROGRESS']
            ).select_related('staff', 'area', 'station')
            
            return {
                'current_assignments': assignments,
                'staff_coverage': self.calculate_staff_coverage(assignments),
                'unassigned_areas': ClinicArea.objects.filter(
                    is_active=True
                ).exclude(id__in=assignments.values_list('area', flat=True))
            }
        except Exception as e:
            logger.error(f"Error getting staff assignments: {str(e)}")
            return {}

    def get_financial_overview(self, today):
        try:
            transactions = VisitPaymentTransaction.objects.filter(
                processed_at__date=today
            )
            
            return {
                'total_revenue': transactions.filter(
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'payment_methods': self.get_payment_method_breakdown(transactions),
                'terminal_status': self.get_terminal_status(),
                'pending_payments': transactions.filter(
                    status='PENDING'
                ).count()
            }
        except Exception as e:
            logger.error(f"Error getting financial overview: {str(e)}")
            return {}

    def get_alerts_and_notifications(self):
        try:
            return {
                'active_alerts': OperationalAlert.objects.filter(
                    status='ACTIVE'
                ).order_by('-priority', '-created_at'),
                'recent_notifications': self.get_recent_notifications(),
                'system_warnings': self.get_system_warnings()
            }
        except Exception as e:
            logger.error(f"Error getting alerts and notifications: {str(e)}")
            return {}

    def get_performance_metrics(self, today):
        try:
            metrics = ClinicMetrics.objects.filter(date=today)
            
            return {
                'daily_metrics': metrics,
                'performance_indicators': self.calculate_performance_indicators(metrics),
                'efficiency_scores': self.calculate_efficiency_scores(today)
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

    # Helper methods
    def calculate_resource_utilization(self, resource_type):
        # Implementation for calculating resource utilization
        pass

    def calculate_staff_coverage(self, assignments):
        # Implementation for calculating staff coverage
        pass

    def get_payment_method_breakdown(self, transactions):
        # Implementation for getting payment method breakdown
        pass

    def get_terminal_status(self):
        # Implementation for getting terminal status
        pass

    def get_recent_notifications(self):
        # Implementation for getting recent notifications
        pass

    def get_system_warnings(self):
        # Implementation for getting system warnings
        pass

    def calculate_performance_indicators(self, metrics):
        # Implementation for calculating performance indicators
        pass

    def calculate_efficiency_scores(self, date):
        # Implementation for calculating efficiency scores
        pass