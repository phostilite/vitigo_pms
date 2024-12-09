# consultation/management/commands/populate_consultations.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
import random
from datetime import timedelta
from decimal import Decimal
import logging

from access_control.models import Role
from consultation_management.models import (
    Consultation, ConsultationPriority, ConsultationType,
    DoctorPrivateNotes, PrescriptionTemplate, TemplateItem,
    Prescription, PrescriptionItem, TreatmentPlan, PaymentStatus,
    TreatmentPlanItem, StaffInstruction, ConsultationPhototherapy,
    ConsultationAttachment
)
from patient_management.models import Medication
from stock_management.models import StockItem
from phototherapy_management.models import PhototherapySession, PhototherapyPlan, PhototherapyProtocol, PhototherapyType

fake = Faker()
logger = logging.getLogger(__name__)

# Add these medical-related lists
MEDICAL_PROCEDURES = [
    'Skin Examination', 'Vitiligo Assessment', 'Patch Testing',
    'UV Light Therapy', 'Skin Biopsy', 'Wood\'s Lamp Examination',
    'Phototherapy Session', 'Melanin Level Check', 'Skin Photography',
    'Treatment Response Assessment'
]

MEDICAL_CONDITIONS = [
    'Vitiligo', 'Focal Vitiligo', 'Segmental Vitiligo', 
    'Non-segmental Vitiligo', 'Universal Vitiligo',
    'Acrofacial Vitiligo', 'Mucosal Vitiligo'
]

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate sample consultation data with all related models'

    def generate_vitals(self):
        """Generate realistic vitals data"""
        return {
            "blood_pressure": f"{random.randint(110, 140)}/{random.randint(70, 90)}",
            "heart_rate": random.randint(60, 100),
            "temperature": round(random.uniform(36.1, 37.5), 1),
            "weight": round(random.uniform(50, 90), 1),
            "height": round(random.uniform(150, 190), 1),
            "bmi": round(random.uniform(18.5, 29.9), 1),
            "respiratory_rate": random.randint(12, 20),
            "oxygen_saturation": random.randint(95, 100)
        }

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Get required roles and users
                doctor_role = Role.objects.get(name='DOCTOR')
                patient_role = Role.objects.get(name='PATIENT')
                
                doctors = User.objects.filter(role=doctor_role)
                patients = User.objects.filter(role=patient_role)
                medications = Medication.objects.all()
                stock_items = StockItem.objects.all()

                if not all([doctors, patients, medications, stock_items]):
                    self.stdout.write(self.style.ERROR('Required data missing. Please populate users, medications, and stock items first.'))
                    return

                # Create prescription templates first
                self.create_prescription_templates(doctors, medications)

                # Create consultations with all related data
                self.create_consultations(doctors, patients, medications, stock_items)

                self.stdout.write(self.style.SUCCESS('Successfully populated consultation data'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def create_prescription_templates(self, doctors, medications):
        """Create reusable prescription templates"""
        templates = []
        for doctor in doctors:
            for _ in range(random.randint(2, 5)):
                template = PrescriptionTemplate.objects.create(
                    name=random.choice(MEDICAL_PROCEDURES),
                    doctor=doctor,
                    description=fake.text(),
                    is_global=random.choice([True, False]),
                    is_active=True
                )
                
                # Add items to template
                for _ in range(random.randint(2, 4)):
                    TemplateItem.objects.create(
                        template=template,
                        medication=random.choice(medications),
                        dosage=f"{random.randint(1, 3)} tablet(s)",
                        frequency=random.choice(["Once daily", "Twice daily", "Three times daily"]),
                        duration=f"{random.randint(1, 14)} days",
                        instructions=fake.sentence(),
                        order=_
                    )
                templates.append(template)
        return templates

    def create_consultations(self, doctors, patients, medications, stock_items):
        """Create comprehensive consultation records"""
        for _ in range(50):  # Create 50 sample consultations
            # Basic consultation data
            scheduled_time = timezone.now() - timedelta(days=random.randint(-30, 30))
            duration = random.choice([15, 30, 45, 60])
            is_completed = scheduled_time < timezone.now()
            
            consultation = Consultation.objects.create(
                patient=random.choice(patients),
                doctor=random.choice(doctors),
                consultation_type=random.choice(ConsultationType.choices)[0],
                priority=random.choice(ConsultationPriority.choices)[0],
                scheduled_datetime=scheduled_time,
                actual_start_time=scheduled_time if is_completed else None,
                actual_end_time=scheduled_time + timedelta(minutes=duration) if is_completed else None,
                chief_complaint=fake.sentence(),
                vitals=self.generate_vitals() if is_completed else None,
                symptoms="\n".join(fake.sentences(3)),
                clinical_notes=fake.text(),
                diagnosis=random.choice(MEDICAL_CONDITIONS),
                follow_up_date=scheduled_time.date() + timedelta(days=random.randint(7, 30)),
                status='COMPLETED' if is_completed else 'SCHEDULED',
                duration_minutes=duration
            )

            # Create private notes
            DoctorPrivateNotes.objects.create(
                consultation=consultation,
                clinical_observations=fake.text(),
                differential_diagnosis=fake.text(),
                treatment_rationale=fake.text(),
                private_remarks=fake.text()
            )

            # Create prescriptions
            self.create_prescriptions(consultation, medications, stock_items)

            # Create treatment plan
            self.create_treatment_plan(consultation)

            # Create staff instructions
            StaffInstruction.objects.create(
                consultation=consultation,
                pre_consultation=fake.text(),
                during_consultation=fake.text(),
                post_consultation=fake.text(),
                priority=random.choice(ConsultationPriority.choices)[0]
            )

            # Create phototherapy sessions
            if random.choice([True, False]):
                self.create_phototherapy_session(consultation)

            # Create attachments
            self.create_attachments(consultation)

    def create_prescriptions(self, consultation, medications, stock_items):
        """Create prescriptions with items"""
        prescription = Prescription.objects.create(
            consultation=consultation,
            notes=fake.text()
        )

        for i in range(random.randint(1, 5)):
            PrescriptionItem.objects.create(
                prescription=prescription,
                medication=random.choice(medications),
                stock_item=random.choice(stock_items),
                dosage=f"{random.randint(1, 3)} tablet(s)",
                frequency=random.choice(["Once daily", "Twice daily", "Three times daily"]),
                duration=f"{random.randint(1, 14)} days",
                quantity_prescribed=random.randint(7, 30),
                instructions=fake.sentence(),
                order=i
            )

    def create_treatment_plan(self, consultation):
        """Create treatment plan with items"""
        plan = TreatmentPlan.objects.create(
            consultation=consultation,
            description=fake.text(),
            duration_weeks=random.randint(4, 12),
            goals=fake.text(),
            lifestyle_modifications=fake.text(),
            dietary_recommendations=fake.text(),
            exercise_recommendations=fake.text(),
            expected_outcomes=fake.text(),
            total_cost=Decimal(random.randint(1000, 5000)),
            payment_status=random.choice(PaymentStatus.choices)[0]
        )

        for i in range(random.randint(2, 5)):
            TreatmentPlanItem.objects.create(
                treatment_plan=plan,
                name=random.choice(MEDICAL_PROCEDURES),
                description=fake.text(),
                cost=Decimal(random.randint(200, 1000)),
                order=i
            )

    def create_phototherapy_session(self, consultation):
        """Create phototherapy session link"""
        try:
            # Get or create a phototherapy type
            photo_type, _ = PhototherapyType.objects.get_or_create(
                name="NBUVB",
                defaults={
                    'description': 'Narrow Band Ultra-Violet B therapy',
                    'is_active': True
                }
            )

            # Get or create a protocol
            protocol, _ = PhototherapyProtocol.objects.get_or_create(
                phototherapy_type=photo_type,
                name="Standard NBUVB Protocol",
                defaults={
                    'description': 'Standard protocol for NBUVB therapy',
                    'initial_dose': 200.0,
                    'max_dose': 2000.0,
                    'increment_percentage': 20.0,
                    'frequency': '3 times per week',
                    'duration_weeks': 12
                }
            )

            # Create a phototherapy plan
            plan = PhototherapyPlan.objects.create(
                patient=consultation.patient,
                protocol=protocol,
                start_date=consultation.scheduled_datetime.date(),
                current_dose=protocol.initial_dose,
                notes="Initial treatment plan",
                created_by=consultation.doctor,
                is_active=True
            )

            # Create the phototherapy session
            session = PhototherapySession.objects.create(
                plan=plan,
                session_date=consultation.scheduled_datetime.date(),
                actual_dose=plan.current_dose,
                duration=random.randint(300, 900),  # 5-15 minutes in seconds
                compliance='COMPLETED',
                notes=fake.text(),
                administered_by=consultation.doctor
            )

            # Create the consultation-phototherapy link
            ConsultationPhototherapy.objects.create(
                consultation=consultation,
                phototherapy_session=session,
                instructions=fake.text(),
                schedule=consultation.scheduled_datetime + timedelta(days=random.randint(1, 7)),
                notes=fake.text()
            )

        except Exception as e:
            logger.error(f"Error creating phototherapy session: {str(e)}")
            raise

    def create_attachments(self, consultation):
        """Create dummy attachments"""
        for _ in range(random.randint(1, 3)):
            ConsultationAttachment.objects.create(
                consultation=consultation,
                file='sample.pdf',  # You would need actual files in production
                title=fake.sentence(),
                description=fake.text(),
                file_type=random.choice(['PDF', 'IMAGE', 'DOCUMENT']),
                uploaded_by=consultation.doctor
            )
    def create_attachments(self, consultation):
        """Create dummy attachments"""
        for _ in range(random.randint(1, 3)):
            ConsultationAttachment.objects.create(
                consultation=consultation,
                file='sample.pdf',  # You would need actual files in production
                title=fake.sentence(),
                description=fake.text(),
                file_type=random.choice(['PDF', 'IMAGE', 'DOCUMENT']),
                uploaded_by=consultation.doctor
            )