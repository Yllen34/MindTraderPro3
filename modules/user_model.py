"""
Modèle User avec système de validation par email
"""
from app import db
from datetime import datetime, timedelta
import secrets
import hashlib

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Validation par email
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(100), nullable=True, index=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Plan et abonnement
    plan = db.Column(db.String(20), default='free', nullable=False)  # free, premium, lifetime
    subscription_end = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Statistiques d'utilisation
    calculations_today = db.Column(db.Integer, default=0)
    last_calculation_date = db.Column(db.Date, nullable=True)
    total_calculations = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def generate_verification_token(self):
        """Génère un token de validation unique"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    def is_verification_token_valid(self, token):
        """Vérifie si le token de validation est valide"""
        if not self.email_verification_token or not self.email_verification_sent_at:
            return False
        
        if self.email_verification_token != token:
            return False
        
        # Le token expire après 24 heures
        expiry_time = self.email_verification_sent_at + timedelta(hours=24)
        return datetime.utcnow() < expiry_time
    
    def verify_email(self):
        """Marque l'email comme vérifié"""
        self.is_email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.updated_at = datetime.utcnow()
    
    def can_access_dashboard(self):
        """Vérifie si l'utilisateur peut accéder au dashboard"""
        return self.is_email_verified and self.is_active
    
    def can_calculate(self):
        """Vérifie si l'utilisateur peut faire un calcul (limite freemium)"""
        if not self.is_email_verified:
            return False, "Email non vérifié"
        
        if self.plan in ['premium', 'lifetime']:
            return True, "Accès illimité"
        
        # Limite pour le plan gratuit : 3 calculs par jour
        today = datetime.utcnow().date()
        if self.last_calculation_date != today:
            self.calculations_today = 0
            self.last_calculation_date = today
        
        if self.calculations_today >= 3:
            return False, "Limite quotidienne atteinte (3 calculs)"
        
        return True, "Calcul autorisé"
    
    def increment_calculation_count(self):
        """Incrémente le compteur de calculs"""
        today = datetime.utcnow().date()
        if self.last_calculation_date != today:
            self.calculations_today = 0
            self.last_calculation_date = today
        
        self.calculations_today += 1
        self.total_calculations += 1
        self.updated_at = datetime.utcnow()
    
    def get_plan_features(self):
        """Retourne les fonctionnalités disponibles selon le plan"""
        if self.plan == 'free':
            return {
                'calculations_per_day': 3,
                'ai_assistant': False,
                'advanced_analytics': False,
                'journal_advanced': False,
                'priority_support': False
            }
        elif self.plan == 'premium':
            return {
                'calculations_per_day': 'unlimited',
                'ai_assistant': True,
                'advanced_analytics': True,
                'journal_advanced': True,
                'priority_support': True
            }
        elif self.plan == 'lifetime':
            return {
                'calculations_per_day': 'unlimited',
                'ai_assistant': True,
                'advanced_analytics': True,
                'journal_advanced': True,
                'priority_support': True,
                'exclusive_features': True,
                'early_access': True
            }
    
    def is_premium(self):
        """Vérifie si l'utilisateur a un plan premium actif"""
        if self.plan == 'lifetime':
            return True
        
        if self.plan == 'premium' and self.subscription_end:
            return datetime.utcnow() < self.subscription_end
        
        return False
    
    def days_since_registration(self):
        """Calcule le nombre de jours depuis l'inscription"""
        return (datetime.utcnow() - self.created_at).days
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire pour les API"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'is_email_verified': self.is_email_verified,
            'is_premium': self.is_premium(),
            'created_at': self.created_at.isoformat(),
            'days_since_registration': self.days_since_registration(),
            'calculations_today': self.calculations_today,
            'total_calculations': self.total_calculations,
            'features': self.get_plan_features()
        }