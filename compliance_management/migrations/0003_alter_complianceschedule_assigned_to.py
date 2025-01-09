# Generated by Django 5.1.2 on 2025-01-09 06:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance_management', '0002_alter_complianceschedule_assigned_to'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='complianceschedule',
            name='assigned_to',
            field=models.ForeignKey(limit_choices_to=models.Q(('role__name', 'PATIENT'), _negated=True), on_delete=django.db.models.deletion.CASCADE, related_name='assigned_compliance_schedules', to=settings.AUTH_USER_MODEL),
        ),
    ]
