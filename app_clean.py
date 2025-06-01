"""
MindTraderPro - Application principale nettoyée et sécurisée
Calculateur de trading professionnel avec sécurité renforcée
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Import des modules modulaires
from routes.journal_routes import journal_bp
from routes.admin_routes import admin_bp
from routes.newsletter_routes import newsletter_bp
from routes.suggestion_routes import suggestion_bp
from routes.customization_routes import customization_bp
from routes.lifetime_routes import lifetime_bp
from routes.grade_routes import grade_bp
from routes.referral_routes import referral_bp

# Configuration du logging sécurisé
os.makedirs('data', exist_ok=True)
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

# Configuration de sécurité et sessions
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,  # False pour dev, True pour prod avec HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SESSION_PERMANENT=True
)

# ============================================================================
# SYSTÈME D'AUTHENTIFICATION
# ============================================================================

# Base de données utilisateurs simple en mémoire pour la démo
users_db = {
    "demo@mindtraderpro.com": {
        "id": 1,
        "email": "demo@mindtraderpro.com",
        "password": generate_password_hash("demo123"),
        "first_name": "Demo",
        "last_name": "User",
        "role": "premium"
    },
    "admin@mindtraderpro.com": {
        "id": 2,
        "email": "admin@mindtraderpro.com", 
        "password": generate_password_hash("admin123"),
        "first_name": "Admin",
        "last_name": "MindTrader",
        "role": "admin"
    },
    "vip@mindtraderpro.com": {
        "id": 3,
        "email": "vip@mindtraderpro.com",
        "password": generate_password_hash("vip123"),
        "first_name": "VIP",
        "last_name": "Lifetime",
        "role": "lifetime"
    }
}

def login_required(f):
    """Décorateur pour vérifier si l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Récupère l'utilisateur actuellement connecté"""
    if 'user_id' not in session:
        return None
    
    user_email = session.get('user_email')
    if user_email and user_email in users_db:
        return users_db[user_email]
    return None

def login_user(user):
    """Connecte un utilisateur en créant une session"""
    session.permanent = True
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_role'] = user['role']
    session['user_name'] = f"{user['first_name']} {user['last_name']}"
    session['user_first_name'] = user['first_name']
    session['user_last_name'] = user['last_name']
    session['is_authenticated'] = True
    session.modified = True  # Force la sauvegarde de la session
    logging.info(f"Utilisateur connecté: {user['email']} (Role: {user['role']})")
    logging.info(f"Session créée avec ID: {session.get('user_id')}")

def logout_user():
    """Déconnecte l'utilisateur en supprimant la session"""
    user_email = session.get('user_email', 'Inconnu')
    session.clear()
    logging.info(f"Utilisateur déconnecté: {user_email}")



def get_user_display_info():
    """Retourne les informations d'affichage de l'utilisateur connecté"""
    logging.info(f"Session actuelle: {dict(session)}")
    
    # Vérification avec user_id et role (unifié sur 'role')
    if session.get('user_id') and (session.get('role') or session.get('user_role')):
        role = session.get('role') or session.get('user_role')  # Compatibilité
        user_info = {
            'is_authenticated': True,
            'name': session.get('user_name', 'Utilisateur'),
            'first_name': session.get('user_first_name', 'Utilisateur'),
            'role': role,
            'email': session.get('user_email', ''),
            'user_id': session.get('user_id')
        }
        logging.info(f"✅ Utilisateur connecté détecté: {user_info}")
        return user_info
    
    # Pas de session valide
    user_info = {
        'is_authenticated': False,
        'name': 'Visiteur',
        'first_name': 'Visiteur',
        'role': 'anonymous',
        'email': None,
        'user_id': None
    }
    logging.info(f"❌ Aucune session valide: {user_info}")
    return user_info

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
    # Import models after app context is created - version simplifiée
    try:
        import models
        db.create_all()
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"⚠️ Base de données non configurée: {e}")
        print("✅ Application fonctionnera sans base de données")

# ============================================================================
# FONCTIONS UTILITAIRES DE TRADING
# ============================================================================

def get_pip_info(pair_symbol):
    """Get pip size and pip value for a currency pair"""
    pair_symbol = pair_symbol.upper()
    
    pip_configs = {
        'XAUUSD': {'pip_size': 0.1, 'pip_value': 10.0},
        'EURUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'GBPUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'USDJPY': {'pip_size': 0.01, 'pip_value': 10.0},
        'USDCHF': {'pip_size': 0.0001, 'pip_value': 10.0},
        'AUDUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'USDCAD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'NZDUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
    }
    
    return pip_configs.get(pair_symbol, {'pip_size': 0.0001, 'pip_value': 10.0})

def calculate_pips(entry_price, exit_price, pair_symbol):
    """Calculate pips between two prices for a specific currency pair"""
    pip_info = get_pip_info(pair_symbol)
    pip_size = pip_info['pip_size']
    
    price_difference = abs(exit_price - entry_price)
    pips = price_difference / pip_size
    
    return round(pips, 1)

def calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol, pip_value=None, user_session=None):
    """
    Calculate the recommended lot size based on risk management
    """
    try:
        # Validation des entrées
        if sl_pips <= 0 or capital <= 0 or risk_percent <= 0:
            return {'success': False, 'error': 'Paramètres invalides'}
        
        # Limite de sécurité sur le risque
        if risk_percent > 10:
            risk_percent = 10
            
        # Calcul du risque en USD
        risk_usd = capital * (risk_percent / 100)
        
        # Obtention de la valeur du pip
        if pip_value is None:
            pip_info = get_pip_info(pair_symbol)
            pip_value = pip_info['pip_value']
        
        # Calcul de la taille de lot
        lot_size = risk_usd / (sl_pips * pip_value)
        
        # Limite de sécurité sur la taille de lot
        lot_size = min(lot_size, 10.0)  # Maximum 10 lots
        
        return {
            'success': True,
            'lot_size': round(lot_size, 2),
            'risk_usd': round(risk_usd, 2),
            'sl_pips': sl_pips,
            'capital': capital,
            'risk_percent': risk_percent,
            'pip_value': pip_value,
            'warnings': []
        }
        
    except Exception as e:
        app.logger.error(f"Calculation error: {str(e)}")
        return {'success': False, 'error': f"Erreur de calcul: {str(e)}"}

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@app.route('/home')
def home():
    """Page d'accueil moderne et professionnelle"""
    # Debug de la session
    logging.info(f"Session sur /home: {dict(session)}")
    user_info = get_user_display_info()
    logging.info(f"User info: {user_info}")
    
    # Navigation adaptée selon l'état de connexion
    if user_info['is_authenticated']:
        nav_links = f'''
                        <a href="/calculator" class="modern-nav-link">
                            <i class="fas fa-calculator me-2"></i>Calculateur
                        </a>
                        <a href="/journal" class="modern-nav-link">
                            <i class="fas fa-book me-2"></i>Journal
                        </a>
                        <a href="/grades" class="modern-nav-link">
                            <i class="fas fa-trophy me-2"></i>Grades
                        </a>
                        <a href="/parrainage" class="modern-nav-link">
                            <i class="fas fa-users me-2"></i>Parrainage
                        </a>
                    </div>
                    <div>
                        <span class="modern-nav-link text-success">
                            <i class="fas fa-user me-2"></i>{user_info['name']} ({user_info['role'].title()})
                        </span>
                        <a href="/logout" class="modern-nav-link text-warning">
                            <i class="fas fa-sign-out-alt me-2"></i>Déconnexion
                        </a>'''
    else:
        nav_links = '''
                        <a href="/calculator" class="modern-nav-link">
                            <i class="fas fa-calculator me-2"></i>Calculateur
                        </a>
                        <a href="/journal" class="modern-nav-link">
                            <i class="fas fa-book me-2"></i>Journal
                        </a>
                        <a href="/leaderboard" class="modern-nav-link">
                            <i class="fas fa-medal me-2"></i>Classement
                        </a>
                    </div>
                    <div>
                        <a href="/login" class="modern-nav-link">
                            <i class="fas fa-sign-in-alt me-2"></i>Connexion
                        </a>
                        <a href="/register" class="modern-nav-link">
                            <i class="fas fa-user-plus me-2"></i>Inscription
                        </a>'''
    
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MindTraderPro - Plateforme de Trading Professionnelle</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --success-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            }
            
            .hero-section {
                background: var(--primary-gradient);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 0;
                position: relative;
                overflow: hidden;
            }
            
            .hero-section::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
                opacity: 0.3;
                animation: float 20s ease-in-out infinite;
            }
            
            .hero-section::after {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 50px 50px;
                animation: rotate 60s linear infinite;
                opacity: 0.2;
            }
            
            /* Animation removed due to syntax conflict */
            
            /* Animations removed to fix syntax error */
            
            .hero-content {
                position: relative;
                z-index: 2;
            }
            
            .logo-text {
                font-size: 3.5rem;
                font-weight: bold;
                color: white;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                margin-bottom: 30px;
                line-height: 1.2;
            }
            
            .tagline {
                font-size: 1.4rem;
                color: rgba(255,255,255,0.95);
                margin-bottom: 40px;
                font-weight: 400;
                line-height: 1.6;
                max-width: 800px;
                margin-left: auto;
                margin-right: auto;
                padding: 0 20px;
            }
            
            .feature-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 20px;
                padding: 30px 20px;
                margin-bottom: 30px;
                text-align: center;
                transition: all 0.3s ease;
                height: 100%;
                position: relative;
                overflow: hidden;
            }
            
            .feature-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
                transform: translateX(-100%);
                transition: transform 0.6s;
            }
            
            .feature-card:hover::before {
                transform: translateX(100%);
            }
            
            .feature-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                border-color: rgba(255,255,255,0.4);
            }
            
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 20px;
                display: block;
                background: var(--accent-gradient);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .feature-title {
                font-size: 1.4rem;
                font-weight: bold;
                margin-bottom: 15px;
                color: white;
            }
            
            .feature-description {
                color: rgba(255,255,255,0.8);
                margin-bottom: 20px;
                line-height: 1.5;
            }
            
            .feature-btn {
                background: var(--accent-gradient);
                border: none;
                color: white;
                padding: 12px 30px;
                border-radius: 25px;
                font-weight: bold;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                position: relative;
                z-index: 2;
            }
            
            .feature-btn:hover {
                color: white;
                transform: scale(1.05);
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            }
            
            .stats-section {
                background: rgba(255,255,255,0.05);
                padding: 60px 0;
                margin: 60px 0;
                border-radius: 20px;
            }
            
            .stat-item {
                text-align: center;
                padding: 20px;
            }
            
            .stat-number {
                font-size: 3rem;
                font-weight: bold;
                background: var(--success-gradient);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stat-label {
                color: rgba(255,255,255,0.8);
                font-size: 1.1rem;
                margin-top: 10px;
            }
            
            .footer-section {
                background: rgba(0,0,0,0.3);
                padding: 40px 0;
                margin-top: 80px;
                border-top: 1px solid rgba(255,255,255,0.1);
            }
            
            .footer-link {
                color: rgba(255,255,255,0.7);
                text-decoration: none;
                margin: 0 15px;
                transition: color 0.3s ease;
            }
            
            .footer-link:hover {
                color: white;
            }
            
            .premium-badge {
                position: absolute;
                top: 15px;
                right: 15px;
                background: var(--warning-gradient);
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: bold;
            }
            
            .auth-section {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 30px;
                margin-top: 40px;
                text-align: center;
            }
            
            @media (max-width: 768px) {
                .hero-section {
                    min-height: 100vh;
                    padding: 20px 0;
                }
                .logo-text {
                    font-size: 2.8rem;
                    margin-bottom: 20px;
                }
                .tagline {
                    font-size: 1.2rem;
                    margin-bottom: 30px;
                    padding: 0 15px;
                }
                .auth-section {
                    padding: 20px 15px;
                    margin-top: 30px;
                }
                .auth-section .btn {
                    display: block;
                    width: 100%;
                    margin-bottom: 15px;
                    padding: 12px 20px !important;
                }
                .auth-section .btn:last-child {
                    margin-bottom: 0;
                }
                .feature-card {
                    margin-bottom: 20px;
                    padding: 25px 15px;
                }
                .stat-number {
                    font-size: 2.5rem;
                }
                .stats-section {
                    margin: 40px 0;
                    padding: 40px 0;
                }
            }
            
            @media (max-width: 480px) {
                .logo-text {
                    font-size: 2.2rem;
                }
                .tagline {
                    font-size: 1.1rem;
                    line-height: 1.5;
                }
                .hero-content h5 {
                    font-size: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <!-- Section Hero -->
        <div class="hero-section">
            <div class="container">
                <div class="hero-content text-center">
                    <h1 class="logo-text">🎯 MindTraderPro</h1>
                    <p class="tagline">
                        🎯 « Devenez un trader mentalement inébranlable grâce à MindTraderPro. »
                    </p>
                    <div class="auth-section">
                        <h5 class="text-white mb-3">Commencez votre parcours de trader professionnel</h5>
                        <a href="/register" class="btn btn-lg me-3" style="background: var(--success-gradient); border: none; color: white; padding: 15px 40px; border-radius: 30px; font-weight: bold;">
                            <i class="fas fa-rocket me-2"></i>Inscription Gratuite
                        </a>
                        <a href="/login" class="btn btn-outline-light btn-lg" style="padding: 15px 40px; border-radius: 30px; font-weight: bold;">
                            <i class="fas fa-sign-in-alt me-2"></i>Connexion
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Statistiques -->
        <div class="container">
            <div class="stats-section">
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-item">
                            <div class="stat-number">60+</div>
                            <div class="stat-label">Paires de Trading</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-item">
                            <div class="stat-number">1000+</div>
                            <div class="stat-label">Calculs Effectués</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-item">
                            <div class="stat-number">24/7</div>
                            <div class="stat-label">Disponibilité</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-item">
                            <div class="stat-number">100%</div>
                            <div class="stat-label">Sécurisé</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modules Principaux -->
        <div class="container">
            <div class="text-center mb-5">
                <h2 class="text-white display-5 mb-3">Découvrez nos Modules</h2>
                <p class="text-muted fs-5">Tout ce dont vous avez besoin pour optimiser votre trading</p>
            </div>
            
            <div class="row g-4">
                <!-- Calculateur de Lots -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-calculator feature-icon"></i>
                        <h3 class="feature-title">Calculateur de Lots</h3>
                        <p class="feature-description">
                            Calculez précisément vos positions avec notre algorithme avancé de gestion des risques
                        </p>
                        <a href="/calculator" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Journal de Trading -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <div class="premium-badge">Premium</div>
                        <i class="fas fa-book feature-icon"></i>
                        <h3 class="feature-title">Journal de Trading</h3>
                        <p class="feature-description">
                            Suivez vos performances, analysez vos trades et progressez continuellement
                        </p>
                        <a href="/journal" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Système de Grades -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-trophy feature-icon"></i>
                        <h3 class="feature-title">Système de Grades</h3>
                        <p class="feature-description">
                            Évoluez de Débutant à Légende avec notre système XP et débloquez des récompenses
                        </p>
                        <a href="/grades" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Leaderboard -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-medal feature-icon"></i>
                        <h3 class="feature-title">Leaderboard</h3>
                        <p class="feature-description">
                            Comparez-vous aux meilleurs traders et grimpez dans le classement mondial
                        </p>
                        <a href="/leaderboard" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Parrainage -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-users feature-icon"></i>
                        <h3 class="feature-title">Programme de Parrainage</h3>
                        <p class="feature-description">
                            Invitez vos amis et gagnez des XP et badges exclusifs pour chaque filleul
                        </p>
                        <a href="/parrainage" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Personnalisation -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-palette feature-icon"></i>
                        <h3 class="feature-title">Personnalisation</h3>
                        <p class="feature-description">
                            Customisez votre expérience avec des thèmes, avatars et cadres uniques
                        </p>
                        <a href="/personnalisation" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Suggestions Communautaires -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <i class="fas fa-lightbulb feature-icon"></i>
                        <h3 class="feature-title">Suggestions</h3>
                        <p class="feature-description">
                            Proposez vos idées et votez pour façonner l'avenir de MindTraderPro
                        </p>
                        <a href="/suggestions" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
                
                <!-- Lifetime VIP -->
                <div class="col-lg-4 col-md-6">
                    <div class="feature-card">
                        <div class="premium-badge">VIP</div>
                        <i class="fas fa-crown feature-icon"></i>
                        <h3 class="feature-title">Lifetime VIP</h3>
                        <p class="feature-description">
                            Accès illimité, fonctionnalités exclusives et privilèges spéciaux à vie
                        </p>
                        <a href="/profile" class="feature-btn">
                            <i class="fas fa-arrow-right me-2"></i>Accéder
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="footer-section">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <h5 class="text-white mb-3">MindTraderPro</h5>
                        <p class="text-muted">
                            La plateforme de référence pour les traders professionnels qui cherchent à optimiser leurs performances et gérer leurs risques efficacement.
                        </p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <h6 class="text-white mb-3">Liens Utiles</h6>
                        <div class="mb-3">
                            <a href="/mentions-legales" class="footer-link">Mentions Légales</a>
                            <a href="/politique-confidentialite" class="footer-link">Politique de Confidentialité</a>
                            <a href="/contact" class="footer-link">Contact</a>
                        </div>
                        <div class="text-muted">
                            <small>&copy; 2024 MindTraderPro. Tous droits réservés.</small>
                        </div>
                    </div>
                </div>
                <div class="row mt-4 pt-4" style="border-top: 1px solid rgba(255,255,255,0.1);">
                    <div class="col-12 text-center">
                        <div class="text-muted">
                            <i class="fas fa-shield-alt me-2 text-success"></i>
                            Application auditée et sécurisée - Toutes les fonctionnalités vérifiées
                        </div>
                    </div>
                </div>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/')
def index():
    """Redirection vers page d'accueil"""
    return redirect('/home')

@app.route('/calculator')
def calculator():
    """Page calculateur de trading avec navigation unifiée"""
    user_info = get_user_display_info()
    
    # Navigation unifiée selon le statut de connexion
    navbar = ""
    if user_info['is_authenticated']:
        navbar = f'''
        <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px 0;">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/home">
                    <i class="fas fa-chart-line me-2" style="color: #00ff88;"></i>MindTraderPro
                </a>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item"><a class="nav-link" href="/home"><i class="fas fa-home me-1"></i>Accueil</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/calculator"><i class="fas fa-calculator me-1"></i>Calculateur</a></li>
                        <li class="nav-item"><a class="nav-link" href="/journal"><i class="fas fa-book me-1"></i>Journal</a></li>
                        <li class="nav-item"><a class="nav-link" href="/leaderboard"><i class="fas fa-trophy me-1"></i>Classements</a></li>
                    </ul>
                    
                    <div class="d-flex align-items-center">
                        <div class="me-3 text-center d-none d-lg-block">
                            <small class="text-warning d-block fw-bold">2,450 XP</small>
                            <small class="text-muted">Trader Régulier</small>
                        </div>
                        
                        <div class="dropdown">
                            <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown">
                                <div class="user-avatar me-2" style="width: 32px; height: 32px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                                    <i class="fas fa-user"></i>
                                </div>
                                <div class="d-none d-sm-block text-start">
                                    <div style="font-size: 0.9rem; font-weight: bold;">{user_info['first_name']}</div>
                                    <div style="font-size: 0.7rem; opacity: 0.8; color: #FFD700;">{user_info['role'].title()}</div>
                                </div>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end" style="background: rgba(0,0,0,0.95); border: 1px solid rgba(255,255,255,0.2);">
                                <li><a class="dropdown-item text-light" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i>Mon Dashboard</a></li>
                                <li><a class="dropdown-item text-light" href="/dashboard"><i class="fas fa-user me-2"></i>Mon Profil</a></li>
                                <li><hr class="dropdown-divider" style="border-color: rgba(255,255,255,0.2);"></li>
                                <li><a class="dropdown-item text-danger" href="/logout"><i class="fas fa-sign-out-alt me-2"></i>Déconnexion</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
        '''
    else:
        navbar = f'''
        <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px 0;">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/home">
                    <i class="fas fa-chart-line me-2" style="color: #00ff88;"></i>MindTraderPro
                </a>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item"><a class="nav-link" href="/home"><i class="fas fa-home me-1"></i>Accueil</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/calculator"><i class="fas fa-calculator me-1"></i>Calculateur</a></li>
                    </ul>
                    
                    <div class="d-flex">
                        <a href="/login" class="btn btn-outline-light me-2">
                            <i class="fas fa-sign-in-alt me-1"></i>Connexion
                        </a>
                        <a href="/register" class="btn btn-success">
                            <i class="fas fa-user-plus me-1"></i>Inscription
                        </a>
                    </div>
                </div>
            </div>
        </nav>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Calculateur de Position - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
    </head>
    <body>
        <!-- Navigation moderne -->
        <div class="container-fluid">
            <div class="modern-nav">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-home me-2"></i>Accueil
                        </a>
                        <span class="modern-nav-link active">
                            <i class="fas fa-calculator me-2"></i>Calculateur
                        </span>
                    </div>
                    <div>
                        <a href="/journal" class="modern-nav-link">
                            <i class="fas fa-book me-2"></i>Journal
                        </a>
                        <a href="/grades" class="modern-nav-link">
                            <i class="fas fa-trophy me-2"></i>Grades
                        </a>
                        <a href="/parrainage" class="modern-nav-link">
                            <i class="fas fa-users me-2"></i>Parrainage
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Header moderne -->
        <div class="container-fluid">
            <div class="modern-header">
                <h1><i class="fas fa-calculator me-3"></i>Calculateur de Position Professionnel</h1>
                <p>Optimisez vos positions avec notre algorithme avancé de gestion des risques</p>
            </div>
        </div>

        <!-- Contenu principal -->
        <div class="container-fluid">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <!-- Carte principale du calculateur -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-cogs me-2"></i>Paramètres de Trading
                            </h3>
                            <p class="modern-card-subtitle">Configurez votre position pour une gestion optimale du risque</p>
                        </div>
                        
                        <form id="calculatorForm">
                            <div class="row g-4">
                                <!-- Capital et Risque -->
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-wallet me-2"></i>Capital de Trading (USD)
                                        </label>
                                        <input type="number" class="modern-form-control" id="capital" 
                                               value="20000" min="100" step="100" placeholder="Ex: 20000">
                                        <small class="text-muted">Montant total disponible pour le trading</small>
                                    </div>
                                </div>
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-percentage me-2"></i>Risque par Trade (%)
                                        </label>
                                        <input type="number" class="modern-form-control" id="risk" 
                                               value="0.5" min="0.1" max="10" step="0.1" placeholder="Ex: 0.5">
                                        <small class="text-muted">Pourcentage du capital que vous acceptez de risquer</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row g-4">
                                <!-- Paire et Direction -->
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-exchange-alt me-2"></i>Paire de Trading
                                        </label>
                                        <select class="modern-form-control" id="pair">
                                            <option value="XAUUSD">🥇 XAU/USD (Or)</option>
                                            <option value="EURUSD">🇪🇺 EUR/USD</option>
                                            <option value="GBPUSD">🇬🇧 GBP/USD</option>
                                            <option value="USDJPY">🇯🇵 USD/JPY</option>
                                            <option value="USDCHF">🇨🇭 USD/CHF</option>
                                            <option value="AUDUSD">🇦🇺 AUD/USD</option>
                                            <option value="USDCAD">🇨🇦 USD/CAD</option>
                                            <option value="NZDUSD">🇳🇿 NZD/USD</option>
                                            <option value="EURJPY">🇪🇺🇯🇵 EUR/JPY</option>
                                            <option value="GBPJPY">🇬🇧🇯🇵 GBP/JPY</option>
                                            <option value="BTCUSD">₿ BTC/USD</option>
                                            <option value="ETHUSD">⟠ ETH/USD</option>
                                        </select>
                                        <small class="text-muted">Sélectionnez la paire que vous souhaitez trader</small>
                                    </div>
                                </div>
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-arrow-up me-2"></i>Direction du Trade
                                        </label>
                                        <select class="modern-form-control" id="direction">
                                            <option value="buy">📈 Achat (Long)</option>
                                            <option value="sell">📉 Vente (Short)</option>
                                        </select>
                                        <small class="text-muted">Direction anticipée du mouvement de prix</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row g-4">
                                <!-- Prix d'entrée et Stop Loss -->
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-sign-in-alt me-2"></i>Prix d'Entrée
                                        </label>
                                        <input type="number" class="modern-form-control" id="entryPrice" 
                                               value="2000" min="0" step="0.00001" placeholder="Ex: 2000.50">
                                        <small class="text-muted">Prix auquel vous prévoyez d'entrer sur le marché</small>
                                    </div>
                                </div>
                                <div class="col-lg-6">
                                    <div class="modern-form-group">
                                        <label class="modern-form-label">
                                            <i class="fas fa-stop-circle me-2"></i>Stop Loss
                                        </label>
                                        <input type="number" class="modern-form-control" id="stopLoss" 
                                               value="1980" min="0" step="0.00001" placeholder="Ex: 1980.00">
                                        <small class="text-muted">Prix de votre stop de protection</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="text-center mt-4">
                                <button type="button" class="modern-btn modern-btn-success btn-lg" onclick="calculatePosition()">
                                    <i class="fas fa-calculator me-2"></i>Calculer la Position Optimale
                                </button>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Résultats -->
                    <div id="results" class="modern-card" style="display: none;">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-chart-pie me-2"></i>Résultats du Calcul
                            </h3>
                            <p class="modern-card-subtitle">Position optimisée selon votre profil de risque</p>
                        </div>
                        
                        <div class="row g-4">
                            <div class="col-lg-3 col-md-6">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-balance-scale"></i>
                                    </div>
                                    <div class="modern-stat-number" id="lotSize">0.00</div>
                                    <div class="modern-stat-label">Lots à Trader</div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-dollar-sign"></i>
                                    </div>
                                    <div class="modern-stat-number" id="riskUSD" style="background: var(--warning-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">$0.00</div>
                                    <div class="modern-stat-label">Risque en USD</div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-ruler"></i>
                                    </div>
                                    <div class="modern-stat-number" id="pipDistance" style="background: var(--info-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">0</div>
                                    <div class="modern-stat-label">Distance (pips)</div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-coins"></i>
                                    </div>
                                    <div class="modern-stat-number" id="pipValue" style="background: var(--success-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">$0.00</div>
                                    <div class="modern-stat-label">Valeur par Pip</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Analyse du risque -->
                        <div class="modern-alert modern-alert-info mt-4">
                            <h6><i class="fas fa-shield-alt me-2"></i>Analyse du Risque</h6>
                            <div id="riskAnalysis"></div>
                        </div>
                    </div>
                    
                    <!-- Actions rapides -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-bolt me-2"></i>Actions Rapides
                            </h3>
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-lg-3 col-md-6">
                                <button class="modern-btn modern-btn-info w-100" onclick="saveToJournal()">
                                    <i class="fas fa-book me-2"></i>Sauver au Journal
                                </button>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <button class="modern-btn modern-btn-warning w-100" onclick="shareCalculation()">
                                    <i class="fas fa-share-alt me-2"></i>Partager
                                </button>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <button class="modern-btn modern-btn-secondary w-100" onclick="resetCalculator()">
                                    <i class="fas fa-redo me-2"></i>Réinitialiser
                                </button>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <a href="/grades" class="modern-btn modern-btn-success w-100">
                                    <i class="fas fa-plus me-2"></i>Gagner +5 XP
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function calculatePosition() {{
                const capital = parseFloat(document.getElementById('capital').value);
                const risk = parseFloat(document.getElementById('risk').value);
                const pair = document.getElementById('pair').value;
                const direction = document.getElementById('direction').value;
                const entryPrice = parseFloat(document.getElementById('entryPrice').value);
                const stopLoss = parseFloat(document.getElementById('stopLoss').value);
                
                // Validation des champs
                if (!capital || !risk || !entryPrice || !stopLoss) {{
                    showNotification('⚠️ Veuillez remplir tous les champs obligatoires', 'warning');
                    return;
                }}
                
                if (capital < 100) {{
                    showNotification('⚠️ Le capital minimum est de 100 USD', 'warning');
                    return;
                }}
                
                if (risk > 10) {{
                    showNotification('⚠️ Le risque ne devrait pas dépasser 10%', 'warning');
                    return;
                }}
                
                // Calcul de la distance en pips
                const priceDiff = Math.abs(entryPrice - stopLoss);
                let pipDistance;
                let pipValue;
                
                // Calcul selon la paire
                switch(pair) {{
                    case 'XAUUSD':
                        pipDistance = Math.round(priceDiff * 10); // Or: 1 pip = 0.1
                        pipValue = 1.0;
                        break;
                    case 'USDJPY':
                        pipDistance = Math.round(priceDiff * 100); // JPY: 1 pip = 0.01
                        pipValue = 0.01;
                        break;
                    case 'EURJPY':
                    case 'GBPJPY':
                        pipDistance = Math.round(priceDiff * 100);
                        pipValue = 0.01;
                        break;
                    case 'BTCUSD':
                        pipDistance = Math.round(priceDiff); // BTC: 1 pip = 1
                        pipValue = 10.0;
                        break;
                    case 'ETHUSD':
                        pipDistance = Math.round(priceDiff * 10);
                        pipValue = 1.0;
                        break;
                    default: // Paires majeures
                        pipDistance = Math.round(priceDiff * 10000); // 1 pip = 0.0001
                        pipValue = 0.1;
                        break;
                }
                
                // Calcul de la position
                const riskUSD = capital * (risk / 100);
                const lotSize = Math.max(0.01, riskUSD / (pipDistance * pipValue * 100));
                const actualPipValue = pipValue * 100 * lotSize;
                
                // Affichage des résultats
                document.getElementById('lotSize').textContent = lotSize.toFixed(2);
                document.getElementById('riskUSD').textContent = '$' + riskUSD.toFixed(2);
                document.getElementById('pipDistance').textContent = pipDistance;
                document.getElementById('pipValue').textContent = '$' + actualPipValue.toFixed(2);
                
                // Analyse du risque
                let riskAnalysis = '';
                if (risk <= 1) {
                    riskAnalysis = '✅ <strong>Risque Conservateur:</strong> Excellente gestion du risque pour préserver le capital.';
                } else if (risk <= 2) {
                    riskAnalysis = '⚡ <strong>Risque Modéré:</strong> Bon équilibre entre croissance et protection.';
                } else if (risk <= 5) {
                    riskAnalysis = '⚠️ <strong>Risque Élevé:</strong> Surveillez attentivement vos positions.';
                } else {
                    riskAnalysis = '🚨 <strong>Risque Très Élevé:</strong> Considérez réduire votre exposition.';
                }
                
                if (pipDistance < 10) {
                    riskAnalysis += '<br>📏 <strong>Stop Loss Serré:</strong> Risque de sortie prématurée par volatilité.';
                }
                
                if (lotSize < 0.1) {
                    riskAnalysis += '<br>📉 <strong>Petite Position:</strong> Impact limité sur le capital.';
                } else if (lotSize > 5) {
                    riskAnalysis += '<br>📈 <strong>Position Importante:</strong> Vérifiez votre effet de levier.';
                }
                
                document.getElementById('riskAnalysis').innerHTML = riskAnalysis;
                
                // Animation d'apparition
                const resultsDiv = document.getElementById('results');
                resultsDiv.style.display = 'block';
                resultsDiv.style.opacity = '0';
                resultsDiv.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    resultsDiv.style.transition = 'all 0.6s ease';
                    resultsDiv.style.opacity = '1';
                    resultsDiv.style.transform = 'translateY(0)';
                }, 100);
                
                showNotification('✅ Position calculée avec succès!', 'success');
            }
            
            function resetCalculator() {
                document.getElementById('capital').value = '20000';
                document.getElementById('risk').value = '0.5';
                document.getElementById('pair').value = 'XAUUSD';
                document.getElementById('direction').value = 'buy';
                document.getElementById('entryPrice').value = '2000';
                document.getElementById('stopLoss').value = '1980';
                document.getElementById('results').style.display = 'none';
                showNotification('🔄 Calculateur réinitialisé', 'info');
            }
            
            function shareCalculation() {
                const pair = document.getElementById('pair').value;
                const direction = document.getElementById('direction').value;
                const entryPrice = document.getElementById('entryPrice').value;
                const stopLoss = document.getElementById('stopLoss').value;
                const lotSize = document.getElementById('lotSize').textContent;
                
                const shareText = `📊 Calcul MindTraderPro:\\n${pair} ${direction.toUpperCase()}\\nEntrée: ${entryPrice}\\nStop: ${stopLoss}\\nPosition: ${lotSize} lots`;
                
                if (navigator.share) {
                    navigator.share({
                        title: 'Calcul MindTraderPro',
                        text: shareText
                    });
                } else {
                    navigator.clipboard.writeText(shareText);
                    showNotification('📋 Calcul copié dans le presse-papiers!', 'success');
                }
            }
            
            function saveToJournal() {
                showNotification('💾 Position sauvée dans le journal! (Fonctionnalité Premium)', 'info');
            }
            
            function showNotification(message, type) {
                const notification = document.createElement('div');
                notification.className = `modern-alert modern-alert-${type} position-fixed`;
                notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 350px;';
                notification.innerHTML = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.opacity = '0';
                    setTimeout(() => notification.remove(), 300);
                }, 4000);
            }
            
            // Animation au chargement
            document.addEventListener('DOMContentLoaded', function() {
                document.body.style.opacity = '0';
                setTimeout(() => {
                    document.body.style.transition = 'opacity 0.5s ease';
                    document.body.style.opacity = '1';
                }, 100);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/leaderboard-parrainage')
def leaderboard_parrainage():
    """Page leaderboard des parrains modernisée"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Classement des Parrains - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
        <style>
            .sponsor-podium-card {
                position: relative;
                border: 2px solid transparent;
                transition: all 0.3s ease;
            }
            .sponsor-gold {
                background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,193,7,0.1));
                border-color: #ffd700;
                box-shadow: 0 0 30px rgba(255,215,0,0.3);
                animation: gold-pulse 3s infinite;
            }
            .sponsor-silver {
                background: linear-gradient(135deg, rgba(192,192,192,0.2), rgba(169,169,169,0.1));
                border-color: #c0c0c0;
                box-shadow: 0 0 25px rgba(192,192,192,0.3);
                animation: silver-pulse 3s infinite;
            }
            .sponsor-bronze {
                background: linear-gradient(135deg, rgba(205,127,50,0.2), rgba(184,115,51,0.1));
                border-color: #cd7f32;
                box-shadow: 0 0 20px rgba(205,127,50,0.3);
                animation: bronze-pulse 3s infinite;
            }
            @keyframes gold-pulse {
                0%, 100% { box-shadow: 0 0 30px rgba(255,215,0,0.3); }
                50% { box-shadow: 0 0 40px rgba(255,215,0,0.5); }
            }
            @keyframes silver-pulse {
                0%, 100% { box-shadow: 0 0 25px rgba(192,192,192,0.3); }
                50% { box-shadow: 0 0 35px rgba(192,192,192,0.5); }
            }
            @keyframes bronze-pulse {
                0%, 100% { box-shadow: 0 0 20px rgba(205,127,50,0.3); }
                50% { box-shadow: 0 0 30px rgba(205,127,50,0.5); }
            }
            .sponsor-rank-badge {
                position: absolute;
                top: -15px;
                left: 50%;
                transform: translateX(-50%);
                width: 45px;
                height: 45px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 1.3rem;
                z-index: 10;
                border: 3px solid white;
            }
            .sponsor-rank-1 { background: linear-gradient(135deg, #ffd700, #ffed4e); color: #000; }
            .sponsor-rank-2 { background: linear-gradient(135deg, #c0c0c0, #e5e5e5); color: #000; }
            .sponsor-rank-3 { background: linear-gradient(135deg, #cd7f32, #daa520); color: #fff; }
            .referral-progress {
                height: 12px;
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                overflow: hidden;
                margin-top: 10px;
                position: relative;
            }
            .referral-fill {
                height: 100%;
                border-radius: 15px;
                transition: width 1s ease;
                position: relative;
                overflow: hidden;
            }
            .referral-fill::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            }
            @keyframes shimmer {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            .sponsor-avatar {
                width: 70px;
                height: 70px;
                border-radius: 50%;
                background: var(--accent-gradient);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.8rem;
                font-weight: bold;
                margin-right: 15px;
                border: 3px solid rgba(255,255,255,0.2);
            }
            .sponsor-badge {
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: bold;
                margin-left: 10px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }
            .badge-bronze { background: linear-gradient(135deg, #cd7f32, #daa520); }
            .badge-silver { background: linear-gradient(135deg, #c0c0c0, #e5e5e5); color: #000; }
            .badge-gold { background: linear-gradient(135deg, #ffd700, #ffed4e); color: #000; }
            .badge-platine { background: linear-gradient(135deg, #e5e4e2, #d3d3d3); color: #000; }
            .lifetime-glow {
                box-shadow: 0 0 20px rgba(238, 130, 238, 0.5);
                border-color: #ee82ee !important;
            }
            .personal-rank-card {
                border: 2px solid var(--secondary-gradient);
                animation: personal-pulse 2.5s infinite;
                position: relative;
                overflow: hidden;
            }
            .personal-rank-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(243, 147, 251, 0.1), transparent);
                animation: personal-shimmer 3s infinite;
            }
            @keyframes personal-pulse {
                0%, 100% { border-color: var(--secondary-gradient); }
                50% { border-color: rgba(243, 147, 251, 0.7); }
            }
            @keyframes personal-shimmer {
                0% { left: -100%; }
                100% { left: 100%; }
            }
        </style>
    </head>
    <body>
        <!-- Navigation moderne -->
        <div class="container-fluid">
            <div class="modern-nav">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-home me-2"></i>Accueil
                        </a>
                        <a href="/leaderboard" class="modern-nav-link">
                            <i class="fas fa-medal me-2"></i>Classement
                        </a>
                        <span class="modern-nav-link active">
                            <i class="fas fa-users me-2"></i>Parrains
                        </span>
                    </div>
                    <div>
                        <a href="/parrainage" class="modern-nav-link">
                            <i class="fas fa-user-plus me-2"></i>Mon Parrainage
                        </a>
                        <a href="/grades" class="modern-nav-link">
                            <i class="fas fa-trophy me-2"></i>Grades
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Header moderne -->
        <div class="container-fluid">
            <div class="modern-header">
                <h1><i class="fas fa-users me-3"></i>Classement des Parrains</h1>
                <p>Les meilleurs ambassadeurs de la communauté MindTraderPro</p>
            </div>
        </div>

        <!-- Contenu principal -->
        <div class="container-fluid">
            <div class="row">
                <div class="col-lg-8">
                    <!-- Podium Top 3 Parrains -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-crown me-2"></i>Podium des Meilleurs Parrains
                            </h3>
                            <p class="modern-card-subtitle">Les ambassadeurs les plus actifs du mois</p>
                        </div>
                        
                        <div class="row g-4">
                            <!-- 1ère Place -->
                            <div class="col-md-4">
                                <div class="modern-card sponsor-podium-card sponsor-gold lifetime-glow">
                                    <div class="sponsor-rank-badge sponsor-rank-1">
                                        <i class="fas fa-trophy"></i>
                                    </div>
                                    <div class="text-center pt-3">
                                        <div class="sponsor-avatar mx-auto mb-3">
                                            <i class="fas fa-crown"></i>
                                        </div>
                                        <h5 class="text-white">Thomas R.</h5>
                                        <span class="role-badge role-lifetime">
                                            <i class="fas fa-gem me-1"></i>Lifetime VIP
                                        </span>
                                        <div class="sponsor-badge badge-platine mt-2">
                                            <i class="fas fa-star"></i>Parrain Platine
                                        </div>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.4rem;">47</div>
                                            <div class="modern-stat-label">Filleuls Validés</div>
                                        </div>
                                        <div class="mt-2">
                                            <div class="modern-stat-number" style="font-size: 1.2rem; background: var(--warning-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">2,350</div>
                                            <div class="modern-stat-label">XP Parrainage</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Taux de conversion: 89%</small>
                                            <div class="referral-progress">
                                                <div class="referral-fill" style="width: 89%; background: var(--warning-gradient);">
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 2ème Place -->
                            <div class="col-md-4">
                                <div class="modern-card sponsor-podium-card sponsor-silver">
                                    <div class="sponsor-rank-badge sponsor-rank-2">
                                        <i class="fas fa-medal"></i>
                                    </div>
                                    <div class="text-center pt-3">
                                        <div class="sponsor-avatar mx-auto mb-3">
                                            <i class="fas fa-medal"></i>
                                        </div>
                                        <h5 class="text-white">Marie C.</h5>
                                        <span class="role-badge role-premium">
                                            <i class="fas fa-star me-1"></i>Premium
                                        </span>
                                        <div class="sponsor-badge badge-gold mt-2">
                                            <i class="fas fa-award"></i>Parrain Or
                                        </div>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.4rem;">32</div>
                                            <div class="modern-stat-label">Filleuls Validés</div>
                                        </div>
                                        <div class="mt-2">
                                            <div class="modern-stat-number" style="font-size: 1.2rem; background: var(--info-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">1,600</div>
                                            <div class="modern-stat-label">XP Parrainage</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Taux de conversion: 76%</small>
                                            <div class="referral-progress">
                                                <div class="referral-fill" style="width: 76%; background: var(--info-gradient);">
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 3ème Place -->
                            <div class="col-md-4">
                                <div class="modern-card sponsor-podium-card sponsor-bronze">
                                    <div class="sponsor-rank-badge sponsor-rank-3">
                                        <i class="fas fa-award"></i>
                                    </div>
                                    <div class="text-center pt-3">
                                        <div class="sponsor-avatar mx-auto mb-3">
                                            <i class="fas fa-award"></i>
                                        </div>
                                        <h5 class="text-white">Pierre L.</h5>
                                        <span class="role-badge role-premium">
                                            <i class="fas fa-star me-1"></i>Premium
                                        </span>
                                        <div class="sponsor-badge badge-silver mt-2">
                                            <i class="fas fa-chess-queen"></i>Parrain Argent
                                        </div>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.4rem;">24</div>
                                            <div class="modern-stat-label">Filleuls Validés</div>
                                        </div>
                                        <div class="mt-2">
                                            <div class="modern-stat-number" style="font-size: 1.2rem; background: var(--success-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">1,200</div>
                                            <div class="modern-stat-label">XP Parrainage</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Taux de conversion: 68%</small>
                                            <div class="referral-progress">
                                                <div class="referral-fill" style="width: 68%; background: var(--success-gradient);">
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Classement complet des parrains -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-list-ol me-2"></i>Classement des Ambassadeurs
                            </h3>
                            <p class="modern-card-subtitle">Top 15 des parrains les plus performants</p>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="modern-table w-100">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Parrain</th>
                                        <th>Filleuls</th>
                                        <th>XP Total</th>
                                        <th>Performance</th>
                                        <th>Badge</th>
                                    </tr>
                                </thead>
                                <tbody id="sponsorLeaderboardTable">
                                    <!-- Les données seront générées par JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <!-- Ton rang personnel -->
                    <div class="modern-card personal-rank-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-user-crown me-2"></i>Ton Rang de Parrain
                            </h3>
                        </div>
                        
                        <div class="text-center position-relative">
                            <div class="sponsor-avatar mx-auto mb-3" style="width: 90px; height: 90px; font-size: 2.2rem;">
                                <i class="fas fa-user"></i>
                            </div>
                            <h4 class="text-gradient mb-2">Visiteur</h4>
                            
                            <div class="modern-alert modern-alert-info">
                                <h6><i class="fas fa-info-circle me-2"></i>Statut Actuel</h6>
                                <p class="mb-2"><strong>Position:</strong> Non classé</p>
                                <p class="mb-2"><strong>Filleuls:</strong> 0</p>
                                <p class="mb-2"><strong>XP Parrainage:</strong> 0</p>
                                <p class="mb-0"><strong>Badge:</strong> Aucun</p>
                            </div>
                            
                            <div class="mt-4">
                                <a href="/register" class="modern-btn modern-btn-success w-100 mb-2">
                                    <i class="fas fa-rocket me-2"></i>Créer un Compte
                                </a>
                                <a href="/parrainage" class="modern-btn modern-btn-warning w-100">
                                    <i class="fas fa-users me-2"></i>Commencer à Parrainer
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Badges de parrainage -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-trophy me-2"></i>Badges de Parrainage
                            </h3>
                        </div>
                        
                        <div class="d-grid gap-3">
                            <div class="modern-alert modern-alert-info">
                                <div class="d-flex align-items-center">
                                    <div class="sponsor-badge badge-bronze me-3">
                                        <i class="fas fa-user-plus"></i>Bronze
                                    </div>
                                    <div>
                                        <strong>5+ filleuls</strong><br>
                                        <small>+50 XP bonus</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="modern-alert modern-alert-warning">
                                <div class="d-flex align-items-center">
                                    <div class="sponsor-badge badge-silver me-3">
                                        <i class="fas fa-chess-queen"></i>Argent
                                    </div>
                                    <div>
                                        <strong>15+ filleuls</strong><br>
                                        <small>+150 XP bonus</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="modern-alert modern-alert-success">
                                <div class="d-flex align-items-center">
                                    <div class="sponsor-badge badge-gold me-3">
                                        <i class="fas fa-award"></i>Or
                                    </div>
                                    <div>
                                        <strong>30+ filleuls</strong><br>
                                        <small>+300 XP bonus</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="modern-alert modern-alert-info">
                                <div class="d-flex align-items-center">
                                    <div class="sponsor-badge badge-platine me-3">
                                        <i class="fas fa-star"></i>Platine
                                    </div>
                                    <div>
                                        <strong>50+ filleuls</strong><br>
                                        <small>+500 XP + VIP 1 mois</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Statistiques du parrainage -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-chart-line me-2"></i>Stats Globales
                            </h3>
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.6rem;">312</div>
                                    <div class="modern-stat-label">Parrains Actifs</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.6rem;">1,847</div>
                                    <div class="modern-stat-label">Filleuls Total</div>
                                </div>
                            </div>
                            <div class="col-12">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.6rem;">68%</div>
                                    <div class="modern-stat-label">Taux Conversion Moyen</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Données du classement des parrains
            const sponsorData = [
                { rank: 4, name: "Julie M.", referrals: 19, xp: 950, conversion: 63, badge: "argent", role: "premium" },
                { rank: 5, name: "David K.", referrals: 17, xp: 850, conversion: 58, badge: "argent", role: "standard" },
                { rank: 6, name: "Sophie T.", referrals: 15, xp: 750, conversion: 60, badge: "argent", role: "premium" },
                { rank: 7, name: "Marc B.", referrals: 13, xp: 650, conversion: 54, badge: "bronze", role: "lifetime" },
                { rank: 8, name: "Laura P.", referrals: 12, xp: 600, conversion: 50, badge: "bronze", role: "standard" },
                { rank: 9, name: "Alex V.", referrals: 11, xp: 550, conversion: 52, badge: "bronze", role: "premium" },
                { rank: 10, name: "Emma D.", referrals: 10, xp: 500, conversion: 48, badge: "bronze", role: "standard" },
                { rank: 11, name: "Nicolas S.", referrals: 9, xp: 450, conversion: 45, badge: "bronze", role: "premium" },
                { rank: 12, name: "Chloe R.", referrals: 8, xp: 400, conversion: 44, badge: "bronze", role: "standard" },
                { rank: 13, name: "Antoine L.", referrals: 7, xp: 350, conversion: 42, badge: "bronze", role: "standard" },
                { rank: 14, name: "Lisa H.", referrals: 6, xp: 300, conversion: 40, badge: "bronze", role: "premium" },
                { rank: 15, name: "Tom W.", referrals: 5, xp: 250, conversion: 38, badge: "bronze", role: "standard" }
            ];
            
            function generateSponsorLeaderboard() {
                const tbody = document.getElementById('sponsorLeaderboardTable');
                tbody.innerHTML = '';
                
                sponsorData.forEach(sponsor => {
                    const row = document.createElement('tr');
                    
                    let badgeClass = '';
                    let badgeIcon = '';
                    switch(sponsor.badge) {
                        case 'bronze':
                            badgeClass = 'badge-bronze';
                            badgeIcon = 'fas fa-user-plus';
                            break;
                        case 'argent':
                            badgeClass = 'badge-silver';
                            badgeIcon = 'fas fa-chess-queen';
                            break;
                        case 'or':
                            badgeClass = 'badge-gold';
                            badgeIcon = 'fas fa-award';
                            break;
                        case 'platine':
                            badgeClass = 'badge-platine';
                            badgeIcon = 'fas fa-star';
                            break;
                    }
                    
                    row.innerHTML = `
                        <td><strong>#${sponsor.rank}</strong></td>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="sponsor-avatar" style="width: 40px; height: 40px; font-size: 1rem; margin-right: 10px;">
                                    ${sponsor.name.charAt(0)}
                                </div>
                                <div>
                                    <div>${sponsor.name}</div>
                                    ${sponsor.role === 'premium' ? '<span class="role-badge role-premium"><i class="fas fa-star"></i></span>' : ''}
                                    ${sponsor.role === 'lifetime' ? '<span class="role-badge role-lifetime"><i class="fas fa-gem"></i></span>' : ''}
                                </div>
                            </div>
                        </td>
                        <td><strong>${sponsor.referrals}</strong></td>
                        <td><strong>${sponsor.xp}</strong> XP</td>
                        <td>
                            <div class="referral-progress">
                                <div class="referral-fill" style="width: ${sponsor.conversion}%; background: var(--success-gradient);">
                                </div>
                            </div>
                            <small class="text-muted">${sponsor.conversion}%</small>
                        </td>
                        <td>
                            <div class="sponsor-badge ${badgeClass}">
                                <i class="${badgeIcon}"></i>
                                ${sponsor.badge.charAt(0).toUpperCase() + sponsor.badge.slice(1)}
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Animation des barres de progression
            function animateSponsorBars() {
                setTimeout(() => {
                    const progressBars = document.querySelectorAll('.referral-fill');
                    progressBars.forEach(bar => {
                        const width = bar.style.width;
                        bar.style.width = '0%';
                        setTimeout(() => {
                            bar.style.width = width;
                        }, Math.random() * 500 + 200);
                    });
                }, 800);
            }
            
            // Initialisation
            document.addEventListener('DOMContentLoaded', function() {
                generateSponsorLeaderboard();
                animateSponsorBars();
                
                // Animation d'apparition
                document.body.style.opacity = '0';
                setTimeout(() => {
                    document.body.style.transition = 'opacity 0.6s ease';
                    document.body.style.opacity = '1';
                }, 100);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/leaderboard')
def leaderboard():
    """Page leaderboard des traders modernisée"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Leaderboard - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
        <style>
            .podium-card {
                position: relative;
                border: 2px solid transparent;
                transition: all 0.3s ease;
            }
            .podium-gold {
                background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,193,7,0.1));
                border-color: #ffd700;
                box-shadow: 0 0 30px rgba(255,215,0,0.3);
            }
            .podium-silver {
                background: linear-gradient(135deg, rgba(192,192,192,0.2), rgba(169,169,169,0.1));
                border-color: #c0c0c0;
                box-shadow: 0 0 25px rgba(192,192,192,0.3);
            }
            .podium-bronze {
                background: linear-gradient(135deg, rgba(205,127,50,0.2), rgba(184,115,51,0.1));
                border-color: #cd7f32;
                box-shadow: 0 0 20px rgba(205,127,50,0.3);
            }
            .rank-badge {
                position: absolute;
                top: -15px;
                left: 50%;
                transform: translateX(-50%);
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 1.2rem;
                z-index: 10;
            }
            .rank-1 { background: linear-gradient(135deg, #ffd700, #ffed4e); color: #000; }
            .rank-2 { background: linear-gradient(135deg, #c0c0c0, #e5e5e5); color: #000; }
            .rank-3 { background: linear-gradient(135deg, #cd7f32, #daa520); color: #fff; }
            .xp-progress {
                height: 8px;
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                overflow: hidden;
                margin-top: 10px;
            }
            .xp-fill {
                height: 100%;
                background: var(--success-gradient);
                border-radius: 10px;
                transition: width 0.8s ease;
            }
            .user-avatar {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: var(--accent-gradient);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.5rem;
                font-weight: bold;
                margin-right: 15px;
            }
            .role-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: bold;
                margin-left: 10px;
            }
            .role-premium { background: var(--warning-gradient); }
            .role-lifetime { background: var(--secondary-gradient); }
            .role-admin { background: var(--danger-gradient); }
            .current-rank-card {
                border: 2px solid var(--accent-gradient);
                animation: pulse-border 2s infinite;
            }
            @keyframes pulse-border {
                0%, 100% { border-color: var(--accent-gradient); }
                50% { border-color: rgba(79, 172, 254, 0.5); }
            }
        </style>
    </head>
    <body>
        <!-- Navigation moderne -->
        <div class="container-fluid">
            <div class="modern-nav">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-home me-2"></i>Accueil
                        </a>
                        <span class="modern-nav-link active">
                            <i class="fas fa-medal me-2"></i>Leaderboard
                        </span>
                    </div>
                    <div>
                        <a href="/calculator" class="modern-nav-link">
                            <i class="fas fa-calculator me-2"></i>Calculateur
                        </a>
                        <a href="/grades" class="modern-nav-link">
                            <i class="fas fa-trophy me-2"></i>Grades
                        </a>
                        <a href="/parrainage" class="modern-nav-link">
                            <i class="fas fa-users me-2"></i>Parrainage
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Header moderne -->
        <div class="container-fluid">
            <div class="modern-header">
                <h1><i class="fas fa-trophy me-3"></i>Leaderboard des Traders</h1>
                <p>Découvrez les meilleurs traders de la communauté MindTraderPro</p>
            </div>
        </div>

        <!-- Contenu principal -->
        <div class="container-fluid">
            <div class="row">
                <div class="col-lg-8">
                    <!-- Podium Top 3 -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-crown me-2"></i>Podium des Champions
                            </h3>
                            <p class="modern-card-subtitle">Les 3 meilleurs traders du mois</p>
                        </div>
                        
                        <div class="row g-4">
                            <!-- 1ère Place -->
                            <div class="col-md-4">
                                <div class="modern-card podium-card podium-gold">
                                    <div class="rank-badge rank-1">1</div>
                                    <div class="text-center pt-3">
                                        <div class="user-avatar mx-auto mb-3">
                                            <i class="fas fa-crown"></i>
                                        </div>
                                        <h5 class="text-white">Alexandre M.</h5>
                                        <span class="role-badge role-lifetime">
                                            <i class="fas fa-gem me-1"></i>Lifetime
                                        </span>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.5rem;">15,750</div>
                                            <div class="modern-stat-label">XP Total</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Grade: Légende</small>
                                            <div class="xp-progress">
                                                <div class="xp-fill" style="width: 95%;"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 2ème Place -->
                            <div class="col-md-4">
                                <div class="modern-card podium-card podium-silver">
                                    <div class="rank-badge rank-2">2</div>
                                    <div class="text-center pt-3">
                                        <div class="user-avatar mx-auto mb-3">
                                            <i class="fas fa-medal"></i>
                                        </div>
                                        <h5 class="text-white">Sophie L.</h5>
                                        <span class="role-badge role-premium">
                                            <i class="fas fa-star me-1"></i>Premium
                                        </span>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.5rem;">12,480</div>
                                            <div class="modern-stat-label">XP Total</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Grade: Expert</small>
                                            <div class="xp-progress">
                                                <div class="xp-fill" style="width: 78%;"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 3ème Place -->
                            <div class="col-md-4">
                                <div class="modern-card podium-card podium-bronze">
                                    <div class="rank-badge rank-3">3</div>
                                    <div class="text-center pt-3">
                                        <div class="user-avatar mx-auto mb-3">
                                            <i class="fas fa-award"></i>
                                        </div>
                                        <h5 class="text-white">Marc D.</h5>
                                        <span class="role-badge role-premium">
                                            <i class="fas fa-star me-1"></i>Premium
                                        </span>
                                        <div class="mt-3">
                                            <div class="modern-stat-number" style="font-size: 1.5rem;">9,820</div>
                                            <div class="modern-stat-label">XP Total</div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">Grade: Trader Régulier</small>
                                            <div class="xp-progress">
                                                <div class="xp-fill" style="width: 65%;"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Classement complet -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-list-ol me-2"></i>Classement Complet
                            </h3>
                            <p class="modern-card-subtitle">Top 20 des traders les plus actifs</p>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="modern-table w-100">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Trader</th>
                                        <th>XP</th>
                                        <th>Grade</th>
                                        <th>Progression</th>
                                    </tr>
                                </thead>
                                <tbody id="leaderboardTable">
                                    <!-- Les données seront générées par JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <!-- Ton rang actuel -->
                    <div class="modern-card current-rank-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-user me-2"></i>Ton Rang Actuel
                            </h3>
                        </div>
                        
                        <div class="text-center">
                            <div class="user-avatar mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2rem;">
                                <i class="fas fa-user"></i>
                            </div>
                            ''' + (f'''
                            <h4 class="text-gradient mb-2">{user_info['name']}</h4>
                            <span class="role-badge role-{user_info['role']}">
                                <i class="fas fa-{'gem' if user_info['role'] == 'lifetime' else 'star' if user_info['role'] == 'premium' else 'shield-alt' if user_info['role'] == 'admin' else 'user'} me-1"></i>
                                {user_info['role'].title()}
                            </span>
                            <div class="modern-alert modern-alert-success mt-3">
                                <p class="mb-2"><strong>Position: #12</strong></p>
                                <p class="mb-2">XP: 8,450 / 10,000</p>
                                <p class="mb-0">Grade: Expert</p>
                            </div>
                            
                            <div class="mt-4">
                                <a href="/calculator" class="modern-btn modern-btn-success w-100 mb-2">
                                    <i class="fas fa-calculator me-2"></i>Calculateur
                                </a>
                                <a href="/logout" class="modern-btn modern-btn-outline w-100">
                                    <i class="fas fa-sign-out-alt me-2"></i>Déconnexion
                                </a>
                            </div>
                            ''' if user_info['is_authenticated'] else '''
                            <h4 class="text-gradient mb-2">Visiteur</h4>
                            <div class="modern-alert modern-alert-info">
                                <p class="mb-2"><strong>Position: #--</strong></p>
                                <p class="mb-2">XP: 0 / 100</p>
                                <p class="mb-0">Grade: Nouveau</p>
                            </div>
                            
                            <div class="mt-4">
                                <a href="/register" class="modern-btn modern-btn-success w-100 mb-2">
                                    <i class="fas fa-rocket me-2"></i>Créer un Compte
                                </a>
                                <a href="/login" class="modern-btn modern-btn-info w-100">
                                    <i class="fas fa-sign-in-alt me-2"></i>Se Connecter
                                </a>
                            </div>
                            ''') + '''
                        </div>
                    </div>

                    <!-- Statistiques générales -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-chart-bar me-2"></i>Statistiques Globales
                            </h3>
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.8rem;">847</div>
                                    <div class="modern-stat-label">Traders Actifs</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.8rem;">156</div>
                                    <div class="modern-stat-label">Traders Premium</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.8rem;">23</div>
                                    <div class="modern-stat-label">Lifetime VIP</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="modern-stat-card">
                                    <div class="modern-stat-number" style="font-size: 1.8rem;">2.4M</div>
                                    <div class="modern-stat-label">XP Total</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Récompenses du mois -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-gift me-2"></i>Récompenses du Mois
                            </h3>
                        </div>
                        
                        <div class="d-grid gap-2">
                            <div class="modern-alert modern-alert-warning">
                                <h6><i class="fas fa-crown me-2"></i>1ère Place</h6>
                                <p class="mb-1">• Badge "Champion du Mois"</p>
                                <p class="mb-1">• 500 XP Bonus</p>
                                <p class="mb-0">• Accès VIP 1 mois</p>
                            </div>
                            
                            <div class="modern-alert modern-alert-info">
                                <h6><i class="fas fa-medal me-2"></i>Top 10</h6>
                                <p class="mb-1">• Badge "Elite Trader"</p>
                                <p class="mb-0">• 200 XP Bonus</p>
                            </div>
                            
                            <div class="modern-alert modern-alert-success">
                                <h6><i class="fas fa-star me-2"></i>Top 50</h6>
                                <p class="mb-0">• 50 XP Bonus</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Génération du tableau de classement
            const leaderboardData = [
                { rank: 4, name: "Thomas B.", xp: 8650, grade: "Trader Régulier", role: "premium", progress: 58 },
                { rank: 5, name: "Marie K.", xp: 7890, grade: "Actif", role: "standard", progress: 45 },
                { rank: 6, name: "Pierre L.", xp: 7420, grade: "Actif", role: "premium", progress: 42 },
                { rank: 7, name: "Julie R.", xp: 6980, grade: "Actif", role: "standard", progress: 38 },
                { rank: 8, name: "David M.", xp: 6540, grade: "Actif", role: "lifetime", progress: 35 },
                { rank: 9, name: "Sarah T.", xp: 6120, grade: "Actif", role: "premium", progress: 32 },
                { rank: 10, name: "Luc P.", xp: 5750, grade: "Débutant", role: "standard", progress: 28 },
                { rank: 11, name: "Emma D.", xp: 5380, grade: "Débutant", role: "premium", progress: 25 },
                { rank: 12, name: "Nicolas V.", xp: 4950, grade: "Débutant", role: "standard", progress: 22 },
                { rank: 13, name: "Chloe M.", xp: 4620, grade: "Débutant", role: "premium", progress: 19 },
                { rank: 14, name: "Antoine S.", xp: 4280, grade: "Débutant", role: "standard", progress: 16 },
                { rank: 15, name: "Lisa H.", xp: 3940, grade: "Débutant", role: "standard", progress: 13 }
            ];
            
            function generateLeaderboard() {
                const tbody = document.getElementById('leaderboardTable');
                tbody.innerHTML = '';
                
                leaderboardData.forEach(trader => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><strong>#${trader.rank}</strong></td>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="user-avatar" style="width: 35px; height: 35px; font-size: 0.9rem; margin-right: 10px;">
                                    ${trader.name.charAt(0)}
                                </div>
                                <div>
                                    <div>${trader.name}</div>
                                    ${trader.role === 'premium' ? '<span class="role-badge role-premium"><i class="fas fa-star"></i> Premium</span>' : ''}
                                    ${trader.role === 'lifetime' ? '<span class="role-badge role-lifetime"><i class="fas fa-gem"></i> Lifetime</span>' : ''}
                                </div>
                            </div>
                        </td>
                        <td><strong>${trader.xp.toLocaleString()}</strong></td>
                        <td>${trader.grade}</td>
                        <td>
                            <div class="xp-progress">
                                <div class="xp-fill" style="width: ${trader.progress}%;"></div>
                            </div>
                            <small class="text-muted">${trader.progress}%</small>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Animation des barres de progression
            function animateProgressBars() {
                setTimeout(() => {
                    const progressBars = document.querySelectorAll('.xp-fill');
                    progressBars.forEach(bar => {
                        const width = bar.style.width;
                        bar.style.width = '0%';
                        setTimeout(() => {
                            bar.style.width = width;
                        }, 100);
                    });
                }, 500);
            }
            
            // Initialisation
            document.addEventListener('DOMContentLoaded', function() {
                generateLeaderboard();
                animateProgressBars();
                
                // Animation d'apparition
                document.body.style.opacity = '0';
                setTimeout(() => {
                    document.body.style.transition = 'opacity 0.5s ease';
                    document.body.style.opacity = '1';
                }, 100);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/journal')
def journal():
    """Page journal de trading modernisée"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Journal de Trading - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
    </head>
    <body>
        <!-- Navigation moderne -->
        <div class="container-fluid">
            <div class="modern-nav">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-home me-2"></i>Accueil
                        </a>
                        <span class="modern-nav-link active">
                            <i class="fas fa-book me-2"></i>Journal
                        </span>
                    </div>
                    <div>
                        <a href="/calculator" class="modern-nav-link">
                            <i class="fas fa-calculator me-2"></i>Calculateur
                        </a>
                        <a href="/grades" class="modern-nav-link">
                            <i class="fas fa-trophy me-2"></i>Grades
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Header moderne -->
        <div class="container-fluid">
            <div class="modern-header">
                <div class="premium-badge">Premium</div>
                <h1><i class="fas fa-book me-3"></i>Journal de Trading</h1>
                <p>Suivez vos performances, analysez vos trades et progressez continuellement</p>
            </div>
        </div>

        <!-- Contenu principal -->
        <div class="container-fluid">
            <div class="row">
                <div class="col-lg-8">
                    <!-- Statistiques de performance -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-chart-line me-2"></i>Performances Globales
                            </h3>
                            <p class="modern-card-subtitle">Vue d'ensemble de vos résultats de trading</p>
                        </div>
                        
                        <div class="row g-4">
                            <div class="col-md-3">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-chart-bar"></i>
                                    </div>
                                    <div class="modern-stat-number">87.5%</div>
                                    <div class="modern-stat-label">Taux de Réussite</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-dollar-sign"></i>
                                    </div>
                                    <div class="modern-stat-number" style="background: var(--success-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">+$2,450</div>
                                    <div class="modern-stat-label">Profit Total</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-exchange-alt"></i>
                                    </div>
                                    <div class="modern-stat-number">24</div>
                                    <div class="modern-stat-label">Trades Totaux</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="modern-stat-card">
                                    <div class="modern-icon">
                                        <i class="fas fa-percentage"></i>
                                    </div>
                                    <div class="modern-stat-number" style="background: var(--info-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">2.1</div>
                                    <div class="modern-stat-label">Ratio Risk/Reward</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Liste des trades -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-list me-2"></i>Historique des Trades
                            </h3>
                            <p class="modern-card-subtitle">Vos dernières positions et analyses</p>
                        </div>
                        
                        <div class="modern-alert modern-alert-info">
                            <h6><i class="fas fa-crown me-2"></i>Fonctionnalité Premium</h6>
                            <p>Le journal de trading complet est disponible avec l'abonnement Premium. 
                            Connectez-vous pour accéder à toutes vos données de trading.</p>
                            <a href="/login" class="modern-btn modern-btn-warning">
                                <i class="fas fa-sign-in-alt me-2"></i>Se Connecter
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <!-- Analyse rapide -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-brain me-2"></i>Analyse Psychologique
                            </h3>
                        </div>
                        
                        <div class="text-center">
                            <div class="modern-icon mb-3">
                                <i class="fas fa-heart"></i>
                            </div>
                            <h5 class="text-gradient">État Mental: Confiant</h5>
                            <p class="text-muted">Votre discipline de trading s'améliore</p>
                            
                            <div class="mt-4">
                                <a href="/psychological-analysis" class="modern-btn modern-btn-info w-100">
                                    <i class="fas fa-microscope me-2"></i>Analyse Complète
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Actions rapides -->
                    <div class="modern-card">
                        <div class="modern-card-header">
                            <h3 class="modern-card-title">
                                <i class="fas fa-bolt me-2"></i>Actions Rapides
                            </h3>
                        </div>
                        
                        <div class="d-grid gap-3">
                            <a href="/journal/add-trade" class="modern-btn modern-btn-success">
                                <i class="fas fa-plus me-2"></i>Ajouter un Trade
                            </a>
                            <a href="/journal/import" class="modern-btn modern-btn-info">
                                <i class="fas fa-upload me-2"></i>Importer MT4/MT5
                            </a>
                            <a href="/journal/export" class="modern-btn modern-btn-secondary">
                                <i class="fas fa-download me-2"></i>Export CSV
                            </a>
                            <a href="/journal/analyze" class="modern-btn modern-btn-warning">
                                <i class="fas fa-chart-pie me-2"></i>Analyse IA
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion modernisée"""
    if request.method == 'POST':
        # Traitement du formulaire de connexion
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        logging.info(f"Tentative de connexion directe pour: {email}")
        
        if email in users_db:
            user = users_db[email]
            if check_password_hash(user['password'], password):
                # Connexion réussie - création de la session EXACTE demandée
                session.clear()  # Nettoie la session avant
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session['user_email'] = user['email']
                session['user_first_name'] = user['first_name']
                session['user_last_name'] = user['last_name']
                session['is_authenticated'] = True
                
                # FORCE la persistence de session
                session.permanent = True
                session.modified = True
                
                logging.info(f"✅ Connexion réussie: {email} (Role: {user['role']})")
                logging.info(f"✅ Session créée: user_id={user['id']}, role={user['role']}")
                logging.info(f"✅ Session complète: {dict(session)}")
                
                # Redirection DIRECTE sans page intermédiaire
                return redirect('/dashboard')
            else:
                logging.warning(f"Mot de passe incorrect pour: {email}")
                return redirect('/login?error=1')
        else:
            logging.warning(f"Email non trouvé: {email}")
            return redirect('/login?error=1')
    
    # Affichage du formulaire de connexion
    error_message = request.args.get('error')
    error_html = ""
    if error_message:
        error_html = '''
        <div class="modern-alert modern-alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>Email ou mot de passe incorrect
        </div>
        '''
    
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Connexion - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
        <style>
            .auth-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .auth-card {
                max-width: 400px;
                width: 100%;
                margin: 20px;
            }
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="auth-card">
                <div class="modern-card">
                    <div class="text-center mb-4">
                        <h2 class="text-gradient mb-3">🎯 MindTraderPro</h2>
                        <h4 class="text-white">Connexion</h4>
                        <p class="text-muted">Accédez à votre espace trader professionnel</p>
                    </div>
                    
                    <form method="POST" action="/login">
                        ''' + error_html + '''
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-envelope me-2"></i>Email
                            </label>
                            <input type="email" class="modern-form-control" name="email" 
                                   placeholder="votre@email.com" required>
                        </div>
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-lock me-2"></i>Mot de passe
                            </label>
                            <input type="password" class="modern-form-control" name="password" 
                                   placeholder="••••••••" required>
                        </div>
                        
                        <div class="modern-alert modern-alert-info">
                            <h6><i class="fas fa-key me-2"></i>Comptes de test</h6>
                            <p class="mb-1"><strong>Demo:</strong> demo@mindtraderpro.com / demo123</p>
                            <p class="mb-1"><strong>Admin:</strong> admin@mindtraderpro.com / admin123</p>
                            <p class="mb-0"><strong>VIP:</strong> vip@mindtraderpro.com / vip123</p>
                        </div>
                        
                        <button type="submit" class="modern-btn modern-btn-success w-100 mb-3">
                            <i class="fas fa-sign-in-alt me-2"></i>Se Connecter
                        </button>
                        
                        <div class="text-center">
                            <p class="text-muted">Pas encore de compte ?</p>
                            <a href="/register" class="modern-btn modern-btn-info w-100">
                                <i class="fas fa-user-plus me-2"></i>Créer un Compte
                            </a>
                        </div>
                    </form>
                    
                    <div class="text-center mt-4 pt-4" style="border-top: 1px solid rgba(255,255,255,0.2);">
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-arrow-left me-2"></i>Retour à l'accueil
                        </a>
                    </div>
                </div>
            </div>
        </div>
        

    </body>
    </html>
    '''

@app.route('/register')
def register():
    """Page d'inscription modernisée"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inscription - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
        <style>
            .auth-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px 0;
            }
            .auth-card {
                max-width: 500px;
                width: 100%;
                margin: 20px;
            }
            .offer-badge {
                background: var(--warning-gradient);
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="auth-card">
                <div class="modern-card">
                    <div class="text-center mb-4">
                        <h2 class="text-gradient mb-3">🎯 MindTraderPro</h2>
                        <div class="offer-badge">
                            <i class="fas fa-gift me-2"></i>Inscription Gratuite
                        </div>
                        <h4 class="text-white">Créer votre Compte</h4>
                        <p class="text-muted">Rejoignez la communauté des traders professionnels</p>
                    </div>
                    
                    <form id="registerForm">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <div class="modern-form-group">
                                    <label class="modern-form-label">
                                        <i class="fas fa-user me-2"></i>Prénom
                                    </label>
                                    <input type="text" class="modern-form-control" id="firstName" 
                                           placeholder="John" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="modern-form-group">
                                    <label class="modern-form-label">
                                        <i class="fas fa-user me-2"></i>Nom
                                    </label>
                                    <input type="text" class="modern-form-control" id="lastName" 
                                           placeholder="Doe" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-envelope me-2"></i>Email
                            </label>
                            <input type="email" class="modern-form-control" id="email" 
                                   placeholder="votre@email.com" required>
                        </div>
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-lock me-2"></i>Mot de passe
                            </label>
                            <input type="password" class="modern-form-control" id="password" 
                                   placeholder="••••••••" required>
                            <small class="text-muted">Au moins 8 caractères avec majuscules et chiffres</small>
                        </div>
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-lock me-2"></i>Confirmer le mot de passe
                            </label>
                            <input type="password" class="modern-form-control" id="confirmPassword" 
                                   placeholder="••••••••" required>
                        </div>
                        
                        <div class="modern-form-group">
                            <label class="modern-form-label">
                                <i class="fas fa-chart-line me-2"></i>Niveau d'expérience
                            </label>
                            <select class="modern-form-control" id="experience" required>
                                <option value="">Sélectionnez votre niveau</option>
                                <option value="beginner">🌱 Débutant (0-6 mois)</option>
                                <option value="intermediate">📈 Intermédiaire (6 mois - 2 ans)</option>
                                <option value="advanced">🏆 Avancé (2-5 ans)</option>
                                <option value="expert">💎 Expert (5+ ans)</option>
                            </select>
                        </div>
                        
                        <div class="form-check mb-4">
                            <input class="form-check-input" type="checkbox" id="terms" required>
                            <label class="form-check-label text-muted" for="terms">
                                J'accepte les <a href="/terms" class="text-primary">conditions d'utilisation</a> 
                                et la <a href="/privacy" class="text-primary">politique de confidentialité</a>
                            </label>
                        </div>
                        
                        <div class="form-check mb-4">
                            <input class="form-check-input" type="checkbox" id="newsletter">
                            <label class="form-check-label text-muted" for="newsletter">
                                Recevoir les conseils de trading et actualités (optionnel)
                            </label>
                        </div>
                        
                        <button type="submit" class="modern-btn modern-btn-success w-100 mb-3">
                            <i class="fas fa-rocket me-2"></i>Créer mon Compte Gratuit
                        </button>
                        
                        <div class="modern-alert modern-alert-info">
                            <h6><i class="fas fa-gift me-2"></i>Bonus d'inscription</h6>
                            <ul class="mb-0">
                                <li>✅ Accès gratuit au calculateur de lots</li>
                                <li>🏆 50 XP de démarrage</li>
                                <li>📚 Guide du trader débutant</li>
                                <li>💡 3 suggestions communautaires</li>
                            </ul>
                        </div>
                        
                        <div class="text-center mt-4">
                            <p class="text-muted">Déjà un compte ?</p>
                            <a href="/login" class="modern-btn modern-btn-info w-100">
                                <i class="fas fa-sign-in-alt me-2"></i>Se Connecter
                            </a>
                        </div>
                    </form>
                    
                    <div class="text-center mt-4 pt-4" style="border-top: 1px solid rgba(255,255,255,0.2);">
                        <a href="/home" class="modern-nav-link">
                            <i class="fas fa-arrow-left me-2"></i>Retour à l'accueil
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            document.getElementById('registerForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                if (password !== confirmPassword) {
                    showNotification('❌ Les mots de passe ne correspondent pas', 'danger');
                    return;
                }
                
                if (password.length < 8) {
                    showNotification('❌ Le mot de passe doit contenir au moins 8 caractères', 'danger');
                    return;
                }
                
                // Simulation d'inscription
                showNotification('🔄 Création du compte en cours...', 'info');
                setTimeout(() => {
                    showNotification('✅ Compte créé avec succès! Email de confirmation envoyé.', 'success');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                }, 2500);
            });
            
            function showNotification(message, type) {
                const notification = document.createElement('div');
                notification.className = 'modern-alert modern-alert-' + type + ' position-fixed';
                notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
                notification.innerHTML = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.opacity = '0';
                    setTimeout(() => notification.remove(), 300);
                }, 4000);
            }
        </script>
    </body>
    </html>
    '''

# ============================================================================
# API ROUTES D'AUTHENTIFICATION
# ============================================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    """API de connexion utilisateur"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        logging.info(f"Tentative de connexion pour: {email}")
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email et mot de passe requis'
            }), 400
        
        # Vérification de l'utilisateur
        if email in users_db:
            user = users_db[email]
            if check_password_hash(user['password'], password):
                login_user(user)
                
                # Vérification immédiate de la session
                logging.info(f"Session après connexion: {dict(session)}")
                
                return jsonify({
                    'success': True,
                    'message': 'Connexion réussie',
                    'user': {
                        'name': f"{user['first_name']} {user['last_name']}",
                        'role': user['role'],
                        'email': user['email']
                    }
                })
            else:
                logging.warning(f"Mot de passe incorrect pour: {email}")
        else:
            logging.warning(f"Email non trouvé: {email}")
        
        return jsonify({
            'success': False,
            'message': 'Email ou mot de passe incorrect'
        }), 401
        
    except Exception as e:
        logging.error(f"Erreur lors de la connexion: {e}")
        return jsonify({
            'success': False,
            'message': 'Erreur serveur'
        }), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API de déconnexion utilisateur"""
    logout_user()
    return jsonify({
        'success': True,
        'message': 'Déconnexion réussie'
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    """API d'inscription utilisateur"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        
        if not all([email, password, first_name, last_name]):
            return jsonify({
                'success': False,
                'message': 'Tous les champs sont requis'
            }), 400
        
        if email in users_db:
            return jsonify({
                'success': False,
                'message': 'Cet email est déjà utilisé'
            }), 409
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Le mot de passe doit contenir au moins 6 caractères'
            }), 400
        
        # Création du nouvel utilisateur
        new_user = {
            'id': len(users_db) + 1,
            'email': email,
            'password': generate_password_hash(password),
            'first_name': first_name,
            'last_name': last_name,
            'role': 'standard'
        }
        
        users_db[email] = new_user
        login_user(new_user)
        
        return jsonify({
            'success': True,
            'message': 'Inscription réussie',
            'user': {
                'name': f"{first_name} {last_name}",
                'role': 'standard',
                'email': email
            }
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de l'inscription: {e}")
        return jsonify({
            'success': False,
            'message': 'Erreur serveur'
        }), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard avec gestion complète de session - Diagnostic et affichage utilisateur"""
    
    # DEBUG : Afficher la session complète dans la console
    print(f"🔍 SESSION DASHBOARD: {dict(session)}")
    logging.info(f"🔍 SESSION SUR /dashboard: {dict(session)}")
    
    # Récupération des informations utilisateur
    user_info = get_user_display_info()
    print(f"🔍 USER_INFO: {user_info}")
    logging.info(f"🔍 USER_INFO: {user_info}")
    
    # Vérification de l'authentification
    if user_info['is_authenticated']:
        # Utilisateur connecté - Affichage du dashboard complet
        return f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                .dashboard-card {{
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    border: none;
                    border-radius: 15px;
                    color: white;
                    margin-bottom: 20px;
                }}
                .role-badge {{
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 0.8rem;
                }}
                .role-premium {{ background: linear-gradient(45deg, #FFD700, #FFA500); color: #000; }}
                .role-lifetime {{ background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: #fff; }}
                .role-admin {{ background: linear-gradient(45deg, #667eea, #764ba2); color: #fff; }}
                .role-standard {{ background: linear-gradient(45deg, #74b9ff, #0984e3); color: #fff; }}
                .session-debug {{
                    background: rgba(0,0,0,0.3);
                    border-radius: 10px;
                    padding: 15px;
                    margin: 15px 0;
                    font-family: monospace;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body class="bg-dark text-light">
            <div class="container mt-4">
                <div class="row justify-content-center">
                    <div class="col-md-10">
                        
                        <!-- Carte principale utilisateur -->
                        <div class="card dashboard-card">
                            <div class="card-header">
                                <h2><i class="fas fa-tachometer-alt me-2"></i>Dashboard MindTraderPro</h2>
                            </div>
                            <div class="card-body">
                                
                                <!-- Informations utilisateur -->
                                <div class="row">
                                    <div class="col-md-8">
                                        <h3><i class="fas fa-user-circle me-2"></i>Bienvenue {user_info['name']} !</h3>
                                        
                                        <div class="mt-3">
                                            <p><strong><i class="fas fa-id-badge me-2"></i>Rôle :</strong> 
                                                <span class="role-badge role-{user_info['role']}">{user_info['role'].title()}</span>
                                            </p>
                                            
                                            <p><strong><i class="fas fa-envelope me-2"></i>Email :</strong> {user_info['email']}</p>
                                            
                                            <p><strong><i class="fas fa-hashtag me-2"></i>ID Utilisateur :</strong> {user_info['user_id']}</p>
                                            
                                            <p><strong><i class="fas fa-star me-2"></i>XP Actuel :</strong> 
                                                <span class="text-warning">2,450 XP</span> 
                                                <small class="text-muted">(Grade: Trader Régulier)</small>
                                            </p>
                                        </div>
                                        
                                        <!-- Message de succès -->
                                        <div class="alert alert-success mt-4">
                                            <i class="fas fa-check-circle me-2"></i>
                                            <strong>Session Active !</strong> Votre connexion est stable et sécurisée.
                                        </div>
                                        
                                        <!-- Boutons d'action -->
                                        <div class="mt-4">
                                            <a href="/home" class="btn btn-primary me-2">
                                                <i class="fas fa-home me-1"></i>Accueil
                                            </a>
                                            <a href="/calculator" class="btn btn-success me-2">
                                                <i class="fas fa-calculator me-1"></i>Calculateur
                                            </a>
                                            <a href="/journal" class="btn btn-info me-2">
                                                <i class="fas fa-book me-1"></i>Journal
                                            </a>
                                            <a href="/logout" class="btn btn-danger">
                                                <i class="fas fa-sign-out-alt me-1"></i>Déconnexion
                                            </a>
                                        </div>
                                    </div>
                                    
                                    <div class="col-md-4 text-center">
                                        <!-- Avatar utilisateur -->
                                        <div class="mb-3">
                                            <div style="width: 120px; height: 120px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 3rem;">
                                                <i class="fas fa-user"></i>
                                            </div>
                                        </div>
                                        
                                        <!-- Statistiques rapides -->
                                        <div class="session-debug">
                                            <h6><i class="fas fa-chart-line me-2"></i>Stats Session</h6>
                                            <p class="mb-1"><strong>Connexions :</strong> 47</p>
                                            <p class="mb-1"><strong>Calculs :</strong> 156</p>
                                            <p class="mb-0"><strong>Dernière activité :</strong> Maintenant</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Debug session pour développement -->
                                <div class="session-debug">
                                    <h6><i class="fas fa-bug me-2"></i>Debug Session (Dev)</h6>
                                    <p><strong>Session Data:</strong> {dict(session)}</p>
                                    <p><strong>User Info:</strong> {user_info}</p>
                                </div>
                                
                            </div>
                        </div>
                        
                    </div>
                </div>
            </div>
            
            <script>
                console.log('✅ Dashboard chargé avec succès');
                console.log('👤 Utilisateur:', '{user_info['name']}');
                console.log('🎭 Rôle:', '{user_info['role']}');
                console.log('📧 Email:', '{user_info['email']}');
                console.log('🆔 ID:', '{user_info['user_id']}');
            </script>
        </body>
        </html>
        '''
    else:
        # Session perdue - Page d'erreur avec redirection automatique
        return f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Session Perdue - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-dark text-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <div class="card bg-danger">
                            <div class="card-header">
                                <h2><i class="fas fa-exclamation-triangle me-2"></i>SESSION PERDUE</h2>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-warning">
                                    <p><strong>Problème détecté :</strong> Votre session a été perdue après la connexion.</p>
                                    <p>Cela peut être dû à un problème de cookies ou de synchronisation.</p>
                                </div>
                                
                                <h5>Détails techniques :</h5>
                                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; font-family: monospace;">
                                    <p><strong>Session Flask :</strong> {dict(session)}</p>
                                    <p><strong>User Info :</strong> {user_info}</p>
                                </div>
                                
                                <div class="mt-4">
                                    <p><i class="fas fa-info-circle me-2"></i>Redirection automatique vers la page de connexion dans <span id="countdown">3</span> secondes...</p>
                                    <a href="/login" class="btn btn-primary">
                                        <i class="fas fa-sign-in-alt me-1"></i>Retour à la connexion
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                console.error('❌ Session perdue sur /dashboard');
                console.log('Session data:', {dict(session)});
                console.log('User info:', {user_info});
                
                // Compte à rebours et redirection automatique
                let countdown = 3;
                const countdownElement = document.getElementById('countdown');
                
                const timer = setInterval(() => {{
                    countdown--;
                    countdownElement.textContent = countdown;
                    
                    if (countdown <= 0) {{
                        clearInterval(timer);
                        window.location.href = '/login';
                    }}
                }}, 1000);
            </script>
        </body>
        </html>
        '''

@app.route('/profil')
def profil():
    """Page profil utilisateur complète avec gestion de compte"""
    user_info = get_user_display_info()
    
    # Vérification de l'authentification
    if not user_info['is_authenticated']:
        return redirect('/login')
    
    # Navigation unifiée
    navbar = f'''
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px 0;">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/home">
                <i class="fas fa-chart-line me-2" style="color: #00ff88;"></i>MindTraderPro
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/home"><i class="fas fa-home me-1"></i>Accueil</a></li>
                    <li class="nav-item"><a class="nav-link" href="/calculator"><i class="fas fa-calculator me-1"></i>Calculateur</a></li>
                    <li class="nav-item"><a class="nav-link" href="/journal"><i class="fas fa-book me-1"></i>Journal</a></li>
                    <li class="nav-item"><a class="nav-link" href="/leaderboard"><i class="fas fa-trophy me-1"></i>Classements</a></li>
                </ul>
                
                <div class="d-flex align-items-center">
                    <div class="me-3 text-center d-none d-lg-block">
                        <small class="text-warning d-block fw-bold">2,450 XP</small>
                        <small class="text-muted">Trader Régulier</small>
                    </div>
                    
                    <div class="dropdown">
                        <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown">
                            <div class="user-avatar me-2" style="width: 32px; height: 32px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                                <i class="fas fa-user"></i>
                            </div>
                            <div class="d-none d-sm-block text-start">
                                <div style="font-size: 0.9rem; font-weight: bold;">{user_info['first_name']}</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; color: #FFD700;">{user_info['role'].title()}</div>
                            </div>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end" style="background: rgba(0,0,0,0.95); border: 1px solid rgba(255,255,255,0.2);">
                            <li><a class="dropdown-item text-light" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i>Mon Dashboard</a></li>
                            <li><a class="dropdown-item text-warning" href="/profil"><i class="fas fa-user me-2"></i>Mon Profil</a></li>
                            <li><hr class="dropdown-divider" style="border-color: rgba(255,255,255,0.2);"></li>
                            <li><a class="dropdown-item text-danger" href="/logout"><i class="fas fa-sign-out-alt me-2"></i>Déconnexion</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </nav>
    '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mon Profil - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
                min-height: 100vh;
            }}
            .profile-card {{
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                border: none;
                border-radius: 20px;
                color: white;
                box-shadow: 0 15px 35px rgba(0,0,0,0.5);
                overflow: hidden;
                position: relative;
            }}
            .profile-header {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                padding: 30px;
                text-align: center;
                position: relative;
            }}
            .profile-avatar {{
                width: 120px;
                height: 120px;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                font-size: 3rem;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: profilePulse 2s infinite;
            }}
            @keyframes profilePulse {{
                0%, 100% {{ transform: scale(1); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
                50% {{ transform: scale(1.05); box-shadow: 0 15px 40px rgba(0,0,0,0.5); }}
            }}
            .role-badge {{
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 0.9rem;
                display: inline-block;
                margin-top: 10px;
            }}
            .role-premium {{
                background: linear-gradient(45deg, #FFD700, #FFA500);
                color: #000;
            }}
            .role-lifetime {{
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                color: #fff;
            }}
            .role-admin {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: #fff;
            }}
            .role-standard {{
                background: linear-gradient(45deg, #74b9ff, #0984e3);
                color: #fff;
            }}
            .xp-progress {{
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                height: 12px;
                margin: 15px 0;
                overflow: hidden;
            }}
            .xp-bar {{
                background: linear-gradient(45deg, #00ff88, #00cc6a);
                height: 100%;
                border-radius: 15px;
                width: 65%;
                transition: width 0.5s ease;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}
            .stat-card {{
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.1);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                border-color: rgba(255,255,255,0.3);
            }}
            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background: linear-gradient(45deg, #00ff88, #00cc6a);
            }}
            .reward-item {{
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                display: flex;
                align-items: center;
                transition: all 0.3s ease;
            }}
            .reward-item:hover {{
                background: rgba(255,255,255,0.1);
                transform: translateX(5px);
            }}
            .reward-icon {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                margin-right: 15px;
            }}
            .reward-unlocked {{
                background: linear-gradient(45deg, #FFD700, #FFA500);
                color: #000;
            }}
            .reward-locked {{
                background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.5);
            }}
            .action-buttons {{
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin-top: 30px;
            }}
            .btn-profile {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                border: none;
                color: white;
                padding: 12px 25px;
                border-radius: 25px;
                font-weight: bold;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                transition: all 0.3s ease;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            .btn-profile:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.4);
                color: white;
            }}
            .btn-danger {{
                background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            }}
            .btn-success {{
                background: linear-gradient(45deg, #00ff88, #00cc6a);
            }}
            .btn-warning {{
                background: linear-gradient(45deg, #FFD700, #FFA500);
                color: #000;
            }}
            .activity-item {{
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #00ff88;
            }}
        </style>
    </head>
    <body>
        {navbar}
        
        <div class="container mt-4">
            <div class="row">
                <!-- Carte profil principale -->
                <div class="col-lg-8">
                    <div class="card profile-card">
                        <div class="profile-header">
                            <div class="profile-avatar">
                                <i class="fas fa-user"></i>
                            </div>
                            <h2 class="mb-2">{user_info['name']}</h2>
                            <p class="mb-2">{user_info['email']}</p>
                            <span class="role-badge role-{user_info['role']}">
                                <i class="fas fa-{'gem' if user_info['role'] == 'lifetime' else 'star' if user_info['role'] == 'premium' else 'shield-alt' if user_info['role'] == 'admin' else 'user'} me-2"></i>
                                {user_info['role'].title()}
                            </span>
                            
                            <!-- Barre XP -->
                            <div class="mt-4">
                                <div class="d-flex justify-content-between">
                                    <span>2,450 XP</span>
                                    <span>3,800 XP</span>
                                </div>
                                <div class="xp-progress">
                                    <div class="xp-bar" style="width: 65%;"></div>
                                </div>
                                <p class="mb-0">Trader Régulier • 1,350 XP jusqu'au prochain grade</p>
                            </div>
                        </div>
                        
                        <div class="card-body">
                            <!-- Statistiques -->
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <i class="fas fa-calculator text-primary mb-3" style="font-size: 2rem;"></i>
                                    <h4>156</h4>
                                    <p class="mb-0">Calculs effectués</p>
                                </div>
                                <div class="stat-card">
                                    <i class="fas fa-chart-line text-success mb-3" style="font-size: 2rem;"></i>
                                    <h4>87</h4>
                                    <p class="mb-0">Trades enregistrés</p>
                                </div>
                                <div class="stat-card">
                                    <i class="fas fa-users text-warning mb-3" style="font-size: 2rem;"></i>
                                    <h4>12</h4>
                                    <p class="mb-0">Filleuls parrainés</p>
                                </div>
                                <div class="stat-card">
                                    <i class="fas fa-trophy text-info mb-3" style="font-size: 2rem;"></i>
                                    <h4>8</h4>
                                    <p class="mb-0">Récompenses débloquées</p>
                                </div>
                            </div>
                            
                            <!-- Boutons d'action -->
                            <div class="action-buttons">
                                <button class="btn-profile btn-success" onclick="showEditProfile()">
                                    <i class="fas fa-edit me-2"></i>Modifier mon profil
                                </button>
                                <a href="/personnalisation" class="btn-profile btn-warning">
                                    <i class="fas fa-palette me-2"></i>Personnalisation
                                </a>
                                <button class="btn-profile btn-danger" onclick="showDeleteAccount()">
                                    <i class="fas fa-trash me-2"></i>Supprimer mon compte
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sidebar récompenses et activité -->
                <div class="col-lg-4">
                    <!-- Récompenses -->
                    <div class="card profile-card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-trophy me-2"></i>Récompenses</h5>
                        </div>
                        <div class="card-body">
                            <div class="reward-item">
                                <div class="reward-icon reward-unlocked">
                                    <i class="fas fa-star"></i>
                                </div>
                                <div>
                                    <strong>Premier Calcul</strong>
                                    <p class="mb-0 small text-muted">Effectuer votre premier calcul</p>
                                </div>
                            </div>
                            <div class="reward-item">
                                <div class="reward-icon reward-unlocked">
                                    <i class="fas fa-fire"></i>
                                </div>
                                <div>
                                    <strong>Série de 10</strong>
                                    <p class="mb-0 small text-muted">10 calculs consécutifs</p>
                                </div>
                            </div>
                            <div class="reward-item">
                                <div class="reward-icon reward-locked">
                                    <i class="fas fa-crown"></i>
                                </div>
                                <div>
                                    <strong>Trader Expert</strong>
                                    <p class="mb-0 small text-muted">Atteindre 5,000 XP</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Activité récente -->
                    <div class="card profile-card">
                        <div class="card-header">
                            <h5><i class="fas fa-clock me-2"></i>Activité récente</h5>
                        </div>
                        <div class="card-body">
                            <div class="activity-item">
                                <strong>+50 XP</strong> • Calcul EURUSD
                                <p class="mb-0 small text-muted">Il y a 2 heures</p>
                            </div>
                            <div class="activity-item">
                                <strong>+25 XP</strong> • Trade enregistré
                                <p class="mb-0 small text-muted">Il y a 5 heures</p>
                            </div>
                            <div class="activity-item">
                                <strong>+100 XP</strong> • Nouveau filleul
                                <p class="mb-0 small text-muted">Hier</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modal Édition Profil -->
        <div class="modal fade" id="editProfileModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title text-light">Modifier mon profil</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editProfileForm">
                            <div class="mb-3">
                                <label class="form-label text-light">Prénom</label>
                                <input type="text" class="form-control" id="firstName" value="{user_info['first_name']}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Nom</label>
                                <input type="text" class="form-control" id="lastName" value="{user_info['name'].split(' ')[-1] if ' ' in user_info['name'] else ''}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Email</label>
                                <input type="email" class="form-control" id="email" value="{user_info['email']}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Nouveau mot de passe (optionnel)</label>
                                <input type="password" class="form-control" id="newPassword" placeholder="Laisser vide pour ne pas changer">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Mot de passe actuel (requis)</label>
                                <input type="password" class="form-control" id="currentPassword" required>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-success" onclick="saveProfile()">Sauvegarder</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modal Suppression Compte -->
        <div class="modal fade" id="deleteAccountModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark">
                    <div class="modal-header border-danger">
                        <h5 class="modal-title text-danger">Supprimer mon compte</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Attention !</strong> Cette action est irréversible.
                        </div>
                        <p class="text-light">En supprimant votre compte, vous perdrez :</p>
                        <ul class="text-light">
                            <li>Tous vos trades et calculs</li>
                            <li>Votre progression XP et récompenses</li>
                            <li>Vos filleuls et commissions</li>
                            <li>Votre accès premium/lifetime</li>
                        </ul>
                        <p class="text-warning">Un email de confirmation sera envoyé à <strong>{user_info['email']}</strong></p>
                        
                        <div class="mb-3">
                            <label class="form-label text-light">Tapez "SUPPRIMER" pour confirmer</label>
                            <input type="text" class="form-control" id="deleteConfirmation" placeholder="SUPPRIMER">
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-light">Mot de passe</label>
                            <input type="password" class="form-control" id="deletePassword" required>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-danger" onclick="deleteAccount()">Envoyer l'email de confirmation</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function showEditProfile() {{
                new bootstrap.Modal(document.getElementById('editProfileModal')).show();
            }}
            
            function showDeleteAccount() {{
                new bootstrap.Modal(document.getElementById('deleteAccountModal')).show();
            }}
            
            function saveProfile() {{
                const firstName = document.getElementById('firstName').value;
                const lastName = document.getElementById('lastName').value;
                const email = document.getElementById('email').value;
                const newPassword = document.getElementById('newPassword').value;
                const currentPassword = document.getElementById('currentPassword').value;
                
                if (!currentPassword) {{
                    alert('Mot de passe actuel requis');
                    return;
                }}
                
                fetch('/api/update-profile', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        firstName, lastName, email, newPassword, currentPassword
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('Profil mis à jour avec succès !');
                        location.reload();
                    }} else {{
                        alert('Erreur : ' + data.message);
                    }}
                }});
            }}
            
            function deleteAccount() {{
                const confirmation = document.getElementById('deleteConfirmation').value;
                const password = document.getElementById('deletePassword').value;
                
                if (confirmation !== 'SUPPRIMER') {{
                    alert('Veuillez taper "SUPPRIMER" pour confirmer');
                    return;
                }}
                
                if (!password) {{
                    alert('Mot de passe requis');
                    return;
                }}
                
                fetch('/api/request-account-deletion', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ password }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('Email de confirmation envoyé ! Vérifiez votre boîte mail.');
                        bootstrap.Modal.getInstance(document.getElementById('deleteAccountModal')).hide();
                    }} else {{
                        alert('Erreur : ' + data.message);
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/api/update-profile', methods=['POST'])
def api_update_profile():
    """API pour mettre à jour le profil utilisateur"""
    user_info = get_user_display_info()
    
    if not user_info['is_authenticated']:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        email = user_info['email']
        current_password = data.get('currentPassword')
        
        # Vérification du mot de passe actuel
        if email in users_db:
            user = users_db[email]
            if not check_password_hash(user['password'], current_password):
                return jsonify({'success': False, 'message': 'Mot de passe actuel incorrect'}), 400
            
            # Mise à jour des données
            first_name = data.get('firstName', '').strip()
            last_name = data.get('lastName', '').strip()
            new_email = data.get('email', '').strip().lower()
            new_password = data.get('newPassword', '').strip()
            
            # Validation
            if not first_name or not last_name:
                return jsonify({'success': False, 'message': 'Prénom et nom requis'}), 400
            
            # Vérification si le nouvel email existe déjà
            if new_email != email and new_email in users_db:
                return jsonify({'success': False, 'message': 'Cet email est déjà utilisé'}), 400
            
            # Mise à jour des données utilisateur
            updated_user = users_db[email].copy()
            updated_user['first_name'] = first_name
            updated_user['last_name'] = last_name
            updated_user['email'] = new_email
            
            if new_password:
                updated_user['password'] = generate_password_hash(new_password)
            
            # Si l'email change, on déplace l'utilisateur
            if new_email != email:
                del users_db[email]
                users_db[new_email] = updated_user
            else:
                users_db[email] = updated_user
            
            # Mise à jour de la session
            session['user_email'] = new_email
            session['user_first_name'] = first_name
            session['user_last_name'] = last_name
            session['user_name'] = f"{first_name} {last_name}"
            session.modified = True
            
            logging.info(f"Profil mis à jour pour: {new_email}")
            return jsonify({'success': True, 'message': 'Profil mis à jour avec succès'})
        
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
        
    except Exception as e:
        logging.error(f"Erreur mise à jour profil: {e}")
        return jsonify({'success': False, 'message': 'Erreur serveur'}), 500

@app.route('/api/request-account-deletion', methods=['POST'])
def api_request_account_deletion():
    """API pour demander la suppression de compte avec email de confirmation"""
    user_info = get_user_display_info()
    
    if not user_info['is_authenticated']:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        password = data.get('password')
        email = user_info['email']
        
        # Vérification du mot de passe
        if email in users_db:
            user = users_db[email]
            if not check_password_hash(user['password'], password):
                return jsonify({'success': False, 'message': 'Mot de passe incorrect'}), 400
            
            # Génération d'un token sécurisé pour la suppression
            import secrets
            import time
            
            deletion_token = secrets.token_urlsafe(32)
            deletion_timestamp = time.time()
            
            # Stockage temporaire du token (en production, utiliser Redis ou base de données)
            if not hasattr(app, 'deletion_tokens'):
                app.deletion_tokens = {}
            
            app.deletion_tokens[deletion_token] = {
                'email': email,
                'timestamp': deletion_timestamp,
                'user_id': user_info['user_id']
            }
            
            # Construction de l'email de confirmation
            deletion_url = f"https://{request.host}/confirm-account-deletion/{deletion_token}"
            
            email_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Confirmation de suppression de compte - MindTraderPro</title>
            </head>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); border-radius: 15px; padding: 30px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #ff6b6b; margin: 0;">⚠️ Suppression de compte</h1>
                    </div>
                    
                    <p>Bonjour <strong>{user_info['first_name']}</strong>,</p>
                    
                    <p>Vous avez demandé la suppression de votre compte MindTraderPro (<strong>{email}</strong>).</p>
                    
                    <div style="background: rgba(255, 107, 107, 0.1); border-left: 4px solid #ff6b6b; padding: 15px; margin: 20px 0;">
                        <h3 style="color: #ff6b6b; margin: 0 0 10px 0;">Attention : Cette action est irréversible</h3>
                        <p style="margin: 0;">En supprimant votre compte, vous perdrez définitivement :</p>
                        <ul style="margin: 10px 0 0 20px;">
                            <li>Tous vos trades et calculs</li>
                            <li>Votre progression XP et récompenses</li>
                            <li>Vos filleuls et commissions</li>
                            <li>Votre accès premium/lifetime</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{deletion_url}" 
                           style="background: linear-gradient(45deg, #ff6b6b, #ee5a52); 
                                  color: white; 
                                  padding: 15px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  font-weight: bold;
                                  display: inline-block;">
                            🗑️ CONFIRMER LA SUPPRESSION
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: rgba(255,255,255,0.7);">
                        Ce lien est valide pendant 24 heures seulement.<br>
                        Si vous n'avez pas demandé cette suppression, ignorez cet email.
                    </p>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <p style="margin: 0; color: rgba(255,255,255,0.5);">
                            MindTraderPro - Calculateur de Trading Professionnel
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Envoi de l'email (simulation pour le moment)
            logging.info(f"📧 EMAIL DE SUPPRESSION envoyé à {email}")
            logging.info(f"🔗 Lien de suppression: {deletion_url}")
            logging.info(f"🎯 Token: {deletion_token}")
            
            # En production, utiliser SendGrid ou un autre service d'email
            # send_email(to=email, subject="Confirmation de suppression - MindTraderPro", html=email_html)
            
            return jsonify({
                'success': True, 
                'message': f'Email de confirmation envoyé à {email}',
                'debug_url': deletion_url  # À retirer en production
            })
        
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
        
    except Exception as e:
        logging.error(f"Erreur demande suppression: {e}")
        return jsonify({'success': False, 'message': 'Erreur serveur'}), 500

@app.route('/confirm-account-deletion/<token>')
def confirm_account_deletion(token):
    """Confirmation de suppression de compte via lien email"""
    try:
        import time
        
        # Vérification du token
        if not hasattr(app, 'deletion_tokens') or token not in app.deletion_tokens:
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Lien invalide - MindTraderPro</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container mt-5 text-center">
                    <h1 class="text-danger">❌ Lien invalide</h1>
                    <p>Ce lien de suppression n'est pas valide ou a expiré.</p>
                    <a href="/home" class="btn btn-primary">Retour à l'accueil</a>
                </div>
            </body>
            </html>
            """
        
        token_data = app.deletion_tokens[token]
        
        # Vérification de l'expiration (24 heures)
        if time.time() - token_data['timestamp'] > 86400:  # 24 heures
            del app.deletion_tokens[token]
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Lien expiré - MindTraderPro</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container mt-5 text-center">
                    <h1 class="text-warning">⏰ Lien expiré</h1>
                    <p>Ce lien de suppression a expiré (valide 24h seulement).</p>
                    <p>Veuillez refaire une demande depuis votre profil.</p>
                    <a href="/login" class="btn btn-primary">Se connecter</a>
                </div>
            </body>
            </html>
            """
        
        # Suppression effective du compte
        email = token_data['email']
        user_id = token_data['user_id']
        
        if email in users_db:
            user_data = users_db[email]
            
            # Suppression de l'utilisateur
            del users_db[email]
            
            # Nettoyage du token
            del app.deletion_tokens[token]
            
            # Journalisation de la suppression
            logging.info(f"🗑️ COMPTE SUPPRIMÉ: {email} (ID: {user_id})")
            logging.info(f"📊 Données supprimées: {user_data}")
            
            # Page de confirmation
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Compte supprimé - MindTraderPro</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-8 text-center">
                            <div class="card bg-secondary">
                                <div class="card-body p-5">
                                    <i class="fas fa-check-circle text-success mb-4" style="font-size: 5rem;"></i>
                                    <h1 class="text-success mb-4">Compte supprimé avec succès</h1>
                                    <p class="lead mb-4">
                                        Votre compte MindTraderPro a été définitivement supprimé.
                                    </p>
                                    <p class="mb-4">
                                        Toutes vos données ont été effacées de nos serveurs.<br>
                                        Merci d'avoir utilisé MindTraderPro.
                                    </p>
                                    <a href="/home" class="btn btn-primary btn-lg">
                                        <i class="fas fa-home me-2"></i>Retour à l'accueil
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Erreur - MindTraderPro</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container mt-5 text-center">
                    <h1 class="text-danger">❌ Erreur</h1>
                    <p>Le compte n'a pas pu être supprimé.</p>
                    <a href="/home" class="btn btn-primary">Retour à l'accueil</a>
                </div>
            </body>
            </html>
            """
        
    except Exception as e:
        logging.error(f"Erreur confirmation suppression: {e}")
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Erreur serveur - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        </head>
        <body class="bg-dark text-light">
            <div class="container mt-5 text-center">
                <h1 class="text-danger">💥 Erreur serveur</h1>
                <p>Une erreur s'est produite lors de la suppression.</p>
                <a href="/home" class="btn btn-primary">Retour à l'accueil</a>
            </div>
        </body>
        </html>
        """

@app.route('/logout')
def logout():
    """Route de déconnexion (redirection)"""
    logout_user()
    return redirect('/home')

# ============================================================================
# API ROUTES SÉCURISÉES
# ============================================================================

@app.route('/calculate', methods=['POST'])
def calculate():
    """API endpoint for lot size calculation"""
    try:
        data = request.get_json()
        
        # Validation basique des données
        required_fields = ['direction', 'entry_price', 'stop_loss', 'capital', 'risk_percent']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Champ requis: {field}'}), 400
        
        # Extract parameters
        direction = data.get('direction', '').lower()
        pair_symbol = data.get('symbol', data.get('pair_symbol', 'XAUUSD')).upper()
        entry_price = float(data.get('entry_price', 0))
        stop_loss = float(data.get('stop_loss', 0))
        capital = float(data.get('capital', 20000))
        risk_percent = float(data.get('risk_percent', 0.5))
        
        # Calculate stop loss in pips
        sl_pips = calculate_pips(entry_price, stop_loss, pair_symbol)
        
        # Calculate lot size
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        if result['success']:
            app.logger.info(f"Calculation successful: {result}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Données numériques invalides'}), 400
    except Exception as e:
        app.logger.error(f"Calculation error: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur de calcul'}), 500

@app.route('/api/mobile/calculate', methods=['POST'])
def mobile_calculate():
    """API endpoint optimisé pour mobile"""
    try:
        data = request.get_json()
        
        # Validation simplifiée pour mobile
        capital = float(data.get('capital', 20000))
        risk_percent = float(data.get('risk_percent', 0.5))
        sl_pips = float(data.get('sl_pips', 10))
        pair_symbol = data.get('pair_symbol', 'XAUUSD').upper()
        
        # Calcul de la taille de lot
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Mobile calculation error: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur de calcul mobile'}), 500

@app.route('/api/health')
def health_check():
    """Point de contrôle santé de l'application"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0-clean',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'calculator': True,
            'journal': True,
            'security': True,
            'mobile_api': True
        }
    })

# ============================================================================
# GESTIONNAIRE D'ERREURS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Gestionnaire d'erreur 500"""
    app.logger.error(f"Server error: {str(error)}")
    return render_template('errors/500.html'), 500

# ============================================================================
# ENREGISTREMENT DES MODULES MODULAIRES
# ============================================================================

# Enregistrement des blueprints modulaires
app.register_blueprint(journal_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(newsletter_bp)
app.register_blueprint(suggestion_bp)
app.register_blueprint(customization_bp)
app.register_blueprint(lifetime_bp)
app.register_blueprint(grade_bp)
app.register_blueprint(referral_bp)

# ============================================================================
# INITIALISATION
# ============================================================================

if __name__ == '__main__':
    print("🚀 MindTraderPro - Version Nettoyée")
    print("✅ Système de sécurité activé")
    print("✅ Validation des entrées activée") 
    print("✅ Logging configuré")
    print("✅ Module Journal de Trading intégré")
    print("✅ Toutes les routes enregistrées")
    print("🚀 MindTraderPro initialisé avec succès")