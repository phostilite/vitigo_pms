from rest_framework import serializers
from django.contrib.auth import get_user_model
from appointment_management.models import Appointment, TimeSlot
from user_management.serializers import CustomUserSerializer
from django.utils import timezone


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time']

class AppointmentSerializer(serializers.ModelSerializer):
    patient = CustomUserSerializer()
    doctor = CustomUserSerializer()
    time_slot = TimeSlotSerializer()
    status = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    appointment_type = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_status(self, obj):
        return obj.get_status_display()

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_appointment_type(self, obj):
        return obj.get_appointment_type_display()
    

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        # Check if the appointment date is within 30 days
        if data['date'] > timezone.now().date() + timezone.timedelta(days=30):
            raise serializers.ValidationError("Appointments cannot be scheduled more than 30 days in advance.")
        
        # Check if the time slot is available
        if not TimeSlot.objects.filter(id=data['time_slot'].id).exists():
            raise serializers.ValidationError("Selected time slot does not exist.")
        
        if not data['time_slot'].is_available(data['date']):
            raise serializers.ValidationError("Selected time slot is not available on the chosen date.")
        
        return data