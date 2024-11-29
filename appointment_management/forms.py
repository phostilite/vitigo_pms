from django import forms
from django.db.models import Q
from .models import Appointment, DoctorTimeSlot
from user_management.models import CustomUser
from access_control.models import Role

class AppointmentCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patient_role = Role.objects.get(name='PATIENT')
        doctor_role = Role.objects.get(name='DOCTOR')
        
        self.fields['patient'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role=patient_role),
            empty_label="Select a Patient",
            widget=forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            })
        )
        
        self.fields['doctor'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role=doctor_role),
            empty_label="Select a Doctor",
            widget=forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            })
        )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_type', 'date', 'priority', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
            'appointment_type': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
            'priority': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
        }
