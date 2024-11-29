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
        logger.info("Received WhatsApp verification request")
        # Verification logic remains same
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token and mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        logger.warning(f"Invalid verification attempt with token: {token}")
        return HttpResponse('Invalid verification token', status=403)

    if request.method == 'POST':
        logger.info("Received WhatsApp webhook POST request")
        try:
            data = json.loads(request.body)
            logger.debug(f"Webhook payload: {data}")
            
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            message = value['messages'][0]
            message_id = message['id']
            
            # Check if message already processed
            if WhatsAppWebhook.objects.filter(message_id=message_id).exists():
                logger.warning(f"Duplicate message received: {message_id}")
                return HttpResponse('OK', status=200)
            
            phone_number = message['from']
            message_text = message['text']['body'].strip()
            
            logger.info(f"Processing message from {phone_number}: {message_text[:50]}...")
            
            # Get or create user
            user = get_or_create_user(phone_number)
            logger.debug(f"User retrieved/created: {user.id}")
            
            # Get latest state
            last_webhook = get_latest_state(phone_number)
            current_state = last_webhook.conversation_state if last_webhook else 'MENU'
            logger.debug(f"Current conversation state: {current_state}")
            
            # Create webhook record with initialized temp_data
            webhook = WhatsAppWebhook.objects.create(
                message_id=message['id'],
                from_number=phone_number,
                message_body=message_text,
                timestamp=timezone.now(),
                status='RECEIVED',
                user=user,
                conversation_state=current_state,
                temp_data={}  # Initialize empty dict
            )
            logger.info(f"Created webhook record: {webhook.id}")

            # Handle conversation states
            if message_text == '3':  # Exit
                logger.info(f"User {phone_number} exiting conversation")
                send_whatsapp_response(phone_number, "Thank you for using VitiGo Query Management. Goodbye!")
                webhook.conversation_state = 'MENU'
                webhook.save()
                return HttpResponse('OK', status=200)

            if current_state == 'MENU' or message_text == '0':
                logger.debug(f"Processing menu option: {message_text}")
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
                logger.debug(f"Processing subject input: {message_text[:50]}...")
                webhook.temp_data = {'subject': message_text}  # Create new dict
                webhook.conversation_state = 'AWAITING_DESCRIPTION'
                webhook.save()
                send_whatsapp_response(phone_number, "Please provide details for your query:")

            elif current_state == 'AWAITING_DESCRIPTION':
                logger.debug(f"Processing query description: {message_text[:50]}...")
                # Get last webhook with subject
                last_webhook = WhatsAppWebhook.objects.filter(
                    from_number=phone_number,
                    conversation_state='AWAITING_DESCRIPTION'
                ).exclude(id=webhook.id).last()
                
                if not last_webhook or 'subject' not in last_webhook.temp_data:
                    logger.error("Subject not found in conversation flow")
                    send_whatsapp_response(phone_number, "Sorry, there was an error. Please start over.\n\n" + MENU_TEXT)
                    webhook.conversation_state = 'MENU'
                    webhook.save()
                    return HttpResponse('OK', status=200)

                # Create new query
                query = Query.objects.create(
                    user=user,
                    subject=last_webhook.temp_data['subject'],
                    description=message_text,
                    source='WHATSAPP',
                    status='NEW',
                    contact_phone=phone_number
                )
                logger.info(f"Created new query: {query.query_id}")
                
                webhook.conversation_state = 'MENU'
                webhook.save()
                
                response = """
Your query has been submitted successfully! 
Our team will review it and get back to you.

Reply 0 for main menu, 3 to exit
"""
                send_whatsapp_response(phone_number, response)
            
            return HttpResponse('OK', status=200)
            
        except KeyError as e:
            logger.error(f"Invalid webhook payload structure: {str(e)}", exc_info=True)
            return HttpResponse('Invalid webhook payload', status=400)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {str(e)}", exc_info=True)
            return HttpResponse('Invalid JSON payload', status=400)
        except Exception as e:
            logger.error(f"Unexpected error processing webhook: {str(e)}", exc_info=True)
            return HttpResponse('Error processing webhook', status=500)