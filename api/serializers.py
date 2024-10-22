from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from patient_management.models import Patient
from subscription_management.models import Subscription
from appointment_management.models import Appointment, TimeSlot

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


class BasicUserInfoUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        # Add any password validation logic here
        return value
    

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time']

class AppointmentSerializer(serializers.ModelSerializer):
    patient = CustomUserSerializer()
    doctor = CustomUserSerializer()
    time_slot = TimeSlotSerializer()

    class Meta:
        model = Appointment
        fields = '__all__'