from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserLoginSerializer, CustomUserSerializer, PatientSerializer, SubscriptionSerializer
from django.contrib.auth import get_user_model

from patient_management.models import Patient
from subscription_management.models import Subscription

User = get_user_model()

class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = CustomUserSerializer(user).data

        if user.role == 'PATIENT':
            try:
                patient = Patient.objects.get(user=user)
                subscription = Subscription.objects.get(user=user)

                patient_data = PatientSerializer(patient).data
                subscription_data = SubscriptionSerializer(subscription).data

                return Response({
                    'user': user_data,
                    'patient': patient_data,
                    'subscription': subscription_data
                }, status=status.HTTP_200_OK)
            except Patient.DoesNotExist:
                return Response({'error': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
            except Subscription.DoesNotExist:
                return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # For non-patient roles, return a sample response
            return Response({
                'user': user_data,
                'message': f'User role is {user.role}. Additional data will be implemented in future.'
            }, status=status.HTTP_200_OK)