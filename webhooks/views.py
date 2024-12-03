# webhooks/views.py

# Python standard library
import json
import logging

# Django imports
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Local application imports
from query_management.models import Query
from .models import WhatsAppWebhook, FacebookMessengerWebhook, InstagramWebhook
from .utils import (
    
    #
    get_or_create_user_whatsapp,
    get_latest_state,
    get_queries_whatsapp,
    send_whatsapp_response,
    
    # 
    get_or_create_user_messenger,
    get_messenger_latest_state,
    get_queries_messenger,
    send_messenger_response,
    send_messenger_media,

    #
    get_or_create_user_instagram,
    get_instagram_latest_state,
    get_queries_instagram,
    send_instagram_response,
    send_instagram_media,
    
    format_query_status,

    # Constants
    MENU_TEXT,
    MESSENGER_MENU_TEXT,
    INSTAGRAM_MENU_TEXT
)

# Logger configuration
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
            user = get_or_create_user_whatsapp(phone_number)
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
                    queries = get_queries_whatsapp(phone_number)
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

@csrf_exempt
def messenger_webhook(request):
    if request.method == 'GET':
        logger.info("Received Messenger verification request")
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token and mode == 'subscribe' and token == settings.FACEBOOK_VERIFY_TOKEN:
            logger.info("Messenger webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        logger.warning(f"Invalid Messenger verification attempt with token: {token}")
        return HttpResponse('Invalid verification token', status=403)

    if request.method == 'POST':
        logger.info("Received Messenger webhook POST request")
        try:
            data = json.loads(request.body)
            logger.debug(f"Messenger webhook payload: {data}")
            
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    sender_psid = messaging_event['sender']['id']
                    
                    if 'message' in messaging_event:
                        message_text = messaging_event['message'].get('text', '')
                        message_id = messaging_event['message']['mid']
                        
                        # Check for duplicate message
                        if FacebookMessengerWebhook.objects.filter(message_id=message_id).exists():
                            logger.warning(f"Duplicate Messenger message received: {message_id}")
                            continue
                        
                        # Get or create user
                        user = get_or_create_user_messenger(sender_psid)
                        
                        # Get latest state
                        last_webhook = get_messenger_latest_state(sender_psid)
                        current_state = last_webhook.conversation_state if last_webhook else 'MENU'
                        
                        # Create webhook record
                        webhook = FacebookMessengerWebhook.objects.create(
                            psid=sender_psid,
                            message_id=message_id,
                            message_body=message_text,
                            timestamp=timezone.now(),
                            status='RECEIVED',
                            user=user,
                            conversation_state=current_state
                        )

                        # Handle conversation states
                        if message_text == '3':  # Exit
                            send_messenger_response(sender_psid, "Thank you for using VitiGo Query Management. Goodbye!")
                            webhook.conversation_state = 'MENU'
                            webhook.save()
                            continue

                        if current_state == 'MENU' or message_text == '0':
                            if message_text == '1':
                                webhook.conversation_state = 'AWAITING_SUBJECT'
                                webhook.save()
                                send_messenger_response(sender_psid, "Please enter the subject for your query:")
                            
                            elif message_text == '2':
                                queries = get_queries_messenger(sender_psid)
                                if queries:
                                    response = "Your recent queries:\n\n"
                                    response += "\n".join(format_query_status(q) for q in queries)
                                    response += "\n\nType 0 for main menu, 3 to exit"
                                else:
                                    response = "You have no queries yet.\n\nType 0 for main menu, 3 to exit"
                                send_messenger_response(sender_psid, response)
                            
                            else:
                                send_messenger_response(sender_psid, MESSENGER_MENU_TEXT)

                        elif current_state == 'AWAITING_SUBJECT':
                            webhook.temp_data = {'subject': message_text}
                            webhook.conversation_state = 'AWAITING_DESCRIPTION'
                            webhook.save()
                            send_messenger_response(sender_psid, "Please provide details for your query:")

                        elif current_state == 'AWAITING_DESCRIPTION':
                            last_webhook = FacebookMessengerWebhook.objects.filter(
                                psid=sender_psid,
                                conversation_state='AWAITING_DESCRIPTION'
                            ).exclude(id=webhook.id).last()

                            if not last_webhook or 'subject' not in last_webhook.temp_data:
                                send_messenger_response(sender_psid, "Sorry, there was an error. Please start over.\n\n" + MESSENGER_MENU_TEXT)
                                webhook.conversation_state = 'MENU'
                                webhook.save()
                                continue

                            # Create new query
                            query = Query.objects.create(
                                user=user,
                                subject=last_webhook.temp_data['subject'],
                                description=message_text,
                                source='MESSENGER',
                                status='NEW'
                            )
                            
                            webhook.conversation_state = 'MENU'
                            webhook.save()
                            
                            response = """
Your query has been submitted successfully! 
Our team will review it and get back to you.

Type 0 for main menu, 3 to exit
"""
                            send_messenger_response(sender_psid, response)
            
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            logger.error(f"Error processing Messenger webhook: {str(e)}", exc_info=True)
            return HttpResponse('Error processing webhook', status=500)
        

@csrf_exempt
def instagram_webhook(request):
    if request.method == 'GET':
        logger.info("Received Instagram verification request")
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token and mode == 'subscribe' and token == settings.INSTAGRAM_VERIFY_TOKEN:
            logger.info("Instagram webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        logger.warning(f"Invalid Instagram verification attempt with token: {token}")
        return HttpResponse('Invalid verification token', status=403)

    if request.method == 'POST':
        logger.info("Received Instagram webhook POST request")
        try:
            data = json.loads(request.body)
            logger.debug(f"Instagram webhook payload: {data}")
            
            for entry in data['entry']:
                for messaging in entry.get('messaging', []):
                    sender_igsid = messaging['sender']['id']
                    message = messaging.get('message', {})
                    message_id = message.get('mid')
                    
                    if not message_id:
                        continue
                        
                    # Check for duplicate message
                    if InstagramWebhook.objects.filter(message_id=message_id).exists():
                        logger.warning(f"Duplicate Instagram message received: {message_id}")
                        continue
                    
                    # Get or create user
                    user = get_or_create_user_instagram(sender_igsid)
                    
                    # Get latest state
                    last_webhook = get_instagram_latest_state(sender_igsid)
                    current_state = last_webhook.conversation_state if last_webhook else 'MENU'
                    
                    message_text = message.get('text', '')
                    message_type = 'text'
                    media_url = None
                    
                    # Handle different message types
                    if 'attachments' in message:
                        for attachment in message['attachments']:
                            if attachment['type'] in ['image', 'video', 'audio']:
                                message_type = attachment['type']
                                media_url = attachment.get('payload', {}).get('url')
                    
                    # Create webhook record
                    webhook = InstagramWebhook.objects.create(
                        igsid=sender_igsid,
                        message_id=message_id,
                        message_body=message_text,
                        message_type=message_type,
                        media_url=media_url,
                        timestamp=timezone.now(),
                        status='RECEIVED',
                        user=user,
                        conversation_state=current_state
                    )

                    # Handle conversation states
                    if message_text == '3':  # Exit
                        send_instagram_response(sender_igsid, "Thank you for using VitiGo Query Management. Goodbye!")
                        webhook.conversation_state = 'MENU'
                        webhook.save()
                        continue

                    if current_state == 'MENU' or message_text == '0':
                        if message_text == '1':
                            webhook.conversation_state = 'AWAITING_SUBJECT'
                            webhook.save()
                            send_instagram_response(sender_igsid, "Please enter the subject for your query:")
                        
                        elif message_text == '2':
                            queries = get_queries_instagram(sender_igsid)
                            if queries:
                                response = "Your recent queries:\n\n"
                                response += "\n".join(format_query_status(q) for q in queries)
                                response += "\n\nType 0 for main menu, 3 to exit"
                            else:
                                response = "You have no queries yet.\n\nType 0 for main menu, 3 to exit"
                            send_instagram_response(sender_igsid, response)
                        
                        else:
                            send_instagram_response(sender_igsid, INSTAGRAM_MENU_TEXT)

                    elif current_state == 'AWAITING_SUBJECT':
                        webhook.temp_data = {'subject': message_text}
                        webhook.conversation_state = 'AWAITING_DESCRIPTION'
                        webhook.save()
                        send_instagram_response(sender_igsid, "Please provide details for your query:")

                    elif current_state == 'AWAITING_DESCRIPTION':
                        last_webhook = InstagramWebhook.objects.filter(
                            igsid=sender_igsid,
                            conversation_state='AWAITING_DESCRIPTION'
                        ).exclude(id=webhook.id).last()

                        if not last_webhook or 'subject' not in last_webhook.temp_data:
                            send_instagram_response(sender_igsid, "Sorry, there was an error. Please start over.\n\n" + INSTAGRAM_MENU_TEXT)
                            webhook.conversation_state = 'MENU'
                            webhook.save()
                            continue

                        # Create new query
                        query = Query.objects.create(
                            user=user,
                            subject=last_webhook.temp_data['subject'],
                            description=message_text,
                            source='INSTAGRAM',
                            status='NEW'
                        )
                        
                        webhook.conversation_state = 'MENU'
                        webhook.save()
                        
                        response = """
Your query has been submitted successfully! 
Our team will review it and get back to you.

Type 0 for main menu, 3 to exit
"""
                        send_instagram_response(sender_igsid, response)
            
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            logger.error(f"Error processing Instagram webhook: {str(e)}", exc_info=True)
            return HttpResponse('Error processing webhook', status=500)