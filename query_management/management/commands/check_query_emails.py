# query_management/management/commands/check_query_emails.py

import logging
import email
import imaplib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from query_management.models import Query

logger = logging.getLogger(__name__)

class EmailQueryHandler:
    def __init__(self):
        self.email_host = settings.EMAIL_HOST
        self.email_user = settings.EMAIL_HOST_USER
        self.email_password = settings.EMAIL_HOST_PASSWORD
        self.imap_server = None

    def connect(self):
        """Connect to the email server"""
        try:
            self.imap_server = imaplib.IMAP4_SSL(self.email_host)
            self.imap_server.login(self.email_user, self.email_password)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {str(e)}")
            return False

    def disconnect(self):
        """Safely disconnect from the email server"""
        if self.imap_server:
            try:
                self.imap_server.logout()
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")

    def process_email(self, email_message):
        """Process a single email and create a Query if relevant"""
        try:
            subject = str(email.header.make_header(
                email.header.decode_header(email_message['subject'])))
            from_address = email.utils.parseaddr(email_message['from'])[1]
            
            # Get email body
            if email_message.is_multipart():
                body = ''
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()

            # Check for relevant keywords
            keywords = ['query', 'new', 'vitiligo']
            subject_lower = subject.lower()
            body_lower = body.lower()
            
            if any(keyword in subject_lower or keyword in body_lower for keyword in keywords):
                Query.objects.create(
                    subject=subject[:255],  # Limit to model's max_length
                    description=body,
                    source='EMAIL',
                    contact_email=from_address,
                    status='NEW',
                    is_anonymous=False
                )
                logger.info(f"Created new query from email: {subject}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return False

    def check_emails(self):
        """Check for new emails and process them"""
        if not self.connect():
            return

        try:
            # Select the inbox
            self.imap_server.select('INBOX')

            # Search for unread emails
            _, message_numbers = self.imap_server.search(None, 'UNSEEN')

            for num in message_numbers[0].split():
                try:
                    # Fetch the email message
                    _, msg = self.imap_server.fetch(num, '(RFC822)')
                    email_body = msg[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Process the email
                    if self.process_email(email_message):
                        # Mark as read if successfully processed
                        self.imap_server.store(num, '+FLAGS', '\\Seen')

                except Exception as e:
                    logger.error(f"Error processing message {num}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error checking emails: {str(e)}")
        finally:
            self.disconnect()

class Command(BaseCommand):
    help = 'Check for new query emails and create Query objects'

    def handle(self, *args, **kwargs):
        try:
            handler = EmailQueryHandler()
            handler.check_emails()
            self.stdout.write(self.style.SUCCESS('Successfully checked emails'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))