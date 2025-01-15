# Generated by Django 5.1.2 on 2025-01-15 07:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('doctor_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='doctoravailability',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='availability', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='associated_conditions',
            field=models.ManyToManyField(to='doctor_management.associatedconditionspecialization'),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='body_areas',
            field=models.ManyToManyField(to='doctor_management.bodyareaspecialization'),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='user',
            field=models.OneToOneField(limit_choices_to={'role__name': 'Doctor'}, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctorreview',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='doctor_management.doctorprofile'),
        ),
        migrations.AddField(
            model_name='doctorreview',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='specializations',
            field=models.ManyToManyField(to='doctor_management.specialization'),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='treatment_methods',
            field=models.ManyToManyField(to='doctor_management.treatmentmethodspecialization'),
        ),
        migrations.AlterUniqueTogether(
            name='doctoravailability',
            unique_together={('doctor', 'day_of_week', 'shift')},
        ),
        migrations.AlterUniqueTogether(
            name='doctorreview',
            unique_together={('doctor', 'patient')},
        ),
    ]
