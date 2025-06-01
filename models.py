from app import db
from datetime import datetime, timedelta
import secrets

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
    plan = db.Column(db.String(20), default='free', nullable=False)
    subscription_end = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
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

class CurrencyPair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    pip_value = db.Column(db.Float, nullable=False)  # Value of 1 pip in the quote currency
    pip_size = db.Column(db.Float, nullable=False)   # Size of 1 pip (0.0001, 0.01, etc.)
    base_currency = db.Column(db.String(3), nullable=False)
    quote_currency = db.Column(db.String(3), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # forex, metals, crypto, indices
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CurrencyPair {self.symbol}>'

class PriceCache(db.Model):
    """Cache for Alpha Vantage API prices to optimize mobile app performance"""
    id = db.Column(db.Integer, primary_key=True)
    pair_symbol = db.Column(db.String(10), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<PriceCache {self.pair_symbol}: {self.price}>'
    
    def is_fresh(self, minutes=30):
        """Check if cached price is still fresh for mobile app"""
        return datetime.utcnow() - self.timestamp < timedelta(minutes=minutes)

class TradeCalculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pair_symbol = db.Column(db.String(10), nullable=False)
    direction = db.Column(db.String(4), nullable=False)  # BUY or SELL
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=False)
    take_profit = db.Column(db.Float, nullable=False)
    capital = db.Column(db.Float, nullable=False)
    risk_percent = db.Column(db.Float, nullable=False)
    calculated_lot_size = db.Column(db.Float, nullable=False)
    risk_usd = db.Column(db.Float, nullable=False)
    sl_pips = db.Column(db.Float, nullable=False)
    tp_pips = db.Column(db.Float, nullable=False)
    risk_reward_ratio = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TradeCalculation {self.pair_symbol} {self.direction}>'

class TradeJournal(db.Model):
    """Journal de trading pour enregistrer les trades réels"""
    id = db.Column(db.Integer, primary_key=True)
    user_session = db.Column(db.String(64), nullable=False, index=True)  # Session pour utilisateur gratuit
    
    # Détails du trade
    pair_symbol = db.Column(db.String(10), nullable=False)
    direction = db.Column(db.String(4), nullable=False)  # BUY or SELL
    lot_size = db.Column(db.Float, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=True)  # Null si trade ouvert
    stop_loss = db.Column(db.Float, nullable=True)
    take_profit = db.Column(db.Float, nullable=True)
    
    # Dates
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_date = db.Column(db.DateTime, nullable=True)
    
    # Résultats
    profit_loss = db.Column(db.Float, nullable=True)  # En USD
    profit_loss_pips = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(10), default='OPEN')  # OPEN, CLOSED, CANCELLED
    
    # Métadonnées
    strategy = db.Column(db.String(50), nullable=True)  # Premium feature
    notes = db.Column(db.Text, nullable=True)
    risk_reward_ratio = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TradeJournal {self.pair_symbol} - {self.direction} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'pair_symbol': self.pair_symbol,
            'direction': self.direction,
            'lot_size': self.lot_size,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'profit_loss': self.profit_loss,
            'profit_loss_pips': self.profit_loss_pips,
            'status': self.status,
            'strategy': self.strategy,
            'notes': self.notes,
            'risk_reward_ratio': self.risk_reward_ratio
        }

