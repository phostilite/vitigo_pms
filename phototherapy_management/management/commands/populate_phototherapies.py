from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from faker import Faker
import random
from decimal import Decimal

from phototherapy_management.models import (
    PhototherapyType, PatientRFIDCard, PhototherapyDevice,
    PhototherapyProtocol, PhototherapyPlan, PhototherapySession,
    HomePhototherapyLog, ProblemReport, PhototherapyPayment,
    PhototherapyReminder, PhototherapyProgress, DeviceMaintenance,
    PhototherapyCenter  # Add this import
)

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with sample phototherapy data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        self.stdout.write('Clearing existing phototherapy data...')
        try:
            # Delete in proper order to respect foreign key constraints
            PhototherapyReminder.objects.all().delete()
            PhototherapyProgress.objects.all().delete()
            DeviceMaintenance.objects.all().delete()
            ProblemReport.objects.all().delete()
            HomePhototherapyLog.objects.all().delete()
            PhototherapyPayment.objects.all().delete()
            PhototherapySession.objects.all().delete()
            PhototherapyPlan.objects.all().delete()
            PatientRFIDCard.objects.all().delete()
            PhototherapyProtocol.objects.all().delete()
            PhototherapyCenter.objects.all().delete()  # Add this line
            PhototherapyDevice.objects.all().delete()
            PhototherapyType.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS('Successfully cleared all existing phototherapy data'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing existing data: {str(e)}')
            )
            return

        self.stdout.write('Starting to populate phototherapy data...')
        
        # Get random users
        users = list(User.objects.all())
        if not users:
            self.stdout.write('No users found. Please create users first.')
            return

        # Create Phototherapy Types
        therapy_types = self._create_therapy_types()
        if not therapy_types:
            self.stdout.write('No therapy types created. Using existing ones...')
            therapy_types = list(PhototherapyType.objects.all())
            if not therapy_types:
                self.stdout.write(self.style.ERROR('No therapy types available. Cannot continue.'))
                return

        self.stdout.write(f'Working with {len(therapy_types)} therapy types')

        # Create Centers
        centers = self._create_centers()
        self.stdout.write('Created phototherapy centers')

        # Create Devices (modified to associate with centers)
        devices = self._create_devices(therapy_types, centers)
        self.stdout.write('Created devices')

        # Create Protocols
        protocols = self._create_protocols(therapy_types)
        self.stdout.write('Created protocols')

        # Create RFID Cards
        rfid_cards = self._create_rfid_cards(users)
        self.stdout.write('Created RFID cards')

        # Create Treatment Plans
        plans = self._create_treatment_plans(users, protocols, rfid_cards)
        self.stdout.write('Created treatment plans')

        # Create Sessions
        sessions = self._create_sessions(plans, devices)
        self.stdout.write('Created sessions')

        # Create remaining related data
        self._create_home_logs(plans)
        self._create_problem_reports(sessions, users)
        self._create_payments(plans, users)  # Modified payment creation
        self._create_reminders(plans)
        self._create_progress_records(plans, users)
        self._create_maintenance_records(devices, users)

        self.stdout.write(self.style.SUCCESS('Successfully populated phototherapy data'))

    def _create_therapy_types(self):
        types = []
        existing_types = set(PhototherapyType.objects.values_list('name', flat=True))
        
        for therapy_type in PhototherapyType.THERAPY_CHOICES:
            try:
                name = f"{therapy_type[1]} Treatment"
                # Skip if type already exists
                if name in existing_types:
                    self.stdout.write(self.style.WARNING(f'Skipping existing therapy type: {name}'))
                    continue
                    
                type_obj = PhototherapyType.objects.create(
                    name=name,
                    therapy_type=therapy_type[0],
                    description=fake.text(),
                    priority=random.choice(['A', 'B', 'C']),
                    requires_rfid=random.choice([True, False])
                )
                types.append(type_obj)
                existing_types.add(name)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error creating therapy type {therapy_type[1]}: {str(e)}'))
                continue
        return types

    def _create_centers(self):
        """Create sample phototherapy centers"""
        centers = []
        
        center_data = [
            {
                'name': 'Main Phototherapy Center',
                'address': '123 Medical Plaza, Downtown Medical District',
                'contact_number': '+91 98765 43210',
                'email': 'main.center@vitigo.com',
                'operating_hours': 'Mon-Sat: 9:00 AM - 6:00 PM, Sun: Closed',
            },
            {
                'name': 'North Branch Clinic',
                'address': '45 North Healthcare Avenue, Suburban Medical Hub',
                'contact_number': '+91 98765 43211',
                'email': 'north.clinic@vitigo.com',
                'operating_hours': 'Mon-Fri: 8:00 AM - 8:00 PM, Sat-Sun: 9:00 AM - 1:00 PM',
            },
            {
                'name': 'South Wing Treatment Center',
                'address': '789 South Medical Complex, Central Hospital Zone',
                'contact_number': '+91 98765 43212',
                'email': 'south.wing@vitigo.com',
                'operating_hours': 'Mon-Sun: 24 Hours',
            },
            {
                'name': 'Express Phototherapy Clinic',
                'address': '321 East Healthcare Street, Business District',
                'contact_number': '+91 98765 43213',
                'email': 'express.clinic@vitigo.com',
                'operating_hours': 'Mon-Sat: 7:00 AM - 9:00 PM',
            }
        ]

        try:
            for data in center_data:
                center = PhototherapyCenter.objects.create(**data)
                centers.append(center)
                self.stdout.write(f'Created center: {center.name}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error creating center: {str(e)}')
            )

        return centers

    def _create_devices(self, therapy_types, centers):
        """Modified to associate devices with centers"""
        if not therapy_types:
            self.stdout.write(self.style.ERROR('No therapy types available for device creation'))
            return []
            
        devices = []
        locations = ['Room A', 'Room B', 'Room C', 'Room D']
        try:
            for i in range(10):
                device = PhototherapyDevice.objects.create(
                    name=f"Device {i+1}",
                    model_number=fake.bothify(text='MOD-####'),
                    serial_number=fake.bothify(text='SER-####-####'),
                    phototherapy_type=random.choice(therapy_types),
                    location=random.choice(locations),
                    installation_date=fake.date_between(start_date='-2y'),
                    last_maintenance_date=fake.date_between(start_date='-6m'),
                    next_maintenance_date=fake.date_between(start_date='today')
                )
                # Assign device to random center(s)
                num_centers = random.randint(1, 2)  # Device can be in 1-2 centers
                selected_centers = random.sample(centers, num_centers)
                for center in selected_centers:
                    center.available_devices.add(device)
                
                devices.append(device)
                self.stdout.write(f'Created device: {device.name} in {num_centers} center(s)')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error creating device: {str(e)}')
            )
        
        return devices

    def _create_protocols(self, therapy_types):
        protocols = []
        for i in range(15):
            initial_dose = random.uniform(100, 300)
            protocol = PhototherapyProtocol.objects.create(
                phototherapy_type=random.choice(therapy_types),
                name=f"Protocol {i+1}",
                description=fake.text(),
                initial_dose=initial_dose,
                max_dose=initial_dose * 3,
                increment_percentage=random.uniform(5, 20),
                frequency_per_week=random.randint(2, 5),
                duration_weeks=random.randint(8, 24),
                safety_guidelines=fake.text()
            )
            protocols.append(protocol)
        return protocols

    def _create_rfid_cards(self, users):
        cards = []
        for user in random.sample(users, len(users)//2):
            card = PatientRFIDCard.objects.create(
                patient=user,
                card_number=fake.bothify(text='RFID-####-####'),
                expires_at=timezone.now() + timedelta(days=365),
                notes=fake.text()
            )
            cards.append(card)
        return cards

    def _create_treatment_plans(self, users, protocols, rfid_cards):
        """Modified to include center assignment"""
        plans = []
        centers = list(PhototherapyCenter.objects.all())
        
        for user in random.sample(users, len(users)//3):
            plan = PhototherapyPlan.objects.create(
                patient=user,
                protocol=random.choice(protocols),
                rfid_card=random.choice(rfid_cards) if rfid_cards else None,
                start_date=fake.date_between(start_date='-6m'),
                current_dose=random.uniform(100, 500),
                total_sessions_planned=random.randint(20, 40),
                total_cost=Decimal(random.uniform(1000, 5000)),
                billing_status=random.choice(['PENDING', 'PARTIAL', 'PAID']),
                special_instructions=fake.text(),
                center=random.choice(centers)  # Assign a random center
            )
            plans.append(plan)
        return plans

    def _create_sessions(self, plans, devices):
        sessions = []
        try:
            # Get eligible staff members first
            excluded_roles = [
                'PATIENT', 'HR_STAFF', 'INVENTORY_MANAGER', 'BILLING_STAFF',
                'LAB_TECHNICIAN', 'PHARMACIST', 'RECEPTIONIST', 'MANAGER'
            ]
            eligible_staff = User.objects.filter(
                is_active=True
            ).exclude(
                role__name__in=excluded_roles
            ).select_related('role')

            if not eligible_staff.exists():
                self.stdout.write(self.style.WARNING('No eligible staff found to administer sessions'))
                return []

            for plan in plans:
                for i in range(random.randint(5, 15)):
                    session_date = fake.date_between(start_date='-3m')
                    # Generate some sample remarks
                    remarks = random.choice([
                        "Patient reported mild sensitivity during previous session",
                        "Dose increased as per protocol guidelines",
                        "Patient requested morning appointments for future sessions",
                        "Treatment area showing good response",
                        "Patient experienced slight redness after last session",
                        "Follow standard protocol - no special instructions",
                        "Monitor exposure time carefully",
                        "Patient has sensitive skin - proceed with caution",
                        "",  # Empty remarks for some sessions
                    ])
                    
                    session = PhototherapySession.objects.create(
                        plan=plan,
                        session_number=i+1,
                        scheduled_date=session_date,
                        scheduled_time=fake.time(),
                        device=random.choice(devices),
                        planned_dose=random.uniform(100, 500),
                        actual_dose=random.uniform(100, 500),
                        duration_seconds=random.randint(60, 300),
                        status=random.choice(['COMPLETED', 'MISSED', 'SCHEDULED']),
                        problem_severity='NONE',
                        administered_by=random.choice(eligible_staff),
                        actual_date=session_date,
                        remarks=remarks  # Add remarks here
                    )
                    sessions.append(session)
                    self.stdout.write(f'Created session {session.session_number} for plan {plan.id} with administrator {session.administered_by.get_full_name()}')

            return sessions
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sessions: {str(e)}')
            )
            return []

    def _create_home_logs(self, plans):
        for plan in plans:
            for _ in range(random.randint(3, 10)):
                HomePhototherapyLog.objects.create(
                    plan=plan,
                    date=fake.date_between(start_date='-3m'),
                    time=fake.time(),
                    duration_minutes=random.randint(5, 30),
                    exposure_type=random.choice(['UVB_DEVICE', 'SUNLIGHT']),
                    body_areas_treated=fake.text(max_nb_chars=100),
                    notes=fake.text()
                )

    def _create_problem_reports(self, sessions, users):
        for session in random.sample(sessions, len(sessions)//4):
            ProblemReport.objects.create(
                session=session,
                reported_by=random.choice(users),
                problem_description=fake.text(),
                severity=random.choice(['MILD', 'MODERATE', 'SEVERE']),
                action_taken=fake.text(),
                resolved=random.choice([True, False])
            )

    def _create_payments(self, plans, users):
        for plan in plans:
            try:
                total_amount = float(plan.total_cost)
                payment_type = random.choice(['FULL', 'PER_SESSION', 'PARTIAL'])
                
                if payment_type == 'FULL':
                    # Create single full payment
                    receipt_number = f"RCP-{int(timezone.now().timestamp())}-{random.randint(1000, 9999)}"
                    PhototherapyPayment.objects.create(
                        plan=plan,
                        payment_type='FULL',
                        amount=plan.total_cost,
                        payment_date=timezone.now() - timedelta(days=random.randint(1, 90)),
                        payment_method=random.choice(['CASH', 'CARD', 'UPI']),
                        transaction_id=fake.bothify(text='TXN####'),
                        status='COMPLETED',
                        receipt_number=receipt_number,
                        recorded_by=random.choice(users)
                    )
                
                elif payment_type == 'PER_SESSION':
                    # Create payment for each completed session
                    completed_sessions = plan.sessions.filter(status='COMPLETED')
                    per_session_amount = total_amount / plan.total_sessions_planned
                    
                    for session in completed_sessions:
                        receipt_number = f"RCP-{int(timezone.now().timestamp())}-{random.randint(1000, 9999)}"
                        PhototherapyPayment.objects.create(
                            plan=plan,
                            payment_type='PER_SESSION',
                            session=session,
                            amount=per_session_amount,
                            payment_date=session.actual_date or session.scheduled_date,
                            payment_method=random.choice(['CASH', 'CARD', 'UPI']),
                            transaction_id=fake.bothify(text='TXN####'),
                            status='COMPLETED',
                            receipt_number=receipt_number,
                            recorded_by=random.choice(users)
                        )
                
                else:  # PARTIAL payments with installments
                    # Create 3-4 installment payments
                    num_installments = random.randint(3, 4)
                    amount_per_installment = total_amount / num_installments
                    
                    for i in range(num_installments):
                        receipt_number = f"RCP-{int(timezone.now().timestamp())}-{random.randint(1000, 9999)}"
                        PhototherapyPayment.objects.create(
                            plan=plan,
                            payment_type='PARTIAL',
                            amount=amount_per_installment,
                            payment_date=timezone.now() - timedelta(days=90-i*30),
                            payment_method=random.choice(['CASH', 'CARD', 'UPI']),
                            transaction_id=fake.bothify(text='TXN####'),
                            status='COMPLETED',
                            receipt_number=receipt_number,
                            recorded_by=random.choice(users),
                            is_installment=True,
                            installment_number=i+1,
                            total_installments=num_installments
                        )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error creating payment for plan {plan.id}: {str(e)}'))
                continue

    def _create_reminders(self, plans):
        for plan in plans:
            PhototherapyReminder.objects.create(
                plan=plan,
                reminder_type=random.choice(['SESSION', 'PAYMENT', 'FOLLOWUP']),
                scheduled_datetime=timezone.now() + timedelta(days=random.randint(1, 30)),
                message=fake.text(),
                status='PENDING'
            )

    def _create_progress_records(self, plans, users):
        for plan in plans:
            PhototherapyProgress.objects.create(
                plan=plan,
                assessment_date=fake.date_between(start_date='-3m'),
                response_level=random.choice(['EXCELLENT', 'GOOD', 'MODERATE', 'POOR']),
                improvement_percentage=random.uniform(0, 100),
                notes=fake.text(),
                assessed_by=random.choice(users)
            )

    def _create_maintenance_records(self, devices, users):
        for device in devices:
            DeviceMaintenance.objects.create(
                device=device,
                maintenance_type=random.choice(['ROUTINE', 'REPAIR', 'CALIBRATION']),
                maintenance_date=fake.date_between(start_date='-6m'),
                performed_by=fake.name(),
                description=fake.text(),
                cost=Decimal(random.uniform(100, 1000)),
                next_maintenance_due=fake.date_between(start_date='today'),
                created_by=random.choice(users)
            )
