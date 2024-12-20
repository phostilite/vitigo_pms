# Generated by Django 5.1.2 on 2024-12-18 18:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('settings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='credentialstore',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_credentials', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='credentialstore',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_credentials', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='emailconfiguration',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_email_configs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='emailconfiguration',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_email_configs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='setting',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_settings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='setting',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_settings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='settingcategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='settings.settingcategory'),
        ),
        migrations.AddField(
            model_name='settingdefinition',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setting_definitions', to='settings.settingcategory'),
        ),
        migrations.AddField(
            model_name='setting',
            name='definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='settings.settingdefinition'),
        ),
        migrations.AddField(
            model_name='socialmediacredential',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_social_credentials', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='socialmediacredential',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_social_credentials', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='credentialstore',
            index=models.Index(fields=['service', 'environment', 'is_active'], name='settings_cr_service_2e5016_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='credentialstore',
            unique_together={('service', 'environment', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='settingdefinition',
            unique_together={('category', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='setting',
            unique_together={('definition',)},
        ),
        migrations.AlterUniqueTogether(
            name='socialmediacredential',
            unique_together={('platform', 'environment')},
        ),
    ]
