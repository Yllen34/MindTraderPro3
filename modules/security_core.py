"""
Module de sécurité central pour MindTraderPro
Gestion des sessions, CSRF, XSS, validation et chiffrement
"""

import os
import hashlib
import secrets
import logging
import bleach
from functools import wraps
from datetime import datetime, timedelta
from flask import session, request, abort, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Configuration du logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/security.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestionnaire de sécurité central"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 heure
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.failed_attempts = {}
        
    def generate_csrf_token(self):
        """Génère un token CSRF sécurisé"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token):
        """Valide le token CSRF"""
        return token and session.get('csrf_token') == token
    
    def hash_password(self, password):
        """Hash sécurisé du mot de passe"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_password(self, password, hash_value):
        """Vérifie le mot de passe"""
        return check_password_hash(hash_value, password)
    
    def sanitize_input(self, text):
        """Nettoie les entrées utilisateur contre XSS"""
        if not text:
            return ""
        
        # Nettoie le HTML malveillant
        allowed_tags = ['b', 'i', 'u', 'em', 'strong']
        clean_text = bleach.clean(text, tags=allowed_tags, strip=True)
        
        # Échappe les caractères spéciaux
        clean_text = clean_text.replace('<', '&lt;').replace('>', '&gt;')
        
        return clean_text
    
    def validate_email(self, email):
        """Valide le format email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password):
        """Valide la force du mot de passe"""
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        
        if not re.search(r'[0-9]', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\?]', password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"
        
        return True, "Mot de passe valide"
    
    def check_rate_limit(self, identifier, max_requests=10, time_window=60):
        """Vérifie les limites de taux"""
        now = datetime.now()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Nettoie les tentatives anciennes
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if now - attempt < timedelta(seconds=time_window)
        ]
        
        # Vérifie la limite
        if len(self.failed_attempts[identifier]) >= max_requests:
            return False
        
        # Ajoute la tentative actuelle
        self.failed_attempts[identifier].append(now)
        return True
    
    def log_security_event(self, event_type, details, user_id=None):
        """Log les événements de sécurité"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'user_id': user_id,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent') if request else 'unknown'
        }
        
        logger.warning(f"SECURITY_EVENT: {log_entry}")
    
    def encrypt_sensitive_data(self, data):
        """Chiffre les données sensibles"""
        # Implémentation basique - à améliorer avec une vraie clé de chiffrement
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_trading_input(self, data):
        """Valide les entrées de trading"""
        errors = []
        
        # Validation du capital
        try:
            capital = float(data.get('capital', 0))
            if capital <= 0 or capital > 10000000:  # 10M max
                errors.append("Capital invalide (entre 1$ et 10M$)")
        except (ValueError, TypeError):
            errors.append("Capital doit être un nombre valide")
        
        # Validation du risque
        try:
            risk = float(data.get('risk_percent', 0))
            if risk <= 0 or risk > 10:  # 10% max pour la sécurité
                errors.append("Risque invalide (entre 0.1% et 10%)")
        except (ValueError, TypeError):
            errors.append("Risque doit être un nombre valide")
        
        # Validation du prix d'entrée
        try:
            entry_price = float(data.get('entry_price', 0))
            if entry_price <= 0:
                errors.append("Prix d'entrée invalide")
        except (ValueError, TypeError):
            errors.append("Prix d'entrée doit être un nombre valide")
        
        # Validation du stop loss
        try:
            stop_loss = float(data.get('stop_loss', 0))
            if stop_loss <= 0:
                errors.append("Stop loss invalide")
        except (ValueError, TypeError):
            errors.append("Stop loss doit être un nombre valide")
        
        return len(errors) == 0, errors

# Instance globale
security = SecurityManager()

def require_csrf(f):
    """Décorateur pour vérifier le token CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not security.validate_csrf_token(token):
                security.log_security_event('CSRF_VIOLATION', 'Token CSRF invalide')
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=10, time_window=60):
    """Décorateur pour limiter le taux de requêtes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            if not security.check_rate_limit(identifier, max_requests, time_window):
                security.log_security_event('RATE_LIMIT_EXCEEDED', f'IP: {identifier}')
                return jsonify({'error': 'Trop de requêtes'}), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator