from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'name', 'asset_id', 'category', 'description', 
            'model_number', 'serial_number', 'manufacturer',
            'purchase_date', 'purchase_cost', 'warranty_expiry',
            'vendor', 'vendor_contact', 'status', 'condition',
            'location', 'specifications', 'power_rating',
            'dimensions', 'weight', 'user_manual', 'certificate',
            'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter asset name',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'asset_id': forms.TextInput(attrs={
                'placeholder': 'Enter unique asset ID',
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Detailed description of the asset'
            }),
            'model_number': forms.TextInput(attrs={
                'placeholder': 'Enter model number'
            }),
            'serial_number': forms.TextInput(attrs={
                'placeholder': 'Enter serial number'
            }),
            'manufacturer': forms.TextInput(attrs={
                'placeholder': 'Enter manufacturer name'
            }),
            'purchase_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'purchase_cost': forms.NumberInput(attrs={
                'placeholder': 'Enter purchase cost',
                'step': '0.01'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'type': 'date'
            }),
            'vendor': forms.TextInput(attrs={
                'placeholder': 'Enter vendor name'
            }),
            'vendor_contact': forms.TextInput(attrs={
                'placeholder': 'Enter vendor contact details'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Enter asset location'
            }),
            'specifications': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter technical specifications'
            }),
            'power_rating': forms.TextInput(attrs={
                'placeholder': 'e.g., 240V/50Hz, 1000W'
            }),
            'dimensions': forms.TextInput(attrs={
                'placeholder': 'e.g., 100cm x 50cm x 75cm'
            }),
            'weight': forms.TextInput(attrs={
                'placeholder': 'e.g., 25kg'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Additional notes or remarks'
            }),
        }
        help_texts = {
            'name': 'A clear, descriptive name for the asset',
            'asset_id': 'Unique identifier for the asset (alphanumeric)',
            'category': 'The type or category this asset belongs to',
            'description': 'Detailed description including key features and purpose',
            'model_number': 'Manufacturer\'s model number or product code',
            'serial_number': 'Unique serial number from manufacturer',
            'manufacturer': 'Name of the asset manufacturer',
            'purchase_date': 'Date when the asset was purchased',
            'purchase_cost': 'Original purchase cost in your currency',
            'warranty_expiry': 'Date when the warranty expires',
            'vendor': 'Name of the supplier or vendor',
            'vendor_contact': 'Contact information for the vendor',
            'status': 'Current operational status of the asset',
            'condition': 'Physical condition of the asset',
            'location': 'Current physical location of the asset',
            'specifications': 'Technical specifications in JSON format',
            'power_rating': 'Power consumption or rating details',
            'dimensions': 'Physical dimensions of the asset',
            'weight': 'Weight of the asset',
            'user_manual': 'Upload user manual (PDF only)',
            'certificate': 'Upload relevant certificates (PDF only)',
            'notes': 'Any additional notes or special instructions'
        }
        labels = {
            'asset_id': 'Asset ID',
            'specifications': 'Technical Specifications',
            'power_rating': 'Power Rating',
            'user_manual': 'User Manual (PDF)',
            'certificate': 'Certificates (PDF)',
        }

    def clean(self):
        cleaned_data = super().clean()
        warranty_expiry = cleaned_data.get('warranty_expiry')
        purchase_date = cleaned_data.get('purchase_date')

        if warranty_expiry and purchase_date and warranty_expiry < purchase_date:
            raise forms.ValidationError("Warranty expiry date cannot be earlier than purchase date")
        
        return cleaned_data
