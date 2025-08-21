from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from premailer import transform
from django.conf import settings
import os


class Util:
    @staticmethod
    def send_html_email(subject, to, path_to_html, value):
        html_content = render_to_string(path_to_html, {"otp": value, "name": to})
        text_content = strip_tags(html_content)
        from_email = os.environ.get("EMAIL_FROM", "dtemplarsarsh@gmail.com")

        # Use the inline_styler to inline the CSS styles
        html_content_with_inline_styles = transform(html_content)

        email = EmailMultiAlternatives(subject, text_content, from_email, [to])
        email.attach_alternative(html_content_with_inline_styles, "text/html")
        email.send()
