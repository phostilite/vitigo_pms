from django import forms
from .models import Appointment, DoctorTimeSlot, ReminderTemplate, ReminderConfiguration
from django.contrib.auth import get_user_model
from access_control.models import Role
from django.utils import timezone
from datetime import datetime

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
        fields = ['patient', 'doctor', 'center', 'appointment_type', 'date', 'priority', 'notes', 'timeslot_id']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'center': forms.Select(attrs={'class': 'form-select'}),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
        help_texts = {
            'patient': 'Select the patient who needs the appointment',
            'doctor': 'Select the doctor you want to consult with',
            'center': 'Select the medical center where the appointment will take place',
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

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        timeslot_id = cleaned_data.get('timeslot_id')
        center = cleaned_data.get('center')

        if date and timeslot_id and center:
            try:
                time_slot = DoctorTimeSlot.objects.get(id=timeslot_id)
                current_datetime = timezone.now()
                
                # Create datetime object for the appointment
                appointment_datetime = timezone.make_aware(
                    datetime.combine(date, time_slot.start_time)
                )

                # Check if appointment datetime is in the past
                if appointment_datetime < current_datetime:
                    raise forms.ValidationError(
                        "Cannot create appointments for past time slots."
                    )

                # Check if time slot matches the selected date
                if time_slot.date != date:
                    raise forms.ValidationError(
                        "Selected time slot does not match the appointment date."
                    )

                # Check if time slot is still available
                if not time_slot.is_available:
                    raise forms.ValidationError(
                        "This time slot is no longer available."
                    )

                # Check if time slot belongs to selected center
                if time_slot.center != center:
                    raise forms.ValidationError(
                        "Selected time slot is not available at this center."
                    )

            except DoctorTimeSlot.DoesNotExist:
                raise forms.ValidationError(
                    "Invalid time slot selected."
                )

        return cleaned_data

class ReminderTemplateForm(forms.ModelForm):
    class Meta:
        model = ReminderTemplate
        fields = ['name', 'days_before', 'hours_before', 'message_template', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input rounded-lg w-full'}),
            'days_before': forms.NumberInput(attrs={'class': 'form-input rounded-lg w-full', 'min': '0'}),
            'hours_before': forms.NumberInput(attrs={'class': 'form-input rounded-lg w-full', 'min': '0'}),
            'message_template': forms.Textarea(attrs={'class': 'form-textarea rounded-lg w-full', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox rounded'}),
        }

class ReminderConfigurationForm(forms.ModelForm):
    class Meta:
        model = ReminderConfiguration
        fields = ['appointment_type', 'templates', 'reminder_types', 'is_active']
        widgets = {
            'appointment_type': forms.Select(attrs={'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
            'templates': forms.CheckboxSelectMultiple(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['templates'].queryset = ReminderTemplate.objects.filter(is_active=True)