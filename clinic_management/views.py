# Python standard library imports
import logging
from datetime import datetime, timedelta

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView, TemplateView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse

# Django database imports
from django.db import models
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, fields, Value, CharField, Case, When
from django.db.models.functions import ExtractHour, Cast

# Local/app imports
from access_control.utils import PermissionManager
from clinic_management.models import (
    ClinicChecklist,
    ClinicVisit,
    VisitChecklist,
    VisitStatus,
    VisitStatusLog,
)
from error_handling.views import handler403, handler500
from .utils import get_template_path
from .forms import NewVisitForm

# Initialize logger
logger = logging.getLogger(__name__)
User = get_user_model()

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
        today = timezone.localtime(timezone.now()).date()
        
        try:
            # Key Metrics
            context['active_visits_count'] = ClinicVisit.objects.filter(
                visit_date=today,
                current_status__name__in=['REGISTERED', 'WAITING', 'IN_PROGRESS', 'IN_WAITING', 'WITH_NURSE', 'WITH_DOCTOR']
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
            visit_statuses = VisitStatus.objects.filter(
                is_active=True
            ).order_by('order')
            
            status_list = []
            for status in visit_statuses:
                active_visits = ClinicVisit.objects.filter(
                    visit_date=today,
                    current_status=status
                ).count()
                
                status_list.append({
                    'display_name': status.display_name,
                    'color_code': status.color_code,
                    'active_visits': active_visits,
                    'order': status.order,
                    'is_active': status.is_active,
                })
            
            context['visit_statuses'] = status_list

            # Recent Activity Logs (with related data)
            recent_logs = VisitStatusLog.objects.select_related(
                'visit', 'status', 'changed_by'
            ).order_by('-timestamp')[:5]
            
            log_list = []
            for log in recent_logs:
                log_list.append({
                    'action': f"{log.changed_by.get_full_name()} changed {log.visit.visit_number} to {log.status.display_name}",
                    'timestamp': log.timestamp.strftime("%b %d, %Y %H:%M"),
                })
            
            context['recent_logs'] = log_list

            # Additional Statistics for Visit Status Distribution
            status_distribution = ClinicVisit.objects.filter(
                visit_date=today
            ).values(
                'current_status__name',
                'current_status__display_name'
            ).annotate(
                count=Count('id')
            ).order_by('current_status__order')
            
            context['visit_status_distribution'] = status_distribution

            # Checklist Completion Stats
            context['checklist_stats'] = self.get_checklist_completion_stats()
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            messages.error(self.request, "Error loading some dashboard data")
            # Provide empty defaults for required context
            context.update({
                'active_visits_count': 0,
                'active_checklists': 0,
                'status_types_count': 0,
                'completed_today': 0,
                'visit_statuses': [],
                'recent_logs': [],
                'visit_status_distribution': [],
                'checklist_stats': {'total': 0, 'completed': 0, 'completion_rate': 0}
            })

        return context

    def get_checklist_completion_stats(self):
        """Calculate checklist completion statistics"""
        try:
            today = timezone.localtime(timezone.now()).date()
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
            today = timezone.localtime(timezone.now()).date()
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


class ActiveVisitsView(LoginRequiredMixin, ListView):
    model = ClinicVisit
    context_object_name = 'visits'
    paginate_by = 10

    def get_template_names(self):
        try:
            return [get_template_path(
                'visits/active_visits.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/visits/active_visits.html']

    def get_queryset(self):
        # Get selected date from request, default to today
        selected_date = self.request.GET.get('visit_date')
        try:
            if selected_date:
                visit_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
            else:
                visit_date = timezone.localtime(timezone.now()).date()
        except ValueError:
            visit_date = timezone.localtime(timezone.now()).date()

        # Base queryset with active statuses and debug logging
        queryset = ClinicVisit.objects.filter(
            visit_date=visit_date,
            current_status__name__in=['REGISTERED', 'WAITING', 'IN_PROGRESS', 'IN_WAITING', 'WITH_NURSE', 'WITH_DOCTOR']
        ).select_related(
            'patient',
            'current_status'
        )

        # Add debug logging
        logger.debug(f"Selected date: {visit_date}")
        logger.debug(f"Current timezone: {timezone.get_current_timezone()}")
        logger.debug(f"Query parameters: {self.request.GET}")
        logger.debug(f"Total visits found: {queryset.count()}")
        logger.debug(f"Visit dates in DB: {list(ClinicVisit.objects.values_list('visit_date', flat=True))}")

        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(visit_number__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(current_status__name=status)

        return queryset.order_by('-registration_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Handle selected date
        selected_date = self.request.GET.get('visit_date')
        try:
            if (selected_date):
                context['selected_date'] = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
            else:
                context['selected_date'] = timezone.localtime(timezone.now()).date()
        except ValueError:
            context['selected_date'] = timezone.localtime(timezone.now()).date()

        # Add other context data
        context['active_statuses'] = VisitStatus.objects.filter(
            name__in=['REGISTERED', 'WAITING', 'IN_PROGRESS', 'IN_WAITING', 'WITH_NURSE', 'WITH_DOCTOR']
        )
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # Get count for each status for the selected date
        context['status_counts'] = ClinicVisit.objects.filter(
            visit_date=context['selected_date'],
            current_status__name__in=['REGISTERED', 'WAITING', 'IN_PROGRESS', 'IN_WAITING', 'WITH_NURSE', 'WITH_DOCTOR']
        ).values('current_status__name').annotate(count=Count('id'))
        
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Active Visits")
                return handler403(request, exception="Access denied to active visits")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in active visits dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing active visits")
            return handler500(request, exception=str(e))


class ActiveChecklistsView(LoginRequiredMixin, ListView):
    context_object_name = 'checklists'
    paginate_by = 10

    def get_template_names(self):
        try:
            return [get_template_path(
                'checklists/active_checklists.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/checklists/active_checklists.html']

    def get_queryset(self):
        try:
            # Get filter parameters
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            search_query = self.request.GET.get('search', '')

            # Base queryset
            queryset = ClinicChecklist.objects.filter(
                is_active=True
            ).annotate(
                items_count=Count('items'),
                completed_visits=Count(
                    'visitchecklist',
                    filter=Q(visitchecklist__completed_at__isnull=False)
                ),
                pending_visits=Count(
                    'visitchecklist',
                    filter=Q(visitchecklist__completed_at__isnull=True)
                )
            ).select_related()

            # Apply date filters if provided
            if date_from:
                try:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                    queryset = queryset.filter(visitchecklist__visit__visit_date__gte=date_from)
                except ValueError:
                    logger.error(f"Invalid date_from format: {date_from}")

            if date_to:
                try:
                    date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                    queryset = queryset.filter(visitchecklist__visit__visit_date__lte=date_to)
                except ValueError:
                    logger.error(f"Invalid date_to format: {date_to}")

            # Apply search filter if provided
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            return queryset.order_by('order', 'name')

        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return ClinicChecklist.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Add filter parameters to context
            context['date_from'] = self.request.GET.get('date_from', '')
            context['date_to'] = self.request.GET.get('date_to', '')
            context['search_query'] = self.request.GET.get('search', '')

            # Add summary statistics
            context['total_checklists'] = self.get_queryset().count()
            context['total_items'] = sum(checklist.items_count for checklist in self.get_queryset())
            context['completed_today'] = VisitChecklist.objects.filter(
                completed_at__date=timezone.now().date()
            ).count()

            # Add last 7 days completion stats
            context['weekly_stats'] = self.get_weekly_stats()

        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading some data")

        return context

    def get_weekly_stats(self):
        try:
            stats = []
            today = timezone.now().date()
            for i in range(7):
                date = today - timedelta(days=i)
                stats.append({
                    'date': date,
                    'completed': VisitChecklist.objects.filter(
                        completed_at__date=date
                    ).count()
                })
            return stats
        except Exception as e:
            logger.error(f"Error getting weekly stats: {str(e)}")
            return []

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Checklist Management")
                return handler403(request, exception="Access denied to checklist management")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in checklist management dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing checklist management")
            return handler500(request, exception=str(e))
        

class VisitStatusConfigView(LoginRequiredMixin, ListView):
    context_object_name = 'statuses'
    paginate_by = 10

    def get_template_names(self):
        try:
            return [get_template_path(
                'status/visit_status_config.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/status/visit_status_config.html']

    def get_queryset(self):
        try:
            # Get filter parameters
            search_query = self.request.GET.get('search', '')
            active_filter = self.request.GET.get('active', 'all')

            # Base queryset with corrected annotation
            queryset = VisitStatus.objects.annotate(
                active_visits=Count(
                    'visits',
                    filter=Q(
                        visits__visit_date=timezone.localtime(timezone.now()).date()
                    )
                )
            )

            # Apply filters
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(display_name__icontains=search_query)
                )

            if active_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif active_filter == 'inactive':
                queryset = queryset.filter(is_active=False)

            return queryset.order_by('order', 'name')

        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return VisitStatus.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Add filter parameters to context
            context['search_query'] = self.request.GET.get('search', '')
            context['active_filter'] = self.request.GET.get('active', 'all')

            # Add summary statistics
            context['total_statuses'] = VisitStatus.objects.count()
            context['active_statuses'] = VisitStatus.objects.filter(is_active=True).count()
            context['terminal_statuses'] = VisitStatus.objects.filter(is_terminal_state=True).count()

            # Get current usage statistics
            today = timezone.localtime(timezone.now()).date()
            context['status_usage'] = self.get_status_usage(today)

        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading some data")

        return context

    def get_status_usage(self, date):
        try:
            return VisitStatus.objects.filter(
                visits__visit_date=date
            ).annotate(
                visit_count=Count('visits')
            ).values('id', 'name', 'display_name', 'visit_count')
        except Exception as e:
            logger.error(f"Error getting status usage: {str(e)}")
            return []

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Status Configuration")
                return handler403(request, exception="Access denied to status configuration")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in status configuration dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing status configuration")
            return handler500(request, exception=str(e))
        

class CompletedVisitsReportView(LoginRequiredMixin, ListView):
    context_object_name = 'visits'
    paginate_by = 15

    def get_template_names(self):
        try:
            return [get_template_path(
                'reports/completed_visits.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/reports/completed_visits.html']

    def get_queryset(self):
        try:
            date = self.request.GET.get('date', timezone.localtime(timezone.now()).date())
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()

            priority = self.request.GET.get('priority')

            # Simplified queryset with straightforward duration calculation
            queryset = ClinicVisit.objects.filter(
                visit_date=date,
                current_status__name__in=['COMPLETED', 'CLOSED'],
                completion_time__isnull=False,
                registration_time__isnull=False
            ).select_related(
                'patient',
                'current_status'
            ).annotate(
                duration=F('completion_time') - F('registration_time')
            ).order_by('-completion_time')

            if priority:
                queryset = queryset.filter(priority=priority)

            return queryset

        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return ClinicVisit.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            date = self.request.GET.get('date', timezone.localtime(timezone.now()).date())
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()

            queryset = self.get_queryset()
            total_completed = queryset.count()

            # Calculate and format average duration
            avg_duration = queryset.aggregate(
                avg_duration=Avg(F('completion_time') - F('registration_time'))
            )['avg_duration']

            # Format the duration before adding to context
            formatted_duration = "No data"
            if avg_duration:
                # Convert to hours and minutes
                total_seconds = avg_duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                formatted_duration = f"{hours:02d}:{minutes:02d}"

            context.update({
                'total_completed': total_completed,
                'avg_duration': formatted_duration,
                'selected_date': date,
                'selected_priority': self.request.GET.get('priority'),
            })

            # Debug logging
            logger.debug(f"Total completed: {total_completed}")
            logger.debug(f"Raw avg duration: {avg_duration}")
            logger.debug(f"Formatted duration: {formatted_duration}")

        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading some report data")
            self.provide_default_context(context)

        return context

    def provide_default_context(self, context):
        """Provide default values for context in case of errors"""
        context.update({
            'total_completed': 0,
            'avg_duration': "00:00",
            'selected_date': timezone.localtime(timezone.now()).date(),
            'selected_priority': None,
        })

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Visit Reports")
                return handler403(request, exception="Access denied to visit reports")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in visit reports dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing visit reports")
            return handler500(request, exception=str(e))


class NewVisitView(LoginRequiredMixin, CreateView):
    form_class = NewVisitForm
    success_url = reverse_lazy('clinic_management:active_visits')

    def get_template_names(self):
        try:
            return [get_template_path(
                'visits/new_visit.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/visits/new_visit.html']

    def form_valid(self, form):
        try:
            # Set the created_by field to current user
            form.instance.created_by = self.request.user
            
            # Set the initial status
            if form.initial_status:
                form.instance.current_status = form.initial_status
            else:
                messages.warning(self.request, "Default status 'REGISTERED' not found. Please check status configuration.")
                return super().form_invalid(form)

            response = super().form_valid(form)

            # Create initial status log entry
            VisitStatusLog.objects.create(
                visit=self.object,
                status=self.object.current_status,
                changed_by=self.request.user,
                notes="Initial visit registration"
            )

            messages.success(self.request, f"Visit {self.object.visit_number} created successfully.")
            return response

        except Exception as e:
            logger.error(f"Error creating new visit: {str(e)}")
            messages.error(self.request, "An error occurred while creating the visit.")
            return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to create new visits")
                logger.warning(f"User {request.user} attempted to access new visit creation without permission")
                return handler403(request, exception="Access denied to create visits")

            # Add session tracking for audit purposes
            request.session['last_visit_action'] = 'new_visit_form'
            request.session['visit_form_access_time'] = timezone.now().isoformat()

            return super().dispatch(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in new visit dispatch: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while accessing new visit form")
            return handler500(request, exception=str(e))


class AllVisitsView(LoginRequiredMixin, ListView):
    model = ClinicVisit
    context_object_name = 'visits'
    paginate_by = 15

    def get_template_names(self):
        try:
            return [get_template_path(
                'visits/all_visits.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/visits/all_visits.html']

    def get_queryset(self):
        # Get selected date range from request
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # Base queryset
        queryset = ClinicVisit.objects.select_related(
            'patient',
            'current_status',
            'created_by'
        )

        # Apply date filters
        try:
            if date_from:
                queryset = queryset.filter(visit_date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
            if date_to:
                queryset = queryset.filter(visit_date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError as e:
            logger.error(f"Date parsing error: {str(e)}")

        # Apply search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(visit_number__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(current_status__name=status)

        # Priority filter
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by('-visit_date', '-registration_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Add filter values to context
            context.update({
                'date_from': self.request.GET.get('date_from', ''),
                'date_to': self.request.GET.get('date_to', ''),
                'search_query': self.request.GET.get('search', ''),
                'current_status': self.request.GET.get('status', ''),
                'current_priority': self.request.GET.get('priority', ''),
                
                # Add all possible statuses for filter
                'all_statuses': VisitStatus.objects.filter(is_active=True),
                
                # Add priority choices
                'priority_choices': ClinicVisit.PRIORITY_CHOICES,
                
                # Add summary statistics
                'total_visits': self.get_queryset().count(),
                'completed_visits': self.get_queryset().filter(
                    current_status__name='COMPLETED'
                ).count(),
                'status_distribution': self.get_status_distribution()
            })
            
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading some data")
            
        return context

    def get_status_distribution(self):
        """Get count of visits grouped by status"""
        try:
            return self.get_queryset().values(
                'current_status__name',
                'current_status__display_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
        except Exception as e:
            logger.error(f"Error getting status distribution: {str(e)}")
            return []

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access All Visits")
                return handler403(request, exception="Access denied to all visits")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in all visits dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing all visits")
            return handler500(request, exception=str(e))


class VisitLogsView(LoginRequiredMixin, ListView):
    context_object_name = 'logs'
    paginate_by = 20

    def get_template_names(self):
        try:
            return [get_template_path(
                'visits/visit_logs.html',
                self.request.user.role,
                'clinic_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['administrator/clinic_management/visits/visit_logs.html']

    def get_queryset(self):
        # Get filter parameters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        visit_number = self.request.GET.get('visit_number')
        status = self.request.GET.get('status')

        # Base queryset with related data
        queryset = VisitStatusLog.objects.select_related(
            'visit', 
            'status', 
            'changed_by',
            'visit__patient'
        ).order_by('-timestamp')

        # Apply filters
        try:
            if date_from:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=date_from)
            
            if date_to:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=date_to)

            if visit_number:
                queryset = queryset.filter(visit__visit_number__icontains=visit_number)

            if status:
                queryset = queryset.filter(status__name=status)

        except ValueError as e:
            logger.error(f"Date parsing error: {str(e)}")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context.update({
                'date_from': self.request.GET.get('date_from', ''),
                'date_to': self.request.GET.get('date_to', ''),
                'visit_number': self.request.GET.get('visit_number', ''),
                'selected_status': self.request.GET.get('status', ''),
                
                # Add all statuses for filter
                'all_statuses': VisitStatus.objects.filter(is_active=True),
                
                # Add summary statistics
                'total_logs': self.get_queryset().count(),
                'today_logs': self.get_queryset().filter(
                    timestamp__date=timezone.now().date()
                ).count(),
                'status_changes': self.get_status_change_stats()
            })
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading some data")
            
        return context

    def get_status_change_stats(self):
        """Get statistics about status changes"""
        try:
            today = timezone.now().date()
            return self.get_queryset().filter(
                timestamp__date=today
            ).values(
                'status__name',
                'status__display_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
        except Exception as e:
            logger.error(f"Error getting status change stats: {str(e)}")
            return []

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'clinic_management'):
                messages.error(request, "You don't have permission to access Visit Logs")
                return handler403(request, exception="Access denied to visit logs")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in visit logs dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing visit logs")
            return handler500(request, exception=str(e))