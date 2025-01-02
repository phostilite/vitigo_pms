# query_management/management/commands/check_query_emails.py

import logging
import email
import imaplib
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from query_management.models import Query

logger = logging.getLogger(__name__)

class EmailQueryHandler:
    def __init__(self):
        self.email_host = 'imap.gmail.com'
        self.email_user = settings.EMAIL_HOST_USER
        self.email_password = settings.EMAIL_HOST_PASSWORD
        self.imap_server = None
        self.log_file = 'email_logs.txt'

    def connect(self):
        try:
            logger.info(f"Connecting to {self.email_host}")
            self.imap_server = imaplib.IMAP4_SSL(self.email_host)
            self.imap_server.login(self.email_user, self.email_password)
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        if self.imap_server:
            try:
                self.imap_server.logout()
            except Exception as e:
                logger.error(f"Disconnect error: {str(e)}")

    def get_email_body(self, email_message):
        """Extract email body from message"""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        return email_message.get_payload(decode=True).decode()

    def log_todays_emails(self):
        """Log all of today's emails to file"""
        if not self.connect():
            return

        try:
            # Clear existing log file
            open(self.log_file, 'w').close()
            
            self.imap_server.select('INBOX')
            today = timezone.now().strftime("%d-%b-%Y")
            _, message_numbers = self.imap_server.search(None, f'(SINCE "{today}")')

            if not message_numbers[0]:
                logger.info("No messages found today")
                return

            messages = message_numbers[0].split()
            logger.info(f"Found {len(messages)} messages today")

            for num in messages:
                try:
                    _, msg = self.imap_server.fetch(num, '(RFC822 FLAGS)')
                    email_body = msg[0][1]
                    flags = imaplib.ParseFlags(msg[0][0])
                    email_message = email.message_from_bytes(email_body)

                    # Get email details
                    subject = str(email.header.make_header(
                        email.header.decode_header(email_message['subject'])))
                    from_address = email.utils.parseaddr(email_message['from'])[1]
                    date = email_message['date']
                    is_read = '\\Seen' in flags
                    body = self.get_email_body(email_message)

                    # Log to file
                    log_entry = {
                        'message_id': num.decode(),
                        'subject': subject,
                        'from': from_address,
                        'date': date,
                        'is_read': is_read,
                        'body': body
                    }

                    with open(self.log_file, 'a') as f:
                        f.write(json.dumps(log_entry) + '\n')

                except Exception as e:
                    logger.error(f"Error logging message {num}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in log_todays_emails: {str(e)}")
        finally:
            self.disconnect()

    def process_logged_emails(self):
        """Process the logged emails and create queries"""
        try:
            if not self.connect():
                return

            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        email_data = json.loads(line.strip())
                        
                        # Check if it's a query email and not read
                        if '[VITIGO-QUERY]' in email_data['subject'].upper() and not email_data['is_read']:
                            logger.info(f"Processing query email: {email_data['subject']}")

                            # Extract clean subject
                            clean_subject = email_data['subject'].split(']', 1)[1].strip()

                            # Determine query type
                            body_lower = email_data['body'].lower()
                            query_type = 'GENERAL'
                            if 'appointment' in body_lower:
                                query_type = 'APPOINTMENT'
                            elif 'treatment' in body_lower:
                                query_type = 'TREATMENT'
                            elif 'billing' in body_lower:
                                query_type = 'BILLING'

                            # Extract contact number
                            contact_phone = None
                            for line in email_data['body'].split('\n'):
                                if '- Contact:' in line:
                                    contact_phone = line.split('- Contact:')[1].strip()
                                    break

                            # Create query
                            query = Query.objects.create(
                                subject=clean_subject[:255],
                                description=email_data['body'],
                                source='EMAIL',
                                contact_email=email_data['from'],
                                contact_phone=contact_phone,
                                status='NEW',
                                is_anonymous=False,
                                query_type=query_type
                            )

                            # Mark email as read in Gmail
                            self.imap_server.select('INBOX')
                            self.imap_server.store(email_data['message_id'].encode(), '+FLAGS', '\\Seen')
                            
                            logger.info(f"Created query {query.query_id} from email")

                    except json.JSONDecodeError:
                        logger.error("Error decoding JSON line")
                    except Exception as e:
                        logger.error(f"Error processing logged email: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error in process_logged_emails: {str(e)}")
        finally:
            self.disconnect()

class Command(BaseCommand):
    help = 'Process query emails and create Query objects'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write("Starting email processing...")
            handler = EmailQueryHandler()
            
            # Step 1: Log all today's emails
            self.stdout.write("Logging today's emails...")
            handler.log_todays_emails()
            
            # Step 2: Process the logged emails
            self.stdout.write("Processing logged emails...")
            handler.process_logged_emails()
            
            self.stdout.write(self.style.SUCCESS('Successfully processed emails'))
            
            # Display the contents of the log file
            self.stdout.write("\nEmail Log Contents:")
            try:
                with open('email_logs.txt', 'r') as f:
                    self.stdout.write(f.read())
            except FileNotFoundError:
                self.stdout.write("No email log file found")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))