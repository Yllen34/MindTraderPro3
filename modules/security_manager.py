"""
Gestionnaire de sécurité - MindTraderPro
Protection CSRF, XSS, validation, limitation tentatives
"""
import hashlib
import secrets
import time
import json
import os
from datetime import datetime, timedelta
from flask import session, request, abort
from functools import wraps

class SecurityManager:
    def __init__(self):
        self.failed_attempts = {}  # IP -> {'count': int, 'last_attempt': timestamp}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.security_log_file = 'data/security_logs.json'
        
    def generate_csrf_token(self):
        """Génère un token CSRF unique"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token):
        """Valide le token CSRF"""
        return token and session.get('csrf_token') == token
    
    def sanitize_input(self, data):
        """Nettoie les entrées utilisateur contre XSS"""
        if isinstance(data, str):
            # Suppression des balises HTML dangereuses
            dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<form']
            for tag in dangerous_tags:
                data = data.replace(tag.lower(), '').replace(tag.upper(), '')
            return data.strip()
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        return data
    
    def validate_email(self, email):
        """Validation stricte d'email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password):
        """Validation de la force du mot de passe"""
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre"
        
        return True, "Mot de passe valide"
    
    def hash_password(self, password):
        """Hachage sécurisé du mot de passe"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + pwd_hash.hex()
    
    def verify_password(self, password, stored_hash):
        """Vérification du mot de passe"""
        salt = stored_hash[:64]
        stored_pwd = stored_hash[64:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash.hex() == stored_pwd
    
    def check_rate_limit(self, ip_address):
        """Vérifie les tentatives de connexion"""
        current_time = time.time()
        
        if ip_address in self.failed_attempts:
            attempt_data = self.failed_attempts[ip_address]
            
            # Si dans la période de blocage
            if current_time - attempt_data['last_attempt'] < self.lockout_duration:
                if attempt_data['count'] >= self.max_attempts:
                    return False, f"Trop de tentatives. Réessayez dans {self.lockout_duration // 60} minutes."
            else:
                # Réinitialiser si période expirée
                self.failed_attempts[ip_address] = {'count': 0, 'last_attempt': current_time}
        
        return True, "OK"
    
    def record_failed_attempt(self, ip_address):
        """Enregistre une tentative échouée"""
        current_time = time.time()
        
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = {'count': 0, 'last_attempt': current_time}
        
        self.failed_attempts[ip_address]['count'] += 1
        self.failed_attempts[ip_address]['last_attempt'] = current_time
        
        # Log de sécurité
        self.log_security_event('failed_login', {
            'ip': ip_address,
            'attempts': self.failed_attempts[ip_address]['count'],
            'timestamp': datetime.now().isoformat()
        })
    
    def reset_failed_attempts(self, ip_address):
        """Remet à zéro les tentatives échouées"""
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]
    
    def log_security_event(self, event_type, data):
        """Enregistre les événements de sécurité"""
        try:
            # Lire les logs existants
            if os.path.exists(self.security_log_file):
                with open(self.security_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Ajouter le nouvel événement
            log_entry = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            logs.append(log_entry)
            
            # Garder seulement les 1000 derniers logs
            logs = logs[-1000:]
            
            # Sauvegarder
            os.makedirs(os.path.dirname(self.security_log_file), exist_ok=True)
            with open(self.security_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erreur lors de l'écriture des logs de sécurité: {e}")
    
    def encrypt_sensitive_data(self, data):
        """Chiffrement des données sensibles"""
        # Utilisation de Fernet pour le chiffrement symétrique
        try:
            from cryptography.fernet import Fernet
            
            # Génération ou récupération de la clé
            key_file = 'data/.encryption_key'
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
            
            fernet = Fernet(key)
            return fernet.encrypt(data.encode()).decode()
            
        except ImportError:
            # Fallback si cryptography n'est pas installé
            return hashlib.sha256(data.encode()).hexdigest()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Déchiffrement des données sensibles"""
        try:
            from cryptography.fernet import Fernet
            
            key_file = 'data/.encryption_key'
            with open(key_file, 'rb') as f:
                key = f.read()
            
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data.encode()).decode()
            
        except (ImportError, Exception):
            # Si déchiffrement impossible, retourner tel quel
            return encrypted_data

# Instance globale
security_manager = SecurityManager()

def require_csrf(f):
    """Décorateur pour vérifier le token CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not security_manager.validate_csrf_token(token):
                abort(403, "Token CSRF invalide")
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(f):
    """Décorateur pour limiter les tentatives"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        allowed, message = security_manager.check_rate_limit(ip)
        if not allowed:
            abort(429, message)
        return f(*args, **kwargs)
    return decorated_function