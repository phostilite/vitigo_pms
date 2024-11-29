# webhooks/utils.py
import re
from django.contrib.auth import get_user_model
from query_management.models import Query
from .models import WhatsAppWebhook
from django.conf import settings
import requests
import logging

logger = logging.getLogger('query_management')

MENU_TEXT = """
Welcome to VitiGo Query Management!
1. Create new query
2. View my queries
3. Exit

Reply with a number to continue.
"""

def get_or_create_user(phone_number):
    """Get or create user based on phone number"""
    logger.debug(f"Getting/creating user for phone: {phone_number}")
    User = get_user_model()
    user = User.objects.filter(phone_number=phone_number).first()
    if not user:
        logger.info(f"Creating new user for phone: {phone_number}")
        email = f"whatsapp_{phone_number}@temp.com"
        user = User.objects.create(
            email=email,
            phone_number=phone_number,
            is_active=True
        )
    return user

def get_latest_state(phone_number):
    """Get user's latest conversation state"""
    logger.debug(f"Fetching latest state for phone: {phone_number}")
    return WhatsAppWebhook.objects.filter(
        from_number=phone_number
    ).order_by('-created_at').first()

def get_user_queries(phone_number):
    """Get queries for a phone number"""
    logger.debug(f"Fetching queries for phone: {phone_number}")
    return Query.objects.filter(
        contact_phone=phone_number
    ).order_by('-created_at')[:5]

def format_query_status(query):
    """Format query status for WhatsApp message"""
    return f"""
Query #{query.query_id}
Subject: {query.subject}
Status: {query.get_status_display()}
Created: {query.created_at.strftime('%Y-%m-%d %H:%M')}
"""

def send_whatsapp_response(to_number, message):
    """Send WhatsApp message"""
    logger.info(f"Sending WhatsApp message to {to_number}")
    logger.debug(f"Message content: {message[:100]}...")
    
    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    try:
        response = requests.post(url, json={
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }, headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        })
        
        response_data = response.json()
        if response.status_code != 200:
            logger.error(f"WhatsApp API error: {response_data}")
        else:
            logger.debug(f"WhatsApp API response: {response_data}")
        return response_data
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API request failed: {str(e)}", exc_info=True)
        raise

def send_messenger_response(psid, message_text):
    """Send Facebook Messenger message"""
    logger.info(f"Sending Messenger message to {psid}")
    logger.debug(f"Message content: {message_text[:100]}...")
    
    url = f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/{settings.FACEBOOK_PAGE_ID}/messages"
    
    try:
        response = requests.post(url, json={
            "recipient": {"id": psid},
            "messaging_type": "RESPONSE",
            "message": {"text": message_text}
        }, headers={
            "Authorization": f"Bearer {settings.FACEBOOK_PAGE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        })
        
        response_data = response.json()
        if response.status_code != 200:
            logger.error(f"Messenger API error: {response_data}")
        else:
            logger.debug(f"Messenger API response: {response_data}")
        return response_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Messenger API request failed: {str(e)}", exc_info=True)
        raise

def send_messenger_media(psid, media_url, media_type='image'):
    """Send media attachment via Messenger"""
    logger.info(f"Sending Messenger {media_type} to {psid}")
    
    url = f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/{settings.FACEBOOK_PAGE_ID}/messages"
    
    try:
        response = requests.post(url, json={
            "recipient": {"id": psid},
            "message": {
                "attachment": {
                    "type": media_type,
                    "payload": {
                        "url": media_url,
                        "is_reusable": True
                    }
                }
            }
        }, headers={
            "Authorization": f"Bearer {settings.FACEBOOK_PAGE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        })
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Messenger media send failed: {str(e)}", exc_info=True)
        raise