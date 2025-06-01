"""
Routes principales de l'application
"""

from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """Page d'accueil publique"""
    return render_template('landing.html')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard - REDIRECTION FORCÉE vers login"""
    # TOUJOURS rediriger vers login
    return redirect('/auth/login')

@main_bp.route('/pricing')
def pricing():
    """Page de tarification"""
    return render_template('pricing.html')

@main_bp.route('/demo')
def demo():
    """Page de démonstration"""
    return render_template('demo.html')

@main_bp.route('/features')
def features():
    """Page des fonctionnalités"""
    return render_template('features.html')

@main_bp.route('/terms')
def terms():
    """Conditions d'utilisation"""
    return render_template('legal/terms.html')

@main_bp.route('/privacy')
def privacy():
    """Politique de confidentialité"""
    return render_template('legal/privacy.html')

@main_bp.route('/contact')
def contact():
    """Page de contact"""
    return render_template('contact.html')

@main_bp.route('/support')
def support():
    """Page de support"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = users_db.get(session['user_email'])
    return render_template('support.html', user=user)

@main_bp.route('/settings')
def settings():
    """Page des paramètres utilisateur"""
    if 'user_id' not in session:
        return redirect('/auth/login')
    
    # Créer un objet utilisateur simple basé sur la session
    user = {
        'name': session.get('user_name', 'Utilisateur'),
        'email': session.get('user_email', ''),
        'plan': session.get('user_plan', 'free')
    }
    return render_template('settings.html', user=user)