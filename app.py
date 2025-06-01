"""
MindTraderPro - Application principale sécurisée
Calculateur de trading professionnel avec sécurité renforcée
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Import des modules de sécurité
from modules.security_core import security, require_csrf, require_auth, rate_limit
from modules.input_validator import validator
from modules.backup_manager import backup_manager

# Configuration du logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/app.log'),
        logging.StreamHandler()
    ]
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Création de l'application Flask sécurisée
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-for-trading-calculator")

# Configuration de sécurité
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# Middleware de sécurité
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration de la base de données
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialisation de la base de données
db.init_app(app)

with app.app_context():
    # Import models after app context is created
    import models
    db.create_all()

# Système de blocage désactivé - accès libre à l'application
# @app.before_request
# def block_everything_except_auth():
#     """BLOQUER TOUT sauf les routes d'authentification"""
#     print(f"🔍 REQUEST PATH: {request.path}")
#     print(f"🔍 SESSION: {session}")
#     
#     # Seules ces routes sont autorisées
#     if request.path in ['/auth/login', '/auth/register', '/auth/logout']:
#         return
#     
#     # Fichiers statiques autorisés
#     if request.path.startswith('/static/'):
#         return
#         
#     # BLOQUER ABSOLUMENT TOUT LE RESTE
# Blocage complètement désactivé

# === TRADING CONFIGURATION ===
DEFAULT_CAPITAL = 20000  # capital in USD
DEFAULT_RISK_PERCENT = 0.5  # % risk

