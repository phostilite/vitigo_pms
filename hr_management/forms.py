from django import forms
from django.contrib.auth import get_user_model
from .models import Employee, Department, Position

User = get_user_model()

class EmployeeCreationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        help_text="Legal first name as per documents"
    )
    last_name = forms.CharField(
        max_length=30,
        help_text="Legal last name as per documents"
    )
    email = forms.EmailField(
        help_text="Work email address"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Must be at least 8 characters long with numbers and special characters"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Re-enter the password to confirm"
    )

    class Meta:
        model = Employee
        fields = [
            'employee_id', 'department', 'position', 'reporting_to',
            'date_of_birth', 'emergency_contact_name', 'emergency_contact_number',
            'address', 'employment_status', 'employment_type', 'join_date',
            'current_salary', 'resume', 'contract_document'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'employee_id': 'Unique employee identifier',
            'department': 'Select the department where employee will work',
            'position': 'Job title or position',
            'reporting_to': 'Name of the reporting manager',
            'date_of_birth': 'Date of birth as per documents',
            'emergency_contact_name': 'Name of the emergency contact person',
            'emergency_contact_number': 'Phone number of the emergency contact person',
            'address': 'Residential address',
            'employment_status': 'Current employment status',
            'employment_type': 'Full-time, part-time, etc.',
            'join_date': 'Date of joining the company',
            'current_salary': 'Current salary of the employee',
            'resume': 'Accepted formats: PDF, DOC, DOCX (Max 5MB)',
            'contract_document': 'Accepted format: PDF only (Max 5MB)'
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data
