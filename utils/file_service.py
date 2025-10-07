"""
File Service Module

This module handles file upload functionality:
- Image uploads
- Document uploads
- File validation
- File storage
- File retrieval
"""

import os
import logging
import uuid
from datetime import datetime
from flask import current_app, request, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import magic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileService:
    """File service class for handling file uploads"""
    
    def __init__(self, app=None):
        """Initialize the file service"""
        self.app = app
        self.allowed_extensions = {
            # Images
            'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
            # Documents
            'pdf', 'doc', 'docx', 'txt', 'rtf',
            # Spreadsheets
            'xls', 'xlsx', 'csv',
            # Presentations
            'ppt', 'pptx',
            # Archives
            'zip', 'rar', '7z'
        }
        self.max_file_size = 16 * 1024 * 1024  # 16MB
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Create upload directories
        self.upload_dirs = {
            'images': os.path.join(app.instance_path, 'uploads', 'images'),
            'documents': os.path.join(app.instance_path, 'uploads', 'documents'),
            'profiles': os.path.join(app.instance_path, 'uploads', 'profiles'),
            'events': os.path.join(app.instance_path, 'uploads', 'events'),
            'vendors': os.path.join(app.instance_path, 'uploads', 'vendors'),
            'temp': os.path.join(app.instance_path, 'uploads', 'temp')
        }
        
        # Create directories if they don't exist
        for directory in self.upload_dirs.values():
            os.makedirs(directory, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_file_type(self, filename):
        """Get file type category"""
        extension = filename.rsplit('.', 1)[1].lower()
        
        image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        document_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
        spreadsheet_extensions = {'xls', 'xlsx', 'csv'}
        presentation_extensions = {'ppt', 'pptx'}
        archive_extensions = {'zip', 'rar', '7z'}
        
        if extension in image_extensions:
            return 'images'
        elif extension in document_extensions:
            return 'documents'
        elif extension in spreadsheet_extensions:
            return 'documents'
        elif extension in presentation_extensions:
            return 'documents'
        elif extension in archive_extensions:
            return 'documents'
        else:
            return 'documents'
    
    def validate_file(self, file_storage):
        """Validate uploaded file"""
        try:
            # Check file size
            file_storage.seek(0, os.SEEK_END)
            file_size = file_storage.tell()
            file_storage.seek(0)
            
            if file_size > self.max_file_size:
                return False, f"File size exceeds maximum limit of {self.max_file_size // (1024 * 1024)}MB"
            
            # Check file extension
            filename = secure_filename(file_storage.filename)
            if not self.allowed_file(filename):
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            
            # Check file content type
            file_content = file_storage.read(1024)  # Read first 1KB for content type detection
            file_storage.seek(0)
            
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                allowed_mime_types = {
                    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                    'application/pdf', 'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-powerpoint',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'text/plain', 'application/zip', 'application/x-rar-compressed'
                }
                
                if mime_type not in allowed_mime_types:
                    return False, f"File content type {mime_type} not allowed"
                    
            except Exception as e:
                logger.warning(f"Could not detect MIME type: {str(e)}")
            
            return True, "File is valid"
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"File validation error: {str(e)}"
    
    def save_file(self, file_storage, file_type='documents', custom_filename=None):
        """
        Save uploaded file
        
        Args:
            file_storage: Flask file storage object
            file_type (str): Type of file (images, documents, etc.)
            custom_filename (str): Custom filename (optional)
            
        Returns:
            dict: File information or None if failed
        """
        try:
            # Validate file
            is_valid, message = self.validate_file(file_storage)
            if not is_valid:
                logger.error(f"File validation failed: {message}")
                return None
            
            # Get original filename
            original_filename = secure_filename(file_storage.filename)
            
            # Generate unique filename
            if custom_filename:
                filename = f"{custom_filename}_{uuid.uuid4().hex[:8]}_{original_filename}"
            else:
                filename = f"{uuid.uuid4().hex[:8]}_{original_filename}"
            
            # Determine file path
            if file_type in self.upload_dirs:
                file_path = os.path.join(self.upload_dirs[file_type], filename)
            else:
                file_path = os.path.join(self.upload_dirs['documents'], filename)
            
            # Save file
            file_storage.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            
            # If it's an image, create thumbnail
            thumbnail_path = None
            if file_type == 'images':
                thumbnail_path = self.create_thumbnail(file_path)
            
            file_info = {
                'filename': filename,
                'original_filename': original_filename,
                'file_path': file_path,
                'file_type': file_type,
                'file_size': file_size,
                'file_extension': file_extension,
                'thumbnail_path': thumbnail_path,
                'uploaded_at': datetime.now().isoformat()
            }
            
            logger.info(f"File saved successfully: {filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return None
    
    def create_thumbnail(self, image_path, size=(200, 200)):
        """
        Create thumbnail for image
        
        Args:
            image_path (str): Path to original image
            size (tuple): Thumbnail size (width, height)
            
        Returns:
            str: Path to thumbnail or None if failed
        """
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Generate thumbnail filename
                directory = os.path.dirname(image_path)
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                thumbnail_filename = f"{name}_thumb{ext}"
                thumbnail_path = os.path.join(directory, thumbnail_filename)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                logger.info(f"Thumbnail created: {thumbnail_filename}")
                return thumbnail_path
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """
        Delete file and its thumbnail
        
        Args:
            file_path (str): Path to file
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Delete main file
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
            
            # Delete thumbnail if exists
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            thumbnail_path = os.path.join(directory, f"{name}_thumb{ext}")
            
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"Thumbnail deleted: {thumbnail_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def get_file_url(self, file_path):
        """
        Get URL for accessing file
        
        Args:
            file_path (str): Path to file
            
        Returns:
            str: URL for file access
        """
        try:
            # Extract relative path from instance path
            relative_path = os.path.relpath(file_path, self.app.instance_path)
            return f"/uploads/{relative_path}"
            
        except Exception as e:
            logger.error(f"Failed to get file URL: {str(e)}")
            return None
    
    def serve_file(self, file_path):
        """
        Serve file for download
        
        Args:
            file_path (str): Path to file
            
        Returns:
            Flask response: File download response
        """
        try:
            if os.path.exists(file_path):
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                return send_from_directory(directory, filename, as_attachment=True)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to serve file {file_path}: {str(e)}")
            return None
    
    def cleanup_old_files(self, days=7):
        """
        Clean up old temporary files
        
        Args:
            days (int): Number of days to keep files
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            temp_dir = self.upload_dirs.get('temp')
            if not temp_dir:
                return 0
            
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old temporary files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0
    
    def get_file_info(self, file_path):
        """
        Get file information
        
        Args:
            file_path (str): Path to file
            
        Returns:
            dict: File information
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            filename = os.path.basename(file_path)
            file_size = stat.st_size
            created_at = datetime.fromtimestamp(stat.st_ctime)
            modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            # Get MIME type
            try:
                mime_type = magic.from_file(file_path, mime=True)
            except:
                mime_type = 'application/octet-stream'
            
            return {
                'filename': filename,
                'file_path': file_path,
                'file_size': file_size,
                'mime_type': mime_type,
                'created_at': created_at.isoformat(),
                'modified_at': modified_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None
    
    def upload_event_image(self, event_id, file_storage):
        """
        Upload event image
        
        Args:
            event_id (int): Event ID
            file_storage: Flask file storage object
            
        Returns:
            dict: File information or None if failed
        """
        try:
            custom_filename = f"event_{event_id}"
            file_info = self.save_file(file_storage, 'events', custom_filename)
            
            if file_info:
                logger.info(f"Event image uploaded for event {event_id}")
                return file_info
            else:
                logger.error(f"Failed to upload event image for event {event_id}")
                return None
                
        except Exception as e:
            logger.error(f"Event image upload error: {str(e)}")
            return None
    
    def upload_vendor_document(self, vendor_id, file_storage):
        """
        Upload vendor document
        
        Args:
            vendor_id (int): Vendor ID
            file_storage: Flask file storage object
            
        Returns:
            dict: File information or None if failed
        """
        try:
            custom_filename = f"vendor_{vendor_id}"
            file_info = self.save_file(file_storage, 'vendors', custom_filename)
            
            if file_info:
                logger.info(f"Vendor document uploaded for vendor {vendor_id}")
                return file_info
            else:
                logger.error(f"Failed to upload vendor document for vendor {vendor_id}")
                return None
                
        except Exception as e:
            logger.error(f"Vendor document upload error: {str(e)}")
            return None
    
    def upload_profile_image(self, user_id, file_storage):
        """
        Upload user profile image
        
        Args:
            user_id (int): User ID
            file_storage: Flask file storage object
            
        Returns:
            dict: File information or None if failed
        """
        try:
            custom_filename = f"profile_{user_id}"
            file_info = self.save_file(file_storage, 'profiles', custom_filename)
            
            if file_info:
                logger.info(f"Profile image uploaded for user {user_id}")
                return file_info
            else:
                logger.error(f"Failed to upload profile image for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Profile image upload error: {str(e)}")
            return None

# Global file service instance
file_service = FileService()