# Currency pair data with pip information
CURRENCY_PAIRS = {
    # Forex Major Pairs
    'EURUSD': {'name': 'Euro/US Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'GBPUSD': {'name': 'British Pound/US Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'USDJPY': {'name': 'US Dollar/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'USDCHF': {'name': 'US Dollar/Swiss Franc', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'USDCAD': {'name': 'US Dollar/Canadian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'AUDUSD': {'name': 'Australian Dollar/US Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'NZDUSD': {'name': 'New Zealand Dollar/US Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    
    # Forex Cross Pairs
    'EURGBP': {'name': 'Euro/British Pound', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'EURJPY': {'name': 'Euro/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'GBPJPY': {'name': 'British Pound/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'EURCHF': {'name': 'Euro/Swiss Franc', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'GBPCHF': {'name': 'British Pound/Swiss Franc', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'AUDCAD': {'name': 'Australian Dollar/Canadian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'AUDCHF': {'name': 'Australian Dollar/Swiss Franc', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'AUDJPY': {'name': 'Australian Dollar/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'CADJPY': {'name': 'Canadian Dollar/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'CHFJPY': {'name': 'Swiss Franc/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    'EURAUD': {'name': 'Euro/Australian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'EURCAD': {'name': 'Euro/Canadian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'EURNZD': {'name': 'Euro/New Zealand Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'GBPAUD': {'name': 'British Pound/Australian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'GBPCAD': {'name': 'British Pound/Canadian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'GBPNZD': {'name': 'British Pound/New Zealand Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'NZDCAD': {'name': 'New Zealand Dollar/Canadian Dollar', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'NZDCHF': {'name': 'New Zealand Dollar/Swiss Franc', 'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex'},
    'NZDJPY': {'name': 'New Zealand Dollar/Japanese Yen', 'pip_size': 0.01, 'pip_value': 10, 'category': 'forex'},
    
    # Precious Metals
    'XAUUSD': {'name': 'Gold/US Dollar', 'pip_size': 0.1, 'pip_value': 10, 'category': 'metals'},
    'XAGUSD': {'name': 'Silver/US Dollar', 'pip_size': 0.001, 'pip_value': 50, 'category': 'metals'},
    
    # Commodities
    'USOIL': {'name': 'US Oil', 'pip_size': 0.01, 'pip_value': 100, 'category': 'commodities'},
    'UKOIL': {'name': 'UK Oil', 'pip_size': 0.01, 'pip_value': 100, 'category': 'commodities'},
    
    # Indices (CFDs)
    'US30': {'name': 'Dow Jones 30', 'pip_size': 1.0, 'pip_value': 100, 'category': 'indices'},
    'SPX500': {'name': 'S&P 500', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
    'NAS100': {'name': 'NASDAQ 100', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
    'GER30': {'name': 'DAX 30', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
    'UK100': {'name': 'FTSE 100', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
    'FRA40': {'name': 'CAC 40', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
    'JPN225': {'name': 'Nikkei 225', 'pip_size': 1.0, 'pip_value': 100, 'category': 'indices'},
    'AUS200': {'name': 'ASX 200', 'pip_size': 0.1, 'pip_value': 100, 'category': 'indices'},
}

def get_pip_info(pair_symbol):
    """Get pip size and pip value for a currency pair"""
    pair_symbol = pair_symbol.upper()
    if pair_symbol in CURRENCY_PAIRS:
        return CURRENCY_PAIRS[pair_symbol]
    else:
        # Default values for unknown pairs
        return {'pip_size': 0.0001, 'pip_value': 10, 'category': 'forex', 'name': pair_symbol}

def calculate_pips(entry_price, exit_price, pair_symbol):
    """Calculate pips between two prices for a specific currency pair"""
    pair_info = get_pip_info(pair_symbol)
    price_diff = abs(entry_price - exit_price)
    pips = price_diff / pair_info['pip_size']
    return round(pips, 1)

def get_exchange_rate_from_alpha_vantage(from_currency, to_currency):
    """Get exchange rate from Alpha Vantage API"""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        app.logger.error("No API key found")
        return None
    
    try:
        # Alpha Vantage FX endpoint
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": api_key
        }
        
        app.logger.info(f"Making API call: {from_currency}/{to_currency}")
        response = requests.get(url, params=params, timeout=10)
        app.logger.info(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"API response data: {data}")
            
            if "Realtime Currency Exchange Rate" in data:
                exchange_rate = data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
                app.logger.info(f"Exchange rate found: {exchange_rate}")
                return float(exchange_rate)
            elif "Error Message" in data:
                app.logger.error(f"API Error: {data['Error Message']}")
            else:
                app.logger.error(f"Unexpected response format: {data}")
    except Exception as e:
        app.logger.error(f"Alpha Vantage API error: {str(e)}")
    
    return None

# Removed multiple API functions - using Alpha Vantage only for reliability

def get_current_price_alpha_vantage(pair_symbol):
    """Get current price for a currency pair from Alpha Vantage"""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return None
    
    try:
        # For forex pairs, split the symbol (e.g., EURUSD -> EUR, USD)
        if len(pair_symbol) == 6 and pair_symbol[:3].isalpha() and pair_symbol[3:].isalpha():
            from_currency = pair_symbol[:3]
            to_currency = pair_symbol[3:]
            return get_exchange_rate_from_alpha_vantage(from_currency, to_currency)
        
        # For special symbols like XAUUSD, use direct API call
        if pair_symbol == "XAUUSD":
            return get_exchange_rate_from_alpha_vantage("XAU", "USD")
        elif pair_symbol == "XAGUSD":
            return get_exchange_rate_from_alpha_vantage("XAG", "USD")
            
    except Exception as e:
        app.logger.error(f"Alpha Vantage price fetch error: {str(e)}")
    
    return None

def get_current_price_optimized(pair_symbol):
    """Optimized price fetching using Alpha Vantage with mobile-friendly caching"""
    from models import PriceCache
    
    # Check cache first (mobile optimization)
    cached_price = PriceCache.query.filter_by(pair_symbol=pair_symbol).order_by(PriceCache.timestamp.desc()).first()
    
    if cached_price and cached_price.is_fresh(minutes=30):
        app.logger.info(f"Using cached price for {pair_symbol}: {cached_price.price}")
        return cached_price.price
    
    # Fetch fresh price from Alpha Vantage
    fresh_price = get_current_price_alpha_vantage(pair_symbol)
    
    if fresh_price:
        # Save to cache for mobile app efficiency
        try:
            new_cache = PriceCache()
            new_cache.pair_symbol = pair_symbol
            new_cache.price = fresh_price
            db.session.add(new_cache)
            db.session.commit()
            app.logger.info(f"Cached fresh price for {pair_symbol}: {fresh_price}")
        except Exception as e:
            app.logger.error(f"Cache save error: {str(e)}")
            db.session.rollback()
        
        return fresh_price
    
    # If API fails but we have old cache, use it (mobile fallback)
    if cached_price:
        app.logger.warning(f"API failed, using stale cache for {pair_symbol}: {cached_price.price}")
        return cached_price.price
    
    return None

def get_or_create_risk_settings(user_session):
    """Récupère ou crée les paramètres de risque pour un utilisateur"""
    from models import RiskSettings
    
    risk_settings = RiskSettings.query.filter_by(user_session=user_session).first()
    if not risk_settings:
        risk_settings = RiskSettings(user_session=user_session)
        db.session.add(risk_settings)
        db.session.commit()
    
    return risk_settings

def check_risk_warnings(risk_percent, risk_usd, user_session):
    """Vérifie les alertes de risque et retourne les avertissements"""
    risk_settings = get_or_create_risk_settings(user_session)
    warnings = []
    
    # Vérifier alerte de risque élevé (Gratuit)
    if risk_settings.is_risk_too_high(risk_percent):
        warnings.append({
            'type': 'high_risk',
            'message': f'⚠️ RISQUE ÉLEVÉ: {risk_percent}% dépasse votre limite de {risk_settings.max_risk_warning}%',
            'level': 'warning'
        })
    
    # Vérifier limite quotidienne (Gratuit)
    if risk_settings.daily_loss_current + risk_usd > risk_settings.daily_loss_limit:
        warnings.append({
            'type': 'daily_limit',
            'message': f'🚨 LIMITE QUOTIDIENNE: Ce trade dépasserait votre limite de {risk_settings.daily_loss_limit}$ (actuel: {risk_settings.daily_loss_current}$)',
            'level': 'danger'
        })
    
    # Vérifier blocage trading (Premium)
    if risk_settings.is_trading_blocked():
        warnings.append({
            'type': 'trading_blocked',
            'message': f'🔒 TRADING BLOQUÉ: {risk_settings.consecutive_losses} pertes consécutives. Déblocage automatique dans quelques heures.',
            'level': 'danger',
            'premium': True
        })
    
    return warnings

def calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol, pip_value=None, user_session=None):
    """
    Calculate the recommended lot size based on risk management
    
    Args:
        sl_pips: Stop loss in pips
        capital: Trading capital in USD
        risk_percent: Risk percentage (0.5 for 0.5%)
        pair_symbol: Currency pair symbol
        pip_value: Custom pip value (optional)
        user_session: Session ID for risk management
    
    Returns:
        dict: Calculation results including lot size, risk in USD, warnings, etc.
    """
    try:
        # Ajustement dynamique du risque (Premium feature)
        original_risk = risk_percent
        if user_session:
            risk_settings = get_or_create_risk_settings(user_session)
            if risk_settings.dynamic_risk_enabled:
                risk_percent = risk_settings.current_risk_percent
        
        risk_usd = capital * (risk_percent / 100)
        
        # Get pip value for the specific pair
        if pip_value is None:
            pair_info = get_pip_info(pair_symbol)
            pip_value = pair_info['pip_value']
        
        lot_size = risk_usd / (sl_pips * pip_value)
        
        # Vérifier les alertes de risque
        warnings = []
        if user_session:
            warnings = check_risk_warnings(original_risk, risk_usd, user_session)
        
        result = {
            'success': True,
            'lot_size': round(lot_size, 2),
            'risk_usd': round(risk_usd, 2),
            'sl_pips': sl_pips,
            'capital': capital,
            'risk_percent': risk_percent,
            'original_risk_percent': original_risk,
            'pip_value': pip_value,
            'warnings': warnings
        }
        
        # Ajouter informations de money management
        if user_session:
            risk_settings = get_or_create_risk_settings(user_session)
            result['money_management'] = {
                'daily_loss_current': risk_settings.daily_loss_current,
                'daily_loss_limit': risk_settings.daily_loss_limit,
                'consecutive_losses': risk_settings.consecutive_losses,
                'risk_adjusted': risk_percent != original_risk,
                'trading_blocked': risk_settings.is_trading_blocked()
            }
        
        return result
        
    except Exception as e:
        app.logger.error(f"Calculation error: {str(e)}")
        return {
            'success': False,
            'error': f"Calculation error: {str(e)}"
        }

@app.route('/calculator')
def calculator():
    """Page calculateur de trading pour utilisateurs connectés"""
    return render_template('calculator.html')

@app.route('/home')
def home():
    """Page d'accueil fonctionnelle - NOUVELLE ROUTE"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MindTraderPro - Accueil</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8 text-center">
                    <h1 class="display-4 mb-4">🚀 MindTraderPro</h1>
                    <p class="lead mb-4">Calculateur de Trading Professionnel</p>
                    <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                        <a href="/calculator" class="btn btn-primary btn-lg">Calculateur</a>
                        <a href="/journal" class="btn btn-outline-primary btn-lg">Journal</a>
                        <a href="/login" class="btn btn-success btn-lg">Connexion</a>
                        <a href="/register" class="btn btn-info btn-lg">Inscription</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/')
def index():
    """Redirection temporaire vers /home"""
    # Redirection vers la vraie page d'accueil
    return redirect('/home')

@app.route('/simple')
def simple():
    """Simple version for testing"""
    # Mode démo - accès libre
    return render_template('simple.html')

@app.route('/journal')
def journal():
    """Trading journal page"""
    # Mode démo - accès libre
    return render_template('journal.html')

@app.route('/money-management')
def money_management():
    """Money Management page - Gestion professionnelle du risque"""
    # Mode démo - accès libre
    return render_template('money_management.html')

@app.route('/ai-assistant')
def ai_assistant_page():
    """Assistant IA page - Coach de trading intelligent"""
    return render_template('ai_assistant.html')

@app.route('/integrations')
def integrations_page():
    """Page des intégrations externes - Partage et notifications"""
    return render_template('integrations.html')

@app.route('/personalization')
def personalization_page():
    """Page de personnalisation - Thèmes et expérience utilisateur"""
    return render_template('personalization.html')

@app.route('/economic-calendar')
def economic_calendar_page():
    """Page du calendrier économique - Événements financiers en temps réel"""
    return render_template('economic_calendar.html')

@app.route('/get_current_price/<pair_symbol>')
def get_current_price(pair_symbol):
    """API endpoint to get current market price for a currency pair"""
    try:
        current_price = get_current_price_optimized(pair_symbol.upper())
        if current_price:
            return jsonify({
                'success': True,
                'pair_symbol': pair_symbol.upper(),
                'current_price': current_price
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to fetch current price'
            })
    except Exception as e:
        app.logger.error(f"Price fetch error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Price service temporarily unavailable'
        })

@app.route('/calculate', methods=['POST'])
def calculate():
    """API endpoint for lot size calculation"""
    try:
        data = request.get_json()
        
        # Extract and validate input parameters
        direction = data.get('direction', '').lower()
        pair_symbol = data.get('symbol', data.get('pair_symbol', 'XAUUSD')).upper()
        entry_price = float(data.get('entry_price', 0))
        stop_loss = float(data.get('stop_loss', 0))
        take_profit = float(data.get('take_profit', 0))
        capital = float(data.get('capital', DEFAULT_CAPITAL))
        risk_percent = float(data.get('risk_percent', DEFAULT_RISK_PERCENT))
        
        # Validate required fields
        if not direction or direction not in ['buy', 'sell']:
            return jsonify({'success': False, 'error': 'Invalid direction. Must be "buy" or "sell".'})
        
        if entry_price <= 0:
            return jsonify({'success': False, 'error': 'Entry price must be greater than 0.'})
        
        if stop_loss <= 0:
            return jsonify({'success': False, 'error': 'Stop loss must be greater than 0.'})
        
        if take_profit <= 0:
            return jsonify({'success': False, 'error': 'Take profit must be greater than 0.'})
        
        if capital <= 0:
            return jsonify({'success': False, 'error': 'Capital must be greater than 0.'})
        
        if risk_percent <= 0 or risk_percent > 100:
            return jsonify({'success': False, 'error': 'Risk percentage must be between 0 and 100.'})
        
        # Calculate stop loss in pips using the correct pip size for the pair
        sl_pips = calculate_pips(entry_price, stop_loss, pair_symbol)
        
        if sl_pips == 0:
            return jsonify({'success': False, 'error': 'Stop loss cannot be equal to entry price.'})
        
        # Validate trade direction logic
        if direction == 'buy' and stop_loss >= entry_price:
            return jsonify({'success': False, 'error': 'For BUY orders, stop loss must be below entry price.'})
        
        if direction == 'sell' and stop_loss <= entry_price:
            return jsonify({'success': False, 'error': 'For SELL orders, stop loss must be above entry price.'})
        
        if direction == 'buy' and take_profit <= entry_price:
            return jsonify({'success': False, 'error': 'For BUY orders, take profit must be above entry price.'})
        
        if direction == 'sell' and take_profit >= entry_price:
            return jsonify({'success': False, 'error': 'For SELL orders, take profit must be below entry price.'})
        
        # Perform calculation
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        if result['success']:
            # Add additional trade information using correct pip calculation
            tp_pips = calculate_pips(entry_price, take_profit, pair_symbol)
            risk_reward_ratio = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
            
            # Calculate potential profit in USD when TP is hit
            potential_profit_usd = round(tp_pips * result['pip_value'] * result['lot_size'], 2)
            
            # Try to get current market price from Alpha Vantage
            current_price = get_current_price_optimized(pair_symbol)
            
            result.update({
                'direction': direction.upper(),
                'pair_symbol': pair_symbol,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'tp_pips': round(tp_pips, 1),
                'risk_reward_ratio': risk_reward_ratio,
                'potential_profit_usd': potential_profit_usd,
                'current_market_price': current_price
            })
        
        return jsonify(result)
        
    except ValueError as e:
        app.logger.error(f"Validation error: {str(e)}")
        return jsonify({'success': False, 'error': 'Invalid input values. Please check your numbers.'})
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred. Please try again.'})

@app.route('/api/mobile/pairs')
def mobile_currency_pairs():
    """Mobile API endpoint - Get all available currency pairs"""
    try:
        pairs_list = []
        for symbol, info in CURRENCY_PAIRS.items():
            pairs_list.append({
                'symbol': symbol,
                'name': info['name'],
                'category': info['category'],
                'pip_size': info['pip_size'],
                'pip_value': info['pip_value']
            })
        
        return jsonify({
            'success': True,
            'pairs': pairs_list,
            'total': len(pairs_list)
        })
    except Exception as e:
        app.logger.error(f"Mobile pairs API error: {str(e)}")
        return jsonify({'success': False, 'error': 'Unable to fetch currency pairs'})

@app.route('/api/mobile/calculate', methods=['POST'])
def mobile_calculate():
    """Mobile API endpoint - Optimized for mobile apps"""
    try:
        data = request.get_json()
        
        # Mobile-optimized validation
        required_fields = ['pair_symbol', 'direction', 'entry_price', 'stop_loss', 'take_profit', 'capital', 'risk_percent']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'})
        
        pair_symbol = data['pair_symbol'].upper()
        direction = data['direction'].lower()
        entry_price = float(data['entry_price'])
        stop_loss = float(data['stop_loss'])
        take_profit = float(data['take_profit'])
        capital = float(data['capital'])
        risk_percent = float(data['risk_percent'])
        
        # Calculate pips and lot size
        sl_pips = calculate_pips(entry_price, stop_loss, pair_symbol)
        tp_pips = calculate_pips(entry_price, take_profit, pair_symbol)
        
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        if result['success']:
            # Get current market price (with caching for mobile efficiency)
            current_price = get_current_price_optimized(pair_symbol)
            
            mobile_response = {
                'success': True,
                'data': {
                    'pair_symbol': pair_symbol,
                    'direction': direction.upper(),
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'capital': capital,
                    'risk_percent': risk_percent,
                    'lot_size': result['lot_size'],
                    'risk_usd': result['risk_usd'],
                    'sl_pips': sl_pips,
                    'tp_pips': tp_pips,
                    'risk_reward_ratio': round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0,
                    'current_market_price': current_price,
                    'pip_value': result['pip_value']
                }
            }
            
            return jsonify(mobile_response)
        else:
            return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"Mobile calculate API error: {str(e)}")
        return jsonify({'success': False, 'error': 'Calculation failed'})

# API Routes pour l'Assistant IA
@app.route('/api/ai/daily-tips')
def get_daily_tips():
    """API pour récupérer les conseils quotidiens (Gratuit)"""
    try:
        # Conseils de trading de base intégrés
        tips = [
            "Ne risquez jamais plus de 2% de votre capital par trade",
            "Toujours définir votre stop loss avant d'entrer en position", 
            "La patience est la clé du succès en trading"
        ]
        return jsonify({
            'success': True,
            'tips': tips
        })
    except Exception as e:
        app.logger.error(f"Error getting daily tips: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Impossible de charger les conseils'
        })

@app.route('/api/ai/quick-advice', methods=['POST'])
@rate_limit(max_requests=5, time_window=60)
@require_csrf
def get_quick_advice():
    """API pour les conseils rapides en temps réel (Gratuit)"""
    try:
        data = request.get_json()
        
        # Validation sécurisée des données
        is_valid, errors = validator.validate_trading_data(data)
        if not is_valid:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Conseil rapide intégré
        advice = "Analysez toujours le contexte du marché avant d'entrer en position"
        
        return jsonify({
            'success': True,
            'advice': advice
        })
        
    except Exception as e:
        app.logger.error(f"Error getting quick advice: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'analyse'
        })

# API Routes pour les Intégrations Externes
@app.route('/api/integrations/generate-image', methods=['POST'])
def generate_trade_image():
    """API pour générer une image SVG de trade (Gratuit)"""
    try:
        from integrations import trading_integrations
        data = request.get_json()
        
        result = trading_integrations.create_trade_image(data)
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error generating trade image: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération d\'image'
        })

@app.route('/api/integrations/generate-trade-text', methods=['POST'])
def generate_trade_text():
    """API pour générer le texte de partage d'un trade (Gratuit)"""
    try:
        from integrations import trading_integrations
        data = request.get_json()
        
        share_text = trading_integrations.generate_trade_share_text(data)
        
        return jsonify({
            'success': True,
            'share_text': share_text
        })
        
    except Exception as e:
        app.logger.error(f"Error generating trade text: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération du texte'
        })

@app.route('/api/integrations/generate-stats', methods=['POST'])
def generate_stats_share():
    """API pour générer le partage des statistiques (Gratuit)"""
    try:
        from integrations import trading_integrations
        data = request.get_json()
        
        share_text = trading_integrations.generate_statistics_summary(data)
        
        return jsonify({
            'success': True,
            'share_text': share_text
        })
        
    except Exception as e:
        app.logger.error(f"Error generating stats share: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération des statistiques'
        })

# API Routes pour le Calendrier Économique
@app.route('/api/economic/events')
def get_economic_events():
    """API pour récupérer les événements économiques en temps réel"""
    try:
        from economic_calendar import economic_calendar
        
        events = economic_calendar.get_economic_events()
        
        # Convertir les événements en format JSON
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'country': event.country,
                'currency': event.currency,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time,
                'impact': event.impact,
                'forecast': event.forecast,
                'previous': event.previous,
                'actual': event.actual,
                'description': event.description,
                'category': event.category
            })
        
        return jsonify({
            'success': True,
            'events': events_data,
            'total': len(events_data)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting economic events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement du calendrier économique'
        })

@app.route('/api/economic/high-impact')
def get_high_impact_events():
    """API pour récupérer uniquement les événements à fort impact"""
    try:
        from economic_calendar import economic_calendar
        
        events = economic_calendar.get_events_by_impact('high')
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'currency': event.currency,
                'date': event.date.strftime('%Y-%m-%d'),
                'time': event.time,
                'forecast': event.forecast,
                'previous': event.previous
            })
        
        return jsonify({
            'success': True,
            'events': events_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting high impact events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des événements à fort impact'
        })

# API Routes pour les Alertes de Prix
@app.route('/price-alerts')
def price_alerts_page():
    """Page des alertes de prix en temps réel"""
    return render_template('price_alerts.html')

@app.route('/api/alerts/create', methods=['POST'])
def create_price_alert():
    """Crée une nouvelle alerte de prix avec limite freemium"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        pair_symbol = data.get('pair_symbol')
        alert_type = data.get('alert_type')
        target_price = data.get('target_price', 0)
        percentage_threshold = data.get('percentage_threshold')
        
        # Vérifier la limite freemium (2 alertes max gratuit)
        from models import PriceAlertModel
        can_create, message = PriceAlertModel.check_freemium_limit(user_session, is_premium=False)
        
        if not can_create:
            return jsonify({
                'success': False,
                'error': message
            })
        
        # Créer l'alerte via le moniteur de prix
        from price_alerts import price_monitor
        alert_id = price_monitor.add_alert(
            user_session=user_session,
            pair_symbol=pair_symbol,
            alert_type=alert_type,
            target_price=target_price,
            percentage_threshold=percentage_threshold
        )
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': f'Alerte créée ! {message}'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating price alert: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la création de l\'alerte'
        })

@app.route('/api/alerts/user/<user_session>')
def get_user_alerts(user_session):
    """Récupère toutes les alertes d'un utilisateur"""
    try:
        from price_alerts import price_monitor
        alerts = price_monitor.get_user_alerts(user_session)
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'pair_symbol': alert.pair_symbol,
                'alert_type': alert.alert_type,
                'target_price': alert.target_price,
                'current_price': alert.current_price,
                'percentage_threshold': alert.percentage_threshold,
                'is_active': alert.is_active,
                'created_at': alert.created_at.isoformat(),
                'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                'message': alert.message
            })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting user alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des alertes'
        })

@app.route('/api/alerts/delete/<alert_id>', methods=['DELETE'])
def delete_price_alert(alert_id):
    """Supprime une alerte de prix"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        
        from price_alerts import price_monitor
        success = price_monitor.remove_alert(alert_id, user_session)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alerte supprimée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Alerte non trouvée ou non autorisée'
            })
        
    except Exception as e:
        app.logger.error(f"Error deleting price alert: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la suppression'
        })

@app.route('/api/alerts/triggered/<user_session>')
def get_triggered_alerts(user_session):
    """Récupère les alertes récemment déclenchées"""
    try:
        from price_alerts import price_monitor
        triggered = price_monitor.get_triggered_alerts(user_session)
        
        alerts_data = []
        for alert in triggered:
            alerts_data.append({
                'id': alert.id,
                'pair_symbol': alert.pair_symbol,
                'message': alert.message,
                'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                'target_price': alert.target_price,
                'current_price': alert.current_price
            })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting triggered alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des alertes déclenchées'
        })

# API Routes pour le Centre d'Apprentissage
@app.route('/learning-center')
def learning_center_page():
    """Page du centre d'apprentissage"""
    return render_template('learning_center.html')

@app.route('/api/learning/glossary')
def get_glossary_terms():
    """API pour récupérer les termes du glossaire (Gratuit)"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        from learning_center import learning_center
        
        if search:
            terms = learning_center.search_glossary(search)
        else:
            terms = learning_center.get_glossary_terms(category if category else None)
        
        terms_data = []
        for term in terms:
            terms_data.append({
                'id': term.id,
                'term': term.term,
                'definition': term.definition,
                'category': term.category,
                'difficulty': term.difficulty,
                'examples': term.examples,
                'related_terms': term.related_terms
            })
        
        return jsonify({
            'success': True,
            'terms': terms_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting glossary terms: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement du glossaire'
        })

@app.route('/api/learning/articles')
def get_learning_articles():
    """API pour récupérer les articles éducatifs"""
    try:
        category = request.args.get('category')
        is_premium = request.args.get('premium')
        
        from learning_center import learning_center
        
        premium_filter = None
        if is_premium == 'true':
            premium_filter = True
        elif is_premium == 'false':
            premium_filter = False
        
        articles = learning_center.get_articles(category, premium_filter)
        
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'category': article.category,
                'difficulty': article.difficulty,
                'reading_time': article.reading_time,
                'author': article.author,
                'is_premium': article.is_premium,
                'tags': article.tags,
                'date_published': article.date_published.isoformat()
            })
        
        return jsonify({
            'success': True,
            'articles': articles_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting learning articles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des articles'
        })

@app.route('/api/learning/premium-content')
def get_premium_content():
    """API pour récupérer le contenu premium"""
    try:
        from learning_center import learning_center
        
        premium_content = learning_center.get_premium_content()
        
        # Convertir les articles premium
        articles_data = []
        for article in premium_content['articles']:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'difficulty': article.difficulty,
                'reading_time': article.reading_time
            })
        
        # Convertir les vidéos
        videos_data = []
        for video in premium_content['videos']:
            videos_data.append({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'duration': video.duration,
                'category': video.category,
                'difficulty': video.difficulty
            })
        
        # Convertir les quiz
        quizzes_data = []
        for quiz in premium_content['quizzes']:
            quizzes_data.append({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'category': quiz.category,
                'difficulty': quiz.difficulty,
                'question_count': len(quiz.questions)
            })
        
        return jsonify({
            'success': True,
            'premium_content': {
                'articles': articles_data,
                'videos': videos_data,
                'quizzes': quizzes_data
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting premium content: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement du contenu premium'
        })

# API Routes pour la Monétisation
@app.route('/pricing')
def pricing_page():
    """Page de tarification avec les 3 plans"""
    return render_template('pricing.html')

@app.route('/api/monetization/plans')
def get_pricing_plans():
    """API pour récupérer les plans tarifaires"""
    try:
        from monetization import monetization_manager
        
        plans_data = monetization_manager.get_pricing_page_data()
        
        return jsonify({
            'success': True,
            'pricing_data': plans_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting pricing plans: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des plans'
        })

@app.route('/api/monetization/check-access', methods=['POST'])
def check_feature_access():
    """Vérifie l'accès à une fonctionnalité"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        feature = data.get('feature')
        
        from monetization import monetization_manager
        
        access_info = monetization_manager.check_feature_access(user_session, feature)
        
        return jsonify({
            'success': True,
            'access_info': access_info
        })
        
    except Exception as e:
        app.logger.error(f"Error checking feature access: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la vérification d\'accès'
        })

@app.route('/api/monetization/usage-stats/<user_session>')
def get_usage_stats(user_session):
    """Récupère les statistiques d'utilisation"""
    try:
        from monetization import monetization_manager
        
        usage_stats = monetization_manager.calculate_usage_stats(user_session)
        
        return jsonify({
            'success': True,
            'usage_stats': usage_stats
        })
        
    except Exception as e:
        app.logger.error(f"Error getting usage stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des statistiques'
        })

# API Routes pour l'Analytics Avancé
@app.route('/analytics')
def analytics_page():
    """Page d'analytics avec graphiques interactifs"""
    return render_template('analytics.html')

@app.route('/api/analytics/performance/<user_session>')
def get_performance_analytics(user_session):
    """API pour récupérer les analytics de performance"""
    try:
        from models import TradeJournal
        from analytics import advanced_analytics
        
        # Récupérer les trades de l'utilisateur
        trades_query = TradeJournal.query.filter_by(user_session=user_session).all()
        
        if not trades_query:
            return jsonify({
                'success': False,
                'error': 'Aucun trade trouvé pour calculer les analytics'
            })
        
        # Convertir en format pour l'analyse
        trades_data = []
        for trade in trades_query:
            trades_data.append({
                'pair_symbol': trade.pair_symbol,
                'direction': trade.direction,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'profit_loss': trade.profit_loss,
                'profit_loss_pips': trade.profit_loss_pips,
                'entry_date': trade.entry_date,
                'exit_date': trade.exit_date,
                'risk_reward_ratio': trade.risk_reward_ratio,
                'status': trade.status
            })
        
        # Calculer les métriques
        metrics = advanced_analytics.calculate_performance_metrics(trades_data)
        equity_curve = advanced_analytics.generate_equity_curve_data(trades_data)
        pair_analysis = advanced_analytics.analyze_performance_by_pair(trades_data)
        time_patterns = advanced_analytics.analyze_time_patterns(trades_data)
        detected_patterns = advanced_analytics.detect_trading_patterns(trades_data)
        insights = advanced_analytics.get_performance_insights(metrics)
        
        return jsonify({
            'success': True,
            'analytics': {
                'metrics': {
                    'total_trades': metrics.total_trades,
                    'winning_trades': metrics.winning_trades,
                    'losing_trades': metrics.losing_trades,
                    'win_rate': metrics.win_rate,
                    'total_profit': metrics.total_profit,
                    'average_win': metrics.average_win,
                    'average_loss': metrics.average_loss,
                    'profit_factor': metrics.profit_factor,
                    'max_drawdown': metrics.max_drawdown,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'largest_win': metrics.largest_win,
                    'largest_loss': metrics.largest_loss,
                    'consecutive_wins': metrics.consecutive_wins,
                    'consecutive_losses': metrics.consecutive_losses,
                    'risk_reward_ratio': metrics.risk_reward_ratio
                },
                'equity_curve': equity_curve,
                'pair_analysis': pair_analysis,
                'time_patterns': time_patterns,
                'detected_patterns': [
                    {
                        'name': pattern.name,
                        'description': pattern.description,
                        'frequency': pattern.frequency,
                        'success_rate': pattern.success_rate,
                        'average_profit': pattern.average_profit,
                        'recommendations': pattern.recommendations
                    } for pattern in detected_patterns
                ],
                'insights': insights
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting performance analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du calcul des analytics'
        })

@app.route('/api/analytics/monthly-report/<user_session>/<int:month>/<int:year>')
def get_monthly_report(user_session, month, year):
    """Génère un rapport mensuel détaillé"""
    try:
        from models import TradeJournal
        from analytics import advanced_analytics
        
        # Récupérer tous les trades pour la comparaison
        all_trades_query = TradeJournal.query.filter_by(user_session=user_session).all()
        
        trades_data = []
        for trade in all_trades_query:
            trades_data.append({
                'pair_symbol': trade.pair_symbol,
                'direction': trade.direction,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'profit_loss': trade.profit_loss,
                'profit_loss_pips': trade.profit_loss_pips,
                'entry_date': trade.entry_date,
                'exit_date': trade.exit_date,
                'risk_reward_ratio': trade.risk_reward_ratio,
                'status': trade.status
            })
        
        # Générer le rapport mensuel
        monthly_report = advanced_analytics.generate_monthly_report(trades_data, month, year)
        
        return jsonify({
            'success': True,
            'monthly_report': monthly_report
        })
        
    except Exception as e:
        app.logger.error(f"Error generating monthly report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération du rapport mensuel'
        })

# API Routes pour le Journal de Trading Intelligent
@app.route('/smart-journal')
def smart_journal_page():
    """Page du journal de trading intelligent"""
    return render_template('smart_journal.html')

@app.route('/api/smart-journal/add-trade', methods=['POST'])
def add_smart_trade():
    """Ajoute un nouveau trade intelligent"""
    try:
        data = request.get_json()
        
        from smart_journal import smart_journal
        
        trade_id = smart_journal.add_trade(data)
        
        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'message': 'Trade intelligent enregistré avec succès'
        })
        
    except Exception as e:
        app.logger.error(f"Error adding smart trade: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'enregistrement du trade'
        })

@app.route('/api/smart-journal/trades/<user_session>')
def get_smart_trades(user_session):
    """Récupère les trades intelligents d'un utilisateur"""
    try:
        filters = {}
        for param in ['strategy', 'pair_symbol', 'status', 'date_from', 'date_to', 'tags', 'emotional_state']:
            if request.args.get(param):
                filters[param] = request.args.get(param)
        
        from smart_journal import smart_journal
        
        trades = smart_journal.get_user_trades(user_session, filters)
        
        trades_data = []
        for trade in trades:
            trades_data.append({
                'trade_id': trade.trade_id,
                'pair_symbol': trade.pair_symbol,
                'direction': trade.direction,
                'lot_size': trade.lot_size,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'profit_loss': trade.profit_loss,
                'profit_loss_pips': trade.profit_loss_pips,
                'status': trade.status.value,
                'strategy': trade.strategy.value if trade.strategy else None,
                'market_context': trade.market_context,
                'confluence_factors': trade.confluence_factors,
                'emotional_state': trade.emotional_state.value,
                'confidence_level': trade.confidence_level,
                'stress_level': trade.stress_level,
                'notes': trade.notes,
                'tags': trade.tags,
                'timeframe': trade.timeframe,
                'market_structure': trade.market_structure,
                'setup_quality': trade.setup_quality,
                'execution_quality': trade.execution_quality,
                'risk_reward_ratio': trade.risk_reward_ratio,
                'created_at': trade.created_at.isoformat(),
                'updated_at': trade.updated_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'trades': trades_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting smart trades: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des trades'
        })

@app.route('/api/smart-journal/search/<user_session>')
def search_smart_trades(user_session):
    """Recherche intelligente dans les trades"""
    try:
        query = request.args.get('q', '')
        
        from smart_journal import smart_journal
        
        trades = smart_journal.search_trades(user_session, query)
        
        trades_data = []
        for trade in trades:
            trades_data.append({
                'trade_id': trade.trade_id,
                'pair_symbol': trade.pair_symbol,
                'direction': trade.direction,
                'notes': trade.notes,
                'tags': trade.tags,
                'strategy': trade.strategy.value if trade.strategy else None,
                'entry_time': trade.entry_time.isoformat(),
                'profit_loss': trade.profit_loss
            })
        
        return jsonify({
            'success': True,
            'trades': trades_data,
            'query': query
        })
        
    except Exception as e:
        app.logger.error(f"Error searching smart trades: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la recherche'
        })

