# Standard library imports
import logging
from datetime import timedelta

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from patient_management.models import Patient
from .models import (
    PhototherapyDevice,
    PhototherapyPlan, 
    PhototherapyProtocol,
    PhototherapySession,
    PhototherapyType,
    PhototherapyPayment,
    HomePhototherapyLog,
    PatientRFIDCard
)
from .forms import TreatmentPlanForm, PhototherapyTypeForm
from .utils import get_template_path

# Configure logging and user model
User = get_user_model()
logger = logging.getLogger(__name__)


class PhototherapyManagementView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to access Phototherapy Management")
                return handler403(request, exception="Access denied to phototherapy management")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy management dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing phototherapy management")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('phototherapy_dashboard.html', request.user.role, 'phototherapy_management')
            
            # Get base context
            context = self.get_context_data()
            
            # Handle pagination only if we have plans
            if 'phototherapy_plans' in context:
                try:
                    page = request.GET.get('page', 1)
                    paginator = Paginator(context['phototherapy_plans'], 10)
                    plans_page = paginator.page(page)
                    
                    # Update context with pagination data
                    context.update({
                        'phototherapy_plans': plans_page,
                        'paginator': paginator,
                        'page_obj': plans_page
                    })
                except (PageNotAnInteger, EmptyPage) as e:
                    logger.warning(f"Pagination error: {str(e)}")
                    # Default to first page on error
                    context.update({
                        'phototherapy_plans': paginator.page(1),
                        'paginator': paginator,
                        'page_obj': paginator.page(1)
                    })
            else:
                # Handle case where no plans exist
                context['phototherapy_plans'] = []
                context['paginator'] = None
                context['page_obj'] = None

            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in phototherapy management view: {str(e)}")
            messages.error(request, "An error occurred while loading phototherapy data")
            return handler500(request, exception=str(e))

    def get_context_data(self):
        try:
            # Initialize base context with revenue calculation first
            initial_context = {
                'revenue_this_month': PhototherapyPayment.objects.filter(
                    payment_date__month=timezone.now().month,
                    status='COMPLETED'
                ).aggregate(total=models.Sum('amount'))['total'] or 0
            }

            # Get all plans with optimized queries
            plans = PhototherapyPlan.objects.select_related(
                'patient',
                'protocol__phototherapy_type',
                'rfid_card',
                'created_by'
            ).prefetch_related(
                'sessions',
                'payments',
                'progress_records'
            ).order_by('-created_at')

            # Basic statistics with safe defaults
            active_plans = plans.filter(is_active=True)
            active_plans_count = active_plans.count()

            # Calculate growth rates first
            last_month_active_plans = PhototherapyPlan.objects.filter(
                is_active=True,
                created_at__lte=timezone.now() - timedelta(days=30)
            ).count()

            active_plans_growth = (
                round(((active_plans_count - last_month_active_plans) / last_month_active_plans) * 100)
                if last_month_active_plans > 0
                else 0
            )

            last_month_revenue = PhototherapyPayment.objects.filter(
                payment_date__month=(timezone.now() - timedelta(days=30)).month,
                status='COMPLETED'
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            revenue_growth = (
                round(((initial_context['revenue_this_month'] - last_month_revenue) / last_month_revenue) * 100)
                if last_month_revenue > 0
                else 0
            )

            # Session distribution calculation
            all_completed_sessions = PhototherapySession.objects.filter(
                scheduled_date__month=timezone.now().month,
                status='COMPLETED'
            ).select_related('plan__protocol__phototherapy_type')

            total_sessions = all_completed_sessions.count()
            
            session_distribution = {}
            for therapy_type in PhototherapyType.THERAPY_CHOICES:
                type_key = therapy_type[0]
                count = all_completed_sessions.filter(
                    plan__protocol__phototherapy_type__therapy_type=type_key
                ).count()
                session_distribution[type_key] = round((count / total_sessions) * 100) if total_sessions > 0 else 0

            # Get devices needing maintenance
            devices = PhototherapyDevice.objects.filter(is_active=True)
            devices_needing_maintenance = devices.filter(
                next_maintenance_date__lte=timezone.now().date()
            ).count()

            # Update patients query to directly use User model
            patients = User.objects.filter(
                role__name='PATIENT'
            ).select_related('role').all()

            # Calculate therapy types count
            therapy_types_count = PhototherapyType.objects.filter(is_active=True).count()

            # Calculate home therapy statistics
            home_therapy_plans = PhototherapyPlan.objects.filter(
                is_active=True,
                protocol__phototherapy_type__therapy_type='HOME_NB'  # Changed from 'HOME' to match model's THERAPY_CHOICES
            )

            # Get unique patients who have home therapy logs in the last 30 days
            active_home_therapy_patients = HomePhototherapyLog.objects.filter(
                date__gte=timezone.now().date() - timedelta(days=30)
            ).values('plan__patient').distinct().count()

            # Use the higher count between plans and active patients
            home_therapy_count = max(
                home_therapy_plans.count(),
                active_home_therapy_patients
            )

            # Calculate compliance rate for home therapy
            recent_home_logs = HomePhototherapyLog.objects.filter(
                plan__in=home_therapy_plans,
                date__gte=timezone.now().date() - timedelta(days=30)
            ).values('plan', 'date').distinct()

            total_expected_sessions = sum(
                plan.protocol.frequency_per_week * 4  # Monthly expected sessions
                for plan in home_therapy_plans
            )

            actual_sessions = recent_home_logs.count()

            compliance_rate = (
                round((actual_sessions / total_expected_sessions) * 100)
                if total_expected_sessions > 0
                else 0
            )

            # Calculate today's sessions
            today = timezone.now().date()
            today_sessions = PhototherapySession.objects.filter(
                scheduled_date=today
            )
            
            sessions_today = today_sessions.count()
            completed_today = today_sessions.filter(status='COMPLETED').count()
            pending_today = today_sessions.filter(
                status__in=['SCHEDULED', 'RESCHEDULED']
            ).count()

            # Calculate overall compliance statistics
            all_sessions = PhototherapySession.objects.filter(
                scheduled_date__lte=timezone.now().date()
            )
            total_scheduled = all_sessions.count()
            total_completed = all_sessions.filter(status='COMPLETED').count()
            total_missed = all_sessions.filter(status='MISSED').count()

            # Calculate overall compliance rate
            overall_compliance = (
                round((total_completed / total_scheduled) * 100)
                if total_scheduled > 0
                else 0
            )

            # Calculate month-over-month change
            last_month = timezone.now().date() - timedelta(days=30)
            last_month_completed = PhototherapySession.objects.filter(
                scheduled_date__lte=last_month,
                status='COMPLETED'
            ).count()
            last_month_total = PhototherapySession.objects.filter(
                scheduled_date__lte=last_month
            ).count()

            last_month_compliance = (
                round((last_month_completed / last_month_total) * 100)
                if last_month_total > 0
                else 0
            )

            compliance_change = overall_compliance - last_month_compliance

            # Calculate treatment distribution
            active_treatments = PhototherapyPlan.objects.filter(is_active=True)
            active_treatments_count = active_treatments.count()

            # Get distribution by therapy type
            treatment_distribution = {}
            for therapy_type in PhototherapyType.THERAPY_CHOICES:
                count = active_treatments.filter(
                    protocol__phototherapy_type__therapy_type=therapy_type[0]
                ).count()
                if count > 0:  # Only include types that have active treatments
                    treatment_distribution[therapy_type[1]] = count

            context = {
                # Basic data
                'phototherapy_types': PhototherapyType.objects.filter(is_active=True),
                'protocols': PhototherapyProtocol.objects.filter(is_active=True),
                'phototherapy_plans': plans,
                'devices': PhototherapyDevice.objects.filter(is_active=True),
                'patients': patients,
                
                # Growth statistics
                'active_plans_growth': active_plans_growth,
                
                # Distribution statistics
                'session_distribution': session_distribution,
                
                # Add other existing context items...
                'active_plans': getattr(active_plans, 'count', lambda: 0)(),
                'completed_sessions': getattr(PhototherapySession.objects.filter(status='COMPLETED'), 'count', lambda: 0)(),
                'missed_sessions': getattr(PhototherapySession.objects.filter(status='MISSED'), 'count', lambda: 0)(),
                'active_devices': getattr(devices, 'count', lambda: 0)(),
                'maintenance_needed': devices_needing_maintenance or 0,
                
                # Additional statistics
                'total_sessions_this_month': PhototherapySession.objects.filter(
                    scheduled_date__month=timezone.now().month
                ).count() or 0,
                'therapy_types_count': therapy_types_count,
                'home_therapy_count': home_therapy_count,
                'compliance_rate': compliance_rate,
                'active_home_patients': active_home_therapy_patients,
                'total_home_logs_this_month': recent_home_logs.count(),

                # Today's sessions statistics
                'sessions_today': sessions_today,
                'completed_today': completed_today,
                'pending_today': pending_today,

                # Compliance statistics
                'compliance_stats': {
                    'overall_rate': overall_compliance,
                    'monthly_change': compliance_change,
                    'total_scheduled': total_scheduled,
                    'total_completed': total_completed,
                    'total_missed': total_missed,
                    'completion_rate': overall_compliance,
                    'target_rate': 90,  # You can make this configurable
                    'last_month_rate': last_month_compliance
                },

                # Treatment distribution
                'active_treatments_count': active_treatments_count,
                'treatment_distribution': treatment_distribution,
            }

            return context
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            # Return minimal context to prevent template errors
            return {
                'phototherapy_plans': [],
                'phototherapy_types': [],
                'protocols': [],
                'devices': [],
                'patients': [],
                'active_plans': 0,
                'completed_sessions': 0,
                'missed_sessions': 0,
                'active_devices': 0,
                'maintenance_needed': 0,
                'total_sessions_this_month': 0,
                'therapy_types_count': 0,
                'home_therapy_count': 0,
                'compliance_rate': 0,
                'active_home_patients': 0,
                'total_home_logs_this_month': 0,
                'sessions_today': 0,
                'completed_today': 0,
                'pending_today': 0,
                'compliance_stats': {
                    'overall_rate': 0,
                    'monthly_change': 0,
                    'total_scheduled': 0,
                    'total_completed': 0,
                    'total_missed': 0,
                    'completion_rate': 0,
                    'target_rate': 90,
                    'last_month_rate': 0
                },
                'active_plans_growth': 0,
                'session_distribution': {
                    'WB_NB': 0,
                    'EXCIMER': 0,
                    'HOME_NB': 0,
                    'SUN_EXP': 0
                },
                'active_treatments_count': 0,
                'treatment_distribution': {},
            }
        

class NewTreatmentPlanView(LoginRequiredMixin, CreateView):
    model = PhototherapyPlan
    form_class = TreatmentPlanForm
    success_url = reverse_lazy('phototherapy_management')

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                logger.warning(
                    f"Access denied to new treatment plan creation for user {request.user.id}"
                )
                messages.error(request, "You don't have permission to access Phototherapy")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            form.instance.is_active = True
            messages.success(self.request, "Treatment plan created successfully")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating treatment plan: {str(e)}")
            messages.error(self.request, "Error creating treatment plan")
            return self.form_invalid(form)

    def get_template_names(self):
        try:
            return [get_template_path(
                'new_treatment_plan_create.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_new_treatment_plan_create.html']
        

class TreatmentPlanListView(LoginRequiredMixin, ListView):
    model = PhototherapyPlan
    context_object_name = 'treatment_plans'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                logger.warning(
                    f"Access denied to treatment plans list for user {request.user.id}"
                )
                messages.error(request, "You don't have permission to access Phototherapy")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in treatment plans list dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            
            # Search functionality
            search_query = self.request.GET.get('search', '')
            if search_query:
                queryset = queryset.filter(
                    Q(patient__first_name__icontains=search_query) |
                    Q(patient__last_name__icontains=search_query) |
                    Q(patient__email__icontains=search_query) |
                    Q(special_instructions__icontains=search_query)
                )

            # Filter by status
            status = self.request.GET.get('status', '')
            if status:
                queryset = queryset.filter(is_active=status == 'active')

            # Sort functionality
            sort_by = self.request.GET.get('sort', '-created_at')
            if sort_by and sort_by in ['created_at', '-created_at', 'total_cost', '-total_cost']:
                queryset = queryset.order_by(sort_by)

            return queryset
        except Exception as e:
            logger.error(f"Error in treatment plans queryset: {str(e)}")
            messages.error(self.request, "Error retrieving treatment plans")
            return PhototherapyPlan.objects.none()

    def get_template_names(self):
        try:
            return [get_template_path(
                'treatment_plan_list.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_treatment_plan_list.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['search_query'] = self.request.GET.get('search', '')
            context['current_status'] = self.request.GET.get('status', '')
            context['current_sort'] = self.request.GET.get('sort', '-created_at')
            
            # Add summary statistics
            context['total_plans'] = self.model.objects.count()
            context['active_plans'] = self.model.objects.filter(is_active=True).count()
            context['completed_plans'] = self.model.objects.filter(
                sessions_completed__gte=models.F('total_sessions_planned')
            ).count()

            # Add data needed for edit modal
            context['protocols'] = PhototherapyProtocol.objects.filter(is_active=True)
            context['rfid_cards'] = PatientRFIDCard.objects.filter(
                is_active=True
            ).exclude(
                phototherapyplan__isnull=False,  # Exclude cards that are already assigned
                phototherapyplan__is_active=True  # to active treatment plans
            )

        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading page data")
        return context
    

class TreatmentPlanDetailView(LoginRequiredMixin, DetailView):
    model = PhototherapyPlan
    context_object_name = 'plan'

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to view treatment plans")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in treatment plan detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the treatment plan")
            return redirect('treatment_plan_list')

    def get_template_names(self):
        try:
            return [get_template_path(
                'treatment_plan_detail.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_treatment_plan_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            plan = self.get_object()
            context.update({
                'sessions': plan.sessions.all().order_by('-scheduled_date'),
                'progress_records': plan.progress_records.all().order_by('-assessment_date'),
                'payments': plan.payments.all().order_by('-payment_date'),
                'completion_percentage': plan.get_completion_percentage(),
                'total_paid': plan.amount_paid,
                'remaining_balance': plan.total_cost - plan.amount_paid,
                'next_session': plan.sessions.filter(
                    scheduled_date__gte=timezone.now().date(),
                    status='SCHEDULED'
                ).first(),
                'recent_progress': plan.progress_records.order_by('-assessment_date').first(),
                'missed_sessions_count': plan.sessions.filter(status='MISSED').count(),
                'completed_sessions_count': plan.sessions.filter(status='COMPLETED').count(),
            })
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading treatment plan data")
        return context


class ActivateTreatmentPlanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to modify treatment plans")
                return handler403(request)

            plan = get_object_or_404(PhototherapyPlan, pk=pk)
            plan.is_active = True
            plan.save()
            
            messages.success(request, "Treatment plan activated successfully")
            return redirect('treatment_plan_detail', pk=pk)
        except Exception as e:
            logger.error(f"Error activating treatment plan: {str(e)}")
            messages.error(request, "Error activating treatment plan")
            return redirect('treatment_plan_detail', pk=pk)

class DeactivateTreatmentPlanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to modify treatment plans")
                return handler403(request)

            plan = get_object_or_404(PhototherapyPlan, pk=pk)
            plan.is_active = False
            plan.save()
            
            messages.success(request, "Treatment plan deactivated successfully")
            return redirect('treatment_plan_detail', pk=pk)
        except Exception as e:
            logger.error(f"Error deactivating treatment plan: {str(e)}")
            messages.error(request, "Error deactivating treatment plan")
            return redirect('treatment_plan_detail', pk=pk)


class EditTreatmentPlanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to modify treatment plans")
                return handler403(request)

            plan = get_object_or_404(PhototherapyPlan, pk=pk)
            
            # Convert reminder frequency from string to integer
            reminder_frequency_map = {
                'NONE': 0,
                'DAILY': 1,
                'WEEKLY': 7
            }
            
            # Update fields with proper type conversion
            try:
                plan.protocol_id = int(request.POST.get('protocol'))
                plan.total_sessions_planned = int(request.POST.get('total_sessions_planned'))
                plan.current_dose = float(request.POST.get('current_dose'))
                plan.total_cost = float(request.POST.get('total_cost'))
                plan.rfid_card_id = request.POST.get('rfid_card') or None
                plan.reminder_frequency = int(request.POST.get('reminder_frequency', 1))  # Default to 1 if not provided
                plan.special_instructions = request.POST.get('special_instructions')
                
                plan.save()
                messages.success(request, "Treatment plan updated successfully")
                
            except (ValueError, TypeError) as e:
                logger.error(f"Data conversion error: {str(e)}")
                messages.error(request, "Invalid data provided for treatment plan update")
                return redirect('treatment_plan_detail', pk=pk)
            
            return redirect('treatment_plan_detail', pk=pk)
            
        except Exception as e:
            logger.error(f"Error updating treatment plan: {str(e)}")
            messages.error(request, "Error updating treatment plan")
            return redirect('treatment_plan_detail', pk=pk)


@method_decorator(csrf_protect, name='dispatch')
class AddPhototherapyTypeView(LoginRequiredMixin, CreateView):
    model = PhototherapyType
    form_class = PhototherapyTypeForm
    success_url = reverse_lazy('phototherapy_management')
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                logger.warning(f"Access denied to phototherapy type creation for user {request.user.id}")
                messages.error(request, "You don't have permission to add phototherapy types")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy type dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'phototherapy_types/add_phototherapy_type.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_add_phototherapy_type.html']
            
    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Phototherapy type created successfully")
            return response
        except Exception as e:
            logger.error(f"Error saving phototherapy type: {str(e)}")
            messages.error(self.request, "Error creating phototherapy type")
            return super().form_invalid(form)
        

class PhototherapyTypeListView(LoginRequiredMixin, ListView):
    model = PhototherapyType
    context_object_name = 'therapy_types'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                logger.warning(f"Access denied to phototherapy types list for user {request.user.id}")
                messages.error(request, "You don't have permission to access Phototherapy Types")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy types list dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'phototherapy_types/phototherapy_types_dashboard.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_phototherapy_types_dashboard.html']

    def get_queryset(self):
        try:
            queryset = PhototherapyType.objects.all().annotate(
                active_protocols_count=Count('phototherapyprotocol', distinct=True),
                active_plans_count=Count('phototherapyprotocol__phototherapyplan', distinct=True)
            )
            
            # Filter by search query if provided
            search_query = self.request.GET.get('search')
            if (search_query):
                queryset = queryset.filter(name__icontains=search_query)
            
            # Filter by therapy type if provided
            therapy_type = self.request.GET.get('therapy_type')
            if therapy_type:
                queryset = queryset.filter(therapy_type=therapy_type)
            
            # Filter by priority if provided
            priority = self.request.GET.get('priority')
            if priority:
                queryset = queryset.filter(priority=priority)
            
            # Sort by specified field
            sort_by = self.request.GET.get('sort', '-created_at')
            queryset = queryset.order_by(sort_by)
            
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return PhototherapyType.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Add filter options
            context['therapy_type_choices'] = PhototherapyType.THERAPY_CHOICES
            context['priority_choices'] = PhototherapyType.PRIORITY_CHOICES
            
            # Add current filter values
            context['current_search'] = self.request.GET.get('search', '')
            context['current_therapy_type'] = self.request.GET.get('therapy_type', '')
            context['current_priority'] = self.request.GET.get('priority', '')
            context['current_sort'] = self.request.GET.get('sort', '-created_at')
            
            # Add summary statistics
            context['total_types'] = PhototherapyType.objects.count()
            context['active_types'] = PhototherapyType.objects.filter(is_active=True).count()
            context['rfid_required_types'] = PhototherapyType.objects.filter(requires_rfid=True).count()
            
            # Add user permissions
            context['can_add'] = PermissionManager.check_module_modify(self.request.user, 'phototherapy_management')
            context['can_edit'] = context['can_add']
            context['can_delete'] = PermissionManager.check_module_delete(self.request.user, 'phototherapy_management')
            
        except Exception as e:
            logger.error(f"Error in get_context_data: {str(e)}")
            messages.error(self.request, "Error loading some dashboard data")
        
        return context


@method_decorator(csrf_protect, name='dispatch')
class EditPhototherapyTypeView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_modify(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to edit phototherapy types")
                return handler403(request)
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in edit phototherapy type dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('therapy_types_dashboard')

    def post(self, request, pk):
        try:
            therapy_type = get_object_or_404(PhototherapyType, pk=pk)
            
            # Update fields
            therapy_type.name = request.POST.get('name')
            therapy_type.therapy_type = request.POST.get('therapy_type')
            therapy_type.description = request.POST.get('description')
            therapy_type.priority = request.POST.get('priority')
            therapy_type.requires_rfid = request.POST.get('requires_rfid') == 'on'
            therapy_type.is_active = request.POST.get('is_active') == 'on'
            
            therapy_type.save()
            messages.success(request, "Phototherapy type updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating phototherapy type: {str(e)}")
            messages.error(request, "Error updating phototherapy type")
            
        return redirect('therapy_types_dashboard')


@method_decorator(csrf_protect, name='dispatch')
class DeletePhototherapyTypeView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_delete(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to delete phototherapy types")
                return handler403(request)
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in delete phototherapy type dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('therapy_types_dashboard')

    def post(self, request, pk):
        try:
            therapy_type = get_object_or_404(PhototherapyType, pk=pk)
            
            # Check if there are any active protocols using this type
            if therapy_type.phototherapyprotocol_set.filter(is_active=True).exists():
                messages.error(request, "Cannot delete phototherapy type that has active protocols")
                return redirect('therapy_types_dashboard')
            
            therapy_type.delete()
            messages.success(request, "Phototherapy type deleted successfully")
            
        except Exception as e:
            logger.error(f"Error deleting phototherapy type: {str(e)}")
            messages.error(request, "Error deleting phototherapy type")
            
        return redirect('therapy_types_dashboard')


def get_treatment_plan_details(request, plan_id):
    try:
        plan = PhototherapyPlan.objects.select_related('protocol').get(id=plan_id)
        return JsonResponse({
            'protocol': {
                'initial_dose': plan.protocol.initial_dose,
                'max_dose': plan.protocol.max_dose,
                'increment_percentage': plan.protocol.increment_percentage
            },
            'current_dose': plan.current_dose,
            'sessions_completed': plan.sessions_completed,
            'total_sessions': plan.total_sessions_planned
        })
    except PhototherapyPlan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)

def get_device_details(request, device_id):
    try:
        device = PhototherapyDevice.objects.get(id=device_id)
        return JsonResponse({
            'location': device.location,
            'last_maintenance_date': device.last_maintenance_date.strftime('%Y-%m-%d') if device.last_maintenance_date else 'Never',
            'next_maintenance_date': device.next_maintenance_date.strftime('%Y-%m-%d') if device.next_maintenance_date else 'Not scheduled',
            'is_active': device.is_active,
            'needs_maintenance': device.needs_maintenance()
        })
    except PhototherapyDevice.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)


