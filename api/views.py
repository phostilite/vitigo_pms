import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (UserRegistrationSerializer, UserLoginSerializer, CustomUserSerializer, PatientSerializer,
                          SubscriptionSerializer, BasicUserInfoUpdateSerializer)
from django.contrib.auth import get_user_model

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .custom_auth import CustomTokenAuthentication
from patient_management.models import Patient
from subscription_management.models import Subscription

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