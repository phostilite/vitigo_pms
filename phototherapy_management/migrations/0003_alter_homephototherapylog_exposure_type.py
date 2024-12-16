# Generated by Django 5.1.2 on 2024-12-15 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phototherapy_management', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homephototherapylog',
            name='exposure_type',
            field=models.CharField(choices=[('UVB_DEVICE', 'UVB Device'), ('SUNLIGHT', 'Natural Sunlight'), ('COMBINATION', 'Combined Treatment')], default='UVB_DEVICE', max_length=20),
        ),
    ]