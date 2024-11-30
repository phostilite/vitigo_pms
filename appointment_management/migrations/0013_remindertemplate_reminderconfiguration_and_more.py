# Generated by Django 5.1.2 on 2024-11-30 07:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment_management', '0012_alter_appointmentreminder_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReminderTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('days_before', models.PositiveIntegerField(help_text='Days before appointment to send reminder')),
                ('hours_before', models.PositiveIntegerField(default=0, help_text='Hours before appointment to send reminder')),
                ('message_template', models.TextField(help_text='Use {patient}, {doctor}, {date}, {time}, {type} as placeholders')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['days_before', 'hours_before'],
            },
        ),
        migrations.CreateModel(
            name='ReminderConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_type', models.CharField(choices=[('CONSULTATION', 'Consultation'), ('FOLLOW_UP', 'Follow-up'), ('PROCEDURE', 'Procedure'), ('PHOTOTHERAPY', 'Phototherapy')], max_length=20, unique=True)),
                ('reminder_types', models.JSONField(default=dict, help_text='Configure email/SMS options for each template')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('templates', models.ManyToManyField(related_name='configurations', to='appointment_management.remindertemplate')),
            ],
        ),
        migrations.AddField(
            model_name='appointmentreminder',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointment_reminders', to='appointment_management.remindertemplate'),
        ),
        migrations.AddIndex(
            model_name='remindertemplate',
            index=models.Index(fields=['is_active', 'days_before'], name='appointment_is_acti_bd1d03_idx'),
        ),
    ]
