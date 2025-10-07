"""
Email Service Module

This module handles all email-related functionality including:
- Event invitations
- RSVP confirmations
- Payment receipts
- Reminders
- Feedback requests
"""

import os
import logging
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Mail, Message
from jinja2 import Template

# Initialize Flask-Mail
mail = Mail()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Email service class for handling all email communications"""
    
    def __init__(self, app=None):
        """Initialize the email service"""
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        mail.init_app(app)
    
    def send_email(self, to, subject, template_name, context=None):
        """
        Send email using template
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            template_name (str): Template filename
            context (dict): Template context variables
        """
        try:
            if not self.app.config.get('MAIL_USERNAME'):
                logger.warning("Email not configured. Skipping email send.")
                return False
            
            with self.app.app_context():
                msg = Message(
                    subject=subject,
                    recipients=[to],
                    sender=self.app.config.get('MAIL_DEFAULT_SENDER')
                )
                
                # Render email template
                if context is None:
                    context = {}
                
                # Add default context
                context.update({
                    'app_name': self.app.config.get('APP_NAME', 'Events Paradise'),
                    'current_year': datetime.now().year,
                    'support_email': self.app.config.get('MAIL_DEFAULT_SENDER')
                })
                
                # For now, use simple text email. In production, you'd use HTML templates
                email_body = self._render_email_template(template_name, context)
                msg.body = email_body
                
                mail.send(msg)
                logger.info(f"Email sent successfully to {to}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    def _render_email_template(self, template_name, context):
        """Render email template with context"""
        # Simple template rendering. In production, use proper template files
        templates = {
            'event_invitation': self._get_event_invitation_template(),
            'rsvp_confirmation': self._get_rsvp_confirmation_template(),
            'payment_receipt': self._get_payment_receipt_template(),
            'event_reminder': self._get_event_reminder_template(),
            'feedback_request': self._get_feedback_request_template(),
            'vendor_welcome': self._get_vendor_welcome_template()
        }
        
        template_str = templates.get(template_name, '')
        template = Template(template_str)
        return template.render(**context)
    
    def send_event_invitation(self, guest, event):
        """Send event invitation to guest"""
        context = {
            'guest_name': guest.name,
            'event_title': event.title,
            'event_description': event.description,
            'event_venue': event.venue,
            'event_date': event.start_date.strftime('%B %d, %Y at %I:%M %p'),
            'ticket_number': guest.ticket_number,
            'rsvp_link': f"http://localhost:5000/rsvp/{guest.ticket_number}",
            'event_organizer': event.organizer.username
        }
        
        subject = f"You're Invited: {event.title}"
        return self.send_email(guest.email, subject, 'event_invitation', context)
    
    def send_rsvp_confirmation(self, guest, event, status):
        """Send RSVP confirmation to guest"""
        context = {
            'guest_name': guest.name,
            'event_title': event.title,
            'rsvp_status': status,
            'event_date': event.start_date.strftime('%B %d, %Y at %I:%M %p'),
            'event_venue': event.venue,
            'ticket_number': guest.ticket_number
        }
        
        subject = f"RSVP Confirmation: {event.title}"
        return self.send_email(guest.email, subject, 'rsvp_confirmation', context)
    
    def send_payment_receipt(self, payment, event, user_email):
        """Send payment receipt"""
        context = {
            'recipient_name': user_email.split('@')[0],
            'event_title': event.title,
            'payment_amount': f"${payment.amount:.2f}",
            'payment_type': payment.payment_type.replace('_', ' ').title(),
            'payment_method': payment.payment_method.replace('_', ' ').title(),
            'transaction_id': payment.transaction_id,
            'payment_date': payment.created_at.strftime('%B %d, %Y at %I:%M %p')
        }
        
        subject = f"Payment Receipt: {event.title}"
        return self.send_email(user_email, subject, 'payment_receipt', context)
    
    def send_event_reminder(self, guest, event, days_before=1):
        """Send event reminder to guest"""
        reminder_date = event.start_date - timedelta(days=days_before)
        
        context = {
            'guest_name': guest.name,
            'event_title': event.title,
            'event_venue': event.venue,
            'event_date': event.start_date.strftime('%B %d, %Y at %I:%M %p'),
            'days_until_event': days_before,
            'ticket_number': guest.ticket_number,
            'organizer_contact': event.organizer.email
        }
        
        subject = f"Reminder: {event.title} in {days_before} day{'s' if days_before > 1 else ''}"
        return self.send_email(guest.email, subject, 'event_reminder', context)
    
    def send_feedback_request(self, guest, event):
        """Send feedback request after event"""
        context = {
            'guest_name': guest.name,
            'event_title': event.title,
            'event_date': event.start_date.strftime('%B %d, %Y'),
            'feedback_link': f"http://localhost:5000/feedback/{guest.ticket_number}",
            'ticket_number': guest.ticket_number
        }
        
        subject = f"How was {event.title}? We'd love your feedback!"
        return self.send_email(guest.email, subject, 'feedback_request', context)
    
    def send_vendor_welcome(self, vendor, event):
        """Send welcome email to vendor"""
        context = {
            'vendor_name': vendor.name,
            'event_title': event.title,
            'service_type': vendor.service_type,
            'contract_amount': f"${vendor.contract_amount:.2f}",
            'event_date': event.start_date.strftime('%B %d, %Y at %I:%M %p'),
            'event_venue': event.venue,
            'organizer_contact': event.organizer.email
        }
        
        subject = f"Vendor Assignment: {event.title}"
        return self.send_email(vendor.email, subject, 'vendor_welcome', context)
    
    # Email Templates
    def _get_event_invitation_template(self):
        return """