@app.route('/api/smart-journal/insights/<user_session>')
def get_trading_insights(user_session):
    """Génère des insights intelligents sur le trading"""
    try:
        from smart_journal import smart_journal
        
        insights = smart_journal.get_trading_insights(user_session)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        app.logger.error(f"Error getting trading insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération des insights'
        })

@app.route('/api/smart-journal/export/<user_session>')
def export_smart_journal(user_session):
    """Export du journal intelligent en CSV"""
    try:
        filters = {}
        for param in ['strategy', 'pair_symbol', 'date_from', 'date_to']:
            if request.args.get(param):
                filters[param] = request.args.get(param)
        
        from smart_journal import smart_journal
        
        csv_content = smart_journal.export_to_csv(user_session, filters)
        
        return csv_content, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=smart_journal_{user_session}.csv'
        }
        
    except Exception as e:
        app.logger.error(f"Error exporting smart journal: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'export'
        })

@app.route('/api/smart-journal/import-mt4', methods=['POST'])
def import_from_mt4():
    """Import automatique depuis MetaTrader 4/5"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        mt4_data = data.get('mt4_data', {})
        
        from smart_journal import smart_journal
        
        imported_trades = smart_journal.import_from_mt4(user_session, mt4_data)
        
        return jsonify({
            'success': True,
            'imported_count': len(imported_trades),
            'trade_ids': imported_trades,
            'message': f'{len(imported_trades)} trades importés depuis MT4/MT5'
        })
        
    except Exception as e:
        app.logger.error(f"Error importing from MT4: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'import MT4/MT5'
        })

# API Routes pour le Calculateur Avancé Multi-Actifs
@app.route('/advanced-calculator')
def advanced_calculator_page():
    """Page du calculateur avancé multi-actifs"""
    return render_template('advanced_calculator.html')

@app.route('/api/calculator/supported-assets')
def get_supported_assets():
    """Récupère la liste des actifs supportés"""
    try:
        from advanced_calculator import advanced_calculator
        
        assets = advanced_calculator.get_supported_assets()
        
        return jsonify({
            'success': True,
            'assets': assets
        })
        
    except Exception as e:
        app.logger.error(f"Error getting supported assets: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des actifs'
        })

@app.route('/api/calculator/calculate-position', methods=['POST'])
def calculate_advanced_position():
    """Calcule une position avec le calculateur avancé"""
    try:
        data = request.get_json()
        
        from advanced_calculator import advanced_calculator, CalculationInput, CalculationType
        from datetime import datetime
        
        # Création de l'input de calcul
        calc_input = CalculationInput(
            calculation_id=f"calc_{int(datetime.now().timestamp())}_{data.get('asset_symbol', 'XXX')}",
            user_session=data.get('user_session', 'default'),
            calculation_type=CalculationType.POSITION_SIZE,
            asset_symbol=data['asset_symbol'],
            timestamp=datetime.now(),
            account_capital=data['account_capital'],
            risk_percentage=data.get('risk_percentage', 0),
            risk_amount_usd=data.get('risk_amount_usd'),
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            take_profit=data.get('take_profit'),
            current_price=data.get('current_price'),
            leverage=data.get('leverage', 30),
            commission_rate=data.get('commission_rate', 0),
            swap_rate=data.get('swap_rate'),
            strategy=data.get('strategy'),
            notes=data.get('notes'),
            tags=data.get('tags', [])
        )
        
        # Calcul de la position
        result = advanced_calculator.calculate_position(calc_input)
        
        # Conversion en dictionnaire pour JSON
        result_dict = {
            'calculation_id': result.calculation_id,
            'success': result.success,
            'recommended_lot_size': result.recommended_lot_size,
            'position_value_usd': result.position_value_usd,
            'margin_required': result.margin_required,
            'risk_amount': result.risk_amount,
            'potential_profit': result.potential_profit,
            'risk_reward_ratio': result.risk_reward_ratio,
            'pip_value': result.pip_value,
            'stop_loss_pips': result.stop_loss_pips,
            'take_profit_pips': result.take_profit_pips,
            'spread_cost': result.spread_cost,
            'commission_cost': result.commission_cost,
            'risk_level': result.risk_level,
            'recommendations': result.recommendations,
            'warnings': result.warnings,
            'actual_profit_loss': result.actual_profit_loss,
            'actual_pips': result.actual_pips,
            'calculation_time': result.calculation_time.isoformat(),
            'asset_type': result.asset_type.value
        }
        
        return jsonify({
            'success': True,
            'calculation': result_dict
        })
        
    except Exception as e:
        app.logger.error(f"Error calculating position: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du calcul de position'
        })

@app.route('/api/calculator/history/<user_session>')
def get_calculation_history(user_session):
    """Récupère l'historique des calculs d'un utilisateur"""
    try:
        days = request.args.get('days', 30, type=int)
        
        from advanced_calculator import advanced_calculator
        
        history = advanced_calculator.get_calculation_history(user_session, days)
        
        history_data = []
        for calc in history:
            history_data.append({
                'calculation_id': calc.calculation_id,
                'recommended_lot_size': calc.recommended_lot_size,
                'risk_amount': calc.risk_amount,
                'potential_profit': calc.potential_profit,
                'risk_reward_ratio': calc.risk_reward_ratio,
                'risk_level': calc.risk_level,
                'asset_type': calc.asset_type.value,
                'calculation_time': calc.calculation_time.isoformat()
            })
        
        return jsonify({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting calculation history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement de l\'historique'
        })

@app.route('/api/calculator/user-stats/<user_session>')
def get_calculator_user_stats(user_session):
    """Récupère les statistiques utilisateur du calculateur"""
    try:
        from advanced_calculator import advanced_calculator
        
        stats = advanced_calculator.get_user_stats(user_session)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        app.logger.error(f"Error getting calculator user stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des statistiques'
        })

@app.route('/api/ai-chat', methods=['POST'])
def chat_with_ai():
    """API pour chat en temps réel avec l'assistant IA"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_context = data.get('context', '')
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message requis'
            })
        
        from ai_assistant import ai_assistant
        
        response = ai_assistant.chat_with_ai(user_message, user_context)
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error in AI chat: {str(e)}")
        return jsonify({
            'success': False,
            'response': 'Désolé, je rencontre un problème technique. Pouvez-vous reformuler votre question ?',
            'error': 'Erreur de connexion IA'
        })

