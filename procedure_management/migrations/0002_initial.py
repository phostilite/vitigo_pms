# Generated by Django 5.1.2 on 2025-01-14 14:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appointment_management', '0002_initial'),
        ('procedure_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='completedchecklistitem',
            name='completed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='completedchecklistitem',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='procedure_management.checklistitem'),
        ),
        migrations.AddField(
            model_name='procedure',
            name='appointment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='procedure', to='appointment_management.appointment'),
        ),
        migrations.AddField(
            model_name='procedure',
            name='assisting_staff',
            field=models.ManyToManyField(blank=True, related_name='assisted_procedures', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='procedure',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_procedures', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='procedure',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'role__name': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='procedures', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='procedure',
            name='primary_doctor',
            field=models.ForeignKey(limit_choices_to={'role__name': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='primary_procedures', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consentform',
            name='procedure',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='consent_form', to='procedure_management.procedure'),
        ),
        migrations.AddField(
            model_name='procedurechecklist',
            name='completed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='procedurechecklist',
            name='procedure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklists', to='procedure_management.procedure'),
        ),
        migrations.AddField(
            model_name='completedchecklistitem',
            name='checklist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completed_items', to='procedure_management.procedurechecklist'),
        ),
        migrations.AddField(
            model_name='procedurechecklist',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='procedure_management.procedurechecklisttemplate'),
        ),
        migrations.AddField(
            model_name='checklistitem',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='procedure_management.procedurechecklisttemplate'),
        ),
        migrations.AddField(
            model_name='proceduremedia',
            name='procedure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='procedure_management.procedure'),
        ),
        migrations.AddField(
            model_name='proceduremedia',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proceduretype',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='procedure_types', to='procedure_management.procedurecategory'),
        ),
        migrations.AddField(
            model_name='procedureprerequisite',
            name='procedure_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites', to='procedure_management.proceduretype'),
        ),
        migrations.AddField(
            model_name='procedureinstruction',
            name='procedure_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instructions', to='procedure_management.proceduretype'),
        ),
        migrations.AddField(
            model_name='procedurechecklisttemplate',
            name='procedure_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_templates', to='procedure_management.proceduretype'),
        ),
        migrations.AddField(
            model_name='procedure',
            name='procedure_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procedures', to='procedure_management.proceduretype'),
        ),
        migrations.AlterUniqueTogether(
            name='completedchecklistitem',
            unique_together={('checklist', 'item')},
        ),
        migrations.AlterUniqueTogether(
            name='procedurechecklist',
            unique_together={('procedure', 'template')},
        ),
        migrations.AlterUniqueTogether(
            name='proceduretype',
            unique_together={('category', 'name')},
        ),
        migrations.AddIndex(
            model_name='procedure',
            index=models.Index(fields=['scheduled_date', 'status'], name='procedure_m_schedul_e86818_idx'),
        ),
        migrations.AddIndex(
            model_name='procedure',
            index=models.Index(fields=['patient', 'status'], name='procedure_m_patient_376bd1_idx'),
        ),
        migrations.AddIndex(
            model_name='procedure',
            index=models.Index(fields=['primary_doctor', 'status'], name='procedure_m_primary_2a19b4_idx'),
        ),
    ]
