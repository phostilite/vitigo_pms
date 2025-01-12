from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Procedure, ProcedureType, ConsentForm

class ProcedureForm(forms.ModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    scheduled_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

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

class ConsentFormForm(forms.ModelForm):
    class Meta:
        model = ConsentForm
        fields = ['procedure', 'witness_name', 'notes', 'scanned_document']
        help_texts = {
            'procedure': 'Select the procedure this consent form is for',
            'witness_name': 'Name of the witness present during consent',
            'notes': 'Any additional notes or comments about the consent',
            'scanned_document': 'Upload the scanned consent document (PDF, JPG, PNG)',
        }
        labels = {
            'procedure': 'Procedure',
            'witness_name': 'Witness Name',
            'notes': 'Additional Notes',
            'scanned_document': 'Scanned Document',
        }
        error_messages = {
            'procedure': {
                'required': 'Please select a procedure',
            },
            'scanned_document': {
                'invalid': 'Please upload a valid document file (PDF, JPG, PNG)',
            },
        }

    def clean_scanned_document(self):
        document = self.cleaned_data.get('scanned_document')
        if document:
            # Add file size validation (e.g., max 5MB)
            if document.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be no more than 5MB")
        return document