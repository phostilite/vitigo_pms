# Standard library imports
from datetime import datetime, timedelta
from collections import defaultdict

# Django imports
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Max, Q, Sum, F, ExpressionWrapper, DurationField
from django.db import models
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
            
            # Recent Activities
            context.update(self.get_recent_activities())

            # Staff Status
            context.update(self.get_staff_status(today))

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
            # Get active areas and their current utilization
            areas = ClinicArea.objects.filter(is_active=True).annotate(
                current_patients=models.Count('current_visits'),
                station_count=models.Count('stations'),
                occupied_stations=models.Count(
                    'stations',
                    filter=models.Q(stations__current_status='OCCUPIED')
                )
            )

            # Calculate basic metrics
            resources = [
                {
                    'area_name': area.name,
                    'capacity': area.capacity,
                    'current_patients': area.current_patients,
                    'utilization_percent': (area.current_patients / area.capacity * 100) if area.capacity > 0 else 0,
                    'available_stations': area.station_count - area.occupied_stations
                }
                for area in areas
            ]

            return {
                'resources': resources,
                'total_capacity': sum(area.capacity for area in areas),
                'total_current': sum(area.current_patients for area in areas),
            }
        except Exception as e:
            logger.error(f"Error getting resource utilization: {str(e)}")
            return {
                'resources': [],
                'total_capacity': 0,
                'total_current': 0
            }

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
        """Get financial summary data for the dashboard"""
        try:
            # Get all transactions for today
            today_transactions = VisitPaymentTransaction.objects.filter(
                processed_at__date=today
            )
            
            # Calculate total revenue and growth
            total_revenue = today_transactions.filter(
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            yesterday = today - timedelta(days=1)
            yesterday_revenue = VisitPaymentTransaction.objects.filter(
                processed_at__date=yesterday,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            revenue_growth = round(((total_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0, 1)
            revenue_target_percentage = round((total_revenue / 50000) * 100, 1)  # Example: Daily target of 50,000
            
            # Pending payments analysis
            pending_transactions = VisitPaymentTransaction.objects.filter(status='PENDING')
            pending_payments = pending_transactions.aggregate(total=Sum('amount'))['total'] or 0
            pending_count = pending_transactions.count()
            
            # Aging analysis
            overdue_transactions = pending_transactions.filter(processed_at__date__lt=today)
            overdue_amount = overdue_transactions.aggregate(total=Sum('amount'))['total'] or 0
            due_today_amount = pending_transactions.filter(processed_at__date=today).aggregate(total=Sum('amount'))['total'] or 0
            
            # Today's collections by payment method
            collections = today_transactions.filter(status='COMPLETED')
            today_collections = collections.aggregate(total=Sum('amount'))['total'] or 0
            cash_collections = collections.filter(payment_method='CASH').aggregate(total=Sum('amount'))['total'] or 0
            online_collections = collections.filter(payment_method='UPI').aggregate(total=Sum('amount'))['total'] or 0
            card_collections = collections.filter(payment_method='CARD').aggregate(total=Sum('amount'))['total'] or 0
            
            # Outstanding balance aging
            thirty_days_ago = today - timedelta(days=30)
            sixty_days_ago = today - timedelta(days=60)
            ninety_days_ago = today - timedelta(days=90)
            
            aging_30_days = pending_transactions.filter(
                processed_at__date__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            aging_60_days = pending_transactions.filter(
                processed_at__date__gte=sixty_days_ago,
                processed_at__date__lt=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            aging_90_days = pending_transactions.filter(
                processed_at__date__lt=sixty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            outstanding_balance = aging_30_days + aging_60_days + aging_90_days
            
            # Recent transactions
            recent_transactions = VisitPaymentTransaction.objects.select_related(
                'visit__patient'
            ).order_by('-processed_at')[:5]
            
            formatted_transactions = [{
                'id': t.id,
                'patient_name': t.visit.patient.get_full_name(),
                'service': t.visit.visit_type.name,
                'amount': t.amount,
                'status': t.status,
                'date': t.processed_at.strftime('%Y-%m-%d %H:%M')
            } for t in recent_transactions]

            return {
                'total_revenue': total_revenue,
                'revenue_growth': revenue_growth,
                'revenue_target_percentage': revenue_target_percentage,
                'pending_payments': pending_payments,
                'pending_count': pending_count,
                'overdue_amount': overdue_amount,
                'due_today_amount': due_today_amount,
                'today_collections': today_collections,
                'cash_collections': cash_collections,
                'online_collections': online_collections,
                'card_collections': card_collections,
                'outstanding_balance': outstanding_balance,
                'aging_30_days': aging_30_days,
                'aging_60_days': aging_60_days,
                'aging_90_days': aging_90_days,
                'recent_transactions': formatted_transactions,
                'last_updated': timezone.now().strftime('%H:%M')
            }
            
        except Exception as e:
            logger.error(f"Error getting financial overview: {str(e)}")
            return {
                'total_revenue': 0,
                'revenue_growth': 0,
                'revenue_target_percentage': 0,
                'pending_payments': 0,
                'pending_count': 0,
                'overdue_amount': 0,
                'due_today_amount': 0,
                'today_collections': 0,
                'cash_collections': 0,
                'online_collections': 0,
                'card_collections': 0,
                'outstanding_balance': 0,
                'aging_30_days': 0,
                'aging_60_days': 0,
                'aging_90_days': 0,
                'recent_transactions': [],
                'last_updated': timezone.now().strftime('%H:%M')
            }

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
        """Get performance metrics for the dashboard"""
        try:
            # Get metrics from ClinicMetrics model
            today_metrics = ClinicMetrics.objects.filter(date=today)
            yesterday = today - timedelta(days=1)
            yesterday_metrics = ClinicMetrics.objects.filter(date=yesterday)

            # Calculate satisfaction rate
            satisfaction_rate = 85  # Example: Could be calculated from patient feedback
            previous_satisfaction = 82.5

            # Calculate wait times
            avg_wait_time = today_metrics.aggregate(
                avg=Avg('avg_wait_time')
            )['avg'] or 0
            previous_wait_time = yesterday_metrics.aggregate(
                avg=Avg('avg_wait_time')
            )['avg'] or 0
            wait_time_percentage = min((avg_wait_time / 30) * 100, 100)  # Based on 30-minute target
            wait_time_trend = '↓ {}m'.format(round(previous_wait_time - avg_wait_time, 1)) if previous_wait_time > avg_wait_time else '↑ {}m'.format(round(avg_wait_time - previous_wait_time, 1))

            # Calculate efficiency metrics
            resource_efficiency = today_metrics.aggregate(
                avg=Avg('capacity_utilization')
            )['avg'] or 0

            # Calculate staff productivity
            completed_visits = ClinicVisit.objects.filter(
                status='COMPLETED',
                end_time__date=today
            ).count()
            active_staff = StaffAssignment.objects.filter(
                date=today,
                status='IN_PROGRESS'
            ).count()
            staff_productivity = (completed_visits / active_staff * 100) if active_staff > 0 else 0

            # Calculate patient flow metrics
            current_hour = timezone.now().hour
            visits_today = ClinicVisit.objects.filter(
                registration_time__date=today
            ).count()
            patient_flow_rate = round(visits_today / (current_hour + 1) if current_hour > 0 else visits_today)
            flow_rate_percentage = min((patient_flow_rate / 10) * 100, 100)  # Based on target of 10 patients/hour

            # Calculate key statistics
            completed_consultations = ClinicVisit.objects.filter(
                status='COMPLETED',
                end_time__date=today
            ).count()
            
            total_scheduled = ClinicVisit.objects.filter(
                registration_time__date=today
            ).count()
            no_shows = ClinicVisit.objects.filter(
                status='NO_SHOW',
                registration_time__date=today
            ).count()
            no_show_rate = round((no_shows / total_scheduled * 100) if total_scheduled > 0 else 0, 1)

            # Calculate revenue metrics
            total_revenue = VisitPaymentTransaction.objects.filter(
                status='COMPLETED',
                processed_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_per_patient = round(total_revenue / completed_consultations if completed_consultations > 0 else 0)

            return {
                'satisfaction_rate': round(satisfaction_rate, 1),
                'previous_satisfaction': round(previous_satisfaction, 1),
                'avg_wait_time': round(avg_wait_time),
                'previous_wait_time': round(previous_wait_time),
                'wait_time_percentage': round(wait_time_percentage),
                'wait_time_trend': wait_time_trend,
                'resource_efficiency': round(resource_efficiency),
                'staff_productivity': round(staff_productivity),
                'patient_flow_rate': patient_flow_rate,
                'flow_rate_percentage': round(flow_rate_percentage),
                'completed_consultations': completed_consultations,
                'no_show_rate': no_show_rate,
                'revenue_per_patient': revenue_per_patient,
                'last_updated': timezone.now().strftime('%H:%M')
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                'satisfaction_rate': 0,
                'previous_satisfaction': 0,
                'avg_wait_time': 0,
                'previous_wait_time': 0,
                'wait_time_percentage': 0,
                'wait_time_trend': '0m',
                'resource_efficiency': 0,
                'staff_productivity': 0,
                'patient_flow_rate': 0,
                'flow_rate_percentage': 0,
                'completed_consultations': 0,
                'no_show_rate': 0,
                'revenue_per_patient': 0,
                'last_updated': timezone.now().strftime('%H:%M')
            }

    def get_recent_activities(self):
        try:
            today = timezone.now().date()
            
            # Get basic metrics for today
            context = {
                'today_checkins': ClinicVisit.objects.filter(
                    registration_time__date=today
                ).count(),
                'active_consultations': ClinicVisit.objects.filter(
                    status='IN_PROGRESS'
                ).count(),
                'completed_today': ClinicVisit.objects.filter(
                    status='COMPLETED',
                    end_time__date=today
                ).count()
            }
            
            # Get last 10 activities
            activities = ClinicVisit.objects.filter(
                registration_time__date=today
            ).select_related(
                'patient', 'current_area'
            ).order_by('-registration_time')[:10]
            
            # Format activities for display
            context['recent_activities'] = [{
                'time': activity.registration_time,
                'patient_name': activity.patient.get_full_name(),
                'description': f"{activity.visit_type.name} Visit",
                'location': activity.current_area.name if activity.current_area else 'Reception',
                'status': activity.status
            } for activity in activities]
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {str(e)}")
            return {
                'today_checkins': 0,
                'active_consultations': 0,
                'completed_today': 0,
                'recent_activities': []
            }

    def get_staff_status(self, today):
        """Get simplified staff status for the dashboard"""
        try:
            # Get active staff assignments for today
            active_assignments = StaffAssignment.objects.filter(
                date=today,
                status='IN_PROGRESS'
            ).select_related('staff', 'staff__role', 'area')

            # Get limited numbers of doctors and staff
            active_doctors = [{
                'name': assignment.staff.get_full_name(),
                'status': 'BUSY' if assignment.status == 'IN_PROGRESS' else 'AVAILABLE',
                'specialization': assignment.staff.role.name,
                'location': assignment.area.name,
            } for assignment in active_assignments.filter(
                staff__role__name='DOCTOR'
            )[:3]]  # Limit to 3 doctors

            support_staff = [{
                'name': assignment.staff.get_full_name(),
                'status': 'BUSY' if assignment.status == 'IN_PROGRESS' else 'AVAILABLE',
                'role': assignment.staff.role.name,
            } for assignment in active_assignments.filter(
                ~Q(staff__role__name='DOCTOR')
            )[:4]]  # Limit to 4 support staff

            # Get total counts for summary
            total_doctors = active_assignments.filter(staff__role__name='DOCTOR').count()
            total_support = active_assignments.filter(~Q(staff__role__name='DOCTOR')).count()

            return {
                'total_staff_on_duty': total_doctors + total_support,
                'total_doctors': total_doctors,
                'total_staff': total_support,
                'active_doctors': active_doctors,
                'support_staff': support_staff,
                'more_doctors': total_doctors > 3,  # Flag if there are more doctors
                'more_staff': total_support > 4,    # Flag if there are more staff
                'remaining_doctors': total_doctors - 3 if total_doctors > 3 else 0,
                'remaining_staff': total_support - 4 if total_support > 4 else 0
            }

        except Exception as e:
            logger.error(f"Error getting staff status: {str(e)}")
            return {
                'total_staff_on_duty': 0,
                'total_doctors': 0,
                'total_staff': 0,
                'active_doctors': [],
                'support_staff': [],
                'more_doctors': False,
                'more_staff': False,
                'remaining_doctors': 0,
                'remaining_staff': 0
            }

    def get_time_ago(self, timestamp):
        """Helper method to format time difference in a human-readable format"""
        now = timezone.now()
        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"

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