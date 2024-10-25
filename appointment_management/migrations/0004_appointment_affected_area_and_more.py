# Generated by Django 5.1.2 on 2024-10-23 14:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment_management', '0003_alter_appointment_status'),
        ('doctor_management', '0002_alter_doctoravailability_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='affected_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='doctor_management.bodyareaspecialization'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='treatment_method',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='doctor_management.treatmentmethodspecialization'),
        ),
    ]