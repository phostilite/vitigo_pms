import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (UserRegistrationSerializer, UserLoginSerializer, CustomUserSerializer, PatientSerializer,
                          SubscriptionSerializer, BasicUserInfoUpdateSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer)
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from .custom_auth import CustomTokenAuthentication
from patient_management.models import Patient
from subscription_management.models import Subscription
from django.utils.encoding import force_bytes
from django.views.generic import TemplateView
from django.shortcuts import render

User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={201: openapi.Response('User registered successfully', UserRegistrationSerializer)},
        operation_description="Register a new user"
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
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
        return Response({
            'status': 'error',
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={200: openapi.Response('Login successful', UserLoginSerializer)},
        operation_description="Login a user"
    )
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

    @swagger_auto_schema(
        responses={200: openapi.Response('User information', CustomUserSerializer)},
        operation_description="Get user information"
    )
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

    @swagger_auto_schema(
        request_body=BasicUserInfoUpdateSerializer,
        responses={200: openapi.Response('User information updated successfully', BasicUserInfoUpdateSerializer)},
        operation_description="Update basic user information"
    )
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

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Password reset email sent successfully",
                examples={
                    "application/json": {
                        "message": "If an account exists with this email, a password reset link has been sent."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "email": ["This field is required."]
                    }
                }
            ),
            500: openapi.Response(
                description="Internal server error",
                examples={
                    "application/json": {
                        "error": "An unexpected error occurred. Please try again later."
                    }
                }
            )
        },
        operation_description="Request a password reset link to be sent to the provided email address."
    )
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