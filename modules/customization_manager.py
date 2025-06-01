"""
Customization Manager - Module de personnalisation visuelle
Permet aux utilisateurs de personnaliser leur expérience visuelle dans MindTraderPro
"""

import sqlite3
import json
from datetime import datetime

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# CONFIGURATION DES THÈMES ET ASSETS
# ============================================================================

# Thèmes disponibles pour tous les utilisateurs
AVAILABLE_THEMES = {
    'light': {
        'name': 'Clair',
        'description': 'Thème classique avec arrière-plan clair',
        'css_class': 'theme-light',
        'preview_color': '#ffffff',
        'icon': 'fas fa-sun'
    },
    'dark': {
        'name': 'Sombre',
        'description': 'Thème sombre pour réduire la fatigue oculaire',
        'css_class': 'theme-dark',
        'preview_color': '#212529',
        'icon': 'fas fa-moon'
    },
    'trading_green': {
        'name': 'Trading Vert',
        'description': 'Thème inspiré des plateformes de trading traditionnelles',
        'css_class': 'theme-trading-green',
        'preview_color': '#198754',
        'icon': 'fas fa-chart-line'
    },
    'crypto_neon': {
        'name': 'Crypto Néon',
        'description': 'Thème futuriste avec accents néon pour crypto',
        'css_class': 'theme-crypto-neon',
        'preview_color': '#6f42c1',
        'icon': 'fab fa-bitcoin'
    },
    'minimalist': {
        'name': 'Minimaliste',
        'description': 'Design épuré et moderne',
        'css_class': 'theme-minimalist',
        'preview_color': '#6c757d',
        'icon': 'fas fa-circle'
    }
}

# Thèmes premium exclusifs
PREMIUM_THEMES = {
    'dark_crystal': {
        'name': 'Crystal Sombre',
        'description': 'Thème premium avec effets cristallins',
        'css_class': 'theme-dark-crystal',
        'preview_color': '#0d1117',
        'icon': 'fas fa-gem',
        'premium_only': True
    },
    'fx_metal': {
        'name': 'FX Metal',
        'description': 'Thème métallique pour traders professionnels',
        'css_class': 'theme-fx-metal',
        'preview_color': '#495057',
        'icon': 'fas fa-coins',
        'premium_only': True
    }
}

# Avatars de base disponibles pour tous
BASE_AVATARS = {
    'trader_1': {'name': 'Trader Classique', 'icon': 'fas fa-user-tie', 'color': '#007bff'},
    'trader_2': {'name': 'Analyste', 'icon': 'fas fa-chart-bar', 'color': '#28a745'},
    'trader_3': {'name': 'Investisseur', 'icon': 'fas fa-briefcase', 'color': '#ffc107'},
    'trader_4': {'name': 'Day Trader', 'icon': 'fas fa-bolt', 'color': '#dc3545'},
    'trader_5': {'name': 'Swing Trader', 'icon': 'fas fa-wave-square', 'color': '#6f42c1'},
    'generic_1': {'name': 'Profil Standard', 'icon': 'fas fa-user', 'color': '#6c757d'},
    'generic_2': {'name': 'Expert Finance', 'icon': 'fas fa-graduation-cap', 'color': '#17a2b8'},
    'generic_3': {'name': 'Entrepreneur', 'icon': 'fas fa-rocket', 'color': '#fd7e14'}
}

# Avatars premium exclusifs
PREMIUM_AVATARS = {
    'vip_trader': {'name': 'VIP Trader', 'icon': 'fas fa-crown', 'color': '#ffd700', 'premium_only': True},
    'crypto_king': {'name': 'Crypto King', 'icon': 'fab fa-ethereum', 'color': '#6f42c1', 'premium_only': True},
    'fx_master': {'name': 'FX Master', 'icon': 'fas fa-chess-king', 'color': '#198754', 'premium_only': True},
    'diamond_hands': {'name': 'Diamond Hands', 'icon': 'far fa-gem', 'color': '#e83e8c', 'premium_only': True},
    'wolf_street': {'name': 'Wolf of Street', 'icon': 'fas fa-wolf-pack-battalion', 'color': '#dc3545', 'premium_only': True},
    'quant_genius': {'name': 'Quant Genius', 'icon': 'fas fa-brain', 'color': '#20c997', 'premium_only': True},
    'market_wizard': {'name': 'Market Wizard', 'icon': 'fas fa-magic', 'color': '#6610f2', 'premium_only': True},
    'algo_trader': {'name': 'Algo Trader', 'icon': 'fas fa-robot', 'color': '#fd7e14', 'premium_only': True},
    'hedge_lord': {'name': 'Hedge Lord', 'icon': 'fas fa-chess-queen', 'color': '#495057', 'premium_only': True},
    'bull_legend': {'name': 'Bull Legend', 'icon': 'fas fa-bullhorn', 'color': '#28a745', 'premium_only': True}
}

