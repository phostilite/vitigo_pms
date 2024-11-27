# Python Standard Library imports
from collections import defaultdict
from datetime import timedelta, datetime
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, FormView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from patient_management.models import MedicalHistory
from .models import Appointment, CancellationReason, DoctorProfile, DoctorTimeSlot
from .forms import AppointmentCreateForm

# Logger configuration
logger = logging.getLogger(__name__)

# Get the User model
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
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class AppointmentDashboardView(LoginRequiredMixin, ListView):
    model = Appointment
    context_object_name = 'appointments'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'appointment_management'):
            messages.error(request, "You don't have permission to access Appointments")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

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

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'appointment_management'):
            messages.error(request, "You don't have permission to view appointment details")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

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

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except self.model.DoesNotExist:
            return handler404(self.request, exception="Appointment not found")

class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentCreateForm
    success_url = reverse_lazy('appointment_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'appointment_management'):
            logger.warning(
                f"Access denied to appointment creation for user {request.user.id}"
            )
            messages.error(request, "You don't have permission to create appointments")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path('appointment_create.html', self.request.user.role, 'appointment_management')]

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')
            
            context.update({
                'patients': User.objects.filter(role=patient_role, is_active=True),
                'doctors': User.objects.filter(role=doctor_role, is_active=True),
            })
            return context
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            messages.error(self.request, "Error loading form data. Please try again.")
            return {}

    def form_invalid(self, form):
        logger.warning(f"Invalid form submission: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

    @transaction.atomic
    def form_valid(self, form):
        try:
            # Get form data
            patient_id = form.cleaned_data.get('patient_id')
            doctor_id = form.cleaned_data.get('doctor_id')
            time_slot_id = form.cleaned_data.get('time_slot_id')
            
            # Validate required fields
            if not all([patient_id, doctor_id, time_slot_id]):
                missing_fields = []
                if not patient_id: missing_fields.append("Patient")
                if not doctor_id: missing_fields.append("Doctor")
                if not time_slot_id: missing_fields.append("Time slot")
                error_msg = f"Required fields missing: {', '.join(missing_fields)}"
                logger.error(f"Appointment creation failed: {error_msg}")
                messages.error(self.request, error_msg)
                return self.form_invalid(form)

            # Get patient and doctor
            try:
                patient = User.objects.get(id=patient_id, role__name='PATIENT')
                doctor = User.objects.get(id=doctor_id, role__name='DOCTOR')
            except User.DoesNotExist as e:
                logger.error(f"User lookup failed: {str(e)}")
                messages.error(self.request, "Invalid patient or doctor selected.")
                return self.form_invalid(form)

            # Get doctor's profile
            try:
                doctor_profile = DoctorProfile.objects.get(user=doctor)
            except DoctorProfile.DoesNotExist:
                logger.error(f"Doctor profile not found for user_id: {doctor_id}")
                messages.error(self.request, "Doctor profile not found.")
                return self.form_invalid(form)

            # Get and verify time slot
            try:
                time_slot = DoctorTimeSlot.objects.select_for_update().get(
                    id=time_slot_id,
                    doctor=doctor_profile,
                    is_available=True
                )
            except DoctorTimeSlot.DoesNotExist:
                logger.error(f"Time slot {time_slot_id} not available or not found")
                messages.error(self.request, "Selected time slot is no longer available.")
                return self.form_invalid(form)

            # Create appointment
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.doctor = doctor
            appointment.time_slot = time_slot
            appointment.status = 'PENDING'

            try:
                # Validate appointment
                appointment.full_clean()
            except ValidationError as e:
                logger.error(f"Appointment validation failed: {str(e)}")
                messages.error(self.request, f"Invalid appointment data: {str(e)}")
                return self.form_invalid(form)

            # Save everything
            time_slot.is_available = False
            time_slot.save()
            appointment.save()

            logger.info(f"Appointment created successfully: ID={appointment.id}")
            messages.success(
                self.request, 
                f'Appointment scheduled successfully for {appointment.date} at {appointment.time_slot.start_time}'
            )
            return super().form_valid(form)

        except Exception as e:
            logger.exception(f"Unexpected error in appointment creation: {str(e)}")
            messages.error(
                self.request,
                "An unexpected error occurred while creating the appointment. Please try again."
            )
            return self.form_invalid(form)

def get_available_time_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    
    if not doctor_id or not date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        # Get the doctor's profile
        doctor_profile = DoctorProfile.objects.get(user_id=doctor_id)
        
        time_slots = DoctorTimeSlot.objects.filter(
            doctor=doctor_profile,  # Changed from doctor__user_id to doctor
            date=date,
            is_available=True
        ).values('id', 'start_time', 'end_time')
        
        return JsonResponse({'time_slots': list(time_slots)})
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_user_info(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'gender': user.get_gender_display(),
            'phone': f"{user.country_code}{user.phone_number}",
            'date_joined': user.date_joined.isoformat(),
            'is_active': user.is_active,
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        }
        return JsonResponse(user_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)