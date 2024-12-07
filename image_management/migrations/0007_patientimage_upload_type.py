# Generated by Django 5.1.2 on 2024-12-04 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_management', '0006_imagecomparison_comparison_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientimage',
            name='upload_type',
            field=models.CharField(choices=[('PROGRESS', 'Progress Update'), ('PROBLEM', 'Problem Report')], default='PROGRESS', max_length=10),
        ),
    ]
