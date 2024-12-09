# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('query_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_queries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='query',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='queries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='queryattachment',
            name='query',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='query_management.query'),
        ),
        migrations.AddField(
            model_name='query',
            name='tags',
            field=models.ManyToManyField(blank=True, to='query_management.querytag'),
        ),
        migrations.AddField(
            model_name='queryupdate',
            name='query',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='query_management.query'),
        ),
        migrations.AddField(
            model_name='queryupdate',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
