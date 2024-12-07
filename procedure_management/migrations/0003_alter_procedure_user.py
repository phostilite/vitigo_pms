# Generated by Django 5.1.2 on 2024-11-06 05:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procedure_management', '0002_remove_procedure_patient_procedure_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='procedure',
            name='user',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'PATIENT'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='procedures', to=settings.AUTH_USER_MODEL),
        ),
    ]
