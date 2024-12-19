from django import forms
from django.contrib.auth import get_user_model
from .models import Patient, MedicalHistory

User = get_user_model()

class PatientRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        help_text="Primary email address for account login and communications"
    )
    
    first_name = forms.CharField(
        help_text="Patient's legal first name"
    )
    
    last_name = forms.CharField(
        help_text="Patient's legal last name"
    )
    
    password1 = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput,
        help_text="Password must be at least 8 characters long and include numbers and special characters"
    )
    
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput,
        help_text="Enter the same password as above for verification"
    )
    
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        help_text="Select the patient's gender identity"
    )
    
    country_code = forms.CharField(
        help_text="Enter country code with + symbol (e.g., +1 for US)",
        initial="+91"
    )
    
    phone_number = forms.CharField(
        help_text="Enter a valid mobile number without country code"
    )
    
    profile_picture = forms.ImageField(
        required=False,
        help_text="Upload a clear, recent photo of the patient (optional)"
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Select the patient's date of birth from the calendar"
    )
    
    emergency_contact_name = forms.CharField(
        max_length=100,
        help_text="Name of person to contact in case of emergency"
    )
    
    emergency_contact_number = forms.CharField(
        max_length=15,
        help_text="Phone number of emergency contact person"
    )
    
    vitiligo_onset_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=False,
        help_text="Approximate date when vitiligo symptoms first appeared (if known)"
    )
    
    allergies = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'List any known allergies to medications, foods, or other substances'
        }),
        required=False,
        help_text="Include all known allergies, even if mild. Write 'None' if no known allergies"
    )
    
    chronic_conditions = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'List any ongoing medical conditions'
        }),
        required=False,
        help_text="Include all chronic medical conditions (e.g., diabetes, hypertension, thyroid disorders)"
    )
    
    past_surgeries = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'List any previous surgeries with dates if known'
        }),
        required=False,
        help_text="Include type of surgery and approximate date. Write 'None' if no previous surgeries"
    )
    
    family_history = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'List any relevant family medical history'
        }),
        required=False,
        help_text="Include any family history of vitiligo, autoimmune conditions, or other relevant medical conditions"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'gender', 'country_code', 
                 'phone_number', 'profile_picture']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        if commit:
            user.save()
            # Create Patient profile
            patient = Patient.objects.create(
                user=user,
                date_of_birth=self.cleaned_data['date_of_birth'],
                gender=self.cleaned_data['gender'],
                phone_number=self.cleaned_data['phone_number'],
                emergency_contact_name=self.cleaned_data['emergency_contact_name'],
                emergency_contact_number=self.cleaned_data['emergency_contact_number'],
                vitiligo_onset_date=self.cleaned_data['vitiligo_onset_date']
            )
            
            # Create Medical History
            MedicalHistory.objects.create(
                patient=patient,
                allergies=self.cleaned_data['allergies'],
                chronic_conditions=self.cleaned_data['chronic_conditions'],
                past_surgeries=self.cleaned_data['past_surgeries'],
                family_history=self.cleaned_data['family_history']
            )
        
        return user
