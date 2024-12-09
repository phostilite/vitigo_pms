# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appointment_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_appointments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='appointment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='appointment_management.appointment'),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reminders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cancellationreason',
            name='appointment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cancellation_reason', to='appointment_management.appointment'),
        ),
        migrations.AddField(
            model_name='cancellationreason',
            name='cancelled_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctortimeslot',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='time_slots', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointment',
            name='time_slot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appointment_management.doctortimeslot'),
        ),
        migrations.AddField(
            model_name='remindertemplate',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reminderconfiguration',
            name='templates',
            field=models.ManyToManyField(related_name='configurations', to='appointment_management.remindertemplate'),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointment_reminders', to='appointment_management.remindertemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='doctortimeslot',
            unique_together={('doctor', 'date', 'start_time')},
        ),
        migrations.AddIndex(
            model_name='remindertemplate',
            index=models.Index(fields=['is_active', 'days_before'], name='appointment_is_acti_bd1d03_idx'),
        ),
        migrations.AddIndex(
            model_name='appointmentreminder',
            index=models.Index(fields=['reminder_date', 'status'], name='appointment_reminde_0ee43e_idx'),
        ),
        migrations.AddIndex(
            model_name='appointmentreminder',
            index=models.Index(fields=['appointment', 'status'], name='appointment_appoint_f576b7_idx'),
        ),
    ]
