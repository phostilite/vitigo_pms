from django.db import models
from django.conf import settings
from patient_management.models import Patient


class BodyPart(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ImageTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PatientImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('CLINIC', 'Clinic Taken'),
        ('PATIENT', 'Patient Uploaded'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='images')
    image_file = models.ImageField(upload_to='patient_images/')
    body_part = models.ForeignKey(BodyPart, on_delete=models.SET_NULL, null=True)
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES)
    date_taken = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(ImageTag, blank=True)

    # Metadata
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)  # in bytes

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='uploaded_images')
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return f"Image of {self.patient.user.get_full_name()} - {self.body_part} on {self.date_taken}"


class ImageComparison(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    images = models.ManyToManyField(PatientImage, through='ComparisonImage')

    def __str__(self):
        return self.title


class ComparisonImage(models.Model):
    comparison = models.ForeignKey(ImageComparison, on_delete=models.CASCADE)
    image = models.ForeignKey(PatientImage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('comparison', 'image')

    def __str__(self):
        return f"Image {self.order} in {self.comparison.title}"


class ImageAnnotation(models.Model):
    image = models.ForeignKey(PatientImage, on_delete=models.CASCADE, related_name='annotations')
    x_coordinate = models.FloatField()
    y_coordinate = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Annotation for {self.image} at ({self.x_coordinate}, {self.y_coordinate})"