# Cadres d'avatar selon le rôle
AVATAR_FRAMES = {
    'standard': {
        'simple': {'name': 'Cadre Simple', 'css_class': 'frame-simple', 'color': '#dee2e6'}
    },
    'premium': {
        'gold_basic': {'name': 'Cadre Or', 'css_class': 'frame-gold-basic', 'color': '#ffd700'},
        'gold_shine': {'name': 'Or Brillant', 'css_class': 'frame-gold-shine', 'color': '#ffed4e', 'animated': True},
        'premium_glow': {'name': 'Lueur Premium', 'css_class': 'frame-premium-glow', 'color': '#ffc107', 'animated': True}
    },
    'lifetime': {
        'diamond_basic': {'name': 'Cadre Diamant', 'css_class': 'frame-diamond-basic', 'color': '#e3f2fd'},
        'diamond_sparkle': {'name': 'Diamant Étincelles', 'css_class': 'frame-diamond-sparkle', 'color': '#b3e5fc', 'animated': True},
        'rainbow_elite': {'name': 'Elite Arc-en-ciel', 'css_class': 'frame-rainbow-elite', 'color': 'linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57)', 'animated': True},
        'cosmic_legend': {'name': 'Légende Cosmique', 'css_class': 'frame-cosmic-legend', 'color': '#667eea', 'animated': True}
    }
}

# ============================================================================
# GESTION DES PRÉFÉRENCES UTILISATEUR
# ============================================================================

