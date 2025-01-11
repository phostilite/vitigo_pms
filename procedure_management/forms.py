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
            'scheduled_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'scheduled_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'procedure_type': forms.Select(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'patient': forms.Select(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'primary_doctor': forms.Select(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'assisting_staff': forms.SelectMultiple(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
            'final_cost': forms.NumberInput(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                    'step': '0.01'
                }
            ),
            'payment_status': forms.Select(
                attrs={
                    'class': 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help texts
        self.fields['scheduled_date'].help_text = "Select the date for the procedure"
        self.fields['scheduled_time'].help_text = "Select the time for the procedure"
        self.fields['assisting_staff'].help_text = "Select one or more staff members to assist"
        
        # Make certain fields required
        self.fields['procedure_type'].required = True
        self.fields['patient'].required = True
        self.fields['primary_doctor'].required = True
        self.fields['scheduled_date'].required = True
        self.fields['scheduled_time'].required = True

        # Add labels
        self.fields['procedure_type'].label = "Type of Procedure"
        self.fields['primary_doctor'].label = "Primary Doctor"
        self.fields['assisting_staff'].label = "Assisting Staff Members"
        self.fields['final_cost'].label = "Procedure Cost"

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        procedure_type = cleaned_data.get('procedure_type')

        # Validate scheduled date is not in the past
        if scheduled_date:
            if scheduled_date < timezone.now().date():
                raise ValidationError({
                    'scheduled_date': "Procedure cannot be scheduled in the past"
                })

        # Validate procedure type is active
        if procedure_type and not procedure_type.is_active:
            raise ValidationError({
                'procedure_type': "Selected procedure type is not currently active"
            })

        # Validate if consent is required
        if procedure_type and procedure_type.requires_consent:
            if cleaned_data.get('status') == 'IN_PROGRESS':
                # Check if consent exists
                try:
                    if not hasattr(self.instance, 'consent_form') or \
                       not self.instance.consent_form.signed_by_patient:
                        raise ValidationError(
                            "Cannot start procedure without patient consent"
                        )
                except Exception as e:
                    raise ValidationError(
                        "Error verifying patient consent. Please check consent form."
                    )

        return cleaned_data

    def clean_final_cost(self):
        """Validate final cost is not less than procedure type base cost"""
        final_cost = self.cleaned_data.get('final_cost')
        procedure_type = self.cleaned_data.get('procedure_type')

        if final_cost and procedure_type and final_cost < procedure_type.base_cost:
            raise ValidationError(
                f"Final cost cannot be less than base cost ({procedure_type.base_cost})"
            )

        return final_cost

    def save(self, commit=True):
        procedure = super().save(commit=False)
        
        # Set base cost from procedure type if not set
        if not procedure.final_cost and procedure.procedure_type:
            procedure.final_cost = procedure.procedure_type.base_cost

        if commit:
            procedure.save()
            self.save_m2m()  # Save many-to-many relationships

        return procedure
