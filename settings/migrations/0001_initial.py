# Generated by Django 5.1.2 on 2025-01-07 18:31

import django.core.validators
import encrypted_model_fields.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalyticsConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(choices=[('GOOGLE_ANALYTICS', 'Google Analytics'), ('MIXPANEL', 'Mixpanel'), ('CUSTOM', 'Custom Analytics')], max_length=50)),
                ('tracking_id', models.CharField(max_length=100)),
                ('api_key', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('additional_settings', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Analytics Configuration',
                'verbose_name_plural': 'Analytics Configurations',
            },
        ),
        migrations.CreateModel(
            name='APIConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('api_url', models.URLField()),
                ('version', models.CharField(max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('auth_type', models.CharField(choices=[('API_KEY', 'API Key'), ('OAUTH2', 'OAuth 2.0'), ('JWT', 'JWT'), ('BASIC', 'Basic Auth')], max_length=20)),
                ('api_key', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('client_id', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('client_secret', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('timeout_seconds', models.PositiveIntegerField(default=30)),
                ('retry_attempts', models.PositiveIntegerField(default=3)),
                ('rate_limit', models.JSONField(blank=True, default=dict)),
                ('custom_headers', models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='AuthenticationProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider_type', models.CharField(choices=[('OAUTH2', 'OAuth 2.0'), ('SAML', 'SAML'), ('LDAP', 'LDAP'), ('ACTIVE_DIRECTORY', 'Active Directory'), ('CUSTOM', 'Custom Provider')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('client_id', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('client_secret', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('authorization_url', models.URLField(blank=True)),
                ('token_url', models.URLField(blank=True)),
                ('userinfo_url', models.URLField(blank=True)),
                ('scope', models.CharField(blank=True, max_length=200)),
                ('additional_settings', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Authentication Provider',
                'verbose_name_plural': 'Authentication Providers',
            },
        ),
        migrations.CreateModel(
            name='BackupConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('backup_provider', models.CharField(choices=[('LOCAL', 'Local Storage'), ('AWS_S3', 'Amazon S3'), ('GCS', 'Google Cloud Storage'), ('AZURE', 'Azure Blob Storage'), ('FTP', 'FTP Server'), ('SFTP', 'SFTP Server'), ('DROPBOX', 'Dropbox'), ('GDRIVE', 'Google Drive')], default='LOCAL', max_length=20)),
                ('schedule', models.JSONField()),
                ('retention_policy', models.JSONField()),
                ('encryption_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CacheConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('cache_type', models.CharField(choices=[('REDIS', 'Redis'), ('MEMCACHED', 'Memcached'), ('FILESYSTEM', 'File System Cache'), ('DATABASE', 'Database Cache'), ('DUMMY', 'Dummy Cache (Development)')], default='REDIS', max_length=20)),
                ('host', models.CharField(max_length=200)),
                ('port', models.PositiveIntegerField()),
                ('password', encrypted_model_fields.fields.EncryptedCharField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CloudStorageProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider_type', models.CharField(choices=[('AWS_S3', 'Amazon S3'), ('GCS', 'Google Cloud Storage'), ('AZURE_BLOB', 'Azure Blob Storage'), ('DIGITAL_OCEAN', 'Digital Ocean Spaces'), ('CLOUDINARY', 'Cloudinary'), ('LOCAL', 'Local Storage')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('access_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('secret_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('bucket_name', models.CharField(max_length=100)),
                ('region', models.CharField(blank=True, max_length=50)),
                ('endpoint_url', models.URLField(blank=True)),
                ('base_url', models.URLField()),
                ('max_file_size', models.PositiveIntegerField()),
                ('allowed_file_types', models.JSONField(default=list)),
                ('custom_headers', models.JSONField(blank=True, default=dict)),
                ('cors_configuration', models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='EmailConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(choices=[('SMTP', 'SMTP'), ('AWS_SES', 'Amazon SES'), ('SENDGRID', 'SendGrid'), ('MAILGUN', 'Mailgun'), ('POSTMARK', 'Postmark'), ('CUSTOM', 'Custom SMTP')], max_length=50)),
                ('host', encrypted_model_fields.fields.EncryptedCharField()),
                ('port', models.IntegerField()),
                ('username', encrypted_model_fields.fields.EncryptedCharField()),
                ('password', encrypted_model_fields.fields.EncryptedCharField()),
                ('use_tls', models.BooleanField(default=True)),
                ('use_ssl', models.BooleanField(default=False)),
                ('from_email', models.EmailField(max_length=254)),
                ('from_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=False)),
                ('is_default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LoggingConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('log_level', models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Information'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=10)),
                ('log_file_path', models.CharField(max_length=255)),
                ('rotation_policy', models.JSONField()),
                ('retention_days', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='MonitoringConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(choices=[('PROMETHEUS', 'Prometheus'), ('GRAFANA', 'Grafana'), ('DATADOG', 'Datadog'), ('NEW_RELIC', 'New Relic'), ('CUSTOM', 'Custom Solution')], max_length=50)),
                ('api_key', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('endpoint_url', models.URLField(blank=True)),
                ('metrics_config', models.JSONField(default=dict)),
                ('alert_config', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Monitoring Configuration',
                'verbose_name_plural': 'Monitoring Configurations',
            },
        ),
        migrations.CreateModel(
            name='NotificationProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider_type', models.CharField(choices=[('FCM', 'Firebase Cloud Messaging'), ('APNS', 'Apple Push Notification Service'), ('ONESIGNAL', 'OneSignal'), ('CUSTOM', 'Custom Provider')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('api_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('app_id', models.CharField(blank=True, max_length=200)),
                ('team_id', models.CharField(blank=True, max_length=200)),
                ('environment', models.CharField(choices=[('development', 'Development'), ('production', 'Production')], default='development', max_length=20)),
                ('certificate_path', models.CharField(blank=True, max_length=255)),
                ('supports_rich_media', models.BooleanField(default=False)),
                ('max_payload_size', models.PositiveIntegerField(default=4096)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentGateway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('gateway_type', models.CharField(choices=[('RAZORPAY', 'Razorpay'), ('STRIPE', 'Stripe'), ('PAYPAL', 'PayPal'), ('PAYTM', 'Paytm'), ('PHONEPE', 'PhonePe'), ('UPI', 'UPI')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('api_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('api_secret', encrypted_model_fields.fields.EncryptedCharField()),
                ('merchant_id', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('environment', models.CharField(choices=[('sandbox', 'Sandbox'), ('production', 'Production')], default='sandbox', max_length=20)),
                ('webhook_secret', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('webhook_url', models.URLField(blank=True)),
                ('supported_currencies', models.JSONField(default=list)),
                ('transaction_fee_percentage', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('settlement_period_days', models.PositiveIntegerField(default=3)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password_policy', models.JSONField(default=dict, help_text='Password requirements and restrictions')),
                ('ip_whitelist', models.JSONField(default=list, help_text='List of allowed IP addresses')),
                ('max_session_duration', models.PositiveIntegerField(default=3600, help_text='Maximum session duration in seconds')),
                ('jwt_secret_key', encrypted_model_fields.fields.EncryptedCharField()),
                ('jwt_expiry_hours', models.PositiveIntegerField(default=24)),
                ('enable_rate_limiting', models.BooleanField(default=True)),
                ('rate_limit_config', models.JSONField(default=dict)),
                ('cors_allowed_origins', models.JSONField(default=list)),
                ('enable_audit_trail', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Security Configuration',
                'verbose_name_plural': 'Security Configurations',
            },
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(blank=True, null=True)),
                ('encrypted_value', encrypted_model_fields.fields.EncryptedTextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SettingCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('key', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Setting Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SettingDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('key', models.SlugField(max_length=100, unique=True)),
                ('setting_type', models.CharField(choices=[('STRING', 'Text String'), ('NUMBER', 'Number'), ('BOOLEAN', 'Boolean'), ('JSON', 'JSON Object'), ('EMAIL', 'Email Address'), ('URL', 'URL'), ('PASSWORD', 'Password'), ('FILE', 'File Path'), ('COLOR', 'Color Code'), ('DATETIME', 'Date and Time'), ('LIST', 'List of Values'), ('ENCRYPTED', 'Encrypted Value')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('default_value', models.TextField(blank=True, null=True)),
                ('is_required', models.BooleanField(default=False)),
                ('is_sensitive', models.BooleanField(default=False)),
                ('validation_regex', models.CharField(blank=True, max_length=500)),
                ('validation_message', models.CharField(blank=True, max_length=200)),
                ('possible_values', models.JSONField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['category', 'order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SettingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_value', models.TextField(blank=True, null=True)),
                ('new_value', models.TextField(blank=True, null=True)),
                ('change_type', models.CharField(choices=[('CREATE', 'Created'), ('UPDATE', 'Updated'), ('DELETE', 'Deleted'), ('SYNC', 'Synchronized'), ('BACKUP', 'Backed Up')], max_length=20)),
                ('change_reason', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Setting Histories',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SMSProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider_type', models.CharField(choices=[('TWILIO', 'Twilio'), ('MSG91', 'MSG91'), ('AWS_SNS', 'Amazon SNS'), ('KALEYRA', 'Kaleyra'), ('CUSTOM', 'Custom Provider')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('account_sid', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('auth_token', encrypted_model_fields.fields.EncryptedCharField()),
                ('sender_id', models.CharField(max_length=20)),
                ('api_endpoint', models.URLField(blank=True)),
                ('webhook_url', models.URLField(blank=True)),
                ('supports_unicode', models.BooleanField(default=True)),
                ('supports_delivery_reports', models.BooleanField(default=True)),
                ('max_message_length', models.PositiveIntegerField(default=160)),
                ('rate_limit', models.PositiveIntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SocialMediaCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('FACEBOOK', 'Facebook'), ('INSTAGRAM', 'Instagram'), ('WHATSAPP', 'WhatsApp'), ('TWITTER', 'Twitter'), ('LINKEDIN', 'LinkedIn'), ('YOUTUBE', 'YouTube')], max_length=20)),
                ('app_id', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('app_secret', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('access_token', encrypted_model_fields.fields.EncryptedTextField(blank=True)),
                ('refresh_token', encrypted_model_fields.fields.EncryptedTextField(blank=True)),
                ('webhook_secret', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('verify_token', encrypted_model_fields.fields.EncryptedCharField(blank=True)),
                ('business_account_id', models.CharField(blank=True, max_length=200)),
                ('phone_number_id', models.CharField(blank=True, max_length=200)),
                ('additional_settings', models.JSONField(blank=True, help_text='Platform-specific additional settings', null=True)),
                ('environment', models.CharField(choices=[('development', 'Development'), ('staging', 'Staging'), ('production', 'Production')], default='development', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SystemConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(max_length=100)),
                ('site_url', models.URLField()),
                ('admin_email', models.EmailField(max_length=254)),
                ('session_timeout_minutes', models.PositiveIntegerField(default=30)),
                ('password_expiry_days', models.PositiveIntegerField(default=90)),
                ('max_login_attempts', models.PositiveIntegerField(default=5)),
                ('require_2fa', models.BooleanField(default=False)),
                ('max_upload_size_mb', models.PositiveIntegerField(default=5)),
                ('allowed_file_extensions', models.JSONField(blank=True, default=list, help_text='Allowed file extensions for uploads', null=True)),
                ('default_timezone', models.CharField(default='UTC', max_length=50)),
                ('default_language', models.CharField(default='en-us', max_length=10)),
                ('date_format', models.CharField(default='YYYY-MM-DD', max_length=50)),
                ('time_format', models.CharField(default='HH:mm:ss', max_length=50)),
                ('business_hours', models.JSONField(blank=True, default=dict, help_text='Business hours configuration', null=True)),
                ('holiday_calendar', models.JSONField(blank=True, default=list, help_text='Holiday calendar configuration', null=True)),
                ('appointment_duration_minutes', models.PositiveIntegerField(default=30)),
            ],
            options={
                'verbose_name': 'System Configuration',
                'verbose_name_plural': 'System Configurations',
            },
        ),
    ]
