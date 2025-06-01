"""
MindTraderPro - Application avec système d'authentification complet
Système sécurisé avec gestion des rôles et permissions
"""

import os
import sqlite3
import bcrypt
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, flash
from functools import wraps

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = "mindtraderpro-auth-secure-key-2024"

# Configuration de la base de données SQLite
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# GESTION DE LA BASE DE DONNÉES UTILISATEURS
# ============================================================================

def init_database():
    """Initialise la base de données SQLite pour les utilisateurs"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Création de la table utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'standard',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            calculations_used INTEGER DEFAULT 0
        )
    ''')
    
    # Création de la table des calculs pour le suivi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pair_symbol TEXT,
            lot_size REAL,
            risk_usd REAL,
            capital REAL,
            risk_percent REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ============================================================================
    # NOUVELLE TABLE: JOURNAL DE TRADING
    # ============================================================================
    
    # Création de la table des trades pour le journal de trading
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trading_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset TEXT NOT NULL,
            trade_type TEXT NOT NULL CHECK (trade_type IN ('buy', 'sell')),
            trade_date DATETIME NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            exit_price REAL,
            lot_size REAL NOT NULL,
            result_pnl REAL DEFAULT 0,
            result_pips REAL DEFAULT 0,
            trading_style TEXT CHECK (trading_style IN ('scalping', 'day_trading', 'swing', 'position')),
            emotions TEXT CHECK (emotions IN ('confident', 'nervous', 'greedy', 'fearful', 'calm', 'frustrated', 'excited')),
            notes TEXT,
            audio_note_path TEXT,
            status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec le module Journal de Trading")

def create_user(email, username, password, role='standard'):
    """Crée un nouvel utilisateur avec mot de passe hashé"""
    try:
        # Hachage sécurisé du mot de passe avec bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (email, username, password_hash, role))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {'success': True, 'user_id': user_id, 'message': 'Utilisateur créé avec succès'}
    
    except sqlite3.IntegrityError as e:
        if 'email' in str(e):
            return {'success': False, 'error': 'Cet email est déjà utilisé'}
        elif 'username' in str(e):
            return {'success': False, 'error': 'Ce nom d\'utilisateur est déjà pris'}
        else:
            return {'success': False, 'error': 'Erreur lors de la création du compte'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def authenticate_user(email, password):
    """Authentifie un utilisateur et retourne ses informations"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, username, password_hash, role, calculations_used
            FROM users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            # Mise à jour de la dernière connexion
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user[0],))
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'username': user[2],
                    'role': user[4],
                    'calculations_used': user[5]
                }
            }
        else:
            conn.close()
            return {'success': False, 'error': 'Email ou mot de passe incorrect'}
            
    except Exception as e:
        return {'success': False, 'error': f'Erreur de connexion: {str(e)}'}

def get_user_by_id(user_id):
    """Récupère un utilisateur par son ID"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, username, role, calculations_used
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'role': user[3],
                'calculations_used': user[4]
            }
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur: {e}")
        return None

def update_user_calculations(user_id):
    """Incrémente le compteur de calculs d'un utilisateur"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET calculations_used = calculations_used + 1 WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour des calculs: {e}")
        return False

