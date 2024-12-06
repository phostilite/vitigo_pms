# Standard library imports
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
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
    PhototherapyType
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
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

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
            
            context = self.get_context_data()
            
            # Pagination for plans
            try:
                page = request.GET.get('page', 1)
                paginator = Paginator(context['phototherapy_plans'], 10)
                context['phototherapy_plans'] = paginator.page(page)
                context['paginator'] = paginator
            except PageNotAnInteger:
                context['phototherapy_plans'] = paginator.page(1)
            except EmptyPage:
                context['phototherapy_plans'] = paginator.page(paginator.num_pages)
            except Exception as e:
                logger.error(f"Pagination error: {str(e)}")
                messages.warning(request, "Error loading page data")

            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in phototherapy management view: {str(e)}")
            messages.error(request, "An error occurred while loading phototherapy data")
            return handler500(request, exception=str(e))

    def get_context_data(self):
        try:
            # Fix the select_related field names to match model relationships
            plans = PhototherapyPlan.objects.select_related(
                'patient',
                'protocol',
                'protocol__phototherapy_type',  
                'created_by'
            ).prefetch_related(
                'sessions__device'
            )

            context = {
                'phototherapy_types': PhototherapyType.objects.all(),
                'protocols': PhototherapyProtocol.objects.select_related('phototherapy_type'),
                'phototherapy_plans': plans,
                'sessions': PhototherapySession.objects.select_related(
                    'plan',
                    'device',
                    'administered_by'  # Changed: field name is administered_by not performed_by
                ),
                'devices': PhototherapyDevice.objects.filter(is_active=True),
                'patients': Patient.objects.all(),
            }

            # Calculate statistics
            context.update({
                'active_plans': plans.filter(is_active=True).count(),
                'completed_sessions': PhototherapySession.objects.filter(compliance='COMPLETED').count(),
                'missed_sessions': PhototherapySession.objects.filter(compliance='MISSED').count(),
                'active_devices': PhototherapyDevice.objects.filter(is_active=True).count(),
            })

            return context
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            return {}

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