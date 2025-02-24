# Generated by Django 5.1.2 on 2025-01-15 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('query_id', models.AutoField(primary_key=True, serialize=False)),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('source', models.CharField(choices=[('WEBSITE', 'Website'), ('CHATBOT', 'Chatbot'), ('SOCIAL_MEDIA', 'Social Media'), ('PHONE', 'Phone Call'), ('IVR', 'Interactive Voice Response'), ('EMAIL', 'Email'), ('WALK_IN', 'Walk-in'), ('MOBILE_APP', 'Mobile App')], max_length=20)),
                ('priority', models.CharField(choices=[('A', 'High'), ('B', 'Medium'), ('C', 'Low')], default='B', max_length=1)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('IN_PROGRESS', 'In Progress'), ('WAITING', 'Waiting for Response'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], default='NEW', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('contact_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('query_type', models.CharField(blank=True, choices=[('GENERAL', 'General Inquiry'), ('APPOINTMENT', 'Appointment Related'), ('TREATMENT', 'Treatment Related'), ('BILLING', 'Billing Related'), ('COMPLAINT', 'Complaint'), ('FEEDBACK', 'Feedback'), ('OTHER', 'Other')], max_length=20, null=True)),
                ('expected_response_date', models.DateTimeField(blank=True, null=True)),
                ('follow_up_date', models.DateTimeField(blank=True, null=True)),
                ('is_patient', models.BooleanField(blank=True, null=True)),
                ('conversion_status', models.BooleanField(blank=True, help_text='Whether query led to appointment/conversion', null=True)),
                ('resolution_summary', models.TextField(blank=True, null=True)),
                ('response_time', models.DurationField(blank=True, null=True)),
                ('satisfaction_rating', models.IntegerField(blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], null=True)),
            ],
            options={
                'verbose_name': 'Query',
                'verbose_name_plural': 'Queries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QueryAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='query_attachments/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='QueryTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='QueryUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportExport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('export_file', models.FileField(blank=True, null=True, upload_to='report_exports/')),
                ('error_message', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
