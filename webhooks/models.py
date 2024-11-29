# webhooks/models.py
from django.db import models

class WhatsAppWebhook(models.Model):
    message_id = models.CharField(max_length=255, unique=True)
    from_number = models.CharField(max_length=20)
    message_body = models.TextField()
    timestamp = models.DateTimeField()
    media_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)