# Generated by Django 5.1.2 on 2025-01-06 06:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phototherapy_management', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='phototherapypayment',
            name='installment_number',
            field=models.PositiveIntegerField(blank=True, help_text='Installment number if part of a payment plan', null=True),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='is_installment',
            field=models.BooleanField(default=False, help_text='Whether this payment is part of an installment plan'),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='payment_type',
            field=models.CharField(choices=[('FULL', 'Full Payment'), ('PER_SESSION', 'Per Session Payment'), ('PARTIAL', 'Partial Payment')], default='FULL', help_text='Whether this is a full payment or per-session payment', max_length=20),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='session',
            field=models.ForeignKey(blank=True, help_text='Associated session if this is a per-session payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='phototherapy_management.phototherapysession'),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='total_installments',
            field=models.PositiveIntegerField(blank=True, help_text='Total number of installments planned', null=True),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['session', 'payment_type'], name='phototherap_session_8bcc57_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['is_installment', 'installment_number'], name='phototherap_is_inst_401de3_idx'),
        ),
    ]
