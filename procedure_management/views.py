# Standard library imports
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views import View

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import Procedure, ProcedureType

# Configure logging and user model
logger = logging.getLogger(__name__)
User = get_user_model()

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

class ProcedureManagementView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'procedure_management'):
                messages.error(request, "You don't have permission to access Procedure Management")
                return handler403(request, exception="Access denied to procedure management")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in procedure management dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing procedure management")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('procedure_dashboard.html', request.user.role, 'procedure_management')
            
            # Get patient role and users
            patient_role = Role.objects.get(name='PATIENT')
            patients = User.objects.filter(role=patient_role)

            # Initialize query
            procedures = Procedure.objects.select_related(
                'user', 'procedure_type', 'performed_by'
            ).prefetch_related('images')

            # Apply filters
            procedures = self.apply_filters(procedures, request)

            # Pagination
            try:
                page = request.GET.get('page', 1)
                paginator = Paginator(procedures, 10)
                procedures = paginator.page(page)
            except PageNotAnInteger:
                procedures = paginator.page(1)
            except EmptyPage:
                procedures = paginator.page(paginator.num_pages)

            context = self.get_context_data(
                procedures=procedures,
                procedure_types=ProcedureType.objects.all(),
                patients=patients,
                paginator=paginator
            )

            return render(request, template_path, context)

        except Role.DoesNotExist:
            logger.error("Patient role not found")
            messages.error(request, "System configuration error")
            return handler500(request, exception="Patient role not found")
        except Exception as e:
            logger.error(f"Error in procedure management view: {str(e)}")
            messages.error(request, "An error occurred while loading procedures")
            return handler500(request, exception=str(e))

    def apply_filters(self, queryset, request):
        try:
            # Fetch procedures with optional filtering
            procedure_type_id = request.GET.get('procedure_type')
            status = request.GET.get('status')
            patient_id = request.GET.get('patient')
            search_query = request.GET.get('search')

            if procedure_type_id:
                queryset = queryset.filter(procedure_type_id=procedure_type_id)
            if status:
                queryset = queryset.filter(status=status)
            if patient_id:
                queryset = queryset.filter(user_id=patient_id)  # Changed from patient_id to user_id
            if search_query:
                queryset = queryset.filter(notes__icontains=search_query)
            return queryset
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            messages.warning(request, "Error applying filters")
            return queryset

    def get_context_data(self, **kwargs):
        try:
            return {
                **kwargs,
                'total_procedures': Procedure.objects.count(),
                'scheduled_procedures': Procedure.objects.filter(status='SCHEDULED').count(),
                'completed_procedures': Procedure.objects.filter(status='COMPLETED').count(),
                'cancelled_procedures': Procedure.objects.filter(status='CANCELLED').count(),
            }
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            return kwargs

class ProcedureDetailView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'procedure_management'):
                messages.error(request, "You don't have permission to view procedure details")
                return handler403(request, exception="Access denied to procedure details")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in procedure detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing procedure details")
            return handler500(request, exception=str(e))

    def get(self, request, procedure_id):
        try:
            template_path = get_template_path('procedure_detail.html', request.user.role, 'procedure_management')
            
            procedure = self.get_procedure_with_relations(procedure_id)
            
            # Validate patient role
            if procedure.user and procedure.user.role.name != 'PATIENT':
                messages.error(request, "Invalid patient assignment")
                return handler403(request, exception="Invalid patient assignment")

            context = self.get_context_data(procedure)
            return render(request, template_path, context)

        except Procedure.DoesNotExist:
            messages.error(request, "Procedure not found")
            return handler404(request, exception="Procedure not found")
        except Exception as e:
            logger.error(f"Error in procedure detail view: {str(e)}")
            messages.error(request, "An error occurred while loading procedure details")
            return handler500(request, exception=str(e))

    def get_procedure_with_relations(self, procedure_id):
        return get_object_or_404(
            Procedure.objects.select_related(
                'user',
                'procedure_type',
                'performed_by',
                'consent_form',
                'result'
            ).prefetch_related('images'),
            id=procedure_id
        )

    def get_context_data(self, procedure):
        try:
            return {
                'procedure': procedure,
                'consent_form': getattr(procedure, 'consent_form', None),
                'procedure_result': getattr(procedure, 'result', None),
                'images': procedure.images.all(),
                'patient_details': self.get_patient_details(procedure.user),
                'performer_details': self.get_performer_details(procedure.performed_by),
            }
        except Exception as e:
            logger.error(f"Error getting procedure context data: {str(e)}")
            return {'procedure': procedure}

    def get_patient_details(self, user):
        if user and user.role.name == 'PATIENT':
            return {
                'name': user.get_full_name(),
                'email': user.email,
                'gender': user.gender,
                'id': user.id
            }
        return None

    def get_performer_details(self, performer):
        if performer:
            return {
                'name': performer.get_full_name(),
                'role': performer.role,
            }
        return None

