# File: patient_management/management/commands/populate_patient_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patient_management.models import Patient, MedicalHistory, Medication, VitiligoAssessment, TreatmentPlan
from django.utils import timezone
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates patient management data for a given user email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email of the user to populate data for')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} does not exist'))
            return

        if user.role != 'PATIENT':
            self.stdout.write(self.style.ERROR(f'User with email {email} is not a patient'))
            return

        self.create_or_update_patient(user)
        self.stdout.write(self.style.SUCCESS(f'Successfully populated data for patient {email}'))

    def create_or_update_patient(self, user):
        patient, created = Patient.objects.update_or_create(
            user=user,
            defaults={
                'date_of_birth': timezone.now().date() - timedelta(days=365*30),
                'gender': random.choice(['M', 'F']),
                'blood_group': random.choice(['A+', 'B+', 'O+', 'AB+']),
                'address': '123 Sample St, Sample City, 12345',
                'phone_number': '1234567890',
                'emergency_contact_name': 'Emergency Contact',
                'emergency_contact_number': '9876543210',
                'vitiligo_onset_date': timezone.now().date() - timedelta(days=365*2),
                'vitiligo_type': random.choice(['Segmental', 'Non-segmental']),
                'affected_body_areas': 'Hands, Face',
            }
        )

        self.create_medical_history(patient)
        self.create_medications(patient)
        self.create_vitiligo_assessments(patient)
        self.create_treatment_plan(patient)

    def create_medical_history(self, patient):
        MedicalHistory.objects.update_or_create(
            patient=patient,
            defaults={
                'allergies': 'Peanuts, Penicillin',
                'chronic_conditions': 'None',
                'past_surgeries': 'Appendectomy in 2010',
                'family_history': 'Father: Hypertension, Mother: Diabetes',
            }
        )

    def create_medications(self, patient):
        doctor = self.get_or_create_doctor()
        medications = [
            {'name': 'Tacrolimus', 'dosage': '0.1% ointment', 'frequency': 'Twice daily'},
            {'name': 'Vitamin D3', 'dosage': '1000 IU', 'frequency': 'Once daily'},
        ]
        for med in medications:
            Medication.objects.create(
                patient=patient,
                name=med['name'],
                dosage=med['dosage'],
                frequency=med['frequency'],
                start_date=timezone.now().date() - timedelta(days=30),
                prescribed_by=doctor
            )

    def create_vitiligo_assessments(self, patient):
        doctor = self.get_or_create_doctor()
        for i in range(3):
            VitiligoAssessment.objects.create(
                patient=patient,
                assessment_date=timezone.now().date() - timedelta(days=30*i),
                body_surface_area_affected=random.uniform(1, 10),
                vasi_score=random.uniform(0, 50),
                treatment_response='Moderate improvement',
                notes='Patient responding well to current treatment',
                assessed_by=doctor
            )

    def create_treatment_plan(self, patient):
        doctor = self.get_or_create_doctor()
        TreatmentPlan.objects.create(
            patient=patient,
            treatment_goals='Repigmentation of affected areas',
            phototherapy_details='NB-UVB therapy, 3 times per week',
            lifestyle_recommendations='Regular sun protection, stress management',
            follow_up_frequency='Every 2 months',
            created_by=doctor
        )

    def get_or_create_doctor(self):
        doctor, created = User.objects.get_or_create(
            email='doctor@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'DOCTOR',
                'is_staff': True
            }
        )
        if created:
            doctor.set_password('password123')  # Set a default password
            doctor.save()
        return doctor