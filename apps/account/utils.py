from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from premailer import transform
import os
import logging

logger = logging.getLogger(__name__)


class Util:
    @staticmethod
    def send_html_email(subject, to, template_path, value):
        """
        Send HTML email with inline styles.
        
        Args:
            subject: Email subject line
            to: Recipient email address
            template_path: Django template path (e.g., 'emails/email_otp.html')
            value: Value to pass to template (OTP or reset link)
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            html_content = render_to_string(template_path, {"otp": value, "name": to})
            text_content = strip_tags(html_content)
            from_email = os.getenv("EMAIL_FROM")

            # Use the inline_styler to inline the CSS styles
            html_content_with_inline_styles = transform(html_content)

            email = EmailMultiAlternatives(subject, text_content, from_email, [to])
            email.attach_alternative(html_content_with_inline_styles, "text/html")
            email.send()
            
            logger.info(f"Email sent successfully to {to} using template {template_path}")
            return True
            
        except FileNotFoundError as e:
            # Template file not found
            logger.error(f"Email template not found: {template_path}")
            logger.error(f"Error details: {e}")
            return False
            
        except OSError as e:
            # Network errors (unreachable SMTP server, connection refused, etc.)
            logger.error(f"Network error sending email to {to}: {e}")
            logger.error("Check EMAIL_HOST configuration and network connectivity")
            return False
            
        except Exception as e:
            # Any other email sending errors
            logger.error(f"Error sending email to {to}: {type(e).__name__}: {e}")
            logger.error(f"Template path attempted: {template_path}")
            return False
