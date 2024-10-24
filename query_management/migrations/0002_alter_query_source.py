# Generated by Django 5.1.2 on 2024-10-23 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='source',
            field=models.CharField(choices=[('WEBSITE', 'Website'), ('CHATBOT', 'Chatbot'), ('SOCIAL_MEDIA', 'Social Media'), ('PHONE', 'Phone Call'), ('IVR', 'Interactive Voice Response'), ('EMAIL', 'Email'), ('WALK_IN', 'Walk-in'), ('MOBILE_APP', 'Mobile App')], max_length=20),
        ),
    ]
