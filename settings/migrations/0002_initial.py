# Generated by Django 5.1.2 on 2025-01-14 14:03

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
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='settings.settingcategory'),
        ),
        migrations.AddField(
            model_name='setting',
            name='definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='settings.settingdefinition'),
        ),
        migrations.AddField(
            model_name='settinghistory',
            name='changed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='settinghistory',
            name='setting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='settings.setting'),
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
