from django import forms
from .models import Appointment, DoctorTimeSlot
from django.contrib.auth import get_user_model
from access_control.models import Role

User = get_user_model()

class AppointmentCreateForm(forms.ModelForm):
    timeslot_id = forms.CharField(
        widget=forms.HiddenInput(), 
        required=True
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        help_text='Select the date for your appointment (must be within next 30 days)'
    )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_type', 'date', 'priority', 'notes', 'timeslot_id']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
        help_texts = {
            'patient': 'Select the patient who needs the appointment',
            'doctor': 'Select the doctor you want to consult with',
            'appointment_type': 'Choose the type of appointment (consultation, follow-up, procedure, or phototherapy)',
            'priority': 'Set priority level - High (A) for urgent cases, Medium (B) for regular visits, Low (C) for routine checkups',
            'notes': 'Add any relevant details, symptoms, or concerns for the doctor (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')
            
            self.fields['patient'].queryset = User.objects.filter(role=patient_role)
            self.fields['doctor'].queryset = User.objects.filter(role=doctor_role)
            
        except Role.DoesNotExist as e:
            print(f"Error loading roles: {e}")
            self.fields['patient'].queryset = User.objects.none()
            self.fields['doctor'].queryset = User.objects.none()