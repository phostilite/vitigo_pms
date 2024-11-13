# Generated by Django 5.1.2 on 2024-11-11 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0003_customuser_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='country_code',
            field=models.CharField(blank=True, help_text='e.g. +91', max_length=5),
        ),
        migrations.AddField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]