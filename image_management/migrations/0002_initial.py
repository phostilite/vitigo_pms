# Generated by Django 5.1.2 on 2025-01-14 14:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('consultation_management', '0002_initial'),
        ('image_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='imageannotation',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='imagecomparison',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comparisonimage',
            name='comparison',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_management.imagecomparison'),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='body_part',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='image_management.bodypart'),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='consultation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='images', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='tagged_users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='tags',
            field=models.ManyToManyField(blank=True, to='image_management.imagetag'),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_images', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='imagecomparison',
            name='images',
            field=models.ManyToManyField(through='image_management.ComparisonImage', to='image_management.patientimage'),
        ),
        migrations.AddField(
            model_name='imageannotation',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='image_management.patientimage'),
        ),
        migrations.AddField(
            model_name='comparisonimage',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_management.patientimage'),
        ),
        migrations.AlterUniqueTogether(
            name='comparisonimage',
            unique_together={('comparison', 'image')},
        ),
    ]