class RiskSettings(db.Model):
    """Paramètres de gestion du risque pour chaque utilisateur/session"""
    id = db.Column(db.Integer, primary_key=True)
    user_session = db.Column(db.String(64), nullable=False, index=True)
    
    # Alertes gratuites
    max_risk_warning = db.Column(db.Float, default=2.0)  # Alerte si risque > 2%
    daily_loss_limit = db.Column(db.Float, default=100.0)  # Limite de perte journalière en USD
    daily_loss_current = db.Column(db.Float, default=0.0)  # Perte actuelle du jour
    
    # Premium: Ajustement dynamique
    dynamic_risk_enabled = db.Column(db.Boolean, default=False)
    base_risk_percent = db.Column(db.Float, default=1.0)
    current_risk_percent = db.Column(db.Float, default=1.0)
    
    # Premium: Blocage après pertes
    consecutive_loss_limit = db.Column(db.Integer, default=3)
    consecutive_losses = db.Column(db.Integer, default=0)
    trading_blocked = db.Column(db.Boolean, default=False)
    block_until = db.Column(db.DateTime, nullable=True)
    
    # Premium: Scaling
    scaling_enabled = db.Column(db.Boolean, default=False)
    scaling_factor = db.Column(db.Float, default=1.1)  # Augmentation de 10%
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RiskSettings {self.user_session}>'
    
    def reset_daily_stats(self):
        """Remet à zéro les stats quotidiennes"""
        self.daily_loss_current = 0.0
        self.consecutive_losses = 0
        self.trading_blocked = False
        self.block_until = None
    
    def add_loss(self, loss_amount):
        """Ajoute une perte et vérifie les limites"""
        self.daily_loss_current += abs(loss_amount)
        self.consecutive_losses += 1
        
        # Vérifier blocage après pertes consécutives
        if self.consecutive_losses >= self.consecutive_loss_limit:
            self.trading_blocked = True
            self.block_until = datetime.utcnow() + timedelta(hours=24)
    
    def add_win(self):
        """Remet à zéro les pertes consécutives après un gain"""
        self.consecutive_losses = 0
        
        # Ajustement dynamique du risque après gain (Premium)
        if self.dynamic_risk_enabled and self.current_risk_percent < self.base_risk_percent * 2:
            self.current_risk_percent = min(
                self.current_risk_percent * 1.1, 
                self.base_risk_percent * 2
            )
    
    def is_risk_too_high(self, risk_percent):
        """Vérifie si le risque dépasse le seuil d'alerte"""
        return risk_percent > self.max_risk_warning
    
    def is_daily_limit_exceeded(self):
        """Vérifie si la limite quotidienne est dépassée"""
        return self.daily_loss_current >= self.daily_loss_limit
    
    def is_trading_blocked(self):
        """Vérifie si le trading est bloqué"""
        if self.block_until and datetime.utcnow() > self.block_until:
            self.trading_blocked = False
            self.block_until = None
            return False
        return self.trading_blocked


class PriceAlertModel(db.Model):
    """Modèle pour les alertes de prix en temps réel"""
    __tablename__ = 'price_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_session = db.Column(db.String(64), nullable=False, index=True)
    
    # Configuration de l'alerte
    pair_symbol = db.Column(db.String(10), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # above, below, percentage_up, percentage_down
    target_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    percentage_threshold = db.Column(db.Float, nullable=True)
    
    # État de l'alerte
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    triggered_at = db.Column(db.DateTime, nullable=True)
    
    # Message et notifications
    message = db.Column(db.Text, nullable=False)
    notification_sent = db.Column(db.Boolean, default=False)
    
    # Premium features
    is_recurring = db.Column(db.Boolean, default=False)
    custom_message = db.Column(db.Text, nullable=True)
    sound_enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<PriceAlert {self.pair_symbol} {self.alert_type} {self.target_price}>'
    
    def to_dict(self):
        """Convertit en dictionnaire pour l'API"""
        return {
            'id': self.alert_id,
            'pair_symbol': self.pair_symbol,
            'alert_type': self.alert_type,
            'target_price': self.target_price,
            'current_price': self.current_price,
            'percentage_threshold': self.percentage_threshold,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'message': self.message,
            'notification_sent': self.notification_sent,
            'is_recurring': self.is_recurring,
            'sound_enabled': self.sound_enabled
        }
    
    @staticmethod
    def get_user_active_count(user_session):
        """Compte les alertes actives d'un utilisateur (pour limite freemium)"""
        return PriceAlertModel.query.filter_by(
            user_session=user_session, 
            is_active=True
        ).count()
    
    @staticmethod
    def check_freemium_limit(user_session, is_premium=False):
        """Vérifie si l'utilisateur peut créer une nouvelle alerte"""
        if is_premium:
            return True, "Premium - Alertes illimitées"
        
        active_count = PriceAlertModel.get_user_active_count(user_session)
        if active_count >= 2:
            return False, "Limite atteinte : 2 alertes maximum (Gratuit). Passez Premium pour plus !"
        
        return True, f"Alertes utilisées : {active_count}/2 (Gratuit)"