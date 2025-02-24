# Generated by Django 5.1.2 on 2025-01-15 07:38

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_type', models.CharField(choices=[('LAPTOP', 'Laptop'), ('DESKTOP', 'Desktop'), ('MOBILE', 'Mobile Device'), ('ACCESS_CARD', 'Access Card'), ('UNIFORM', 'Uniform'), ('OTHER', 'Other Equipment')], max_length=20)),
                ('asset_id', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('assigned_date', models.DateField()),
                ('return_due_date', models.DateField(blank=True, null=True)),
                ('returned_date', models.DateField(blank=True, null=True)),
                ('condition_on_assignment', models.TextField()),
                ('condition_on_return', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('check_in', models.DateTimeField()),
                ('check_out', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('HALF_DAY', 'Half Day'), ('LATE', 'Late'), ('LEAVE', 'Leave')], default='PRESENT', max_length=20)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('IDENTIFICATION', 'Identification Documents'), ('EDUCATIONAL', 'Educational Certificates'), ('PROFESSIONAL', 'Professional Certificates'), ('MEDICAL', 'Medical Records'), ('CONTRACT', 'Employment Contracts'), ('OTHER', 'Other Documents')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='employee_documents/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('date_of_birth', models.DateField()),
                ('emergency_contact_name', models.CharField(max_length=100)),
                ('emergency_contact_number', models.CharField(max_length=20)),
                ('address', models.TextField()),
                ('employment_status', models.CharField(choices=[('FULL_TIME', 'Full Time'), ('PART_TIME', 'Part Time'), ('CONTRACT', 'Contract'), ('INTERN', 'Intern'), ('PROBATION', 'Probation')], max_length=20)),
                ('employment_type', models.CharField(choices=[('PERMANENT', 'Permanent'), ('TEMPORARY', 'Temporary'), ('SEASONAL', 'Seasonal')], max_length=20)),
                ('join_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('current_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('resume', models.FileField(blank=True, null=True, upload_to='employee_documents/resumes/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])),
                ('contract_document', models.FileField(blank=True, null=True, upload_to='employee_documents/contracts/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skill_name', models.CharField(max_length=100)),
                ('proficiency_level', models.PositiveIntegerField(help_text='1-5 scale where 5 is expert level', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('years_of_experience', models.DecimalField(decimal_places=1, max_digits=4, validators=[django.core.validators.MinValueValidator(0)])),
                ('is_primary', models.BooleanField(default=False)),
                ('certified', models.BooleanField(default=False)),
                ('certification_details', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Grievance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('HIGH', 'High Priority'), ('MEDIUM', 'Medium Priority'), ('LOW', 'Low Priority')], default='MEDIUM', max_length=10)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], default='OPEN', max_length=20)),
                ('filed_date', models.DateTimeField(auto_now_add=True)),
                ('resolution', models.TextField(blank=True)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('is_confidential', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(choices=[('ANNUAL', 'Annual Leave'), ('SICK', 'Sick Leave'), ('MATERNITY', 'Maternity Leave'), ('PATERNITY', 'Paternity Leave'), ('UNPAID', 'Unpaid Leave'), ('OTHER', 'Other')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(choices=[('ANNUAL', 'Annual Leave'), ('SICK', 'Sick Leave'), ('MATERNITY', 'Maternity Leave'), ('PATERNITY', 'Paternity Leave'), ('UNPAID', 'Unpaid Leave'), ('OTHER', 'Other')], max_length=20, unique=True)),
                ('annual_allowance', models.PositiveIntegerField(help_text='Number of days allowed per year')),
                ('carry_forward_limit', models.PositiveIntegerField(default=0, help_text='Maximum days that can be carried forward to next year')),
                ('min_service_days', models.PositiveIntegerField(default=0, help_text='Minimum service days required before leave type becomes available')),
                ('requires_approval', models.BooleanField(default=True)),
                ('requires_documentation', models.BooleanField(default=False)),
                ('documentation_info', models.TextField(blank=True, help_text='Information about required documentation')),
                ('notice_period_days', models.PositiveIntegerField(default=0, help_text='Minimum notice period required in days')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Leave Settings',
                'ordering': ['leave_type'],
            },
        ),
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('priority', models.CharField(choices=[('HIGH', 'High Priority'), ('MEDIUM', 'Medium Priority'), ('LOW', 'Low Priority')], default='MEDIUM', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payroll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basic_salary', models.DecimalField(decimal_places=2, max_digits=10)),
                ('allowances', models.JSONField(default=dict)),
                ('deductions', models.JSONField(default=dict)),
                ('net_salary', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_status', models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSED', 'Processed'), ('PAID', 'Paid'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PayrollPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='PerformanceReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_date', models.DateField()),
                ('review_period_start', models.DateField()),
                ('review_period_end', models.DateField()),
                ('technical_skills', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('communication', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('teamwork', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('productivity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('reliability', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('achievements', models.TextField()),
                ('areas_for_improvement', models.TextField()),
                ('goals', models.TextField()),
                ('overall_comments', models.TextField()),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('COMPLETED', 'Completed'), ('ACKNOWLEDGED', 'Acknowledged')], default='DRAFT', max_length=20)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('requirements', models.TextField()),
                ('responsibilities', models.TextField()),
                ('min_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('max_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['department', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Training',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('trainer', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('location', models.CharField(max_length=200)),
                ('max_participants', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('PLANNED', 'Planned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PLANNED', max_length=20)),
                ('materials', models.FileField(blank=True, null=True, upload_to='training_materials/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx'])])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TrainingParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ENROLLED', 'Enrolled'), ('COMPLETED', 'Completed'), ('DROPPED', 'Dropped'), ('FAILED', 'Failed')], default='ENROLLED', max_length=20)),
                ('enrollment_date', models.DateField(auto_now_add=True)),
                ('completion_date', models.DateField(blank=True, null=True)),
                ('attendance', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('feedback', models.TextField(blank=True)),
            ],
        ),
    ]
