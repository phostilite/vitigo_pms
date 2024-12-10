# Django imports 
import logging
from datetime import datetime
from django.utils import timezone  

# Standard library imports
from django.views.generic import ListView, View, DetailView, CreateView, UpdateView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from datetime import timedelta
from django.db import transaction
from django.urls import reverse_lazy
from django.http import Http404

# Local application imports
from .models import (
    Consultation, DoctorPrivateNotes, ConsultationType,
    ConsultationPriority, PaymentStatus
)
from .forms import ConsultationForm
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500

logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module='consultation_management'):
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

class ConsultationDashboardView(LoginRequiredMixin, ListView):
    model = Consultation
    context_object_name = 'consultations'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to access Consultations")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path('consultation_dashboard.html', self.request.user.role, 'consultation_management')]

    def get_queryset(self):
        # Add your queryset filters here
        return Consultation.objects.select_related('patient', 'doctor').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your context data here
        return context
    

class ConsultationCreateView(LoginRequiredMixin, CreateView):
    model = Consultation
    form_class = ConsultationForm
    success_url = reverse_lazy('consultation_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                logger.warning(
                    f"Access denied to consultation creation for user {request.user.id}"
                )
                messages.error(request, "You don't have permission to access Consultations")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in consultation dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'consultation_create.html',
                self.request.user.role,
                'consultation_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['consultation_management/default_consultation_create.html']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs['user'] = self.request.user
        except Exception as e:
            logger.error(f"Error setting form kwargs: {str(e)}")
        return kwargs

    def form_valid(self, form):
        try:
            # Set defaults for required fields
            consultation = form.save(commit=False)
            
            # Set the doctor if not already set
            if not consultation.doctor:
                consultation.doctor = self.request.user
            
            # Updated datetime validation
            if consultation.scheduled_datetime <= timezone.now():
                form.add_error('scheduled_datetime', 'Consultation must be scheduled for a future time')
                return self.form_invalid(form)
            
            # Save the consultation
            consultation.save()
            
            # Create private notes
            try:
                DoctorPrivateNotes.objects.create(consultation=consultation)
            except Exception as e:
                logger.warning(f"Error creating private notes: {str(e)}")
                # Continue execution as this is not critical
            
            messages.success(self.request, "Consultation created successfully")
            logger.info(f"Consultation {consultation.id} created by user {self.request.user.id}")
            
            return super().form_valid(form)
            
        except ValidationError as e:
            logger.error(f"Validation error in consultation creation: {str(e)}")
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            messages.error(self.request, "An error occurred while creating the consultation")
            return self.form_invalid(form)

    def form_invalid(self, form):
        try:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            logger.warning(
                f"Invalid consultation form submission by user {self.request.user.id}: {form.errors}"
            )
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"Error handling invalid form: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request")
            return redirect('consultation_dashboard')

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context.update({
                'consultation_types': ConsultationType.choices,
                'priority_levels': ConsultationPriority.choices,
                'payment_statuses': PaymentStatus.choices,
                'page_title': 'Create New Consultation',
                'submit_text': 'Schedule Consultation'
            })
            return context
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            return {'error': 'Error loading page data'}
        

class ConsultationDetailView(LoginRequiredMixin, DetailView):
    model = Consultation
    context_object_name = 'consultation'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'consultation_management'):
                logger.warning(f"Access denied to consultation details for user {request.user.id}")
                messages.error(request, "You don't have permission to view consultation details")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in consultation detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the consultation details")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'consultation_detail.html',
                self.request.user.role,
                'consultation_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['consultation_management/default_consultation_detail.html']

    def get_object(self, queryset=None):
        try:
            return Consultation.objects.select_related(
                'patient',
                'doctor',
                'private_notes',
                'treatment_plan',
                'staff_instructions'
            ).prefetch_related(
                'prescriptions__items__medication',
                'phototherapy_sessions',
                'attachments'
            ).get(pk=self.kwargs['pk'])
        except Consultation.DoesNotExist:
            logger.warning(f"Consultation {self.kwargs['pk']} not found")
            raise Http404("Consultation not found")
        except Exception as e:
            logger.error(f"Error retrieving consultation: {str(e)}")
            raise

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            consultation = self.object
            
            # Base consultation information
            context['page_title'] = f'Consultation Details - {consultation.patient.get_full_name()}'
            
            # Get prescriptions with items
            try:
                prescriptions = consultation.prescriptions.prefetch_related('items__medication').all()
                context['prescriptions'] = prescriptions
            except Exception as e:
                logger.warning(f"Error fetching prescriptions: {str(e)}")
                context['prescriptions'] = None
                context['prescription_error'] = "Unable to load prescriptions"
            
            # Get treatment plan details
            try:
                if hasattr(consultation, 'treatment_plan'):
                    context['treatment_plan_items'] = consultation.treatment_plan.items.all()
            except Exception as e:
                logger.warning(f"Error fetching treatment plan: {str(e)}")
                context['treatment_plan_items'] = None
                context['treatment_plan_error'] = "Unable to load treatment plan"
            
            # Get phototherapy sessions
            try:
                context['phototherapy_sessions'] = consultation.phototherapy_sessions.all()
            except Exception as e:
                logger.warning(f"Error fetching phototherapy sessions: {str(e)}")
                context['phototherapy_sessions'] = None
                context['phototherapy_error'] = "Unable to load phototherapy sessions"
            
            # Get attachments
            try:
                context['attachments'] = consultation.attachments.all()
            except Exception as e:
                logger.warning(f"Error fetching attachments: {str(e)}")
                context['attachments'] = None
                context['attachments_error'] = "Unable to load attachments"
            
            # Add permissions context
            context['can_edit'] = PermissionManager.check_module_modify(
                self.request.user, 
                'consultation_management'
            )
            context['can_delete'] = PermissionManager.check_module_delete(
                self.request.user, 
                'consultation_management'
            )
            
            # Add consultation status context
            context['is_upcoming'] = consultation.scheduled_datetime > timezone.now()
            context['is_completed'] = consultation.status == 'COMPLETED'
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting consultation detail context: {str(e)}")
            messages.error(self.request, "Error loading consultation details")
            return {'error': 'Error loading consultation data'}
        

class ConsultationDeleteView(LoginRequiredMixin, View):
    def post(self, request, consultation_id):  # Changed from pk to consultation_id
        if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to delete consultations")
            return handler403(request, exception="Access Denied")

        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            
            # Check if consultation is in the past
            if consultation.scheduled_datetime <= timezone.now():
                messages.error(request, "Cannot delete past consultations")
                return redirect('consultation_dashboard')
                
            consultation.delete()
            messages.success(request, "Consultation deleted successfully")
            return redirect('consultation_dashboard')
        except Exception as e:
            logger.error(f"Error deleting consultation {consultation_id}: {str(e)}")
            messages.error(request, "Error deleting consultation")
            return redirect('consultation_dashboard')