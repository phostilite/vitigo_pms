# Generated by Django 5.1.2 on 2025-01-15 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('result_data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DataCollectionPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('target_date', models.DurationField(help_text='Time from enrollment date')),
            ],
        ),
        migrations.CreateModel(
            name='PatientStudyEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment_date', models.DateField()),
                ('status', models.CharField(choices=[('SCREENING', 'Screening'), ('ENROLLED', 'Enrolled'), ('COMPLETED', 'Completed'), ('WITHDRAWN', 'Withdrawn')], default='SCREENING', max_length=20)),
                ('withdrawal_reason', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('authors', models.TextField()),
                ('journal', models.CharField(max_length=255)),
                ('publication_date', models.DateField()),
                ('doi', models.CharField(blank=True, max_length=100, null=True)),
                ('url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ResearchData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collected_date', models.DateField()),
                ('data', models.JSONField()),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ResearchStudy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PLANNING', 'Planning'), ('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('SUSPENDED', 'Suspended'), ('TERMINATED', 'Terminated')], default='PLANNING', max_length=20)),
                ('ethics_approval_document', models.FileField(blank=True, null=True, upload_to='research_documents/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Research Studies',
            },
        ),
        migrations.CreateModel(
            name='StudyProtocol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=20)),
                ('document', models.FileField(upload_to='study_protocols/')),
                ('approved_date', models.DateField()),
            ],
        ),
    ]
