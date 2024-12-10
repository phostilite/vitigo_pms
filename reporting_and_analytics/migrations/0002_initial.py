# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reporting_and_analytics', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='analyticslog',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dashboard',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_dashboards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dashboardwidget',
            name='dashboard',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='reporting_and_analytics.dashboard'),
        ),
        migrations.AddField(
            model_name='report',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dashboardwidget',
            name='data_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reporting_and_analytics.report'),
        ),
        migrations.AddField(
            model_name='reportexecution',
            name='executed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reportexecution',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='reporting_and_analytics.report'),
        ),
    ]