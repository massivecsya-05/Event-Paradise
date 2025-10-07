"""
Notification Service Module

This module handles all notification-related functionality:
- Real-time notifications via WebSocket
- Push notifications
- In-app notifications
- Notification preferences
"""

import os
import logging
import json
from datetime import datetime, timedelta
from flask import current_app, request
from flask_login import current_user
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO()

class NotificationService:
    """Notification service class for handling all notifications"""
    
    def __init__(self, app=None):
        """Initialize the notification service"""
        self.app = app
        self.connected_users = {}
        self.user_notifications = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize SocketIO
        socketio.init_app(
            app,
            cors_allowed_origins="*",
            async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
        )
        
        # Register socket event handlers
        self._register_socket_handlers()
        
        logger.info("Notification service initialized")
    
    def _register_socket_handlers(self):
        """Register SocketIO event handlers"""
        
        @socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
                self.connected_users[user_id] = request.sid
                self.user_notifications[user_id] = self.user_notifications.get(user_id, [])
                logger.info(f"User {user_id} connected")
                
                # Send pending notifications
                pending_notifications = self.user_notifications.get(user_id, [])
                for notification in pending_notifications:
                    socketio.emit('notification', notification, room=request.sid)
                
                # Clear pending notifications
                self.user_notifications[user_id] = []
            
            socketio.emit('connection_established', {'user_id': user_id})
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            if current_user.is_authenticated:
                user_id = current_user.id
                if user_id in self.connected_users:
                    del self.connected_users[user_id]
                logger.info(f"User {user_id} disconnected")
        
        @socketio.on('mark_notification_read')
        def handle_mark_read(notification_id):
            """Handle marking notification as read"""
            if current_user.is_authenticated:
                user_id = current_user.id
                logger.info(f"User {user_id} marked notification {notification_id} as read")
                socketio.emit('notification_read', {'notification_id': notification_id})
        
        @socketio.on('get_user_notifications')
        def handle_get_notifications():
            """Handle getting user notifications"""
            if current_user.is_authenticated:
                user_id = current_user.id
                notifications = self.get_user_notifications(user_id)
                socketio.emit('user_notifications', notifications, room=request.sid)
    
    def send_notification(self, user_id, notification_data):
        """
        Send notification to a specific user
        
        Args:
            user_id (int): User ID
            notification_data (dict): Notification data
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            notification = {
                'id': f"notif_{datetime.now().timestamp()}",
                'user_id': user_id,
                'type': notification_data.get('type', 'info'),
                'title': notification_data.get('title', ''),
                'message': notification_data.get('message', ''),
                'data': notification_data.get('data', {}),
                'created_at': datetime.now().isoformat(),
                'read': False
            }
            
            # Check if user is connected
            if user_id in self.connected_users:
                # Send real-time notification
                socketio.emit('notification', notification, room=self.connected_users[user_id])
                logger.info(f"Real-time notification sent to user {user_id}")
                return True
            else:
                # Store notification for later delivery
                if user_id not in self.user_notifications:
                    self.user_notifications[user_id] = []
                self.user_notifications[user_id].append(notification)
                logger.info(f"Notification stored for user {user_id} (offline)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
            return False
    
    def send_broadcast_notification(self, notification_data, user_role=None):
        """
        Send broadcast notification to all users or users with specific role
        
        Args:
            notification_data (dict): Notification data
            user_role (str): User role filter (optional)
            
        Returns:
            int: Number of users notified
        """
        try:
            notification = {
                'id': f"broadcast_{datetime.now().timestamp()}",
                'type': notification_data.get('type', 'info'),
                'title': notification_data.get('title', ''),
                'message': notification_data.get('message', ''),
                'data': notification_data.get('data', {}),
                'created_at': datetime.now().isoformat(),
                'broadcast': True
            }
            
            # Send to all connected users (or filtered by role)
            notified_count = 0
            for user_id, sid in self.connected_users.items():
                # In a real implementation, you would check user role here
                # For now, send to all connected users
                socketio.emit('notification', notification, room=sid)
                notified_count += 1
            
            logger.info(f"Broadcast notification sent to {notified_count} users")
            return notified_count
            
        except Exception as e:
            logger.error(f"Failed to send broadcast notification: {str(e)}")
            return 0
    
    def send_event_notification(self, event, notification_type, data=None):
        """
        Send event-related notification
        
        Args:
            event: Event object
            notification_type (str): Type of notification
            data (dict): Additional data
            
        Returns:
            int: Number of users notified
        """
        try:
            if data is None:
                data = {}
            
            notification_data = {
                'type': 'event',
                'subtype': notification_type,
                'title': f"Event Update: {event.title}",
                'message': self._get_event_message(event, notification_type),
                'data': {
                    'event_id': event.id,
                    'event_title': event.title,
                    'event_status': event.status,
                    **data
                }
            }
            
            # Send to event organizer
            if event.organizer_id:
                self.send_notification(event.organizer_id, notification_data)
            
            # Send to all guests (for certain notification types)
            if notification_type in ['event_reminder', 'event_cancelled', 'event_updated']:
                notified_guests = 0
                for guest in event.guests:
                    # In a real implementation, you would have user accounts for guests
                    # For now, we'll send to the organizer only
                    pass
                return 1  # Organizer notified
            
            return 1  # Organizer notified
            
        except Exception as e:
            logger.error(f"Failed to send event notification for {event.title}: {str(e)}")
            return 0
    
    def send_payment_notification(self, payment, user_id, notification_type):
        """
        Send payment-related notification
        
        Args:
            payment: Payment object
            user_id (int): User ID
            notification_type (str): Type of notification
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            notification_data = {
                'type': 'payment',
                'subtype': notification_type,
                'title': f"Payment {notification_type.replace('_', ' ').title()}",
                'message': self._get_payment_message(payment, notification_type),
                'data': {
                    'payment_id': payment.id,
                    'amount': payment.amount,
                    'payment_type': payment.payment_type,
                    'transaction_id': payment.transaction_id,
                    'status': payment.status
                }
            }
            
            return self.send_notification(user_id, notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send payment notification: {str(e)}")
            return False
    
    def send_guest_notification(self, guest, event, notification_type):
        """
        Send guest-related notification
        
        Args:
            guest: Guest object
            event: Event object
            notification_type (str): Type of notification
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            notification_data = {
                'type': 'guest',
                'subtype': notification_type,
                'title': f"Guest {notification_type.replace('_', ' ').title()}",
                'message': self._get_guest_message(guest, event, notification_type),
                'data': {
                    'guest_id': guest.id,
                    'guest_name': guest.name,
                    'event_id': event.id,
                    'event_title': event.title,
                    'ticket_number': guest.ticket_number
                }
            }
            
            # Send to event organizer
            if event.organizer_id:
                return self.send_notification(event.organizer_id, notification_data)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send guest notification: {str(e)}")
            return False
    
    def get_user_notifications(self, user_id, limit=50):
        """
        Get notifications for a user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of notifications
            
        Returns:
            list: User notifications
        """
        try:
            # In a real implementation, you would fetch from database
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {str(e)}")
            return []
    
    def mark_notification_read(self, user_id, notification_id):
        """
        Mark notification as read
        
        Args:
            user_id (int): User ID
            notification_id (str): Notification ID
            
        Returns:
            bool: True if marked successfully, False otherwise
        """
        try:
            # In a real implementation, you would update in database
            logger.info(f"Notification {notification_id} marked as read for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {str(e)}")
            return False
    
    def _get_event_message(self, event, notification_type):
        """Get event notification message"""
        messages = {
            'event_created': f"New event '{event.title}' has been created.",
            'event_updated': f"Event '{event.title}' has been updated.",
            'event_cancelled': f"Event '{event.title}' has been cancelled.",
            'event_reminder': f"Reminder: Event '{event.title}' is coming up soon.",
            'event_started': f"Event '{event.title}' has started.",
            'event_completed': f"Event '{event.title}' has been completed."
        }
        return messages.get(notification_type, f"Update for event '{event.title}'.")
    
    def _get_payment_message(self, payment, notification_type):
        """Get payment notification message"""
        messages = {
            'payment_received': f"Payment of ${payment.amount:.2f} has been received.",
            'payment_failed': f"Payment of ${payment.amount:.2f} has failed.",
            'payment_refunded': f"Payment of ${payment.amount:.2f} has been refunded.",
            'payment_pending': f"Payment of ${payment.amount:.2f} is pending."
        }
        return messages.get(notification_type, f"Payment update for ${payment.amount:.2f}.")
    
    def _get_guest_message(self, guest, event, notification_type):
        """Get guest notification message"""
        messages = {
            'guest_registered': f"{guest.name} has registered for '{event.title}'.",
            'guest_checked_in': f"{guest.name} has checked in for '{event.title}'.",
            'guest_rsvp_confirmed': f"{guest.name} has confirmed RSVP for '{event.title}'.",
            'guest_rsvp_declined': f"{guest.name} has declined RSVP for '{event.title}'."
        }
        return messages.get(notification_type, f"Guest update for {guest.name}.")
    
    def get_connected_users(self):
        """
        Get list of connected users
        
        Returns:
            dict: Connected users
        """
        return {
            'total_connected': len(self.connected_users),
            'users': list(self.connected_users.keys())
        }
    
    def cleanup_old_notifications(self, days=30):
        """
        Clean up old notifications
        
        Args:
            days (int): Number of days to keep notifications
            
        Returns:
            int: Number of notifications cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            # In a real implementation, you would clean up database
            logger.info(f"Cleaned up {cleaned_count} old notifications")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {str(e)}")
            return 0

# Global notification service instance
notification_service = NotificationService()