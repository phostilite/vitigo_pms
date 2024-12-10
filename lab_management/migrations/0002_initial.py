# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lab_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='laborder',
            name='ordered_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ordered_lab_tests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='laborder',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='lab_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='laborderitem',
            name='lab_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='lab_management.laborder'),
        ),
        migrations.AddField(
            model_name='labreport',
            name='lab_order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='lab_management.laborder'),
        ),
        migrations.AddField(
            model_name='labreport',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labreportcomment',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labreportcomment',
            name='lab_report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='lab_management.labreport'),
        ),
        migrations.AddField(
            model_name='labresult',
            name='lab_order_item',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='lab_management.laborderitem'),
        ),
        migrations.AddField(
            model_name='labresult',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='performed_lab_tests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='laborderitem',
            name='lab_test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lab_management.labtest'),
        ),
    ]