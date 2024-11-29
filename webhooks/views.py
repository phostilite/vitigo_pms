# webhooks/views.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from query_management.models import Query
import json
from .models import WhatsAppWebhook
from django.conf import settings
import logging

logger = logging.getLogger('query_management')

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        # Handle webhook verification from WhatsApp
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        # Verify token should match what you set in WhatsApp cloud API
        if mode and token and mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type='text/plain')
        return HttpResponse('Invalid verification token', status=403)

    if request.method == 'POST':
        # Handle incoming messages
        data = json.loads(request.body)
        
        try:
            # Extract message details
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            message = value['messages'][0]
            
            # Create WhatsApp webhook record
            webhook = WhatsAppWebhook.objects.create(
                message_id=message['id'],
                from_number=message['from'],
                message_body=message['text']['body'],
                timestamp=timezone.now(),
                status='RECEIVED'
            )
            
            # Create query from webhook
            Query.objects.create(
                subject=f"WhatsApp Query from {webhook.from_number}",
                description=webhook.message_body,
                source='WHATSAPP',
                status='NEW',
                priority='MEDIUM',
                contact_phone=webhook.from_number
            )
            
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            # Log error
            logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return HttpResponse('Error processing webhook', status=500)