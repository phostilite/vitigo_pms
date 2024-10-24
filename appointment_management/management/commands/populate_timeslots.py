# appointment_management/management/commands/populate_timeslots.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from doctor_management.models import DoctorProfile, DoctorAvailability
from appointment_management.models import DoctorTimeSlot
from datetime import datetime, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate time slots for doctors for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate slots for (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing time slots before creating new ones'
        )

    def setup_doctor_availability(self, doctor):
        """Setup availability for a doctor for all weekdays"""
        # Clear existing availability for the doctor
        DoctorAvailability.objects.filter(doctor=doctor).delete()
        
        # Create availability for weekdays
        availability_data = []
        for day in range(5):  # 0-4 represents Monday to Friday
            # Morning shift
            availability_data.append(
                DoctorAvailability(
                    doctor=doctor,
                    day_of_week=day,
                    shift='MORNING',
                    start_time=datetime.strptime('09:00', '%H:%M').time(),
                    end_time=datetime.strptime('12:00', '%H:%M').time(),
                    is_available=True
                )
            )
            # Evening shift
            availability_data.append(
                DoctorAvailability(
                    doctor=doctor,
                    day_of_week=day,
                    shift='EVENING',
                    start_time=datetime.strptime('14:00', '%H:%M').time(),
                    end_time=datetime.strptime('17:00', '%H:%M').time(),
                    is_available=True
                )
            )
        
        # Bulk create all availability records
        DoctorAvailability.objects.bulk_create(availability_data)

    def handle(self, *args, **options):
        days = options['days']
        clear = options['clear']

        if clear:
            self.stdout.write('Clearing existing time slots...')
            DoctorTimeSlot.objects.all().delete()
            self.stdout.write('Existing time slots cleared.')

        # Get all doctors
        doctors = DoctorProfile.objects.filter(user__role='DOCTOR', is_available=True)
        
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('No doctors found. Please create some doctors first.'))
            return

        self.stdout.write(f'Found {doctors.count()} doctors. Generating time slots...')

        # Standard clinic hours
        time_slots = [
            ('09:00', '09:30'), ('09:30', '10:00'),
            ('10:00', '10:30'), ('10:30', '11:00'),
            ('11:00', '11:30'), ('11:30', '12:00'),
            ('14:00', '14:30'), ('14:30', '15:00'),
            ('15:00', '15:30'), ('15:30', '16:00'),
            ('16:00', '16:30'), ('16:30', '17:00'),
        ]

        slots_created = 0
        start_date = timezone.now().date()

        for doctor in doctors:
            self.stdout.write(f'Setting up availability for doctor: {doctor}')
            # Setup availability for the doctor
            self.setup_doctor_availability(doctor)
            
            self.stdout.write(f'Generating slots for doctor: {doctor}')
            
            # Generate time slots for the specified number of days
            time_slot_data = []
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Skip weekends
                if current_date.weekday() >= 5:
                    continue
                
                # Randomly make some slots unavailable to simulate booked appointments
                available_slots = random.sample(time_slots, k=random.randint(6, len(time_slots)))
                
                for start_time, end_time in time_slots:
                    is_available = (start_time, end_time) in available_slots
                    
                    time_slot_data.append(
                        DoctorTimeSlot(
                            doctor=doctor,
                            date=current_date,
                            start_time=datetime.strptime(start_time, '%H:%M').time(),
                            end_time=datetime.strptime(end_time, '%H:%M').time(),
                            is_available=is_available
                        )
                    )
            
            # Bulk create time slots for the doctor
            created_slots = DoctorTimeSlot.objects.bulk_create(
                time_slot_data,
                ignore_conflicts=True  # Skip any duplicate entries
            )
            slots_created += len(created_slots)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {slots_created} time slots for {doctors.count()} doctors '
                f'over {days} days'
            )
        )