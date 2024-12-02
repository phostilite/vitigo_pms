# consultation/management/commands/populate_consultations.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files import File
from PIL import Image
import os
from django.conf import settings
from patient_management.models import Patient, Medication
from consultation_management.models import (
    Consultation, Prescription, TreatmentInstruction, 
    ConsultationAttachment, FollowUpPlan
)
from image_management.models import PatientImage, BodyPart
from access_control.models import Role  # Add this import

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate sample consultations data with patient images'

    def generate_sample_image(self):
        """Generate a sample image file"""
        img_dir = os.path.join(settings.MEDIA_ROOT, 'temp_images')
        os.makedirs(img_dir, exist_ok=True)
        
        # Create a random colored image
        width, height = random.randint(800, 1200), random.randint(800, 1200)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        img = Image.new('RGB', (width, height), color=color)
        img_path = os.path.join(img_dir, f'sample_{random.randint(1000, 9999)}.png')
        img.save(img_path)
        
        return img_path

    def create_patient_images(self, consultation, patient):
        """Create sample images for a consultation"""
        try:
            # Get or create some body parts
            body_parts = BodyPart.objects.all()
            if not body_parts.exists():
                body_parts = [
                    BodyPart.objects.create(name=name) 
                    for name in ['Face', 'Hands', 'Arms', 'Legs', 'Trunk']
                ]
            else:
                body_parts = list(body_parts)

            # Create 1-3 images per consultation
            for _ in range(random.randint(1, 3)):
                img_path = self.generate_sample_image()
                
                with open(img_path, 'rb') as img_file:
                    image = PatientImage.objects.create(
                        patient=patient,
                        image_file=File(img_file, name=f'patient_{patient.id}_consult_{consultation.id}.png'),
                        body_part=random.choice(body_parts),
                        image_type='CLINIC',
                        date_taken=consultation.date_time.date(),
                        consultation=consultation,
                        uploaded_by=consultation.doctor,
                        notes=f"Image taken during consultation on {consultation.date_time.date()}"
                    )
                
                # Clean up temporary file
                os.remove(img_path)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating images for consultation {consultation.id}: {str(e)}')
            )

    def handle(self, *args, **kwargs):
        try:
            # Get roles first
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')

            # Get only users who have patient profiles
            patient_users = User.objects.filter(
                role=patient_role,
                patient_profile__isnull=False  # Only get users with patient profiles
            ).select_related('patient_profile')  # Optimize by pre-fetching patient profiles
            
            doctors = User.objects.filter(role=doctor_role)
            medications = Medication.objects.all()

            if not patient_users.exists() or not doctors.exists() or not medications.exists():
                self.stdout.write(
                    self.style.ERROR(
                        'Ensure there are patients with profiles, doctors, and medications in the system.'
                    )
                )
                return

            consultation_types = ['INITIAL', 'FOLLOW_UP', 'EMERGENCY', 'TELE']
            for _ in range(25):  # Create 25 sample consultations
                patient_user = random.choice(patient_users)
                doctor = random.choice(doctors)
                
                consultation = Consultation.objects.create(
                    patient=patient_user,  # Now using the User instance directly
                    doctor=doctor,
                    consultation_type=random.choice(consultation_types),
                    date_time=timezone.now() - timezone.timedelta(days=random.randint(0, 365)),
                    chief_complaint="Sample chief complaint",
                    vitals={"blood_pressure": "120/80", "heart_rate": "72"},
                    notes="Sample notes",
                    diagnosis="Sample diagnosis",
                    follow_up_date=timezone.now() + timezone.timedelta(days=random.randint(1, 30))
                )

                # Create sample images for this consultation
                self.create_patient_images(consultation, patient_user.patient_profile)

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
                    follow_up_date=timezone.now() + timezone.timedelta(days=random.randint(1, 30)),
                    reason="Sample follow-up reason",
                    tests_required="Sample tests required",
                    additional_notes="Sample additional notes"
                )

            self.stdout.write(
                self.style.SUCCESS('Successfully populated sample consultations data with images.')
            )

        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Required roles (PATIENT, DOCTOR) not found. Please run populate_access_control first.'
                )
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred: {str(e)}')
            )
            return