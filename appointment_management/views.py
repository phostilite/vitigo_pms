from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Appointment
from django.db.models import Q
from collections import defaultdict
from patient_management.models import MedicalHistory
from .models import CancellationReason
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from access_control.models import Role

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

class AppointmentDashboardView(LoginRequiredMixin, ListView):
    model = Appointment
    context_object_name = 'appointments'
    paginate_by = 10

    def get_template_names(self):
        return [get_template_path('appointment_dashboard.html', self.request.user.role, 'appointment_management')]

    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            'patient',
            'doctor',
            'time_slot'
        )
        
        # Apply filters based on GET parameters
        filters = {}
        
        # Priority filter
        priority = self.request.GET.get('priority')
        if priority:
            filters['priority'] = priority
            
        # Status filter
        status = self.request.GET.get('status')
        if status:
            filters['status'] = status
            
        # Date filter
        appointment_date = self.request.GET.get('date')
        if appointment_date:
            filters['date'] = appointment_date
            
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(doctor__first_name__icontains=search_query) |
                Q(doctor__last_name__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
            
        return queryset.filter(**filters).order_by('-date', '-time_slot__start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        # Basic statistics
        context.update({
            'total_appointments': Appointment.objects.count(),
            'pending_appointments': Appointment.objects.filter(status='PENDING').count(),
            'completed_appointments': Appointment.objects.filter(status='COMPLETED').count(),
            'today_appointments': Appointment.objects.filter(date=today).count(),
            
            # Current filters for template
            'current_filters': {
                'priority': self.request.GET.get('priority', ''),
                'status': self.request.GET.get('status', ''),
                'date': self.request.GET.get('date', ''),
                'search': self.request.GET.get('search', ''),
            },
        })
        
        return context

class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    context_object_name = 'appointment'

    def get_template_names(self):
        return [get_template_path('appointment_detail.html', self.request.user.role, 'appointment_management')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.object
        
        # Get patient's medical history
        try:
            medical_history = MedicalHistory.objects.get(patient=appointment.patient.patient_profile)
        except MedicalHistory.DoesNotExist:
            medical_history = None

        # Get cancellation reason if appointment is cancelled
        try:
            cancellation = CancellationReason.objects.get(appointment=appointment) if appointment.status == 'CANCELLED' else None
        except CancellationReason.DoesNotExist:
            cancellation = None

        # Get doctor's profile and specializations
        try:
            doctor_profile = appointment.doctor.doctor_profile
        except:
            doctor_profile = None

        context.update({
            'medical_history': medical_history,
            'cancellation': cancellation,
            'doctor_profile': doctor_profile,
            'previous_appointments': Appointment.objects.filter(
                patient=appointment.patient,
                date__lt=appointment.date
            ).order_by('-date')[:5]
        })
        
        return context

