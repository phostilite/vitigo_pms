# procedure_management/management/commands/populate_procedures.py

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from user_management.models import CustomUser
from patient_management.models import Patient
from procedure_management.models import Procedure, ProcedureType

class Command(BaseCommand):
    help = 'Generate sample procedure management data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample procedure management data...')

        # Create sample procedure types if they don't exist
        procedure_types = [
            {'name': 'Blood Test', 'description': 'Routine blood test', 'duration': '00:30:00', 'price': 50.00},
            {'name': 'X-Ray', 'description': 'Chest X-Ray', 'duration': '00:45:00', 'price': 100.00},
            {'name': 'MRI', 'description': 'Brain MRI', 'duration': '01:30:00', 'price': 500.00},
        ]
        for pt in procedure_types:
            duration_parts = pt['duration'].split(':')
            duration = timedelta(hours=int(duration_parts[0]), minutes=int(duration_parts[1]), seconds=int(duration_parts[2]))
            ProcedureType.objects.get_or_create(
                name=pt['name'],
                defaults={
                    'description': pt['description'],
                    'duration': duration,
                    'price': pt['price'],
                    'is_active': True
                }
            )

        # Fetch all procedure types, patients, and staff
        procedure_types = ProcedureType.objects.all()
        patients = Patient.objects.all()
        staff = CustomUser.objects.filter(role__in=['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PHARMACIST', 'LAB_TECHNICIAN'])

        # Generate sample procedures
        for _ in range(50):  # Generate 50 sample procedures
            procedure_type = random.choice(procedure_types)
            patient = random.choice(patients)
            performed_by = random.choice(staff) if random.choice([True, False]) else None
            status = random.choice(['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
            scheduled_date = timezone.now() + timezone.timedelta(days=random.randint(1, 30))

            Procedure.objects.create(
                patient=patient,
                procedure_type=procedure_type,
                scheduled_date=scheduled_date,
                status=status,
                performed_by=performed_by,
                notes='Sample procedure notes'
            )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample procedure management data'))