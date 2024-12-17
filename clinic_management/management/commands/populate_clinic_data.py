from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random
import logging
from faker import Faker

from access_control.models import Role
from clinic_management.models import (
    ClinicArea, ClinicStation, VisitType, ClinicVisit, VisitChecklist,
    VisitChecklistCompletion, PaymentTerminal, VisitPaymentTransaction,
    ClinicFlow, WaitingList, ClinicDaySheet, StaffAssignment,
    ResourceAllocation, ClinicNotification, OperationalAlert, ClinicMetrics
)

logger = logging.getLogger(__name__)
fake = Faker()
User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample clinic management data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--visits',
            type=int,
            default=50,
            help='Number of clinic visits to create'
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write('Starting clinic data population...')
                
                # Create sample data in sequence
                roles = self.create_roles()
                users = self.create_users(roles)
                areas = self.create_clinic_areas()
                stations = self.create_clinic_stations(areas)
                visit_types = self.create_visit_types()
                checklists = self.create_checklists(visit_types)
                terminals = self.create_payment_terminals()
                visits = self.create_clinic_visits(options['visits'], users, visit_types)
                
                # Create related data
                self.create_checklist_completions(visits, checklists, users)
                self.create_payment_transactions(visits, terminals, users)
                self.create_clinic_flows(visits, areas, stations, users)
                self.create_waiting_lists(visits, areas)
                self.create_day_sheets(users)
                self.create_staff_assignments(users, areas, stations)
                self.create_resource_allocations(visits, users)
                self.create_notifications(roles, users)
                self.create_operational_alerts(areas, visit_types, users)
                self.create_clinic_metrics(areas)

                self.stdout.write(self.style.SUCCESS('Successfully populated clinic data'))
                
        except Exception as e:
            logger.error(f'Error populating clinic data: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Failed to populate data: {str(e)}'))

    def create_roles(self):
        roles = []
        role_names = ['DOCTOR', 'NURSE', 'RECEPTIONIST', 'ADMIN', 'PATIENT']
        
        try:
            for role_name in role_names:
                role, created = Role.objects.get_or_create(
                    name=role_name,
                    defaults={
                        'display_name': role_name.title(),
                        'template_folder': role_name.lower(),
                        'description': f'Role for {role_name.lower()}'
                    }
                )
                roles.append(role)
            logger.info(f'Created {len(roles)} roles')
            return roles
        except Exception as e:
            logger.error(f'Error creating roles: {str(e)}')
            raise

    def create_users(self, roles):
        users = []
        try:
            for i in range(20):
                role = random.choice(roles)
                user = User.objects.create(
                    email=fake.email(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=fake.phone_number(),
                    role=role
                )
                users.append(user)
            logger.info(f'Created {len(users)} users')
            return users
        except Exception as e:
            logger.error(f'Error creating users: {str(e)}')
            raise

    def create_clinic_areas(self):
        areas = []
        area_data = [
            ('Reception', 'RCPT', 20, False),
            ('Consultation', 'CONS', 10, True),
            ('Procedure', 'PROC', 5, True),
            ('Pharmacy', 'PHAR', 15, False),
            ('Laboratory', 'LAB', 8, False)
        ]
        
        try:
            for name, code, capacity, requires_doctor in area_data:
                area = ClinicArea.objects.create(
                    name=name,
                    code=code,
                    description=f'{name} area of the clinic',
                    capacity=capacity,
                    requires_doctor=requires_doctor
                )
                areas.append(area)
            logger.info(f'Created {len(areas)} clinic areas')
            return areas
        except Exception as e:
            logger.error(f'Error creating clinic areas: {str(e)}')
            raise

    def create_clinic_stations(self, areas):
        stations = []
        try:
            for area in areas:
                for i in range(1, random.randint(2, 5)):
                    station = ClinicStation.objects.create(
                        area=area,
                        name=f'{area.name} Station {i}',
                        station_number=f'{area.code}-{i:02d}',
                        current_status='AVAILABLE'
                    )
                    stations.append(station)
            logger.info(f'Created {len(stations)} clinic stations')
            return stations
        except Exception as e:
            logger.error(f'Error creating clinic stations: {str(e)}')
            raise

    def create_visit_types(self):
        visit_types = []
        type_data = [
            ('Initial Consultation', 'INIT', 30),
            ('Follow-up', 'FOLLOW', 20),
            ('Procedure', 'PROC', 45),
            ('Lab Test', 'LAB', 15),
            ('Pharmacy Visit', 'PHARM', 10)
        ]
        
        try:
            for name, code, duration in type_data:
                visit_type = VisitType.objects.create(
                    name=name,
                    code=code,
                    description=f'Visit type for {name}',
                    default_duration=duration,
                    requires_doctor=code in ['INIT', 'FOLLOW', 'PROC']
                )
                visit_types.append(visit_type)
            logger.info(f'Created {len(visit_types)} visit types')
            return visit_types
        except Exception as e:
            logger.error(f'Error creating visit types: {str(e)}')
            raise

    def create_checklists(self, visit_types):
        checklists = []
        try:
            for visit_type in visit_types:
                for i in range(3):
                    checklist = VisitChecklist.objects.create(
                        visit_type=visit_type,
                        name=f'Checklist {i+1} for {visit_type.name}',
                        description=fake.text(),
                        is_mandatory=random.choice([True, False]),
                        order=i,
                        estimated_duration=random.randint(5, 30)
                    )
                    checklists.append(checklist)
            logger.info(f'Created {len(checklists)} checklists')
            return checklists
        except Exception as e:
            logger.error(f'Error creating checklists: {str(e)}')
            raise

    def create_payment_terminals(self):
        terminals = []
        terminal_data = [
            ('Main Counter', 'CARD'),
            ('Reception', 'UPI'),
            ('Pharmacy', 'CASH')
        ]
        
        try:
            for location, term_type in terminal_data:
                terminal = PaymentTerminal.objects.create(
                    name=f'{location} Terminal',
                    terminal_id=f'TERM{random.randint(1000, 9999)}',
                    location=location,
                    terminal_type=term_type
                )
                terminals.append(terminal)
            logger.info(f'Created {len(terminals)} payment terminals')
            return terminals
        except Exception as e:
            logger.error(f'Error creating payment terminals: {str(e)}')
            raise

    def create_clinic_visits(self, num_visits, users, visit_types):
        visits = []
        priorities = ['A', 'B', 'C']
        statuses = ['REGISTERED', 'WAITING', 'IN_PROGRESS', 'COMPLETED']
        
        try:
            patients = [u for u in users if u.role.name == 'PATIENT']
            doctors = [u for u in users if u.role.name == 'DOCTOR']
            
            for _ in range(num_visits):
                visit = ClinicVisit.objects.create(
                    patient=random.choice(patients),
                    visit_type=random.choice(visit_types),
                    priority=random.choice(priorities),
                    status=random.choice(statuses),
                    chief_complaint=fake.text(),
                    created_by=random.choice(users)
                )
                visits.append(visit)
            logger.info(f'Created {len(visits)} clinic visits')
            return visits
        except Exception as e:
            logger.error(f'Error creating clinic visits: {str(e)}')
            raise

    def create_checklist_completions(self, visits, checklists, users):
        try:
            for visit in visits:
                for checklist in random.sample(checklists, k=random.randint(1, 3)):
                    VisitChecklistCompletion.objects.create(
                        visit=visit,
                        checklist_item=checklist,
                        status=random.choice(['PENDING', 'COMPLETED']),
                        completed_by=random.choice(users) if random.choice([True, False]) else None
                    )
            logger.info('Created checklist completions')
        except Exception as e:
            logger.error(f'Error creating checklist completions: {str(e)}')
            raise

    def create_payment_transactions(self, visits, terminals, users):
        try:
            for visit in visits:
                if random.choice([True, False]):
                    VisitPaymentTransaction.objects.create(
                        visit=visit,
                        amount=random.randint(100, 1000),
                        payment_method=random.choice(['CASH', 'CARD', 'UPI']),
                        terminal=random.choice(terminals),
                        transaction_id=f'TXN{random.randint(10000, 99999)}',
                        status=random.choice(['COMPLETED', 'PENDING']),
                        receipt_number=f'RCPT{random.randint(10000, 99999)}',
                        processed_by=random.choice(users)
                    )
            logger.info('Created payment transactions')
        except Exception as e:
            logger.error(f'Error creating payment transactions: {str(e)}')
            raise

    def create_clinic_flows(self, visits, areas, stations, users):
        try:
            for visit in visits:
                for area in random.sample(areas, k=random.randint(1, 3)):
                    ClinicFlow.objects.create(
                        visit=visit,
                        area=area,
                        station=random.choice(stations),
                        entry_time=timezone.now() - timedelta(hours=random.randint(1, 8)),
                        exit_time=timezone.now() - timedelta(hours=random.randint(0, 1)),
                        status=random.choice(['WAITING', 'IN_PROGRESS', 'COMPLETED']),
                        handled_by=random.choice(users)
                    )
            logger.info('Created clinic flows')
        except Exception as e:
            logger.error(f'Error creating clinic flows: {str(e)}')
            raise

    def create_waiting_lists(self, visits, areas):
        try:
            for visit in visits:
                if random.choice([True, False]):
                    WaitingList.objects.create(
                        area=random.choice(areas),
                        visit=visit,
                        priority=random.choice(['A', 'B', 'C']),
                        estimated_wait_time=random.randint(5, 60),
                        status=random.choice(['WAITING', 'CALLED', 'IN_PROGRESS'])
                    )
            logger.info('Created waiting lists')
        except Exception as e:
            logger.error(f'Error creating waiting lists: {str(e)}')
            raise

    def create_day_sheets(self, users):
        try:
            for i in range(7):
                date = timezone.now().date() - timedelta(days=i)
                ClinicDaySheet.objects.create(
                    date=date,
                    status=random.choice(['PLANNED', 'IN_PROGRESS', 'COMPLETED']),
                    total_appointments=random.randint(20, 50),
                    total_walk_ins=random.randint(5, 15),
                    total_patients=random.randint(25, 65),
                    opened_by=random.choice(users),
                    closed_by=random.choice(users) if random.choice([True, False]) else None
                )
            logger.info('Created day sheets')
        except Exception as e:
            logger.error(f'Error creating day sheets: {str(e)}')
            raise

    def create_staff_assignments(self, users, areas, stations):
        try:
            staff = [u for u in users if u.role.name != 'PATIENT']
            for user in staff:
                StaffAssignment.objects.create(
                    staff=user,
                    area=random.choice(areas),
                    station=random.choice(stations),
                    date=timezone.now().date(),
                    start_time=timezone.now().time(),
                    end_time=(timezone.now() + timedelta(hours=8)).time(),
                    is_primary=random.choice([True, False]),
                    status=random.choice(['SCHEDULED', 'IN_PROGRESS'])
                )
            logger.info('Created staff assignments')
        except Exception as e:
            logger.error(f'Error creating staff assignments: {str(e)}')
            raise

    def create_resource_allocations(self, visits, users):
        try:
            for visit in visits:
                ResourceAllocation.objects.create(
                    visit=visit,
                    resource_type=random.choice(['ROOM', 'EQUIPMENT', 'STAFF']),
                    resource_id=f'RES{random.randint(100, 999)}',
                    allocated_by=random.choice(users)
                )
            logger.info('Created resource allocations')
        except Exception as e:
            logger.error(f'Error creating resource allocations: {str(e)}')
            raise

    def create_notifications(self, roles, users):
        try:
            for _ in range(10):
                notification = ClinicNotification.objects.create(
                    title=fake.sentence(),
                    message=fake.text(),
                    priority=random.choice(['HIGH', 'MEDIUM', 'LOW']),
                    status=random.choice(['PENDING', 'SENT', 'READ']),
                    send_at=timezone.now(),
                    expires_at=timezone.now() + timedelta(days=random.randint(1, 30)),
                    created_by=random.choice(users)
                )
                # Add random roles to the notification
                notification.recipient_roles.set(random.sample(roles, k=random.randint(1, 3)))
                # Add random users to the notification
                notification.recipient_users.set(random.sample(list(users), k=random.randint(1, 5)))
            logger.info('Created clinic notifications')
        except Exception as e:
            logger.error(f'Error creating clinic notifications: {str(e)}')
            raise

    def create_operational_alerts(self, areas, visit_types, users):
        try:
            alert_types = ['CAPACITY', 'WAIT_TIME', 'RESOURCE', 'EMERGENCY', 'OTHER']
            for _ in range(5):
                alert = OperationalAlert.objects.create(
                    title=fake.sentence(),
                    description=fake.text(),
                    alert_type=random.choice(alert_types),
                    priority=random.choice(['HIGH', 'MEDIUM', 'LOW']),
                    status=random.choice(['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED']),
                    area=random.choice(areas),
                    resolution_notes=fake.text() if random.choice([True, False]) else '',
                    resolved_by=random.choice(users) if random.choice([True, False]) else None,
                    resolved_at=timezone.now() if random.choice([True, False]) else None
                )
                # Add random affected services
                alert.affected_services.set(random.sample(list(visit_types), k=random.randint(1, 3)))
            logger.info('Created operational alerts')
        except Exception as e:
            logger.error(f'Error creating operational alerts: {str(e)}')
            raise

    def create_clinic_metrics(self, areas):
        try:
            # Create metrics for the last 30 days
            for i in range(30):
                date = timezone.now().date() - timedelta(days=i)
                for area in areas:
                    ClinicMetrics.objects.create(
                        date=date,
                        area=area,
                        total_patients=random.randint(10, 50),
                        avg_wait_time=random.uniform(5.0, 60.0),
                        max_wait_time=random.uniform(60.0, 120.0),
                        total_no_shows=random.randint(0, 5),
                        capacity_utilization=random.uniform(50.0, 95.0)
                    )
            logger.info('Created clinic metrics')
        except Exception as e:
            logger.error(f'Error creating clinic metrics: {str(e)}')
            raise