Dear {{ guest_name }},

You are cordially invited to attend:

{{ event_title }}

{{ event_description }}

Event Details:
- Date: {{ event_date }}
- Venue: {{ event_venue }}
- Organizer: {{ event_organizer }}

Your Ticket Number: {{ ticket_number }}

Please RSVP by clicking the link below:
{{ rsvp_link }}

We look forward to seeing you at the event!

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """
    
    def _get_rsvp_confirmation_template(self):
        return """
Dear {{ guest_name }},

Thank you for your RSVP for {{ event_title }}.

Your RSVP Status: {{ rsvp_status }}

Event Details:
- Date: {{ event_date }}
- Venue: {{ event_venue }}
- Ticket Number: {{ ticket_number }}

{{ rsvp_status == 'confirmed' and 'We are excited to see you at the event!' or 'We understand you cannot make it. Thank you for letting us know.' }}

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """
    
    def _get_payment_receipt_template(self):
        return """
Dear {{ recipient_name }},

Thank you for your payment. Here is your receipt:

Payment Details:
- Event: {{ event_title }}
- Amount: {{ payment_amount }}
- Payment Type: {{ payment_type }}
- Payment Method: {{ payment_method }}
- Transaction ID: {{ transaction_id }}
- Date: {{ payment_date }}

Your payment has been successfully processed.

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """
    
    def _get_event_reminder_template(self):
        return """
Dear {{ guest_name }},

This is a friendly reminder that {{ event_title }} is coming up in {{ days_until_event }} day{{ 's' if days_until_event > 1 else '' }}.

Event Details:
- Date: {{ event_date }}
- Venue: {{ event_venue }}
- Ticket Number: {{ ticket_number }}

We look forward to seeing you there!

If you have any questions, please contact the event organizer at {{ organizer_contact }}.

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """
    
    def _get_feedback_request_template(self):
        return """
Dear {{ guest_name }},

We hope you enjoyed {{ event_title }} on {{ event_date }}!

Your feedback is important to us and helps us improve future events. Please take a moment to share your experience:

{{ feedback_link }}

Your feedback is valuable and will help us create better events in the future.

Thank you for your time and participation!

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """
    
    def _get_vendor_welcome_template(self):
        return """
Dear {{ vendor_name }},

You have been assigned to provide {{ service_type }} services for:

{{ event_title }}

Event Details:
- Date: {{ event_date }}
- Venue: {{ event_venue }}
- Contract Amount: {{ contract_amount }}

Please review the event details and confirm your availability. If you have any questions or need additional information, please contact the event organizer at {{ organizer_contact }}.

We look forward to working with you!

Best regards,
{{ app_name }} Team

---
This is an automated email. Please do not reply to this message.
For support, contact: {{ support_email }}
© {{ current_year }} {{ app_name }}. All rights reserved.
        """

# Global email service instance
email_service = EmailService()