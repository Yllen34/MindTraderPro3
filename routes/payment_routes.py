"""
Routes de paiement Stripe pour les plans premium
"""

import os
import stripe
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import User
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)

# Configuration Stripe

# Prix des plans (en centimes)
PLAN_PRICES = {
    'premium': 999,  # 9.99€
    'lifetime': 14900  # 149€
}

@payment_bp.route('/checkout/<plan>')
def checkout(plan):
    """Page de checkout pour un plan spécifique"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if plan not in PLAN_PRICES:
        return "Plan invalide", 400
    
    user = users_db.get(session.get('user_email', ''))
    if not user:
        return redirect(url_for('auth.login'))
    
    # Calculer le prix
    price = PLAN_PRICES[plan]
    
    return render_template('payment/checkout.html', 
                         plan=plan, 
                         price=price,
                         stripe_key=STRIPE_PUBLISHABLE_KEY,
                         user=user)

@payment_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Créer une session de checkout Stripe"""
    try:
        data = request.get_json()
        plan = data.get('plan')
        
        if not plan or plan not in PLAN_PRICES:
            return jsonify({'error': 'Plan invalide'}), 400
        
        if 'user_id' not in session:
            return jsonify({'error': 'Non connecté'}), 401
        
        user = users_db.get(session.get('user_email', ''))
        if not user:
            return jsonify({'error': 'Utilisateur introuvable'}), 404
        
        # Déterminer le mode de paiement
        mode = 'subscription' if plan == 'premium' else 'payment'
        
        # Créer la session Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Trading Calculator Pro - {plan.title()}',
                        'description': 'Accès complet à toutes les fonctionnalités avancées'
                    },
                    'unit_amount': PLAN_PRICES[plan],
                    'recurring': {'interval': 'month'} if plan == 'premium' else None,
                },
                'quantity': 1,
            }],
            mode=mode,
            success_url=request.url_root + f'payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan}',
            cancel_url=request.url_root + 'payment/cancel',
            customer_email=user['email'],
            metadata={
                'user_id': user['id'],
                'plan': plan
            }
        )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/success')
def payment_success():
    """Page de succès après paiement"""
    session_id = request.args.get('session_id')
    plan = request.args.get('plan')
    
    if not session_id:
        return redirect(url_for('main.dashboard'))
    
    try:
        # Récupérer la session Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Mettre à jour le plan utilisateur
            user_id = checkout_session.metadata.get('user_id')
            user_email = None
            
            # Trouver l'utilisateur par ID
            for email, user_data in users_db.items():
                if user_data['id'] == user_id:
                    user_email = email
                    break
            
            if user_email and user_email in users_db:
                user = users_db[user_email]
                user['plan'] = plan
                
                if plan == 'premium':
                    user['subscription_end'] = datetime.now() + timedelta(days=30)
                elif plan == 'lifetime':
                    user['subscription_end'] = datetime.now() + timedelta(days=36500)  # 100 ans
                
                # Mettre à jour la session
                session['user_plan'] = plan
                
                return render_template('payment/success.html', plan=plan)
        
        return render_template('payment/error.html', error="Paiement non confirmé")
        
    except Exception as e:
        return render_template('payment/error.html', error=str(e))

@payment_bp.route('/cancel')
def payment_cancel():
    """Page d'annulation de paiement"""
    return render_template('payment/cancel.html')

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour gérer les événements"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Gérer les différents types d'événements
    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        
        # Traitement du paiement réussi
        user_id = session_data['metadata'].get('user_id')
        plan = session_data['metadata'].get('plan')
        
        # Mettre à jour l'utilisateur dans la base de données
        # (logique similaire à payment_success)
        
    elif event['type'] == 'invoice.payment_succeeded':
        # Renouvellement d'abonnement réussi
        pass
    
    elif event['type'] == 'invoice.payment_failed':
        # Échec de paiement
        pass
    
    return 'Success', 200

@payment_bp.route('/manage-subscription')
def manage_subscription():
    """Page de gestion d'abonnement"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = users_db.get(session.get('user_email', ''))
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('payment/manage.html', user=user)