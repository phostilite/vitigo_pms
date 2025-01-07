# Generated by Django 5.1.2 on 2025-01-07 18:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('research_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisresult',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientstudyenrollment',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='study_enrollments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='researchdata',
            name='collected_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='researchdata',
            name='collection_point',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='research_management.datacollectionpoint'),
        ),
        migrations.AddField(
            model_name='researchdata',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='research_data', to='research_management.patientstudyenrollment'),
        ),
        migrations.AddField(
            model_name='researchstudy',
            name='principal_investigator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='led_studies', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publication',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publications', to='research_management.researchstudy'),
        ),
        migrations.AddField(
            model_name='patientstudyenrollment',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_enrollments', to='research_management.researchstudy'),
        ),
        migrations.AddField(
            model_name='datacollectionpoint',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_collection_points', to='research_management.researchstudy'),
        ),
        migrations.AddField(
            model_name='analysisresult',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analysis_results', to='research_management.researchstudy'),
        ),
        migrations.AddField(
            model_name='studyprotocol',
            name='study',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='protocol', to='research_management.researchstudy'),
        ),
    ]
