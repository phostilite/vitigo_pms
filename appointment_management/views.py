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

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View


# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from patient_management.models import MedicalHistory
from .models import Appointment, CancellationReason, DoctorProfile, DoctorTimeSlot
from doctor_management.models import DoctorProfile
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
            messages.error(request, "You don't have permission to create appointments")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path('appointment_create.html', self.request.user.role, 'appointment_management')]

    def form_valid(self, form):
        try:
            with transaction.atomic():
                appointment = form.save(commit=False)
                
                # Get the selected timeslot ID
                timeslot_id = form.cleaned_data.get('timeslot_id')
                if not timeslot_id:
                    form.add_error(None, 'Time slot selection is required')
                    return self.form_invalid(form)

                try:
                    timeslot = DoctorTimeSlot.objects.get(id=timeslot_id)
                except DoctorTimeSlot.DoesNotExist:
                    form.add_error(None, 'Selected time slot is invalid')
                    return self.form_invalid(form)

                # Verify timeslot is still available
                if not timeslot.is_available:
                    form.add_error(None, 'This time slot is no longer available')
                    return self.form_invalid(form)

                # Set the timeslot and mark it as unavailable
                appointment.time_slot = timeslot
                timeslot.is_available = False
                timeslot.save()
                
                appointment.save()
                messages.success(self.request, 'Appointment created successfully!')
                return super().form_valid(form)
                
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            messages.error(self.request, 'Error creating appointment. Please try again.')
            return self.form_invalid(form)

