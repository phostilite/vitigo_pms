from rest_framework import serializers
from django.contrib.auth import get_user_model
from appointment_management.models import Appointment, TimeSlot
from user_management.serializers import CustomUserSerializer


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