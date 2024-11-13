from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from notifications.models import UserNotification, EmailNotification
from django.utils import timezone
import logging

logger = logging.getLogger('query_management')

def send_query_notification(query, notification_type, recipient=None, **kwargs):
    """Send notifications for query events"""
    try:
        if recipient is None:
            recipient = query.assigned_to or query.user

        if not recipient:
            logger.warning(f"No recipient found for query #{query.query_id}")
            return

        # Log notification attempt
        logger.info(f"Preparing notification for query #{query.query_id}, type: {notification_type}")

        # Create in-app notification
        notification_messages = {
            'created': f'New query #{query.query_id} has been created: {query.subject}',
            'assigned': f'Query #{query.query_id} has been assigned to you',
            'status_updated': f'Status updated for query #{query.query_id}: {query.status}',
            'resolved': f'Query #{query.query_id} has been resolved',
        }

        message = notification_messages.get(notification_type, '')
        
        UserNotification.objects.create(
            user=recipient,
            notification_type_id=1,  # Assuming you have created NotificationType for queries
            message=message
        )

        # Email notification setup
        email_subjects = {
            'created': f'New Query Created - #{query.query_id}',
            'assigned': f'Query Assigned - #{query.query_id}',
            'status_updated': f'Query Status Updated - #{query.query_id}',
            'resolved': f'Query Resolved - #{query.query_id}',
        }

        subject = email_subjects.get(notification_type, '')
        email_template = f'query_{notification_type}_email.html'
        
        # Log template selection
        logger.debug(f"Using email template: {email_template}")

        try:
            html_message = render_to_string(email_template, {
                'query': query,
                'recipient': recipient,
                **kwargs
            })
            logger.debug("Email template rendered successfully")

            # Always try to send real email regardless of DEBUG mode
            logger.info(f"Attempting to send email to {recipient.email}")
            
            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                fail_silently=False,
            )
            
            email_sent = send_mail(
                subject=subject,
                message='',
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                connection=connection
            )
            
            logger.info(f"Email sent successfully: {email_sent}")
            
            # Log email notification
            EmailNotification.objects.create(
                user=recipient,
                subject=subject,
                message=html_message,
                status='SENT' if email_sent else 'FAILED',
                sent_at=timezone.now()
            )

        except Exception as e:
            logger.error(f"Email error: {str(e)}")
            logger.error(f"Email settings: HOST={settings.EMAIL_HOST}, "
                        f"PORT={settings.EMAIL_PORT}, "
                        f"USER={settings.EMAIL_HOST_USER}, "
                        f"TLS={settings.EMAIL_USE_TLS}")
            
            EmailNotification.objects.create(
                user=recipient,
                subject=subject,
                message=f"Error sending email: {str(e)}",
                status='FAILED',
                sent_at=timezone.now()
            )
            raise  # Re-raise the exception to see it in the logs

    except Exception as e:
        logger.exception(f"General notification error: {str(e)}")
        raise  # Re-raise to see the error in development