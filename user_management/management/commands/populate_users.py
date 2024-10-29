# user_management/management/commands/populate_users.py
from django.core.management.base import BaseCommand
from user_management.models import CustomUser
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Populate the database with multiple users with different roles'

    def add_arguments(self, parser):
        parser.add_argument('num_users', type=int, help='The number of users to create')

    def handle(self, *args, **kwargs):
        fake = Faker()
        roles = ['PATIENT', 'DOCTOR', 'NURSE', 'RECEPTIONIST', 'PHARMACIST', 'LAB_TECHNICIAN', 'ADMIN']
        num_users = kwargs['num_users']

        for _ in range(num_users):
            email = fake.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            password = 'password123'
            role = random.choice(roles)

            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created user {user.email} with role {user.role}'))