# Generated by Django 5.1.2 on 2024-12-03 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0002_customuser_psid'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='igsid',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]