# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Consultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consultation_type', models.CharField(choices=[('INITIAL', 'Initial Consultation'), ('FOLLOW_UP', 'Follow-up Consultation'), ('EMERGENCY', 'Emergency Consultation'), ('TELE', 'Tele-consultation')], default='INITIAL', max_length=20)),
                ('priority', models.CharField(choices=[('A', 'Blue A - High Priority'), ('B', 'Green B - Medium Priority'), ('C', 'Red C - Low Priority')], default='B', max_length=1)),
                ('scheduled_datetime', models.DateTimeField()),
                ('actual_start_time', models.DateTimeField(blank=True, null=True)),
                ('actual_end_time', models.DateTimeField(blank=True, null=True)),
                ('chief_complaint', models.TextField()),
                ('vitals', models.JSONField(blank=True, help_text='Store vital signs as JSON: BP, pulse, temperature, etc.', null=True)),
                ('symptoms', models.TextField(blank=True)),
                ('clinical_notes', models.TextField(blank=True)),
                ('diagnosis', models.TextField()),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('follow_up_notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('NO_SHOW', 'No Show')], default='SCHEDULED', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('duration_minutes', models.IntegerField(default=30)),
            ],
            options={
                'ordering': ['-scheduled_datetime'],
            },
        ),
        migrations.CreateModel(
            name='ConsultationAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='consultation_attachments/')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('file_type', models.CharField(default='unknown', max_length=50)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsultationPhototherapy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instructions', models.TextField()),
                ('schedule', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='DoctorPrivateNotes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clinical_observations', models.TextField(blank=True)),
                ('differential_diagnosis', models.TextField(blank=True)),
                ('treatment_rationale', models.TextField(blank=True)),
                ('private_remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'permissions': [('view_private_notes', "Can view doctor's private notes")],
            },
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PrescriptionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=100)),
                ('frequency', models.CharField(max_length=100)),
                ('duration', models.CharField(max_length=100)),
                ('quantity_prescribed', models.PositiveIntegerField()),
                ('instructions', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='PrescriptionTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_global', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='StaffInstruction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pre_consultation', models.TextField(blank=True, help_text='Instructions for staff before consultation')),
                ('during_consultation', models.TextField(blank=True, help_text='Instructions for staff during consultation')),
                ('post_consultation', models.TextField(blank=True, help_text='Instructions for staff after consultation')),
                ('priority', models.CharField(choices=[('A', 'Blue A - High Priority'), ('B', 'Green B - Medium Priority'), ('C', 'Red C - Low Priority')], default='B', max_length=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TemplateItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=100)),
                ('frequency', models.CharField(max_length=100)),
                ('duration', models.CharField(max_length=100)),
                ('instructions', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='TreatmentPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('duration_weeks', models.PositiveIntegerField()),
                ('goals', models.TextField()),
                ('lifestyle_modifications', models.TextField(blank=True)),
                ('dietary_recommendations', models.TextField(blank=True)),
                ('exercise_recommendations', models.TextField(blank=True)),
                ('expected_outcomes', models.TextField()),
                ('total_cost', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('payment_status', models.CharField(choices=[('PENDING', 'Payment Pending'), ('PARTIAL', 'Partially Paid'), ('COMPLETED', 'Payment Completed'), ('CANCELLED', 'Payment Cancelled')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TreatmentPlanItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
