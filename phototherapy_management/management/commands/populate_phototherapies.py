# phototherapy_managementmanagement/commands/populate_phototherapies.py

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from user_management.models import CustomUser
from patient_management.models import Patient
from phototherapy_management.models import PhototherapyType, PhototherapyProtocol, PhototherapyPlan, PhototherapySession, PhototherapyDevice, HomePhototherapyLog

class Command(BaseCommand):
    help = 'Generate sample phototherapy management data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample phototherapy management data...')

        # Create sample phototherapy types if they don't exist
        phototherapy_types = [
            {'name': 'UVB', 'description': 'Narrowband UVB phototherapy'},
            {'name': 'PUVA', 'description': 'Psoralen and UVA phototherapy'},
        ]
        for pt in phototherapy_types:
            PhototherapyType.objects.get_or_create(
                name=pt['name'],
                defaults={
                    'description': pt['description'],
                    'is_active': True
                }
            )

        # Create sample phototherapy protocols if they don't exist
        protocols = [
            {'phototherapy_type': 'UVB', 'name': 'Standard UVB', 'description': 'Standard UVB protocol', 'initial_dose': 200, 'max_dose': 1000, 'increment_percentage': 10, 'frequency': '3 times per week', 'duration_weeks': 12},
            {'phototherapy_type': 'PUVA', 'name': 'Standard PUVA', 'description': 'Standard PUVA protocol', 'initial_dose': 300, 'max_dose': 1500, 'increment_percentage': 15, 'frequency': '2 times per week', 'duration_weeks': 10},
        ]
        for protocol in protocols:
            phototherapy_type = PhototherapyType.objects.get(name=protocol['phototherapy_type'])
            PhototherapyProtocol.objects.get_or_create(
                phototherapy_type=phototherapy_type,
                name=protocol['name'],
                defaults={
                    'description': protocol['description'],
                    'initial_dose': protocol['initial_dose'],
                    'max_dose': protocol['max_dose'],
                    'increment_percentage': protocol['increment_percentage'],
                    'frequency': protocol['frequency'],
                    'duration_weeks': protocol['duration_weeks']
                }
            )

        # Fetch all phototherapy types, protocols, patients, and staff
        phototherapy_types = PhototherapyType.objects.all()
        protocols = PhototherapyProtocol.objects.all()
        patients = Patient.objects.all()
        staff = CustomUser.objects.filter(role__in=['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PHARMACIST', 'LAB_TECHNICIAN'])

        # Generate sample phototherapy plans
        for _ in range(50):  # Generate 50 sample plans
            protocol = random.choice(protocols)
            patient = random.choice(patients)
            created_by = random.choice(staff)
            start_date = timezone.now().date()
            end_date = start_date + timedelta(weeks=protocol.duration_weeks)
            current_dose = protocol.initial_dose

            PhototherapyPlan.objects.create(
                patient=patient,
                protocol=protocol,
                start_date=start_date,
                end_date=end_date,
                current_dose=current_dose,
                created_by=created_by,
                notes='Sample phototherapy plan notes',
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample phototherapy management data'))