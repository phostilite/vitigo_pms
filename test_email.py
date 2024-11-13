
import os
import django
from django.core.mail import send_mail
from django.conf import settings
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitigo_pms.settings')
django.setup()

logger = logging.getLogger(__name__)

def test_email_settings():
    """Print current email settings"""
    print("\nCurrent Email Settings:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"DEBUG: {settings.DEBUG}")

def send_test_email():
    """Send a test email"""
    try:
        print("\nAttempting to send test email...")
        
        # First, make sure we're not in DEBUG mode for email
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        
        subject = 'Test Email from Vitigo PMS'
        message = 'This is a test email from Vitigo PMS. If you receive this, email sending is working!'
        html_message = f"""
        <html>
            <body>
                <h2>Test Email from Vitigo PMS</h2>
                <p>This is a test email from Vitigo PMS.</p>
                <p>If you receive this, email sending is working!</p>
                <p>Current time: {django.utils.timezone.now()}</p>
            </body>
        </html>
        """
        
        # Send email
        success = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['ps4798214@gmail.com'],  # Replace with your email
            html_message=html_message,
            fail_silently=False
        )
        
        if success:
            print("Email sent successfully!")
        else:
            print("Email sending failed!")
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        # Print current settings
        test_email_settings()
        
        # Send test email
        send_test_email()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")