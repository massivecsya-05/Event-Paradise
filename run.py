#!/usr/bin/env python3
"""
Events Paradise Event Management System - Enhanced Version
Startup Script

This script initializes and runs the enhanced Flask application with all integrations.
"""

import os
import sys
from app import app, db, init_db, socketio

def main():
    """Main function to run the enhanced application"""
    print("=" * 80)
    print("Events Paradise - Event Management System (Enhanced Version)")
    print("=" * 80)
    print()
    print("Enhanced Features:")
    print("✓ Email notifications (Flask-Mail)")
    print("✓ SMS notifications (Twilio)")
    print("✓ QR code generation for tickets")
    print("✓ Google Calendar integration")
    print("✓ Stripe payment processing")
    print("✓ Real-time notifications (WebSocket)")
    print("✓ Automated scheduled tasks")
    print("✓ Data export functionality")
    print("✓ File upload handling")
    print("✓ Comprehensive analytics")
    print()
    
    # Check for required environment variables
    print("Checking configuration...")
    
    required_vars = [
        'SECRET_KEY',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Warning: The following environment variables are not set:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Some features may not work properly without these variables.")
        print("Please set them in your .env file or environment.")
        print()
    else:
        print("✓ All required environment variables are set.")
        print()
    
    # Initialize the database
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
    
    # Create necessary directories
    print("Creating directories...")
    try:
        directories = [
            'instance/uploads/images',
            'instance/uploads/documents',
            'instance/uploads/profiles',
            'instance/uploads/events',
            'instance/uploads/vendors',
            'instance/uploads/temp',
            'instance/exports',
            'static/qrcodes'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        print("✓ Directories created successfully")
    except Exception as e:
        print(f"✗ Error creating directories: {e}")
        sys.exit(1)
    
    print()
    print("Starting enhanced web server...")
    print("Access the application at: http://localhost:5000")
    print("Default admin login: admin / admin123")
    print()
    print("Available Features:")
    print("• Real-time notifications and updates")
    print("• Email and SMS notifications")
    print("• QR code ticketing")
    print("• Stripe payment processing")
    print("• Google Calendar integration")
    print("• Automated reminders and reports")
    print("• Data export (CSV, Excel, PDF)")
    print("• File upload and management")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 80)
    
    try:
        # Run the enhanced application with SocketIO
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()