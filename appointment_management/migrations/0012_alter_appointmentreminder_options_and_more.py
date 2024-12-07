# Generated by Django 5.1.2 on 2024-11-30 07:46

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment_management', '0011_alter_appointment_time_slot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appointmentreminder',
            options={'ordering': ['reminder_date']},
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reminders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='failure_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='reminder_type',
            field=models.CharField(choices=[('SMS', 'SMS'), ('EMAIL', 'Email'), ('BOTH', 'Both SMS and Email')], default='BOTH', max_length=5),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('FAILED', 'Failed')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
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