def save_calculation(user_id, pair_symbol, lot_size, risk_usd, capital, risk_percent):
    """Sauvegarde un calcul dans l'historique"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO calculations (user_id, pair_symbol, lot_size, risk_usd, capital, risk_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, pair_symbol, lot_size, risk_usd, capital, risk_percent))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du calcul: {e}")
        return False

# ============================================================================
# FONCTIONS DE GESTION DU JOURNAL DE TRADING
# ============================================================================

def add_trade_to_journal(user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit, 
                        lot_size, trading_style, emotions, notes, audio_note_path=None):
    """
    Ajoute un nouveau trade au journal de trading
    
    Args:
        user_id (int): ID de l'utilisateur
        asset (str): Actif tradé (ex: EURUSD, XAUUSD)
        trade_type (str): Type de trade ('buy' ou 'sell')
        trade_date (str): Date et heure du trade
        entry_price (float): Prix d'entrée
        stop_loss (float): Stop loss
        take_profit (float): Take profit
        lot_size (float): Taille de la position
        trading_style (str): Style de trading (scalping, day_trading, swing, position)
        emotions (str): État émotionnel (confident, nervous, greedy, fearful, calm, frustrated, excited)
        notes (str): Notes textuelles
        audio_note_path (str): Chemin vers la note audio (optionnel)
    
    Returns:
        dict: Résultat de l'ajout avec succès/erreur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trading_journal (
                user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
                lot_size, trading_style, emotions, notes, audio_note_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        ''', (user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
              lot_size, trading_style, emotions, notes, audio_note_path))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'trade_id': trade_id, 'message': 'Trade ajouté avec succès'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'ajout du trade: {str(e)}'}

def update_trade_result(trade_id, user_id, exit_price, result_pnl, result_pips):
    """
    Met à jour les résultats d'un trade (quand il est clôturé)
    
    Args:
        trade_id (int): ID du trade
        user_id (int): ID de l'utilisateur (pour vérification)
        exit_price (float): Prix de sortie
        result_pnl (float): Résultat en devise
        result_pips (float): Résultat en pips
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trading_journal 
            SET exit_price = ?, result_pnl = ?, result_pips = ?, status = 'closed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (exit_price, result_pnl, result_pips, trade_id, user_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Trade mis à jour avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Trade non trouvé ou accès non autorisé'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def get_user_trades(user_id, limit=50, offset=0):
    """
    Récupère la liste des trades d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        limit (int): Nombre maximum de trades à récupérer
        offset (int): Décalage pour la pagination
    
    Returns:
        list: Liste des trades de l'utilisateur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
                   exit_price, lot_size, result_pnl, result_pips, trading_style, emotions,
                   notes, audio_note_path, status, created_at
            FROM trading_journal 
            WHERE user_id = ?
            ORDER BY trade_date DESC, created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        trades = cursor.fetchall()
        conn.close()
        
        # Conversion en dictionnaire pour faciliter l'utilisation
        trades_list = []
        for trade in trades:
            trades_list.append({
                'id': trade[0],
                'asset': trade[1],
                'trade_type': trade[2],
                'trade_date': trade[3],
                'entry_price': trade[4],
                'stop_loss': trade[5],
                'take_profit': trade[6],
                'exit_price': trade[7],
                'lot_size': trade[8],
                'result_pnl': trade[9],
                'result_pips': trade[10],
                'trading_style': trade[11],
                'emotions': trade[12],
                'notes': trade[13],
                'audio_note_path': trade[14],
                'status': trade[15],
                'created_at': trade[16]
            })
        
        return trades_list
    except Exception as e:
        print(f"Erreur lors de la récupération des trades: {e}")
        return []

def get_trading_statistics(user_id):
    """
    Calcule les statistiques de trading pour un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Statistiques de trading (winrate, R moyen, drawdown, etc.)
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération de tous les trades fermés
        cursor.execute('''
            SELECT result_pnl, result_pips, asset, trading_style
            FROM trading_journal 
            WHERE user_id = ? AND status = 'closed' AND result_pnl IS NOT NULL
            ORDER BY trade_date ASC
        ''', (user_id,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'winrate': 0,
                'total_pnl': 0,
                'average_win': 0,
                'average_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'assets_traded': [],
                'styles_distribution': {}
            }
        
        # Calculs statistiques
        total_trades = len(trades)
        pnl_values = [trade[0] for trade in trades]
        
        winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
        losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
        
        winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(pnl_values)
        
        wins = [pnl for pnl in pnl_values if pnl > 0]
        losses = [pnl for pnl in pnl_values if pnl < 0]
        
        average_win = (sum(wins) / len(wins)) if wins else 0
        average_loss = (sum(losses) / len(losses)) if losses else 0
        
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Calcul du drawdown maximum
        running_total = 0
        peak = 0
        max_drawdown = 0
        
        for pnl in pnl_values:
            running_total += pnl
            if running_total > peak:
                peak = running_total
            drawdown = peak - running_total
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Meilleur et pire trade
        best_trade = max(pnl_values) if pnl_values else 0
        worst_trade = min(pnl_values) if pnl_values else 0
        
        # Actifs tradés et styles
        assets_traded = list(set([trade[2] for trade in trades]))
        styles = [trade[3] for trade in trades if trade[3]]
        styles_distribution = {}
        for style in set(styles):
            styles_distribution[style] = styles.count(style)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'winrate': round(winrate, 2),
            'total_pnl': round(total_pnl, 2),
            'average_win': round(average_win, 2),
            'average_loss': round(average_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'assets_traded': assets_traded,
            'styles_distribution': styles_distribution
        }
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

# ============================================================================
# DECORATEURS D'AUTHENTIFICATION ET PERMISSIONS
# ============================================================================

def login_required(f):
    """Décorateur pour les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté pour accéder à cette page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles):
    """Décorateur pour vérifier les rôles utilisateur"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Connexion requise', 'warning')
                return redirect(url_for('login'))
            
            user = get_user_by_id(session['user_id'])
            if not user or user['role'] not in required_roles:
                flash('Accès non autorisé - Upgrade requis', 'error')
                return redirect(url_for('pricing'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_calculation_limit(user):
    """Vérifie si l'utilisateur peut effectuer un calcul"""
    if user['role'] == 'standard' and user['calculations_used'] >= 3:
        return False
    return True

# ============================================================================
# FONCTIONS DE CALCUL DE TRADING (INCHANGÉES)
# ============================================================================

def get_pip_info(pair_symbol):
    """Get pip size and pip value for a currency pair"""
    pip_configs = {
        'XAUUSD': {'pip_size': 0.1, 'pip_value': 10.0},
        'EURUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'GBPUSD': {'pip_size': 0.0001, 'pip_value': 10.0},
        'USDJPY': {'pip_size': 0.01, 'pip_value': 10.0},
    }
    return pip_configs.get(pair_symbol.upper(), {'pip_size': 0.0001, 'pip_value': 10.0})

def calculate_pips(entry_price, exit_price, pair_symbol):
    """Calculate pips between two prices"""
    pip_info = get_pip_info(pair_symbol)
    price_difference = abs(exit_price - entry_price)
    pips = price_difference / pip_info['pip_size']
    return round(pips, 1)

def calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol):
    """Calculate recommended lot size"""
    try:
        if sl_pips <= 0 or capital <= 0 or risk_percent <= 0:
            return {'success': False, 'error': 'Paramètres invalides'}
        
        # Limite de sécurité
        if risk_percent > 10:
            risk_percent = 10
            
        risk_usd = capital * (risk_percent / 100)
        pip_info = get_pip_info(pair_symbol)
        lot_size = risk_usd / (sl_pips * pip_info['pip_value'])
        lot_size = min(lot_size, 10.0)  # Max 10 lots
        
        return {
            'success': True,
            'lot_size': round(lot_size, 2),
            'risk_usd': round(risk_usd, 2),
            'sl_pips': sl_pips,
            'capital': capital,
            'risk_percent': risk_percent,
            'pip_value': pip_info['pip_value']
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ============================================================================
# TEMPLATE DE BASE AVEC NAVIGATION DYNAMIQUE
# ============================================================================

def get_base_template(page_title, active_page="home"):
    """Template de base avec navigation qui s'adapte selon l'authentification"""
    
    # Récupération des informations utilisateur si connecté
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    # Badge spécial pour les utilisateurs lifetime
    lifetime_badge = ''
    if user and user['role'] == 'lifetime':
        lifetime_badge = '<span class="badge bg-warning ms-2">👑 LIFETIME</span>'
    
    # Menu adaptatif selon l'état de connexion
    if user:
        # Menu pour utilisateurs connectés
        nav_menu = f'''
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'dashboard' else ''}" href="/dashboard">
                                <i class="fas fa-tachometer-alt me-1"></i>Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'calculator' else ''}" href="/calculator">
                                <i class="fas fa-calculator me-1"></i>Calculateur
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'journal' else ''}" href="/journal">
                                <i class="fas fa-book me-1"></i>Journal
                            </a>
                        </li>
                    </ul>
                    
                    <ul class="navbar-nav">
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-user me-1"></i>{user['username']}{lifetime_badge}
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/profile"><i class="fas fa-user-cog me-2"></i>Profil</a></li>
                                <li><a class="dropdown-item" href="/pricing"><i class="fas fa-star me-2"></i>Upgrade</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt me-2"></i>Déconnexion</a></li>
                            </ul>
                        </li>
                    </ul>
        '''
    else:
        # Menu pour utilisateurs non connectés
        nav_menu = f'''
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'home' else ''}" href="/">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'calculator' else ''}" href="/calculator">
                                <i class="fas fa-calculator me-1"></i>Calculateur
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'pricing' else ''}" href="/pricing">
                                <i class="fas fa-star me-1"></i>Tarifs
                            </a>
                        </li>
                    </ul>
                    
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link {'active' if active_page == 'login' else ''}" href="/login">
                                <i class="fas fa-sign-in-alt me-1"></i>Connexion
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link btn btn-primary px-3 ms-2 {'active' if active_page == 'register' else ''}" href="/register">
                                <i class="fas fa-user-plus me-1"></i>Inscription
                            </a>
                        </li>
                    </ul>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - MindTraderPro</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{ padding-top: 80px; }}
        .navbar-brand {{ font-weight: bold; font-size: 1.5rem; }}
        .calculator-form {{ max-width: 600px; margin: 0 auto; }}
        .result-box {{ background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-top: 20px; }}
        .highlight {{ color: #00ff88; font-weight: bold; }}
        .hero-section {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 80px 0; margin: -20px 0 40px 0; }}
        .feature-card {{ transition: transform 0.3s ease; }}
        .feature-card:hover {{ transform: translateY(-5px); }}
        footer {{ background: #1a1a1a; margin-top: 50px; }}
        .role-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; }}
        .standard {{ background: #6c757d; }}
        .premium {{ background: #28a745; }}
        .lifetime {{ background: #ffc107; color: #000; }}
        .alert-calculations {{ border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <!-- Messages Flash -->
    <div class="container mt-3">
        <div id="flash-messages"></div>
    </div>
    
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line me-2 text-primary"></i>MindTraderPro
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                {nav_menu}
            </div>
        </div>
    </nav>
'''

def get_footer():
    """Footer responsive pour toutes les pages"""
    return '''
    <footer class="bg-dark text-light py-5 mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-4 mb-4">
                    <h5><i class="fas fa-chart-line me-2 text-primary"></i>MindTraderPro</h5>
                    <p class="text-muted">
                        Plateforme professionnelle de trading avec système d'authentification sécurisé
                        et gestion des permissions par rôles.
                    </p>
                </div>
                
                <div class="col-md-4 mb-4">
                    <h6 class="text-primary">Fonctionnalités</h6>
                    <ul class="list-unstyled">
                        <li><span class="badge standard me-2">Standard</span>3 calculs gratuits</li>
                        <li><span class="badge premium me-2">Premium</span>Accès illimité + Journal</li>
                        <li><span class="badge lifetime me-2">Lifetime</span>Accès total + Badge VIP</li>
                    </ul>
                </div>
                
                <div class="col-md-4 mb-4">
                    <h6 class="text-primary">Contact</h6>
                    <p class="text-muted mb-1">
                        <i class="fas fa-envelope me-2"></i>support@mindtraderpro.com
                    </p>
                    <p class="text-muted">
                        <i class="fas fa-shield-alt me-2"></i>Authentification sécurisée avec bcrypt
                    </p>
                </div>
            </div>
            
            <hr class="my-4">
            
            <div class="row align-items-center">
                <div class="col-md-6">
                    <p class="mb-0 text-muted">
                        &copy; 2024 MindTraderPro. Système d'authentification sécurisé.
                    </p>
                </div>
                <div class="col-md-6 text-md-end">
                    <span class="badge bg-success">
                        <i class="fas fa-lock me-1"></i>Sécurisé avec SQLite + bcrypt
                    </span>
                </div>
            </div>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Gestion des messages flash
        function showFlashMessage(message, type) {
            const alertClass = type === 'error' ? 'alert-danger' : 
                              type === 'success' ? 'alert-success' : 
                              type === 'warning' ? 'alert-warning' : 'alert-info';
            
            const flashDiv = document.getElementById('flash-messages');
            flashDiv.innerHTML = `
                <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

# Initialisation de la base de données au démarrage
init_database()

# ============================================================================
# ROUTES D'AUTHENTIFICATION
# ============================================================================

@app.route('/')
def home():
    """Page d'accueil adaptée selon l'état de connexion"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    content = '''
    <div class="hero-section text-white">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold mb-4">
                        Calculateur de Trading Professionnel
                    </h1>
                    <p class="lead mb-4">
                        Rejoignez MindTraderPro et optimisez vos trades avec notre système intelligent.
                        Créez un compte pour débloquer toutes les fonctionnalités !
                    </p>
                    <div class="d-flex gap-3 flex-wrap">
                        <a href="/register" class="btn btn-light btn-lg">
                            <i class="fas fa-user-plus me-2"></i>Créer un Compte
                        </a>
                        <a href="/login" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-sign-in-alt me-2"></i>Se Connecter
                        </a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <i class="fas fa-chart-line" style="font-size: 8rem; opacity: 0.7;"></i>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="row mb-5">
            <div class="col-12 text-center">
                <h2 class="display-5 fw-bold mb-3">Plans & Fonctionnalités</h2>
                <p class="lead text-muted mb-5">Choisissez le plan qui correspond à vos besoins</p>
            </div>
        </div>
        
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header text-center">
                        <h4><span class="badge standard">Standard</span></h4>
                        <h3>Gratuit</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>3 calculs de lot gratuits</li>
                            <li><i class="fas fa-check text-success me-2"></i>Accès aux fonctions de base</li>
                            <li><i class="fas fa-times text-danger me-2"></i>Journal de trading limité</li>
                        </ul>
                        <a href="/register" class="btn btn-outline-primary w-100">Commencer</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-success">
                    <div class="card-header text-center bg-success text-white">
                        <h4><span class="badge bg-light text-success">Premium</span></h4>
                        <h3>9.99€/mois</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>Calculs illimités</li>
                            <li><i class="fas fa-check text-success me-2"></i>Journal de trading complet</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support prioritaire</li>
                        </ul>
                        <a href="/register" class="btn btn-success w-100">Choisir Premium</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-warning">
                    <div class="card-header text-center bg-warning text-dark">
                        <h4><span class="badge bg-dark">👑 Lifetime</span></h4>
                        <h3>149€ <small>une fois</small></h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>Accès total à vie</li>
                            <li><i class="fas fa-check text-success me-2"></i>Badge VIP exclusif</li>
                            <li><i class="fas fa-check text-success me-2"></i>Toutes les futures fonctionnalités</li>
                        </ul>
                        <a href="/register" class="btn btn-warning w-100">Devenir Lifetime</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_base_template("Accueil", "home") + content + get_footer()

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page et traitement d'inscription"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            email = data.get('email', '').strip()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            role = data.get('role', 'standard')
            
            # Validation des données
            if not email or not username or not password:
                return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires'})
            
            if len(password) < 6:
                return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 6 caractères'})
            
            if password != confirm_password:
                return jsonify({'success': False, 'error': 'Les mots de passe ne correspondent pas'})
            
            if role not in ['standard', 'premium', 'lifetime']:
                role = 'standard'
            
            # Création de l'utilisateur
            result = create_user(email, username, password, role)
            
            if result['success']:
                return jsonify({'success': True, 'message': 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.'})
            else:
                return jsonify(result)
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erreur: {str(e)}'})
    
    # Page d'inscription (GET)
    content = '''
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header text-center">
                        <h2><i class="fas fa-user-plus me-2 text-primary"></i>Inscription à MindTraderPro</h2>
                        <p class="text-muted mb-0">Créez votre compte pour accéder aux fonctionnalités de trading</p>
                    </div>
                    <div class="card-body">
                        <form id="registerForm">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Email <span class="text-danger">*</span></label>
                                    <input type="email" class="form-control" id="email" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Nom d'utilisateur <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" id="username" required>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Mot de passe <span class="text-danger">*</span></label>
                                    <input type="password" class="form-control" id="password" required>
                                    <small class="text-muted">Au moins 6 caractères</small>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Confirmer le mot de passe <span class="text-danger">*</span></label>
                                    <input type="password" class="form-control" id="confirm_password" required>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label class="form-label">Type de compte</label>
                                <select class="form-select" id="role">
                                    <option value="standard">Standard (Gratuit)</option>
                                    <option value="premium">Premium (9.99€/mois)</option>
                                    <option value="lifetime">Lifetime (149€ une fois)</option>
                                </select>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-lg w-100">
                                <i class="fas fa-user-plus me-2"></i>Créer mon Compte
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Déjà un compte ? <a href="/login" class="text-primary">Se connecter</a></p>
                        </div>
                        
                        <div id="result" style="display: none; margin-top: 20px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                email: document.getElementById('email').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                confirm_password: document.getElementById('confirm_password').value,
                role: document.getElementById('role').value
            };
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>✅ Inscription réussie !</h5>
                            <p>${result.message}</p>
                            <a href="/login" class="btn btn-success">Se connecter maintenant</a>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <h5>❌ Erreur</h5>
                            <p>${result.error}</p>
                        </div>
                    `;
                }
                
                resultDiv.style.display = 'block';
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('result').innerHTML = `
                    <div class="alert alert-danger">
                        <h5>❌ Erreur de connexion</h5>
                        <p>Impossible de créer le compte.</p>
                    </div>
                `;
                document.getElementById('result').style.display = 'block';
            }
        });
    </script>
    '''
    
    return get_base_template("Inscription", "register") + content + get_footer()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page et traitement de connexion"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({'success': False, 'error': 'Email et mot de passe requis'})
            
            # Authentification
            result = authenticate_user(email, password)
            
            if result['success']:
                # Création de la session
                session['user_id'] = result['user']['id']
                session['username'] = result['user']['username']
                session['role'] = result['user']['role']
                
                return jsonify({
                    'success': True, 
                    'message': f"Connexion réussie ! Bienvenue {result['user']['username']}",
                    'redirect': '/dashboard'
                })
            else:
                return jsonify(result)
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erreur: {str(e)}'})
    
    # Page de connexion (GET)
    content = '''
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header text-center">
                        <h2><i class="fas fa-sign-in-alt me-2 text-primary"></i>Connexion</h2>
                        <p class="text-muted mb-0">Accédez à votre compte MindTraderPro</p>
                    </div>
                    <div class="card-body">
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" id="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-lg w-100">
                                <i class="fas fa-sign-in-alt me-2"></i>Se connecter
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Pas encore de compte ? <a href="/register" class="text-primary">S'inscrire</a></p>
                        </div>
                        
                        <div id="result" style="display: none; margin-top: 20px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>✅ ${result.message}</h5>
                            <p>Redirection vers le dashboard...</p>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                    
                    // Redirection après 1 seconde
                    setTimeout(() => {
                        window.location.href = result.redirect;
                    }, 1000);
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <h5>❌ Erreur de connexion</h5>
                            <p>${result.error}</p>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('result').innerHTML = `
                    <div class="alert alert-danger">
                        <h5>❌ Erreur de connexion</h5>
                        <p>Impossible de se connecter.</p>
                    </div>
                `;
                document.getElementById('result').style.display = 'block';
            }
        });
    </script>
    '''
    
    return get_base_template("Connexion", "login") + content + get_footer()

@app.route('/logout')
def logout():
    """Déconnexion utilisateur"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard utilisateur avec informations de compte"""
    user = get_user_by_id(session['user_id'])
    
    # Calcul des limites selon le rôle
    calculations_limit = "Illimité" if user['role'] in ['premium', 'lifetime'] else "3"
    calculations_remaining = max(0, 3 - user['calculations_used']) if user['role'] == 'standard' else "Illimité"
    
    # Couleur du badge selon le rôle
    role_class = {'standard': 'secondary', 'premium': 'success', 'lifetime': 'warning'}
    role_icon = {'standard': 'fas fa-user', 'premium': 'fas fa-star', 'lifetime': 'fas fa-crown'}
    
    content = f'''
    <div class="container">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h1 class="display-5 fw-bold">
                            <i class="fas fa-tachometer-alt text-primary me-3"></i>Dashboard
                        </h1>
                        <p class="lead text-muted">Bienvenue {user['username']} !</p>
                    </div>
                    <div>
                        <span class="badge bg-{role_class[user['role']]} role-badge">
                            <i class="{role_icon[user['role']]} me-1"></i>{user['role'].upper()}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-4 mb-5">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-calculator text-primary mb-3" style="font-size: 3rem;"></i>
                        <h4>Calculs Utilisés</h4>
                        <h2 class="text-primary">{user['calculations_used']}</h2>
                        <p class="text-muted">Limite: {calculations_limit}</p>
                        <p class="text-muted">Restants: {calculations_remaining}</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-user-circle text-success mb-3" style="font-size: 3rem;"></i>
                        <h4>Profil</h4>
                        <h6>{user['email']}</h6>
                        <p class="text-muted">@{user['username']}</p>
                        <span class="badge bg-{role_class[user['role']]}">{user['role'].upper()}</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-chart-line text-warning mb-3" style="font-size: 3rem;"></i>
                        <h4>Actions Rapides</h4>
                        <div class="d-grid gap-2">
                            <a href="/calculator" class="btn btn-primary">
                                <i class="fas fa-calculator me-2"></i>Calculateur
                            </a>
                            <a href="/journal" class="btn btn-success">
                                <i class="fas fa-book me-2"></i>Journal
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        {get_role_specific_content(user)}
    </div>
    '''
    
    return get_base_template("Dashboard", "dashboard") + content + get_footer()

def get_role_specific_content(user):
    """Retourne du contenu spécifique selon le rôle utilisateur"""
    if user['role'] == 'standard':
        remaining = max(0, 3 - user['calculations_used'])
        if remaining <= 1:
            return '''
            <div class="alert alert-warning alert-calculations">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>Limite Presque Atteinte</h5>
                <p>Vous avez presque épuisé vos calculs gratuits. Passez à Premium pour un accès illimité !</p>
                <a href="/pricing" class="btn btn-warning">Upgrader maintenant</a>
            </div>
            '''
        else:
            return f'''
            <div class="alert alert-info">
                <h5><i class="fas fa-info-circle me-2"></i>Compte Standard</h5>
                <p>Il vous reste {remaining} calculs gratuits. Découvrez nos plans Premium pour plus de fonctionnalités !</p>
                <a href="/pricing" class="btn btn-primary">Voir les Plans</a>
            </div>
            '''
    
    elif user['role'] == 'premium':
        return '''
        <div class="alert alert-success">
            <h5><i class="fas fa-star me-2"></i>Membre Premium</h5>
            <p>Profitez de votre accès illimité au calculateur et au journal de trading !</p>
            <div class="row">
                <div class="col-md-6">
                    <a href="/calculator" class="btn btn-success w-100">Calculateur Illimité</a>
                </div>
                <div class="col-md-6">
                    <a href="/journal" class="btn btn-outline-success w-100">Journal Complet</a>
                </div>
            </div>
        </div>
        '''
    
    elif user['role'] == 'lifetime':
        return '''
        <div class="alert" style="background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%); color: #000;">
            <h5><i class="fas fa-crown me-2"></i>Membre Lifetime VIP 👑</h5>
            <p><strong>Félicitations !</strong> Vous avez un accès à vie à toutes les fonctionnalités actuelles et futures de MindTraderPro.</p>
            <div class="row">
                <div class="col-md-4">
                    <a href="/calculator" class="btn btn-dark w-100 mb-2">Calculateur Illimité</a>
                </div>
                <div class="col-md-4">
                    <a href="/journal" class="btn btn-dark w-100 mb-2">Journal Premium</a>
                </div>
                <div class="col-md-4">
                    <a href="/vip-features" class="btn btn-dark w-100 mb-2">Fonctionnalités VIP</a>
                </div>
            </div>
        </div>
        '''
    
    return ''

# ============================================================================
# ROUTES PRINCIPALES AVEC GESTION DES PERMISSIONS
# ============================================================================

@app.route('/calculator', methods=['GET'])
def calculator():
    """Page calculateur avec vérification des permissions"""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    # Vérification des limites pour les utilisateurs standard
    limit_warning = ''
    if user and user['role'] == 'standard':
        remaining = max(0, 3 - user['calculations_used'])
        if remaining == 0:
            limit_warning = '''
            <div class="alert alert-danger">
                <h5><i class="fas fa-ban me-2"></i>Limite Atteinte</h5>
                <p>Vous avez épuisé vos 3 calculs gratuits. Passez à Premium pour un accès illimité !</p>
                <a href="/pricing" class="btn btn-warning">Upgrader maintenant</a>
            </div>
            '''
        elif remaining <= 1:
            limit_warning = f'''
            <div class="alert alert-warning">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>Attention</h5>
                <p>Il vous reste {remaining} calcul(s) gratuit(s). Pensez à upgrader pour un accès illimité !</p>
                <a href="/pricing" class="btn btn-warning btn-sm">Voir les Plans</a>
            </div>
            '''
    
    content = f'''
    <div class="container">
        <div class="row">
            <div class="col-12 text-center mb-4">
                <h1 class="display-5 fw-bold">
                    <i class="fas fa-calculator text-primary me-3"></i>Calculateur de Position
                </h1>
                <p class="lead text-muted">Optimisez vos trades avec notre calculateur professionnel</p>
                {f"<p>Connecté en tant que: <span class='badge bg-{{'standard': 'secondary', 'premium': 'success', 'lifetime': 'warning'}}[user['role']]'>{user['username']} - {user['role'].upper()}</span></p>" if user else "<p class='text-warning'>Mode invité - Connectez-vous pour sauvegarder vos calculs</p>"}
            </div>
        </div>
        
        {limit_warning}
        
        <div class="calculator-form">
            <div class="card">
                <div class="card-header">
                    <h3>Paramètres de Trading</h3>
                    {f"<small class='text-muted'>Calculs utilisés: {user['calculations_used']}/{'∞' if user['role'] != 'standard' else '3'}</small>" if user else ""}
                </div>
                <div class="card-body">
                    <form id="calculatorForm">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Paire de devises</label>
                                <select class="form-select" id="pair_symbol">
                                    <option value="XAUUSD">XAU/USD (Or)</option>
                                    <option value="EURUSD">EUR/USD</option>
                                    <option value="GBPUSD">GBP/USD</option>
                                    <option value="USDJPY">USD/JPY</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Direction</label>
                                <select class="form-select" id="direction">
                                    <option value="buy">Achat (Buy)</option>
                                    <option value="sell">Vente (Sell)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Prix d'entrée</label>
                                <input type="number" class="form-control" id="entry_price" step="0.00001" value="2000" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Stop Loss</label>
                                <input type="number" class="form-control" id="stop_loss" step="0.00001" value="1990" required>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Capital ($)</label>
                                <input type="number" class="form-control" id="capital" value="20000" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Risque (%)</label>
                                <input type="number" class="form-control" id="risk_percent" step="0.1" value="0.5" max="10" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-lg w-100" {'disabled' if user and user['role'] == 'standard' and user['calculations_used'] >= 3 else ''}>
                            <i class="fas fa-calculator me-2"></i>Calculer la Position
                        </button>
                    </form>
                    
                    <div id="result" class="result-box" style="display: none;"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('calculatorForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const formData = {{
                pair_symbol: document.getElementById('pair_symbol').value,
                direction: document.getElementById('direction').value,
                entry_price: parseFloat(document.getElementById('entry_price').value),
                stop_loss: parseFloat(document.getElementById('stop_loss').value),
                capital: parseFloat(document.getElementById('capital').value),
                risk_percent: parseFloat(document.getElementById('risk_percent').value)
            }};
            
            try {{
                const response = await fetch('/calculate', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(formData)
                }});
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                
                if (result.success) {{
                    resultDiv.innerHTML = `
                        <h4 class="text-success">✅ Calcul Réussi</h4>
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Taille de lot:</strong> <span class="highlight">${{result.lot_size}}</span></p>
                                <p><strong>Risque USD:</strong> <span class="highlight">${{result.risk_usd}}</span></p>
                                <p><strong>Stop Loss (pips):</strong> ${{result.sl_pips}}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Capital:</strong> ${{result.capital}}</p>
                                <p><strong>Risque %:</strong> ${{result.risk_percent}}%</p>
                                <p><strong>Valeur pip:</strong> ${{result.pip_value}}</p>
                            </div>
                        </div>
                        ${{result.usage_info ? `<div class="alert alert-info mt-3"><small>${{result.usage_info}}</small></div>` : ''}}
                    `;
                    
                    // Rechargement de la page si limite atteinte
                    if (result.reload_needed) {{
                        setTimeout(() => {{ window.location.reload(); }}, 2000);
                    }}
                }} else {{
                    resultDiv.innerHTML = `
                        <h4 class="text-danger">❌ Erreur</h4>
                        <p>${{result.error}}</p>
                        ${{result.upgrade_needed ? '<a href="/pricing" class="btn btn-warning">Upgrader maintenant</a>' : ''}}
                    `;
                }}
                
                resultDiv.style.display = 'block';
            }} catch (error) {{
                console.error('Erreur:', error);
                document.getElementById('result').innerHTML = `
                    <h4 class="text-danger">❌ Erreur de connexion</h4>
                    <p>Impossible de calculer la position.</p>
                `;
                document.getElementById('result').style.display = 'block';
            }}
        }});
    </script>
    '''
    
    return get_base_template("Calculateur", "calculator") + content + get_footer()

# ============================================================================
# ROUTES DU JOURNAL DE TRADING COMPLET
# ============================================================================

@app.route('/journal')
@login_required
def journal():
    """Page journal de trading complet avec formulaire, historique et statistiques"""
    user = get_user_by_id(session['user_id'])
    
    # Vérification des permissions - Accès limité aux utilisateurs premium et lifetime uniquement
    if user['role'] == 'standard':
        content = '''
        <div class="container">
            <div class="row">
                <div class="col-12 text-center mb-4">
                    <h1 class="display-5 fw-bold">
                        <i class="fas fa-book text-success me-3"></i>Journal de Trading
                    </h1>
                    <p class="lead text-muted">Fonctionnalité Premium requise</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-lg-8 mx-auto">
                    <div class="alert alert-warning">
                        <h4><i class="fas fa-lock me-2"></i>Accès Premium Requis</h4>
                        <p>Le journal de trading complet est réservé aux membres Premium et Lifetime.</p>
                        <p>Avec un compte Premium, vous aurez accès à :</p>
                        <ul>
                            <li>Formulaire d'ajout de trades détaillé</li>
                            <li>Historique complet avec tri et filtres</li>
                            <li>Statistiques avancées (winrate, drawdown, etc.)</li>
                            <li>Graphiques de performances</li>
                            <li>Notes vocales pour chaque trade</li>
                            <li>Export des données</li>
                        </ul>
                        <a href="/pricing" class="btn btn-warning btn-lg">Upgrader vers Premium</a>
                    </div>
                </div>
            </div>
        </div>
        '''
        return get_base_template("Journal", "journal") + content + get_footer()
    
    # Récupération des données pour les utilisateurs premium/lifetime
    trades = get_user_trades(user['id'])
    stats = get_trading_statistics(user['id'])
    
    # Préparation des données pour les graphiques
    wins = [t for t in trades if t['status'] == 'closed' and t['result_pnl'] and t['result_pnl'] > 0]
    losses = [t for t in trades if t['status'] == 'closed' and t['result_pnl'] and t['result_pnl'] < 0]
    
    content = f'''
    <div class="container-fluid">
        <div class="row">
            <div class="col-12 mb-4">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="display-6 fw-bold">
                            <i class="fas fa-book text-success me-3"></i>Journal de Trading
                        </h1>
                        <p class="lead text-muted">Gestion complète de vos trades et performances</p>
                    </div>
                    <div>
                        <span class="badge bg-{'success' if user['role'] == 'premium' else 'warning'} fs-6">
                            <i class="fas fa-{'star' if user['role'] == 'premium' else 'crown'} me-1"></i>{user['role'].upper()}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Statistiques de Trading -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-chart-line fa-2x mb-2"></i>
                        <h3>{stats.get('total_trades', 0)}</h3>
                        <small>Trades Total</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-percentage fa-2x mb-2"></i>
                        <h3>{stats.get('winrate', 0)}%</h3>
                        <small>Taux de Réussite</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-dollar-sign fa-2x mb-2"></i>
                        <h3>${stats.get('total_pnl', 0)}</h3>
                        <small>P&L Total</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-dark h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-trending-down fa-2x mb-2"></i>
                        <h3>${stats.get('max_drawdown', 0)}</h3>
                        <small>Drawdown Max</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Formulaire d'Ajout de Trade -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fas fa-plus-circle me-2"></i>Ajouter un Nouveau Trade</h4>
                    </div>
                    <div class="card-body">
                        <form id="addTradeForm">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Actif <span class="text-danger">*</span></label>
                                    <select class="form-select" id="asset" required>
                                        <option value="">Sélectionner un actif</option>
                                        <option value="EURUSD">EUR/USD</option>
                                        <option value="GBPUSD">GBP/USD</option>
                                        <option value="USDJPY">USD/JPY</option>
                                        <option value="USDCHF">USD/CHF</option>
                                        <option value="AUDUSD">AUD/USD</option>
                                        <option value="USDCAD">USD/CAD</option>
                                        <option value="NZDUSD">NZD/USD</option>
                                        <option value="XAUUSD">XAU/USD (Or)</option>
                                        <option value="XAGUSD">XAG/USD (Argent)</option>
                                        <option value="BTCUSD">BTC/USD</option>
                                        <option value="ETHUSD">ETH/USD</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Type <span class="text-danger">*</span></label>
                                    <select class="form-select" id="trade_type" required>
                                        <option value="">Sélectionner</option>
                                        <option value="buy">Achat (Buy)</option>
                                        <option value="sell">Vente (Sell)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Date & Heure <span class="text-danger">*</span></label>
                                    <input type="datetime-local" class="form-control" id="trade_date" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Taille de lot <span class="text-danger">*</span></label>
                                    <input type="number" class="form-control" id="lot_size" step="0.01" min="0.01" required>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Prix d'entrée <span class="text-danger">*</span></label>
                                    <input type="number" class="form-control" id="entry_price" step="0.00001" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Stop Loss</label>
                                    <input type="number" class="form-control" id="stop_loss" step="0.00001">
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Take Profit</label>
                                    <input type="number" class="form-control" id="take_profit" step="0.00001">
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Style de Trading</label>
                                    <select class="form-select" id="trading_style">
                                        <option value="">Sélectionner un style</option>
                                        <option value="scalping">Scalping</option>
                                        <option value="day_trading">Day Trading</option>
                                        <option value="swing">Swing Trading</option>
                                        <option value="position">Position Trading</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">État Émotionnel</label>
                                    <select class="form-select" id="emotions">
                                        <option value="">Sélectionner une émotion</option>
                                        <option value="confident">Confiant</option>
                                        <option value="nervous">Nerveux</option>
                                        <option value="greedy">Cupide</option>
                                        <option value="fearful">Craintif</option>
                                        <option value="calm">Calme</option>
                                        <option value="frustrated">Frustré</option>
                                        <option value="excited">Excité</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Notes</label>
                                <textarea class="form-control" id="notes" rows="3" placeholder="Décrivez votre analyse, votre stratégie ou vos observations..."></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Note Vocale (Audio)</label>
                                <input type="file" class="form-control" id="audio_note" accept="audio/*">
                                <small class="text-muted">Formats acceptés: MP3, WAV, M4A (max 10MB)</small>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-success btn-lg">
                                    <i class="fas fa-save me-2"></i>Enregistrer le Trade
                                </button>
                            </div>
                        </form>
                        
                        <div id="addTradeResult" class="mt-3" style="display: none;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Statistiques Détaillées -->
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar me-2"></i>Statistiques Détaillées</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center mb-3">
                            <div class="col-6">
                                <h6 class="text-success">Trades Gagnants</h6>
                                <h4 class="text-success">{stats.get('winning_trades', 0)}</h4>
                            </div>
                            <div class="col-6">
                                <h6 class="text-danger">Trades Perdants</h6>
                                <h4 class="text-danger">{stats.get('losing_trades', 0)}</h4>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="mb-2">
                            <small class="text-muted">Gain Moyen:</small>
                            <span class="float-end text-success">${stats.get('average_win', 0)}</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Perte Moyenne:</small>
                            <span class="float-end text-danger">${stats.get('average_loss', 0)}</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Facteur de Profit:</small>
                            <span class="float-end fw-bold">{stats.get('profit_factor', 0)}</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Meilleur Trade:</small>
                            <span class="float-end text-success">${stats.get('best_trade', 0)}</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Pire Trade:</small>
                            <span class="float-end text-danger">${stats.get('worst_trade', 0)}</span>
                        </div>
                        
                        <hr>
                        
                        <div class="mb-2">
                            <small class="text-muted">Actifs Tradés:</small>
                            <span class="float-end">{len(stats.get('assets_traded', []))}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Graphique Simple Win/Loss -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h6><i class="fas fa-chart-pie me-2"></i>Répartition Win/Loss</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="winLossChart" width="300" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Historique des Trades -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4><i class="fas fa-history me-2"></i>Historique des Trades</h4>
                        <div class="d-flex gap-2">
                            <input type="text" class="form-control form-control-sm" id="searchTrades" placeholder="Rechercher..." style="width: 200px;">
                            <select class="form-select form-select-sm" id="filterStatus" style="width: 150px;">
                                <option value="">Tous les statuts</option>
                                <option value="open">Ouvert</option>
                                <option value="closed">Fermé</option>
                                <option value="cancelled">Annulé</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover" id="tradesTable">
                                <thead class="table-dark">
                                    <tr>
                                        <th data-sort="asset">Actif <i class="fas fa-sort"></i></th>
                                        <th data-sort="trade_type">Type</th>
                                        <th data-sort="trade_date">Date <i class="fas fa-sort"></i></th>
                                        <th data-sort="entry_price">Entrée</th>
                                        <th data-sort="exit_price">Sortie</th>
                                        <th data-sort="lot_size">Lot</th>
                                        <th data-sort="result_pnl">P&L <i class="fas fa-sort"></i></th>
                                        <th data-sort="result_pips">Pips</th>
                                        <th data-sort="trading_style">Style</th>
                                        <th data-sort="emotions">Émotion</th>
                                        <th data-sort="status">Statut</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="tradesTableBody">'''
    
    # Génération des lignes du tableau
    for trade in trades[:20]:  # Affichage des 20 derniers trades
        status_badge = {
            'open': 'badge bg-primary',
            'closed': 'badge bg-success', 
            'cancelled': 'badge bg-secondary'
        }.get(trade['status'], 'badge bg-secondary')
        
        type_badge = 'badge bg-success' if trade['trade_type'] == 'buy' else 'badge bg-danger'
        
        pnl_class = ''
        if trade['result_pnl']:
            pnl_class = 'text-success' if trade['result_pnl'] > 0 else 'text-danger'
        
        emotion_icon = {
            'confident': 'fas fa-smile text-success',
            'nervous': 'fas fa-grimace text-warning',
            'greedy': 'fas fa-dollar-sign text-warning',
            'fearful': 'fas fa-frown text-danger',
            'calm': 'fas fa-zen text-info',
            'frustrated': 'fas fa-angry text-danger',
            'excited': 'fas fa-grin-stars text-success'
        }.get(trade['emotions'], 'fas fa-meh text-muted')
        
        content += f'''
                                    <tr data-trade-id="{trade['id']}">
                                        <td><strong>{trade['asset']}</strong></td>
                                        <td><span class="{type_badge}">{trade['trade_type'].upper()}</span></td>
                                        <td>{trade['trade_date'][:16] if trade['trade_date'] else 'N/A'}</td>
                                        <td>{trade['entry_price']}</td>
                                        <td>{trade['exit_price'] or '-'}</td>
                                        <td>{trade['lot_size']}</td>
                                        <td class="{pnl_class}">${trade['result_pnl'] or 0}</td>
                                        <td class="{pnl_class}">{trade['result_pips'] or 0}</td>
                                        <td>{trade['trading_style'] or '-'}</td>
                                        <td><i class="{emotion_icon}" title="{trade['emotions'] or 'N/A'}"></i></td>
                                        <td><span class="{status_badge}">{trade['status'].upper()}</span></td>
                                        <td>
                                            <div class="btn-group btn-group-sm">'''
        
        # Ajout conditionnel des boutons selon le statut et les données
        if trade['status'] == 'open':
            content += f'''
                                                <button class="btn btn-warning btn-sm" onclick="closeTradeModal({trade['id']})">
                                                    <i class="fas fa-edit"></i>
                                                </button>'''
        
        if trade['audio_note_path']:
            content += f'''
                                                <button class="btn btn-info btn-sm" onclick="playAudioNote('{trade['audio_note_path']}')">
                                                    <i class="fas fa-volume-up"></i>
                                                </button>'''
        
        content += f'''
                                                <button class="btn btn-outline-secondary btn-sm" onclick="showTradeDetails({trade['id']})">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>'''
    
    if not trades:
        content += '''
                                    <tr>
                                        <td colspan="12" class="text-center py-4">
                                            <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                                            <h5 class="text-muted">Aucun trade enregistré</h5>
                                            <p class="text-muted">Commencez par ajouter votre premier trade ci-dessus.</p>
                                        </td>
                                    </tr>'''
    
    content += '''
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- Pagination -->
                        <nav aria-label="Navigation des trades">
                            <ul class="pagination justify-content-center">
                                <li class="page-item disabled">
                                    <a class="page-link" href="#" tabindex="-1">Précédent</a>
                                </li>
                                <li class="page-item active"><a class="page-link" href="#">1</a></li>
                                <li class="page-item disabled">
                                    <a class="page-link" href="#">Suivant</a>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal pour clôturer un trade -->
    <div class="modal fade" id="closeTradeModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Clôturer le Trade</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="closeTradeForm">
                        <input type="hidden" id="closeTradeId">
                        <div class="mb-3">
                            <label class="form-label">Prix de sortie <span class="text-danger">*</span></label>
                            <input type="number" class="form-control" id="exit_price" step="0.00001" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Résultat P&L ($)</label>
                                <input type="number" class="form-control" id="result_pnl" step="0.01">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Résultat (Pips)</label>
                                <input type="number" class="form-control" id="result_pips" step="0.1">
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-success" onclick="submitCloseTrade()">Clôturer</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // ============================================================================
        // JAVASCRIPT POUR LE JOURNAL DE TRADING
        // ============================================================================
        
        // Configuration automatique de la date actuelle
        document.addEventListener('DOMContentLoaded', function() {{
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById('trade_date').value = now.toISOString().slice(0, 16);
        }});
        
        // Soumission du formulaire d'ajout de trade
        document.getElementById('addTradeForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('asset', document.getElementById('asset').value);
            formData.append('trade_type', document.getElementById('trade_type').value);
            formData.append('trade_date', document.getElementById('trade_date').value);
            formData.append('entry_price', document.getElementById('entry_price').value);
            formData.append('stop_loss', document.getElementById('stop_loss').value);
            formData.append('take_profit', document.getElementById('take_profit').value);
            formData.append('lot_size', document.getElementById('lot_size').value);
            formData.append('trading_style', document.getElementById('trading_style').value);
            formData.append('emotions', document.getElementById('emotions').value);
            formData.append('notes', document.getElementById('notes').value);
            
            // Ajout du fichier audio si sélectionné
            const audioFile = document.getElementById('audio_note').files[0];
            if (audioFile) {{
                formData.append('audio_note', audioFile);
            }}
            
            try {{
                const response = await fetch('/journal/add-trade', {{
                    method: 'POST',
                    body: formData
                }});
                
                const result = await response.json();
                const resultDiv = document.getElementById('addTradeResult');
                
                if (result.success) {{
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h6>✅ ${{result.message}}</h6>
                            <p class="mb-0">Trade ID: ${{result.trade_id}}</p>
                        </div>
                    `;
                    document.getElementById('addTradeForm').reset();
                    
                    // Rechargement de la page après 2 secondes pour afficher le nouveau trade
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 2000);
                }} else {{
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <h6>❌ Erreur</h6>
                            <p class="mb-0">${{result.error}}</p>
                        </div>
                    `;
                }}
                
                resultDiv.style.display = 'block';
            }} catch (error) {{
                console.error('Erreur:', error);
                document.getElementById('addTradeResult').innerHTML = `
                    <div class="alert alert-danger">
                        <h6>❌ Erreur de connexion</h6>
                        <p class="mb-0">Impossible d'ajouter le trade.</p>
                    </div>
                `;
                document.getElementById('addTradeResult').style.display = 'block';
            }}
        }});
        
        // Graphique Win/Loss avec Chart.js
        const ctx = document.getElementById('winLossChart').getContext('2d');
        const winLossChart = new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Trades Gagnants', 'Trades Perdants'],
                datasets: [{{
                    data: [{stats.get('winning_trades', 0)}, {stats.get('losing_trades', 0)}],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Fonction pour ouvrir le modal de clôture
        function closeTradeModal(tradeId) {{
            document.getElementById('closeTradeId').value = tradeId;
            new bootstrap.Modal(document.getElementById('closeTradeModal')).show();
        }}
        
        // Soumission de la clôture de trade
        async function submitCloseTrade() {{
            const tradeId = document.getElementById('closeTradeId').value;
            const exitPrice = document.getElementById('exit_price').value;
            const resultPnl = document.getElementById('result_pnl').value;
            const resultPips = document.getElementById('result_pips').value;
            
            try {{
                const response = await fetch('/journal/close-trade', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        trade_id: tradeId,
                        exit_price: parseFloat(exitPrice),
                        result_pnl: parseFloat(resultPnl),
                        result_pips: parseFloat(resultPips)
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    bootstrap.Modal.getInstance(document.getElementById('closeTradeModal')).hide();
                    window.location.reload();
                }} else {{
                    alert('Erreur: ' + result.error);
                }}
            }} catch (error) {{
                console.error('Erreur:', error);
                alert('Erreur de connexion');
            }}
        }}
        
        // Tri des colonnes du tableau
        document.querySelectorAll('[data-sort]').forEach(header => {{
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {{
                const column = this.dataset.sort;
                sortTable(column);
            }});
        }});
        
        // Fonction de tri basique
        function sortTable(column) {{
            // Implementation simple du tri - peut être améliorée
            console.log('Tri par:', column);
        }}
        
        // Recherche dans le tableau
        document.getElementById('searchTrades').addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#tradesTableBody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            }});
        }});
        
        // Filtrage par statut
        document.getElementById('filterStatus').addEventListener('change', function() {{
            const filterValue = this.value;
            const rows = document.querySelectorAll('#tradesTableBody tr');
            
            rows.forEach(row => {{
                if (!filterValue) {{
                    row.style.display = '';
                }} else {{
                    const statusBadge = row.querySelector('.badge');
                    const status = statusBadge ? statusBadge.textContent.toLowerCase() : '';
                    row.style.display = status.includes(filterValue) ? '' : 'none';
                }}
            }});
        }});
        
        // Fonction pour jouer les notes audio
        function playAudioNote(audioPath) {{
            if (audioPath && audioPath !== 'None') {{
                const audio = new Audio('/static/audio/' + audioPath);
                audio.play().catch(e => console.error('Erreur lecture audio:', e));
            }}
        }}
        
        // Fonction pour afficher les détails d'un trade
        function showTradeDetails(tradeId) {{
            // Peut être implémentée pour afficher un modal avec tous les détails
            console.log('Affichage des détails du trade:', tradeId);
        }}
    </script>
    '''
    
    return get_base_template("Journal", "journal") + content + get_footer()

# ============================================================================
# ROUTES API POUR LE JOURNAL DE TRADING
# ============================================================================

@app.route('/journal/add-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def add_trade_api():
    """API pour ajouter un nouveau trade au journal"""
    try:
        user = get_user_by_id(session['user_id'])
        
        # Récupération des données du formulaire
        asset = request.form.get('asset')
        trade_type = request.form.get('trade_type')
        trade_date = request.form.get('trade_date')
        entry_price = float(request.form.get('entry_price'))
        stop_loss = request.form.get('stop_loss')
        take_profit = request.form.get('take_profit')
        lot_size = float(request.form.get('lot_size'))
        trading_style = request.form.get('trading_style')
        emotions = request.form.get('emotions')
        notes = request.form.get('notes')
        
        # Gestion du fichier audio (note vocale)
        audio_note_path = None
        if 'audio_note' in request.files:
            audio_file = request.files['audio_note']
            if audio_file.filename:
                # Création du dossier audio s'il n'existe pas
                os.makedirs('static/audio', exist_ok=True)
                
                # Génération d'un nom de fichier unique
                import uuid
                file_extension = audio_file.filename.split('.')[-1]
                unique_filename = f"trade_{user['id']}_{uuid.uuid4().hex[:8]}.{file_extension}"
                audio_note_path = unique_filename
                
                # Sauvegarde du fichier
                audio_file.save(f'static/audio/{unique_filename}')
        
        # Conversion des valeurs optionnelles
        stop_loss = float(stop_loss) if stop_loss else None
        take_profit = float(take_profit) if take_profit else None
        
        # Ajout du trade dans la base de données
        result = add_trade_to_journal(
            user['id'], asset, trade_type, trade_date, entry_price, 
            stop_loss, take_profit, lot_size, trading_style, 
            emotions, notes, audio_note_path
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de l\'ajout: {str(e)}'}), 400

@app.route('/journal/close-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def close_trade_api():
    """API pour clôturer un trade ouvert"""
    try:
        user = get_user_by_id(session['user_id'])
        data = request.get_json()
        
        trade_id = data.get('trade_id')
        exit_price = data.get('exit_price')
        result_pnl = data.get('result_pnl')
        result_pips = data.get('result_pips')
        
        # Mise à jour du trade
        result = update_trade_result(trade_id, user['id'], exit_price, result_pnl, result_pips)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de la clôture: {str(e)}'}), 400

@app.route('/journal/trades-data')
@login_required
@role_required(['premium', 'lifetime'])
def get_trades_data():
    """API pour récupérer les données des trades (pour AJAX)"""
    try:
        user = get_user_by_id(session['user_id'])
        
        # Paramètres de pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        # Récupération des trades
        trades = get_user_trades(user['id'], limit, offset)
        stats = get_trading_statistics(user['id'])
        
        return jsonify({
            'success': True,
            'trades': trades,
            'stats': stats,
            'page': page,
            'has_more': len(trades) == limit
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@app.route('/journal/export')
@login_required
@role_required(['premium', 'lifetime'])
def export_trades():
    """Export des trades en CSV"""
    try:
        user = get_user_by_id(session['user_id'])
        trades = get_user_trades(user['id'], limit=1000)  # Export de tous les trades
        
        import csv
        import io
        from flask import make_response
        
        # Création du CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes CSV
        writer.writerow([
            'ID', 'Actif', 'Type', 'Date', 'Prix Entrée', 'Stop Loss', 'Take Profit',
            'Prix Sortie', 'Lot Size', 'P&L', 'Pips', 'Style', 'Émotions', 'Notes', 'Statut'
        ])
        
        # Données des trades
        for trade in trades:
            writer.writerow([
                trade['id'], trade['asset'], trade['trade_type'], trade['trade_date'],
                trade['entry_price'], trade['stop_loss'], trade['take_profit'],
                trade['exit_price'], trade['lot_size'], trade['result_pnl'],
                trade['result_pips'], trade['trading_style'], trade['emotions'],
                trade['notes'], trade['status']
            ])
        
        # Préparation de la réponse
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=trades_export_{user["username"]}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur export: {str(e)}'}), 400

@app.route('/pricing')
def pricing():
    """Page de tarification"""
    content = '''
    <div class="container">
        <div class="row">
            <div class="col-12 text-center mb-5">
                <h1 class="display-4 fw-bold">Plans & Tarifs</h1>
                <p class="lead text-muted">Choisissez le plan qui correspond à vos besoins de trading</p>
            </div>
        </div>
        
        <div class="row g-4 justify-content-center">
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header text-center">
                        <h4><span class="badge standard">Standard</span></h4>
                        <h2>Gratuit</h2>
                        <p class="text-muted">Pour débuter</p>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>3 calculs de lot gratuits</li>
                            <li><i class="fas fa-check text-success me-2"></i>Accès aux fonctions de base</li>
                            <li><i class="fas fa-times text-danger me-2"></i>Journal de trading limité</li>
                            <li><i class="fas fa-times text-danger me-2"></i>Support standard</li>
                        </ul>
                        <a href="/register" class="btn btn-outline-primary w-100">Commencer Gratuitement</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-success position-relative">
                    <div class="position-absolute top-0 start-50 translate-middle">
                        <span class="badge bg-success">POPULAIRE</span>
                    </div>
                    <div class="card-header text-center bg-success text-white">
                        <h4><span class="badge bg-light text-success">Premium</span></h4>
                        <h2>9.99€<small>/mois</small></h2>
                        <p class="mb-0">Pour les traders actifs</p>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>Calculs illimités</li>
                            <li><i class="fas fa-check text-success me-2"></i>Journal de trading complet</li>
                            <li><i class="fas fa-check text-success me-2"></i>Analyse des performances</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support prioritaire</li>
                            <li><i class="fas fa-check text-success me-2"></i>Export des données</li>
                        </ul>
                        <a href="/register" class="btn btn-success w-100">Choisir Premium</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-warning">
                    <div class="card-header text-center bg-warning text-dark">
                        <h4><span class="badge bg-dark">👑 Lifetime</span></h4>
                        <h2>149€ <small>une fois</small></h2>
                        <p class="mb-0">Accès à vie</p>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success me-2"></i>Toutes les fonctionnalités Premium</li>
                            <li><i class="fas fa-check text-success me-2"></i>Badge VIP exclusif 👑</li>
                            <li><i class="fas fa-check text-success me-2"></i>Accès aux futures fonctionnalités</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support VIP prioritaire</li>
                            <li><i class="fas fa-check text-success me-2"></i>Pas d'abonnement mensuel</li>
                        </ul>
                        <a href="/register" class="btn btn-warning w-100">Devenir Lifetime</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-5">
            <div class="col-lg-8 mx-auto">
                <div class="card">
                    <div class="card-header text-center">
                        <h4>Questions Fréquentes</h4>
                    </div>
                    <div class="card-body">
                        <div class="accordion" id="faqAccordion">
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                                        Puis-je changer de plan à tout moment ?
                                    </button>
                                </h2>
                                <div id="faq1" class="accordion-collapse collapse show" data-bs-parent="#faqAccordion">
                                    <div class="accordion-body">
                                        Oui, vous pouvez upgrader votre compte à tout moment. L'upgrade est immédiat et vous donnera accès à toutes les fonctionnalités du nouveau plan.
                                    </div>
                                </div>
                            </div>
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
                                        Que se passe-t-il avec mes données ?
                                    </button>
                                </h2>
                                <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                                    <div class="accordion-body">
                                        Toutes vos données sont sécurisées et sauvegardées. Quand vous upgradez, vous conservez tout votre historique et vos calculs précédents.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return get_base_template("Tarifs", "pricing") + content + get_footer()

