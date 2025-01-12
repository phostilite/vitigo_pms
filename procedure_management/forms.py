from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Procedure, ProcedureType, ConsentForm, ProcedureCategory, ProcedurePrerequisite

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

class ProcedureCategoryForm(forms.ModelForm):
    class Meta:
        model = ProcedureCategory
        fields = ['name', 'description', 'is_active']
        help_texts = {
            'name': 'Name of the procedure category',
            'description': 'Detailed description of the category',
            'is_active': 'Whether this category is currently active'
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
            'is_active': 'Active Status'
        }
        error_messages = {
            'name': {
                'required': 'Please enter a category name',
                'unique': 'A category with this name already exists'
            }
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError("Category name must be at least 3 characters long")
        return name

class ProcedureTypeForm(forms.ModelForm):
    class Meta:
        model = ProcedureType
        fields = [
            'category', 'name', 'code', 'description', 
            'duration_minutes', 'base_cost', 'priority',
            'requires_consent', 'requires_fasting',
            'recovery_time_minutes', 'risk_level', 'is_active'
        ]
        help_texts = {
            'category': 'Select the category this procedure type belongs to',
            'name': 'Name of the procedure type',
            'code': 'Unique code for identifying this procedure type',
            'description': 'Detailed description of the procedure type',
            'duration_minutes': 'Expected duration in minutes',
            'base_cost': 'Base cost for this procedure type',
            'priority': 'Priority level of this procedure type',
            'requires_consent': 'Whether this procedure requires patient consent',
            'requires_fasting': 'Whether this procedure requires fasting',
            'recovery_time_minutes': 'Expected recovery time in minutes',
            'risk_level': 'Risk level associated with this procedure type',
            'is_active': 'Whether this procedure type is currently active'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'base_cost': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'duration_minutes': forms.NumberInput(attrs={'min': '1'}),
            'recovery_time_minutes': forms.NumberInput(attrs={'min': '0'})
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) < 2:
            raise ValidationError("Code must be at least 2 characters long")
        return code.upper()

class ProcedurePrerequisiteForm(forms.ModelForm):
    class Meta:
        model = ProcedurePrerequisite
        fields = ['procedure_type', 'name', 'description', 'is_mandatory', 'order']
        help_texts = {
            'procedure_type': 'Select the procedure type this prerequisite belongs to',
            'name': 'Name of the prerequisite',
            'description': 'Detailed description of the prerequisite',
            'is_mandatory': 'Whether this prerequisite is mandatory',
            'order': 'Order in which this prerequisite should be displayed'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': '0'})
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError("Prerequisite name must be at least 3 characters long")
        return name