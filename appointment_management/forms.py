from django import forms
from .models import Appointment, DoctorTimeSlot
from django.contrib.auth import get_user_model
from access_control.models import Role

User = get_user_model()

class AppointmentCreateForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        help_text='Select appointment date'
    )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_type', 'date', 'priority', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            # Get role objects first
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')
            
            # Then filter users by role objects
            self.fields['patient'].queryset = User.objects.filter(role=patient_role)
            self.fields['doctor'].queryset = User.objects.filter(role=doctor_role)
            
        except Role.DoesNotExist as e:
            # Log the error and provide empty querysets as fallback
            print(f"Error loading roles: {e}")
            self.fields['patient'].queryset = User.objects.none()
            self.fields['doctor'].queryset = User.objects.none()