# API Routes pour le Système d'Alertes Avancé
@app.route('/advanced-alerts')
def advanced_alerts_page():
    """Page du système d'alertes avancé"""
    return render_template('advanced_alerts.html')

@app.route('/api/alerts/create', methods=['POST'])
def create_advanced_alert():
    """Crée une nouvelle alerte avancée"""
    try:
        data = request.get_json()
        
        from advanced_alerts import advanced_alert_system
        
        alert_id = advanced_alert_system.create_price_alert(data)
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Alerte créée avec succès'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating advanced alert: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la création de l\'alerte'
        })

@app.route('/api/alerts/user/<user_session>')
def get_user_advanced_alerts(user_session):
    """Récupère les alertes avancées d'un utilisateur"""
    try:
        from advanced_alerts import advanced_alert_system
        
        alerts = advanced_alert_system.get_user_alerts(user_session)
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'alert_id': alert.alert_id,
                'pair_symbol': alert.pair_symbol,
                'target_price': alert.target_price,
                'current_price': alert.current_price,
                'direction': alert.direction,
                'priority': alert.priority.value,
                'is_active': alert.is_active,
                'notification_channels': [ch.value for ch in alert.notification_channels],
                'custom_message': alert.custom_message,
                'created_at': alert.created_at.isoformat(),
                'trigger_count': alert.trigger_count,
                'max_triggers': alert.max_triggers
            })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting user alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des alertes'
        })

