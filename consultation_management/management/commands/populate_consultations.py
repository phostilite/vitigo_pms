# consultation/management/commands/populate_consultations.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from patient_management.models import Patient
from consultation_management.models import Consultation, Prescription, TreatmentInstruction, ConsultationAttachment, FollowUpPlan
from patient_management.models import Medication

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate sample consultations data'

    def handle(self, *args, **kwargs):
        patients = Patient.objects.all()
        doctors = User.objects.filter(role='DOCTOR')
        medications = Medication.objects.all()

        if not patients.exists() or not doctors.exists() or not medications.exists():
            self.stdout.write(self.style.ERROR('Ensure there are patients, doctors, and medications in the system before running this command.'))
            return

        consultation_types = ['INITIAL', 'FOLLOW_UP', 'EMERGENCY', 'TELE']
        for _ in range(25):  # Create 50 sample consultations
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            consultation_type = random.choice(consultation_types)
            date_time = timezone.now() - timezone.timedelta(days=random.randint(0, 365))
            chief_complaint = "Sample chief complaint"
            vitals = {"blood_pressure": "120/80", "heart_rate": "72"}
            notes = "Sample notes"
            diagnosis = "Sample diagnosis"
            follow_up_date = date_time + timezone.timedelta(days=random.randint(1, 30))

            consultation = Consultation.objects.create(
                patient=patient,
                doctor=doctor,
                consultation_type=consultation_type,
                date_time=date_time,
                chief_complaint=chief_complaint,
                vitals=vitals,
                notes=notes,
                diagnosis=diagnosis,
                follow_up_date=follow_up_date
            )

            # Create sample prescriptions
            for _ in range(random.randint(1, 3)):
                medication = random.choice(medications)
                dosage = "1 tablet"
                frequency = "Twice a day"
                duration = "7 days"
                instructions = "Take after meals"

                Prescription.objects.create(
                    consultation=consultation,
                    medication=medication,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions
                )

            # Create sample treatment instructions
            TreatmentInstruction.objects.create(
                consultation=consultation,
                lifestyle_changes="Sample lifestyle changes",
                dietary_instructions="Sample dietary instructions",
                skincare_routine="Sample skincare routine",
                additional_notes="Sample additional notes"
            )

            # Create sample consultation attachments
            ConsultationAttachment.objects.create(
                consultation=consultation,
                file='/Users/apple/Documents/vitigo_pms/test.pdf',
                description="Sample attachment"
            )

            # Create sample follow-up plan
            FollowUpPlan.objects.create(
                consultation=consultation,
                follow_up_date=follow_up_date,
                reason="Sample follow-up reason",
                tests_required="Sample tests required",
                additional_notes="Sample additional notes"
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated sample consultations data.'))