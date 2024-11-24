from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser
from access_control.models import Role

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]',
            'placeholder': 'you@example.com'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PATIENT'
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]',
            'placeholder': 'you@example.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[#cbd5e0] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1a365d]',
            'placeholder': '••••••••'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email address.")
        return email

class StaffUserCreationForm(UserCreationForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.exclude(name__in=['PATIENT']),
        empty_label="Select Role",
        required=True
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role', 'gender', 
                 'country_code', 'phone_number', 'is_staff', 'is_active')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_staff'].initial = True
        self.fields['is_active'].initial = True