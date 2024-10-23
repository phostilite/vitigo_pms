import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from appointment_management.models import Appointment, TimeSlot
from patient_management.models import Patient, MedicalHistory, Medication, VitiligoAssessment, TreatmentPlan
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Fill sample data for a patient and doctors'

    def add_arguments(self, parser):
        parser.add_argument('patient_email', type=str, help='Email of the patient to fill sample data')

    def handle(self, *args, **kwargs):
        patient_email = kwargs['patient_email']

        # Create or get the patient user
        patient_user, created = User.objects.get_or_create(
            email=patient_email,
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'PATIENT',
                'password': 'password123'  # Change this to a secure password
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created patient user: {patient_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Patient user already exists: {patient_email}'))

        # Create patient profile
        patient, created = Patient.objects.get_or_create(
            user=patient_user,
            defaults={
                'date_of_birth': '1990-01-01',
                'gender': 'M',
                'address': '123 Main St',
                'phone_number': '1234567890',
                'emergency_contact_name': 'John Doe',
                'emergency_contact_number': '0987654321'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created patient profile for: {patient_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Patient profile already exists for: {patient_email}'))

        # Create doctors
        doctor_emails = ['doctor1@example.com', 'doctor2@example.com', 'doctor3@example.com']
        doctors = []

        for email in doctor_emails:
            doctor_user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': 'Doctor',
                    'last_name': email.split('@')[0],
                    'role': 'DOCTOR',
                    'password': 'password123'  # Change this to a secure password
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created doctor user: {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'Doctor user already exists: {email}'))

            doctors.append(doctor_user)

        # Create sample time slots
        time_slots = [
            TimeSlot.objects.get_or_create(start_time='09:00', end_time='09:30')[0],
            TimeSlot.objects.get_or_create(start_time='10:00', end_time='10:30')[0],
            TimeSlot.objects.get_or_create(start_time='11:00', end_time='11:30')[0],
        ]

        # Create sample appointments
        for i in range(5):
            Appointment.objects.create(
                patient=patient_user,
                doctor=random.choice(doctors),
                appointment_type='CONSULTATION',
                date=timezone.now().date() + timezone.timedelta(days=i),
                time_slot=random.choice(time_slots),
                status='SCHEDULED',
                priority='B',
                notes='Sample appointment'
            )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully'))