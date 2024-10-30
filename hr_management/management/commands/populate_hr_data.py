# hr_management/management/commands/populate_hr_data.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from user_management.models import CustomUser
from hr_management.models import (
    Employee, Attendance, LeaveType, LeaveRequest, PerformanceReview, Training, TrainingAttendance
)

class Command(BaseCommand):
    help = 'Generate sample HR management data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample HR management data...')

        # Filter users to exclude non-employee roles
        users = CustomUser.objects.exclude(role='PATIENT')

        # Create sample employees if they don't exist
        for user in users:
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': f"EMP{random.randint(1000, 9999)}",
                    'department': random.choice(['HR', 'Finance', 'IT', 'Operations']),
                    'position': random.choice(['Manager', 'Executive', 'Analyst', 'Assistant']),
                    'date_of_joining': timezone.now().date() - timezone.timedelta(days=random.randint(0, 3650)),
                    'date_of_birth': timezone.now().date() - timezone.timedelta(days=random.randint(6570, 18250)),
                    'gender': random.choice(['M', 'F', 'O']),
                    'address': '123 Main St, City, Country',
                    'phone_number': f"+1234567890{random.randint(0, 9)}",
                    'emergency_contact_name': 'John Doe',
                    'emergency_contact_number': f"+1234567890{random.randint(0, 9)}",
                    'bank_account_number': f"1234567890{random.randint(0, 9)}",
                    'bank_name': 'Bank Name',
                    'is_active': True
                }
            )

        # Fetch all employees
        employees = Employee.objects.all()

        # Create sample attendance records
        for employee in employees:
            for _ in range(random.randint(20, 30)):  # Generate 20 to 30 attendance records per employee
                date = timezone.now().date() - timezone.timedelta(days=random.randint(0, 365))
                Attendance.objects.get_or_create(
                    employee=employee,
                    date=date,
                    defaults={
                        'time_in': timezone.now().time(),
                        'time_out': timezone.now().time(),
                        'status': random.choice(['PRESENT', 'ABSENT', 'HALF_DAY', 'LATE']),
                        'notes': 'Sample attendance note'
                    }
                )

        # Create sample leave types if they don't exist
        leave_types = [
            {'name': 'Sick Leave', 'description': 'Leave for sickness', 'max_days_per_year': 10},
            {'name': 'Casual Leave', 'description': 'Casual leave', 'max_days_per_year': 12},
            {'name': 'Maternity Leave', 'description': 'Leave for maternity', 'max_days_per_year': 180},
        ]
        for leave_type in leave_types:
            LeaveType.objects.get_or_create(
                name=leave_type['name'],
                defaults={
                    'description': leave_type['description'],
                    'max_days_per_year': leave_type['max_days_per_year']
                }
            )

        # Fetch all leave types
        leave_types = LeaveType.objects.all()

        # Create sample leave requests
        for employee in employees:
            for _ in range(random.randint(1, 5)):  # Generate 1 to 5 leave requests per employee
                leave_type = random.choice(leave_types)
                start_date = timezone.now().date() - timezone.timedelta(days=random.randint(0, 365))
                end_date = start_date + timezone.timedelta(days=random.randint(1, leave_type.max_days_per_year))
                LeaveRequest.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    reason='Sample leave reason',
                    status=random.choice(['PENDING', 'APPROVED', 'REJECTED']),
                    approved_by=random.choice(users) if random.choice([True, False]) else None
                )

        # Create sample performance reviews
        for employee in employees:
            for _ in range(random.randint(1, 3)):  # Generate 1 to 3 performance reviews per employee
                PerformanceReview.objects.create(
                    employee=employee,
                    reviewer=random.choice(users),
                    review_date=timezone.now().date() - timezone.timedelta(days=random.randint(0, 365)),
                    performance_score=random.randint(1, 5),
                    strengths='Sample strengths',
                    areas_for_improvement='Sample areas for improvement',
                    goals_for_next_period='Sample goals for next period',
                    employee_comments='Sample employee comments'
                )

        # Create sample trainings
        trainings = [
            {'title': 'Leadership Training', 'description': 'Training for leadership skills', 'trainer': 'John Smith', 'start_date': timezone.now().date() - timezone.timedelta(days=30), 'end_date': timezone.now().date() - timezone.timedelta(days=25), 'location': 'Training Room 1', 'max_participants': 20},
            {'title': 'Technical Training', 'description': 'Training for technical skills', 'trainer': 'Jane Doe', 'start_date': timezone.now().date() - timezone.timedelta(days=20), 'end_date': timezone.now().date() - timezone.timedelta(days=15), 'location': 'Training Room 2', 'max_participants': 15},
        ]
        for training in trainings:
            Training.objects.get_or_create(
                title=training['title'],
                defaults={
                    'description': training['description'],
                    'trainer': training['trainer'],
                    'start_date': training['start_date'],
                    'end_date': training['end_date'],
                    'location': training['location'],
                    'max_participants': training['max_participants']
                }
            )

        # Fetch all trainings
        trainings = Training.objects.all()

        # Create sample training attendances
        for training in trainings:
            participants = random.sample(list(employees), random.randint(5, training.max_participants))
            for employee in participants:
                TrainingAttendance.objects.create(
                    training=training,
                    employee=employee,
                    status=random.choice(['REGISTERED', 'ATTENDED', 'COMPLETED', 'NO_SHOW']),
                    feedback='Sample feedback'
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample HR management data'))