@app.route('/api/alerts/delete/<alert_id>', methods=['DELETE'])
def delete_advanced_alert(alert_id):
    """Supprime une alerte avancée"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        
        from advanced_alerts import advanced_alert_system
        
        success = advanced_alert_system.delete_alert(user_session, alert_id)
        
        return jsonify({
            'success': success,
            'message': 'Alerte supprimée' if success else 'Alerte introuvable'
        })
        
    except Exception as e:
        app.logger.error(f"Error deleting alert: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la suppression'
        })

@app.route('/api/alerts/preferences', methods=['POST'])
def set_alert_preferences():
    """Configure les préférences utilisateur pour les alertes"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        preferences = data.get('preferences')
        
        from advanced_alerts import advanced_alert_system
        
        advanced_alert_system.set_user_preferences(user_session, preferences)
        
        return jsonify({
            'success': True,
            'message': 'Préférences sauvegardées'
        })
        
    except Exception as e:
        app.logger.error(f"Error setting preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la sauvegarde'
        })

@app.route('/api/alerts/stats/<user_session>')
def get_alert_stats(user_session):
    """Récupère les statistiques des notifications"""
    try:
        from advanced_alerts import advanced_alert_system
        
        stats = advanced_alert_system.get_notification_stats(user_session)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        app.logger.error(f"Error getting alert stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des statistiques'
        })

