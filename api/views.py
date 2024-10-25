import logging
from datetime import datetime, timedelta

# Django and DRF imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DatabaseError
from django.shortcuts import render, get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Custom authentication
from .custom_auth import CustomTokenAuthentication

# Serializers
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, PatientSerializer,
    SubscriptionSerializer, BasicUserInfoUpdateSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from patient_management.serializers import (
    MedicalHistorySerializer, MedicationSerializer, VitiligoAssessmentSerializer, TreatmentPlanSerializer
)
from appointment_management.serializers import (
    AppointmentSerializer, AppointmentCreateSerializer, DoctorTimeSlotSerializer, DoctorTimeSlotDetailSerializer
)
from user_management.serializers import CustomUserSerializer
from query_management.serializers import QuerySerializer
from doctor_management.serializers import (
    DoctorListSerializer, DoctorDetailSerializer, SpecializationSerializer, TreatmentMethodSerializer,
    BodyAreaSerializer, AssociatedConditionSerializer
)

# Models
from subscription_management.models import Subscription, SubscriptionTier
from patient_management.models import (
    Patient, MedicalHistory, Medication, VitiligoAssessment, TreatmentPlan
)
from appointment_management.models import Appointment, DoctorTimeSlot
from query_management.models import Query
from doctor_management.models import (
    DoctorProfile, Specialization, TreatmentMethodSpecialization, BodyAreaSpecialization, AssociatedConditionSpecialization
)

User = get_user_model()
logger = logging.getLogger(__name__)

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           AUTHENTICATION VIEWS                                ║
║ Contains all authentication related functionality including user registration,║
║ login, password management, and basic user operations.                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""


