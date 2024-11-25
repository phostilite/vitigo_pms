# File: patient_management/management/commands/populate_patient_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from access_control.models import Role
from patient_management.models import Patient, MedicalHistory, Medication, VitiligoAssessment, TreatmentPlan
import random
from datetime import timedelta
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Creates a patient user and populates related patient data'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Specify email for the patient user')
        parser.add_argument('--password', type=str, help='Specify password for the patient user')
        parser.add_argument('--count', type=int, default=1, help='Number of patients to create')

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create patient role
        patient_role, _ = Role.objects.get_or_create(
            name='PATIENT',
            defaults={
                'display_name': 'Patient',
                'template_folder': 'patient'
            }
        )

        for _ in range(count):
            # Create user with specified or random email
            email = options['email'] or fake.email()
            password = options['password'] or 'defaultpass123'
            
            # Check if user exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'User {email} already exists'))
                continue

            # Create user with patient role
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=patient_role,
                is_active=True
            )

            # Create patient profile
            self.create_patient_profile(user)
            self.stdout.write(self.style.SUCCESS(f'Successfully created patient user: {email}'))

    def create_patient_profile(self, user):
        patient = Patient.objects.create(
            user=user,
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender=random.choice(['M', 'F', 'O']),
            blood_group=random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']),
            address=fake.address(),
            phone_number=fake.phone_number(),
            emergency_contact_name=fake.name(),
            emergency_contact_number=fake.phone_number(),
            vitiligo_onset_date=fake.date_between(start_date='-10y', end_date='today'),
            vitiligo_type=random.choice(['Segmental', 'Non-segmental', 'Focal', 'Universal']),
            affected_body_areas=random.choice(['Face', 'Hands', 'Trunk', 'Multiple areas'])
        )

        # Create related medical records
        self.create_medical_history(patient)
        self.create_vitiligo_assessment(patient)
        self.create_treatment_plan(patient)

    def create_medical_history(self, patient):
        MedicalHistory.objects.create(
            patient=patient,
            allergies=fake.text(max_nb_chars=100),
            chronic_conditions=fake.text(max_nb_chars=100),
            past_surgeries=fake.text(max_nb_chars=100),
            family_history=fake.text(max_nb_chars=100)
        )

    def create_vitiligo_assessment(self, patient):
        VitiligoAssessment.objects.create(
            patient=patient,
            assessment_date=timezone.now().date(),
            body_surface_area_affected=random.uniform(1, 30),
            vasi_score=random.uniform(1, 100),
            treatment_response=fake.text(max_nb_chars=100),
            notes=fake.text(max_nb_chars=200)
        )

    def create_treatment_plan(self, patient):
        plan = TreatmentPlan.objects.create(
            patient=patient,
            treatment_goals=fake.text(max_nb_chars=200),
            phototherapy_details=fake.text(max_nb_chars=100),
            lifestyle_recommendations=fake.text(max_nb_chars=200),
            follow_up_frequency=f'Every {random.randint(1,6)} months'
        )

        # Create some medications
        for _ in range(random.randint(1, 3)):
            Medication.objects.create(
                patient=patient,
                name=fake.word(),
                dosage=f'{random.randint(1,500)}mg',
                frequency=f'{random.randint(1,3)} times daily',
                start_date=timezone.now().date() - timedelta(days=random.randint(1, 365))
            )