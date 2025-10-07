"""
Scheduler Service Module

This module handles scheduled tasks:
- Automated reminders
- Daily/weekly reports
- Data cleanup
- System maintenance
"""

import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Scheduler service class for handling scheduled tasks"""
    
    def __init__(self, app=None):
        """Initialize the scheduler service"""
        self.app = app
        self.scheduler = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            timezone=app.config.get('SCHEDULER_TIMEZONE', 'UTC')
        )
        
        # Register scheduled jobs
        self._register_jobs()
        
        # Start scheduler
        if app.config.get('SCHEDULER_API_ENABLED', True):
            self.scheduler.start()
            logger.info("Scheduler service started")
    
    def _register_jobs(self):
        """Register all scheduled jobs"""
        
        # Daily event reminders (8:00 AM every day)
        self.scheduler.add_job(
            func=self.send_daily_event_reminders,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_event_reminders',
            name='Daily Event Reminders',
            replace_existing=True
        )
        
        # Vendor reminders (9:00 AM every day)
        self.scheduler.add_job(
            func=self.send_vendor_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='vendor_reminders',
            name='Vendor Reminders',
            replace_existing=True
        )
        
        # Feedback requests (9:00 AM every day)
        self.scheduler.add_job(
            func=self.send_feedback_requests,
            trigger=CronTrigger(hour=9, minute=30),
            id='feedback_requests',
            name='Feedback Requests',
            replace_existing=True
        )
        
        # Daily reports (6:00 PM every day)
        self.scheduler.add_job(
            func=self.generate_daily_reports,
            trigger=CronTrigger(hour=18, minute=0),
            id='daily_reports',
            name='Daily Reports',
            replace_existing=True
        )
        
        # Weekly reports (Monday 8:00 AM)
        self.scheduler.add_job(
            func=self.generate_weekly_reports,
            trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),
            id='weekly_reports',
            name='Weekly Reports',
            replace_existing=True
        )
        
        # Data cleanup (2:00 AM every Sunday)
        self.scheduler.add_job(
            func=self.cleanup_old_data,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='data_cleanup',
            name='Data Cleanup',
            replace_existing=True
        )
        
        # System health check (every hour)
        self.scheduler.add_job(
            func=self.system_health_check,
            trigger=IntervalTrigger(hours=1),
            id='health_check',
            name='System Health Check',
            replace_existing=True
        )
        
        # Notification cleanup (every 6 hours)
        self.scheduler.add_job(
            func=self.cleanup_notifications,
            trigger=IntervalTrigger(hours=6),
            id='notification_cleanup',
            name='Notification Cleanup',
            replace_existing=True
        )
    
    def send_daily_event_reminders(self):
        """Send daily event reminders to guests"""
        try:
            with self.app.app_context():
                from app import db, Event, Guest
                
                # Get events happening in the next 1-3 days
                start_date = datetime.now() + timedelta(days=1)
                end_date = datetime.now() + timedelta(days=3)
                
                upcoming_events = Event.query.filter(
                    Event.start_date.between(start_date, end_date),
                    Event.status.in_(['planned', 'ongoing'])
                ).all()
                
                reminders_sent = 0
                
                for event in upcoming_events:
                    for guest in event.guests:
                        if guest.rsvp_status == 'confirmed' and not guest.check_in_status:
                            # Send email reminder
                            from utils.email_service import email_service
                            email_service.send_event_reminder(guest, event, days_before=2)
                            
                            # Send SMS reminder if phone number available
                            if guest.phone:
                                from utils.sms_service import sms_service
                                sms_service.send_event_reminder(guest, event, days_before=2)
                            
                            reminders_sent += 1
                
                logger.info(f"Sent {reminders_sent} daily event reminders")
                
        except Exception as e:
            logger.error(f"Failed to send daily event reminders: {str(e)}")
    
    def send_vendor_reminders(self):
        """Send reminders to vendors"""
        try:
            with self.app.app_context():
                from app import db, Event, Vendor
                
                # Get events happening in the next 2-7 days
                start_date = datetime.now() + timedelta(days=2)
                end_date = datetime.now() + timedelta(days=7)
                
                upcoming_events = Event.query.filter(
                    Event.start_date.between(start_date, end_date),
                    Event.status.in_(['planned', 'ongoing'])
                ).all()
                
                reminders_sent = 0
                
                for event in upcoming_events:
                    for vendor in event.vendors:
                        if vendor.payment_status != 'paid':
                            # Send email reminder
                            from utils.email_service import email_service
                            email_service.send_vendor_welcome(vendor, event)
                            
                            # Send SMS reminder if phone number available
                            if vendor.phone:
                                from utils.sms_service import sms_service
                                sms_service.send_vendor_reminder(vendor, event, days_before=3)
                            
                            reminders_sent += 1
                
                logger.info(f"Sent {reminders_sent} vendor reminders")
                
        except Exception as e:
            logger.error(f"Failed to send vendor reminders: {str(e)}")
    
    def send_feedback_requests(self):
        """Send feedback requests after completed events"""
        try:
            with self.app.app_context():
                from app import db, Event, Guest
                
                # Get events completed in the last 1-2 days
                end_date = datetime.now() - timedelta(days=1)
                start_date = datetime.now() - timedelta(days=2)
                
                completed_events = Event.query.filter(
                    Event.end_date.between(start_date, end_date),
                    Event.status == 'completed'
                ).all()
                
                feedback_requests_sent = 0
                
                for event in completed_events:
                    for guest in event.guests:
                        if guest.rsvp_status == 'confirmed':
                            # Send feedback request email
                            from utils.email_service import email_service
                            email_service.send_feedback_request(guest, event)
                            
                            # Send SMS reminder if phone number available
                            if guest.phone:
                                from utils.sms_service import sms_service
                                sms_service.send_event_update(
                                    guest, event, 
                                    "Thank you for attending! Please share your feedback."
                                )
                            
                            feedback_requests_sent += 1
                
                logger.info(f"Sent {feedback_requests_sent} feedback requests")
                
        except Exception as e:
            logger.error(f"Failed to send feedback requests: {str(e)}")
    
    def generate_daily_reports(self):
        """Generate daily reports for administrators"""
        try:
            with self.app.app_context():
                from app import db, Event, Guest, Payment, User
                
                # Get today's date range
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                # Get today's statistics
                events_created = Event.query.filter(
                    Event.created_at.between(today_start, today_end)
                ).count()
                
                guests_registered = Guest.query.filter(
                    Guest.created_at.between(today_start, today_end)
                ).count()
                
                payments_processed = Payment.query.filter(
                    Payment.created_at.between(today_start, today_end),
                    Payment.status == 'completed'
                ).count()
                
                total_revenue = db.session.query(
                    db.func.sum(Payment.amount)
                ).filter(
                    Payment.created_at.between(today_start, today_end),
                    Payment.status == 'completed'
                ).scalar() or 0
                
                # Get admin users
                admin_users = User.query.filter_by(role='admin').all()
                
                # Send daily report to admins
                from utils.email_service import email_service
                
                for admin in admin_users:
                    if admin.email:
                        report_data = {
                            'date': today_start.strftime('%Y-%m-%d'),
                            'events_created': events_created,
                            'guests_registered': guests_registered,
                            'payments_processed': payments_processed,
                            'total_revenue': total_revenue
                        }
                        
                        # Send daily report email
                        subject = f"Daily Report - {today_start.strftime('%Y-%m-%d')}"
                        email_service.send_email(
                            admin.email,
                            subject,
                            'daily_report',
                            report_data
                        )
                
                logger.info(f"Generated daily reports for {len(admin_users)} admins")
                
        except Exception as e:
            logger.error(f"Failed to generate daily reports: {str(e)}")
    
    def generate_weekly_reports(self):
        """Generate weekly reports for administrators"""
        try:
            with self.app.app_context():
                from app import db, Event, Guest, Payment, User
                
                # Get last week's date range
                today = datetime.now()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=7)
                
                # Get weekly statistics
                events_created = Event.query.filter(
                    Event.created_at.between(week_start, week_end)
                ).count()
                
                guests_registered = Guest.query.filter(
                    Guest.created_at.between(week_start, week_end)
                ).count()
                
                payments_processed = Payment.query.filter(
                    Payment.created_at.between(week_start, week_end),
                    Payment.status == 'completed'
                ).count()
                
                total_revenue = db.session.query(
                    db.func.sum(Payment.amount)
                ).filter(
                    Payment.created_at.between(week_start, week_end),
                    Payment.status == 'completed'
                ).scalar() or 0
                
                # Get admin users
                admin_users = User.query.filter_by(role='admin').all()
                
                # Send weekly report to admins
                from utils.email_service import email_service
                
                for admin in admin_users:
                    if admin.email:
                        report_data = {
                            'week_start': week_start.strftime('%Y-%m-%d'),
                            'week_end': week_end.strftime('%Y-%m-%d'),
                            'events_created': events_created,
                            'guests_registered': guests_registered,
                            'payments_processed': payments_processed,
                            'total_revenue': total_revenue
                        }
                        
                        # Send weekly report email
                        subject = f"Weekly Report - {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
                        email_service.send_email(
                            admin.email,
                            subject,
                            'weekly_report',
                            report_data
                        )
                
                logger.info(f"Generated weekly reports for {len(admin_users)} admins")
                
        except Exception as e:
            logger.error(f"Failed to generate weekly reports: {str(e)}")
    
    def cleanup_old_data(self):
        """Clean up old data"""
        try:
            with self.app.app_context():
                from app import db, Feedback
                
                # Delete feedback older than 1 year
                cutoff_date = datetime.now() - timedelta(days=365)
                
                deleted_feedback = Feedback.query.filter(
                    Feedback.created_at < cutoff_date
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Cleaned up {deleted_feedback} old feedback records")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
    
    def system_health_check(self):
        """Perform system health check"""
        try:
            with self.app.app_context():
                from app import db, Event, Guest, Payment, User
                
                # Check database connectivity
                try:
                    db.session.execute('SELECT 1')
                    db_status = "healthy"
                except:
                    db_status = "unhealthy"
                
                # Get system statistics
                total_users = User.query.count()
                total_events = Event.query.count()
                total_guests = Guest.query.count()
                total_payments = Payment.query.count()
                
                health_data = {
                    'timestamp': datetime.now().isoformat(),
                    'database_status': db_status,
                    'total_users': total_users,
                    'total_events': total_events,
                    'total_guests': total_guests,
                    'total_payments': total_payments,
                    'scheduler_jobs': len(self.scheduler.get_jobs())
                }
                
                logger.info(f"System health check: {health_data}")
                
                # Send alert if system is unhealthy
                if db_status == "unhealthy":
                    from utils.email_service import email_service
                    admin_users = User.query.filter_by(role='admin').all()
                    
                    for admin in admin_users:
                        if admin.email:
                            email_service.send_email(
                                admin.email,
                                "System Health Alert",
                                'system_alert',
                                health_data
                            )
                
        except Exception as e:
            logger.error(f"Failed to perform system health check: {str(e)}")
    
    def cleanup_notifications(self):
        """Clean up old notifications"""
        try:
            with self.app.app_context():
                from utils.notification_service import notification_service
                
                # Clean up notifications older than 30 days
                cleaned_count = notification_service.cleanup_old_notifications(days=30)
                
                logger.info(f"Cleaned up {cleaned_count} old notifications")
                
        except Exception as e:
            logger.error(f"Failed to cleanup notifications: {str(e)}")
    
    def get_scheduler_status(self):
        """Get scheduler status"""
        try:
            if not self.scheduler:
                return {'status': 'not_initialized'}
            
            return {
                'status': 'running' if self.scheduler.running else 'stopped',
                'jobs': len(self.scheduler.get_jobs()),
                'next_run_time': self.scheduler.get_jobs()[0].next_run_time.isoformat() if self.scheduler.get_jobs() else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def add_job(self, func, trigger, job_id, name, **kwargs):
        """Add a custom job to the scheduler"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs
            )
            logger.info(f"Added custom job: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom job {name}: {str(e)}")
            return False
    
    def remove_job(self, job_id):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
            return False
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler service shutdown")
        except Exception as e:
            logger.error(f"Failed to shutdown scheduler: {str(e)}")

# Global scheduler service instance
scheduler_service = SchedulerService()