def get_user_customization(user_id):
    """
    Récupère les préférences de personnalisation d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Préférences de personnalisation
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT theme, avatar, avatar_frame, custom_settings
            FROM user_customization 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            custom_settings = {}
            if result[3]:
                try:
                    custom_settings = json.loads(result[3])
                except:
                    custom_settings = {}
            
            return {
                'theme': result[0] or 'dark',
                'avatar': result[1] or 'trader_1',
                'avatar_frame': result[2] or 'simple',
                'custom_settings': custom_settings
            }
        else:
            # Valeurs par défaut pour nouvel utilisateur
            return {
                'theme': 'dark',
                'avatar': 'trader_1',
                'avatar_frame': 'simple',
                'custom_settings': {}
            }
            
    except Exception as e:
        print(f"Erreur lors de la récupération des préférences: {e}")
        return {
            'theme': 'dark',
            'avatar': 'trader_1',
            'avatar_frame': 'simple',
            'custom_settings': {}
        }

def save_user_customization(user_id, theme=None, avatar=None, avatar_frame=None, custom_settings=None):
    """
    Sauvegarde les préférences de personnalisation d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        theme (str): Thème choisi
        avatar (str): Avatar choisi
        avatar_frame (str): Cadre d'avatar choisi
        custom_settings (dict): Paramètres personnalisés supplémentaires
    
    Returns:
        dict: Résultat de la sauvegarde
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des préférences actuelles
        current_prefs = get_user_customization(user_id)
        
        # Mise à jour des valeurs fournies
        if theme is not None:
            current_prefs['theme'] = theme
        if avatar is not None:
            current_prefs['avatar'] = avatar
        if avatar_frame is not None:
            current_prefs['avatar_frame'] = avatar_frame
        if custom_settings is not None:
            current_prefs['custom_settings'].update(custom_settings)
        
        # Sauvegarde en base
        cursor.execute('''
            INSERT OR REPLACE INTO user_customization 
            (user_id, theme, avatar, avatar_frame, custom_settings, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_id,
            current_prefs['theme'],
            current_prefs['avatar'],
            current_prefs['avatar_frame'],
            json.dumps(current_prefs['custom_settings'])
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': 'Préférences sauvegardées avec succès',
            'preferences': current_prefs
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur lors de la sauvegarde: {str(e)}'
        }

def get_available_options(user_role):
    """
    Récupère les options de personnalisation disponibles selon le rôle utilisateur
    
    Args:
        user_role (str): Rôle de l'utilisateur ('standard', 'premium', 'lifetime', 'admin')
    
    Returns:
        dict: Options disponibles
    """
    try:
        # Thèmes de base pour tous
        available_themes = AVAILABLE_THEMES.copy()
        
        # Avatars de base pour tous
        available_avatars = BASE_AVATARS.copy()
        
        # Cadres selon le rôle
        available_frames = AVATAR_FRAMES['standard'].copy()
        
        # Ajout des options premium
        if user_role in ['premium', 'lifetime', 'admin']:
            available_themes.update(PREMIUM_THEMES)
            available_avatars.update(PREMIUM_AVATARS)
            available_frames.update(AVATAR_FRAMES['premium'])
        
        # Ajout des options lifetime
        if user_role in ['lifetime', 'admin']:
            available_frames.update(AVATAR_FRAMES['lifetime'])
        
        return {
            'themes': available_themes,
            'avatars': available_avatars,
            'frames': available_frames,
            'user_role': user_role
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des options: {e}")
        return {
            'themes': AVAILABLE_THEMES,
            'avatars': BASE_AVATARS,
            'frames': AVATAR_FRAMES['standard'],
            'user_role': 'standard'
        }

def generate_user_profile_card(user_id, username, user_role, preferences=None):
    """
    Génère le HTML d'une carte de profil utilisateur personnalisée
    
    Args:
        user_id (int): ID de l'utilisateur
        username (str): Nom d'utilisateur
        user_role (str): Rôle de l'utilisateur
        preferences (dict): Préférences de personnalisation (optionnel)
    
    Returns:
        str: HTML de la carte de profil
    """
    try:
        # Récupération des préférences si non fournies
        if not preferences:
            preferences = get_user_customization(user_id)
        
        # Récupération des infos d'avatar
        all_avatars = {**BASE_AVATARS, **PREMIUM_AVATARS}
        avatar_info = all_avatars.get(preferences['avatar'], BASE_AVATARS['trader_1'])
        
        # Récupération des infos de cadre
        all_frames = {}
        for role_frames in AVATAR_FRAMES.values():
            all_frames.update(role_frames)
        frame_info = all_frames.get(preferences['avatar_frame'], AVATAR_FRAMES['standard']['simple'])
        
        # Badge de rôle
        role_badges = {
            'standard': {'text': 'Standard', 'class': 'bg-secondary'},
            'premium': {'text': 'Premium', 'class': 'bg-warning text-dark'},
            'lifetime': {'text': 'Lifetime', 'class': 'bg-primary'},
            'admin': {'text': 'Admin', 'class': 'bg-danger'}
        }
        role_badge = role_badges.get(user_role, role_badges['standard'])
        
        # Animation CSS pour les cadres animés
        animation_class = 'animated-frame' if frame_info.get('animated') else ''
        
        profile_card_html = f'''
        <div class="profile-card {preferences['theme']}-theme" style="max-width: 300px;">
            <div class="card">
                <div class="card-body text-center">
                    <!-- Avatar avec cadre personnalisé -->
                    <div class="avatar-container {frame_info['css_class']} {animation_class}" style="position: relative; display: inline-block; margin-bottom: 15px;">
                        <div class="avatar-circle" style="
                            width: 80px; 
                            height: 80px; 
                            border-radius: 50%; 
                            background: {avatar_info['color']}; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center;
                            font-size: 2rem;
                            color: white;
                            border: 3px solid {frame_info['color']};
                        ">
                            <i class="{avatar_info['icon']}"></i>
                        </div>
                    </div>
                    
                    <!-- Nom d'utilisateur -->
                    <h5 class="card-title mb-2">{username}</h5>
                    
                    <!-- Badge de rôle -->
                    <span class="badge {role_badge['class']} mb-3">{role_badge['text']}</span>
                    
                    <!-- Informations supplémentaires -->
                    <div class="user-stats">
                        <small class="text-muted">
                            <i class="fas fa-palette me-1"></i>
                            Thème: {AVAILABLE_THEMES.get(preferences['theme'], PREMIUM_THEMES.get(preferences['theme'], {'name': 'Inconnu'}))['name']}
                        </small>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return profile_card_html
        
    except Exception as e:
        return f'<div class="alert alert-danger">Erreur lors de la génération du profil: {str(e)}</div>'

def get_customization_statistics():
    """
    Récupère les statistiques d'utilisation de la personnalisation
    
    Returns:
        dict: Statistiques de personnalisation
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Utilisateurs ayant personnalisé leur profil
        cursor.execute('SELECT COUNT(*) FROM user_customization')
        customized_users = cursor.fetchone()[0]
        
        # Thèmes les plus populaires
        cursor.execute('''
            SELECT theme, COUNT(*) as count 
            FROM user_customization 
            GROUP BY theme 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_themes = cursor.fetchall()
        
        # Avatars les plus populaires
        cursor.execute('''
            SELECT avatar, COUNT(*) as count 
            FROM user_customization 
            GROUP BY avatar 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_avatars = cursor.fetchall()
        
        # Répartition par rôle des utilisateurs ayant personnalisé
        cursor.execute('''
            SELECT u.role, COUNT(uc.user_id) as count
            FROM users u
            LEFT JOIN user_customization uc ON u.id = uc.user_id
            WHERE uc.user_id IS NOT NULL
            GROUP BY u.role
        ''')
        role_distribution = cursor.fetchall()
        
        conn.close()
        
        return {
            'customized_users': customized_users,
            'popular_themes': popular_themes,
            'popular_avatars': popular_avatars,
            'role_distribution': role_distribution
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

def generate_theme_css(theme_name):
    """
    Génère le CSS personnalisé pour un thème spécifique
    
    Args:
        theme_name (str): Nom du thème
    
    Returns:
        str: CSS du thème
    """
    theme_styles = {
        'light': '''
            .theme-light { background-color: #ffffff; color: #212529; }
            .theme-light .card { background-color: #f8f9fa; border: 1px solid #dee2e6; }
            .theme-light .btn-primary { background-color: #0d6efd; }
        ''',
        'dark': '''
            .theme-dark { background-color: #212529; color: #ffffff; }
            .theme-dark .card { background-color: #343a40; border: 1px solid #495057; }
            .theme-dark .btn-primary { background-color: #0d6efd; }
        ''',
        'trading_green': '''
            .theme-trading-green { background-color: #0d2818; color: #ffffff; }
            .theme-trading-green .card { background-color: #198754; border: 1px solid #20c997; }
            .theme-trading-green .btn-primary { background-color: #20c997; }
        ''',
        'crypto_neon': '''
            .theme-crypto-neon { background-color: #1a0033; color: #e0e0ff; }
            .theme-crypto-neon .card { background-color: #6f42c1; border: 1px solid #e83e8c; }
            .theme-crypto-neon .btn-primary { background-color: #e83e8c; }
        ''',
        'minimalist': '''
            .theme-minimalist { background-color: #f5f5f5; color: #333333; }
            .theme-minimalist .card { background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .theme-minimalist .btn-primary { background-color: #6c757d; }
        ''',
        'dark_crystal': '''
            .theme-dark-crystal { background-color: #0d1117; color: #c9d1d9; }
            .theme-dark-crystal .card { background-color: #161b22; border: 1px solid #30363d; box-shadow: 0 0 10px rgba(79, 172, 254, 0.3); }
            .theme-dark-crystal .btn-primary { background-color: #4fc3f7; }
        ''',
        'fx_metal': '''
            .theme-fx-metal { background-color: #2c2c2c; color: #e0e0e0; }
            .theme-fx-metal .card { background-color: #3c3c3c; border: 1px solid #666666; background-image: linear-gradient(45deg, #3c3c3c 25%, #4a4a4a 25%, #4a4a4a 50%, #3c3c3c 50%); }
            .theme-fx-metal .btn-primary { background-color: #ffc107; color: #000; }
        '''
    }
    
    # CSS pour les animations de cadres
    animations_css = '''
        @keyframes frameGlow {
            0% { box-shadow: 0 0 5px currentColor; }
            50% { box-shadow: 0 0 20px currentColor; }
            100% { box-shadow: 0 0 5px currentColor; }
        }
        
        @keyframes frameSparkle {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes rainbowShift {
            0% { border-color: #ff6b6b; }
            25% { border-color: #4ecdc4; }
            50% { border-color: #45b7d1; }
            75% { border-color: #96ceb4; }
            100% { border-color: #feca57; }
        }
        
        .animated-frame.frame-gold-shine { animation: frameGlow 2s ease-in-out infinite; }
        .animated-frame.frame-premium-glow { animation: frameGlow 1.5s ease-in-out infinite; }
        .animated-frame.frame-diamond-sparkle { animation: frameSparkle 3s linear infinite; }
        .animated-frame.frame-rainbow-elite { animation: rainbowShift 2s ease-in-out infinite; }
        .animated-frame.frame-cosmic-legend { 
            animation: frameGlow 2s ease-in-out infinite, frameSparkle 4s linear infinite; 
            background: linear-gradient(45deg, #667eea, #764ba2);
        }
    '''
    
    return theme_styles.get(theme_name, '') + animations_css

# ============================================================================
# INITIALISATION DES TABLES PERSONNALISATION
# ============================================================================

def init_customization_tables():
    """
    Initialise les tables nécessaires pour la personnalisation
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table de personnalisation utilisateur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_customization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                theme TEXT DEFAULT 'dark',
                avatar TEXT DEFAULT 'trader_1',
                avatar_frame TEXT DEFAULT 'simple',
                custom_settings TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_customization_user_id ON user_customization(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_customization_theme ON user_customization(theme)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables personnalisation initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables personnalisation: {e}")

# Initialisation automatique des tables
init_customization_tables()