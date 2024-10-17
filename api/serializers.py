from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from patient_management.models import Patient
from subscription_management.models import Subscription

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='PATIENT')

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                return user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['date_of_birth', 'gender', 'blood_group', 'address', 'phone_number',
                  'emergency_contact_name', 'emergency_contact_number', 'vitiligo_onset_date',
                  'vitiligo_type', 'affected_body_areas']


class SubscriptionSerializer(serializers.ModelSerializer):
    tier_name = serializers.CharField(source='tier.name')

    class Meta:
        model = Subscription
        fields = ['tier_name', 'start_date', 'end_date', 'is_active', 'is_trial']