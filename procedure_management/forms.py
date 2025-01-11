from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Procedure, ProcedureType

class ProcedureForm(forms.ModelForm):
    class Meta:
        model = Procedure
        fields = [
            'procedure_type',
            'patient',
            'appointment',
            'primary_doctor',
            'assisting_staff',
            'scheduled_date',
            'scheduled_time',
            'status',
            'notes',
            'final_cost',
            'payment_status'
        ]
        widgets = {
            'procedure_type': forms.Select(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select procedure type',
                }
            ),
            'patient': forms.Select(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select patient',
                }
            ),
            'appointment': forms.Select(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select associated appointment',
                }
            ),
            'primary_doctor': forms.Select(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select primary doctor',
                }
            ),
            'assisting_staff': forms.SelectMultiple(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select assisting staff members',
                }
            ),
            'scheduled_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD',
                }
            ),
            'scheduled_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                    'placeholder': 'HH:MM',
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'form-control',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Enter any additional notes or comments...',
                }
            ),
            'final_cost': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '0.00',
                    'step': '0.01',
                }
            ),
            'payment_status': forms.Select(
                attrs={
                    'class': 'form-control',
                }
            ),
        }
        help_texts = {
            'procedure_type': 'Select the type of medical procedure to be performed',
            'patient': 'Select the patient undergoing the procedure',
            'appointment': 'Link to the scheduled appointment (if applicable)',
            'primary_doctor': 'Doctor responsible for performing the procedure',
            'assisting_staff': 'Select any additional staff members assisting with the procedure',
            'scheduled_date': 'Date when the procedure is scheduled to take place',
            'scheduled_time': 'Time when the procedure is scheduled to begin',
            'status': 'Current status of the procedure',
            'notes': 'Any additional notes, special requirements, or comments about the procedure',
            'final_cost': 'Total cost of the procedure (including any additional charges)',
            'payment_status': 'Current status of payment for this procedure'
        }
        labels = {
            'procedure_type': 'Procedure Type',
            'patient': 'Patient Name',
            'appointment': 'Associated Appointment',
            'primary_doctor': 'Primary Doctor',
            'assisting_staff': 'Assisting Staff Members',
            'scheduled_date': 'Procedure Date',
            'scheduled_time': 'Procedure Time',
            'status': 'Procedure Status',
            'notes': 'Additional Notes',
            'final_cost': 'Procedure Cost',
            'payment_status': 'Payment Status'
        }
        error_messages = {
            'procedure_type': {
                'required': 'Please select a procedure type',
            },
            'patient': {
                'required': 'Please select a patient',
            },
            'primary_doctor': {
                'required': 'Please select a primary doctor',
            },
            'scheduled_date': {
                'required': 'Please select a date for the procedure',
            },
            'scheduled_time': {
                'required': 'Please specify the procedure time',
            },
            'final_cost': {
                'required': 'Please enter the procedure cost',
                'invalid': 'Please enter a valid amount',
                'min_value': 'Cost cannot be negative',
            },
        }