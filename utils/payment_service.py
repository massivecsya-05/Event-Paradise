"""
Payment Service Module

This module handles payment processing using Stripe:
- Payment creation and processing
- Webhook handling
- Refund processing
- Payment verification
"""

import os
import logging
import stripe
from datetime import datetime
from flask import current_app, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentService:
    """Payment service class for handling Stripe payments"""
    
    def __init__(self, app=None):
        """Initialize the payment service"""
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Configure Stripe
        stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
        
        # Create Stripe products for different payment types
        self._create_stripe_products()
    
    def _create_stripe_products(self):
        """Create Stripe products for different payment types"""
        try:
            # Product for event tickets
            stripe.Product.create(
                name="Event Ticket",
                description="Payment for event ticket",
                metadata={"type": "ticket"}
            )
            
            # Product for vendor payments
            stripe.Product.create(
                name="Vendor Service",
                description="Payment for vendor services",
                metadata={"type": "vendor"}
            )
            
            # Product for event deposits
            stripe.Product.create(
                name="Event Deposit",
                description="Payment for event deposit",
                metadata={"type": "deposit"}
            )
            
            # Product for sponsorships
            stripe.Product.create(
                name="Event Sponsorship",
                description="Payment for event sponsorship",
                metadata={"type": "sponsorship"}
            )
            
            logger.info("Stripe products created successfully")
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe products: {str(e)}")
    
    def create_payment_intent(self, amount, currency='usd', payment_type='ticket', metadata=None):
        """
        Create a Stripe PaymentIntent
        
        Args:
            amount (float): Payment amount
            currency (str): Currency code (default: 'usd')
            payment_type (str): Type of payment (ticket, vendor, deposit, sponsorship)
            metadata (dict): Additional metadata
            
        Returns:
            dict: PaymentIntent data or None if failed
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            # Prepare metadata
            payment_metadata = {
                'payment_type': payment_type,
                'created_at': datetime.now().isoformat()
            }
            
            if metadata:
                payment_metadata.update(metadata)
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                payment_method_types=['card'],
                metadata=payment_metadata,
                description=f"{payment_type.title()} payment"
            )
            
            logger.info(f"Created PaymentIntent: {intent.id} for {amount} {currency}")
            return {
                'client_secret': intent.client_secret,
                'intent_id': intent.id,
                'amount': amount,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create PaymentIntent: {str(e)}")
            return None
    
    def confirm_payment(self, payment_intent_id):
        """
        Confirm a payment
        
        Args:
            payment_intent_id (str): Stripe PaymentIntent ID
            
        Returns:
            dict: Payment confirmation data or None if failed
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                return {
                    'success': True,
                    'payment_intent_id': intent.id,
                    'amount': intent.amount / 100,  # Convert back to dollars
                    'currency': intent.currency,
                    'payment_method': intent.payment_method_types[0] if intent.payment_method_types else 'card',
                    'metadata': intent.metadata
                }
            else:
                return {
                    'success': False,
                    'status': intent.status,
                    'error': 'Payment not successful'
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"Failed to confirm payment {payment_intent_id}: {str(e)}")
            return None
    
    def create_refund(self, payment_intent_id, amount=None, reason='requested_by_customer'):
        """
        Create a refund for a payment
        
        Args:
            payment_intent_id (str): Stripe PaymentIntent ID
            amount (float): Refund amount (None for full refund)
            reason (str): Refund reason
            
        Returns:
            dict: Refund data or None if failed
        """
        try:
            refund_data = {
                'payment_intent': payment_intent_id,
                'reason': reason
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info(f"Created refund: {refund.id} for PaymentIntent: {payment_intent_id}")
            return {
                'refund_id': refund.id,
                'amount': refund.amount / 100,  # Convert back to dollars
                'status': refund.status,
                'reason': refund.reason
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create refund for {payment_intent_id}: {str(e)}")
            return None
    
    def handle_webhook(self, payload, signature):
        """
        Handle Stripe webhook events
        
        Args:
            payload (bytes): Webhook payload
            signature (str): Stripe signature header
            
        Returns:
            dict: Webhook event data or None if invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info(f"Received webhook event: {event.type}")
            
            # Handle different event types
            if event.type == 'payment_intent.succeeded':
                return self._handle_payment_succeeded(event)
            elif event.type == 'payment_intent.payment_failed':
                return self._handle_payment_failed(event)
            elif event.type == 'charge.refunded':
                return self._handle_charge_refunded(event)
            else:
                logger.info(f"Unhandled webhook event type: {event.type}")
                return {'event_type': event.type, 'handled': False}
                
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return None
    
    def _handle_payment_succeeded(self, event):
        """Handle payment_intent.succeeded event"""
        try:
            payment_intent = event.data.object
            logger.info(f"Payment succeeded: {payment_intent.id}")
            
            return {
                'event_type': 'payment_succeeded',
                'payment_intent_id': payment_intent.id,
                'amount': payment_intent.amount / 100,
                'currency': payment_intent.currency,
                'metadata': payment_intent.metadata,
                'handled': True
            }
            
        except Exception as e:
            logger.error(f"Failed to handle payment succeeded event: {str(e)}")
            return None
    
    def _handle_payment_failed(self, event):
        """Handle payment_intent.payment_failed event"""
        try:
            payment_intent = event.data.object
            logger.error(f"Payment failed: {payment_intent.id}")
            
            return {
                'event_type': 'payment_failed',
                'payment_intent_id': payment_intent.id,
                'error': payment_intent.last_payment_error,
                'metadata': payment_intent.metadata,
                'handled': True
            }
            
        except Exception as e:
            logger.error(f"Failed to handle payment failed event: {str(e)}")
            return None
    
    def _handle_charge_refunded(self, event):
        """Handle charge.refunded event"""
        try:
            charge = event.data.object
            logger.info(f"Charge refunded: {charge.id}")
            
            return {
                'event_type': 'charge_refunded',
                'charge_id': charge.id,
                'amount_refunded': charge.amount_refunded / 100,
                'payment_intent_id': charge.payment_intent,
                'handled': True
            }
            
        except Exception as e:
            logger.error(f"Failed to handle charge refunded event: {str(e)}")
            return None
    
    def get_payment_status(self, payment_intent_id):
        """
        Get payment status
        
        Args:
            payment_intent_id (str): Stripe PaymentIntent ID
            
        Returns:
            dict: Payment status information
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'created': intent.created,
                'metadata': intent.metadata,
                'last_payment_error': intent.last_payment_error
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get payment status for {payment_intent_id}: {str(e)}")
            return None
    
    def create_test_payment(self, amount=10.00):
        """
        Create a test payment for development/testing
        
        Args:
            amount (float): Test payment amount
            
        Returns:
            dict: Test payment data
        """
        try:
            # Use Stripe test card
            test_card = 'pm_card_visa'
            
            # Create test PaymentMethod
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={'token': 'tok_visa'},  # Stripe test token
            )
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='usd',
                payment_method=payment_method.id,
                confirm=True,
                metadata={'test': 'true', 'created_at': datetime.now().isoformat()}
            )
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'amount': amount,
                'status': intent.status,
                'client_secret': intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create test payment: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global payment service instance
payment_service = PaymentService()