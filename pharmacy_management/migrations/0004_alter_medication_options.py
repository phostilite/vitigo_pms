# Generated by Django 5.1.2 on 2024-12-22 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy_management', '0003_stockadjustment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='medication',
            options={'ordering': ['name']},
        ),
    ]
