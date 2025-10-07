"""
SMS Service Module

This module handles all SMS-related functionality using Twilio:
- Event reminders
- RSVP confirmations
- Check-in notifications
- Urgent updates
"""

import os
import logging
from datetime import datetime, timedelta
from flask import current_app

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSService:
    """SMS service class for handling all SMS communications"""
    
    def __init__(self, app=None):
        """Initialize the SMS service"""
        self.app = app
        self.client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize Twilio client if credentials are available
        if TWILIO_AVAILABLE and self._check_twilio_credentials():
            account_sid = app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = app.config.get('TWILIO_AUTH_TOKEN')
            self.client = Client(account_sid, auth_token)
        else:
            logger.warning("Twilio credentials not configured. SMS functionality will be simulated.")
    
    def _check_twilio_credentials(self):
        """Check if Twilio credentials are configured"""
        required_creds = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
        return all(self.app.config.get(cred) for cred in required_creds)
    
    def send_sms(self, to, message):
        """
        Send SMS message
        
        Args:
            to (str): Recipient phone number (E.164 format)
            message (str): SMS message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not self.client:
                # Simulate SMS sending for development/testing
                logger.info(f"[SMS SIMULATION] To: {to}, Message: {message}")
                return True
            
            # Send actual SMS via Twilio
            message_obj = self.client.messages.create(
                body=message,
                from_=self.app.config.get('TWILIO_PHONE_NUMBER'),
                to=to
            )
            
            logger.info(f"SMS sent successfully to {to}. SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {str(e)}")
            return False
    
    def send_event_reminder(self, guest, event, days_before=1):
        """Send event reminder SMS to guest"""
        message = (
            f"REMINDER: {event.title} is in {days_before} day{'s' if days_before > 1 else ''}! "
            f"Date: {event.start_date.strftime('%b %d, %I:%M %p')}, "
            f"Venue: {event.venue}. "
            f"Ticket: {guest.ticket_number}. "
            f"We look forward to seeing you!"
        )
        
        return self.send_sms(guest.phone, message)
    
    def send_rsvp_confirmation(self, guest, event, status):
        """Send RSVP confirmation SMS to guest"""
        status_text = "confirmed" if status == "confirmed" else "declined"
        message = (
            f"RSVP {status_text.upper()} for {event.title}. "
            f"Date: {event.start_date.strftime('%b %d, %I:%M %p')}. "
            f"Ticket: {guest.ticket_number}. "
            f"{'See you there!' if status == 'confirmed' else 'Thank you for letting us know.'}"
        )
        
        return self.send_sms(guest.phone, message)
    
    def send_check_in_notification(self, guest, event):
        """Send check-in confirmation SMS to guest"""
        message = (
            f"Checked in successfully! Welcome to {event.title}. "
            f"Enjoy the event! "
            f"Ticket: {guest.ticket_number}"
        )
        
        return self.send_sms(guest.phone, message)
    
    def send_event_update(self, guest, event, update_message):
        """Send event update SMS to guest"""
        message = (
            f"UPDATE for {event.title}: {update_message} "
            f"Date: {event.start_date.strftime('%b %d, %I:%M %p')}. "
            f"Ticket: {guest.ticket_number}"
        )
        
        return self.send_sms(guest.phone, message)
    
    def send_vendor_reminder(self, vendor, event, days_before=2):
        """Send reminder SMS to vendor"""
        message = (
            f"REMINDER: Your {vendor.service_type} services for {event.title} "
            f"are needed in {days_before} day{'s' if days_before > 1 else ''}. "
            f"Date: {event.start_date.strftime('%b %d, %I:%M %p')}, "
            f"Venue: {event.venue}. "
            f"Contact organizer for questions."
        )
        
        return self.send_sms(vendor.phone, message)
    
    def send_payment_confirmation(self, user_phone, amount, event_title):
        """Send payment confirmation SMS"""
        message = (
            f"PAYMENT CONFIRMED: ${amount:.2f} received for {event_title}. "
            f"Thank you for your payment!"
        )
        
        return self.send_sms(user_phone, message)
    
    def send_emergency_notification(self, guest, event, emergency_message):
        """Send emergency notification SMS to guest"""
        message = (
            f"URGENT: {event.title} - {emergency_message} "
            f"Please check your email for more information. "
            f"Ticket: {guest.ticket_number}"
        )
        
        return self.send_sms(guest.phone, message)
    
    def send_welcome_message(self, guest, event):
        """Send welcome SMS to newly registered guest"""
        message = (
            f"Welcome! You're registered for {event.title}. "
            f"Date: {event.start_date.strftime('%b %d, %I:%M %p')}, "
            f"Venue: {event.venue}. "
            f"Ticket: {guest.ticket_number}. "
            f"Check your email for details!"
        )
        
        return self.send_sms(guest.phone, message)
    
    def bulk_send_event_reminders(self, guests, event, days_before=1):
        """Send bulk event reminders to all guests"""
        success_count = 0
        total_count = 0
        
        for guest in guests:
            if guest.phone:  # Only send to guests with phone numbers
                total_count += 1
                if self.send_event_reminder(guest, event, days_before):
                    success_count += 1
        
        logger.info(f"Bulk SMS reminders sent: {success_count}/{total_count} successful")
        return {
            'total': total_count,
            'successful': success_count,
            'failed': total_count - success_count
        }
    
    def bulk_send_vendor_reminders(self, vendors, event, days_before=2):
        """Send bulk reminders to all vendors"""
        success_count = 0
        total_count = 0
        
        for vendor in vendors:
            if vendor.phone:  # Only send to vendors with phone numbers
                total_count += 1
                if self.send_vendor_reminder(vendor, event, days_before):
                    success_count += 1
        
        logger.info(f"Bulk vendor reminders sent: {success_count}/{total_count} successful")
        return {
            'total': total_count,
            'successful': success_count,
            'failed': total_count - success_count
        }
    
    def get_sms_status(self, message_sid):
        """Get status of a sent SMS message"""
        try:
            if not self.client:
                return {'status': 'simulated', 'error': 'Twilio not configured'}
            
            message = self.client.messages(message_sid).fetch()
            return {
                'status': message.status,
                'date_created': message.date_created,
                'date_sent': message.date_sent,
                'error_code': message.error_code,
                'error_message': message.error_message
            }
        except Exception as e:
            logger.error(f"Failed to get SMS status for {message_sid}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def validate_phone_number(self, phone_number):
        """Validate and format phone number"""
        try:
            if not self.client:
                # Basic validation for simulation
                phone_number = phone_number.strip()
                if phone_number.startswith('+'):
                    return phone_number
                elif phone_number.startswith('0'):
                    return f'+265{phone_number[1:]}'  # Malawi country code
                else:
                    return f'+265{phone_number}'
            
            # Use Twilio lookup for proper validation
            phone_number = self.client.lookups.v2.phone_numbers(phone_number).fetch()
            return phone_number.phone_number
        except Exception as e:
            logger.error(f"Phone number validation failed for {phone_number}: {str(e)}")
            return None

# Global SMS service instance
sms_service = SMSService()