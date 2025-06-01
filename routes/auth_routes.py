"""
Routes d'authentification avec validation par email
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import os

# Import des services
from modules.email_service import email_service
from models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page et traitement d'inscription avec validation email"""
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        data = request.get_json()
        
        # Validation des données
        if not all([data.get('email'), data.get('password'), data.get('name')]):
            return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires'})
        
        email = data['email'].lower().strip()
        name = data['name'].strip()
        password = data['password']
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Un compte existe déjà avec cet email'})
        
        # Créer le nouvel utilisateur
        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            plan=data.get('plan', 'free'),
            is_email_verified=False
        )
        
        # Générer le token de validation
        token = user.generate_verification_token()
        
        # Sauvegarder en base
        db.session.add(user)
        db.session.commit()
        
        # Créer le lien de validation
        base_url = request.url_root.rstrip('/')
        validation_link = f"{base_url}/auth/verify-email/{token}"
        
        # Envoyer l'email de validation
        email_sent = email_service.send_validation_email(
            to_email=email,
            user_name=name,
            validation_link=validation_link
        )
        
        if email_sent:
            return jsonify({
                'success': True, 
                'message': 'Inscription réussie ! Vérifiez votre email pour activer votre compte.',
                'redirect': '/auth/email-sent'
            })
        else:
            # Si l'email n'a pas pu être envoyé, supprimer l'utilisateur
            db.session.delete(user)
            db.session.commit()
            return jsonify({
                'success': False, 
                'error': 'Erreur lors de l\'envoi de l\'email de validation. Veuillez réessayer.'
            })
        
        # Configuration du plan premium/lifetime si nécessaire
        if data.get('plan') == 'premium':
            user.subscription_end = datetime.utcnow() + timedelta(days=30)
        elif data.get('plan') == 'lifetime':
            user.plan = 'lifetime'
        
        db.session.commit()
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de l\'inscription: {str(e)}'})

@auth_bp.route('/email-sent')
def email_sent():
    """Page de confirmation d'envoi d'email"""
    return render_template('email_sent.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Validation de l'email avec le token"""
    try:
        # Trouver l'utilisateur avec ce token
        user = User.query.filter_by(email_verification_token=token).first()
        
        if not user:
            flash('Lien de validation invalide.', 'error')
            return redirect('/auth/login')
        
        if user.is_verification_token_valid(token):
            # Valider l'email
            user.verify_email()
            db.session.commit()
            
            # Envoyer l'email de bienvenue
            email_service.send_welcome_email(user.email, user.name)
            
            flash('Email validé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect('/auth/login')
        else:
            flash('Le lien de validation a expiré. Veuillez vous réinscrire.', 'error')
            return redirect('/auth/register')
            
    except Exception as e:
        flash('Erreur lors de la validation. Veuillez réessayer.', 'error')
        return redirect('/auth/register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page et traitement de connexion"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Vérifier les identifiants
        user = users_db.get(email)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'success': False, 'error': 'Identifiants incorrects'})
        
        if not user['is_active']:
            return jsonify({'success': False, 'error': 'Compte désactivé'})
        
        # Créer une session
        session['user_id'] = user['id']
        session['user_email'] = email
        session['user_plan'] = user['plan']
        
        return jsonify({
            'success': True,
            'message': 'Connexion réussie',
            'user_id': user['id'],
            'plan': user['plan']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur de connexion: {str(e)}'})

@auth_bp.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('main.landing'))

@auth_bp.route('/profile')
def profile():
    """Page de profil utilisateur"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = users_db.get(session['user_email'])
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('profile.html', user=user)

@auth_bp.route('/upgrade', methods=['POST'])
def upgrade_plan():
    """Mise à niveau du plan utilisateur"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Non connecté'})
    
    try:
        data = request.get_json()
        new_plan = data.get('plan')
        
        if new_plan not in ['premium', 'lifetime']:
            return jsonify({'success': False, 'error': 'Plan invalide'})
        
        user = users_db.get(session['user_email'])
        if not user:
            return jsonify({'success': False, 'error': 'Utilisateur introuvable'})
        
        # Simulation du paiement (ici on intégrerait Stripe)
        # Pour l'instant, on met à jour directement
        user['plan'] = new_plan
        if new_plan == 'premium':
            user['subscription_end'] = datetime.now() + timedelta(days=30)
        elif new_plan == 'lifetime':
            user['subscription_end'] = datetime.now() + timedelta(days=36500)
        
        session['user_plan'] = new_plan
        
        return jsonify({
            'success': True,
            'message': f'Plan mis à niveau vers {new_plan}',
            'new_plan': new_plan
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur de mise à niveau: {str(e)}'})

def check_plan_access(required_plan='free'):
    """Vérifie si l'utilisateur a accès à une fonctionnalité"""
    if 'user_id' not in session:
        return False
    
    user = users_db.get(session['user_email'])
    if not user:
        return False
    
    user_plan = user['plan']
    
    # Hiérarchie des plans
    plan_hierarchy = {'free': 0, 'premium': 1, 'lifetime': 2}
    
    if plan_hierarchy.get(user_plan, 0) >= plan_hierarchy.get(required_plan, 0):
        # Vérifier si l'abonnement est encore valide
        if user_plan != 'free' and user['subscription_end']:
            return datetime.now() <= user['subscription_end']
        return True
    
    return False

def check_daily_limits():
    """Vérifie les limites quotidiennes pour les utilisateurs gratuits"""
    if 'user_id' not in session:
        return False, "Non connecté"
    
    user = users_db.get(session['user_email'])
    if not user:
        return False, "Utilisateur introuvable"
    
    if user['plan'] != 'free':
        return True, "Plan premium"
    
    # Réinitialiser le compteur quotidien si nécessaire
    today = datetime.now().date()
    last_calc_date = user['last_calculation_date']
    
    if not last_calc_date or last_calc_date.date() != today:
        user['calculations_today'] = 0
        user['last_calculation_date'] = datetime.now()
    
    # Limite pour les utilisateurs gratuits: 5 calculs par jour
    if user['calculations_today'] >= 5:
        return False, "Limite quotidienne atteinte (5 calculs/jour). Passez au premium pour des calculs illimités."
    
    return True, "OK"

def increment_daily_usage():
    """Incrémente le compteur d'utilisation quotidienne"""
    if 'user_id' not in session:
        return
    
    user = users_db.get(session['user_email'])
    if user and user['plan'] == 'free':
        user['calculations_today'] += 1
        user['last_calculation_date'] = datetime.now()