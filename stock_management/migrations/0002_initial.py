# Generated by Django 5.1.2 on 2025-01-15 07:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stock_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_purchase_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_purchase_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='purchase_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='stock_management.purchaseorder'),
        ),
        migrations.AddField(
            model_name='stockaudit',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stockitem',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='stock_management.itemcategory'),
        ),
        migrations.AddField(
            model_name='stockaudit',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock_management.stockitem'),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock_management.stockitem'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='stock_management.stockitem'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock_management.supplier'),
        ),
    ]
