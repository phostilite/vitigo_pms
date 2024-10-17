# File: user_management/management/commands/populate_sample_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from patient_management.models import Patient
from subscription_management.models import Subscription, SubscriptionTier

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample user, patient, and subscription data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create a user
        user = User.objects.create_user(
            email='john.doe@example.com',
            password='securepassword123',
            first_name='John',
            last_name='Doe',
            role='PATIENT',
            is_active=True,
            date_joined=timezone.now()
        )

        # Create a patient profile
        patient = Patient.objects.create(
            user=user,
            date_of_birth='1990-05-15',
            gender='M',
            blood_group='A+',
            address='123 Main St, Anytown, AT 12345',
            phone_number='+1234567890',
            emergency_contact_name='Jane Doe',
            emergency_contact_number='+1987654321',
            vitiligo_onset_date='2020-01-01',
            vitiligo_type='Non-segmental',
            affected_body_areas='Hands, Face'
        )

        # Create a subscription tier (if not exists)
        tier, _ = SubscriptionTier.objects.get_or_create(
            name='Basic',
            defaults={
                'description': 'Basic tier with essential features',
                'price': 9.99,
                'duration_days': 30,
                'max_patients': 1
            }
        )

        # Create a subscription
        subscription = Subscription.objects.create(
            user=user,
            tier=tier,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            is_active=True,
            auto_renew=True,
            billing_cycle='monthly',
            last_billing_date=timezone.now(),
            next_billing_date=timezone.now() + timezone.timedelta(days=30),
            is_trial=False
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created sample data:'))
        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'Patient: {patient}')
        self.stdout.write(f'Subscription: {subscription}')