# webhooks/utils.py
import re
from django.contrib.auth import get_user_model
from query_management.models import Query
from .models import WhatsAppWebhook
from django.conf import settings
import requests

MENU_TEXT = """
Welcome to VitiGo Query Management!
1. Create new query
2. View my queries
3. Exit

Reply with a number to continue.
"""

def get_or_create_user(phone_number):
    """Get or create user based on phone number"""
    User = get_user_model()
    user = User.objects.filter(phone_number=phone_number).first()
    if not user:
        # Create temp user with phone number
        email = f"whatsapp_{phone_number}@temp.com"
        user = User.objects.create(
            email=email,
            phone_number=phone_number,
            is_active=True
        )
    return user

def get_latest_state(phone_number):
    """Get user's latest conversation state"""
    return WhatsAppWebhook.objects.filter(
        from_number=phone_number
    ).order_by('-created_at').first()

def get_user_queries(phone_number):
    """Get queries for a phone number"""
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
    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()