@api_view(['GET'])
def get_doctor_timeslots(request):
    """
    Get all timeslots for a doctor on a specific date.
    Required query parameters:
    - user_id: ID of the doctor
    - date: Date in YYYY-MM-DD format
    """
    logger.info("Fetching doctor timeslots")
    
    try:
        # Get and validate user_id
        user_id = request.GET.get('user_id')
        if not user_id:
            logger.error("No user_id provided")
            return Response(
                {"error": "user_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get and validate date
        date_str = request.GET.get('date')
        if not date_str:
            logger.error("No date provided")
            return Response(
                {"error": "date is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} not found")
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is a doctor
        if not user.role.name == 'DOCTOR':
            logger.error(f"User {user_id} is not a doctor")
            return Response(
                {"error": "User is not a doctor"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get doctor profile
        try:
            doctor_profile = user.doctor_profile
        except DoctorProfile.DoesNotExist:
            logger.error(f"Doctor profile not found for user {user_id}")
            return Response(
                {"error": "Doctor profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all timeslots for the doctor on the specified date
        timeslots = DoctorTimeSlot.objects.filter(
            doctor=doctor_profile,
            date=date
        ).order_by('start_time')

        # Serialize the timeslots
        timeslots_data = [{
            'id': slot.id,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_available': slot.is_available
        } for slot in timeslots]

        logger.info(f"Successfully retrieved {len(timeslots_data)} timeslots for doctor {user_id}")
        return Response({
            'doctor_name': user.get_full_name(),
            'date': date_str,
            'timeslots': timeslots_data
        })

    except Exception as e:
        logger.exception(f"Unexpected error in get_doctor_timeslots: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
def update_doctor_timeslot(request, timeslot_id):
    """
    Update a doctor's timeslot availability
    Required path parameter:
    - timeslot_id: ID of the timeslot to update
    Required body parameter:
    - is_available: boolean
    """
    logger.info(f"Updating doctor timeslot {timeslot_id}")
    
    try:
        # Get the timeslot
        try:
            timeslot = DoctorTimeSlot.objects.get(id=timeslot_id)
        except DoctorTimeSlot.DoesNotExist:
            logger.error(f"Timeslot with id {timeslot_id} not found")
            return Response(
                {"error": "Timeslot not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get and validate is_available from request body
        is_available = request.data.get('is_available')
        if is_available is None:
            logger.error("No is_available value provided")
            return Response(
                {"error": "is_available is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the timeslot
        timeslot.is_available = is_available
        timeslot.save()

        # Return updated timeslot data
        response_data = {
            'id': timeslot.id,
            'doctor_name': timeslot.doctor.user.get_full_name(),
            'date': timeslot.date,
            'start_time': timeslot.start_time.strftime('%H:%M'),
            'end_time': timeslot.end_time.strftime('%H:%M'),
            'is_available': timeslot.is_available
        }

        logger.info(f"Successfully updated timeslot {timeslot_id}")
        return Response(response_data)

    except Exception as e:
        logger.exception(f"Unexpected error in update_doctor_timeslot: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
def update_appointment_timeslot(request, appointment_id):
    """
    Update an appointment's time slot
    Required path parameter:
    - appointment_id: ID of the appointment to update
    Required body parameter:
    - timeslot_id: ID of the new timeslot
    """
    logger.info(f"Updating appointment {appointment_id} time slot")
    
    try:
        # Get the appointment
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            logger.error(f"Appointment with id {appointment_id} not found")
            return Response(
                {"error": "Appointment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get and validate timeslot_id from request body
        timeslot_id = request.data.get('timeslot_id')
        if timeslot_id is None:
            logger.error("No timeslot_id provided")
            return Response(
                {"error": "timeslot_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the timeslot
        try:
            timeslot = DoctorTimeSlot.objects.get(id=timeslot_id)
        except DoctorTimeSlot.DoesNotExist:
            logger.error(f"TimeSlot with id {timeslot_id} not found")
            return Response(
                {"error": "TimeSlot not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify timeslot is available
        if not timeslot.is_available:
            logger.error(f"TimeSlot {timeslot_id} is not available")
            return Response(
                {"error": "TimeSlot is not available"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the appointment
        with transaction.atomic():
            # Make old timeslot available if it exists
            if appointment.time_slot:
                old_timeslot = appointment.time_slot
                old_timeslot.is_available = True
                old_timeslot.save()

            # Update appointment with new timeslot
            appointment.time_slot = timeslot
            appointment.save()

            # Mark new timeslot as unavailable
            timeslot.is_available = False
            timeslot.save()

        # Return updated appointment data
        response_data = {
            'id': appointment.id,
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': appointment.doctor.get_full_name(),
            'date': appointment.date,
            'timeslot': {
                'id': timeslot.id,
                'start_time': timeslot.start_time.strftime('%H:%M'),
                'end_time': timeslot.end_time.strftime('%H:%M')
            }
        }

        logger.info(f"Successfully updated appointment {appointment_id} time slot")
        return Response(response_data)

    except Exception as e:
        logger.exception(f"Unexpected error in update_appointment_timeslot: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def update_appointment_status(request, appointment_id):
    """Update an appointment's status"""
    logger.info(f"Starting status update for appointment {appointment_id}")
    logger.debug(f"Request data: {request.data}")
    
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        new_status = request.data.get('status')
        old_status = appointment.status
        
        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        # Status-specific messages
        status_messages = {
            'CONFIRMED': {
                'success': 'Appointment confirmed successfully. Patient will be notified.',
                'log': f'Appointment {appointment_id} confirmed by {request.user.get_full_name()}'
            },
            'CANCELLED': {
                'success': 'Appointment cancelled successfully. All parties will be notified.',
                'log': f'Appointment {appointment_id} cancelled by {request.user.get_full_name()}'
            },
            'COMPLETED': {
                'success': 'Appointment marked as completed successfully.',
                'log': f'Appointment {appointment_id} marked as completed by {request.user.get_full_name()}'
            },
            'NO_SHOW': {
                'success': 'Patient marked as no-show for this appointment.',
                'log': f'Appointment {appointment_id} marked as no-show by {request.user.get_full_name()}'
            }
        }

        # Handle cancellation
        if new_status == 'CANCELLED':
            reason = request.data.get('reason')
            if not reason:
                return Response({"error": "Cancellation reason is required"}, status=400)
            
            try:
                with transaction.atomic():
                    appointment.status = new_status
                    appointment.save()
                    
                    CancellationReason.objects.create(
                        appointment=appointment,
                        reason=reason,
                        cancelled_by=request.user
                    )
                    
                    if appointment.time_slot:
                        appointment.time_slot.is_available = True
                        appointment.time_slot.save()
                        logger.info(f"Released time slot for cancelled appointment {appointment_id}")

                    messages.warning(request, f"Appointment cancelled - {reason}")
                    logger.info(status_messages[new_status]['log'])
            except Exception as e:
                logger.error(f"Failed to cancel appointment: {str(e)}")
                return Response({"error": "Failed to cancel appointment"}, status=500)
        else:
            # Handle other status updates
            try:
                appointment.status = new_status
                appointment.save()
                
                # Add appropriate messages based on status
                if new_status == 'CONFIRMED':
                    messages.success(request, status_messages[new_status]['success'])
                elif new_status == 'COMPLETED':
                    messages.success(request, status_messages[new_status]['success'])
                elif new_status == 'NO_SHOW':
                    messages.warning(request, status_messages[new_status]['success'])
                
                logger.info(status_messages.get(new_status, {}).get('log', f'Status updated to {new_status}'))
            except Exception as e:
                logger.error(f"Failed to update status: {str(e)}")
                return Response({"error": "Failed to update status"}, status=500)

        # Return success response with detailed message
        return Response({
            "status": "success",
            "message": status_messages.get(new_status, {}).get('success', f'Status updated to {new_status}'),
            "appointment": {
                "id": appointment.id,
                "new_status": new_status,
                "old_status": old_status,
                "patient_name": appointment.patient.get_full_name(),
                "doctor_name": appointment.doctor.get_full_name(),
                "date": appointment.date,
                "time": appointment.time_slot.start_time if appointment.time_slot else None
            }
        })

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return Response({"error": "An unexpected error occurred"}, status=500)

class AppointmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_delete(self.request.user, 'appointment_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_delete(self.request.user, 'appointment_management'):
            messages.error(request, "You don't have permission to delete appointments")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment_number = appointment.id  # Store for message

            with transaction.atomic():
                # If there's a time slot, mark it as available again
                if appointment.time_slot:
                    appointment.time_slot.is_available = True
                    appointment.time_slot.save()
                    logger.info(f"Released time slot for appointment {appointment_id}")
                
                appointment.delete()
            
            messages.success(request, f"Appointment #{appointment_number} deleted successfully")
            return redirect('appointment_dashboard')
            
        except Exception as e:
            logger.error(f"Error deleting appointment: {str(e)}")
            messages.error(request, f"Error deleting appointment: {str(e)}")
            return redirect('appointment_dashboard')