# ============================================================================
# API DE CALCUL AVEC GESTION DES PERMISSIONS
# ============================================================================

@app.route('/calculate', methods=['POST'])
def calculate():
    """API de calcul avec gestion des permissions et limites"""
    try:
        data = request.get_json()
        
        # Vérification de l'authentification pour les limites
        user = None
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])
        
        # Vérification des limites pour les utilisateurs standard
        if user and user['role'] == 'standard':
            if user['calculations_used'] >= 3:
                return jsonify({
                    'success': False, 
                    'error': 'Limite de calculs gratuits atteinte (3/3)',
                    'upgrade_needed': True
                })
        
        # Extraction des paramètres
        pair_symbol = data.get('pair_symbol', 'XAUUSD').upper()
        entry_price = float(data.get('entry_price', 0))
        stop_loss = float(data.get('stop_loss', 0))
        capital = float(data.get('capital', 20000))
        risk_percent = float(data.get('risk_percent', 0.5))
        
        # Calcul des pips de stop loss
        sl_pips = calculate_pips(entry_price, stop_loss, pair_symbol)
        
        # Calcul de la taille de lot
        result = calculate_lot_size(sl_pips, capital, risk_percent, pair_symbol)
        
        if result['success'] and user:
            # Mise à jour du compteur pour les utilisateurs connectés
            update_user_calculations(user['id'])
            save_calculation(user['id'], pair_symbol, result['lot_size'], result['risk_usd'], capital, risk_percent)
            
            # Information sur l'utilisation
            if user['role'] == 'standard':
                remaining = max(0, 2 - user['calculations_used'])  # -1 car on vient d'utiliser un calcul
                result['usage_info'] = f"Calcul {user['calculations_used'] + 1}/3 utilisé. Encore {remaining} calcul(s) gratuit(s)."
                if remaining == 0:
                    result['usage_info'] += " Passez à Premium pour un accès illimité !"
                    result['reload_needed'] = True
            else:
                result['usage_info'] = f"Calcul illimité - Statut: {user['role'].upper()}"
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# ROUTES UTILITAIRES
# ============================================================================

@app.route('/health')
def health():
    """Point de contrôle santé avec informations d'authentification"""
    return jsonify({
        'status': 'healthy',
        'version': 'auth-1.0',
        'database': 'sqlite',
        'authentication': 'bcrypt',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 MindTraderPro - Système d'Authentification Complet")
    print("✅ Base de données SQLite initialisée")
    print("✅ Authentification sécurisée avec bcrypt")
    print("✅ Gestion des rôles: Standard, Premium, Lifetime")
    print("✅ Navigation dynamique selon l'authentification")
    print("✅ Système de permissions par fonctionnalité")
    print("✅ Prêt à l'utilisation !")
    app.run(host='0.0.0.0', port=5000, debug=True)