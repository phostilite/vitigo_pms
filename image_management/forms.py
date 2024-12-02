from django import forms
from .models import PatientImage, Patient, ImageAnnotation
from datetime import date
from django.conf import settings
from consultation_management.models import Consultation

class PatientImageUploadForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select rounded-lg'})
    )
    consultation = forms.ModelChoiceField(
        queryset=Consultation.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select rounded-lg'})
    )

    class Meta:
        model = PatientImage
        fields = ['patient', 'image_file', 'body_part', 'image_type', 'consultation', 'date_taken', 'notes', 'is_private']
        widgets = {
            'date_taken': forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_image_file(self):
        image = self.cleaned_data.get('image_file')
        if image:
            if image.size > settings.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(f'Image size cannot exceed {settings.MAX_UPLOAD_SIZE/1024/1024}MB')
            return image
        raise forms.ValidationError('No image file uploaded')

class ImageAnnotationForm(forms.ModelForm):
    class Meta:
        model = ImageAnnotation
        fields = ['x_coordinate', 'y_coordinate', 'width', 'height', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'rounded-lg'}),
        }

class AnnotationForm(forms.ModelForm):
    class Meta:
        model = ImageAnnotation
        fields = ['x_coordinate', 'y_coordinate', 'width', 'height', 'text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'rounded-lg w-full',
                'placeholder': 'Enter annotation details...'
            })
        }
