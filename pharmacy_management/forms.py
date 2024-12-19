from django import forms
from .models import Medication, MedicationStock

class MedicationForm(forms.ModelForm):
    initial_stock = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
        help_text="Enter the initial quantity of medication to be added to inventory"
    )
    reorder_level = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'}),
        help_text="Minimum stock level at which reorder notification will be triggered"
    )

    class Meta:
        model = Medication
        fields = ['name', 'generic_name', 'description', 'dosage_form', 'strength',
                 'manufacturer', 'price', 'requires_prescription']
        help_texts = {
            'name': 'Brand or commercial name of the medication',
            'generic_name': 'Scientific or generic name of the medication',
            'description': 'Brief description of the medication and its uses',
            'dosage_form': 'Form of medication (e.g., tablet, capsule, syrup, injection)',
            'strength': 'Medication strength (e.g., 500mg, 10ml)',
            'manufacturer': 'Company that manufactures this medication',
            'price': 'Retail price per unit in ₹',
            'requires_prescription': 'Check if this medication requires a prescription for dispensing',
        }