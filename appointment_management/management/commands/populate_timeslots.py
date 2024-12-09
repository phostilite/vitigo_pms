# appointment_management/management/commands/populate_timeslots.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from access_control.models import Role
, DoctorAvailability
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

        # Get doctor role
        try:
            doctor_role = Role.objects.get(name='DOCTOR')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Doctor role not found.'))
            return

        # Get all active doctors with doctor profile
        doctors = DoctorProfile.objects.filter(
            user__role=doctor_role,
            user__is_active=True,
            is_available=True
        )
        
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('No active doctors found. Please create some doctors first.'))
            return

        self.stdout.write(f'Found {doctors.count()} active doctors. Generating time slots...')

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
        slots_skipped = 0
        start_date = timezone.now().date()

        for doctor in doctors:
            self.stdout.write(f'Processing slots for doctor: {doctor}')
            
            # Generate time slots for the specified number of days
            time_slot_data = []
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Skip weekends
                if current_date.weekday() >= 5:
                    continue

                # Check doctor's availability for this day
                day_availability = doctor.availability.filter(
                    day_of_week=current_date.weekday(),
                    is_available=True
                )
                
                if not day_availability.exists():
                    continue

                # Get existing slots for this date to avoid duplicates
                existing_slots = set(DoctorTimeSlot.objects.filter(
                    doctor=doctor,
                    date=current_date
                ).values_list('start_time', 'end_time'))

                # Randomly make some slots unavailable to simulate booked appointments
                available_slots = random.sample(time_slots, k=random.randint(6, len(time_slots)))
                
                for start_time, end_time in time_slots:
                    start = datetime.strptime(start_time, '%H:%M').time()
                    end = datetime.strptime(end_time, '%H:%M').time()
                    
                    # Skip if slot already exists
                    if (start, end) in existing_slots:
                        slots_skipped += 1
                        continue

                    # Check if slot falls within doctor's availability
                    slot_available = any(
                        avail.start_time <= start and avail.end_time >= end 
                        for avail in day_availability
                    )
                    
                    if slot_available:
                        is_available = (start_time, end_time) in available_slots
                        time_slot_data.append(
                            DoctorTimeSlot(
                                doctor=doctor,
                                date=current_date,
                                start_time=start,
                                end_time=end,
                                is_available=is_available
                            )
                        )

            if time_slot_data:
                # Bulk create time slots for the doctor
                created_slots = DoctorTimeSlot.objects.bulk_create(
                    time_slot_data,
                    ignore_conflicts=True
                )
                slots_created += len(created_slots)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {slots_created} time slots '
                f'(skipped {slots_skipped} existing slots) for {doctors.count()} '
                f'doctors over {days} days'
            )
        )