class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Received user registration request")
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            if user.role == 'PATIENT':
                logger.info(f"Creating free subscription for patient: {user.email}")
                try:
                    free_tier = SubscriptionTier.objects.get(name='Free')
                    subscription = Subscription.objects.create(
                        user=user,
                        tier=free_tier,
                        start_date=timezone.now(),
                        end_date=timezone.now() + timezone.timedelta(days=free_tier.duration_days),
                        is_trial=True,
                        trial_end_date=timezone.now() + timezone.timedelta(days=free_tier.duration_days)
                    )
                    logger.info(f"Free subscription created for patient: {user.email}")
                except SubscriptionTier.DoesNotExist:
                    logger.error("Free subscription tier not found")
                except Exception as e:
                    logger.error(f"Error creating free subscription for patient: {user.email}. Error: {str(e)}")

            logger.info(f"User registered successfully: {user.email}")
            return Response({
                'status': 'success',
                'message': 'User registered successfully',
                'data': {
                    'token': token.key,
                    'user_id': user.pk,
                    'email': user.email,
                    'role': user.role
                }
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"User registration failed. Errors: {serializer.errors}")
        return Response({
            'status': 'error',
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'status': 'success',
                'message': 'Login successful',
                'data': {
                    'token': token.key,
                    'user_id': user.pk,
                    'email': user.email,
                    'role': user.role
                }
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Login failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = CustomUserSerializer(user).data
        response_data = {'user': user_data}

        # Attempt to get patient data
        try:
            patient = Patient.objects.get(user=user)
            response_data['patient'] = PatientSerializer(patient).data
        except Patient.DoesNotExist:
            response_data['patient'] = None

        # Attempt to get subscription data
        try:
            subscription = Subscription.objects.get(user=user)
            response_data['subscription'] = SubscriptionSerializer(subscription).data
        except Subscription.DoesNotExist:
            response_data['subscription'] = None

        # Add role-specific message
        if user.role == 'PATIENT':
            if response_data['patient'] is None:
                response_data['message'] = "Patient profile not found. Please complete your profile."
            elif response_data['subscription'] is None:
                response_data['message'] = "No active subscription found. Please subscribe to access full features."
        else:
            response_data['message'] = f"User role is {user.role}. Additional role-specific data will be implemented in the future."

        return Response(response_data, status=status.HTTP_200_OK)


class BasicUserInfoUpdateAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = BasicUserInfoUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
        try:
            if serializer.is_valid():
                # Check if password is being updated
                if 'password' in serializer.validated_data:
                    user.set_password(serializer.validated_data['password'])
                    serializer.validated_data.pop('password')

                serializer.save()
                logger.info(f"User {user.id} information updated successfully")
                return Response({
                    'status': 'success',
                    'message': 'User information updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"User {user.id} update failed: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Update failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating user {user.id} information: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        logger.info("Password reset request received")
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            logger.info(f"Processing password reset request for email: {email}")
            try:
                user = User.objects.filter(email=email).first()
                if user:
                    logger.info(f"User found for email: {email}")
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    # Check if FRONTEND_URL is set
                    if not hasattr(settings, 'FRONTEND_URL') or not settings.FRONTEND_URL:
                        logger.error("FRONTEND_URL is not set in settings")
                        return Response({
                            "error": "Server configuration error. Please contact the administrator."
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    reset_link = f"{settings.FRONTEND_URL}/api/reset-password/{uid}/{token}/"
                    logger.info(f"Reset link generated: {reset_link}")

                    # Send email
                    subject = "Password Reset Request"
                    message = f"Please use this link to reset your password: {reset_link}"
                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                        logger.info(f"Password reset email sent to: {email}")
                    except Exception as e:
                        logger.error(f"Failed to send password reset email: {str(e)}", exc_info=True)
                        return Response({
                            "error": "Failed to send password reset email. Please try again later."
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.info(f"No user found for email: {email}")

                return Response({
                    "message": "If an account exists with this email, a password reset link has been sent."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error processing password reset request: {str(e)}", exc_info=True)
                return Response({
                    "error": "An unexpected error occurred. Please try again later."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Invalid password reset request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    template_name = 'password_reset/password_reset_confirm.html'

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            context = {
                'valid': True,
                'uidb64': uidb64,
                'token': token,
            }
        else:
            context = {'valid': False}

        return render(request, self.template_name, context)

    def post(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)


"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                             PATIENT VIEWS                                    ║
║ Handles all patient-specific operations including profile management,        ║
║ medical history, and patient-specific data retrieval.                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


class PatientInfoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'PATIENT':
            return Response({"error": "Only patients can access this information"}, status=status.HTTP_403_FORBIDDEN)

        try:
            patient = Patient.objects.get(user=user)
            response_data = self.get_patient_data(patient)
            return Response(response_data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            logger.warning(f"Patient profile not found for user {user.id}")
            return Response({"error": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving patient information for user {user.id}: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_patient_data(self, patient):
        data = {
            "patient": PatientSerializer(patient).data,
            "medical_history": self.get_medical_history(patient),
            "medications": self.get_medications(patient),
            "vitiligo_assessments": self.get_vitiligo_assessments(patient),
            "treatment_plans": self.get_treatment_plans(patient)
        }
        return data

    def get_medical_history(self, patient):
        try:
            medical_history = MedicalHistory.objects.get(patient=patient)
            return MedicalHistorySerializer(medical_history).data
        except MedicalHistory.DoesNotExist:
            return None

    def get_medications(self, patient):
        medications = Medication.objects.filter(patient=patient)
        return MedicationSerializer(medications, many=True).data

    def get_vitiligo_assessments(self, patient):
        assessments = VitiligoAssessment.objects.filter(patient=patient).order_by('-assessment_date')
        return VitiligoAssessmentSerializer(assessments, many=True).data

    def get_treatment_plans(self, patient):
        plans = TreatmentPlan.objects.filter(patient=patient).order_by('-created_date')
        return TreatmentPlanSerializer(plans, many=True).data
    

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           APPOINTMENT VIEWS                                  ║
║ Handles all appointment-related operations including scheduling, viewing,    ║
║ and managing appointments.                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


class UserAppointmentsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'PATIENT':
            return Response({"error": "Only patients can access this information"}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointments = Appointment.objects.filter(patient=user)
            if not appointments.exists():
                return Response({"error": "No appointments found"}, status=status.HTTP_404_NOT_FOUND)
            
            response_data = AppointmentSerializer(appointments, many=True).data
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving appointments for user {user.id}: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAppointmentDetailView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        user = request.user
        if user.role != 'PATIENT':
            return Response({"error": "Only patients can access this information"}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=user)
            response_data = AppointmentSerializer(appointment).data
            return Response(response_data, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving appointment {appointment_id} for user {user.id}: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DoctorAvailableTimeSlotsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        
        if not all([doctor_id, date_str]):
            return Response(
                {"error": "Both doctor_id and date parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get the user with role DOCTOR
            user = User.objects.get(id=doctor_id, role='DOCTOR')
            doctor = user.doctor_profile
            
            # Get all available time slots for the doctor on the given date
            available_slots = DoctorTimeSlot.objects.filter(
                doctor=doctor,
                date=date,
                is_available=True
            ).order_by('start_time')
            
            # If no slots exist for this date, generate them based on doctor's availability
            if not available_slots.exists():
                day_of_week = date.weekday()
                availabilities = doctor.availability.filter(
                    day_of_week=day_of_week,
                    is_available=True
                )
                
                new_slots = []
                for availability in availabilities:
                    current_time = availability.start_time
                    while current_time < availability.end_time:
                        end_time = (
                            datetime.combine(date, current_time) + 
                            timedelta(minutes=30)
                        ).time()
                        
                        if end_time <= availability.end_time:
                            new_slots.append(DoctorTimeSlot(
                                doctor=doctor,
                                date=date,
                                start_time=current_time,
                                end_time=end_time
                            ))
                        
                        current_time = end_time
                
                if new_slots:
                    DoctorTimeSlot.objects.bulk_create(new_slots)
                    available_slots = DoctorTimeSlot.objects.filter(
                        doctor=doctor,
                        date=date,
                        is_available=True
                    ).order_by('start_time')
            
            serializer = DoctorTimeSlotSerializer(available_slots, many=True)
            return Response({
                'status': 'success',
                'message': 'Available time slots retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {"error": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving available time slots: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DoctorTimeSlotDetailView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, slot_id):
        try:
            # Fetch the time slot by ID
            time_slot = DoctorTimeSlot.objects.get(id=slot_id)
            serializer = DoctorTimeSlotDetailSerializer(time_slot)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except DoctorTimeSlot.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Time slot not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving time slot {slot_id}: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AppointmentTypesView(APIView):
    def get(self, request):
        types = [{'value': choice[0], 'label': choice[1]} for choice in Appointment.APPOINTMENT_TYPES]
        return Response(types, status=status.HTTP_200_OK)


class AppointmentStatusView(APIView):
    def get(self, request):
        statuses = [{'value': choice[0], 'label': choice[1]} for choice in Appointment.STATUS_CHOICES]
        return Response(statuses, status=status.HTTP_200_OK)


class AppointmentPriorityView(APIView):
    def get(self, request):
        priorities = [{'value': choice[0], 'label': choice[1]} for choice in Appointment.PRIORITY_CHOICES]
        return Response(priorities, status=status.HTTP_200_OK)
        

class CreateAppointmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        try:
            if serializer.is_valid():
                appointment = serializer.save(patient=request.user)
                
                # Update the DoctorTimeSlot to mark it as unavailable
                doctor_time_slot = appointment.time_slot
                doctor_time_slot.is_available = False
                doctor_time_slot.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DoctorTimeSlot.DoesNotExist:
            return Response({"error": "Time slot does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              DOCTOR VIEWS                                    ║
║ Manages doctor-related operations including listings, profiles, and          ║
║ specialization information.                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


class DoctorListView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Valid parameter mappings
    PARAM_MAPPINGS = {
        'specialization': {
            'model': Specialization,
            'filter_field': 'specializations__id'
        },
        'treatment_method': {
            'model': TreatmentMethodSpecialization,
            'filter_field': 'treatment_methods__id'
        },
        'body_area': {
            'model': BodyAreaSpecialization,
            'filter_field': 'body_areas__id'
        },
        'associated_condition': {
            'model': AssociatedConditionSpecialization,
            'filter_field': 'associated_conditions__id'
        }
    }

    def normalize_param_name(self, param_name):
        """Normalize parameter names to handle different formats"""
        return param_name.replace('-', '_')

    def validate_param_name(self, param_name):
        """Validate if the parameter name is valid"""
        normalized_name = self.normalize_param_name(param_name)
        if normalized_name not in self.PARAM_MAPPINGS:
            return False, f"Invalid parameter: '{param_name}'. Valid parameters are: {', '.join(self.PARAM_MAPPINGS.keys())}"
        return True, normalized_name

    def validate_single_param(self, param_name, param_value, model):
        """Validate a single filter parameter value"""
        try:
            param_id = int(param_value)
            if not model.objects.filter(id=param_id, is_active=True).exists():
                return None, f"Invalid {param_name} ID: {param_value} (ID does not exist)"
            return param_id, None
        except (ValueError, TypeError):
            return None, f"Invalid {param_name} parameter: {param_value} (must be an integer)"

    def get(self, request):
        try:
            # First, validate all parameters in the request
            unknown_params = []
            for param_name in request.query_params.keys():
                is_valid, _ = self.validate_param_name(param_name)
                if not is_valid:
                    unknown_params.append(param_name)
            
            if unknown_params:
                return Response({
                    'status': 'error',
                    'error': f"Unknown parameter(s): {', '.join(unknown_params)}",
                    'valid_parameters': list(self.PARAM_MAPPINGS.keys())
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check for any valid filter parameters
            filter_param = None
            filter_value = None
            
            for key, value in request.query_params.items():
                is_valid, normalized_key = self.validate_param_name(key)
                if is_valid:
                    filter_param = normalized_key
                    filter_value = value
                    break

            # If a filter parameter is found, validate and apply it
            if filter_param and filter_value:
                mapping = self.PARAM_MAPPINGS[filter_param]
                param_id, error = self.validate_single_param(
                    filter_param,
                    filter_value,
                    mapping['model']
                )

                if error:
                    return Response({
                        'status': 'error',
                        'error': error
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Get filtered doctors
                doctors = DoctorProfile.objects.select_related('user').prefetch_related(
                    'specializations',
                    'treatment_methods',
                    'body_areas',
                    'associated_conditions'
                ).filter(
                    user__role='DOCTOR',
                    user__is_active=True,
                    is_available=True,
                    **{mapping['filter_field']: param_id}
                ).distinct()

                serializer = DoctorListSerializer(doctors, many=True)
                return Response({
                    'status': 'success',
                    'filter_applied': {
                        'parameter': filter_param,
                        'value': filter_value,
                        'id': param_id
                    },
                    'count': doctors.count(),
                    'results': serializer.data
                }, status=status.HTTP_200_OK)

            # If no filter parameters are provided, return all active doctors
            doctors = DoctorProfile.objects.select_related('user').prefetch_related(
                'specializations',
                'treatment_methods',
                'body_areas',
                'associated_conditions'
            ).filter(
                user__role='DOCTOR',
                user__is_active=True,
                is_available=True
            )
            
            serializer = DoctorListSerializer(doctors, many=True)
            return Response({
                'status': 'success',
                'filter_applied': None,
                'count': doctors.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in doctor list view: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred',
                'error_details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorDetailView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        try:
            # Get the user with role DOCTOR
            user = get_object_or_404(User, id=doctor_id, role='DOCTOR', is_active=True)
            doctor = get_object_or_404(
                DoctorProfile.objects.select_related('user').prefetch_related(
                    'specializations',
                    'treatment_methods',
                    'body_areas',
                    'associated_conditions',
                    'availability',
                    'reviews__patient'
                ),
                user=user
            )
            
            serializer = DoctorDetailSerializer(doctor)
            return Response({
                'status': 'success',
                'message': 'Doctor details retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response(
                {"error": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": "Doctor profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving doctor details for user ID {doctor_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SpecializationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            specializations = Specialization.objects.filter(is_active=True)
            serializer = SpecializationSerializer(specializations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specializations: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TreatmentMethodListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            treatments = TreatmentMethodSpecialization.objects.filter(is_active=True)
            serializer = TreatmentMethodSerializer(treatments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving treatment methods: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BodyAreaListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            body_areas = BodyAreaSpecialization.objects.filter(is_active=True)
            serializer = BodyAreaSerializer(body_areas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving body areas: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssociatedConditionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            conditions = AssociatedConditionSpecialization.objects.filter(is_active=True)
            serializer = AssociatedConditionSerializer(conditions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving associated conditions: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


""" 
╔══════════════════════════════════════════════════════════════════════════════╗
║                              QUERY VIEWS                                     ║
║ Manages user queries and related operations for patient-doctor               ║
║ communication.                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


class UserQueriesView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            queries = Query.objects.filter(patient=user)
            serializer = QuerySerializer(queries, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)