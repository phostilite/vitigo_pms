from rest_framework import serializers
from .models import Patient, MedicalHistory, Medication, VitiligoAssessment, TreatmentPlan
from user_management.serializers import CustomUserSerializer

class PatientSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'gender', 'blood_group', 'address', 'phone_number',
                  'emergency_contact_name', 'emergency_contact_number', 'vitiligo_onset_date',
                  'vitiligo_type', 'affected_body_areas', 'created_at', 'updated_at']

class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = ['id', 'allergies', 'chronic_conditions', 'past_surgeries', 'family_history']

class MedicationSerializer(serializers.ModelSerializer):
    prescribed_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = Medication
        fields = ['id', 'name', 'dosage', 'frequency', 'start_date', 'end_date', 'prescribed_by']

class VitiligoAssessmentSerializer(serializers.ModelSerializer):
    assessed_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = VitiligoAssessment
        fields = ['id', 'assessment_date', 'body_surface_area_affected', 'vasi_score',
                  'treatment_response', 'notes', 'assessed_by']

class TreatmentPlanSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    medications = MedicationSerializer(many=True, read_only=True)

    class Meta:
        model = TreatmentPlan
        fields = ['id', 'created_date', 'updated_date', 'treatment_goals', 'medications',
                  'phototherapy_details', 'lifestyle_recommendations', 'follow_up_frequency',
                  'created_by']