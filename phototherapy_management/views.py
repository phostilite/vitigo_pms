# Standard library imports
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models  # Added
from django.shortcuts import render
from django.utils import timezone  # Added
from django.views import View

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
    PhototherapyPayment
)

# Configure logging and user model
User = get_user_model()
logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'{role_folder}/{module}/{base_template}'
    return f'{role_folder}/{base_template}'

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
            }

class PhototherapyDetailView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                messages.error(request, "You don't have permission to view phototherapy details")
                return handler403(request, exception="Access denied to phototherapy details")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing phototherapy details")
            return handler500(request, exception=str(e))

    def get(self, request, plan_id):
        try:
            template_path = get_template_path('phototherapy_detail.html', request.user.role, 'phototherapy_management')
            
            plan = self.get_plan_with_relations(plan_id)
            if not plan:
                messages.error(request, "Phototherapy plan not found")
                return handler404(request, exception="Phototherapy plan not found")

            context = self.get_context_data(plan)
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in phototherapy detail view: {str(e)}")
            messages.error(request, "An error occurred while loading phototherapy details")
            return handler500(request, exception=str(e))

    def get_plan_with_relations(self, plan_id):
        try:
            return PhototherapyPlan.objects.select_related(
                'patient',
                'protocol',
                'protocol__phototherapy_type',  # Changed: access phototherapy_type through protocol
                'created_by'
            ).prefetch_related(
                'sessions__device',
                'sessions__administered_by',  # Changed: field name is administered_by
                'home_logs'  # Added: to fetch home therapy logs
            ).get(id=plan_id)
        except PhototherapyPlan.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching phototherapy plan: {str(e)}")
            return None

    def get_context_data(self, plan):
        try:
            return {
                'plan': plan,
                'sessions': plan.sessions.all().order_by('-date'),
                'progress_photos': plan.progress_photos.all().order_by('-date'),
                'compliance_rate': self.calculate_compliance_rate(plan),
                'patient_details': self.get_patient_details(plan.patient),
            }
        except Exception as e:
            logger.error(f"Error getting phototherapy context data: {str(e)}")
            return {'plan': plan}

    def calculate_compliance_rate(self, plan):
        try:
            total_sessions = plan.sessions.count()
            if total_sessions == 0:
                return 0
            completed_sessions = plan.sessions.filter(compliance='COMPLETED').count()
            return (completed_sessions / total_sessions) * 100
        except Exception as e:
            logger.error(f"Error calculating compliance rate: {str(e)}")
            return 0

    def get_patient_details(self, patient):
        try:
            return {
                'name': patient.get_full_name(),
                'age': patient.age,
                'gender': patient.gender,
                'medical_history': getattr(patient, 'medical_history', None),
            }
        except Exception as e:
            logger.error(f"Error getting patient details: {str(e)}")
            return None