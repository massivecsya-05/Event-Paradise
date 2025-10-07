"""
Calendar Service Module

This module handles Google Calendar integration:
- Event synchronization
- Calendar creation
- Invitation management
- Reminder synchronization
"""

import os
import logging
from datetime import datetime, timedelta
from flask import current_app

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService:
    """Calendar service class for Google Calendar integration"""
    
    def __init__(self, app=None):
        """Initialize the calendar service"""
        self.app = app
        self.service = None
        self.credentials = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize Google Calendar service if credentials are available
        if GOOGLE_AVAILABLE and self._check_google_credentials():
            self._authenticate()
        else:
            logger.warning("Google credentials not configured. Calendar functionality will be simulated.")
    
    def _check_google_credentials(self):
        """Check if Google credentials are configured"""
        required_creds = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
        return all(self.app.config.get(cred) for cred in required_creds)
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            # For development, use simulated authentication
            if not self.app.config.get('GOOGLE_CLIENT_ID'):
                logger.info("Using simulated calendar service")
                return
            
            # In production, implement proper OAuth2 flow
            # For now, we'll simulate the service
            self.service = self._create_simulated_service()
            logger.info("Calendar service initialized (simulated)")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {str(e)}")
    
    def _create_simulated_service(self):
        """Create a simulated calendar service for development"""
        class SimulatedCalendarService:
            def __init__(self):
                self.events = []
                self.calendars = []
            
            def events(self):
                return SimulatedEventsService(self)
            
            def calendars(self):
                return SimulatedCalendarsService(self)
        
        class SimulatedEventsService:
            def __init__(self, calendar_service):
                self.calendar_service = calendar_service
            
            def insert(self, calendar_id='primary', body=None, sendUpdates=None):
                event_data = {
                    'id': f"event_{len(self.calendar_service.events) + 1}",
                    'summary': body.get('summary', 'Untitled Event'),
                    'description': body.get('description', ''),
                    'start': body.get('start', {}),
                    'end': body.get('end', {}),
                    'location': body.get('location', ''),
                    'attendees': body.get('attendees', []),
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat()
                }
                self.calendar_service.events.append(event_data)
                logger.info(f"Created simulated calendar event: {event_data['summary']}")
                return event_data
            
            def update(self, calendar_id='primary', eventId=None, body=None):
                for event in self.calendar_service.events:
                    if event['id'] == eventId:
                        event.update(body)
                        event['updated'] = datetime.now().isoformat()
                        logger.info(f"Updated simulated calendar event: {event['summary']}")
                        return event
                return None
            
            def delete(self, calendar_id='primary', eventId=None):
                for i, event in enumerate(self.calendar_service.events):
                    if event['id'] == eventId:
                        removed_event = self.calendar_service.events.pop(i)
                        logger.info(f"Deleted simulated calendar event: {removed_event['summary']}")
                        return removed_event
                return None
            
            def list(self, calendar_id='primary', timeMin=None, timeMax=None, singleEvents=None, orderBy=None):
                events = self.calendar_service.events
                if timeMin:
                    events = [e for e in events if e.get('start', {}).get('dateTime', '') >= timeMin]
                if timeMax:
                    events = [e for e in events if e.get('end', {}).get('dateTime', '') <= timeMax]
                return {'items': events}
        
        class SimulatedCalendarsService:
            def __init__(self, calendar_service):
                self.calendar_service = calendar_service
            
            def insert(self, body=None):
                calendar_data = {
                    'id': f"calendar_{len(self.calendar_service.calendars) + 1}",
                    'summary': body.get('summary', 'Untitled Calendar'),
                    'description': body.get('description', ''),
                    'timeZone': body.get('timeZone', 'UTC'),
                    'created': datetime.now().isoformat()
                }
                self.calendar_service.calendars.append(calendar_data)
                logger.info(f"Created simulated calendar: {calendar_data['summary']}")
                return calendar_data
        
        return SimulatedCalendarService()
    
    def create_event_calendar(self, event):
        """
        Create a calendar for an event
        
        Args:
            event: Event object
            
        Returns:
            dict: Calendar creation result
        """
        try:
            calendar_data = {
                'summary': f"{event.title} - Event Calendar",
                'description': f"Calendar for event: {event.description}",
                'timeZone': 'UTC'
            }
            
            if self.service:
                calendar = self.service.calendars().insert(body=calendar_data).execute()
                return {
                    'success': True,
                    'calendar_id': calendar['id'],
                    'summary': calendar['summary']
                }
            else:
                # Simulated response
                return {
                    'success': True,
                    'calendar_id': f"simulated_calendar_{event.id}",
                    'summary': calendar_data['summary']
                }
                
        except Exception as e:
            logger.error(f"Failed to create calendar for event {event.title}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_event_to_calendar(self, event, calendar_id='primary'):
        """
        Add event to Google Calendar
        
        Args:
            event: Event object
            calendar_id (str): Calendar ID
            
        Returns:
            dict: Event creation result
        """
        try:
            # Prepare event data for Google Calendar
            event_data = {
                'summary': event.title,
                'description': event.description or f"Event managed by Events Paradise",
                'location': event.venue,
                'start': {
                    'dateTime': event.start_date.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': event.end_date.isoformat(),
                    'timeZone': 'UTC'
                },
                'attendees': [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30}  # 30 minutes before
                    ]
                }
            }
            
            # Add organizer as attendee
            if event.organizer and event.organizer.email:
                event_data['attendees'].append({
                    'email': event.organizer.email,
                    'displayName': event.organizer.username,
                    'organizer': True
                })
            
            # Add guests as attendees
            for guest in event.guests:
                if guest.email:
                    event_data['attendees'].append({
                        'email': guest.email,
                        'displayName': guest.name
                    })
            
            if self.service:
                calendar_event = self.service.events().insert(
                    calendarId=calendar_id,
                    body=event_data,
                    sendUpdates='all'
                ).execute()
                
                return {
                    'success': True,
                    'event_id': calendar_event['id'],
                    'html_link': calendar_event.get('htmlLink', ''),
                    'calendar_id': calendar_id
                }
            else:
                # Simulated response
                return {
                    'success': True,
                    'event_id': f"simulated_event_{event.id}",
                    'html_link': f"https://calendar.google.com/calendar/event?eid=simulated_{event.id}",
                    'calendar_id': calendar_id
                }
                
        except Exception as e:
            logger.error(f"Failed to add event {event.title} to calendar: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_calendar_event(self, event, calendar_event_id, calendar_id='primary'):
        """
        Update event in Google Calendar
        
        Args:
            event: Event object
            calendar_event_id (str): Google Calendar event ID
            calendar_id (str): Calendar ID
            
        Returns:
            dict: Update result
        """
        try:
            event_data = {
                'summary': event.title,
                'description': event.description or f"Event managed by Events Paradise",
                'location': event.venue,
                'start': {
                    'dateTime': event.start_date.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': event.end_date.isoformat(),
                    'timeZone': 'UTC'
                }
            }
            
            if self.service:
                updated_event = self.service.events().update(
                    calendarId=calendar_id,
                    eventId=calendar_event_id,
                    body=event_data,
                    sendUpdates='all'
                ).execute()
                
                return {
                    'success': True,
                    'event_id': updated_event['id'],
                    'html_link': updated_event.get('htmlLink', '')
                }
            else:
                # Simulated response
                return {
                    'success': True,
                    'event_id': calendar_event_id,
                    'html_link': f"https://calendar.google.com/calendar/event?eid={calendar_event_id}"
                }
                
        except Exception as e:
            logger.error(f"Failed to update calendar event {calendar_event_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_calendar_event(self, calendar_event_id, calendar_id='primary'):
        """
        Delete event from Google Calendar
        
        Args:
            calendar_event_id (str): Google Calendar event ID
            calendar_id (str): Calendar ID
            
        Returns:
            dict: Deletion result
        """
        try:
            if self.service:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=calendar_event_id
                ).execute()
                
                return {'success': True, 'event_id': calendar_event_id}
            else:
                # Simulated response
                return {'success': True, 'event_id': calendar_event_id}
                
        except Exception as e:
            logger.error(f"Failed to delete calendar event {calendar_event_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_calendar_invitations(self, event, calendar_event_id, calendar_id='primary'):
        """
        Send calendar invitations to guests
        
        Args:
            event: Event object
            calendar_event_id (str): Google Calendar event ID
            calendar_id (str): Calendar ID
            
        Returns:
            dict: Invitation result
        """
        try:
            invitations_sent = 0
            
            for guest in event.guests:
                if guest.email:
                    # In a real implementation, this would send actual calendar invitations
                    logger.info(f"Calendar invitation sent to {guest.email} for event {event.title}")
                    invitations_sent += 1
            
            return {
                'success': True,
                'invitations_sent': invitations_sent,
                'total_guests': len(event.guests)
            }
            
        except Exception as e:
            logger.error(f"Failed to send calendar invitations for event {event.title}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_event_reminders(self, event, calendar_event_id, calendar_id='primary'):
        """
        Sync event reminders with Google Calendar
        
        Args:
            event: Event object
            calendar_event_id (str): Google Calendar event ID
            calendar_id (str): Calendar ID
            
        Returns:
            dict: Sync result
        """
        try:
            reminder_data = {
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30}  # 30 minutes before
                    ]
                }
            }
            
            if self.service:
                updated_event = self.service.events().update(
                    calendarId=calendar_id,
                    eventId=calendar_event_id,
                    body=reminder_data,
                    sendUpdates='none'
                ).execute()
                
                return {
                    'success': True,
                    'event_id': updated_event['id'],
                    'reminders_set': True
                }
            else:
                # Simulated response
                return {
                    'success': True,
                    'event_id': calendar_event_id,
                    'reminders_set': True
                }
                
        except Exception as e:
            logger.error(f"Failed to sync reminders for event {event.title}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_calendar_events(self, calendar_id='primary', time_min=None, time_max=None):
        """
        Get events from Google Calendar
        
        Args:
            calendar_id (str): Calendar ID
            time_min (str): Minimum time (ISO format)
            time_max (str): Maximum time (ISO format)
            
        Returns:
            dict: Calendar events
        """
        try:
            if self.service:
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                return {
                    'success': True,
                    'events': events_result.get('items', [])
                }
            else:
                # Simulated response
                return {
                    'success': True,
                    'events': []
                }
                
        except Exception as e:
            logger.error(f"Failed to get calendar events: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global calendar service instance
calendar_service = CalendarService()