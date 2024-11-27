from django import forms
from .models import Appointment, DoctorTimeSlot
from access_control.models import Role

class AppointmentCreateForm(forms.ModelForm):
    patient_id = forms.CharField(widget=forms.HiddenInput())
    doctor_id = forms.CharField(widget=forms.HiddenInput())
    time_slot_id = forms.CharField(widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Appointment
        fields = ['date', 'appointment_type', 'priority', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['appointment_type'].widget.attrs.update({'class': 'form-control'})
        self.fields['priority'].widget.attrs.update({'class': 'form-control'})
        self.fields['notes'].widget.attrs.update({'class': 'form-control', 'rows': 3})
