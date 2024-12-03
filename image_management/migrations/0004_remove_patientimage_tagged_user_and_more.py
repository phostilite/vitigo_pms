# Generated by Django 5.1.2 on 2024-12-01 03:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultation_management', '0003_alter_consultation_patient'),
        ('image_management', '0003_patientimage_consultation_patientimage_tagged_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientimage',
            name='tagged_user',
        ),
        migrations.RemoveField(
            model_name='patientimage',
            name='upload_type',
        ),
        migrations.AlterField(
            model_name='patientimage',
            name='consultation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='consultation_management.consultation'),
        ),
    ]