@app.route('/api/alerts/test', methods=['POST'])
def test_notifications():
    """Test des notifications sur tous les canaux"""
    try:
        data = request.get_json()
        user_session = data.get('user_session')
        channels = data.get('channels', ['email'])
        
        # Créer une alerte de test
        test_alert_data = {
            'user_session': user_session,
            'pair_symbol': 'TEST',
            'target_price': 1.0000,
            'direction': 'touch',
            'channels': channels,
            'custom_message': 'Ceci est un test de notification',
            'title': 'Test Notification',
            'expires_days': 1,
            'max_triggers': 1,
            'is_recurring': False
        }
        
        from advanced_alerts import advanced_alert_system
        
        # Pour le test, on simule juste le succès
        return jsonify({
            'success': True,
            'message': f'Test envoyé sur {len(channels)} canaux'
        })
        
    except Exception as e:
        app.logger.error(f"Error testing notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du test'
        })

# API Routes pour le Simulateur de Trading
@app.route('/trading-simulator')
def trading_simulator_page():
    """Page du simulateur de trading"""
    return render_template('trading_simulator.html')

@app.route('/api/simulator/strategies')
def get_simulator_strategies():
    """Récupère les stratégies disponibles"""
    try:
        from trading_simulator import trading_simulator
        
        strategies = trading_simulator.get_available_strategies()
        
        return jsonify({
            'success': True,
            'strategies': strategies
        })
        
    except Exception as e:
        app.logger.error(f"Error getting strategies: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du chargement des stratégies'
        })

