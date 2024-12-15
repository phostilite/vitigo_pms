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
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect


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
    HomePhototherapyLog
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
            # Get all plans with optimized queries
            plans = PhototherapyPlan.objects.select_related(
                'patient',  # Changed: removed user reference
                'protocol__phototherapy_type',
                'rfid_card',
                'created_by'
            ).prefetch_related(
                'sessions',
                'payments',
                'progress_records'
            ).order_by('-created_at')

            # Calculate statistics
            active_plans = plans.filter(is_active=True)
            completed_sessions = PhototherapySession.objects.filter(status='COMPLETED')
            missed_sessions = PhototherapySession.objects.filter(status='MISSED')
            devices = PhototherapyDevice.objects.filter(is_active=True)

            # Get devices needing maintenance
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

            context = {
                'phototherapy_types': PhototherapyType.objects.filter(is_active=True) or [],
                'protocols': PhototherapyProtocol.objects.filter(is_active=True) or [],
                'phototherapy_plans': plans or [],
                'devices': devices or [],
                'patients': patients,
                
                # Statistics with safe defaults
                'active_plans': getattr(active_plans, 'count', lambda: 0)(),
                'completed_sessions': getattr(completed_sessions, 'count', lambda: 0)(),
                'missed_sessions': getattr(missed_sessions, 'count', lambda: 0)(),
                'active_devices': getattr(devices, 'count', lambda: 0)(),
                'maintenance_needed': devices_needing_maintenance or 0,
                
                # Additional statistics
                'total_sessions_this_month': PhototherapySession.objects.filter(
                    scheduled_date__month=timezone.now().month
                ).count() or 0,
                'revenue_this_month': PhototherapyPayment.objects.filter(
                    payment_date__month=timezone.now().month,
                    status='COMPLETED'
                ).aggregate(total=models.Sum('amount'))['total'] or 0,
                'therapy_types_count': therapy_types_count,
                'home_therapy_count': home_therapy_count,
                'compliance_rate': compliance_rate,
                'active_home_patients': active_home_therapy_patients,
                'total_home_logs_this_month': recent_home_logs.count(),
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
                'revenue_this_month': 0,
                'therapy_types_count': 0,
                'home_therapy_count': 0,
                'compliance_rate': 0,
                'active_home_patients': 0,
                'total_home_logs_this_month': 0,
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
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading page data")
        return context
    


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
                'add_phototherapy_type.html',
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
                'phototherapy_types_dashboard.html',
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
            if search_query:
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