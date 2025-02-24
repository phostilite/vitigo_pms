# Generated by Django 5.1.2 on 2025-01-15 07:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('telemedicine_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='teleconsultationfeedback',
            name='submitted_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='teleconsultationfile',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='teleconsultationsession',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teleconsultations_conducted', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='teleconsultationsession',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='teleconsultations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='teleconsultationprescription',
            name='teleconsultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='prescription', to='telemedicine_management.teleconsultationsession'),
        ),
        migrations.AddField(
            model_name='teleconsultationfile',
            name='teleconsultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='telemedicine_management.teleconsultationsession'),
        ),
        migrations.AddField(
            model_name='teleconsultationfeedback',
            name='teleconsultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='telemedicine_management.teleconsultationsession'),
        ),
        migrations.AddField(
            model_name='telemedicinevirtualwaitingroom',
            name='patient',
            field=models.OneToOneField(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='virtual_waiting_room', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='telemedicinevirtualwaitingroom',
            name='teleconsultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='waiting_room_entries', to='telemedicine_management.teleconsultationsession'),
        ),
    ]