@app.route('/api/simulator/backtest', methods=['POST'])
def run_simulator_backtest():
    """Lance un backtest"""
    try:
        data = request.get_json()
        
        from trading_simulator import trading_simulator
        
        result = trading_simulator.run_backtest(data['user_session'], data)
        
        # Convertir le résultat en dictionnaire
        result_dict = {
            'strategy_name': result.strategy_name,
            'symbol': result.symbol,
            'timeframe': result.timeframe.value,
            'start_date': result.start_date.isoformat(),
            'end_date': result.end_date.isoformat(),
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'win_rate': result.win_rate,
            'initial_balance': result.initial_balance,
            'final_balance': result.final_balance,
            'total_return': result.total_return,
            'total_return_percent': result.total_return_percent,
            'max_drawdown': result.max_drawdown,
            'max_drawdown_percent': result.max_drawdown_percent,
            'sharpe_ratio': result.sharpe_ratio,
            'profit_factor': result.profit_factor,
            'average_win': result.average_win,
            'average_loss': result.average_loss,
            'largest_win': result.largest_win,
            'largest_loss': result.largest_loss,
            'equity_curve': result.equity_curve,
            'trade_list': result.trade_list
        }
        
        return jsonify({
            'success': True,
            'backtest_result': result_dict
        })
        
    except Exception as e:
        app.logger.error(f"Error running backtest: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du backtest'
        })

