# Generated by Django 5.1.2 on 2025-01-14 14:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hr_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='assetassignment',
            name='assigned_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_assets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='department',
            name='head',
            field=models.ForeignKey(limit_choices_to={'is_active': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='headed_departments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='department',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subdepartments', to='hr_management.department'),
        ),
        migrations.AddField(
            model_name='document',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='hr_management.department'),
        ),
        migrations.AddField(
            model_name='employee',
            name='reporting_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subordinates', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='assetassignment',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_assets', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='employeeskill',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='grievance',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_grievances', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grievance',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grievances', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='leave',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_leaves', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='leave',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaves', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='notice',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_notices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payroll',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_records', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='payrollperiod',
            name='processed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_payrolls', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payroll',
            name='period',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payrolls', to='hr_management.payrollperiod'),
        ),
        migrations.AddField(
            model_name='performancereview',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_reviews', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='performancereview',
            name='reviewer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conducted_reviews', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='position',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='hr_management.department'),
        ),
        migrations.AddField(
            model_name='employee',
            name='position',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='hr_management.position'),
        ),
        migrations.AddField(
            model_name='trainingparticipant',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_participations', to='hr_management.employee'),
        ),
        migrations.AddField(
            model_name='trainingparticipant',
            name='training',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='hr_management.training'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['code'], name='hr_manageme_code_680934_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['employee', 'document_type'], name='hr_manageme_employe_7511bb_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['expiry_date'], name='hr_manageme_expiry__9e34a3_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['employee', 'date'], name='hr_manageme_employe_bf4a45_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['date', 'status'], name='hr_manageme_date_dd6905_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('employee', 'date')},
        ),
        migrations.AddIndex(
            model_name='assetassignment',
            index=models.Index(fields=['employee', 'asset_type'], name='hr_manageme_employe_70c758_idx'),
        ),
        migrations.AddIndex(
            model_name='assetassignment',
            index=models.Index(fields=['asset_id'], name='hr_manageme_asset_i_affb2b_idx'),
        ),
        migrations.AddIndex(
            model_name='employeeskill',
            index=models.Index(fields=['employee', 'is_primary'], name='hr_manageme_employe_cf6d39_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='employeeskill',
            unique_together={('employee', 'skill_name')},
        ),
        migrations.AddIndex(
            model_name='grievance',
            index=models.Index(fields=['employee', 'status'], name='hr_manageme_employe_e2c5eb_idx'),
        ),
        migrations.AddIndex(
            model_name='grievance',
            index=models.Index(fields=['priority', 'status'], name='hr_manageme_priorit_a2d7b9_idx'),
        ),
        migrations.AddIndex(
            model_name='leave',
            index=models.Index(fields=['employee', 'start_date'], name='hr_manageme_employe_8045bc_idx'),
        ),
        migrations.AddIndex(
            model_name='leave',
            index=models.Index(fields=['status'], name='hr_manageme_status_e7137c_idx'),
        ),
        migrations.AddIndex(
            model_name='notice',
            index=models.Index(fields=['priority'], name='hr_manageme_priorit_4c8ca3_idx'),
        ),
        migrations.AddIndex(
            model_name='notice',
            index=models.Index(fields=['created_at'], name='hr_manageme_created_45703b_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollperiod',
            index=models.Index(fields=['start_date', 'end_date'], name='hr_manageme_start_d_5c3029_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollperiod',
            index=models.Index(fields=['is_processed'], name='hr_manageme_is_proc_fb47a3_idx'),
        ),
        migrations.AddIndex(
            model_name='payroll',
            index=models.Index(fields=['employee', 'period'], name='hr_manageme_employe_20875b_idx'),
        ),
        migrations.AddIndex(
            model_name='payroll',
            index=models.Index(fields=['payment_status'], name='hr_manageme_payment_d03414_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='payroll',
            unique_together={('employee', 'period')},
        ),
        migrations.AddIndex(
            model_name='performancereview',
            index=models.Index(fields=['employee', 'review_date'], name='hr_manageme_employe_32ecf1_idx'),
        ),
        migrations.AddIndex(
            model_name='performancereview',
            index=models.Index(fields=['status'], name='hr_manageme_status_b64f4d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='position',
            unique_together={('title', 'department')},
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['employee_id'], name='hr_manageme_employe_bf5541_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['department', 'position'], name='hr_manageme_departm_60ac2f_idx'),
        ),
        migrations.AddIndex(
            model_name='trainingparticipant',
            index=models.Index(fields=['training', 'status'], name='hr_manageme_trainin_1cebc9_idx'),
        ),
        migrations.AddIndex(
            model_name='trainingparticipant',
            index=models.Index(fields=['employee', 'status'], name='hr_manageme_employe_baf8ec_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='trainingparticipant',
            unique_together={('training', 'employee')},
        ),
    ]
