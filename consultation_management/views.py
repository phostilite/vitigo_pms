# 
import logging

# Standard library imports
from django.views.generic import ListView, View, DetailView, CreateView, UpdateView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from datetime import timedelta
from django.db import transaction
from django.urls import reverse_lazy

# Local application imports
from .models import Consultation, DoctorPrivateNotes, Prescription, TreatmentPlan, StaffInstruction, ConsultationPhototherapy, ConsultationAttachment
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

class ConsultationDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to delete consultations")
            return handler403(request, exception="Access Denied")

        try:
            consultation = get_object_or_404(Consultation, pk=pk)
            consultation.delete()
            messages.success(request, "Consultation deleted successfully")
            return redirect('consultation_dashboard')
        except Exception as e:
            messages.error(request, f"Error deleting consultation: {str(e)}")
            return redirect('consultation_dashboard')