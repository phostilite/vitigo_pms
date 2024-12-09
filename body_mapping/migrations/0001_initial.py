# Generated by Django 5.1.2 on 2024-12-09 13:01

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BodyModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BodyView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('description', models.TextField(blank=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Gender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='BodyRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('parent_region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_regions', to='body_mapping.bodyregion')),
                ('applicable_views', models.ManyToManyField(to='body_mapping.bodyview')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BodyImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='body_images/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])),
                ('resolution', models.CharField(blank=True, max_length=20)),
                ('image_quality', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('body_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='body_mapping.bodymodel')),
                ('view', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='body_mapping.bodyview')),
            ],
            options={
                'unique_together': {('body_model', 'view')},
            },
        ),
        migrations.CreateModel(
            name='CoordinateGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('body_image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coordinate_groups', to='body_mapping.bodyimage')),
                ('body_region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coordinate_groups', to='body_mapping.bodyregion')),
            ],
            options={
                'unique_together': {('body_image', 'body_region')},
            },
        ),
        migrations.AddField(
            model_name='bodymodel',
            name='gender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='body_mapping.gender'),
        ),
        migrations.CreateModel(
            name='RegionMeasurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('value', models.FloatField()),
                ('unit', models.CharField(max_length=20)),
                ('measurement_type', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('coordinate_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurements', to='body_mapping.coordinategroup')),
            ],
        ),
        migrations.CreateModel(
            name='Coordinate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=50)),
                ('x_coordinate', models.FloatField()),
                ('y_coordinate', models.FloatField()),
                ('sequence', models.PositiveIntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('coordinate_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coordinates', to='body_mapping.coordinategroup')),
            ],
            options={
                'ordering': ['sequence'],
                'unique_together': {('coordinate_group', 'label')},
            },
        ),
    ]
