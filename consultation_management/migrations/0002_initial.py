# Generated by Django 5.1.2 on 2024-12-18 18:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('consultation_management', '0001_initial'),
        ('pharmacy_management', '0001_initial'),
        ('phototherapy_management', '0001_initial'),
        ('stock_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='consultation',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_consultations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consultation',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_consultations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consultation',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='consultations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consultationattachment',
            name='consultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='consultationattachment',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consultationfeedback',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='consultationfeedback',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultation_feedbacks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consultationphototherapy',
            name='consultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phototherapy_sessions', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='consultationphototherapy',
            name='phototherapy_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consultations', to='phototherapy_management.phototherapysession'),
        ),
        migrations.AddField(
            model_name='doctorprivatenotes',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='private_notes', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='prescription',
            name='consultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='prescriptionitem',
            name='medication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy_management.medication'),
        ),
        migrations.AddField(
            model_name='prescriptionitem',
            name='prescription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='consultation_management.prescription'),
        ),
        migrations.AddField(
            model_name='prescriptionitem',
            name='stock_item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prescription_items', to='stock_management.stockitem'),
        ),
        migrations.AddField(
            model_name='prescriptiontemplate',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='prescription_templates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='prescription',
            name='template_used',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='consultation_management.prescriptiontemplate'),
        ),
        migrations.AddField(
            model_name='staffinstruction',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_instructions', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='templateitem',
            name='medication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy_management.medication'),
        ),
        migrations.AddField(
            model_name='templateitem',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='consultation_management.prescriptiontemplate'),
        ),
        migrations.AddField(
            model_name='treatmentplan',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='treatment_plan', to='consultation_management.consultation'),
        ),
        migrations.AddField(
            model_name='treatmentplanitem',
            name='treatment_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='consultation_management.treatmentplan'),
        ),
        migrations.AddIndex(
            model_name='consultation',
            index=models.Index(fields=['scheduled_datetime', 'status'], name='consultatio_schedul_269c0a_idx'),
        ),
        migrations.AddIndex(
            model_name='consultation',
            index=models.Index(fields=['patient', 'status'], name='consultatio_patient_74eb95_idx'),
        ),
        migrations.AddIndex(
            model_name='consultation',
            index=models.Index(fields=['doctor', 'status'], name='consultatio_doctor__5f7ba7_idx'),
        ),
        migrations.AddIndex(
            model_name='consultationfeedback',
            index=models.Index(fields=['consultation', 'rating'], name='consultatio_consult_b5a4a3_idx'),
        ),
        migrations.AddIndex(
            model_name='consultationfeedback',
            index=models.Index(fields=['created_at'], name='consultatio_created_550dbc_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='consultationphototherapy',
            unique_together={('consultation', 'phototherapy_session')},
        ),
    ]
