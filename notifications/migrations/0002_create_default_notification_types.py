
from django.db import migrations

def create_notification_types(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    
    default_types = [
        {
            'name': 'QUERY_CREATED',
            'description': 'Notification for new query creation'
        },
        {
            'name': 'QUERY_ASSIGNED',
            'description': 'Notification for query assignment'
        },
        {
            'name': 'QUERY_STATUS_UPDATED',
            'description': 'Notification for query status updates'
        },
        {
            'name': 'QUERY_RESOLVED',
            'description': 'Notification for resolved queries'
        }
    ]
    
    for type_data in default_types:
        NotificationType.objects.get_or_create(**type_data)

def reverse_func(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    NotificationType.objects.filter(
        name__in=['QUERY_CREATED', 'QUERY_ASSIGNED', 'QUERY_STATUS_UPDATED', 'QUERY_RESOLVED']
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_notification_types, reverse_func),
    ]