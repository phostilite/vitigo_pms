# Python Standard Library imports
from collections import defaultdict
from datetime import timedelta, datetime
import logging
import json
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.http import HttpResponse

# Django core imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView


# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from patient_management.models import MedicalHistory
from doctor_management.models import DoctorProfile
from .models import Appointment, CancellationReason, DoctorTimeSlot, AppointmentReminder, ReminderConfiguration, ReminderTemplate

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
        
        # Get filter parameters from URL
        filters = {}
        priority = self.request.GET.get('priority')
        status = self.request.GET.get('status')
        date = self.request.GET.get('date')
        doctor = self.request.GET.get('doctor')
        patient = self.request.GET.get('patient')
        appointment_type = self.request.GET.get('appointment_type')
        search = self.request.GET.get('search')
        
        # Apply filters
        if priority:
            filters['priority'] = priority
        if status:
            filters['status'] = status
        if date:
            filters['date'] = date
        if doctor:
            filters['doctor_id'] = doctor
        if patient:
            filters['patient_id'] = patient
        if appointment_type:
            filters['appointment_type'] = appointment_type
            
        # Apply search query
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(patient__email__icontains=search) |
                Q(doctor__first_name__icontains=search) |
                Q(doctor__last_name__icontains=search) |
                Q(doctor__email__icontains=search) |
                Q(notes__icontains=search)
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
        
        context.update({
            # Add choices for filter dropdowns
            'status_choices': Appointment.STATUS_CHOICES,
            'priority_choices': Appointment.PRIORITY_CHOICES,
            'appointment_type_choices': Appointment.APPOINTMENT_TYPES,
            
            # Add available doctors and patients for filters
            'doctors': User.objects.filter(role__name='DOCTOR').order_by('first_name'),
            'patients': User.objects.filter(role__name='PATIENT').order_by('first_name'),
            
            # Current filter values
            'current_filters': {
                'priority': self.request.GET.get('priority', ''),
                'status': self.request.GET.get('status', ''),
                'date': self.request.GET.get('date', ''),
                'doctor': self.request.GET.get('doctor', ''),
                'patient': self.request.GET.get('patient', ''),
                'appointment_type': self.request.GET.get('appointment_type', ''),
                'search': self.request.GET.get('search', ''),
            }
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

from notifications.services import NotificationService
from notifications.models import NotificationType

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
                
                # Get the selected timeslot
                timeslot_id = form.cleaned_data.get('timeslot_id')
                if not timeslot_id:
                    messages.error(self.request, 'Time slot selection is required')
                    return self.form_invalid(form)

                try:
                    timeslot = DoctorTimeSlot.objects.get(id=timeslot_id)
                except DoctorTimeSlot.DoesNotExist:
                    messages.error(self.request, 'Selected time slot is invalid')
                    return self.form_invalid(form)

                # Additional validation for past time slots
                current_datetime = timezone.now()
                appointment_datetime = timezone.make_aware(
                    datetime.combine(appointment.date, timeslot.start_time)
                )

                if appointment_datetime < current_datetime:
                    messages.error(self.request, 'Cannot create appointments for past time slots')
                    return self.form_invalid(form)

                # Verify timeslot is still available
                if not timeslot.is_available:
                    messages.error(self.request, 'This time slot is no longer available')
                    return self.form_invalid(form)
                
                # Follow-up specific validation
                if appointment.appointment_type == 'FOLLOW_UP':
                    days_until_appointment = (appointment.date - timezone.now().date()).days
                    if days_until_appointment > 30:
                        messages.error(self.request, 'Follow-up appointments cannot be scheduled more than 30 days in advance')
                        return self.form_invalid(form)
                    if days_until_appointment < 1:
                        messages.error(self.request, 'Follow-up appointments must be scheduled at least 1 day in advance')
                        return self.form_invalid(form)

                # Set the timeslot and mark it as unavailable
                appointment.time_slot = timeslot
                timeslot.is_available = False
                timeslot.save()
                
                appointment.save()

                # Create notifications outside the transaction
                self._create_appointment_notifications(appointment)
                
                messages.success(self.request, 'Appointment created successfully!')
                return super().form_valid(form)
                
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            messages.error(self.request, 'Error creating appointment. Please try again.')
            return self.form_invalid(form)

    def _create_appointment_notifications(self, appointment):
        """
        Create notifications for both patient and doctor
        """
        try:
            # Get or create notification types
            appointment_created_type, _ = NotificationType.objects.get_or_create(
                name='APPOINTMENT_CREATED',
                defaults={'description': 'New appointment created'}
            )

            # Patient notification
            patient_message = (
                f"Your appointment with Dr. {appointment.doctor.get_full_name()} "
                f"has been scheduled for {appointment.date} at "
                f"{appointment.time_slot.start_time.strftime('%I:%M %p')}"
            )
            
            success, error = NotificationService.create_notifications(
                user=appointment.patient,
                notification_type=appointment_created_type,
                message=patient_message,
                send_email=True,
                send_sms=True,
                phone_number=appointment.patient.phone_number if hasattr(appointment.patient, 'phone_number') else None
            )

            if not success:
                logger.error(f"Failed to create patient notification: {error}")

            # Doctor notification
            doctor_message = (
                f"New appointment scheduled with {appointment.patient.get_full_name()} "
                f"for {appointment.date} at "
                f"{appointment.time_slot.start_time.strftime('%I:%M %p')}"
            )
            
            success, error = NotificationService.create_notifications(
                user=appointment.doctor,
                notification_type=appointment_created_type,
                message=doctor_message,
                send_email=True
            )

            if not success:
                logger.error(f"Failed to create doctor notification: {error}")

        except Exception as e:
            logger.error(f"Error in _create_appointment_notifications: {str(e)}")
            # Don't raise the exception - we want the appointment to be created even if notifications fail

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
        current_datetime = timezone.now()
        timeslots = DoctorTimeSlot.objects.filter(
            doctor=doctor_profile,
            date=date
        ).order_by('start_time')

        # Filter out past time slots
        timeslots_data = []
        for slot in timeslots:
            slot_datetime = timezone.make_aware(
                datetime.combine(date, slot.start_time)
            )
            
            if slot_datetime > current_datetime:
                timeslots_data.append({
                    'id': slot.id,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'is_available': slot.is_available
                })

        if not timeslots_data:
            return Response({
                'doctor_name': user.get_full_name(),
                'date': date_str,
                'timeslots': [],
                'message': 'No available time slots found for this date.'
            })

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

                    # Create cancellation notifications outside the transaction
                    _create_cancellation_notifications(appointment, reason, request.user)
                    
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

def _create_cancellation_notifications(appointment, reason, cancelled_by):
    """
    Create notifications for appointment cancellation
    """
    try:
        cancellation_type, _ = NotificationType.objects.get_or_create(
            name='APPOINTMENT_CANCELLED',
            defaults={'description': 'Appointment cancelled notification'}
        )

        # Patient notification
        patient_message = (
            f"Your appointment with Dr. {appointment.doctor.get_full_name()} "
            f"for {appointment.date} has been cancelled. Reason: {reason}"
        )
        
        NotificationService.create_notifications(
            user=appointment.patient,
            notification_type=cancellation_type,
            message=patient_message,
            send_email=True,
            send_sms=True,
            phone_number=appointment.patient.phone_number if hasattr(appointment.patient, 'phone_number') else None
        )

        # Doctor notification
        doctor_message = (
            f"Appointment with {appointment.patient.get_full_name()} "
            f"for {appointment.date} has been cancelled by {cancelled_by.get_full_name()}. "
            f"Reason: {reason}"
        )
        
        NotificationService.create_notifications(
            user=appointment.doctor,
            notification_type=cancellation_type,
            message=doctor_message,
            send_email=True
        )

    except Exception as e:
        logger.error(f"Error in _create_cancellation_notifications: {str(e)}")
        # Don't raise the exception - we want the cancellation to proceed even if notifications fail

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

class AppointmentExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def get_filtered_queryset(self, date_range, start_date=None, end_date=None):
        """Filter queryset based on date range"""
        queryset = Appointment.objects.select_related('patient', 'doctor', 'time_slot')

        if date_range == 'custom':
            if not start_date or not end_date:
                raise ValueError("Both start date and end date are required for custom range")
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(date__range=[start_datetime, end_datetime])
            except ValueError as e:
                raise ValueError(f"Invalid date format: {str(e)}")
        else:
            try:
                days = int(date_range or '30')
                if days <= 0:
                    raise ValueError("Days must be a positive number")
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=days)
                queryset = queryset.filter(date__range=[start_date, end_date])
            except ValueError:
                raise ValueError("Invalid date range value")

        return queryset

    def get(self, request):
        try:
            export_format = request.GET.get('format', 'csv')
            date_range = request.GET.get('date_range')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            queryset = self.get_filtered_queryset(date_range, start_date, end_date)

            if export_format == 'csv':
                return self.export_csv(queryset)
            elif export_format == 'pdf':
                return self.export_pdf(queryset)
            else:
                messages.error(request, "Invalid export format")
                return redirect('appointment_dashboard')

        except Exception as e:
            messages.error(request, f"Export failed: {str(e)}")
            return redirect('appointment_dashboard')

    def export_csv(self, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="appointments_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Appointment ID',
            'Patient Name',
            'Doctor Name',
            'Date',
            'Time',
            'Type',
            'Status',
            'Priority',
            'Notes',
            'Created At',
            'Last Updated',
            'Cancellation Reason'
        ])

        for appointment in queryset:
            cancellation_reason = appointment.cancellation_reason.reason if hasattr(appointment, 'cancellation_reason') else 'N/A'
            writer.writerow([
                appointment.id,
                appointment.patient.get_full_name(),
                appointment.doctor.get_full_name(),
                appointment.date,
                appointment.time_slot.start_time if appointment.time_slot else 'N/A',
                appointment.get_appointment_type_display(),
                appointment.get_status_display(),
                appointment.get_priority_display(),
                appointment.notes or 'N/A',
                appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                cancellation_reason
            ])

        return response

    def export_pdf(self, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="appointments_report.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        normal_style = styles['Normal']

        # Title
        elements.append(Paragraph('Appointments Report', title_style))
        elements.append(Spacer(1, 20))

        # Statistics
        stats = [
            ['Total Appointments:', str(queryset.count())],
            ['Pending Appointments:', str(queryset.filter(status='PENDING').count())],
            ['Completed Appointments:', str(queryset.filter(status='COMPLETED').count())],
            ['Cancelled Appointments:', str(queryset.filter(status='CANCELLED').count())]
        ]

        stats_table = Table(stats, colWidths=[150, 100])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),  # Changed from colors.grey
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Appointments table
        data = [['Date', 'Time', 'Patient', 'Doctor', 'Type', 'Status']]
        for appointment in queryset:
            data.append([
                appointment.date.strftime('%Y-%m-%d'),
                appointment.time_slot.start_time.strftime('%H:%M') if appointment.time_slot else 'N/A',
                appointment.patient.get_full_name(),
                appointment.doctor.get_full_name(),
                appointment.get_appointment_type_display(),
                appointment.get_status_display()
            ])

        table = Table(data, colWidths=[70, 50, 100, 100, 80, 80])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),  # Light gray background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Changed text color
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        return response

