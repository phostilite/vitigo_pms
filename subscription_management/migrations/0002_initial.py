# Generated by Django 5.1.2 on 2024-12-12 07:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('subscription_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='featureusage',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_usage', to='subscription_management.subscription'),
        ),
        migrations.AddField(
            model_name='subscriptionaddonpurchase',
            name='add_on',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='subscription_management.subscriptionaddon'),
        ),
        migrations.AddField(
            model_name='subscriptionaddonpurchase',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='add_on_purchases', to='subscription_management.subscription'),
        ),
        migrations.AddField(
            model_name='subscriptioncommunication',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communications', to='subscription_management.subscription'),
        ),
        migrations.AddField(
            model_name='featureusage',
            name='feature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscription_management.subscriptionfeature'),
        ),
        migrations.AddField(
            model_name='subscriptionhistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_history', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subscriptionhistory',
            name='tier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='subscription_management.subscriptiontier'),
        ),
        migrations.AddField(
            model_name='subscriptionfeature',
            name='tiers',
            field=models.ManyToManyField(related_name='features', to='subscription_management.subscriptiontier'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='tier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='subscription_management.subscriptiontier'),
        ),
        migrations.AlterUniqueTogether(
            name='featureusage',
            unique_together={('subscription', 'feature')},
        ),
    ]
