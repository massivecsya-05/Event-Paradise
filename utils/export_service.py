"""
Export Service Module

This module handles data export functionality:
- CSV exports
- Excel exports
- PDF reports
- Data backup
"""

import os
import logging
import pandas as pd
from datetime import datetime
from flask import current_app, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExportService:
    """Export service class for handling data exports"""
    
    def __init__(self, app=None):
        """Initialize the export service"""
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Create export directory if it doesn't exist
        export_dir = os.path.join(app.instance_path, 'exports')
        os.makedirs(export_dir, exist_ok=True)
    
    def export_guests_to_csv(self, event_id):
        """
        Export guest list to CSV
        
        Args:
            event_id (int): Event ID
            
        Returns:
            str: Path to exported CSV file
        """
        try:
            with self.app.app_context():
                from app import db, Guest, Event
                
                event = Event.query.get_or_404(event_id)
                guests = Guest.query.filter_by(event_id=event_id).all()
                
                # Prepare data for CSV
                guest_data = []
                for guest in guests:
                    guest_data.append({
                        'Ticket Number': guest.ticket_number,
                        'Name': guest.name,
                        'Email': guest.email,
                        'Phone': guest.phone or '',
                        'RSVP Status': guest.rsvp_status,
                        'Check-in Status': 'Yes' if guest.check_in_status else 'No',
                        'Registration Date': guest.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Create DataFrame
                df = pd.DataFrame(guest_data)
                
                # Generate filename
                filename = f"guests_{event.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Export to CSV
                df.to_csv(filepath, index=False)
                
                logger.info(f"Exported {len(guests)} guests to CSV: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to export guests to CSV: {str(e)}")
            return None
    
    def export_guests_to_excel(self, event_id):
        """
        Export guest list to Excel
        
        Args:
            event_id (int): Event ID
            
        Returns:
            str: Path to exported Excel file
        """
        try:
            with self.app.app_context():
                from app import db, Guest, Event
                
                event = Event.query.get_or_404(event_id)
                guests = Guest.query.filter_by(event_id=event_id).all()
                
                # Prepare data for Excel
                guest_data = []
                for guest in guests:
                    guest_data.append({
                        'Ticket Number': guest.ticket_number,
                        'Name': guest.name,
                        'Email': guest.email,
                        'Phone': guest.phone or '',
                        'RSVP Status': guest.rsvp_status,
                        'Check-in Status': 'Yes' if guest.check_in_status else 'No',
                        'Registration Date': guest.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Create DataFrame
                df = pd.DataFrame(guest_data)
                
                # Generate filename
                filename = f"guests_{event.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Export to Excel
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Guests', index=False)
                    
                    # Add summary sheet
                    summary_data = {
                        'Metric': ['Total Guests', 'Confirmed RSVP', 'Declined RSVP', 'Pending RSVP', 'Checked In'],
                        'Count': [
                            len(guests),
                            len([g for g in guests if g.rsvp_status == 'confirmed']),
                            len([g for g in guests if g.rsvp_status == 'declined']),
                            len([g for g in guests if g.rsvp_status == 'pending']),
                            len([g for g in guests if g.check_in_status])
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                logger.info(f"Exported {len(guests)} guests to Excel: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to export guests to Excel: {str(e)}")
            return None
    
    def export_vendors_to_csv(self, event_id):
        """
        Export vendor list to CSV
        
        Args:
            event_id (int): Event ID
            
        Returns:
            str: Path to exported CSV file
        """
        try:
            with self.app.app_context():
                from app import db, Vendor, Event
                
                event = Event.query.get_or_404(event_id)
                vendors = Vendor.query.filter_by(event_id=event_id).all()
                
                # Prepare data for CSV
                vendor_data = []
                for vendor in vendors:
                    vendor_data.append({
                        'Vendor Name': vendor.name,
                        'Service Type': vendor.service_type,
                        'Email': vendor.email or '',
                        'Phone': vendor.phone or '',
                        'Contract Amount': vendor.contract_amount,
                        'Payment Status': vendor.payment_status,
                        'Registration Date': vendor.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Create DataFrame
                df = pd.DataFrame(vendor_data)
                
                # Generate filename
                filename = f"vendors_{event.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Export to CSV
                df.to_csv(filepath, index=False)
                
                logger.info(f"Exported {len(vendors)} vendors to CSV: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to export vendors to CSV: {str(e)}")
            return None
    
    def export_payments_to_csv(self, event_id):
        """
        Export payment history to CSV
        
        Args:
            event_id (int): Event ID
            
        Returns:
            str: Path to exported CSV file
        """
        try:
            with self.app.app_context():
                from app import db, Payment, Event
                
                event = Event.query.get_or_404(event_id)
                payments = Payment.query.filter_by(event_id=event_id).all()
                
                # Prepare data for CSV
                payment_data = []
                for payment in payments:
                    payment_data.append({
                        'Transaction ID': payment.transaction_id,
                        'Amount': payment.amount,
                        'Payment Type': payment.payment_type,
                        'Payment Method': payment.payment_method,
                        'Status': payment.status,
                        'Payment Date': payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Create DataFrame
                df = pd.DataFrame(payment_data)
                
                # Generate filename
                filename = f"payments_{event.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Export to CSV
                df.to_csv(filepath, index=False)
                
                logger.info(f"Exported {len(payments)} payments to CSV: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to export payments to CSV: {str(e)}")
            return None
    
    def generate_event_report_pdf(self, event_id):
        """
        Generate comprehensive event report in PDF
        
        Args:
            event_id (int): Event ID
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            with self.app.app_context():
                from app import db, Event, Guest, Vendor, Payment
                
                event = Event.query.get_or_404(event_id)
                guests = Guest.query.filter_by(event_id=event_id).all()
                vendors = Vendor.query.filter_by(event_id=event_id).all()
                payments = Payment.query.filter_by(event_id=event_id).all()
                
                # Generate filename
                filename = f"event_report_{event.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Create PDF document
                doc = SimpleDocTemplate(filepath, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    alignment=1  # Center alignment
                )
                
                story.append(Paragraph(f"Event Report: {event.title}", title_style))
                story.append(Spacer(1, 20))
                
                # Event Details
                story.append(Paragraph("Event Details", styles['Heading2']))
                event_details_data = [
                    ['Field', 'Value'],
                    ['Title', event.title],
                    ['Venue', event.venue],
                    ['Start Date', event.start_date.strftime('%Y-%m-%d %H:%M:%S')],
                    ['End Date', event.end_date.strftime('%Y-%m-%d %H:%M:%S')],
                    ['Status', event.status],
                    ['Budget', f"${event.budget:.2f}"],
                    ['Organizer', event.organizer.username]
                ]
                
                event_table = Table(event_details_data, colWidths=[2*inch, 4*inch])
                event_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(event_table)
                story.append(Spacer(1, 20))
                
                # Guest Summary
                story.append(Paragraph("Guest Summary", styles['Heading2']))
                guest_summary_data = [
                    ['Metric', 'Count'],
                    ['Total Guests', len(guests)],
                    ['Confirmed RSVP', len([g for g in guests if g.rsvp_status == 'confirmed'])],
                    ['Declined RSVP', len([g for g in guests if g.rsvp_status == 'declined'])],
                    ['Pending RSVP', len([g for g in guests if g.rsvp_status == 'pending'])],
                    ['Checked In', len([g for g in guests if g.check_in_status])]
                ]
                
                guest_table = Table(guest_summary_data, colWidths=[2*inch, 2*inch])
                guest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(guest_table)
                story.append(Spacer(1, 20))
                
                # Financial Summary
                story.append(Paragraph("Financial Summary", styles['Heading2']))
                total_revenue = sum([p.amount for p in payments if p.status == 'completed'])
                total_contract_value = sum([v.contract_amount for v in vendors])
                
                financial_data = [
                    ['Metric', 'Amount'],
                    ['Event Budget', f"${event.budget:.2f}"],
                    ['Total Revenue', f"${total_revenue:.2f}"],
                    ['Total Contract Value', f"${total_contract_value:.2f}"],
                    ['Budget Utilization', f"{(total_revenue / event.budget * 100):.1f}%" if event.budget > 0 else "0%"]
                ]
                
                financial_table = Table(financial_data, colWidths=[2*inch, 2*inch])
                financial_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(financial_table)
                story.append(Spacer(1, 20))
                
                # Vendor Summary
                story.append(Paragraph("Vendor Summary", styles['Heading2']))
                vendor_summary_data = []
                vendor_summary_data.append(['Vendor', 'Service', 'Contract Amount', 'Payment Status'])
                
                for vendor in vendors:
                    vendor_summary_data.append([
                        vendor.name,
                        vendor.service_type,
                        f"${vendor.contract_amount:.2f}",
                        vendor.payment_status
                    ])
                
                vendor_table = Table(vendor_summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                vendor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(vendor_table)
                story.append(Spacer(1, 20))
                
                # Payment Summary
                story.append(Paragraph("Payment Summary", styles['Heading2']))
                payment_summary_data = []
                payment_summary_data.append(['Transaction ID', 'Amount', 'Type', 'Method', 'Status'])
                
                for payment in payments:
                    payment_summary_data.append([
                        payment.transaction_id,
                        f"${payment.amount:.2f}",
                        payment.payment_type,
                        payment.payment_method,
                        payment.status
                    ])
                
                payment_table = Table(payment_summary_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                payment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(payment_table)
                
                # Footer
                footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Events Paradise"
                footer_style = ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=10,
                    alignment=1,
                    textColor=colors.grey
                )
                story.append(Spacer(1, 30))
                story.append(Paragraph(footer_text, footer_style))
                
                # Build PDF
                doc.build(story)
                
                logger.info(f"Generated event report PDF: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to generate event report PDF: {str(e)}")
            return None
    
    def export_system_data_json(self):
        """
        Export all system data to JSON
        
        Returns:
            str: Path to exported JSON file
        """
        try:
            with self.app.app_context():
                from app import db, Event, Guest, Vendor, Payment, User, Feedback
                
                # Export all data
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'users': [],
                    'events': [],
                    'guests': [],
                    'vendors': [],
                    'payments': [],
                    'feedback': []
                }
                
                # Export users
                for user in User.query.all():
                    export_data['users'].append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'created_at': user.created_at.isoformat()
                    })
                
                # Export events
                for event in Event.query.all():
                    export_data['events'].append({
                        'id': event.id,
                        'title': event.title,
                        'description': event.description,
                        'venue': event.venue,
                        'start_date': event.start_date.isoformat(),
                        'end_date': event.end_date.isoformat(),
                        'status': event.status,
                        'budget': event.budget,
                        'organizer_id': event.organizer_id,
                        'created_at': event.created_at.isoformat()
                    })
                
                # Export guests
                for guest in Guest.query.all():
                    export_data['guests'].append({
                        'id': guest.id,
                        'name': guest.name,
                        'email': guest.email,
                        'phone': guest.phone,
                        'rsvp_status': guest.rsvp_status,
                        'check_in_status': guest.check_in_status,
                        'event_id': guest.event_id,
                        'ticket_number': guest.ticket_number,
                        'created_at': guest.created_at.isoformat()
                    })
                
                # Export vendors
                for vendor in Vendor.query.all():
                    export_data['vendors'].append({
                        'id': vendor.id,
                        'name': vendor.name,
                        'service_type': vendor.service_type,
                        'email': vendor.email,
                        'phone': vendor.phone,
                        'contract_amount': vendor.contract_amount,
                        'payment_status': vendor.payment_status,
                        'event_id': vendor.event_id,
                        'created_at': vendor.created_at.isoformat()
                    })
                
                # Export payments
                for payment in Payment.query.all():
                    export_data['payments'].append({
                        'id': payment.id,
                        'amount': payment.amount,
                        'payment_type': payment.payment_type,
                        'payment_method': payment.payment_method,
                        'status': payment.status,
                        'transaction_id': payment.transaction_id,
                        'event_id': payment.event_id,
                        'created_at': payment.created_at.isoformat()
                    })
                
                # Export feedback
                for feedback in Feedback.query.all():
                    export_data['feedback'].append({
                        'id': feedback.id,
                        'guest_id': feedback.guest_id,
                        'event_id': feedback.event_id,
                        'rating': feedback.rating,
                        'comments': feedback.comments,
                        'created_at': feedback.created_at.isoformat()
                    })
                
                # Generate filename
                filename = f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.app.instance_path, 'exports', filename)
                
                # Export to JSON
                with open(filepath, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                logger.info(f"Exported system data to JSON: {filename}")
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to export system data to JSON: {str(e)}")
            return None
    
    def download_file(self, filepath):
        """
        Download exported file
        
        Args:
            filepath (str): Path to file
            
        Returns:
            Flask response: File download response
        """
        try:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to download file {filepath}: {str(e)}")
            return None
    
    def cleanup_old_exports(self, days=7):
        """
        Clean up old export files
        
        Args:
            days (int): Number of days to keep files
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            export_dir = os.path.join(self.app.instance_path, 'exports')
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            cleaned_count = 0
            for filename in os.listdir(export_dir):
                filepath = os.path.join(export_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old export files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {str(e)}")
            return 0

# Global export service instance
export_service = ExportService()