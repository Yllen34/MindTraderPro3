"""
MindTraderPro - Application finale avec navigation unifiée
Calculateur de trading professionnel avec navigation moderne
"""

from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
import os
import sqlite3
import logging
import requests
import json
import time
from datetime import datetime
from app_navigation import get_modern_navbar, get_page_template, get_user_session_info

# Configuration API Twelve Data
TWELVE_DATA_API_KEY = "xNq2H4tmrRNdCV8H7eUT"
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"

# Cache pour les prix (durée: 30 secondes)
price_cache = {}
CACHE_DURATION = 30

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Configuration Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "mindtraderpro-secret-key-2024"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///mindtraderpro_users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Modèle pour les paires de devises
class CurrencyPair(db.Model):
    __tablename__ = 'currency_pairs'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)  # Ex: EURUSD
    name = db.Column(db.String(50), nullable=False)  # Ex: EUR/USD
    display_name = db.Column(db.String(100), nullable=False)  # Ex: Euro / Dollar US
    category = db.Column(db.String(20), nullable=False)  # Major, Cross, Metal, Crypto, Index
    base_currency = db.Column(db.String(10), nullable=False)  # Ex: EUR
    quote_currency = db.Column(db.String(10), nullable=False)  # Ex: USD
    pip_size = db.Column(db.Float, nullable=False, default=0.0001)
    pip_value = db.Column(db.Float, nullable=False, default=10.0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'display_name': self.display_name,
            'category': self.category,
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'pip_size': self.pip_size,
            'pip_value': self.pip_value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Gestion des sessions permanentes
@app.before_request
def make_session_permanent():
    session.permanent = True

def login_required(f):
    """Décorateur pour vérifier si l'utilisateur est connecté"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = get_user_session_info()
        if not user_info['is_authenticated']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour vérifier si l'utilisateur est administrateur"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = get_user_session_info()
        if not user_info['is_authenticated']:
            return redirect(url_for('login'))
        if user_info['role'] != 'admin':
            return render_template_string('''
                <div class="container mt-5">
                    <div class="alert alert-danger text-center">
                        <h4><i class="fas fa-lock me-2"></i>Accès Restreint</h4>
                        <p>Cette page est réservée aux administrateurs.</p>
                        <a href="/home" class="btn btn-primary">Retour à l'accueil</a>
                    </div>
                </div>
            '''), 403
        return f(*args, **kwargs)
    return decorated_function

def init_default_currency_pairs():
    """Initialise les paires de devises par défaut dans la base de données"""
    try:
        with app.app_context():
            # Créer les tables si elles n'existent pas
            db.create_all()
            
            # Vérifier si des paires existent déjà
            existing_pairs = CurrencyPair.query.count()
            if existing_pairs > 0:
                return
            
            # Données par défaut des paires
            default_pairs = [
                # Paires forex majeures
                {'symbol': 'EURUSD', 'name': 'EUR/USD', 'display_name': 'Euro / Dollar US', 'category': 'Major', 'base_currency': 'EUR', 'quote_currency': 'USD', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'GBPUSD', 'name': 'GBP/USD', 'display_name': 'Livre Sterling / Dollar US', 'category': 'Major', 'base_currency': 'GBP', 'quote_currency': 'USD', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'USDJPY', 'name': 'USD/JPY', 'display_name': 'Dollar US / Yen Japonais', 'category': 'Major', 'base_currency': 'USD', 'quote_currency': 'JPY', 'pip_size': 0.01, 'pip_value': 10.0},
                {'symbol': 'USDCHF', 'name': 'USD/CHF', 'display_name': 'Dollar US / Franc Suisse', 'category': 'Major', 'base_currency': 'USD', 'quote_currency': 'CHF', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'AUDUSD', 'name': 'AUD/USD', 'display_name': 'Dollar Australien / Dollar US', 'category': 'Major', 'base_currency': 'AUD', 'quote_currency': 'USD', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'USDCAD', 'name': 'USD/CAD', 'display_name': 'Dollar US / Dollar Canadien', 'category': 'Major', 'base_currency': 'USD', 'quote_currency': 'CAD', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'NZDUSD', 'name': 'NZD/USD', 'display_name': 'Dollar Néo-Zélandais / Dollar US', 'category': 'Major', 'base_currency': 'NZD', 'quote_currency': 'USD', 'pip_size': 0.0001, 'pip_value': 10.0},
                
                # Paires croisées
                {'symbol': 'EURGBP', 'name': 'EUR/GBP', 'display_name': 'Euro / Livre Sterling', 'category': 'Cross', 'base_currency': 'EUR', 'quote_currency': 'GBP', 'pip_size': 0.0001, 'pip_value': 10.0},
                {'symbol': 'EURJPY', 'name': 'EUR/JPY', 'display_name': 'Euro / Yen Japonais', 'category': 'Cross', 'base_currency': 'EUR', 'quote_currency': 'JPY', 'pip_size': 0.01, 'pip_value': 10.0},
                {'symbol': 'GBPJPY', 'name': 'GBP/JPY', 'display_name': 'Livre Sterling / Yen Japonais', 'category': 'Cross', 'base_currency': 'GBP', 'quote_currency': 'JPY', 'pip_size': 0.01, 'pip_value': 10.0},
                
                # Métaux précieux
                {'symbol': 'XAUUSD', 'name': 'XAU/USD', 'display_name': 'Or / Dollar US', 'category': 'Metal', 'base_currency': 'XAU', 'quote_currency': 'USD', 'pip_size': 0.1, 'pip_value': 1.0},
                {'symbol': 'XAGUSD', 'name': 'XAG/USD', 'display_name': 'Argent / Dollar US', 'category': 'Metal', 'base_currency': 'XAG', 'quote_currency': 'USD', 'pip_size': 0.001, 'pip_value': 5.0},
                
                # Cryptomonnaies
                {'symbol': 'BTCUSD', 'name': 'BTC/USD', 'display_name': 'Bitcoin / Dollar US', 'category': 'Crypto', 'base_currency': 'BTC', 'quote_currency': 'USD', 'pip_size': 1.0, 'pip_value': 1.0},
                {'symbol': 'ETHUSD', 'name': 'ETH/USD', 'display_name': 'Ethereum / Dollar US', 'category': 'Crypto', 'base_currency': 'ETH', 'quote_currency': 'USD', 'pip_size': 0.01, 'pip_value': 1.0},
                
                # Indices
                {'symbol': 'US30', 'name': 'US30', 'display_name': 'Dow Jones Industrial Average', 'category': 'Index', 'base_currency': 'US30', 'quote_currency': 'USD', 'pip_size': 1.0, 'pip_value': 1.0},
                {'symbol': 'SPX500', 'name': 'SPX500', 'display_name': 'S&P 500 Index', 'category': 'Index', 'base_currency': 'SPX500', 'quote_currency': 'USD', 'pip_size': 0.1, 'pip_value': 1.0},
                {'symbol': 'NAS100', 'name': 'NAS100', 'display_name': 'Nasdaq 100 Index', 'category': 'Index', 'base_currency': 'NAS100', 'quote_currency': 'USD', 'pip_size': 0.1, 'pip_value': 1.0},
            ]
            
            # Ajouter chaque paire à la base de données
            for pair_data in default_pairs:
                pair = CurrencyPair(**pair_data)
                db.session.add(pair)
            
            db.session.commit()
            logging.info("✅ Paires de devises par défaut initialisées")
            
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation des paires: {e}")

def get_active_trading_pairs():
    """Retourne les paires de trading actives depuis la base de données"""
    try:
        with app.app_context():
            pairs = CurrencyPair.query.filter_by(is_active=True).all()
            return {pair.symbol: pair.to_dict() for pair in pairs}
    except Exception as e:
        logging.error(f"Erreur récupération paires actives: {e}")
        return {}

def get_all_trading_pairs():
    """Retourne toutes les paires de trading depuis la base de données"""
    try:
        with app.app_context():
            pairs = CurrencyPair.query.all()
            return {pair.symbol: pair.to_dict() for pair in pairs}
    except Exception as e:
        logging.error(f"Erreur récupération toutes paires: {e}")
        return {}

def get_pip_info(pair_symbol):
    """Get pip size and pip value for a currency pair"""
    all_pairs = get_all_trading_pairs()
    pair_info = all_pairs.get(pair_symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
    return {'pip_size': pair_info['pip_size'], 'pip_value': pair_info['pip_value']}

def get_real_time_price(pair_symbol):
    """Récupère le prix en temps réel avec système de fallback intelligent"""
    try:
        current_time = time.time()
        cache_key = f"price_{pair_symbol}"
        
        # Vérifier le cache
        if cache_key in price_cache:
            cached_data = price_cache[cache_key]
            if current_time - cached_data['timestamp'] < CACHE_DURATION:
                logging.info(f"Prix en cache pour {pair_symbol}: {cached_data['price']}")
                return {
                    'success': True,
                    'price': cached_data['price'],
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'source': 'Cache',
                    'cached': True
                }
        
        # Vérifier si une clé API Twelve Data est disponible
        twelve_data_key = os.environ.get('TWELVE_DATA_API_KEY')
        if twelve_data_key:
            try:
                # Convertir le symbole pour Twelve Data (ex: EURUSD -> EUR/USD)
                if len(pair_symbol) >= 6 and pair_symbol.isalpha():
                    formatted_symbol = f"{pair_symbol[:3]}/{pair_symbol[3:]}"
                else:
                    formatted_symbol = pair_symbol
                
                # Appel API Twelve Data
                url = f"{TWELVE_DATA_BASE_URL}/price"
                params = {
                    'symbol': formatted_symbol,
                    'apikey': twelve_data_key
                }
                
                logging.info(f"Appel API Twelve Data pour {formatted_symbol}")
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'price' in data and data['price']:
                        price = float(data['price'])
                        
                        # Mettre à jour le cache
                        price_cache[cache_key] = {
                            'price': price,
                            'timestamp': current_time
                        }
                        
                        logging.info(f"Prix reçu de Twelve Data pour {pair_symbol}: {price}")
                        return {
                            'success': True,
                            'price': round(price, 5),
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'source': 'Twelve Data',
                            'cached': False
                        }
            except Exception as api_error:
                logging.warning(f"Erreur API Twelve Data: {api_error}")
        
        # Système de fallback avec prix simulés réalistes
        import random
        
        # Prix de référence basés sur des valeurs de marché réelles (Janvier 2024)
        realistic_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 148.50,
            'USDCHF': 0.8750,
            'AUDUSD': 0.6750,
            'USDCAD': 1.3450,
            'NZDUSD': 0.6250,
            'EURGBP': 0.8580,
            'EURJPY': 161.20,
            'GBPJPY': 187.80,
            'XAUUSD': 2025.50,
            'XAGUSD': 23.85,
            'BTCUSD': 43500.00,
            'ETHUSD': 2650.00,
            'USDZAR': 18.75,
            'USDMXN': 17.05,
            'USDINR': 83.15,
            'USDCNY': 7.18
        }
        
        base_price = realistic_prices.get(pair_symbol, 1.0000)
        
        # Variation réaliste (-0.5% à +0.5%)
        variation_percent = random.uniform(-0.005, 0.005)
        current_price = base_price * (1 + variation_percent)
        
        # Ajuster la précision selon l'instrument
        if pair_symbol in ['XAUUSD', 'XAGUSD']:
            price = round(current_price, 2)  # Métaux: 2 décimales
        elif pair_symbol in ['BTCUSD', 'ETHUSD']:
            price = round(current_price, 2)  # Crypto: 2 décimales
        elif 'JPY' in pair_symbol:
            price = round(current_price, 3)  # Yen: 3 décimales
        else:
            price = round(current_price, 5)  # Forex: 5 décimales
        
        # Mettre à jour le cache
        price_cache[cache_key] = {
            'price': price,
            'timestamp': current_time
        }
        
        logging.info(f"Prix simulé réaliste pour {pair_symbol}: {price}")
        return {
            'success': True,
            'price': price,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'source': 'Simulation Réaliste',
            'cached': False
        }
        
    except Exception as e:
        logging.error(f"Erreur récupération prix pour {pair_symbol}: {e}")
        return {
            'success': False,
            'error': str(e),
            'price': 0,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }

def calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol, pip_value=None):
    """Calculate the recommended lot size based on risk management"""
    try:
        # Récupération des informations de pip
        pip_info = get_pip_info(pair_symbol)
        if pip_value is None:
            pip_value = pip_info['pip_value']
        
        # Calcul du risque en USD
        risk_usd = capital * (risk_percent / 100)
        
        # Calcul de la taille de lot
        if sl_pips > 0 and pip_value > 0:
            lot_size = risk_usd / (sl_pips * pip_value)
        else:
            lot_size = 0
        
        return {
            'lot_size': round(lot_size, 2),
            'risk_usd': round(risk_usd, 2),
            'pip_value': pip_value,
            'pip_size': pip_info['pip_size']
        }
    except Exception as e:
        logging.error(f"Erreur calcul lot size: {e}")
        return {'error': str(e)}

# ==================== ROUTES PRINCIPALES ====================

@app.route('/')
def index():
    """Redirection vers page d'accueil"""
    return redirect(url_for('home'))

@app.route('/home')
def home():
    """Page d'accueil avec navigation unifiée moderne"""
    
    content = '''
    <!-- Section Héros -->
    <div class="hero-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 80px 0; color: white;">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-3 fw-bold mb-4">
                        <i class="fas fa-chart-line me-3" style="color: #00ff88;"></i>MindTraderPro
                    </h1>
                    <p class="lead mb-4" style="font-size: 1.3rem;">
                        Calculateur de trading professionnel avec gestion du risque avancée
                    </p>
                    <p class="mb-4" style="font-size: 1.1rem; opacity: 0.9;">
                        Optimisez vos positions de trading avec notre calculateur intelligent et gérez votre risque comme un professionnel
                    </p>
                    <div class="d-flex flex-wrap gap-3">
                        <a href="/calculator" class="btn btn-light btn-lg">
                            <i class="fas fa-calculator me-2"></i>Commencer à calculer
                        </a>
                        <a href="/register" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-user-plus me-2"></i>S'inscrire gratuitement
                        </a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <div class="hero-image mt-4 mt-lg-0">
                        <i class="fas fa-chart-area" style="font-size: 12rem; opacity: 0.3;"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Section Statistiques -->
    <div class="stats-section py-5" style="background: rgba(0,0,0,0.3);">
        <div class="container">
            <div class="row text-center">
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-card" style="padding: 30px; border-radius: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                        <h2 class="display-4 fw-bold text-success mb-2">60+</h2>
                        <p class="text-muted mb-0">Paires de trading supportées</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-card" style="padding: 30px; border-radius: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                        <h2 class="display-4 fw-bold text-primary mb-2">1000+</h2>
                        <p class="text-muted mb-0">Traders actifs</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-card" style="padding: 30px; border-radius: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                        <h2 class="display-4 fw-bold text-warning mb-2">24/7</h2>
                        <p class="text-muted mb-0">Support disponible</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-card" style="padding: 30px; border-radius: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                        <h2 class="display-4 fw-bold text-info mb-2">100%</h2>
                        <p class="text-muted mb-0">Satisfaction garantie</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Section Tarification -->
    <div class="pricing-section py-5" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);">
        <div class="container">
            <div class="row mb-5">
                <div class="col-12 text-center">
                    <h2 class="display-5 fw-bold mb-3 text-white">Choisissez Votre Plan</h2>
                    <p class="lead text-muted">Des tarifs flexibles pour tous les types de traders</p>
                </div>
            </div>
            
            <div class="row justify-content-center">
                <!-- Plan Gratuit -->
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="pricing-card h-100" style="background: rgba(255,255,255,0.05); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <h3 class="text-success mb-2">Gratuit</h3>
                            <div class="price mb-3">
                                <span class="display-4 fw-bold text-white">0€</span>
                                <small class="text-muted">/mois</small>
                            </div>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Calculateur de base</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>3 calculs par jour</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Paires principales</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Support communautaire</li>
                        </ul>
                        <div class="text-center">
                            <a href="/register" class="btn btn-outline-success btn-lg w-100">Commencer Gratuitement</a>
                        </div>
                    </div>
                </div>
                
                <!-- Plan Premium -->
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="pricing-card h-100" style="background: linear-gradient(145deg, rgba(0,123,255,0.1), rgba(0,86,179,0.1)); padding: 40px; border-radius: 20px; border: 2px solid #007bff; box-shadow: 0 10px 30px rgba(0,123,255,0.3); transform: scale(1.05);">
                        <div class="text-center mb-4">
                            <span class="badge bg-primary mb-2">POPULAIRE</span>
                            <h3 class="text-primary mb-2">Premium</h3>
                            <div class="price mb-3">
                                <span class="display-4 fw-bold text-white">14,99€</span>
                                <small class="text-muted">/mois</small>
                            </div>
                            <small class="text-muted">ou 119€/an (-33%)</small>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>Calculs illimités</li>
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>60+ paires de trading</li>
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>Journal de trading avancé</li>
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>Alertes de prix</li>
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>Analytics détaillés</li>
                            <li class="mb-2"><i class="fas fa-check text-primary me-2"></i>Support prioritaire</li>
                        </ul>
                        <div class="text-center">
                            <a href="/register" class="btn btn-primary btn-lg w-100">Essayer Premium</a>
                        </div>
                    </div>
                </div>
                
                <!-- Plan Lifetime -->
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="pricing-card h-100" style="background: linear-gradient(145deg, rgba(255,193,7,0.1), rgba(255,143,0,0.1)); padding: 40px; border-radius: 20px; border: 1px solid #ffc107; transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <span class="badge bg-warning text-dark mb-2">MEILLEURE VALEUR</span>
                            <h3 class="text-warning mb-2">Lifetime</h3>
                            <div class="price mb-3">
                                <span class="display-4 fw-bold text-white">249€</span>
                                <small class="text-muted">/une fois</small>
                            </div>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Tout du Premium à vie</li>
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Simulateur de trading</li>
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Assistant IA avancé</li>
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Backtesting complet</li>
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Badge VIP exclusif</li>
                            <li class="mb-2"><i class="fas fa-check text-warning me-2"></i>Accès anticipé aux nouvelles fonctionnalités</li>
                        </ul>
                        <div class="text-center">
                            <a href="/register" class="btn btn-lg w-100 text-white" style="background: linear-gradient(45deg, #ffc107, #ff8c00); border: none; font-weight: bold;">Acheter Lifetime</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Section Modules/Fonctionnalités -->
    <div class="features-section py-5">
        <div class="container">
            <div class="row mb-5">
                <div class="col-12 text-center">
                    <h2 class="display-5 fw-bold mb-3">Fonctionnalités Professionnelles</h2>
                    <p class="lead text-muted">Découvrez tous les outils disponibles dans MindTraderPro</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-calculator fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Calculateur de Position</h4>
                        <p class="text-muted text-center mb-4">Calculez la taille optimale de vos positions en fonction de votre capital et de votre tolérance au risque</p>
                        <div class="text-center">
                            <a href="/calculator" class="btn btn-outline-primary">Utiliser maintenant</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(0,255,136,0.1), rgba(0,200,100,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #00ff88, #00c864); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-book fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Journal de Trading</h4>
                        <p class="text-muted text-center mb-4">Suivez et analysez vos performances avec notre journal intelligent et ses statistiques avancées</p>
                        <div class="text-center">
                            <a href="/journal" class="btn btn-outline-success">Découvrir</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(255,193,7,0.1), rgba(255,152,0,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #ffc107, #ff9800); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-medal fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Système de Grades</h4>
                        <p class="text-muted text-center mb-4">Progressez dans vos compétences de trading et débloquez de nouveaux avantages</p>
                        <div class="text-center">
                            <a href="/grades" class="btn btn-outline-warning">Explorer</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(220,53,69,0.1), rgba(181,23,58,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #dc3545, #b5173a); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-trophy fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Classements</h4>
                        <p class="text-muted text-center mb-4">Comparez vos performances avec la communauté et visez le sommet</p>
                        <div class="text-center">
                            <a href="/leaderboard" class="btn btn-outline-danger">Voir le classement</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(13,202,240,0.1), rgba(11,172,204,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #0dcaf0, #0baccc); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-handshake fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Programme de Parrainage</h4>
                        <p class="text-muted text-center mb-4">Invitez vos amis et gagnez des récompenses exclusives</p>
                        <div class="text-center">
                            <a href="/parrainage" class="btn btn-outline-info">Découvrir</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="feature-card h-100" style="background: linear-gradient(145deg, rgba(111,66,193,0.1), rgba(142,36,170,0.1)); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;">
                        <div class="text-center mb-4">
                            <div class="feature-icon" style="width: 80px; height: 80px; background: linear-gradient(45deg, #6f42c1, #8e24aa); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <i class="fas fa-palette fa-2x text-white"></i>
                            </div>
                        </div>
                        <h4 class="text-center mb-3">Personnalisation</h4>
                        <p class="text-muted text-center mb-4">Customisez votre expérience avec des thèmes et avatars uniques</p>
                        <div class="text-center">
                            <a href="/personnalisation" class="btn btn-outline-secondary">Personnaliser</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer mt-5" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 50px 0 30px 0; border-top: 1px solid rgba(255,255,255,0.1);">
        <div class="container">
            <div class="row">
                <div class="col-lg-4 col-md-6 mb-4">
                    <h5 class="fw-bold mb-3">
                        <i class="fas fa-chart-line me-2 text-success"></i>MindTraderPro
                    </h5>
                    <p class="text-muted">
                        Plateforme professionnelle de calcul de positions de trading avec gestion avancée du risque.
                    </p>
                    <div class="social-links">
                        <a href="#" class="text-muted me-3"><i class="fab fa-twitter fa-lg"></i></a>
                        <a href="#" class="text-muted me-3"><i class="fab fa-linkedin fa-lg"></i></a>
                        <a href="#" class="text-muted me-3"><i class="fab fa-telegram fa-lg"></i></a>
                    </div>
                </div>
                
                <div class="col-lg-2 col-md-6 mb-4">
                    <h6 class="fw-bold mb-3">Plateforme</h6>
                    <ul class="list-unstyled">
                        <li><a href="/calculator" class="text-muted">Calculateur</a></li>
                        <li><a href="/journal" class="text-muted">Journal</a></li>
                        <li><a href="/grades" class="text-muted">Grades</a></li>
                        <li><a href="/leaderboard" class="text-muted">Classements</a></li>
                    </ul>
                </div>
                
                <div class="col-lg-2 col-md-6 mb-4">
                    <h6 class="fw-bold mb-3">Communauté</h6>
                    <ul class="list-unstyled">
                        <li><a href="/suggestions" class="text-muted">Suggestions</a></li>
                        <li><a href="/parrainage" class="text-muted">Parrainage</a></li>
                        <li><a href="/personnalisation" class="text-muted">Thèmes</a></li>
                        <li><a href="/leaderboard-parrainage" class="text-muted">Top Parrains</a></li>
                    </ul>
                </div>
                
                <div class="col-lg-2 col-md-6 mb-4">
                    <h6 class="fw-bold mb-3">Support</h6>
                    <ul class="list-unstyled">
                        <li><a href="#" class="text-muted">Centre d'aide</a></li>
                        <li><a href="#" class="text-muted">Contact</a></li>
                        <li><a href="#" class="text-muted">FAQ</a></li>
                        <li><a href="#" class="text-muted">Tutoriels</a></li>
                    </ul>
                </div>
                
                <div class="col-lg-2 col-md-6 mb-4">
                    <h6 class="fw-bold mb-3">Légal</h6>
                    <ul class="list-unstyled">
                        <li><a href="#" class="text-muted">Conditions d'utilisation</a></li>
                        <li><a href="#" class="text-muted">Politique de confidentialité</a></li>
                        <li><a href="#" class="text-muted">Mentions légales</a></li>
                        <li><a href="#" class="text-muted">RGPD</a></li>
                    </ul>
                </div>
            </div>
            
            <hr style="border-color: rgba(255,255,255,0.1); margin: 40px 0 20px 0;">
            
            <div class="row align-items-center">
                <div class="col-md-6">
                    <p class="text-muted mb-0">
                        © 2024 MindTraderPro. Tous droits réservés.
                    </p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p class="text-muted mb-0">
                        Fait avec <i class="fas fa-heart text-danger"></i> pour les traders professionnels
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <style>
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .stat-card:hover {
            transform: scale(1.05);
            transition: all 0.3s ease;
        }
        
        footer a:hover {
            color: #00ff88 !important;
            transition: color 0.3s ease;
        }
        
        .social-links a:hover {
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
    </style>
    '''
    
    return get_page_template("Accueil", content, "home")

@app.route('/calculator')
def calculator():
    """Page calculateur avancé avec prix en temps réel"""
    
    # Vérification de l'authentification
    user_info = get_user_session_info()
    is_authenticated = user_info['is_authenticated']
    
    # Récupération de toutes les paires disponibles
    all_pairs = get_all_trading_pairs()
    
    content = f'''
    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="calculator-header text-center mb-4">
                    <h2 class="display-6 fw-bold">
                        <i class="fas fa-calculator me-3 text-success"></i>Calculateur de Position Avancé
                    </h2>
                    <p class="lead text-muted">Calculez vos positions avec des données de marché en temps réel</p>
                </div>
                
                {'<div class="alert alert-warning mb-4"><i class="fas fa-exclamation-triangle me-2"></i>Connectez-vous pour utiliser le calculateur avec données en temps réel et fonctionnalités avancées.</div>' if not is_authenticated else ''}
                
                <div class="calculator-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 20px; border: none; box-shadow: 0 20px 40px rgba(102,126,234,0.3), 0 0 30px rgba(118,75,162,0.2);">
                    
                    <form id="calculatorForm" {'style="opacity: 0.6; pointer-events: none;"' if not is_authenticated else ''}>

                        <!-- Sélection de la paire -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-exchange-alt me-2 text-success"></i>Paire de Trading
                                </label>
                                <select class="form-select form-select-lg" id="pairSymbol" required style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                    <option value="">Sélectionnez une paire...</option>
                                    <optgroup label="🔥 Paires Majeures">
                                        <option value="EURUSD">EUR/USD - Euro / Dollar US</option>
                                        <option value="GBPUSD">GBP/USD - Livre Sterling / Dollar US</option>
                                        <option value="USDJPY">USD/JPY - Dollar US / Yen Japonais</option>
                                        <option value="USDCHF">USD/CHF - Dollar US / Franc Suisse</option>
                                        <option value="AUDUSD">AUD/USD - Dollar Australien / Dollar US</option>
                                        <option value="USDCAD">USD/CAD - Dollar US / Dollar Canadien</option>
                                        <option value="NZDUSD">NZD/USD - Dollar Néo-Zélandais / Dollar US</option>
                                    </optgroup>
                                    <optgroup label="💎 Métaux Précieux">
                                        <option value="XAUUSD" selected>XAU/USD - Or / Dollar US</option>
                                        <option value="XAGUSD">XAG/USD - Argent / Dollar US</option>
                                    </optgroup>
                                    <optgroup label="₿ Cryptomonnaies">
                                        <option value="BTCUSD">BTC/USD - Bitcoin / Dollar US</option>
                                        <option value="ETHUSD">ETH/USD - Ethereum / Dollar US</option>
                                    </optgroup>
                                    <optgroup label="📊 Indices">
                                        <option value="US30">US30 - Dow Jones</option>
                                        <option value="SPX500">SPX500 - S&P 500</option>
                                        <option value="NAS100">NAS100 - Nasdaq 100</option>
                                    </optgroup>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Affichage du prix sous la sélection de paire -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <div id="priceDisplay" class="price-display" style="background: rgba(0,255,136,0.1); padding: 12px; border-radius: 8px; border: 1px solid rgba(0,255,136,0.3); text-align: center; display: none;">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <small class="text-muted me-2">Prix actuel:</small>
                                        <span id="displayPairName" class="me-2 text-white fw-bold" style="font-size: 0.9rem;">--</span>
                                        <span id="currentPrice" class="text-success fw-bold" style="font-size: 1.3rem;">--</span>
                                    </div>
                                    <div id="priceLoading" style="display: none;">
                                        <small class="text-muted">Chargement...</small>
                                    </div>
                                    <div id="priceError" style="display: none;">
                                        <small class="text-danger">Prix indisponible - API déconnectée</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Type d'ordre BUY/SELL - Centré et unique -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <label class="form-label fw-bold text-white text-center d-block">
                                    <i class="fas fa-chart-line me-2 text-success"></i>Type d'Ordre
                                </label>
                                <div class="d-flex justify-content-center">
                                    <div class="btn-group" role="group" style="width: 300px;">
                                        <input type="radio" class="btn-check" name="orderType" id="buyOrder" value="BUY" checked>
                                        <label class="btn btn-outline-success btn-lg" for="buyOrder">
                                            <i class="fas fa-arrow-up me-2"></i>BUY
                                        </label>
                                        
                                        <input type="radio" class="btn-check" name="orderType" id="sellOrder" value="SELL">
                                        <label class="btn btn-outline-danger btn-lg" for="sellOrder">
                                            <i class="fas fa-arrow-down me-2"></i>SELL
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        


                        <!-- Capital et Risque -->
                        <div class="row mb-4">
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-wallet me-2 text-success"></i>Capital
                                </label>
                                <div class="input-group input-group-lg">
                                    <input type="number" class="form-control" id="capital" value="10000" min="100" max="10000000" step="100" required placeholder="Ex: 10000" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                    <select class="form-select" id="accountCurrency" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px); max-width: 100px;">
                                        <option value="USD">$</option>
                                        <option value="EUR">€</option>
                                    </select>
                                </div>
                                <small class="text-white-50">Montant total disponible pour le trading</small>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-shield-alt me-2 text-warning"></i>Risque par Trade (%)
                                </label>
                                <input type="number" class="form-control form-control-lg" id="riskPercent" value="0.5" min="0.1" max="10" step="0.1" required style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                <small class="text-white-50">Pourcentage du capital à risquer</small>
                                <div class="mt-1">
                                    <small class="text-info">
                                        <i class="fas fa-info-circle me-1"></i>Risque recommandé : 0.5% à 2% par trade
                                    </small>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Prix d'entrée (toujours visible) -->
                        <div class="row mb-3" id="entryPriceRow">
                            <div class="col-md-6">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-chart-line me-2 text-success"></i>Prix d'Entrée
                                </label>
                                <input type="number" class="form-control form-control-lg" id="entryPrice" value="" min="0.01" step="0.00001" placeholder="Ex: 2025.50" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                <small class="text-white-50">Prix d'entrée pour calculer les pips</small>
                            </div>
                        </div>
                        
                        <!-- Stop Loss et Take Profit -->
                        <div class="row mb-4">
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-stop-circle me-2 text-danger"></i>Stop Loss
                                </label>
                                <div class="mb-2">
                                    <div class="btn-group w-100" role="group">
                                        <input type="radio" class="btn-check" name="slMode" id="slPriceMode" value="price" checked>
                                        <label class="btn btn-outline-info" for="slPriceMode">Prix</label>
                                        <input type="radio" class="btn-check" name="slMode" id="slPipsMode" value="pips">
                                        <label class="btn btn-outline-info" for="slPipsMode">Pips</label>
                                    </div>
                                </div>
                                <input type="number" class="form-control form-control-lg" id="slPips" value="10" min="0.01" step="0.01" required placeholder="Ex: 10" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px); display: none;">
                                <input type="number" class="form-control form-control-lg" id="slPrice" value="" min="0.01" step="0.00001" placeholder="Ex: 2015.50" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                <small class="text-white-50" id="slDescription">Valeur exacte du stop loss</small>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-bold text-white">
                                    <i class="fas fa-bullseye me-2 text-success"></i>Take Profit (Optionnel)
                                </label>
                                <div class="mb-2">
                                    <div class="btn-group w-100" role="group">
                                        <input type="radio" class="btn-check" name="tpMode" id="tpPriceMode" value="price" checked>
                                        <label class="btn btn-outline-success" for="tpPriceMode">Prix</label>
                                        <input type="radio" class="btn-check" name="tpMode" id="tpPipsMode" value="pips">
                                        <label class="btn btn-outline-success" for="tpPipsMode">Pips</label>
                                    </div>
                                </div>
                                <input type="number" class="form-control form-control-lg" id="tpPips" value="" min="0.01" step="0.01" placeholder="Ex: 20" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px); display: none;">
                                <input type="number" class="form-control form-control-lg" id="tpPrice" value="" min="0.01" step="0.00001" placeholder="Ex: 2045.50" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; backdrop-filter: blur(10px);">
                                <small class="text-white-50" id="tpDescription">Valeur exacte du take profit</small>
                            </div>
                        </div>
                        
                        <!-- Bouton de Calcul -->
                        <div class="text-center mt-4">
                            <button type="submit" class="btn btn-lg px-5" id="calculateBtn" style="background: linear-gradient(45deg, #00ff88, #00cc6a); border: none; color: black; font-weight: bold; border-radius: 25px; box-shadow: 0 5px 15px rgba(0,255,136,0.3);">
                                <i class="fas fa-calculator me-2"></i>Calculer la Position Optimale
                            </button>
                        </div>
                    </form>
                    
                    <!-- Bloc de résultats complet -->
                    <div id="calculatorResults" class="mt-5" style="display: none;">
                        <!-- Le contenu sera généré dynamiquement par JavaScript -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <style>
        .price-display {{
            animation: fadeInUp 0.5s ease;
        }}
        
        .price-value {{
            animation: pulse 2s infinite;
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        
        .calculator-card {{
            transition: all 0.3s ease;
        }}
        
        .calculator-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }}
        
        .btn-check:checked + .btn {{
            transform: scale(1.05);
        }}
    </style>
    
    <script>
        // Calculateur MindTraderPro
        document.addEventListener('DOMContentLoaded', function() {{
            setupCalculator();
        }});

        function setupCalculator() {{
            const pairSelect = document.getElementById('pairSymbol');
            if (pairSelect) {{
                pairSelect.addEventListener('change', updateRealTimePrice);
            }}
            
            setupToggleButtons();
            setupCalculateButton();
            setupValidationListeners();
        }}
        
        function setupValidationListeners() {{
            // Éléments à surveiller pour la validation
            const entryPrice = document.getElementById('entryPrice');
            const slPrice = document.getElementById('slPrice');
            const tpPrice = document.getElementById('tpPrice');
            const buyRadio = document.querySelector('input[name="orderType"][value="BUY"]');
            const sellRadio = document.querySelector('input[name="orderType"][value="SELL"]');
            const slModeInputs = document.querySelectorAll('input[name="slMode"]');
            const tpModeInputs = document.querySelectorAll('input[name="tpMode"]');
            
            // Ajout des événements
            if (entryPrice) entryPrice.addEventListener('input', validateTradingLogic);
            if (slPrice) slPrice.addEventListener('input', validateTradingLogic);
            if (tpPrice) tpPrice.addEventListener('input', validateTradingLogic);
            if (buyRadio) buyRadio.addEventListener('change', validateTradingLogic);
            if (sellRadio) sellRadio.addEventListener('change', validateTradingLogic);
            
            slModeInputs.forEach(input => {{
                input.addEventListener('change', validateTradingLogic);
            }});
            
            tpModeInputs.forEach(input => {{
                input.addEventListener('change', validateTradingLogic);
            }});
        }}

        function setupCalculateButton() {{
            const calculateBtn = document.getElementById('calculateBtn');
            if (calculateBtn) {{
                calculateBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    calculatePosition();
                }});
            }}
        }}

        function validateTradingLogic() {{
            const entryPrice = parseFloat(document.getElementById('entryPrice').value) || 0;
            const tradeDirection = document.querySelector('input[name="orderType"]:checked')?.value?.toLowerCase() || 'buy';
            const calculateBtn = document.getElementById('calculateBtn');
            
            let hasErrors = false;
            
            // Réinitialiser tous les styles d'erreur
            clearValidationErrors();
            
            if (entryPrice > 0) {{
                // Vérification SL en mode prix
                const slPriceMode = document.querySelector('input[name="slMode"]:checked')?.value === 'price';
                if (slPriceMode) {{
                    const slInput = document.getElementById('slPrice');
                    const slPrice = parseFloat(slInput?.value) || 0;
                    
                    if (slPrice > 0 && slInput) {{
                        let slError = false;
                        let slErrorMsg = '';
                        let slTooltip = '';
                        
                        if (tradeDirection === 'buy' && slPrice >= entryPrice) {{
                            slError = true;
                            slErrorMsg = 'SL invalide pour un ordre BUY';
                            slTooltip = 'Le Stop Loss doit être inférieur au prix d\\'entrée pour un ordre BUY';
                        }} else if (tradeDirection === 'sell' && slPrice <= entryPrice) {{
                            slError = true;
                            slErrorMsg = 'SL invalide pour un ordre SELL';
                            slTooltip = 'Le Stop Loss doit être supérieur au prix d\\'entrée pour un ordre SELL';
                        }}
                        
                        if (slError) {{
                            showFieldError(slInput, slErrorMsg, slTooltip);
                            hasErrors = true;
                        }}
                    }}
                }}
                
                // Vérification TP en mode prix
                const tpPriceMode = document.querySelector('input[name="tpMode"]:checked')?.value === 'price';
                if (tpPriceMode) {{
                    const tpInput = document.getElementById('tpPrice');
                    const tpPrice = parseFloat(tpInput?.value) || 0;
                    
                    if (tpPrice > 0 && tpInput) {{
                        let tpError = false;
                        let tpErrorMsg = '';
                        let tpTooltip = '';
                        
                        if (tradeDirection === 'buy' && tpPrice <= entryPrice) {{
                            tpError = true;
                            tpErrorMsg = 'TP invalide pour un ordre BUY';
                            tpTooltip = 'Le Take Profit doit être supérieur au prix d\\'entrée pour un ordre BUY';
                        }} else if (tradeDirection === 'sell' && tpPrice >= entryPrice) {{
                            tpError = true;
                            tpErrorMsg = 'TP invalide pour un ordre SELL';
                            tpTooltip = 'Le Take Profit doit être inférieur au prix d\\'entrée pour un ordre SELL';
                        }}
                        
                        if (tpError) {{
                            showFieldError(tpInput, tpErrorMsg, tpTooltip);
                            hasErrors = true;
                        }}
                    }}
                }}
            }}
            
            // Gestion du bouton de calcul
            if (calculateBtn) {{
                if (hasErrors) {{
                    calculateBtn.disabled = true;
                    calculateBtn.style.opacity = '0.5';
                    calculateBtn.style.cursor = 'not-allowed';
                }} else {{
                    calculateBtn.disabled = false;
                    calculateBtn.style.opacity = '1';
                    calculateBtn.style.cursor = 'pointer';
                }}
            }}
        }}
        
        function showFieldError(inputElement, errorMessage, tooltipText) {{
            // Bordure rouge sur le champ
            inputElement.style.border = '2px solid #FF5555';
            inputElement.style.boxShadow = '0 0 5px rgba(255, 85, 85, 0.3)';
            
            // Créer ou mettre à jour le message d'erreur
            const fieldId = inputElement.id;
            let errorDiv = document.getElementById(fieldId + '_error');
            
            if (!errorDiv) {{
                errorDiv = document.createElement('div');
                errorDiv.id = fieldId + '_error';
                errorDiv.className = 'field-error';
                errorDiv.style.cssText = 'color: #FF5555; font-size: 0.85em; margin-top: 4px; font-weight: 500;';
                inputElement.parentNode.appendChild(errorDiv);
            }}
            
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${{errorMessage}}`;
            
            // Créer ou mettre à jour l'icône d'erreur avec tooltip
            let errorIcon = document.getElementById(fieldId + '_icon');
            
            if (!errorIcon) {{
                errorIcon = document.createElement('i');
                errorIcon.id = fieldId + '_icon';
                errorIcon.className = 'fas fa-exclamation-triangle';
                errorIcon.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #FF5555; cursor: help; z-index: 10;';
                errorIcon.title = tooltipText;
                
                // Positionner l'icône relativement au parent
                const parentDiv = inputElement.parentNode;
                if (parentDiv.style.position !== 'relative') {{
                    parentDiv.style.position = 'relative';
                }}
                parentDiv.appendChild(errorIcon);
            }} else {{
                errorIcon.title = tooltipText;
            }}
        }}
        
        function clearValidationErrors() {{
            // Supprimer toutes les erreurs visuelles
            document.querySelectorAll('.field-error').forEach(el => el.remove());
            document.querySelectorAll('[id$="_icon"]').forEach(el => el.remove());
            
            // Réinitialiser les styles des champs
            const inputs = ['slPrice', 'tpPrice'];
            inputs.forEach(inputId => {{
                const input = document.getElementById(inputId);
                if (input) {{
                    input.style.border = '';
                    input.style.boxShadow = '';
                }}
            }});
        }}

        function calculatePosition() {{
            // Validation avant calcul
            validateTradingLogic();
            
            // Si erreur de validation, arrêter le calcul
            const errorDiv = document.getElementById('validationError');
            if (errorDiv && errorDiv.style.display === 'block') {{
                return;
            }}
            
            // Récupération des valeurs des champs
            const capital = parseFloat(document.getElementById('capital').value);
            const currency = document.getElementById('accountCurrency').value;
            const risk = parseFloat(document.getElementById('riskPercent').value);
            const entryPrice = parseFloat(document.getElementById('entryPrice').value) || 0;
            const symbol = document.getElementById('pairSymbol').value;
            
            // Vérification du type de trade
            const tradeDirection = document.querySelector('input[name="orderType"]:checked')?.value || 'buy';
            
            // Récupération du Stop Loss
            let stopLoss, stopLossPips;
            const slPipsMode = document.getElementById('slPipsMode');
            if (slPipsMode && slPipsMode.checked) {{
                stopLossPips = parseFloat(document.getElementById('slPips').value);
            }} else {{
                const stopLossPrice = parseFloat(document.getElementById('slPrice').value);
                if (entryPrice > 0 && stopLossPrice > 0) {{
                    let pipSize = getPipSize(symbol);
                    stopLossPips = Math.abs(entryPrice - stopLossPrice) / pipSize;
                }} else {{
                    showError('Prix d\\'entrée requis pour calculer avec un prix de stop loss');
                    return;
                }}
            }}
            
            // Récupération du Take Profit (optionnel)
            let takeProfitPips = null;
            const tpPipsMode = document.getElementById('tpPipsMode');
            if (tpPipsMode && tpPipsMode.checked) {{
                const tpValue = document.getElementById('tpPips').value;
                if (tpValue) takeProfitPips = parseFloat(tpValue);
            }} else {{
                const takeProfitPrice = parseFloat(document.getElementById('tpPrice').value);
                if (entryPrice > 0 && takeProfitPrice > 0) {{
                    let pipSize = getPipSize(symbol);
                    takeProfitPips = Math.abs(takeProfitPrice - entryPrice) / pipSize;
                }}
            }}
            
            // Validation des entrées
            if (!capital || capital <= 0) {{
                showError('Capital invalide');
                return;
            }}
            if (!risk || risk <= 0) {{
                showError('Pourcentage de risque invalide');
                return;
            }}
            if (!stopLossPips || stopLossPips <= 0) {{
                showError('Stop loss invalide');
                return;
            }}
            
            // Calcul de la position avec spécifications d'instruments
            const specs = getInstrumentSpecs(symbol);
            let pipSize = specs.pipSize;
            let contractSize = specs.contractSize;
            let pipValue = contractSize * pipSize;
            let riskAmount = (capital * risk) / 100;
            
            // Calcul des pips de stop loss
            let slPipsCalculated = stopLossPips;
            if (!slPipsMode || !slPipsMode.checked) {{
                // Si SL donné en prix, recalculer les pips
                const stopLossPrice = parseFloat(document.getElementById('slPrice').value);
                slPipsCalculated = Math.abs(entryPrice - stopLossPrice) / pipSize;
            }}
            
            // Calcul de la taille de position : (capital * riskPercent / 100) / (stopLossPips * pipValue)
            let positionSize = riskAmount / (slPipsCalculated * pipValue);
            
            // Calcul du gain potentiel
            let potentialGain = null;
            let rrRatio = null;
            let tpPipsCalculated = takeProfitPips;
            
            if (takeProfitPips) {{
                if (!tpPipsMode || !tpPipsMode.checked) {{
                    // Si TP donné en prix, recalculer les pips
                    const takeProfitPrice = parseFloat(document.getElementById('tpPrice').value);
                    if (entryPrice > 0 && takeProfitPrice > 0) {{
                        tpPipsCalculated = Math.abs(entryPrice - takeProfitPrice) / pipSize;
                    }}
                }}
                
                if (tpPipsCalculated) {{
                    potentialGain = (positionSize * tpPipsCalculated * pipValue).toFixed(2);
                    rrRatio = (tpPipsCalculated / slPipsCalculated).toFixed(2);
                }}
            }}
            
            // Calcul des prix SL/TP basés sur la direction du trade
            let stopLossPrice = 0;
            let takeProfitPrice = 0;
            
            if (entryPrice > 0) {{
                // Conversion en nombre pour éviter NaN
                const safeEntryPrice = parseFloat(entryPrice) || 0;
                const safePipSize = parseFloat(pipSize) || 0.0001;
                const safeSlPips = parseFloat(slPipsCalculated) || 0;
                const safeTpPips = parseFloat(tpPipsCalculated) || 0;
                
                // Calcul du prix SL selon la direction
                if (tradeDirection === 'buy') {{
                    stopLossPrice = safeEntryPrice - (safeSlPips * safePipSize);
                }} else {{
                    stopLossPrice = safeEntryPrice + (safeSlPips * safePipSize);
                }}
                
                // Calcul du prix TP selon la direction (si TP défini)
                if (safeTpPips > 0) {{
                    if (tradeDirection === 'buy') {{
                        takeProfitPrice = safeEntryPrice + (safeTpPips * safePipSize);
                    }} else {{
                        takeProfitPrice = safeEntryPrice - (safeTpPips * safePipSize);
                    }}
                }}
            }}
            
            // Affichage du résultat
            showResult({{
                lotSize: positionSize.toFixed(2),
                riskAmount: riskAmount.toFixed(2),
                stopLossPips: slPipsCalculated.toFixed(1),
                stopLossPrice: stopLossPrice > 0 ? stopLossPrice.toFixed(2) : '0.00',
                takeProfitPips: tpPipsCalculated ? tpPipsCalculated.toFixed(1) : null,
                takeProfitPrice: takeProfitPrice > 0 ? takeProfitPrice.toFixed(2) : null,
                potentialGain: potentialGain,
                rrRatio: rrRatio,
                pipValue: pipValue.toFixed(2),
                contractSize: contractSize,
                pipSize: pipSize,
                currency: currency,
                capital: capital,
                entryPrice: entryPrice,
                orderType: tradeDirection
            }});
        }}

        function getPipSize(symbol) {{
            if (symbol.includes("JPY")) return 0.01;
            if (symbol.includes("XAU")) return 0.1;
            if (symbol.includes("XAG")) return 0.01;
            return 0.0001;
        }}

        function getInstrumentSpecs(symbol) {{
            // Métaux Précieux
            if (symbol.includes('XAU')) {{
                return {{
                    pipSize: 0.1,
                    contractSize: 100
                }};
            }}
            if (symbol.includes('XAG')) {{
                return {{
                    pipSize: 0.01,
                    contractSize: 5000
                }};
            }}
            
            // Paires avec le Yen Japonais
            if (symbol.includes('JPY')) {{
                return {{
                    pipSize: 0.01,
                    contractSize: 100000
                }};
            }}
            
            // Forex Paires Standard
            return {{
                pipSize: 0.0001,
                contractSize: 100000
            }};
        }}

        function getPipValue(symbol) {{
            const specs = getInstrumentSpecs(symbol);
            return specs.contractSize * specs.pipSize;
        }}

        function getPipValuePerLot(symbol) {{
            return getPipValue(symbol);
        }}

        function showResult(result) {{
            // Sauvegarder les résultats pour le partage
            lastCalculationResult = result;
            
            const container = document.getElementById('calculatorResults');
            
            container.innerHTML = `
                <div style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px);">
                    <div class="text-center mb-4">
                        <h4 class="mb-2" style="color: #ffffff; font-weight: bold;">
                            <i class="fas fa-check-circle me-2 text-success"></i>Position Calculée
                        </h4>
                        <p style="color: #e0e0e0;">Résultats basés sur vos paramètres de risque</p>
                    </div>
                    
                    <div class="row g-3 mb-4">
                        <div class="col-md-6" style="margin-bottom: 16px;">
                            <div class="d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #00ffcc, #0099cc); border-radius: 14px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); padding: 16px; min-height: 80px;">
                                <div style="color: #ffffff; font-weight: bold; font-size: 1.2em; font-variant: small-caps; letter-spacing: 0.5px; text-align: center;">Taille de position : ${{result.lotSize}} lots</div>
                            </div>
                        </div>
                        <div class="col-md-6" style="margin-bottom: 16px;">
                            <div class="d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #ffcc00, #ff8800); border-radius: 14px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); padding: 16px; min-height: 80px;">
                                <div style="color: #ffffff; font-weight: bold; font-size: 1.2em; font-variant: small-caps; letter-spacing: 0.5px; text-align: center;">Montant à risque : ${{result.riskAmount}} ${{result.currency}} (${{(result.riskAmount / result.capital * 100).toFixed(2)}}%)</div>
                            </div>
                        </div>

                        <div class="col-md-6" style="margin-bottom: 16px;">
                            <div class="d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #66ccff, #3366ff); border-radius: 14px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); padding: 16px; min-height: 80px;">
                                <div style="color: #ffffff; font-weight: bold; font-size: 16px; text-align: center; line-height: 1.6;">
                                    ${{result.entryPrice && result.entryPrice > 0 ? `<div style="margin-bottom: 8px;"><span style="color: ${{result.orderType && result.orderType.toLowerCase() === 'buy' ? '#00FF00' : '#FF5555'}};">${{result.orderType ? result.orderType.toUpperCase() : 'BUY'}}</span> : <span style="color: #ffffff;">${{parseFloat(result.entryPrice).toFixed(2)}}</span></div>` : ''}}
                                    ${{result.takeProfitPrice && result.takeProfitPrice !== 'null' && result.takeProfitPrice !== '0.00' ? `<div style="margin-bottom: 8px; color: #ffffff;">TP : ${{result.takeProfitPrice}} (<span style="color: ${{result.slPips && result.tpPips && result.slPips > result.tpPips ? '#FF5555' : '#ffffff'}};">${{result.takeProfitPips}} pips</span>)</div>` : ''}}
                                    <div style="color: #ffffff;">SL : ${{result.stopLossPrice}} (<span style="color: ${{result.slPips && result.tpPips && result.slPips > result.tpPips ? '#FF5555' : '#ffffff'}};">${{result.stopLossPips}} pips</span>)</div>
                                </div>
                            </div>
                        </div>
                        ${{result.potentialGain ? `
                        <div class="col-md-6" style="margin-bottom: 16px;">
                            <div class="d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #66ff99, #33cc66); border-radius: 14px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); padding: 16px; min-height: 80px;">
                                <div style="color: #ffffff; font-weight: bold; font-size: 1.2em; font-variant: small-caps; letter-spacing: 0.5px; text-align: center;">Gain potentiel : ${{result.potentialGain}} ${{result.currency}} (${{(result.potentialGain / result.capital * 100).toFixed(2)}}%)</div>
                            </div>
                        </div>` : ''}}
                        ${{result.rrRatio ? `
                        <div class="col-md-6" style="margin-bottom: 16px;">
                            <div class="d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #ccccff, #6666ff); border-radius: 14px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); padding: 16px; min-height: 80px;">
                                <div style="font-weight: bold; font-size: 1.2em; font-variant: small-caps; letter-spacing: 0.5px; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                                    <span style="color: #ffffff;">R:R </span>
                                    <span style="color: ${{result.rrRatio && parseFloat(result.rrRatio) >= 1.00 ? '#00FF00' : '#FF5555'}};">${{result.rrRatio}}</span>
                                </div>
                            </div>
                        </div>` : ''}}
                    </div>
                    
                    <!-- Boutons d'action -->
                    <div class="text-center mt-4">
                        <div class="row g-2">
                            <div class="col-md-6">
                                <button type="button" class="btn btn-success btn-lg w-100" onclick="generateShareImage()" style="background: linear-gradient(135deg, #28a745, #20c997); border: none; color: white;">
                                    <i class="fas fa-share-alt me-2"></i>Partager le Résultat
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button type="button" class="btn btn-outline-light btn-lg w-100" onclick="window.location.reload()" style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); border: none; color: white;">
                                    <i class="fas fa-redo me-2"></i>Réinitialiser
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            container.style.display = 'block';
            container.scrollIntoView({{ behavior: 'smooth' }});
            
            // Transformer le bouton en bouton Réinitialiser
            const calculateBtn = document.getElementById('calculateBtn');
            if (calculateBtn) {{
                calculateBtn.innerHTML = '<i class="fas fa-redo me-2"></i>Réinitialiser';
                calculateBtn.style.background = 'linear-gradient(135deg, #ff6b6b, #ee5a24)';
                calculateBtn.style.border = 'none';
                calculateBtn.style.color = 'white';
                calculateBtn.style.minWidth = '200px';
                calculateBtn.className = 'btn btn-outline-light btn-lg w-100';
                calculateBtn.onclick = function(e) {{
                    e.preventDefault();
                    window.location.reload();
                }};
            }}
        }}

        // Variable globale pour stocker les derniers résultats
        let lastCalculationResult = null;

        function generateShareImage() {{
            if (!lastCalculationResult) {{
                alert('Aucun résultat à partager. Effectuez d abord un calcul.');
                return;
            }}

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Dimensions de l'image (format carré Instagram)
            canvas.width = 1080;
            canvas.height = 1080;
            
            // Fond dégradé
            const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
            gradient.addColorStop(0, '#1a1a2e');
            gradient.addColorStop(1, '#16213e');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // En-tête MindTraderPro
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 48px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('MindTraderPro', canvas.width / 2, 100);
            
            // Titre
            ctx.fillStyle = '#00ff88';
            ctx.font = 'bold 36px Arial';
            ctx.fillText('Résultat de mon Trade', canvas.width / 2, 180);
            
            // Bloc central avec fond
            const blockX = 100;
            const blockY = 250;
            const blockWidth = canvas.width - 200;
            const blockHeight = 600;
            
            // Fond du bloc avec bordure arrondie
            ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.roundRect(blockX, blockY, blockWidth, blockHeight, 20);
            ctx.fill();
            
            // Informations du trade
            let yPos = blockY + 80;
            const lineHeight = 70;
            
            // Type d'ordre (BUY/SELL)
            const orderType = lastCalculationResult.orderType || 'BUY';
            ctx.fillStyle = orderType === 'BUY' ? '#00FF00' : '#FF5555';
            ctx.font = 'bold 56px Arial';
            ctx.fillText(orderType, canvas.width / 2, yPos);
            yPos += lineHeight + 20;
            
            // Autres informations
            ctx.fillStyle = '#ffffff';
            ctx.font = '40px Arial';
            
            const infos = [
                `Entrée: ${{lastCalculationResult.entryPrice || 'N/A'}}`,
                `TP: ${{lastCalculationResult.takeProfitPrice || 'N/A'}} (${{lastCalculationResult.takeProfitPips || 'N/A'}} pips)`,
                `SL: ${{lastCalculationResult.stopLossPrice || 'N/A'}} (${{lastCalculationResult.stopLossPips || 'N/A'}} pips)`,
                `Lot: ${{lastCalculationResult.lotSize || 'N/A'}}`,
                `Risque: ${{lastCalculationResult.riskAmount || 'N/A'}} ${{lastCalculationResult.currency || ''}} (${{((lastCalculationResult.riskAmount / lastCalculationResult.capital) * 100).toFixed(2) || 'N/A'}}%)`,
                `R:R: ${{lastCalculationResult.rrRatio || 'N/A'}}`
            ];
            
            infos.forEach(info => {{
                ctx.fillText(info, canvas.width / 2, yPos);
                yPos += lineHeight;
            }});
            
            // Phrase d'accroche
            yPos = blockY + blockHeight + 80;
            ctx.fillStyle = '#00ff88';
            ctx.font = 'bold 32px Arial';
            ctx.fillText('Et toi, tu maîtrises tes trades ?', canvas.width / 2, yPos);
            
            // Logo/lien
            yPos += 60;
            ctx.fillStyle = '#cccccc';
            ctx.font = '28px Arial';
            ctx.fillText('mindtrader.pro', canvas.width / 2, yPos);
            
            // Télécharger l'image
            const link = document.createElement('a');
            link.download = 'mindtraderpro-resultat.png';
            link.href = canvas.toDataURL();
            link.click();
            
            // Afficher un message de succès
            alert('Image générée et téléchargée ! Vous pouvez maintenant la partager sur vos réseaux sociaux.');
        }}

        // Extension pour les bordures arrondies
        CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {{
            if (w < 2 * r) r = w / 2;
            if (h < 2 * r) r = h / 2;
            this.beginPath();
            this.moveTo(x + r, y);
            this.arcTo(x + w, y, x + w, y + h, r);
            this.arcTo(x + w, y + h, x, y + h, r);
            this.arcTo(x, y + h, x, y, r);
            this.arcTo(x, y, x + w, y, r);
            this.closePath();
            return this;
        }};

        function showError(message) {{
            const container = document.getElementById('calculatorResults');
            container.innerHTML = `
                <div class="alert alert-danger text-center" style="background: rgba(220,53,69,0.2); border: 1px solid rgba(220,53,69,0.3); color: #ff6b6b;">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${{message}}
                </div>
            `;
            container.style.display = 'block';
        }}

        function setupToggleButtons() {{
            const slPipsMode = document.getElementById('slPipsMode');
            const slPriceMode = document.getElementById('slPriceMode');
            const tpPipsMode = document.getElementById('tpPipsMode');
            const tpPriceMode = document.getElementById('tpPriceMode');
            
            if (slPipsMode) {{
                slPipsMode.addEventListener('change', function() {{
                    if (this.checked) {{
                        document.getElementById('slPips').style.display = 'block';
                        document.getElementById('slPrice').style.display = 'none';
                        document.getElementById('slDescription').textContent = 'Distance en pips entre votre entrée et votre stop loss';
                    }}
                }});
            }}
            
            if (slPriceMode) {{
                slPriceMode.addEventListener('change', function() {{
                    if (this.checked) {{
                        document.getElementById('slPips').style.display = 'none';
                        document.getElementById('slPrice').style.display = 'block';
                        document.getElementById('slDescription').textContent = 'Prix exact de votre stop loss';
                    }}
                }});
            }}
            
            if (tpPipsMode) {{
                tpPipsMode.addEventListener('change', function() {{
                    if (this.checked) {{
                        document.getElementById('tpPips').style.display = 'block';
                        document.getElementById('tpPrice').style.display = 'none';
                        document.getElementById('tpDescription').textContent = 'Distance en pips entre votre entrée et votre take profit';
                    }}
                }});
            }}
            
            if (tpPriceMode) {{
                tpPriceMode.addEventListener('change', function() {{
                    if (this.checked) {{
                        document.getElementById('tpPips').style.display = 'none';
                        document.getElementById('tpPrice').style.display = 'block';
                        document.getElementById('tpDescription').textContent = 'Prix exact de votre take profit';
                    }}
                }});
            }}
        }}

        // Prix d'entrée toujours visible maintenant

        function updateRealTimePrice() {{
            const pairSymbol = document.getElementById('pairSymbol').value;
            if (!pairSymbol) {{
                document.getElementById('priceDisplay').style.display = 'none';
                return;
            }}
            
            document.getElementById('priceDisplay').style.display = 'block';
            document.getElementById('priceLoading').style.display = 'block';
            
            fetch(`/api/current-price/${{pairSymbol}}`)
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('priceLoading').style.display = 'none';
                    
                    if (data.success) {{
                        document.getElementById('currentPrice').textContent = data.price;
                        document.getElementById('displayPairName').textContent = pairSymbol;
                        
                        // Animation de mise à jour
                        const priceElement = document.getElementById('currentPrice');
                        priceElement.style.transform = 'scale(1.1)';
                        priceElement.style.color = '#00ff88';
                        setTimeout(() => {{
                            priceElement.style.transform = 'scale(1)';
                        }}, 200);
                    }} else {{
                        document.getElementById('currentPrice').textContent = 'Prix non disponible';
                        document.getElementById('priceTimestamp').textContent = data.timestamp;
                        document.getElementById('priceSource').textContent = 'Erreur: ' + data.error;
                    }}
                }})
                .catch(error => {{
                    console.error('Erreur prix:', error);
                    document.getElementById('priceLoading').style.display = 'none';
                    document.querySelector('.price-info').style.display = 'block';
                    document.getElementById('currentPrice').textContent = 'Erreur de connexion';
                }});
        }}
        
        // Mise à jour automatique du prix toutes les 30 secondes
        function startPriceUpdates() {{
            clearInterval(priceUpdateInterval);
            priceUpdateInterval = setInterval(() => {{
                if (document.getElementById('pairSymbol').value) {{
                    updateRealTimePrice();
                }}
            }}, 30000);
        }}
        
        // Initialisation au chargement de la page
        document.addEventListener('DOMContentLoaded', function() {{
            // Mise à jour initiale du prix pour XAUUSD
            setTimeout(updateRealTimePrice, 1000);
            startPriceUpdates();
        }});
        
        document.getElementById('calculatorForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const calculateBtn = document.getElementById('calculateBtn');
            calculateBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Calcul en cours...';
            calculateBtn.disabled = true;
            
            const formData = new FormData();
            formData.append('pair_symbol', document.getElementById('pairSymbol').value);
            formData.append('order_type', document.querySelector('input[name="orderType"]:checked').value);
            formData.append('capital', document.getElementById('capital').value);
            formData.append('risk_percent', document.getElementById('riskPercent').value);
            
            // Gestion Stop Loss
            const slMode = document.querySelector('input[name="slMode"]:checked').value;
            const slValue = document.getElementById('slValue').value;
            
            if (slMode === 'pips') {{
                formData.append('sl_pips', slValue);
            }} else {{
                formData.append('sl_price', slValue);
                formData.append('entry_price', document.getElementById('entryPrice').value);
            }}
            
            // Gestion Take Profit
            const tpMode = document.querySelector('input[name="tpMode"]:checked').value;
            const tpValue = document.getElementById('tpValue').value;
            
            if (tpValue) {{
                if (tpMode === 'pips') {{
                    formData.append('tp_pips', tpValue);
                }} else {{
                    formData.append('tp_price', tpValue);
                    formData.append('entry_price', document.getElementById('entryPrice').value);
                }}
            }} else {{
                formData.append('tp_pips', '0');
            }}
            
            fetch('/calculate', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(data => {{
                calculateBtn.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculer la Position Optimale';
                calculateBtn.disabled = false;
                
                if (data.error) {{
                    document.getElementById('resultContent').innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Erreur: ${{data.error}}
                        </div>
                    `;
                }} else {{
                    const tpInfo = data.tp_pips > 0 ? `
                        <div class="col-md-6">
                            <strong>Profit potentiel:</strong> $$${{data.potential_profit || 'N/A'}}
                        </div>
                        <div class="col-md-6">
                            <strong>Ratio R/R:</strong> ${{data.risk_reward_ratio || 'N/A'}}
                        </div>
                    ` : '';
                    
                    document.getElementById('resultContent').innerHTML = `
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>Taille de lot recommandée:</strong> 
                                <span class="text-success fs-5">${{data.lot_size}} lots</span>
                            </div>
                            <div class="col-md-6">
                                <strong>Risque en USD:</strong> 
                                <span class="text-warning fs-5">${{data.risk_usd}} USD</span>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Valeur du pip:</strong> ${{data.pip_value}} USD
                            </div>
                            <div class="col-md-6">
                                <strong>Type d'ordre:</strong> ${{formData.get('order_type')}}
                            </div>
                            ${{tpInfo}}
                        </div>
                    `;
                }}
                document.getElementById('results').style.display = 'block';
                document.getElementById('results').scrollIntoView({{ behavior: 'smooth' }});
            }})
            .catch(error => {{
                console.error('Erreur:', error);
                calculateBtn.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculer la Position Optimale';
                calculateBtn.disabled = false;
                document.getElementById('resultContent').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Erreur de calcul. Veuillez réessayer.
                    </div>
                `;
                document.getElementById('results').style.display = 'block';
            }});
        }});
        
        // Gestion du basculement entre pips et prix
        document.addEventListener('DOMContentLoaded', function() {{
            // Écouteurs pour les modes Stop Loss
            document.querySelectorAll('input[name="slMode"]').forEach(radio => {{
                radio.addEventListener('change', updateSLMode);
            }});
            
            // Écouteurs pour les modes Take Profit
            document.querySelectorAll('input[name="tpMode"]').forEach(radio => {{
                radio.addEventListener('change', updateTPMode);
            }});
            
            // Initialiser les modes
            updateSLMode();
            updateTPMode();
        }});
        
        function updateSLMode() {{
            const slMode = document.querySelector('input[name="slMode"]:checked').value;
            const slHint = document.getElementById('slHint');
            const slValue = document.getElementById('slValue');
            
            if (slMode === 'pips') {{
                slHint.textContent = 'Distance en pips pour limiter les pertes';
                slValue.placeholder = 'Ex: 10';
            }} else {{
                slHint.textContent = 'Valeur exacte du stop loss';
                slValue.placeholder = 'Ex: 2015.50';
            }}
            checkEntryPriceVisibility();
        }}
        
        function updateTPMode() {{
            const tpMode = document.querySelector('input[name="tpMode"]:checked').value;
            const tpHint = document.getElementById('tpHint');
            const tpValue = document.getElementById('tpValue');
            
            if (tpMode === 'pips') {{
                tpHint.textContent = 'Distance en pips pour prendre les profits';
                tpValue.placeholder = 'Ex: 20';
            }} else {{
                tpHint.textContent = 'Valeur exacte du take profit';
                tpValue.placeholder = 'Ex: 2045.50';
            }}
            checkEntryPriceVisibility();
        }}
        
        function checkEntryPriceVisibility() {{
            const slMode = document.querySelector('input[name="slMode"]:checked').value;
            const tpMode = document.querySelector('input[name="tpMode"]:checked').value;
            const entryPriceRow = document.getElementById('entryPriceRow');
            
            // Afficher le prix d'entrée si au moins un mode est en "prix"
            if (slMode === 'price' || tpMode === 'price') {{
                entryPriceRow.style.display = 'block';
            }} else {{
                entryPriceRow.style.display = 'none';
            }}
        }}
    </script>
    '''
    
    return get_page_template("Calculateur Avancé", content, "calculator")

@app.route('/journal')
@login_required
def journal():
    """Page journal avec navigation unifiée"""
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-book me-2 text-primary"></i>Journal de Trading</h2>
                <p class="text-muted">Suivez et analysez vos performances de trading</p>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Fonctionnalité en développement - Disponible bientôt pour les membres Premium et Lifetime
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Journal", content, "journal")

@app.route('/grades')
@login_required
def grades():
    """Page grades avec navigation unifiée"""
    
    content = '''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-medal me-2 text-warning"></i>Système de Grades</h2>
                <p class="text-muted">Progressez et débloquez de nouveaux avantages</p>
                
                <div class="alert alert-warning">
                    <i class="fas fa-construction me-2"></i>
                    Système de grades en cours de développement
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Grades", content, "grades")

@app.route('/suggestions')
@login_required
def suggestions():
    """Page suggestions avec navigation unifiée"""
    
    navbar = get_modern_navbar("suggestions")
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-lightbulb me-2 text-info"></i>Suggestions</h2>
                <p class="text-muted">Proposez vos idées pour améliorer MindTraderPro</p>
                
                <div class="alert alert-info">
                    <i class="fas fa-rocket me-2"></i>
                    Module de suggestions communautaires bientôt disponible
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Suggestions", navbar + content, "suggestions")

@app.route('/parrainage')
@login_required
def parrainage():
    """Page parrainage avec navigation unifiée"""
    
    navbar = get_modern_navbar("parrainage")
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-handshake me-2 text-success"></i>Programme de Parrainage</h2>
                <p class="text-muted">Invitez vos amis et gagnez des récompenses</p>
                
                <div class="alert alert-success">
                    <i class="fas fa-gift me-2"></i>
                    Système de parrainage avec récompenses progressives en préparation
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Parrainage", navbar + content, "parrainage")

@app.route('/leaderboard')
@login_required
def leaderboard():
    """Page leaderboard avec navigation unifiée"""
    
    navbar = get_modern_navbar("leaderboard")
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-trophy me-2 text-warning"></i>Classement des Traders</h2>
                <p class="text-muted">Découvrez les meilleurs traders de la communauté</p>
                
                <div class="alert alert-primary">
                    <i class="fas fa-chart-bar me-2"></i>
                    Système de classement basé sur les performances - Bientôt disponible
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Classement", navbar + content, "leaderboard")

@app.route('/leaderboard-parrainage')
@login_required
def leaderboard_parrainage():
    """Page leaderboard parrainage avec navigation unifiée"""
    
    navbar = get_modern_navbar("leaderboard-parrainage")
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-users me-2 text-success"></i>Classement des Parrains</h2>
                <p class="text-muted">Top des meilleurs ambassadeurs MindTraderPro</p>
                
                <div class="alert alert-info">
                    <i class="fas fa-star me-2"></i>
                    Classement des parrains avec badges et récompenses spéciales
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Parrains", navbar + content, "leaderboard-parrainage")

@app.route('/personnalisation')
@login_required
def personnalisation():
    """Page personnalisation avec navigation unifiée"""
    
    navbar = get_modern_navbar("personnalisation")
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-palette me-2 text-info"></i>Personnalisation</h2>
                <p class="text-muted">Customisez votre expérience MindTraderPro</p>
                
                <div class="alert alert-secondary">
                    <i class="fas fa-paint-brush me-2"></i>
                    Thèmes, avatars et personnalisation avancée en développement
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Personnalisation", navbar + content, "personnalisation")

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard utilisateur avec navigation unifiée"""
    
    navbar = get_modern_navbar("dashboard")
    user_info = get_user_session_info()
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-tachometer-alt me-2 text-primary"></i>Mon Dashboard</h2>
                <p class="text-muted">Vue d'ensemble de votre activité</p>
                
                <div class="row">
                    <div class="col-md-6 mb-4">
                        <div class="card bg-dark">
                            <div class="card-body">
                                <h5><i class="fas fa-user me-2"></i>Profil</h5>
                                <p><strong>Nom:</strong> {user_info['first_name']}</p>
                                <p><strong>Rôle:</strong> {user_info['role'].title()}</p>
                                <p><strong>XP:</strong> 2,450</p>
                                <p><strong>Grade:</strong> Trader Régulier</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-4">
                        <div class="card bg-dark">
                            <div class="card-body">
                                <h5><i class="fas fa-chart-line me-2"></i>Statistiques</h5>
                                <p><strong>Calculs effectués:</strong> 47</p>
                                <p><strong>Trades journalisés:</strong> 23</p>
                                <p><strong>Dernière connexion:</strong> Aujourd'hui</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Dashboard", navbar + content, "dashboard")

@app.route('/profil')
@login_required
def profil():
    """Page profil avec navigation unifiée"""
    
    navbar = get_modern_navbar("profil")
    user_info = get_user_session_info()
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-user me-2 text-success"></i>Mon Profil</h2>
                <p class="text-muted">Gérez vos informations personnelles</p>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="text-center mb-4">
                            <div class="user-avatar mx-auto" style="width: 120px; height: 120px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3rem; margin-bottom: 20px;">
                                <i class="fas fa-user text-white"></i>
                            </div>
                            <h4>{user_info['first_name']}</h4>
                            <span class="badge bg-primary">{user_info['role'].title()}</span>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card bg-dark">
                            <div class="card-body">
                                <h5>Informations du compte</h5>
                                <form>
                                    <div class="mb-3">
                                        <label class="form-label">Nom d'utilisateur</label>
                                        <input type="text" class="form-control" value="{user_info['first_name']}" readonly>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Rôle</label>
                                        <input type="text" class="form-control" value="{user_info['role'].title()}" readonly>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Points XP</label>
                                        <input type="text" class="form-control" value="2,450 XP" readonly>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Grade actuel</label>
                                        <input type="text" class="form-control" value="Trader Régulier" readonly>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Profil", navbar + content, "profil")

# ==================== AUTHENTIFICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        # Simulation de connexion pour la démo
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if username and password:
            # Création d'une session de test
            session['user_id'] = 1
            session['user_name'] = username
            session['user_first_name'] = username
            session['user_email'] = f"{username}@example.com"
            session['role'] = 'premium'
            session['is_authenticated'] = True
            session.permanent = True
            session.modified = True
            
            logging.info(f"✅ Connexion réussie pour {username}")
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(get_login_page("Nom d'utilisateur et mot de passe requis"))
    
    return render_template_string(get_login_page())

def get_login_page(error_message=""):
    """Template de la page de connexion"""
    navbar = get_modern_navbar("login")
    
    content = f'''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card bg-dark">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">
                            <i class="fas fa-sign-in-alt me-2"></i>Connexion
                        </h3>
                        
                        {f'<div class="alert alert-danger">{error_message}</div>' if error_message else ''}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Nom d'utilisateur</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-sign-in-alt me-2"></i>Se connecter
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Pas encore de compte ? <a href="/register">S'inscrire</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Connexion", navbar + content, "login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        # Simulation d'inscription pour la démo
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if username and email and password:
            # Création automatique d'une session après inscription
            session['user_id'] = 2
            session['user_name'] = username
            session['user_first_name'] = username
            session['user_email'] = email
            session['role'] = 'standard'
            session['is_authenticated'] = True
            session.permanent = True
            session.modified = True
            
            logging.info(f"✅ Inscription réussie pour {username}")
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(get_register_page("Tous les champs sont requis"))
    
    return render_template_string(get_register_page())

def get_register_page(error_message=""):
    """Template de la page d'inscription"""
    navbar = get_modern_navbar("register")
    
    content = f'''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card bg-dark">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">
                            <i class="fas fa-user-plus me-2"></i>Inscription
                        </h3>
                        
                        {f'<div class="alert alert-danger">{error_message}</div>' if error_message else ''}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Nom d'utilisateur</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">
                                <i class="fas fa-user-plus me-2"></i>Créer un compte
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Déjà un compte ? <a href="/login">Se connecter</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_page_template("Inscription", navbar + content, "register")

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    logging.info("✅ Déconnexion réussie")
    return redirect(url_for('home'))

# ==================== ROUTES ADMINISTRATIVES ====================

@app.route('/admin/market-pairs')
@admin_required
def admin_market_pairs():
    """Page d'administration des paires de devises"""
    
    # Initialiser les paires par défaut si nécessaire
    init_default_currency_pairs()
    
    # Récupération des paramètres de pagination et filtrage
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Construction de la requête
    query = CurrencyPair.query
    
    if category_filter:
        query = query.filter(CurrencyPair.category == category_filter)
    
    if status_filter == 'active':
        query = query.filter(CurrencyPair.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(CurrencyPair.is_active == False)
    
    if search_query:
        query = query.filter(
            db.or_(
                CurrencyPair.symbol.contains(search_query.upper()),
                CurrencyPair.name.contains(search_query.upper()),
                CurrencyPair.display_name.contains(search_query)
            )
        )
    
    # Pagination
    per_page = 10
    pairs_pagination = query.order_by(CurrencyPair.category, CurrencyPair.symbol).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques
    total_pairs = CurrencyPair.query.count()
    active_pairs = CurrencyPair.query.filter_by(is_active=True).count()
    inactive_pairs = total_pairs - active_pairs
    
    # Catégories disponibles
    categories = db.session.query(CurrencyPair.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    content = f'''
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="admin-header mb-4">
                    <h2 class="display-6 fw-bold">
                        <i class="fas fa-cogs me-3 text-primary"></i>Gestion des Paires de Devises
                    </h2>
                    <p class="lead text-muted">Administration des instruments financiers disponibles</p>
                </div>
                
                <!-- Statistiques -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="stat-card text-center" style="background: rgba(0,123,255,0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,123,255,0.3);">
                            <h3 class="text-primary">{total_pairs}</h3>
                            <p class="mb-0">Total des paires</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card text-center" style="background: rgba(40,167,69,0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(40,167,69,0.3);">
                            <h3 class="text-success">{active_pairs}</h3>
                            <p class="mb-0">Paires actives</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card text-center" style="background: rgba(220,53,69,0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(220,53,69,0.3);">
                            <h3 class="text-danger">{inactive_pairs}</h3>
                            <p class="mb-0">Paires inactives</p>
                        </div>
                    </div>
                </div>
                
                <!-- Barre d'actions -->
                <div class="actions-bar mb-4" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <button class="btn btn-success" onclick="showAddPairModal()">
                                <i class="fas fa-plus me-2"></i>Ajouter une nouvelle paire
                            </button>
                            <button class="btn btn-info ms-2" onclick="window.location.reload()">
                                <i class="fas fa-sync me-2"></i>Actualiser
                            </button>
                        </div>
                        <div class="col-md-6">
                            <form method="GET" class="d-flex">
                                <input type="text" class="form-control me-2" name="search" placeholder="Rechercher..." value="{search_query}">
                                <select class="form-select me-2" name="category">
                                    <option value="">Toutes catégories</option>
                                    {''.join([f'<option value="{cat}" {"selected" if cat == category_filter else ""}>{cat}</option>' for cat in categories])}
                                </select>
                                <select class="form-select me-2" name="status">
                                    <option value="">Tous statuts</option>
                                    <option value="active" {"selected" if status_filter == "active" else ""}>Actives</option>
                                    <option value="inactive" {"selected" if status_filter == "inactive" else ""}>Inactives</option>
                                </select>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-search"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <!-- Tableau des paires -->
                <div class="pairs-table" style="background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); overflow: hidden;">
                    <div class="table-responsive">
                        <table class="table table-dark table-hover mb-0">
                            <thead style="background: rgba(0,0,0,0.3);">
                                <tr>
                                    <th>Symbole</th>
                                    <th>Nom</th>
                                    <th>Catégorie</th>
                                    <th>Pip Size</th>
                                    <th>Pip Value</th>
                                    <th>Statut</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal d'ajout/modification -->
    <div class="modal fade" id="pairModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content bg-dark">
                <div class="modal-header">
                    <h5 class="modal-title" id="pairModalTitle">Ajouter une nouvelle paire</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form id="pairForm">
                    <div class="modal-body">
                        <input type="hidden" id="pairId" name="pair_id">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Symbole *</label>
                                <input type="text" class="form-control" id="symbol" name="symbol" required placeholder="Ex: EURUSD">
                                <small class="text-muted">Format: sans espace, majuscules</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Nom court *</label>
                                <input type="text" class="form-control" id="name" name="name" required placeholder="Ex: EUR/USD">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nom d'affichage *</label>
                            <input type="text" class="form-control" id="displayName" name="display_name" required placeholder="Ex: Euro / Dollar US">
                        </div>
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">Catégorie *</label>
                                <select class="form-select" id="category" name="category" required>
                                    <option value="">Sélectionnez...</option>
                                    <option value="Major">Major (Paires majeures)</option>
                                    <option value="Cross">Cross (Paires croisées)</option>
                                    <option value="Metal">Metal (Métaux précieux)</option>
                                    <option value="Crypto">Crypto (Cryptomonnaies)</option>
                                    <option value="Index">Index (Indices)</option>
                                </select>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">Devise de base *</label>
                                <input type="text" class="form-control" id="baseCurrency" name="base_currency" required placeholder="Ex: EUR">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">Devise de cotation *</label>
                                <input type="text" class="form-control" id="quoteCurrency" name="quote_currency" required placeholder="Ex: USD">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Taille du pip *</label>
                                <input type="number" class="form-control" id="pipSize" name="pip_size" step="0.00001" required placeholder="Ex: 0.0001">
                                <small class="text-muted">Ex: 0.0001 pour EUR/USD, 0.01 pour USD/JPY</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Valeur du pip *</label>
                                <input type="number" class="form-control" id="pipValue" name="pip_value" step="0.1" required placeholder="Ex: 10.0">
                                <small class="text-muted">Valeur en USD pour 1 lot standard</small>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="isActive" name="is_active" checked>
                                <label class="form-check-label" for="isActive">
                                    Paire active (visible dans le calculateur)
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="submit" class="btn btn-success">
                            <i class="fas fa-save me-2"></i>Enregistrer
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function showAddPairModal() {{
            document.getElementById('pairModalTitle').textContent = 'Ajouter une nouvelle paire';
            document.getElementById('pairForm').reset();
            document.getElementById('pairId').value = '';
            new bootstrap.Modal(document.getElementById('pairModal')).show();
        }}
        
        function editPair(pairId) {{
            fetch(`/admin/api/pairs/${{pairId}}`)
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        const pair = data.pair;
                        document.getElementById('pairModalTitle').textContent = 'Modifier la paire';
                        document.getElementById('pairId').value = pair.id;
                        document.getElementById('symbol').value = pair.symbol;
                        document.getElementById('name').value = pair.name;
                        document.getElementById('displayName').value = pair.display_name;
                        document.getElementById('category').value = pair.category;
                        document.getElementById('baseCurrency').value = pair.base_currency;
                        document.getElementById('quoteCurrency').value = pair.quote_currency;
                        document.getElementById('pipSize').value = pair.pip_size;
                        document.getElementById('pipValue').value = pair.pip_value;
                        document.getElementById('isActive').checked = pair.is_active;
                        new bootstrap.Modal(document.getElementById('pairModal')).show();
                    }}
                }});
        }}
        
        function togglePairStatus(pairId, isActive) {{
            fetch(`/admin/api/pairs/${{pairId}}/toggle`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{is_active: isActive}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    window.location.reload();
                }} else {{
                    alert('Erreur lors de la mise à jour du statut');
                }}
            }});
        }}
        
        function deletePair(pairId, symbol) {{
            if (confirm(`Êtes-vous sûr de vouloir supprimer la paire ${{symbol}} ?\\n\\nCette action est irréversible.`)) {{
                fetch(`/admin/api/pairs/${{pairId}}`, {{
                    method: 'DELETE'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        window.location.reload();
                    }} else {{
                        alert('Erreur lors de la suppression: ' + data.error);
                    }}
                }});
            }}
        }}
        
        document.getElementById('pairForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const formData = new FormData(this);
            const pairId = formData.get('pair_id');
            const url = pairId ? `/admin/api/pairs/${{pairId}}` : '/admin/api/pairs';
            const method = pairId ? 'PUT' : 'POST';
            
            const data = {{}};
            for (let [key, value] of formData.entries()) {{
                if (key !== 'pair_id') {{
                    data[key] = value;
                }}
            }}
            data.is_active = document.getElementById('isActive').checked;
            
            fetch(url, {{
                method: method,
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    bootstrap.Modal.getInstance(document.getElementById('pairModal')).hide();
                    window.location.reload();
                }} else {{
                    alert('Erreur: ' + data.error);
                }}
            }});
        }});
    </script>
    '''
    
    return get_page_template("Admin - Paires de Devises", content, "admin")

# ==================== API ADMIN ====================

@app.route('/admin/api/pairs', methods=['GET', 'POST'])
@admin_required
def admin_api_pairs():
    """API pour la gestion des paires de devises"""
    
    if request.method == 'GET':
        # Récupération de toutes les paires
        pairs = CurrencyPair.query.all()
        return jsonify({
            'success': True,
            'pairs': [pair.to_dict() for pair in pairs]
        })
    
    elif request.method == 'POST':
        # Création d'une nouvelle paire
        try:
            data = request.get_json()
            
            # Validation des données
            required_fields = ['symbol', 'name', 'display_name', 'category', 'base_currency', 'quote_currency', 'pip_size', 'pip_value']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'success': False, 'error': f'Le champ {field} est requis'})
            
            # Vérifier si le symbole existe déjà
            existing = CurrencyPair.query.filter_by(symbol=data['symbol'].upper()).first()
            if existing:
                return jsonify({'success': False, 'error': 'Ce symbole existe déjà'})
            
            # Créer la nouvelle paire
            pair = CurrencyPair(
                symbol=data['symbol'].upper(),
                name=data['name'].upper(),
                display_name=data['display_name'],
                category=data['category'],
                base_currency=data['base_currency'].upper(),
                quote_currency=data['quote_currency'].upper(),
                pip_size=float(data['pip_size']),
                pip_value=float(data['pip_value']),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(pair)
            db.session.commit()
            
            return jsonify({'success': True, 'pair': pair.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/api/pairs/<int:pair_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def admin_api_pair_detail(pair_id):
    """API pour la gestion d'une paire spécifique"""
    
    pair = CurrencyPair.query.get_or_404(pair_id)
    
    if request.method == 'GET':
        return jsonify({'success': True, 'pair': pair.to_dict()})
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Mise à jour des champs
            if 'symbol' in data:
                # Vérifier l'unicité si le symbole change
                if data['symbol'].upper() != pair.symbol:
                    existing = CurrencyPair.query.filter_by(symbol=data['symbol'].upper()).first()
                    if existing:
                        return jsonify({'success': False, 'error': 'Ce symbole existe déjà'})
                pair.symbol = data['symbol'].upper()
            
            if 'name' in data:
                pair.name = data['name'].upper()
            if 'display_name' in data:
                pair.display_name = data['display_name']
            if 'category' in data:
                pair.category = data['category']
            if 'base_currency' in data:
                pair.base_currency = data['base_currency'].upper()
            if 'quote_currency' in data:
                pair.quote_currency = data['quote_currency'].upper()
            if 'pip_size' in data:
                pair.pip_size = float(data['pip_size'])
            if 'pip_value' in data:
                pair.pip_value = float(data['pip_value'])
            if 'is_active' in data:
                pair.is_active = data['is_active']
            
            pair.updated_at = datetime.now()
            db.session.commit()
            
            return jsonify({'success': True, 'pair': pair.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(pair)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/api/pairs/<int:pair_id>/toggle', methods=['POST'])
@admin_required
def admin_api_toggle_pair(pair_id):
    """API pour activer/désactiver une paire"""
    try:
        pair = CurrencyPair.query.get_or_404(pair_id)
        data = request.get_json()
        
        pair.is_active = data.get('is_active', not pair.is_active)
        pair.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({'success': True, 'pair': pair.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# ==================== API PUBLIQUE ====================

@app.route('/api/pairs')
def api_pairs():
    """API publique pour récupérer les paires actives"""
    try:
        active_pairs = CurrencyPair.query.filter_by(is_active=True).order_by(CurrencyPair.category, CurrencyPair.symbol).all()
        
        # Organiser par catégories
        pairs_by_category = {}
        for pair in active_pairs:
            if pair.category not in pairs_by_category:
                pairs_by_category[pair.category] = []
            pairs_by_category[pair.category].append(pair.to_dict())
        
        return jsonify({
            'success': True,
            'pairs': pairs_by_category,
            'total': len(active_pairs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== API EXISTANTES ====================

@app.route('/get-real-time-price/<pair_symbol>')
def get_real_time_price_api(pair_symbol):
    """API pour récupérer le prix en temps réel d'une paire"""
    try:
        price_data = get_real_time_price(pair_symbol)
        return jsonify(price_data)
    except Exception as e:
        logging.error(f"Erreur API prix temps réel: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'price': 0,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

@app.route('/calculate', methods=['POST'])
def calculate():
    """API de calcul de position avancé"""
    try:
        pair_symbol = request.form.get('pair_symbol', 'XAUUSD')
        order_type = request.form.get('order_type', 'BUY')
        capital = float(request.form.get('capital', 20000))
        risk_percent = float(request.form.get('risk_percent', 0.5))
        sl_pips = float(request.form.get('sl_pips', 10))
        tp_pips = float(request.form.get('tp_pips', 0)) if request.form.get('tp_pips') else 0
        
        # Calcul de base de la position
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        if 'error' not in result:
            # Ajout des informations sur le type d'ordre
            result['order_type'] = order_type
            result['tpPips'] = tp_pips
            result['slPips'] = sl_pips
            
            # Calcul du profit potentiel si Take Profit défini
            if tp_pips > 0:
                potential_profit = result['lot_size'] * tp_pips * result['pip_value']
                result['potential_profit'] = round(potential_profit, 2)
                result['risk_reward_ratio'] = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
            
            # Ajout du prix actuel si possible
            price_data = get_real_time_price(pair_symbol)
            if price_data['success']:
                result['current_price'] = price_data['price']
                result['price_timestamp'] = price_data['timestamp']
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Erreur API calculate: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/health')
def health():
    """Point de contrôle santé"""
    user_info = get_user_session_info()
    return jsonify({
        'status': 'OK',
        'app': 'MindTraderPro',
        'version': '1.0',
        'navigation': 'Unified Modern System',
        'user_authenticated': user_info['is_authenticated'],
        'user_role': user_info['role'],
        'session_info': dict(session) if user_info['is_authenticated'] else 'Not authenticated'
    })

# Initialisation de la base de données au démarrage
with app.app_context():
    db.create_all()
    init_default_currency_pairs()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)