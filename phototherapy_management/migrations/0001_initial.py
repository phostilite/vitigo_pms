# Generated by Django 5.1.2 on 2024-10-16 04:47

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patient_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PhototherapyProtocol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('initial_dose', models.FloatField(help_text='Initial dose in mJ/cm²')),
                ('max_dose', models.FloatField(help_text='Maximum dose in mJ/cm²')),
                ('increment_percentage', models.FloatField(help_text='Percentage to increase dose each session', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('frequency', models.CharField(help_text="e.g., '3 times per week'", max_length=50)),
                ('duration_weeks', models.PositiveIntegerField(help_text='Recommended duration in weeks')),
            ],
        ),
        migrations.CreateModel(
            name='PhototherapyType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='PhototherapyPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('current_dose', models.FloatField(help_text='Current dose in mJ/cm²')),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phototherapy_plans', to='patient_management.patient')),
                ('protocol', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='phototherapy_management.phototherapyprotocol')),
            ],
        ),
        migrations.CreateModel(
            name='HomePhototherapyLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('duration', models.PositiveIntegerField(help_text='Duration of session in seconds')),
                ('notes', models.TextField(blank=True)),
                ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_logs', to='phototherapy_management.phototherapyplan')),
            ],
        ),
        migrations.CreateModel(
            name='PhototherapySession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_date', models.DateField()),
                ('actual_dose', models.FloatField(help_text='Actual dose administered in mJ/cm²')),
                ('duration', models.PositiveIntegerField(help_text='Duration of session in seconds')),
                ('compliance', models.CharField(choices=[('COMPLETED', 'Completed'), ('MISSED', 'Missed'), ('RESCHEDULED', 'Rescheduled')], max_length=20)),
                ('side_effects', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('administered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='phototherapy_management.phototherapyplan')),
            ],
        ),
        migrations.AddField(
            model_name='phototherapyprotocol',
            name='phototherapy_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='phototherapy_management.phototherapytype'),
        ),
        migrations.CreateModel(
            name='PhototherapyDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
                ('serial_number', models.CharField(max_length=100, unique=True)),
                ('location', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('last_maintenance_date', models.DateField(blank=True, null=True)),
                ('next_maintenance_date', models.DateField(blank=True, null=True)),
                ('phototherapy_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='phototherapy_management.phototherapytype')),
            ],
        ),
    ]
