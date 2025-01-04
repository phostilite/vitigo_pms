from django import forms
from django.contrib.auth import get_user_model
from .models import Employee, Department, Position, Document, Notice
from django.utils import timezone

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

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head', 'parent']
        help_texts = {
            'name': 'Full name of the department',
            'code': 'Unique identifier code (3-5 characters)',
            'description': 'Detailed description of the department\'s role and responsibilities',
            'head': 'Employee who will lead this department',
            'parent': 'Parent department if this is a sub-department'
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            # Check if code exists (excluding current instance in case of update)
            exists = Department.objects.filter(code=code)
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise forms.ValidationError("This department code already exists")
        return code

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'title', 'description', 'file', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'document_type': 'Select the type of document you are uploading',
            'title': 'Enter a descriptive title for the document',
            'description': 'Provide any additional details about the document',
            'file': 'Upload document in PDF, JPG, JPEG, or PNG format (Max 5MB)',
            'expiry_date': 'Set expiry date if applicable (optional)'
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("File size must be no more than 5MB")
        return file

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'priority', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'content': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'title': 'Enter a clear and concise title for the notice',
            'content': 'Provide the complete notice content',
            'priority': 'Select the importance level of this notice',
            'expiry_date': 'Set an expiry date for the notice (optional)'
        }

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < timezone.now().date():
            raise forms.ValidationError("Expiry date cannot be in the past")
        return expiry_date
