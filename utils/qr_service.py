"""
QR Code Service Module

This module handles QR code generation for:
- Guest tickets
- Event check-ins
- Vendor badges
- Payment receipts
"""

import os
import qrcode
import logging
from datetime import datetime, timedelta
from flask import current_app
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRService:
    """QR code service class for generating QR codes"""
    
    def __init__(self, app=None):
        """Initialize the QR service"""
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Create QR code output directory if it doesn't exist
        qr_dir = app.config.get('QR_CODE_OUTPUT_DIR', 'static/qrcodes')
        os.makedirs(qr_dir, exist_ok=True)
    
    def generate_guest_ticket_qr(self, guest, event):
        """
        Generate QR code for guest ticket
        
        Args:
            guest: Guest object
            event: Event object
            
        Returns:
            str: Path to generated QR code image
        """
        try:
            # Create QR code data
            qr_data = {
                'type': 'guest_ticket',
                'ticket_number': guest.ticket_number,
                'guest_id': guest.id,
                'event_id': event.id,
                'guest_name': guest.name,
                'event_title': event.title,
                'event_date': event.start_date.isoformat(),
                'venue': event.venue,
                'generated_at': datetime.now().isoformat()
            }
            
            # Convert to JSON string
            import json
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=self.app.config.get('QR_CODE_BOX_SIZE', 10),
                border=self.app.config.get('QR_CODE_BORDER', 4),
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Add text overlay
            qr_img = self._add_text_overlay(qr_img, guest.ticket_number, guest.name, event.title)
            
            # Save QR code
            filename = f"ticket_{guest.ticket_number}.png"
            filepath = os.path.join(self.app.config.get('QR_CODE_OUTPUT_DIR', 'static/qrcodes'), filename)
            qr_img.save(filepath)
            
            logger.info(f"Generated QR code for guest {guest.name}, ticket {guest.ticket_number}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for guest {guest.name}: {str(e)}")
            return None
    
    def generate_vendor_badge_qr(self, vendor, event):
        """
        Generate QR code for vendor badge
        
        Args:
            vendor: Vendor object
            event: Event object
            
        Returns:
            str: Path to generated QR code image
        """
        try:
            # Create QR code data
            qr_data = {
                'type': 'vendor_badge',
                'vendor_id': vendor.id,
                'event_id': event.id,
                'vendor_name': vendor.name,
                'service_type': vendor.service_type,
                'event_title': event.title,
                'event_date': event.start_date.isoformat(),
                'venue': event.venue,
                'generated_at': datetime.now().isoformat()
            }
            
            # Convert to JSON string
            import json
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=self.app.config.get('QR_CODE_BOX_SIZE', 10),
                border=self.app.config.get('QR_CODE_BORDER', 4),
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Add text overlay
            qr_img = self._add_text_overlay(qr_img, f"VENDOR-{vendor.id}", vendor.name, event.title)
            
            # Save QR code
            filename = f"vendor_{vendor.id}_{event.id}.png"
            filepath = os.path.join(self.app.config.get('QR_CODE_OUTPUT_DIR', 'static/qrcodes'), filename)
            qr_img.save(filepath)
            
            logger.info(f"Generated QR code for vendor {vendor.name}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for vendor {vendor.name}: {str(e)}")
            return None
    
    def generate_payment_receipt_qr(self, payment, event):
        """
        Generate QR code for payment receipt
        
        Args:
            payment: Payment object
            event: Event object
            
        Returns:
            str: Path to generated QR code image
        """
        try:
            # Create QR code data
            qr_data = {
                'type': 'payment_receipt',
                'payment_id': payment.id,
                'event_id': event.id,
                'transaction_id': payment.transaction_id,
                'amount': payment.amount,
                'payment_type': payment.payment_type,
                'payment_method': payment.payment_method,
                'status': payment.status,
                'event_title': event.title,
                'generated_at': datetime.now().isoformat()
            }
            
            # Convert to JSON string
            import json
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=self.app.config.get('QR_CODE_BOX_SIZE', 10),
                border=self.app.config.get('QR_CODE_BORDER', 4),
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Add text overlay
            qr_img = self._add_text_overlay(qr_img, payment.transaction_id, f"PAYMENT ${payment.amount}", event.title)
            
            # Save QR code
            filename = f"payment_{payment.transaction_id}.png"
            filepath = os.path.join(self.app.config.get('QR_CODE_OUTPUT_DIR', 'static/qrcodes'), filename)
            qr_img.save(filepath)
            
            logger.info(f"Generated QR code for payment {payment.transaction_id}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for payment {payment.transaction_id}: {str(e)}")
            return None
    
    def generate_event_checkin_qr(self, event):
        """
        Generate QR code for event check-in station
        
        Args:
            event: Event object
            
        Returns:
            str: Path to generated QR code image
        """
        try:
            # Create QR code data
            qr_data = {
                'type': 'event_checkin',
                'event_id': event.id,
                'event_title': event.title,
                'venue': event.venue,
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat(),
                'generated_at': datetime.now().isoformat()
            }
            
            # Convert to JSON string
            import json
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=self.app.config.get('QR_CODE_BOX_SIZE', 10),
                border=self.app.config.get('QR_CODE_BORDER', 4),
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Add text overlay
            qr_img = self._add_text_overlay(qr_img, f"CHECKIN-{event.id}", f"Check-in: {event.title}", event.venue)
            
            # Save QR code
            filename = f"checkin_{event.id}.png"
            filepath = os.path.join(self.app.config.get('QR_CODE_OUTPUT_DIR', 'static/qrcodes'), filename)
            qr_img.save(filepath)
            
            logger.info(f"Generated QR code for event check-in: {event.title}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for event check-in {event.title}: {str(e)}")
            return None
    
    def _add_text_overlay(self, qr_img, code_text, title_text, subtitle_text=""):
        """
        Add text overlay to QR code image
        
        Args:
            qr_img: PIL Image object
            code_text: Text to display as code
            title_text: Title text
            subtitle_text: Subtitle text
            
        Returns:
            PIL Image object with text overlay
        """
        try:
            # Convert to RGB mode for better text rendering
            qr_img = qr_img.convert('RGB')
            
            # Create a new image with space for text
            img_width, img_height = qr_img.size
            new_height = img_height + 80  # Add space for text
            new_img = Image.new('RGB', (img_width, new_height), 'white')
            
            # Paste QR code on the new image
            new_img.paste(qr_img, (0, 0))
            
            # Create drawing context
            draw = ImageDraw.Draw(new_img)
            
            # Try to use a default font, fall back to basic font
            try:
                font_large = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add code text
            code_bbox = draw.textbbox((0, 0), code_text, font=font_large)
            code_width = code_bbox[2] - code_bbox[0]
            draw.text(((img_width - code_width) // 2, img_height + 10), code_text, font=font_large, fill='black')
            
            # Add title text
            if title_text:
                # Truncate title if too long
                if len(title_text) > 30:
                    title_text = title_text[:27] + "..."
                
                title_bbox = draw.textbbox((0, 0), title_text, font=font_small)
                title_width = title_bbox[2] - title_bbox[0]
                draw.text(((img_width - title_width) // 2, img_height + 35), title_text, font=font_small, fill='black')
            
            # Add subtitle text
            if subtitle_text:
                if len(subtitle_text) > 40:
                    subtitle_text = subtitle_text[:37] + "..."
                
                subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_small)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                draw.text(((img_width - subtitle_width) // 2, img_height + 55), subtitle_text, font=font_small, fill='gray')
            
            return new_img
            
        except Exception as e:
            logger.error(f"Failed to add text overlay: {str(e)}")
            return qr_img  # Return original image if text overlay fails
    
    def decode_qr_code(self, qr_image_path):
        """
        Decode QR code from image file
        
        Args:
            qr_image_path: Path to QR code image file
            
        Returns:
            dict: Decoded QR code data
        """
        try:
            import json
            from PIL import Image
            
            # Open image file
            img = Image.open(qr_image_path)
            
            # Decode QR code
            from pyzbar.pyzbar import decode
            decoded_objects = decode(img)
            
            if decoded_objects:
                qr_data = json.loads(decoded_objects[0].data.decode('utf-8'))
                return qr_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to decode QR code from {qr_image_path}: {str(e)}")
            return None
    
    def validate_qr_code(self, qr_data, expected_type=None):
        """
        Validate QR code data
        
        Args:
            qr_data: Decoded QR code data
            expected_type: Expected QR code type
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check if QR data is a dictionary
            if not isinstance(qr_data, dict):
                return False, "Invalid QR code format"
            
            # Check required fields
            required_fields = ['type', 'generated_at']
            for field in required_fields:
                if field not in qr_data:
                    return False, f"Missing required field: {field}"
            
            # Check QR code type if specified
            if expected_type and qr_data.get('type') != expected_type:
                return False, f"Invalid QR code type. Expected: {expected_type}, Got: {qr_data.get('type')}"
            
            # Check if QR code is expired (24 hours validity)
            generated_at = datetime.fromisoformat(qr_data['generated_at'])
            if datetime.now() - generated_at > timedelta(hours=24):
                return False, "QR code has expired"
            
            return True, "Valid QR code"
            
        except Exception as e:
            logger.error(f"Failed to validate QR code: {str(e)}")
            return False, f"Validation error: {str(e)}"

# Global QR service instance
qr_service = QRService()