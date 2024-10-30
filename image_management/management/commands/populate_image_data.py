# image_management/management/commands/populate_image_data.py

import random
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from PIL import Image
from django.conf import settings
from user_management.models import CustomUser
from patient_management.models import Patient
from image_management.models import (
    BodyPart, ImageTag, PatientImage, ImageComparison, ComparisonImage, ImageAnnotation
)

class Command(BaseCommand):
    help = 'Generate sample image management data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample image management data...')

        # Create sample body parts if they don't exist
        body_parts = [
            {'name': 'Head', 'description': 'Head region'},
            {'name': 'Arm', 'description': 'Arm region'},
            {'name': 'Leg', 'description': 'Leg region'},
        ]
        for part in body_parts:
            BodyPart.objects.get_or_create(
                name=part['name'],
                defaults={'description': part['description']}
            )

        # Create sample image tags if they don't exist
        tags = ['Tag1', 'Tag2', 'Tag3']
        for tag in tags:
            ImageTag.objects.get_or_create(name=tag)

        # Fetch all body parts, tags, patients, and staff
        body_parts = BodyPart.objects.all()
        tags = ImageTag.objects.all()
        patients = Patient.objects.all()
        users = CustomUser.objects.all()

        # Path to the sample image file in the media folder
        sample_image_dir = os.path.join(settings.MEDIA_ROOT, 'sample_images')
        sample_image_path = os.path.join(sample_image_dir, 'sample_image.jpg')

        # Create the sample image file if it doesn't exist
        if not os.path.exists(sample_image_dir):
            os.makedirs(sample_image_dir)
        if not os.path.exists(sample_image_path):
            image = Image.new('RGB', (100, 100), color = (73, 109, 137))
            image.save(sample_image_path)

        # Generate sample patient images
        for _ in range(20):  # Generate 20 sample patient images
            patient = random.choice(patients)
            body_part = random.choice(body_parts)
            uploaded_by = random.choice(users)
            image_type = random.choice(['CLINIC', 'PATIENT'])
            date_taken = timezone.now().date() - timezone.timedelta(days=random.randint(0, 365))

            with open(sample_image_path, 'rb') as image_file:
                patient_image = PatientImage.objects.create(
                    patient=patient,
                    image_file=File(image_file, name='sample_images/sample_image.jpg'),
                    body_part=body_part,
                    image_type=image_type,
                    date_taken=date_taken,
                    uploaded_by=uploaded_by,
                    is_private=random.choice([True, False])
                )
                patient_image.tags.set(random.sample(list(tags), random.randint(1, len(tags))))
                patient_image.save()

        # Generate sample image comparisons
        for _ in range(5):  # Generate 5 sample image comparisons
            created_by = random.choice(users)
            comparison = ImageComparison.objects.create(
                title=f"Comparison {_ + 1}",
                description='Sample comparison description',
                created_by=created_by
            )
            images = random.sample(list(PatientImage.objects.all()), random.randint(2, 5))
            for order, image in enumerate(images, start=1):
                ComparisonImage.objects.create(
                    comparison=comparison,
                    image=image,
                    order=order
                )

        # Generate sample image annotations
        for image in PatientImage.objects.all():
            for _ in range(random.randint(1, 3)):  # Add 1 to 3 annotations to each image
                ImageAnnotation.objects.create(
                    image=image,
                    x_coordinate=random.uniform(0, 1),
                    y_coordinate=random.uniform(0, 1),
                    width=random.uniform(0.1, 0.5),
                    height=random.uniform(0.1, 0.5),
                    text='Sample annotation text',
                    created_by=random.choice(users)
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample image management data'))