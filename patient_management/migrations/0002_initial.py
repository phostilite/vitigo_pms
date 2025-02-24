# Generated by Django 5.1.2 on 2025-01-15 07:38

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
        migrations.AddField(
            model_name='medication',
            name='prescribed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prescribed_medications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patient',
            name='user',
            field=models.OneToOneField(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='medication',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medications', to='patient_management.patient'),
        ),
        migrations.AddField(
            model_name='medicalhistory',
            name='patient',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='medical_history', to='patient_management.patient'),
        ),
        migrations.AddField(
            model_name='treatmentplan',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='treatmentplan',
            name='medications',
            field=models.ManyToManyField(blank=True, to='patient_management.medication'),
        ),
        migrations.AddField(
            model_name='treatmentplan',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='treatment_plans', to='patient_management.patient'),
        ),
        migrations.AddField(
            model_name='vitiligoassessment',
            name='assessed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vitiligoassessment',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vitiligo_assessments', to='patient_management.patient'),
        ),
    ]
