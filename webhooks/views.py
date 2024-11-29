# webhooks/views.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from query_management.models import Query
import json
from .models import WhatsAppWebhook
from .utils import get_or_create_user, get_latest_state, get_user_queries, format_query_status, send_whatsapp_response, MENU_TEXT
from django.conf import settings
import logging

logger = logging.getLogger('query_management')

# webhooks/views.py
@csrf_exempt 
def whatsapp_webhook(request):
    if request.method == 'GET':
        # Verification logic remains same
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token and mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type='text/plain')
        return HttpResponse('Invalid verification token', status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            message = value['messages'][0]
            
            phone_number = message['from']
            message_text = message['text']['body'].strip()
            
            # Get or create user
            user = get_or_create_user(phone_number)
            
            # Get latest state
            last_webhook = get_latest_state(phone_number)
            current_state = last_webhook.conversation_state if last_webhook else 'MENU'
            
            # Create webhook record
            webhook = WhatsAppWebhook.objects.create(
                message_id=message['id'],
                from_number=phone_number,
                message_body=message_text,
                timestamp=timezone.now(),
                status='RECEIVED',
                user=user,
                conversation_state=current_state
            )

            # Handle conversation states
            if message_text == '3':  # Exit
                send_whatsapp_response(phone_number, "Thank you for using VitiGo Query Management. Goodbye!")
                webhook.conversation_state = 'MENU'
                webhook.save()
                return HttpResponse('OK', status=200)

            if current_state == 'MENU' or message_text == '0':
                if message_text == '1':
                    webhook.conversation_state = 'AWAITING_SUBJECT'
                    webhook.save()
                    send_whatsapp_response(phone_number, "Please enter the subject for your query:")
                
                elif message_text == '2':
                    queries = get_user_queries(phone_number)
                    if queries:
                        response = "Your recent queries:\n\n"
                        response += "\n".join(format_query_status(q) for q in queries)
                        response += "\n\nReply 0 for main menu, 3 to exit"
                    else:
                        response = "You have no queries yet.\n\nReply 0 for main menu, 3 to exit"
                    send_whatsapp_response(phone_number, response)
                
                else:
                    send_whatsapp_response(phone_number, MENU_TEXT)

            elif current_state == 'AWAITING_SUBJECT':
                webhook.temp_data['subject'] = message_text
                webhook.conversation_state = 'AWAITING_DESCRIPTION'
                webhook.save()
                send_whatsapp_response(phone_number, "Please provide details for your query:")

            elif current_state == 'AWAITING_DESCRIPTION':
                # Create new query
                Query.objects.create(
                    user=user,
                    subject=webhook.temp_data['subject'],
                    description=message_text,
                    source='WHATSAPP',
                    status='NEW',
                    contact_phone=phone_number
                )
                
                webhook.conversation_state = 'MENU'
                webhook.save()
                
                response = """
Your query has been submitted successfully! 
Our team will review it and get back to you.

Reply 0 for main menu, 3 to exit
"""
                send_whatsapp_response(phone_number, response)
            
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return HttpResponse('Error processing webhook', status=500)