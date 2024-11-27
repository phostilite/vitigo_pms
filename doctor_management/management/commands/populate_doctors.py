# doctor_management/management/commands/populate_doctors.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from access_control.models import Role
from doctor_management.models import (
    Specialization,
    TreatmentMethodSpecialization,
    BodyAreaSpecialization,
    AssociatedConditionSpecialization,
    DoctorProfile,
    DoctorAvailability
)
import random
from datetime import time

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample doctors and their specializations'

    def create_doctor_availability(self, doctor_profile):
        # Create availability for weekdays
        for day in range(0, 5):  # Monday to Friday
            # Morning shift
            DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=day,
                shift='MORNING',
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(13, 0),   # 1:00 PM
                is_available=True
            )
            # Evening shift
            DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=day,
                shift='EVENING',
                start_time=time(16, 0),  # 4:00 PM
                end_time=time(20, 0),    # 8:00 PM
                is_available=True
            )
        
        # Add some weekend availability (randomly)
        if random.choice([True, False]):
            DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=5,  # Saturday
                shift='MORNING',
                start_time=time(10, 0),  # 10:00 AM
                end_time=time(14, 0),    # 2:00 PM
                is_available=True
            )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # First, clear existing data
        self.stdout.write('Clearing existing data...')
        DoctorAvailability.objects.all().delete()
        DoctorProfile.objects.all().delete()
        
        # Get doctor role
        try:
            doctor_role = Role.objects.get(name='DOCTOR')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Doctor role does not exist. Please create it first.'))
            return
            
        # Updated user deletion query
        User.objects.filter(role=doctor_role).delete()
        Specialization.objects.all().delete()
        TreatmentMethodSpecialization.objects.all().delete()
        BodyAreaSpecialization.objects.all().delete()
        AssociatedConditionSpecialization.objects.all().delete()

        # Create specializations
        self.stdout.write('Creating specializations...')
        specializations = [
            "Vitiligo Treatment",
            "Dermatology",
            "Pediatric Dermatology",
            "Cosmetic Dermatology",
            "Clinical Research"
        ]
        created_specializations = [Specialization.objects.create(name=name) 
                                 for name in specializations]

        # Create treatment methods
        treatment_methods = [
            "Phototherapy",
            "PUVA Therapy",
            "Topical Treatment",
            "Surgical Treatment",
            "Combination Therapy",
            "Laser Treatment"
        ]
        created_treatment_methods = [TreatmentMethodSpecialization.objects.create(name=method) 
                                   for method in treatment_methods]

        # Create body areas
        body_areas = [
            "Facial Vitiligo",
            "Acral Vitiligo",
            "Segmental Vitiligo",
            "Generalized Vitiligo",
            "Mucosal Vitiligo"
        ]
        created_body_areas = [BodyAreaSpecialization.objects.create(name=area) 
                            for area in body_areas]

        # Create associated conditions
        conditions = [
            "Autoimmune Disorders",
            "Thyroid Conditions",
            "Psychological Support",
            "Allergic Conditions",
            "Pediatric Conditions"
        ]
        created_conditions = [AssociatedConditionSpecialization.objects.create(name=condition) 
                            for condition in conditions]

        # Create doctors
        doctors_data = [
            {
                'email': 'dr.smith@example.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'qualification': 'MD, Dermatology',
                'experience': '10-15',
                'city': 'New York'
            },
            {
                'email': 'dr.patel@example.com',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'qualification': 'MD, MBBS, DVD',
                'experience': '5-10',
                'city': 'Chicago'
            },
            {
                'email': 'dr.wilson@example.com',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'qualification': 'MD, PhD in Dermatology',
                'experience': '15+',
                'city': 'Los Angeles'
            },
            {
                'email': 'dr.zhang@example.com',
                'first_name': 'Li',
                'last_name': 'Zhang',
                'qualification': 'MD, Specialist in Vitiligo',
                'experience': '5-10',
                'city': 'San Francisco'
            },
            {
                'email': 'dr.garcia@example.com',
                'first_name': 'Maria',
                'last_name': 'Garcia',
                'qualification': 'MD, Pediatric Dermatology',
                'experience': '10-15',
                'city': 'Miami'
            }
        ]

        self.stdout.write('Creating doctors...')
        for doctor_data in doctors_data:
            try:
                # Create user with role object
                user = User.objects.create_user(
                    email=doctor_data['email'],
                    password='password123',
                    first_name=doctor_data['first_name'],
                    last_name=doctor_data['last_name'],
                    role=doctor_role,
                    is_active=True
                )

                # Create doctor profile
                doctor_profile = DoctorProfile.objects.create(
                    user=user,
                    registration_number=f"DOC{random.randint(1000, 9999)}",
                    qualification=doctor_data['qualification'],
                    experience=doctor_data['experience'],
                    consultation_fee=random.randint(100, 300),
                    about=f"Experienced dermatologist specializing in vitiligo treatment with {doctor_data['experience']} years of experience.",
                    address=f"123 Medical Plaza, Suite {random.randint(100, 999)}",
                    city=doctor_data['city'],
                    state="State",
                    country="USA",
                    rating=round(random.uniform(4.0, 5.0), 1)
                )

                # Add random specializations
                doctor_profile.specializations.add(*random.sample(created_specializations, k=random.randint(2, 4)))
                doctor_profile.treatment_methods.add(*random.sample(created_treatment_methods, k=random.randint(2, 4)))
                doctor_profile.body_areas.add(*random.sample(created_body_areas, k=random.randint(2, 4)))
                doctor_profile.associated_conditions.add(*random.sample(created_conditions, k=random.randint(2, 3)))

                # Create availability
                self.create_doctor_availability(doctor_profile)

                self.stdout.write(f'Created doctor: Dr. {user.get_full_name()}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating doctor {doctor_data["email"]}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS('Successfully populated doctors data'))