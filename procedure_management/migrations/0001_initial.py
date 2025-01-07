# Generated by Django 5.1.2 on 2025-01-07 18:31

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=500)),
                ('is_mandatory', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['template', 'order'],
            },
        ),
        migrations.CreateModel(
            name='CompletedChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsentForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signed_by_patient', models.BooleanField(default=False)),
                ('patient_signature', models.ImageField(blank=True, null=True, upload_to='procedure_consents/signatures/')),
                ('signed_datetime', models.DateTimeField(blank=True, null=True)),
                ('witness_name', models.CharField(blank=True, max_length=100)),
                ('witness_signature', models.ImageField(blank=True, null=True, upload_to='procedure_consents/signatures/')),
                ('scanned_document', models.FileField(blank=True, null=True, upload_to='procedure_consents/documents/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Procedure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_date', models.DateField()),
                ('scheduled_time', models.TimeField()),
                ('actual_start_time', models.DateTimeField(blank=True, null=True)),
                ('actual_end_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('CONSENT_PENDING', 'Consent Pending'), ('READY', 'Ready to Start'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='SCHEDULED', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('complications', models.TextField(blank=True)),
                ('outcome', models.TextField(blank=True)),
                ('final_cost', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('payment_status', models.CharField(choices=[('PENDING', 'Payment Pending'), ('PARTIAL', 'Partially Paid'), ('COMPLETED', 'Payment Completed'), ('REFUNDED', 'Refunded')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-scheduled_date', '-scheduled_time'],
            },
        ),
        migrations.CreateModel(
            name='ProcedureCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Procedure Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProcedureChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProcedureChecklistTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProcedureInstruction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruction_type', models.CharField(choices=[('PRE', 'Pre-procedure'), ('POST', 'Post-procedure')], max_length=4)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['procedure_type', 'instruction_type', 'order'],
            },
        ),
        migrations.CreateModel(
            name='ProcedureMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('file_type', models.CharField(choices=[('IMAGE', 'Image'), ('VIDEO', 'Video'), ('DOCUMENT', 'Document'), ('OTHER', 'Other')], max_length=20)),
                ('file', models.FileField(upload_to='procedure_media/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'mp4', 'mov'])])),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_private', models.BooleanField(default=True, help_text='Whether the file is for internal use only')),
            ],
            options={
                'verbose_name_plural': 'Procedure Media',
            },
        ),
        migrations.CreateModel(
            name='ProcedurePrerequisite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('is_mandatory', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['procedure_type', 'order'],
            },
        ),
        migrations.CreateModel(
            name='ProcedureType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField()),
                ('duration_minutes', models.PositiveIntegerField()),
                ('base_cost', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('priority', models.CharField(choices=[('A', 'Blue A - High Priority'), ('B', 'Green B - Medium Priority'), ('C', 'Red C - Low Priority')], default='B', max_length=1)),
                ('requires_consent', models.BooleanField(default=True)),
                ('requires_fasting', models.BooleanField(default=False)),
                ('recovery_time_minutes', models.PositiveIntegerField()),
                ('risk_level', models.CharField(choices=[('LOW', 'Low Risk'), ('MODERATE', 'Moderate Risk'), ('HIGH', 'High Risk')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['category', 'name'],
            },
        ),
    ]