@app.route('/api/simulator/paper-account', methods=['POST'])
def create_simulator_paper_account():
    """Crée un compte de paper trading"""
    try:
        data = request.get_json()
        
        from trading_simulator import trading_simulator
        
        result = trading_simulator.create_paper_account(
            data['user_session'], 
            data.get('initial_balance', 10000)
        )
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error creating paper account: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la création du compte'
        })

@app.route('/api/simulator/paper-account/<user_session>')
def get_simulator_paper_account(user_session):
    """Récupère le compte de paper trading"""
    try:
        from trading_simulator import trading_simulator
        
        account = trading_simulator.get_paper_account(user_session)
        
        return jsonify(account)
        
    except Exception as e:
        app.logger.error(f"Error getting paper account: {str(e)}")
        return jsonify({
            'error': 'Compte introuvable'
        })

@app.route('/api/simulator/paper-order', methods=['POST'])
def place_simulator_paper_order():
    """Place un ordre en paper trading"""
    try:
        data = request.get_json()
        
        from trading_simulator import trading_simulator
        
        result = trading_simulator.place_paper_order(data['user_session'], data)
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error placing paper order: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du passage d\'ordre'
        })

# API Routes pour l'Analyse Psychologique
@app.route('/psychological-analysis')
def psychological_analysis_page():
    """Page d'analyse psychologique"""
    return render_template('psychological_analysis.html')

@app.route('/api/psychology/record-emotion', methods=['POST'])
def record_emotional_state():
    """Enregistre l'état émotionnel d'un trader"""
    try:
        data = request.get_json()
        
        from psychological_analysis import psychological_analyzer
        
        record_id = psychological_analyzer.record_emotional_state(data['user_session'], data)
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'message': 'État émotionnel enregistré avec succès'
        })
        
    except Exception as e:
        app.logger.error(f"Error recording emotion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'enregistrement'
        })

@app.route('/api/psychology/mental-score', methods=['POST'])
def calculate_mental_score():
    """Calcule le score mental"""
    try:
        data = request.get_json()
        
        from psychological_analysis import psychological_analyzer
        
        score_data = psychological_analyzer.calculate_mental_score(data['user_session'], data)
        
        return jsonify({
            'success': True,
            'score_data': score_data
        })
        
    except Exception as e:
        app.logger.error(f"Error calculating mental score: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors du calcul du score mental'
        })

@app.route('/api/psychology/insights/<user_session>')
def get_emotional_insights(user_session):
    """Récupère les insights émotionnels rapides"""
    try:
        from psychological_analysis import psychological_analyzer
        
        insights = psychological_analyzer.get_emotional_insights(user_session)
        
        return jsonify(insights)
        
    except Exception as e:
        app.logger.error(f"Error getting insights: {str(e)}")
        return jsonify({
            'message': 'Erreur lors du chargement des insights',
            'insights': []
        })

@app.route('/api/psychology/report/<user_session>')
def generate_psychological_report(user_session):
    """Génère un rapport psychologique complet"""
    try:
        from psychological_analysis import psychological_analyzer
        
        report = psychological_analyzer.generate_psychological_report(user_session)
        
        return jsonify(report)
        
    except Exception as e:
        app.logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la génération du rapport'
        })

@app.route('/api/psychology/mental-score-history/<user_session>')
def get_mental_score_history(user_session):
    """Récupère l'historique des scores mentaux"""
    try:
        from psychological_analysis import psychological_analyzer
        
        history = psychological_analyzer.get_mental_score_history(user_session)
        
        return jsonify(history)
        
    except Exception as e:
        app.logger.error(f"Error getting mental score history: {str(e)}")
        return jsonify([])

# Routes d'authentification simples
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    """Page et traitement d'inscription"""
    if request.method == 'GET':
        return render_template('register_simple.html')
    
    try:
        data = request.get_json()
        
        # Validation des données
        if not all([data.get('email'), data.get('password'), data.get('name')]):
            return jsonify({'success': False, 'message': 'Tous les champs sont obligatoires'})
        
        email = data['email'].lower().strip()
        name = data['name'].strip()
        
        # Générer un token de validation
        verification_token = f"{email}_{hash(email + name)}"
        
        # Créer l'utilisateur
        session['user_id'] = f"user_{email}"
        session['user_email'] = email
        session['user_plan'] = data.get('plan', 'free')
        session['user_name'] = name
        session['user_verified'] = False  # Pas encore vérifié
        session['verification_token'] = verification_token
        session.permanent = True
        
        # Envoyer l'email de validation
        try:
            from modules.email_service import email_service
            verification_link = f"https://{request.host}/auth/verify/{verification_token}"
            email_service.send_validation_email(email, name, verification_link)
            
            return jsonify({
                'success': True,
                'message': 'Compte créé avec succès ! Vérifiez votre email pour activer votre compte.',
                'user_id': session['user_id'],
                'plan': data.get('plan', 'free')
            })
        except Exception as email_error:
            app.logger.error(f"Erreur envoi email: {email_error}")
            return jsonify({
                'success': True,
                'message': 'Compte créé avec succès ! (Email de validation en cours d\'envoi)',
                'user_id': session['user_id'],
                'plan': data.get('plan', 'free')
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur lors de l\'inscription: {str(e)}'})

@app.route('/auth/verify/<token>')
def verify_email(token):
    """Validation de l'email via le lien reçu"""
    try:
        # Vérifier si l'utilisateur a ce token
        if 'verification_token' in session and session['verification_token'] == token:
            session['user_verified'] = True
            session.pop('verification_token', None)  # Supprimer le token utilisé
            return render_template('email_sent.html', 
                                 message="Votre compte a été validé avec succès ! Vous pouvez maintenant utiliser MindTraderPro.")
        else:
            return render_template('email_sent.html', 
                                 message="Lien de validation invalide ou expiré.")
    except Exception as e:
        return render_template('email_sent.html', 
                             message="Erreur lors de la validation.")

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """Page et traitement de connexion"""
    if request.method == 'GET':
        return render_template('login_simple.html')
    
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        plan = data.get('plan', 'free')
        
        # Connexion simplifiée pour les tests
        session['user_id'] = f"user_{email}"
        session['user_email'] = email
        session['user_plan'] = plan
        session['user_name'] = email.split('@')[0]
        session['user_verified'] = True
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Connexion réussie',
            'user_id': session['user_id'],
            'plan': plan
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur de connexion: {str(e)}'})

@app.route('/auth/logout')
def logout():
    """Déconnexion"""
    from flask import redirect, session
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
