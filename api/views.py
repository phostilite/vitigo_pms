import logging

# Django and DRF imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
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
    AppointmentSerializer, TimeSlotSerializer, AppointmentCreateSerializer
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
from appointment_management.models import Appointment, TimeSlot
from query_management.models import Query
from doctor_management.models import (
    DoctorProfile, Specialization, TreatmentMethodSpecialization, BodyAreaSpecialization, AssociatedConditionSpecialization
)

User = get_user_model()
logger = logging.getLogger(__name__)

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
        

class AvailableTimeSlotsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get('date')
        if not date:
            return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            available_time_slots = [time_slot for time_slot in TimeSlot.objects.all() if time_slot.is_available(date)]
            response_data = TimeSlotSerializer(available_time_slots, many=True).data
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving available time slots for date {date}: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

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
                serializer.save(patient=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class DoctorListView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            doctors = DoctorProfile.objects.select_related('user').prefetch_related(
                'specializations',
                'treatment_methods',
                'body_areas',
                'associated_conditions'
            ).filter(user__role='DOCTOR', user__is_active=True)
            
            # Get filter parameters from query string
            specialization_id = request.query_params.get('specialization')
            treatment_method_id = request.query_params.get('treatment_method')
            body_area_id = request.query_params.get('body_area')
            associated_condition_id = request.query_params.get('associated_condition')
            
            # Apply filters if parameters are provided
            if specialization_id:
                doctors = doctors.filter(specializations__id=specialization_id)
            
            if treatment_method_id:
                doctors = doctors.filter(treatment_methods__id=treatment_method_id)
            
            if body_area_id:
                doctors = doctors.filter(body_areas__id=body_area_id)
            
            if associated_condition_id:
                doctors = doctors.filter(associated_conditions__id=associated_condition_id)
            
            # Remove duplicates that might occur due to multiple matching criteria
            doctors = doctors.distinct()
            
            serializer = DoctorListSerializer(doctors, many=True)
            return Response({
                'count': doctors.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error retrieving doctors: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DoctorDetailView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        try:
            doctor = get_object_or_404(
                DoctorProfile.objects.select_related('user').prefetch_related(
                    'specializations',
                    'treatment_methods',
                    'body_areas',
                    'associated_conditions',
                    'availability',
                    'reviews__patient'
                ),
                id=doctor_id,
                user__role='DOCTOR',
                user__is_active=True
            )
            
            serializer = DoctorDetailSerializer(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving doctor details for ID {doctor_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
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