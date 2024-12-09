# 
import logging

# Standard library imports
from django.views.generic import ListView, View, DetailView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from datetime import timedelta
from django.db import transaction

# Local application imports
from .models import Consultation, DoctorPrivateNotes, Prescription, TreatmentPlan, StaffInstruction, ConsultationPhototherapy, ConsultationAttachment
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500

logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        try:
            role = Role.objects.get(name=role)
            role_folder = role.template_folder
        except Role.DoesNotExist:
            role_folder = 'default'
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class ConsultationManagementView(LoginRequiredMixin, ListView):
    model = Consultation
    template_name = 'dashboard/administrator/consultation_management/consultation_dashboard.html'
    context_object_name = 'consultations'
    paginate_by = 10

    def get_queryset(self):
        return Consultation.objects.select_related(
            'patient', 
            'doctor'
        ).prefetch_related(
            'prescriptions',
            'attachments'
        ).order_by('-scheduled_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get total consultations for current month
        context['total_consultations'] = Consultation.objects.filter(
            scheduled_datetime__month=timezone.now().month
        ).count()

        # Get upcoming followups for next 7 days
        context['upcoming_followups'] = Consultation.objects.filter(
            follow_up_date__range=[
                timezone.now().date(),
                timezone.now().date() + timezone.timedelta(days=7)
            ]
        ).count()

        return context

class ConsultationDeleteView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to delete consultations")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, consultation_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            
            # Store info for message
            patient_name = consultation.patient.get_full_name()
            consultation_date = consultation.scheduled_datetime.strftime('%Y-%m-%d')  # Changed from date_time to scheduled_datetime
            
            # Additional permission check for doctors
            if request.user.role.name == 'DOCTOR' and consultation.doctor != request.user:
                messages.error(request, "You can only delete your own consultations")
                return redirect('consultation_management')
            
            with transaction.atomic():
                # Delete associated records first
                if hasattr(consultation, 'treatment_instruction'):
                    consultation.treatment_instruction.delete()
                if hasattr(consultation, 'follow_up_plan'):
                    consultation.follow_up_plan.delete()
                
                # Delete prescriptions and attachments through cascade
                consultation.delete()
            
            messages.success(request, f"Consultation for {patient_name} on {consultation_date} has been deleted successfully")
            logger.info(f"Consultation {consultation_id} deleted by {request.user.email}")
            return redirect('consultation_management')
            
        except Exception as e:
            logger.error(f"Error deleting consultation: {str(e)}")
            messages.error(request, f"Error deleting consultation: {str(e)}")
            return redirect('consultation_management')