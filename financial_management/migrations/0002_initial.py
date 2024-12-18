# Generated by Django 5.1.2 on 2024-12-18 18:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('financial_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='approved_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_expenses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='expense',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_expenses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='financialreport',
            name='generated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='financialreport',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='financial_management.financialyear'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoice',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='gst_rate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='financial_management.gstrate'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='financial_management.invoice'),
        ),
        migrations.AddField(
            model_name='payment',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='financial_management.invoice'),
        ),
        migrations.AddField(
            model_name='payment',
            name='received_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tdsentry',
            name='expense',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tds_entries', to='financial_management.expense'),
        ),
    ]
