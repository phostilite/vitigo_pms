from django import forms
from django.contrib.auth import get_user_model
from .models import ClinicVisit, VisitStatus

class NewVisitForm(forms.ModelForm):
    # Override the patient field to use Select2
    patient = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(role__name='PATIENT'),
        widget=forms.Select(attrs={
            'class': 'select2-patient-search block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'data-placeholder': 'Search patient by name...',
        })
    )

    class Meta:
        model = ClinicVisit
        fields = ['patient', 'priority', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'resize-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the initial "REGISTERED" status
        try:
            self.initial_status = VisitStatus.objects.get(name='REGISTERED')
        except VisitStatus.DoesNotExist:
            self.initial_status = None

        # Update patient queryset to be ordered by name and include full name
        self.fields['patient'].queryset = (
            self.fields['patient'].queryset
            .order_by('first_name', 'last_name')
        )
        
        # Override the label_from_instance method to display full name
        self.fields['patient'].label_from_instance = lambda obj: f"{obj.get_full_name()}"

        # Add Tailwind CSS classes for other fields
        self.fields['priority'].widget.attrs.update({
            'class': 'block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        })
        self.fields['notes'].widget.attrs.update({
            'class': 'block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 resize-none'
        })
