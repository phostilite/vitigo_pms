from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
import json
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

User = get_user_model()

class SettingCategory(models.Model):
    """Categories for organizing different types of settings"""
    name = models.CharField(max_length=100, unique=True)
    key = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Setting Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class SettingDefinition(models.Model):
    """Defines the structure and validation rules for settings"""
    SETTING_TYPES = [
        ('STRING', 'Text String'),
        ('NUMBER', 'Number'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON Object'),
        ('EMAIL', 'Email Address'),
        ('URL', 'URL'),
        ('PASSWORD', 'Password'),
        ('FILE', 'File Path'),
        ('COLOR', 'Color Code'),
        ('DATETIME', 'Date and Time'),
        ('LIST', 'List of Values'),
        ('ENCRYPTED', 'Encrypted Value'),
    ]

    category = models.ForeignKey(
        SettingCategory,
        on_delete=models.CASCADE,
        related_name='setting_definitions'
    )
    name = models.CharField(max_length=100)
    key = models.SlugField(max_length=100, unique=True)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES)
    description = models.TextField(blank=True)
    default_value = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Whether this setting contains sensitive information"
    )
    validation_regex = models.CharField(
        max_length=500,
        blank=True,
        help_text="Regular expression for validation"
    )
    validation_message = models.CharField(max_length=200, blank=True)
    possible_values = models.JSONField(
        null=True,
        blank=True,
        help_text="List of possible values for LIST type settings"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'name']
        unique_together = ['category', 'key']

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Setting(models.Model):
    """Stores the actual setting values"""
    definition = models.ForeignKey(
        SettingDefinition,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    value = models.TextField(blank=True, null=True)
    encrypted_value = EncryptedTextField(
        blank=True,
        null=True,
        help_text="Encrypted storage for sensitive values"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_settings'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_settings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['definition']

    def __str__(self):
        return f"{self.definition.name}: {self.get_masked_value()}"

    def clean(self):
        self.validate_value()

    def validate_value(self):
        """Validate the setting value based on its type and rules"""
        if not self.value and self.definition.is_required:
            raise ValidationError(f"{self.definition.name} is required")

        if self.value:
            setting_type = self.definition.setting_type
            try:
                if setting_type == 'NUMBER':
                    float(self.value)
                elif setting_type == 'BOOLEAN':
                    if self.value.lower() not in ['true', 'false', '1', '0']:
                        raise ValueError
                elif setting_type == 'JSON':
                    json.loads(self.value)
                elif setting_type == 'EMAIL':
                    if '@' not in self.value:
                        raise ValueError("Invalid email format")
                elif setting_type == 'URL':
                    URLValidator()(self.value)
                elif setting_type == 'LIST':
                    if self.definition.possible_values:
                        if self.value not in self.definition.possible_values:
                            raise ValueError("Value not in allowed list")
            except ValueError as e:
                raise ValidationError(f"Invalid value for {self.definition.name}: {str(e)}")

    def get_masked_value(self):
        """Return masked value for sensitive settings"""
        if self.definition.is_sensitive and self.value:
            return '*' * 8
        return self.value

class CredentialStore(models.Model):
    """Secure storage for various API credentials and secrets"""
    CREDENTIAL_TYPES = [
        ('API_KEY', 'API Key'),
        ('ACCESS_TOKEN', 'Access Token'),
        ('SECRET_KEY', 'Secret Key'),
        ('USERNAME', 'Username'),
        ('PASSWORD', 'Password'),
        ('CERTIFICATE', 'Certificate'),
        ('JWT', 'JWT Token'),
        ('OAUTH', 'OAuth Credentials'),
    ]

    name = models.CharField(max_length=100)
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPES)
    service = models.CharField(max_length=100, help_text="Service these credentials are for")
    environment = models.CharField(
        max_length=20,
        choices=[
            ('development', 'Development'),
            ('staging', 'Staging'),
            ('production', 'Production'),
        ],
        default='development'
    )
    key = models.CharField(max_length=100, help_text="Credential identifier")
    value = EncryptedTextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional configuration or metadata"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_credentials'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_credentials'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['service', 'environment', 'key']
        indexes = [
            models.Index(fields=['service', 'environment', 'is_active']),
        ]

    def __str__(self):
        return f"{self.service} - {self.name} ({self.environment})"

class EmailConfiguration(models.Model):
    """Email service provider configurations"""
    name = models.CharField(max_length=100)
    provider = models.CharField(
        max_length=50,
        choices=[
            ('SMTP', 'SMTP'),
            ('AWS_SES', 'Amazon SES'),
            ('SENDGRID', 'SendGrid'),
            ('MAILGUN', 'Mailgun'),
            ('POSTMARK', 'Postmark'),
            ('CUSTOM', 'Custom SMTP'),
        ]
    )
    host = EncryptedCharField(max_length=200)
    port = models.IntegerField()
    username = EncryptedCharField(max_length=200)
    password = EncryptedCharField(max_length=200)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_email_configs'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_email_configs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default configuration exists
            EmailConfiguration.objects.filter(
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)

class SocialMediaCredential(models.Model):
    """Credentials for various social media platforms"""
    PLATFORM_CHOICES = [
        ('FACEBOOK', 'Facebook'),
        ('INSTAGRAM', 'Instagram'),
        ('WHATSAPP', 'WhatsApp'),
        ('TWITTER', 'Twitter'),
        ('LINKEDIN', 'LinkedIn'),
        ('YOUTUBE', 'YouTube'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    app_id = EncryptedCharField(max_length=200, blank=True)
    app_secret = EncryptedCharField(max_length=200, blank=True)
    access_token = EncryptedTextField(blank=True)
    refresh_token = EncryptedTextField(blank=True)
    webhook_secret = EncryptedCharField(max_length=200, blank=True)
    verify_token = EncryptedCharField(max_length=200, blank=True)
    business_account_id = models.CharField(max_length=200, blank=True)
    phone_number_id = models.CharField(max_length=200, blank=True)
    additional_settings = models.JSONField(
        null=True,
        blank=True,
        help_text="Platform-specific additional settings"
    )
    environment = models.CharField(
        max_length=20,
        choices=[
            ('development', 'Development'),
            ('staging', 'Staging'),
            ('production', 'Production'),
        ],
        default='development'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_social_credentials'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_social_credentials'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['platform', 'environment']

    def __str__(self):
        return f"{self.platform} Credentials ({self.environment})"