class AppointmentReminderView(LoginRequiredMixin, ListView):
    model = ReminderTemplate
    context_object_name = 'reminder_templates'

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(self.request.user, 'appointment_management'):
            messages.error(request, "You don't have permission to access appointment reminders")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path('appointment_reminders.html', self.request.user.role, 'appointment_management')]

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            
            # Add reminder-related data
            context.update({
                'appointment_types': dict(Appointment.APPOINTMENT_TYPES),
                'reminder_configs': ReminderConfiguration.objects.select_related().all(),
                
                # Statistics
                'total_templates': ReminderTemplate.objects.count(),
                'active_templates': ReminderTemplate.objects.filter(is_active=True).count(),
                'total_reminders': AppointmentReminder.objects.count(),
                'pending_reminders': AppointmentReminder.objects.filter(status='PENDING').count(),
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error in AppointmentReminderView context: {str(e)}")
            messages.error(self.request, "Error loading reminder data")
            return {}

from .forms import ReminderTemplateForm

class CreateReminderTemplateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            form = ReminderTemplateForm(request.POST)
            if form.is_valid():
                template = form.save(commit=False)
                template.created_by = request.user
                template.save()
                
                messages.success(request, 'Reminder template created successfully!')
                return redirect('appointment_reminders')
            else:
                messages.error(request, 'Failed to create template. Please check the form data.')
                return redirect('appointment_reminders')
        except Exception as e:
            logger.error(f"Error creating reminder template: {str(e)}")
            messages.error(request, 'An error occurred while creating the template.')
            return redirect('appointment_reminders')

from .forms import ReminderConfigurationForm

class ConfigureReminderSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        configs = ReminderConfiguration.objects.all()
        return JsonResponse({
            'configs': list(configs.values('id', 'appointment_type', 'reminder_types', 'is_active')),
            'templates': list(ReminderTemplate.objects.filter(is_active=True).values('id', 'name'))
        })

    def post(self, request):
        try:
            appointment_type = request.POST.get('appointment_type')
            template_ids = request.POST.getlist('templates')
            
            # Fix: Properly handle notification methods
            reminder_types = {
                'email': request.POST.get('notification_email') == 'on',
                'sms': request.POST.get('notification_sms') == 'on'
            }
            
            # Fix: Properly handle active status
            is_active = request.POST.get('is_active') == 'on'

            config, created = ReminderConfiguration.objects.update_or_create(
                appointment_type=appointment_type,
                defaults={
                    'reminder_types': reminder_types,
                    'is_active': is_active
                }
            )
            
            # Update templates
            config.templates.set(template_ids)
            
            messages.success(request, 'Reminder settings updated successfully!')
            return redirect('appointment_reminders')
            
        except Exception as e:
            logger.error(f"Error configuring reminder settings: {str(e)}")
            messages.error(request, 'Failed to update reminder settings')
            return redirect('appointment_reminders')

class DeleteReminderTemplateView(LoginRequiredMixin, View):
    def post(self, request, template_id):
        try:
            template = get_object_or_404(ReminderTemplate, id=template_id)
            template_name = template.name
            
            # Check if template is being used in any configurations
            if template.configurations.exists():
                messages.error(request, 'Cannot delete template as it is being used in active configurations.')
                return redirect('appointment_reminders')
            
            template.delete()
            messages.success(request, f'Template "{template_name}" deleted successfully.')
            return redirect('appointment_reminders')
            
        except Exception as e:
            logger.error(f"Error deleting reminder template: {str(e)}")
            messages.error(request, 'Failed to delete template.')
            return redirect('appointment_reminders')

class DeleteReminderConfigurationView(LoginRequiredMixin, View):
    def post(self, request, config_id):
        try:
            config = get_object_or_404(ReminderConfiguration, id=config_id)
            appointment_type = config.get_appointment_type_display()
            
            # Remove template associations first
            config.templates.clear()
            config.delete()
            
            messages.success(request, f'Configuration for "{appointment_type}" deleted successfully.')
            return redirect('appointment_reminders')
            
        except Exception as e:
            logger.error(f"Error deleting reminder configuration: {str(e)}")
            messages.error(request, 'Failed to delete configuration.')
            return redirect('appointment_reminders')

class EditReminderTemplateView(LoginRequiredMixin, View):
    def get(self, request, template_id):
        template = get_object_or_404(ReminderTemplate, id=template_id)
        return JsonResponse({
            'id': template.id,
            'name': template.name,
            'days_before': template.days_before,
            'hours_before': template.hours_before,
            'message_template': template.message_template,
            'is_active': template.is_active,
        })
    
    def post(self, request, template_id):
        try:
            template = get_object_or_404(ReminderTemplate, id=template_id)
            form = ReminderTemplateForm(request.POST, instance=template)
            
            if form.is_valid():
                template = form.save()
                messages.success(request, f'Template "{template.name}" updated successfully.')
                return redirect('appointment_reminders')
            else:
                messages.error(request, 'Failed to update template. Please check the form data.')
                return redirect('appointment_reminders')
                
        except Exception as e:
            logger.error(f"Error updating reminder template: {str(e)}")
            messages.error(request, 'Failed to update template.')
            return redirect('appointment_reminders')

class EditReminderConfigurationView(LoginRequiredMixin, View):
    def get(self, request, config_id):
        config = get_object_or_404(ReminderConfiguration, id=config_id)
        return JsonResponse({
            'id': config.id,
            'appointment_type': config.appointment_type,
            'templates': list(config.templates.values_list('id', flat=True)),
            'reminder_types': config.reminder_types,
            'is_active': config.is_active
        })

    def post(self, request, config_id):
        try:
            config = get_object_or_404(ReminderConfiguration, id=config_id)
            
            # Update basic fields
            config.appointment_type = request.POST.get('appointment_type')
            config.reminder_types = {
                'email': request.POST.get('notification_email') == 'on',
                'sms': request.POST.get('notification_sms') == 'on'
            }
            config.is_active = request.POST.get('is_active') == 'on'
            
            # Update template associations
            template_ids = request.POST.getlist('templates')
            
            with transaction.atomic():
                config.save()
                config.templates.set(template_ids)
            
            messages.success(request, f'Configuration for "{config.get_appointment_type_display()}" updated successfully.')
            return redirect('appointment_reminders')
            
        except Exception as e:
            logger.error(f"Error updating reminder configuration: {str(e)}")
            messages.error(request, 'Failed to update configuration.')
            return redirect('appointment_reminders')

class AppointmentExportSingleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def get(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            export_format = request.GET.get('format', 'csv')

            if export_format == 'csv':
                return self.export_csv(appointment)
            elif export_format == 'pdf':
                return self.export_pdf(appointment)
            else:
                messages.error(request, "Invalid export format")
                return redirect('appointment_dashboard')

        except Exception as e:
            messages.error(request, f"Export failed: {str(e)}")
            return redirect('appointment_dashboard')

    def export_csv(self, appointment):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Appointment ID',
            'Patient Name',
            'Doctor Name',
            'Date',
            'Time',
            'Type',
            'Status',
            'Priority',
            'Notes',
            'Created At',
            'Last Updated',
            'Cancellation Reason'
        ])

        # Get cancellation reason if exists
        cancellation_reason = appointment.cancellation_reason.reason if hasattr(appointment, 'cancellation_reason') else 'N/A'

        writer.writerow([
            appointment.id,
            appointment.patient.get_full_name(),
            appointment.doctor.get_full_name(),
            appointment.date,
            appointment.time_slot.start_time if appointment.time_slot else 'N/A',
            appointment.get_appointment_type_display(),
            appointment.get_status_display(),
            appointment.get_priority_display(),
            appointment.notes or 'N/A',
            appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            cancellation_reason
        ])

        return response

    def export_pdf(self, appointment):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']

        # Title
        elements.append(Paragraph(f'Appointment Details - #{appointment.id}', title_style))
        elements.append(Spacer(1, 20))

        # Basic Info
        elements.append(Paragraph('Basic Information', subtitle_style))
        elements.append(Spacer(1, 10))

        data = [
            ['Patient Name:', appointment.patient.get_full_name()],
            ['Doctor Name:', appointment.doctor.get_full_name()],
            ['Date:', appointment.date.strftime('%B %d, %Y')],
            ['Time:', appointment.time_slot.start_time.strftime('%I:%M %p') if appointment.time_slot else 'N/A'],
            ['Type:', appointment.get_appointment_type_display()],
            ['Status:', appointment.get_status_display()],
            ['Priority:', appointment.get_priority_display()]
        ]

        # Create table for basic info
        table = Table(data, colWidths=[120, 300])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Notes Section
        if appointment.notes:
            elements.append(Paragraph('Notes', subtitle_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(appointment.notes, normal_style))
            elements.append(Spacer(1, 20))

        # Cancellation Info
        if hasattr(appointment, 'cancellation_reason'):
            elements.append(Paragraph('Cancellation Information', subtitle_style))
            elements.append(Spacer(1, 10))
            cancel_data = [
                ['Reason:', appointment.cancellation_reason.reason],
                ['Cancelled By:', appointment.cancellation_reason.cancelled_by.get_full_name()],
                ['Cancelled At:', appointment.cancellation_reason.cancelled_at.strftime('%B %d, %Y %I:%M %p')]
            ]
            cancel_table = Table(cancel_data, colWidths=[120, 300])
            cancel_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(cancel_table)

        doc.build(elements)
        return response

class AppointmentRescheduleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def post(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            new_timeslot_id = request.POST.get('timeslot_id')

            if not new_timeslot_id:
                messages.error(request, 'Please select a new time slot')
                return redirect('appointment_dashboard')

            try:
                new_timeslot = DoctorTimeSlot.objects.get(id=new_timeslot_id)
            except DoctorTimeSlot.DoesNotExist:
                messages.error(request, 'Selected time slot is invalid')
                return redirect('appointment_dashboard')

            if not new_timeslot.is_available:
                messages.error(request, 'Selected time slot is no longer available')
                return redirect('appointment_dashboard')

            with transaction.atomic():
                # Make the old timeslot available
                if appointment.time_slot:
                    old_timeslot = appointment.time_slot
                    old_timeslot.is_available = True
                    old_timeslot.save()

                # Update appointment with new timeslot
                appointment.time_slot = new_timeslot
                appointment.date = new_timeslot.date
                appointment.save()

                # Mark new timeslot as unavailable
                new_timeslot.is_available = False
                new_timeslot.save()

            messages.success(request, 'Appointment rescheduled successfully')
            return redirect('appointment_dashboard')

        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            messages.error(request, 'Error rescheduling appointment')
            return redirect('appointment_dashboard')