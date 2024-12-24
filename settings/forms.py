# settings/forms.py

from django import forms
import json
import pytz
from .models import SettingCategory, SettingDefinition, Setting, SystemConfiguration

class SettingCategoryForm(forms.ModelForm):
    name = forms.CharField(
        help_text='Display name for the settings category'
    )
    key = forms.CharField(
        help_text='Unique identifier for the category (no spaces allowed)'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Detailed description of what this category encompasses'
    )
    icon = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'fa-cog'}),
        help_text='Font Awesome icon class (e.g., fa-cog, fa-user)'
    )
    order = forms.IntegerField(
        help_text='Display order of the category (lower numbers appear first)'
    )
    is_active = forms.BooleanField(
        required=False,
        help_text='Whether this category is currently active'
    )
    parent = forms.ModelChoiceField(
        queryset=SettingCategory.objects.all(),
        required=False,
        help_text='Parent category if this is a sub-category'
    )

    class Meta:
        model = SettingCategory
        fields = ['name', 'key', 'description', 'icon', 'order', 'is_active', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={'placeholder': 'fa-cog'}),
        }

    def clean_key(self):
        key = self.cleaned_data['key']
        if ' ' in key:
            raise forms.ValidationError("Key cannot contain spaces")
        return key.lower()

class SettingDefinitionForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=SettingCategory.objects.all(),
        help_text='The category this setting belongs to'
    )
    name = forms.CharField(
        help_text='Display name for the setting'
    )
    key = forms.CharField(
        help_text='Unique identifier for the setting (no spaces allowed)'
    )
    setting_type = forms.ChoiceField(
        choices=SettingDefinition.SETTING_TYPES,
        help_text='The type of value this setting will store'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Detailed description of what this setting controls'
    )
    default_value = forms.CharField(
        required=False,
        help_text='Default value for this setting'
    )
    is_required = forms.BooleanField(
        required=False,
        help_text='Whether this setting must have a value'
    )
    is_sensitive = forms.BooleanField(
        required=False,
        help_text='Whether this setting contains sensitive information'
    )
    validation_regex = forms.CharField(
        required=False,
        help_text='Regular expression pattern for validating the setting value'
    )
    validation_message = forms.CharField(
        required=False,
        help_text='Custom message to display when validation fails'
    )
    possible_values = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='JSON array of possible values (e.g., ["option1", "option2"])'
    )
    order = forms.IntegerField(
        help_text='Display order of the setting (lower numbers appear first)'
    )
    is_active = forms.BooleanField(
        required=False,
        help_text='Whether this setting definition is currently active'
    )

    class Meta:
        model = SettingDefinition
        fields = ['category', 'name', 'key', 'setting_type', 'description', 
                 'default_value', 'is_required', 'is_sensitive', 
                 'validation_regex', 'validation_message', 'possible_values', 
                 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'validation_message': forms.TextInput(),
            'possible_values': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_key(self):
        key = self.cleaned_data['key']
        if ' ' in key:
            raise forms.ValidationError("Key cannot contain spaces")
        return key.lower()

    def clean_possible_values(self):
        possible_values = self.cleaned_data.get('possible_values')
        if possible_values:
            try:
                return json.loads(possible_values)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format")
        return None

class SystemConfigurationForm(forms.ModelForm):
    site_name = forms.CharField(
        help_text='The name of your site that will be displayed to users'
    )
    site_url = forms.URLField(
        help_text='The main URL of your application (must start with http:// or https://)'
    )
    admin_email = forms.EmailField(
        help_text='Primary email address for system notifications and alerts'
    )
    session_timeout_minutes = forms.IntegerField(
        help_text='How long until an inactive user session expires (in minutes)'
    )
    password_expiry_days = forms.IntegerField(
        help_text='Number of days before users must change their password (0 for never)'
    )
    max_login_attempts = forms.IntegerField(
        help_text='Number of failed login attempts before account lockout'
    )
    require_2fa = forms.BooleanField(
        required=False,
        help_text='Require two-factor authentication for all users'
    )
    max_upload_size_mb = forms.IntegerField(
        help_text='Maximum file upload size allowed in megabytes'
    )
    allowed_file_extensions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='JSON array of allowed file extensions (e.g., [".pdf", ".jpg", ".png"])'
    )
    default_timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.common_timezones],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Default timezone for displaying dates and times'
    )
    default_language = forms.CharField(
        help_text='Default language code for the application (e.g., en-us, fr-fr)'
    )
    date_format = forms.CharField(
        help_text='Default date format (e.g., YYYY-MM-DD, DD/MM/YYYY)'
    )
    time_format = forms.CharField(
        help_text='Default time format (e.g., HH:mm:ss, hh:mm A)'
    )
    business_hours = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='JSON object defining business hours for each day (e.g., {"monday": {"start": "09:00", "end": "17:00"}})'
    )
    holiday_calendar = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='JSON array of holiday dates and descriptions'
    )
    appointment_duration_minutes = forms.IntegerField(
        help_text='Default duration for appointments in minutes'
    )

    class Meta:
        model = SystemConfiguration
        fields = ['site_name', 'site_url', 'admin_email', 'session_timeout_minutes',
                 'password_expiry_days', 'max_login_attempts', 'require_2fa',
                 'max_upload_size_mb', 'allowed_file_extensions', 'default_timezone',
                 'default_language', 'date_format', 'time_format', 'business_hours',
                 'holiday_calendar', 'appointment_duration_minutes']

    def clean_site_url(self):
        url = self.cleaned_data['site_url']
        if not url.startswith(('http://', 'https://')):
            raise forms.ValidationError("URL must start with http:// or https://")
        return url

    def clean_allowed_file_extensions(self):
        value = self.cleaned_data.get('allowed_file_extensions')
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format")
        return None

    def clean_business_hours(self):
        value = self.cleaned_data.get('business_hours')
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format")
        return None

    def clean_holiday_calendar(self):
        value = self.cleaned_data.get('holiday_calendar')
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format")
        return None

class SettingValueForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['value', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.definition:
            if self.instance.definition.setting_type == 'BOOLEAN':
                self.fields['value'] = forms.BooleanField(required=False)
            elif self.instance.definition.setting_type == 'NUMBER':
                self.fields['value'] = forms.FloatField()
            elif self.instance.definition.setting_type == 'JSON':
                self.fields['value'] = forms.JSONField()
            elif self.instance.definition.setting_type == 'EMAIL':
                self.fields['value'] = forms.EmailField()
            elif self.instance.definition.setting_type == 'URL':
                self.fields['value'] = forms.URLField()