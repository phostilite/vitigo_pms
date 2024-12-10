# Generated by Django 5.1.2 on 2024-12-10 06:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultation_management', '0002_initial'),
        ('pharmacy_management', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prescriptionitem',
            name='medication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy_management.medication'),
        ),
        migrations.AlterField(
            model_name='templateitem',
            name='medication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy_management.medication'),
        ),
    ]
