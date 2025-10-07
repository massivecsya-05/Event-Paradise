"""
Events Paradise Event Management System - Enhanced Version

This is the enhanced version with all integrations:
- Email notifications (Flask-Mail)
- SMS notifications (Twilio)
- QR code generation
- Calendar integration (Google Calendar)
- Payment processing (Stripe)
- Real-time notifications (WebSocket)
- Scheduled tasks (APScheduler)
- Export functionality
- File upload
- Automated reminders
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
from functools import wraps
from config import get_config

# Import utility services
from utils.email_service import email_service, mail
from utils.sms_service import sms_service
from utils.qr_service import qr_service
from utils.payment_service import payment_service
from utils.calender_service import calendar_service
from utils.notification_service import notification_service, socketio
from utils.scheduler_service import scheduler_service
from utils.export_service import export_service

# Initialize Flask app with configuration
config = get_config()
app = Flask(__name__, instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'))
app.config.from_object(config)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize services
mail.init_app(app)
email_service.init_app(app)
sms_service.init_app(app)
qr_service.init_app(app)
payment_service.init_app(app)
calendar_service.init_app(app)
notification_service.init_app(app)
scheduler_service.init_app(app)
export_service.init_app(app)

# Database Models (unchanged from original)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    events = db.relationship('Event', backref='organizer', lazy=True)
    vendors = db.relationship('Vendor', backref='contact_person', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    venue = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='planned')
    budget = db.Column(db.Float, default=0.0)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    calendar_event_id = db.Column(db.String(100))  # Google Calendar event ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    guests = db.relationship('Guest', backref='event', lazy=True, cascade='all, delete-orphan')
    vendors = db.relationship('Vendor', backref='event', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='event', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='event', lazy=True, cascade='all, delete-orphan')

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    rsvp_status = db.Column(db.String(20), default='pending')
    check_in_status = db.Column(db.Boolean, default=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True)
    qr_code_path = db.Column(db.String(200))  # Path to QR code image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    contact_person_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    contract_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    stripe_payment_intent_id = db.Column(db.String(100))  # Stripe PaymentIntent ID
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Functions
def generate_ticket_number(event_id, guest_count):
    """Generate unique ticket number"""
    return f"TKT-{event_id}-{guest_count + 1:04d}"

def generate_transaction_id(event_id, payment_count):
    """Generate unique transaction ID"""
    return f"TXN-{event_id}-{payment_count + 1:04d}"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_events = Event.query.filter_by(organizer_id=current_user.id).all()
    upcoming_events = Event.query.filter(
        Event.organizer_id == current_user.id,
        Event.start_date > datetime.now(),
        Event.status == 'planned'
    ).all()
    
    return render_template('dashboard.html', 
                         events=user_events, 
                         upcoming_events=upcoming_events)

# Event Management Routes
@app.route('/events')
@login_required
def events():
    user_events = Event.query.filter_by(organizer_id=current_user.id).all()
    return render_template('events.html', events=user_events)

@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        venue = request.form['venue']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M')
        budget = float(request.form['budget'])
        
        new_event = Event(
            title=title,
            description=description,
            venue=venue,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            organizer_id=current_user.id
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        # Send notification
        notification_service.send_event_notification(new_event, 'event_created')
        
        # Sync with Google Calendar
        calendar_result = calendar_service.add_event_to_calendar(new_event)
        if calendar_result.get('success'):
            new_event.calendar_event_id = calendar_result.get('event_id')
            db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('create_event.html')

@app.route('/events/<int:event_id>')
@login_required
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is the organizer or admin
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    guests = Guest.query.filter_by(event_id=event_id).all()
    vendors = Vendor.query.filter_by(event_id=event_id).all()
    payments = Payment.query.filter_by(event_id=event_id).all()
    
    return render_template('event_details.html', 
                         event=event, 
                         guests=guests, 
                         vendors=vendors, 
                         payments=payments)

# Guest Management Routes
@app.route('/events/<int:event_id>/guests', methods=['GET', 'POST'])
@login_required
def manage_guests(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')
        
        # Generate unique ticket number
        guest_count = Guest.query.filter_by(event_id=event_id).count()
        ticket_number = generate_ticket_number(event_id, guest_count)
        
        new_guest = Guest(
            name=name,
            email=email,
            phone=phone,
            event_id=event_id,
            ticket_number=ticket_number
        )
        
        db.session.add(new_guest)
        db.session.commit()
        
        # Generate QR code
        qr_path = qr_service.generate_guest_ticket_qr(new_guest, event)
        if qr_path:
            new_guest.qr_code_path = qr_path
            db.session.commit()
        
        # Send email invitation
        email_service.send_event_invitation(new_guest, event)
        
        # Send SMS if phone number provided
        if phone:
            sms_service.send_welcome_message(new_guest, event)
        
        # Send notification to organizer
        notification_service.send_guest_notification(new_guest, event, 'guest_registered')
        
        flash('Guest added successfully!', 'success')
        return redirect(url_for('manage_guests', event_id=event_id))
    
    guests = Guest.query.filter_by(event_id=event_id).all()
    return render_template('manage_guests.html', event=event, guests=guests)

@app.route('/events/<int:event_id>/guests/<int:guest_id>/checkin', methods=['POST'])
@login_required
def check_in_guest(event_id, guest_id):
    guest = Guest.query.get_or_404(guest_id)
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    guest.check_in_status = True
    db.session.commit()
    
    # Send check-in notification
    sms_service.send_check_in_notification(guest, event)
    notification_service.send_guest_notification(guest, event, 'guest_checked_in')
    
    flash('Guest checked in successfully!', 'success')
    return redirect(url_for('manage_guests', event_id=event_id))

@app.route('/events/<int:event_id>/guests/<int:guest_id>/rsvp', methods=['POST'])
@login_required
def update_rsvp(event_id, guest_id):
    guest = Guest.query.get_or_404(guest_id)
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    rsvp_status = request.json.get('rsvp_status')
    if rsvp_status in ['confirmed', 'declined']:
        guest.rsvp_status = rsvp_status
        db.session.commit()
        
        # Send RSVP confirmation
        email_service.send_rsvp_confirmation(guest, event, rsvp_status)
        sms_service.send_rsvp_confirmation(guest, event, rsvp_status)
        
        # Send notification
        notification_service.send_guest_notification(guest, event, f'guest_rsvp_{rsvp_status}')
        
        return jsonify({'success': True, 'rsvp_status': rsvp_status})
    
    return jsonify({'error': 'Invalid RSVP status'}), 400

# Vendor Management Routes
@app.route('/events/<int:event_id>/vendors', methods=['GET', 'POST'])
@login_required
def manage_vendors(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        name = request.form['name']
        service_type = request.form['service_type']
        email = request.form.get('email')
        phone = request.form.get('phone')
        contract_amount = float(request.form.get('contract_amount', 0))
        
        new_vendor = Vendor(
            name=name,
            service_type=service_type,
            email=email,
            phone=phone,
            contract_amount=contract_amount,
            event_id=event_id
        )
        
        db.session.add(new_vendor)
        db.session.commit()
        
        # Send vendor welcome email
        email_service.send_vendor_welcome(new_vendor, event)
        
        # Generate QR code for vendor badge
        qr_service.generate_vendor_badge_qr(new_vendor, event)
        
        flash('Vendor added successfully!', 'success')
        return redirect(url_for('manage_vendors', event_id=event_id))
    
    vendors = Vendor.query.filter_by(event_id=event_id).all()
    return render_template('manage_vendors.html', event=event, vendors=vendors)

# Payment Processing Routes
@app.route('/events/<int:event_id>/payments', methods=['GET', 'POST'])
@login_required
def manage_payments(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        payment_type = request.form['payment_type']
        payment_method = request.form['payment_method']
        
        # Generate transaction ID
        payment_count = Payment.query.filter_by(event_id=event_id).count()
        transaction_id = generate_transaction_id(event_id, payment_count)
        
        new_payment = Payment(
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_method,
            transaction_id=transaction_id,
            event_id=event_id,
            status='completed'
        )
        
        db.session.add(new_payment)
        db.session.commit()
        
        # Generate QR code for receipt
        qr_service.generate_payment_receipt_qr(new_payment, event)
        
        # Send payment notification
        notification_service.send_payment_notification(new_payment, event.organizer_id, 'payment_received')
        
        # Send payment receipt email
        if event.organizer.email:
            email_service.send_payment_receipt(new_payment, event, event.organizer.email)
        
        flash('Payment processed successfully!', 'success')
        return redirect(url_for('manage_payments', event_id=event_id))
    
    payments = Payment.query.filter_by(event_id=event_id).all()
    return render_template('manage_payments.html', event=event, payments=payments)

# Stripe Payment Integration
@app.route('/events/<int:event_id>/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    amount = data.get('amount')
    payment_type = data.get('payment_type', 'ticket')
    
    # Create Stripe PaymentIntent
    payment_intent = payment_service.create_payment_intent(
        amount=amount,
        payment_type=payment_type,
        metadata={'event_id': event_id, 'event_title': event.title}
    )
    
    if payment_intent:
        return jsonify(payment_intent)
    else:
        return jsonify({'error': 'Failed to create payment intent'}), 500

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    # Verify webhook signature
    event = payment_service.handle_webhook(payload, signature)
    
    if event and event.get('handled'):
        # Process the webhook event
        if event['event_type'] == 'payment_succeeded':
            # Update payment status in database
            payment_intent_id = event['payment_intent_id']
            amount = event['amount']
            metadata = event['metadata']
            
            # Find and update payment record
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                payment.status = 'completed'
                db.session.commit()
                
                # Send notifications
                notification_service.send_payment_notification(
                    payment, payment.event.organizer_id, 'payment_received'
                )
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error'}), 400

# Export Routes
@app.route('/events/<int:event_id>/export/guests/csv')
@login_required
def export_guests_csv(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    filepath = export_service.export_guests_to_csv(event_id)
    if filepath:
        return export_service.download_file(filepath)
    else:
        flash('Failed to export guests', 'danger')
        return redirect(url_for('manage_guests', event_id=event_id))

@app.route('/events/<int:event_id>/export/guests/excel')
@login_required
def export_guests_excel(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    filepath = export_service.export_guests_to_excel(event_id)
    if filepath:
        return export_service.download_file(filepath)
    else:
        flash('Failed to export guests', 'danger')
        return redirect(url_for('manage_guests', event_id=event_id))

@app.route('/events/<int:event_id>/export/report/pdf')
@login_required
def export_event_report(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('events'))
    
    filepath = export_service.generate_event_report_pdf(event_id)
    if filepath:
        return export_service.download_file(filepath)
    else:
        flash('Failed to generate report', 'danger')
        return redirect(url_for('event_details', event_id=event_id))

# Analytics and Reporting Routes
@app.route('/analytics')
@login_required
def analytics():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    total_events = Event.query.count()
    total_guests = Guest.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    
    events_by_month = db.session.query(
        db.func.strftime('%Y-%m', Event.start_date).label('month'),
        db.func.count(Event.id).label('count')
    ).group_by(db.func.strftime('%Y-%m', Event.start_date)).all()
    
    revenue_by_month = db.session.query(
        db.func.strftime('%Y-%m', Payment.created_at).label('month'),
        db.func.sum(Payment.amount).label('revenue')
    ).filter_by(status='completed').group_by(db.func.strftime('%Y-%m', Payment.created_at)).all()
    
    return render_template('analytics.html',
                         total_events=total_events,
                         total_guests=total_guests,
                         total_revenue=total_revenue,
                         events_by_month=events_by_month,
                         revenue_by_month=revenue_by_month)

# API Routes for real-time updates
@app.route('/api/events/<int:event_id>/status')
@login_required
def event_status(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    guest_count = Guest.query.filter_by(event_id=event_id).count()
    checked_in_count = Guest.query.filter_by(event_id=event_id, check_in_status=True).count()
    total_payments = db.session.query(db.func.sum(Payment.amount)).filter_by(event_id=event_id, status='completed').scalar() or 0
    
    return jsonify({
        'event_status': event.status,
        'guest_count': guest_count,
        'checked_in_count': checked_in_count,
        'total_payments': total_payments
    })

@app.route('/api/scheduler/status')
@login_required
def scheduler_status():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(scheduler_service.get_scheduler_status())

@app.route('/api/notifications/unread')
@login_required
def unread_notifications():
    notifications = notification_service.get_user_notifications(current_user.id)
    return jsonify({'notifications': notifications})

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@eventparadise.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()

# Shutdown handler
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Main execution
if __name__ == '__main__':
    init_db()
    
    # Create instance directory
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Run with SocketIO for real-time features
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)