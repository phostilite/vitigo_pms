# phototherapy_management/forms.py
from django import forms
from .models import PhototherapyProtocol, PhototherapyType, PhototherapyDevice, PhototherapyType, DeviceMaintenance, PhototherapyPlan, PatientRFIDCard, PhototherapySession
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ProtocolForm(forms.ModelForm):
    class Meta:
        model = PhototherapyProtocol
        fields = [
            'name',
            'phototherapy_type',
            'description',
            'initial_dose',
            'max_dose',
            'increment_percentage',
            'frequency_per_week',
            'duration_weeks',
            'contraindications',
            'safety_guidelines',
            'is_active'
        ]
        help_texts = {
            'name': 'A unique, descriptive name for the protocol',
            'phototherapy_type': 'Select the type of phototherapy this protocol is for',
            'description': 'Detailed description of the protocol and its intended use',
            'initial_dose': 'Starting dose in mJ/cm². Must be less than maximum dose',
            'max_dose': 'Maximum allowable dose in mJ/cm²',
            'increment_percentage': 'Percentage to increase dose each session (0-100)',
            'frequency_per_week': 'Number of sessions recommended per week',
            'duration_weeks': 'Total duration of the protocol in weeks',
            'contraindications': 'List any conditions where this protocol should not be used',
            'safety_guidelines': 'Important safety information and guidelines for this protocol',
            'is_active': 'Uncheck to disable this protocol'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'contraindications': forms.Textarea(attrs={'rows': 3}),
            'safety_guidelines': forms.Textarea(attrs={'rows': 3}),
            'initial_dose': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'max_dose': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'increment_percentage': forms.NumberInput(attrs={'min': '0', 'max': '100'}),
            'frequency_per_week': forms.NumberInput(attrs={'min': '1', 'max': '7'}),
            'duration_weeks': forms.NumberInput(attrs={'min': '1'})
        }

    def clean(self):
        cleaned_data = super().clean()
        initial_dose = cleaned_data.get('initial_dose')
        max_dose = cleaned_data.get('max_dose')

        if initial_dose and max_dose:
            if initial_dose > max_dose:
                raise forms.ValidationError("Initial dose cannot exceed maximum dose")

        return cleaned_data
    

class PhototherapyDeviceForm(forms.ModelForm):
    class Meta:
        model = PhototherapyDevice
        fields = [
            'name', 
            'model_number', 
            'serial_number',
            'phototherapy_type',
            'location',
            'installation_date',
            'last_maintenance_date',
            'next_maintenance_date',
            'maintenance_notes'
        ]
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'maintenance_notes': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'name': 'Name of the phototherapy device or unit',
            'model_number': 'Manufacturer model number of the device',
            'serial_number': 'Unique serial number of the device',
            'phototherapy_type': 'Type of phototherapy this device delivers',
            'location': 'Physical location of the device in the facility',
            'installation_date': 'Date when the device was installed',
            'last_maintenance_date': 'Date of the most recent maintenance',
            'next_maintenance_date': 'Scheduled date for next maintenance',
            'maintenance_notes': 'Any additional notes about device maintenance'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active phototherapy types
        self.fields['phototherapy_type'].queryset = PhototherapyType.objects.filter(is_active=True)
        
        # Add classes and placeholders
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            if field_name != 'maintenance_notes':  # Don't add required to optional field
                field.widget.attrs['required'] = 'required'


class ScheduleMaintenanceForm(forms.ModelForm):
    class Meta:
        model = DeviceMaintenance
        fields = [
            'device',
            'maintenance_type',
            'maintenance_date',
            'performed_by',
            'description',
            'cost',
            'next_maintenance_due',
            'parts_replaced',
            'notes'
        ]
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_due': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'parts_replaced': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active devices
        self.fields['device'].queryset = PhototherapyDevice.objects.filter(is_active=True)
        
        # Add classes and customize labels
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500'
            if field_name in ['device', 'maintenance_type', 'maintenance_date', 'performed_by']:
                field.widget.attrs['required'] = 'required'


class TreatmentPlanForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(role__name='PATIENT', is_active=True),
        empty_label="Select Patient",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the patient who will receive the phototherapy treatment"
    )
    
    protocol = forms.ModelChoiceField(
        queryset=PhototherapyProtocol.objects.filter(is_active=True),
        empty_label="Select Protocol",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Choose the treatment protocol to follow. This determines the treatment parameters"
    )
    
    rfid_card = forms.ModelChoiceField(
        queryset=PatientRFIDCard.objects.filter(is_active=True),
        required=False,
        empty_label="Select RFID Card (Optional)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Assign an RFID card for access control (required for Wholebody NB and Excimer treatments)"
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="When should the treatment plan begin? Select today or a future date"
    )

    total_sessions_planned = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Total number of sessions planned for this treatment course"
    )

    current_dose = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="Initial dose in mJ/cm². Must not exceed protocol maximum dose"
    )

    total_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Total cost of the treatment plan in INR"
    )

    special_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        help_text="Any special instructions or precautions for this patient's treatment"
    )

    reminder_frequency = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How often to send reminders (in days). Recommended: 1-3 days"
    )

    class Meta:
        model = PhototherapyPlan
        fields = [
            'patient', 'protocol', 'rfid_card', 'start_date', 
            'total_sessions_planned', 'current_dose', 'total_cost',
            'special_instructions', 'reminder_frequency'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholder text for text fields
        self.fields['special_instructions'].widget.attrs['placeholder'] = (
            "Enter any special instructions, precautions, or notes for this treatment plan"
        )

    def clean(self):
        cleaned_data = super().clean()
        protocol = cleaned_data.get('protocol')
        current_dose = cleaned_data.get('current_dose')
        start_date = cleaned_data.get('start_date')

        try:
            # Validate dose against protocol limits
            if protocol and current_dose:
                if current_dose > protocol.max_dose:
                    self.add_error('current_dose', 
                        f'Current dose ({current_dose}) cannot exceed protocol maximum dose ({protocol.max_dose})'
                    )
                if current_dose < protocol.initial_dose:
                    self.add_error('current_dose', 
                        f'Current dose ({current_dose}) cannot be less than protocol initial dose ({protocol.initial_dose})'
                    )

            # Validate RFID requirement for specific protocols
            if protocol and protocol.phototherapy_type.requires_rfid:
                rfid_card = cleaned_data.get('rfid_card')
                if not rfid_card:
                    self.add_error('rfid_card', 'RFID card is required for this type of phototherapy')

            # Validate start date
            if start_date:
                from django.utils import timezone
                if start_date < timezone.now().date():
                    self.add_error('start_date', 'Start date cannot be in the past')

        except Exception as e:
            logger.error(f"Error in form validation: {str(e)}")
            self.add_error(None, str(e))
        
        return cleaned_data
    

class ScheduleSessionForm(forms.ModelForm):
    class Meta:
        model = PhototherapySession
        fields = [
            'plan', 
            'scheduled_date', 
            'scheduled_time', 
            'device',
            'planned_dose'
        ]
        widgets = {
            'scheduled_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'placeholder': 'Select session date'
                }
            ),
            'scheduled_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'placeholder': 'Select session time'
                }
            ),
        }
        help_texts = {
            'plan': 'Select an active treatment plan. Only active plans are shown.',
            'scheduled_date': 'Choose a date within the treatment plan period. Cannot schedule beyond plan end date.',
            'scheduled_time': 'Select a time slot. Check device and staff availability.',
            'device': 'Select the phototherapy device to be used. Only active devices are shown.',
            'planned_dose': 'Enter the planned dose in mJ/cm². Must be within protocol limits.'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Filter active plans only
            self.fields['plan'].queryset = PhototherapyPlan.objects.filter(is_active=True)
            
            # Add Bootstrap classes and enhance help texts
            for field in self.fields:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200'
                })
            
            # Add detailed help text for each field
            self.fields['plan'].help_text += ' The selected plan determines available devices and dose ranges.'
            self.fields['scheduled_date'].help_text += ' Sessions must be scheduled at least 24 hours in advance.'
            self.fields['scheduled_time'].help_text += ' Consider patient preference and clinic hours.'
            self.fields['device'].help_text += ' Ensure device maintenance status and availability.'
            self.fields['planned_dose'].help_text += f' Recommended range: {self.get_dose_range()}'
            
        except Exception as e:
            logger.error(f"Error initializing ScheduleSessionForm: {str(e)}")

    def get_dose_range(self):
        """Get recommended dose range based on protocol defaults"""
        try:
            return "100-2000 mJ/cm² (varies by protocol)"
        except Exception as e:
            logger.error(f"Error getting dose range: {str(e)}")
            return "Contact administrator for recommended range"

    def clean(self):
        cleaned_data = super().clean()
        try:
            plan = cleaned_data.get('plan')
            scheduled_date = cleaned_data.get('scheduled_date')
            planned_dose = cleaned_data.get('planned_dose')

            if plan and scheduled_date:
                # Check if the plan is still active on the scheduled date
                if plan.end_date and scheduled_date > plan.end_date:
                    raise forms.ValidationError({
                        'scheduled_date': "Cannot schedule session after plan end date"
                    })

                # Check if there's already a session scheduled for this time
                if PhototherapySession.objects.filter(
                    plan=plan,
                    scheduled_date=scheduled_date,
                    scheduled_time=cleaned_data.get('scheduled_time')
                ).exists():
                    raise forms.ValidationError({
                        'scheduled_time': "A session is already scheduled for this time"
                    })

                # Validate dose against plan protocol
                if planned_dose:
                    protocol = plan.protocol
                    if planned_dose > protocol.max_dose:
                        raise forms.ValidationError({
                            'planned_dose': f"Dose exceeds maximum allowed ({protocol.max_dose} mJ/cm²)"
                        })
                    if planned_dose < protocol.initial_dose:
                        raise forms.ValidationError({
                            'planned_dose': f"Dose below minimum recommended ({protocol.initial_dose} mJ/cm²)"
                        })

        except Exception as e:
            logger.error(f"Error in form validation: {str(e)}")
            raise forms.ValidationError("An error occurred during validation")

        return cleaned_data