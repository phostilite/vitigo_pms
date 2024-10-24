# Generated by Django 5.1.2 on 2024-10-16 04:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patient_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='LabOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('ORDERED', 'Ordered'), ('COLLECTED', 'Sample Collected'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='ORDERED', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('ordered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ordered_lab_tests', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lab_orders', to='patient_management.patient')),
            ],
        ),
        migrations.CreateModel(
            name='LabOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('lab_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='lab_management.laborder')),
                ('lab_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lab_management.labtest')),
            ],
        ),
        migrations.CreateModel(
            name='LabReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_file', models.FileField(upload_to='lab_reports/')),
                ('upload_type', models.CharField(choices=[('MANUAL', 'Manual Upload'), ('AUTOMATIC', 'Automatic Upload')], max_length=20)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_sent_to_patient', models.BooleanField(default=False)),
                ('lab_order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='lab_management.laborder')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LabReportComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('lab_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='lab_management.labreport')),
            ],
        ),
        migrations.CreateModel(
            name='LabResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255)),
                ('unit', models.CharField(max_length=50)),
                ('reference_range', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('NORMAL', 'Normal'), ('ABNORMAL', 'Abnormal'), ('CRITICAL', 'Critical')], max_length=20)),
                ('performed_at', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('lab_order_item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='lab_management.laborderitem')),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='performed_lab_tests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
