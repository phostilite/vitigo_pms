# Generated by Django 5.1.2 on 2024-12-19 10:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy_management', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('adjustment_type', models.CharField(choices=[('ADD', 'Stock Addition'), ('REMOVE', 'Stock Removal'), ('CORRECTION', 'Stock Correction')], max_length=20)),
                ('quantity', models.IntegerField(help_text='Use positive number for additions, negative for removals')),
                ('reason', models.TextField()),
                ('adjusted_at', models.DateTimeField(auto_now_add=True)),
                ('reference_number', models.CharField(blank=True, help_text='External reference number if any', max_length=50)),
                ('adjusted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('medication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_adjustments', to='pharmacy_management.medication')),
            ],
        ),
    ]