# Generated by Django 5.1.2 on 2025-01-15 07:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mobile_app_backend', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileappointmentrequest',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='mobile_appointment_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mobiledevicetoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mobile_tokens', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mobilenotification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mobile_notifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientquery',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='mobile_queries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientqueryresponse',
            name='query',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='mobile_app_backend.patientquery'),
        ),
        migrations.AddField(
            model_name='patientqueryresponse',
            name='responder',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
