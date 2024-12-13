from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from appointment_management.models import Appointment
from access_control.models import Role
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample appointments for random patients with doctors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of appointments to create'
        )

    def handle(self, *args, **kwargs):
        count = kwargs['count']

        # Get patient and doctor roles
        try:
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Required roles not found'))
            return

        # Get all active patients and doctors
        patients = User.objects.filter(role=patient_role, is_active=True)
        doctors = User.objects.filter(role=doctor_role, is_active=True)

        if not patients.exists() or not doctors.exists():
            self.stdout.write(self.style.ERROR('No patients or doctors found'))
            return

        appointment_types = ['CONSULTATION', 'FOLLOW_UP', 'PROCEDURE']
        priorities = ['A', 'B', 'C']

        appointments_created = 0
        for _ in range(count):
            try:
                Appointment.objects.create(
                    patient=random.choice(patients),
                    doctor=random.choice(doctors),
                    appointment_type=random.choice(appointment_types),
                    date=timezone.now().date() + timezone.timedelta(days=random.randint(1, 30)),
                    status='SCHEDULED',
                    priority=random.choice(priorities),
                    notes='Sample appointment'
                )
                appointments_created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to create appointment: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Created {appointments_created} sample appointments'))