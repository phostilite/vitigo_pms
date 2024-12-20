# Generated by Django 5.1.2 on 2024-12-18 18:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('time_in', models.TimeField()),
                ('time_out', models.TimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('HALF_DAY', 'Half Day'), ('LATE', 'Late')], max_length=20)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('department', models.CharField(max_length=100)),
                ('position', models.CharField(max_length=100)),
                ('date_of_joining', models.DateField()),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=10)),
                ('address', models.TextField()),
                ('phone_number', models.CharField(max_length=15)),
                ('emergency_contact_name', models.CharField(max_length=100)),
                ('emergency_contact_number', models.CharField(max_length=15)),
                ('bank_account_number', models.CharField(max_length=50)),
                ('bank_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('max_days_per_year', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PerformanceReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_date', models.DateField()),
                ('performance_score', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('strengths', models.TextField()),
                ('areas_for_improvement', models.TextField()),
                ('goals_for_next_period', models.TextField()),
                ('employee_comments', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Training',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('trainer', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('location', models.CharField(max_length=255)),
                ('max_participants', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TrainingAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('REGISTERED', 'Registered'), ('ATTENDED', 'Attended'), ('COMPLETED', 'Completed'), ('NO_SHOW', 'No Show')], max_length=20)),
                ('feedback', models.TextField(blank=True)),
            ],
        ),
    ]
