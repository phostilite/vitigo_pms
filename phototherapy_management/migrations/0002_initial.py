# Generated by Django 5.1.2 on 2025-01-07 18:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('phototherapy_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='devicemaintenance',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_maintenance', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='homephototherapylog',
            name='reported_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientrfidcard',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapycenter',
            name='available_devices',
            field=models.ManyToManyField(blank=True, related_name='centers', to='phototherapy_management.phototherapydevice'),
        ),
        migrations.AddField(
            model_name='devicemaintenance',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_records', to='phototherapy_management.phototherapydevice'),
        ),
        migrations.AddField(
            model_name='phototherapypackage',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='recorded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_phototherapy_payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapyplan',
            name='center',
            field=models.ForeignKey(blank=True, help_text='Select the phototherapy center where treatment will be administered', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='treatment_plans', to='phototherapy_management.phototherapycenter'),
        ),
        migrations.AddField(
            model_name='phototherapyplan',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_phototherapy_plans', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapyplan',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='phototherapy_plans', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapyplan',
            name='rfid_card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='phototherapy_management.patientrfidcard'),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='phototherapy_management.phototherapyplan'),
        ),
        migrations.AddField(
            model_name='homephototherapylog',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_logs', to='phototherapy_management.phototherapyplan'),
        ),
        migrations.AddField(
            model_name='phototherapyprogress',
            name='assessed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='phototherapy_assessments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapyprogress',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_records', to='phototherapy_management.phototherapyplan'),
        ),
        migrations.AddField(
            model_name='phototherapyprotocol',
            name='created_by',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapyplan',
            name='protocol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='phototherapy_management.phototherapyprotocol'),
        ),
        migrations.AddField(
            model_name='phototherapyreminder',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='phototherapy_management.phototherapyplan'),
        ),
        migrations.AddField(
            model_name='phototherapysession',
            name='administered_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='administered_phototherapy_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='phototherapysession',
            name='device',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='phototherapy_management.phototherapydevice'),
        ),
        migrations.AddField(
            model_name='phototherapysession',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='phototherapy_management.phototherapyplan'),
        ),
        migrations.AddField(
            model_name='phototherapypayment',
            name='session',
            field=models.ForeignKey(blank=True, help_text='Associated session if this is a per-session payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='phototherapy_management.phototherapysession'),
        ),
        migrations.AddIndex(
            model_name='phototherapytype',
            index=models.Index(fields=['therapy_type', 'priority'], name='phototherap_therapy_3a5df5_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapytype',
            index=models.Index(fields=['is_active'], name='phototherap_is_acti_8d84f0_idx'),
        ),
        migrations.AddField(
            model_name='phototherapyprotocol',
            name='phototherapy_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='phototherapy_management.phototherapytype'),
        ),
        migrations.AddField(
            model_name='phototherapypackage',
            name='therapy_type',
            field=models.ForeignKey(blank=True, help_text='Optional: Specific therapy type this package is for', null=True, on_delete=django.db.models.deletion.SET_NULL, to='phototherapy_management.phototherapytype'),
        ),
        migrations.AddField(
            model_name='phototherapydevice',
            name='phototherapy_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='phototherapy_management.phototherapytype'),
        ),
        migrations.AddField(
            model_name='problemreport',
            name='reported_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_phototherapy_problems', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='problemreport',
            name='resolved_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_phototherapy_problems', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='problemreport',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_reports', to='phototherapy_management.phototherapysession'),
        ),
        migrations.AddIndex(
            model_name='patientrfidcard',
            index=models.Index(fields=['card_number'], name='phototherap_card_nu_f267bd_idx'),
        ),
        migrations.AddIndex(
            model_name='patientrfidcard',
            index=models.Index(fields=['is_active', 'expires_at'], name='phototherap_is_acti_771ad8_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapycenter',
            index=models.Index(fields=['is_active'], name='phototherap_is_acti_667398_idx'),
        ),
        migrations.AddIndex(
            model_name='devicemaintenance',
            index=models.Index(fields=['device', 'maintenance_date'], name='phototherap_device__7c2820_idx'),
        ),
        migrations.AddIndex(
            model_name='devicemaintenance',
            index=models.Index(fields=['maintenance_type'], name='phototherap_mainten_02c2d1_idx'),
        ),
        migrations.AddIndex(
            model_name='homephototherapylog',
            index=models.Index(fields=['plan', 'date'], name='phototherap_plan_id_0cfbaa_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyprogress',
            index=models.Index(fields=['plan', 'assessment_date'], name='phototherap_plan_id_f8c2c2_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyprogress',
            index=models.Index(fields=['response_level'], name='phototherap_respons_e57dfd_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyplan',
            index=models.Index(fields=['patient', 'is_active'], name='phototherap_patient_a5b07a_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyplan',
            index=models.Index(fields=['billing_status'], name='phototherap_billing_f8a3bb_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyreminder',
            index=models.Index(fields=['plan', 'reminder_type', 'status'], name='phototherap_plan_id_901213_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyreminder',
            index=models.Index(fields=['scheduled_datetime', 'status'], name='phototherap_schedul_792980_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapysession',
            index=models.Index(fields=['plan', 'status'], name='phototherap_plan_id_4e6901_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapysession',
            index=models.Index(fields=['scheduled_date', 'status'], name='phototherap_schedul_278159_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['plan', 'status'], name='phototherap_plan_id_bac588_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['receipt_number'], name='phototherap_receipt_387a1f_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['session', 'payment_type'], name='phototherap_session_8bcc57_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypayment',
            index=models.Index(fields=['is_installment', 'installment_number'], name='phototherap_is_inst_401de3_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapyprotocol',
            index=models.Index(fields=['phototherapy_type', 'is_active'], name='phototherap_phototh_aa44a1_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapypackage',
            index=models.Index(fields=['is_active', 'is_featured'], name='phototherap_is_acti_ebfd78_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapydevice',
            index=models.Index(fields=['serial_number'], name='phototherap_serial__d57783_idx'),
        ),
        migrations.AddIndex(
            model_name='phototherapydevice',
            index=models.Index(fields=['is_active'], name='phototherap_is_acti_387cee_idx'),
        ),
        migrations.AddIndex(
            model_name='problemreport',
            index=models.Index(fields=['session', 'resolved'], name='phototherap_session_92ad36_idx'),
        ),
        migrations.AddIndex(
            model_name='problemreport',
            index=models.Index(fields=['severity'], name='phototherap_severit_f822f6_idx'),
        ),
    ]
