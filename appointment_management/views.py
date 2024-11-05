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

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'appointment_dashboard.html' and role 'DOCTOR', 
    returns 'dashboard/doctor/appointment_management/appointment_dashboard.html'
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'RECEPTIONIST': 'receptionist',
        'PHARMACIST': 'pharmacist',
        'LAB_TECHNICIAN': 'lab',
    }
    
    role_folder = role_template_map.get(user_role, 'admin') 
    return f'dashboard/{role_folder}/appointment_management/{base_template}'

class AppointmentDashboardView(LoginRequiredMixin, ListView):
    model = Appointment
    context_object_name = 'appointments'
    paginate_by = 10

    def get_template_names(self):
        user_role = self.request.user.role  # Assuming user role is stored in user model
        return [get_template_path('appointment_dashboard.html', user_role)]

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
        user_role = self.request.user.role
        return [get_template_path('appointment_detail.html', user_role)]

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

