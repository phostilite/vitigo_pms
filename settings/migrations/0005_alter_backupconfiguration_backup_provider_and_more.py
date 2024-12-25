# Generated by Django 5.1.2 on 2024-12-24 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0004_alter_systemconfiguration_allowed_file_extensions_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backupconfiguration',
            name='backup_provider',
            field=models.CharField(choices=[('LOCAL', 'Local Storage'), ('AWS_S3', 'Amazon S3'), ('GCS', 'Google Cloud Storage'), ('AZURE', 'Azure Blob Storage'), ('FTP', 'FTP Server'), ('SFTP', 'SFTP Server'), ('DROPBOX', 'Dropbox'), ('GDRIVE', 'Google Drive')], default='LOCAL', max_length=20),
        ),
        migrations.AlterField(
            model_name='cacheconfiguration',
            name='cache_type',
            field=models.CharField(choices=[('REDIS', 'Redis'), ('MEMCACHED', 'Memcached'), ('FILESYSTEM', 'File System Cache'), ('DATABASE', 'Database Cache'), ('DUMMY', 'Dummy Cache (Development)')], default='REDIS', max_length=20),
        ),
        migrations.AlterField(
            model_name='loggingconfiguration',
            name='log_level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Information'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=10),
        ),
    ]