"""
Grade Manager - Module de gestion des grades utilisateurs avec XP évolutif
Système complet de progression des utilisateurs dans MindTraderPro
"""

import sqlite3
import json
from datetime import datetime, timedelta

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# CONFIGURATION DES GRADES PAR DÉFAUT
# ============================================================================

DEFAULT_GRADES = {
    'debutant': {
        'name': 'Débutant',
        'xp_threshold': 0,
        'icon': '🌱',
        'color': '#6c757d',
        'description': 'Nouveau trader en apprentissage',
        'is_fixed': False,
        'advantages': 'Accès aux fonctionnalités de base, guides pour débutants'
    },
    'actif': {
        'name': 'Actif',
        'xp_threshold': 51,
        'icon': '⚡',
        'color': '#0d6efd',
        'description': 'Trader actif qui utilise régulièrement la plateforme',
        'is_fixed': False,
        'advantages': 'Accès aux statistiques avancées, historique étendu'
    },
    'trader_regulier': {
        'name': 'Trader Régulier',
        'xp_threshold': 201,
        'icon': '📈',
        'color': '#198754',
        'description': 'Trader expérimenté avec une activité soutenue',
        'is_fixed': False,
        'advantages': 'Accès aux analyses techniques, alertes personnalisées'
    },
    'expert': {
        'name': 'Expert',
        'xp_threshold': 501,
        'icon': '🏆',
        'color': '#ffc107',
        'description': 'Trader expert maîtrisant les stratégies avancées',
        'is_fixed': False,
        'advantages': 'Accès aux outils professionnels, analyses approfondies'
    },
    'legende': {
        'name': 'Légende',
        'xp_threshold': 1001,
        'icon': '👑',
        'color': '#dc3545',
        'description': 'Trader légendaire au sommet de son art',
        'is_fixed': False,
        'advantages': 'Accès complet, reconnaissance communautaire, mentoring'
    },
    'lifetime': {
        'name': 'Lifetime VIP',
        'xp_threshold': 0,
        'icon': '💎',
        'color': '#6f42c1',
        'description': 'Utilisateur Lifetime avec accès privilégié permanent',
        'is_fixed': True,
        'advantages': 'Tous les avantages + fonctionnalités exclusives + support prioritaire'
    }
}

# Configuration des actions XP par défaut
DEFAULT_XP_RULES = {
    'calculator_used': {
        'name': 'Utilisation du calculateur',
        'xp_value': 5,
        'description': 'Utiliser le calculateur de lot',
        'is_active': True,
        'daily_limit': 10  # Maximum 10 fois par jour
    },
    'trade_added': {
        'name': 'Trade ajouté au journal',
        'xp_value': 10,
        'description': 'Ajouter un trade dans le journal',
        'is_active': True,
        'daily_limit': 20
    },
    'suggestion_sent': {
        'name': 'Suggestion envoyée',
        'xp_value': 20,
        'description': 'Proposer une nouvelle suggestion',
        'is_active': True,
        'daily_limit': 5
    },
    'vote_cast': {
        'name': 'Vote sur suggestion',
        'xp_value': 3,
        'description': 'Voter pour une suggestion',
        'is_active': True,
        'daily_limit': 50
    },
    'daily_login': {
        'name': 'Connexion quotidienne',
        'xp_value': 2,
        'description': 'Se connecter chaque jour',
        'is_active': True,
        'daily_limit': 1
    },
    'profile_customized': {
        'name': 'Personnalisation du profil',
        'xp_value': 15,
        'description': 'Personnaliser son profil utilisateur',
        'is_active': True,
        'daily_limit': 1
    },
    'contribution_made': {
        'name': 'Contribution Lifetime',
        'xp_value': 50,
        'description': 'Faire une contribution Lifetime',
        'is_active': True,
        'daily_limit': 3
    }
}

# ============================================================================
# GESTION DES GRADES UTILISATEURS
# ============================================================================

def get_user_grade_info(user_id):
    """
    Récupère les informations complètes de grade d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Informations de grade et XP
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des données utilisateur
        cursor.execute('SELECT username, role, xp, current_grade FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return None
        
        username, role, xp, current_grade = user_data
        xp = xp or 0
        
        # Récupération des informations du grade actuel
        cursor.execute('SELECT * FROM user_grades WHERE grade_key = ?', (current_grade or 'debutant',))
        grade_data = cursor.fetchone()
        
        if not grade_data:
            # Utiliser le grade par défaut
            grade_info = DEFAULT_GRADES['debutant'].copy()
            grade_info['grade_key'] = 'debutant'
        else:
            grade_info = {
                'grade_key': grade_data[1],
                'name': grade_data[2],
                'xp_threshold': grade_data[3],
                'icon': grade_data[4],
                'color': grade_data[5],
                'description': grade_data[6],
                'is_fixed': bool(grade_data[7]),
                'advantages': grade_data[8]
            }
        
        # Calcul du grade suivant et progression
        next_grade = get_next_grade(xp, role)
        progress_to_next = 0
        xp_needed = 0
        
        if next_grade and not grade_info['is_fixed']:
            xp_needed = next_grade['xp_threshold'] - xp
            if next_grade['xp_threshold'] > grade_info['xp_threshold']:
                progress_range = next_grade['xp_threshold'] - grade_info['xp_threshold']
                current_progress = xp - grade_info['xp_threshold']
                progress_to_next = min(100, max(0, (current_progress / progress_range) * 100))
        
        conn.close()
        
        return {
            'user_info': {
                'username': username,
                'role': role,
                'xp': xp
            },
            'current_grade': grade_info,
            'next_grade': next_grade,
            'progress_to_next': progress_to_next,
            'xp_needed': max(0, xp_needed)
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération du grade: {e}")
        return None

def get_next_grade(current_xp, user_role):
    """
    Détermine le prochain grade disponible pour un utilisateur
    
    Args:
        current_xp (int): XP actuel de l'utilisateur
        user_role (str): Rôle de l'utilisateur
    
    Returns:
        dict: Informations du prochain grade ou None
    """
    try:
        # Les utilisateurs Lifetime ont un grade fixe
        if user_role == 'lifetime':
            return None
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération du prochain grade disponible
        cursor.execute('''
            SELECT * FROM user_grades 
            WHERE xp_threshold > ? AND is_fixed = 0
            ORDER BY xp_threshold ASC 
            LIMIT 1
        ''', (current_xp,))
        
        next_grade_data = cursor.fetchone()
        conn.close()
        
        if next_grade_data:
            return {
                'grade_key': next_grade_data[1],
                'name': next_grade_data[2],
                'xp_threshold': next_grade_data[3],
                'icon': next_grade_data[4],
                'color': next_grade_data[5],
                'description': next_grade_data[6],
                'is_fixed': bool(next_grade_data[7]),
                'advantages': next_grade_data[8]
            }
        
        return None
        
    except Exception as e:
        print(f"Erreur lors de la recherche du prochain grade: {e}")
        return None

def update_user_grade(user_id, force_check=False):
    """
    Met à jour automatiquement le grade d'un utilisateur selon son XP
    
    Args:
        user_id (int): ID de l'utilisateur
        force_check (bool): Forcer la vérification même pour les grades fixes
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des données utilisateur
        cursor.execute('SELECT role, xp, current_grade FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        role, xp, current_grade = user_data
        xp = xp or 0
        
        # Utilisateurs Lifetime : garde leur grade spécial
        if role == 'lifetime' and not force_check:
            if current_grade != 'lifetime':
                cursor.execute('UPDATE users SET current_grade = ? WHERE id = ?', ('lifetime', user_id))
                conn.commit()
            conn.close()
            return {'success': True, 'grade_changed': True, 'new_grade': 'lifetime'}
        
        # Recherche du grade approprié selon l'XP
        cursor.execute('''
            SELECT grade_key, name FROM user_grades 
            WHERE xp_threshold <= ? AND is_fixed = 0
            ORDER BY xp_threshold DESC 
            LIMIT 1
        ''', (xp,))
        
        appropriate_grade = cursor.fetchone()
        
        if not appropriate_grade:
            # Utiliser le grade débutant par défaut
            new_grade = 'debutant'
            new_grade_name = 'Débutant'
        else:
            new_grade, new_grade_name = appropriate_grade
        
        # Mise à jour si le grade a changé
        grade_changed = current_grade != new_grade
        
        if grade_changed:
            cursor.execute('UPDATE users SET current_grade = ? WHERE id = ?', (new_grade, user_id))
            
            # Log du changement de grade
            cursor.execute('''
                INSERT INTO user_xp_logs (user_id, action_type, xp_change, description, created_at)
                VALUES (?, 'grade_change', 0, ?, CURRENT_TIMESTAMP)
            ''', (user_id, f'Grade changé vers: {new_grade_name}'))
            
            conn.commit()
        
        conn.close()
        
        return {
            'success': True,
            'grade_changed': grade_changed,
            'new_grade': new_grade,
            'new_grade_name': new_grade_name
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour du grade: {str(e)}'}

# ============================================================================
# GESTION DE L'XP UTILISATEUR
# ============================================================================

def add_user_xp(user_id, action_type, xp_amount=None, description=None):
    """
    Ajoute de l'XP à un utilisateur pour une action spécifique
    
    Args:
        user_id (int): ID de l'utilisateur
        action_type (str): Type d'action effectuée
        xp_amount (int): Montant d'XP personnalisé (optionnel)
        description (str): Description personnalisée (optionnelle)
    
    Returns:
        dict: Résultat de l'ajout d'XP
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération de la règle XP
        cursor.execute('SELECT * FROM xp_rules WHERE rule_key = ? AND is_active = 1', (action_type,))
        rule_data = cursor.fetchone()
        
        if not rule_data and not xp_amount:
            conn.close()
            return {'success': False, 'error': 'Règle XP non trouvée ou inactive'}
        
        # Utilisation de l'XP de la règle ou de l'XP personnalisé
        if xp_amount is None:
            xp_to_add = rule_data[3]  # xp_value
            rule_name = rule_data[2]  # name
            daily_limit = rule_data[5]  # daily_limit
        else:
            xp_to_add = xp_amount
            rule_name = description or action_type
            daily_limit = None
        
        # Vérification de la limite quotidienne
        if daily_limit:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM user_xp_logs 
                WHERE user_id = ? AND action_type = ? AND DATE(created_at) = ?
            ''', (user_id, action_type, today))
            
            today_count = cursor.fetchone()[0]
            
            if today_count >= daily_limit:
                conn.close()
                return {
                    'success': False, 
                    'error': f'Limite quotidienne atteinte pour cette action ({daily_limit} fois)'
                }
        
        # Ajout de l'XP à l'utilisateur
        cursor.execute('SELECT xp FROM users WHERE id = ?', (user_id,))
        current_xp = cursor.fetchone()
        
        if not current_xp:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        new_xp = (current_xp[0] or 0) + xp_to_add
        
        cursor.execute('UPDATE users SET xp = ? WHERE id = ?', (new_xp, user_id))
        
        # Log de l'action XP
        log_description = description or f'{rule_name} (+{xp_to_add} XP)'
        cursor.execute('''
            INSERT INTO user_xp_logs (user_id, action_type, xp_change, description, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, action_type, xp_to_add, log_description))
        
        conn.commit()
        conn.close()
        
        # Vérification et mise à jour du grade
        grade_update = update_user_grade(user_id)
        
        return {
            'success': True,
            'xp_added': xp_to_add,
            'new_total_xp': new_xp,
            'description': log_description,
            'grade_changed': grade_update.get('grade_changed', False),
            'new_grade': grade_update.get('new_grade_name') if grade_update.get('grade_changed') else None
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'ajout d\'XP: {str(e)}'}

def get_user_xp_history(user_id, limit=50, offset=0):
    """
    Récupère l'historique des actions XP d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        limit (int): Nombre d'entrées à récupérer
        offset (int): Décalage pour la pagination
    
    Returns:
        list: Historique des actions XP
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, xp_change, description, created_at
            FROM user_xp_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        history = cursor.fetchall()
        conn.close()
        
        return [
            {
                'action_type': record[0],
                'xp_change': record[1],
                'description': record[2],
                'created_at': record[3]
            }
            for record in history
        ]
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique XP: {e}")
        return []

# ============================================================================
# GESTION ADMINISTRATIVE DES GRADES
# ============================================================================

def get_all_users_grades(limit=100, offset=0, sort_by='xp_desc'):
    """
    Récupère la liste de tous les utilisateurs avec leurs grades et XP
    
    Args:
        limit (int): Nombre d'utilisateurs à récupérer
        offset (int): Décalage pour la pagination
        sort_by (str): Tri ('xp_desc', 'xp_asc', 'grade', 'username')
    
    Returns:
        list: Liste des utilisateurs avec informations de grade
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête avec tri
        sort_clauses = {
            'xp_desc': 'u.xp DESC',
            'xp_asc': 'u.xp ASC',
            'grade': 'ug.name ASC',
            'username': 'u.username ASC'
        }
        
        sort_clause = sort_clauses.get(sort_by, 'u.xp DESC')
        
        cursor.execute(f'''
            SELECT u.id, u.username, u.role, u.xp, u.current_grade, u.created_at,
                   ug.name as grade_name, ug.icon, ug.color
            FROM users u
            LEFT JOIN user_grades ug ON u.current_grade = ug.grade_key
            ORDER BY {sort_clause}
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'xp': user[3] or 0,
                'current_grade': user[4] or 'debutant',
                'created_at': user[5],
                'grade_name': user[6] or 'Débutant',
                'grade_icon': user[7] or '🌱',
                'grade_color': user[8] or '#6c757d'
            }
            for user in users
        ]
        
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
        return []

def manually_adjust_user_xp(user_id, xp_change, admin_id, reason):
    """
    Ajuste manuellement l'XP d'un utilisateur (admin uniquement)
    
    Args:
        user_id (int): ID de l'utilisateur
        xp_change (int): Changement d'XP (positif ou négatif)
        admin_id (int): ID de l'administrateur
        reason (str): Raison de l'ajustement
    
    Returns:
        dict: Résultat de l'ajustement
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération de l'XP actuel
        cursor.execute('SELECT username, xp FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        username, current_xp = user_data
        current_xp = current_xp or 0
        new_xp = max(0, current_xp + xp_change)  # L'XP ne peut pas être négatif
        
        # Mise à jour de l'XP
        cursor.execute('UPDATE users SET xp = ? WHERE id = ?', (new_xp, user_id))
        
        # Log de l'action administrative
        cursor.execute('''
            INSERT INTO user_xp_logs (user_id, action_type, xp_change, description, created_at)
            VALUES (?, 'admin_adjustment', ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, xp_change, f'Ajustement admin: {reason}'))
        
        # Log administratif
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'xp_adjustment', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_id, user_id, f'XP ajusté de {xp_change} pour {username}: {reason}'))
        
        conn.commit()
        conn.close()
        
        # Mise à jour du grade
        grade_update = update_user_grade(user_id)
        
        return {
            'success': True,
            'old_xp': current_xp,
            'new_xp': new_xp,
            'xp_change': xp_change,
            'grade_changed': grade_update.get('grade_changed', False),
            'new_grade': grade_update.get('new_grade_name') if grade_update.get('grade_changed') else None
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'ajustement: {str(e)}'}

def manually_set_user_grade(user_id, new_grade_key, admin_id, reason):
    """
    Change manuellement le grade d'un utilisateur (admin uniquement)
    
    Args:
        user_id (int): ID de l'utilisateur
        new_grade_key (str): Clé du nouveau grade
        admin_id (int): ID de l'administrateur
        reason (str): Raison du changement
    
    Returns:
        dict: Résultat du changement
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que le grade existe
        cursor.execute('SELECT name FROM user_grades WHERE grade_key = ?', (new_grade_key,))
        grade_data = cursor.fetchone()
        
        if not grade_data:
            conn.close()
            return {'success': False, 'error': 'Grade non trouvé'}
        
        # Récupération des données utilisateur
        cursor.execute('SELECT username, current_grade FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        username, old_grade = user_data
        grade_name = grade_data[0]
        
        # Mise à jour du grade
        cursor.execute('UPDATE users SET current_grade = ? WHERE id = ?', (new_grade_key, user_id))
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO user_xp_logs (user_id, action_type, xp_change, description, created_at)
            VALUES (?, 'grade_manual_change', 0, ?, CURRENT_TIMESTAMP)
        ''', (user_id, f'Grade changé manuellement vers: {grade_name} - Raison: {reason}'))
        
        # Log administratif
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'grade_manual_change', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_id, user_id, f'Grade de {username} changé de {old_grade} vers {new_grade_key}: {reason}'))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'old_grade': old_grade,
            'new_grade': new_grade_key,
            'new_grade_name': grade_name
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors du changement de grade: {str(e)}'}

def get_grade_statistics():
    """
    Récupère les statistiques globales des grades
    
    Returns:
        dict: Statistiques complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Nombre d'utilisateurs par grade
        cursor.execute('''
            SELECT ug.name, ug.icon, ug.color, COUNT(u.id) as user_count
            FROM user_grades ug
            LEFT JOIN users u ON ug.grade_key = u.current_grade
            GROUP BY ug.grade_key, ug.name, ug.icon, ug.color
            ORDER BY ug.xp_threshold ASC
        ''')
        grade_distribution = cursor.fetchall()
        
        # XP moyen global
        cursor.execute('SELECT AVG(xp) FROM users WHERE xp IS NOT NULL')
        avg_xp = cursor.fetchone()[0] or 0
        
        # XP total distribué
        cursor.execute('SELECT SUM(xp) FROM users WHERE xp IS NOT NULL')
        total_xp = cursor.fetchone()[0] or 0
        
        # Actions XP les plus fréquentes (derniers 30 jours)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT action_type, COUNT(*) as count, SUM(xp_change) as total_xp
            FROM user_xp_logs
            WHERE created_at >= ?
            GROUP BY action_type
            ORDER BY count DESC
            LIMIT 10
        ''', (thirty_days_ago,))
        top_actions = cursor.fetchall()
        
        # Évolution XP par jour (derniers 7 jours)
        cursor.execute('''
            SELECT DATE(created_at) as date, SUM(xp_change) as daily_xp
            FROM user_xp_logs
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''')
        daily_xp_evolution = cursor.fetchall()
        
        conn.close()
        
        return {
            'grade_distribution': [
                {
                    'name': grade[0],
                    'icon': grade[1],
                    'color': grade[2],
                    'user_count': grade[3]
                }
                for grade in grade_distribution
            ],
            'avg_xp': round(avg_xp, 2),
            'total_xp': total_xp,
            'top_actions': [
                {
                    'action_type': action[0],
                    'count': action[1],
                    'total_xp': action[2]
                }
                for action in top_actions
            ],
            'daily_xp_evolution': [
                {
                    'date': day[0],
                    'daily_xp': day[1]
                }
                for day in daily_xp_evolution
            ]
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

# ============================================================================
# INITIALISATION DES TABLES GRADES
# ============================================================================

def init_grade_tables():
    """
    Initialise les tables nécessaires pour le système de grades
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des grades disponibles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                xp_threshold INTEGER NOT NULL,
                icon TEXT NOT NULL,
                color TEXT NOT NULL,
                description TEXT,
                is_fixed BOOLEAN DEFAULT 0,
                advantages TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des règles d'XP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                xp_value INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                daily_limit INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des logs XP utilisateur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_xp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                xp_change INTEGER NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Ajout des colonnes XP et grade à la table users si elles n'existent pas
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Colonne déjà existante
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN current_grade TEXT DEFAULT "debutant"')
        except sqlite3.OperationalError:
            pass  # Colonne déjà existante
        
        # Insertion des grades par défaut
        for grade_key, grade_data in DEFAULT_GRADES.items():
            cursor.execute('''
                INSERT OR REPLACE INTO user_grades 
                (grade_key, name, xp_threshold, icon, color, description, is_fixed, advantages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                grade_key,
                grade_data['name'],
                grade_data['xp_threshold'],
                grade_data['icon'],
                grade_data['color'],
                grade_data['description'],
                grade_data['is_fixed'],
                grade_data['advantages']
            ))
        
        # Insertion des règles XP par défaut
        for rule_key, rule_data in DEFAULT_XP_RULES.items():
            cursor.execute('''
                INSERT OR REPLACE INTO xp_rules 
                (rule_key, name, xp_value, description, is_active, daily_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                rule_key,
                rule_data['name'],
                rule_data['xp_value'],
                rule_data['description'],
                rule_data['is_active'],
                rule_data['daily_limit']
            ))
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_xp_logs_user_id ON user_xp_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_xp_logs_created_at ON user_xp_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_grades_xp_threshold ON user_grades(xp_threshold)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables grades et XP initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables grades: {e}")

# ============================================================================
# GESTION DES NOTIFICATIONS UTILISATEUR
# ============================================================================

def create_user_notification(user_id, message, notification_type='grade_up'):
    """
    Crée une notification pour un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        message (str): Message de notification
        notification_type (str): Type de notification
    
    Returns:
        dict: Résultat de la création
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_notifications (user_id, message, notification_type, is_read, created_at)
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
        ''', (user_id, message, notification_type))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'notification_id': notification_id}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la création de notification: {str(e)}'}

def get_user_notifications(user_id, unread_only=False, limit=10):
    """
    Récupère les notifications d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        unread_only (bool): Seulement les non lues
        limit (int): Nombre de notifications
    
    Returns:
        list: Notifications de l'utilisateur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, message, notification_type, is_read, created_at
            FROM user_notifications
            WHERE user_id = ?
        '''
        params = [user_id]
        
        if unread_only:
            query += ' AND is_read = 0'
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': notif[0],
                'message': notif[1],
                'notification_type': notif[2],
                'is_read': bool(notif[3]),
                'created_at': notif[4]
            }
            for notif in notifications
        ]
        
    except Exception as e:
        print(f"Erreur lors de la récupération des notifications: {e}")
        return []

def mark_notification_as_read(notification_id, user_id):
    """
    Marque une notification comme lue
    
    Args:
        notification_id (int): ID de la notification
        user_id (int): ID de l'utilisateur pour vérification
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_notifications 
            SET is_read = 1 
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def get_unread_notifications_count(user_id):
    """
    Compte les notifications non lues d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        int: Nombre de notifications non lues
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_notifications 
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"Erreur lors du comptage des notifications: {e}")
        return 0

# ============================================================================
# SYSTÈME DE RÉCOMPENSES
# ============================================================================

# Configuration des récompenses par palier XP
REWARD_MILESTONES = {
    100: {
        'name': 'Avatar Spécial',
        'description': 'Débloquez un avatar exclusif pour 100 XP',
        'type': 'avatar',
        'value': 'special_trader'
    },
    300: {
        'name': 'Cadre Doré',
        'description': 'Un magnifique cadre doré pour votre profil',
        'type': 'frame',
        'value': 'golden_frame'
    },
    500: {
        'name': 'Thème Premium Crystal Sombre',
        'description': 'Accès au thème premium exclusif',
        'type': 'theme',
        'value': 'dark_crystal'
    },
    1000: {
        'name': 'Statut Légende + Bonus 50 XP',
        'description': 'Statut spécial et bonus XP immédiat',
        'type': 'status_bonus',
        'value': 50
    }
}

def check_and_unlock_rewards(user_id, current_xp):
    """
    Vérifie et débloque les récompenses selon l'XP
    
    Args:
        user_id (int): ID de l'utilisateur
        current_xp (int): XP actuel de l'utilisateur
    
    Returns:
        list: Nouvelles récompenses débloquées
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des récompenses déjà débloquées
        cursor.execute('SELECT reward_milestone FROM user_rewards WHERE user_id = ?', (user_id,))
        unlocked_milestones = {row[0] for row in cursor.fetchall()}
        
        new_rewards = []
        
        # Vérification de chaque palier
        for milestone, reward_data in REWARD_MILESTONES.items():
            if current_xp >= milestone and milestone not in unlocked_milestones:
                # Débloquer la récompense
                cursor.execute('''
                    INSERT INTO user_rewards (user_id, reward_milestone, reward_name, reward_type, reward_value, unlocked_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, milestone, reward_data['name'], reward_data['type'], reward_data['value']))
                
                new_rewards.append(reward_data)
                
                # Créer une notification
                create_user_notification(
                    user_id, 
                    f"🎁 Récompense débloquée: {reward_data['name']}! {reward_data['description']}", 
                    'reward_unlocked'
                )
                
                # Bonus XP spécial pour le palier légende
                if reward_data['type'] == 'status_bonus':
                    cursor.execute('UPDATE users SET xp = xp + ? WHERE id = ?', (reward_data['value'], user_id))
                    cursor.execute('''
                        INSERT INTO user_xp_logs (user_id, action_type, xp_change, description, created_at)
                        VALUES (?, 'reward_bonus', ?, 'Bonus XP Statut Légende', CURRENT_TIMESTAMP)
                    ''', (user_id, reward_data['value']))
        
        conn.commit()
        conn.close()
        
        return new_rewards
        
    except Exception as e:
        print(f"Erreur lors de la vérification des récompenses: {e}")
        return []

def get_user_rewards(user_id):
    """
    Récupère toutes les récompenses d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        list: Récompenses de l'utilisateur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT reward_milestone, reward_name, reward_type, reward_value, unlocked_at
            FROM user_rewards
            WHERE user_id = ?
            ORDER BY reward_milestone ASC
        ''', (user_id,))
        
        rewards = cursor.fetchall()
        conn.close()
        
        return [
            {
                'milestone': reward[0],
                'name': reward[1],
                'type': reward[2],
                'value': reward[3],
                'unlocked_at': reward[4]
            }
            for reward in rewards
        ]
        
    except Exception as e:
        print(f"Erreur lors de la récupération des récompenses: {e}")
        return []

def get_available_rewards(current_xp):
    """
    Récupère les récompenses disponibles et à venir
    
    Args:
        current_xp (int): XP actuel
    
    Returns:
        dict: Récompenses disponibles et à venir
    """
    available = []
    upcoming = []
    
    for milestone, reward_data in REWARD_MILESTONES.items():
        reward_info = {
            'milestone': milestone,
            'name': reward_data['name'],
            'description': reward_data['description'],
            'type': reward_data['type']
        }
        
        if current_xp >= milestone:
            available.append(reward_info)
        else:
            reward_info['xp_needed'] = milestone - current_xp
            upcoming.append(reward_info)
    
    return {'available': available, 'upcoming': upcoming}

# ============================================================================
# LEADERBOARD GLOBAL
# ============================================================================

def get_global_leaderboard(limit=20, sort_by='xp', role_filter=None):
    """
    Récupère le classement global des utilisateurs
    
    Args:
        limit (int): Nombre d'utilisateurs à récupérer
        sort_by (str): Tri ('xp', 'actions', 'date')
        role_filter (str): Filtrer par rôle
    
    Returns:
        list: Classement des utilisateurs
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête de base
        query = '''
            SELECT u.id, u.username, u.role, u.xp, u.current_grade, u.created_at,
                   ug.name as grade_name, ug.icon, ug.color,
                   COUNT(uxl.id) as action_count
            FROM users u
            LEFT JOIN user_grades ug ON u.current_grade = ug.grade_key
            LEFT JOIN user_xp_logs uxl ON u.id = uxl.user_id
            WHERE u.xp IS NOT NULL
        '''
        params = []
        
        # Filtre par rôle si spécifié
        if role_filter and role_filter != 'all':
            query += ' AND u.role = ?'
            params.append(role_filter)
        
        query += ' GROUP BY u.id, u.username, u.role, u.xp, u.current_grade, u.created_at, ug.name, ug.icon, ug.color'
        
        # Application du tri
        if sort_by == 'actions':
            query += ' ORDER BY action_count DESC, u.xp DESC'
        elif sort_by == 'date':
            query += ' ORDER BY u.created_at DESC'
        else:  # xp par défaut
            query += ' ORDER BY u.xp DESC, u.created_at ASC'
        
        query += ' LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, user in enumerate(users, 1):
            leaderboard.append({
                'rank': i,
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'xp': user[3] or 0,
                'current_grade': user[4] or 'debutant',
                'created_at': user[5],
                'grade_name': user[6] or 'Débutant',
                'grade_icon': user[7] or '🌱',
                'grade_color': user[8] or '#6c757d',
                'action_count': user[9]
            })
        
        return leaderboard
        
    except Exception as e:
        print(f"Erreur lors de la récupération du leaderboard: {e}")
        return []

def get_user_leaderboard_position(user_id):
    """
    Récupère la position d'un utilisateur dans le classement
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Position et informations de classement
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération de l'XP de l'utilisateur
        cursor.execute('SELECT xp FROM users WHERE id = ?', (user_id,))
        user_xp_result = cursor.fetchone()
        
        if not user_xp_result:
            conn.close()
            return None
        
        user_xp = user_xp_result[0] or 0
        
        # Calcul de la position (nombre d'utilisateurs avec plus d'XP)
        cursor.execute('SELECT COUNT(*) FROM users WHERE xp > ?', (user_xp,))
        position = cursor.fetchone()[0] + 1
        
        # Total des utilisateurs avec XP
        cursor.execute('SELECT COUNT(*) FROM users WHERE xp IS NOT NULL AND xp > 0')
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'position': position,
            'total_users': total_users,
            'user_xp': user_xp,
            'percentile': round((1 - (position - 1) / total_users) * 100, 1) if total_users > 0 else 0
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul de la position: {e}")
        return None

# ============================================================================
# MISE À JOUR DU SYSTÈME XP AVEC NOTIFICATIONS
# ============================================================================

def add_user_xp_with_notifications(user_id, action_type, xp_amount=None, description=None):
    """
    Version améliorée d'ajout XP avec notifications automatiques
    
    Args:
        user_id (int): ID de l'utilisateur
        action_type (str): Type d'action
        xp_amount (int): XP personnalisé (optionnel)
        description (str): Description personnalisée
    
    Returns:
        dict: Résultat avec notifications
    """
    # Récupération du grade actuel avant modification
    current_grade_info = get_user_grade_info(user_id)
    old_grade = current_grade_info['current_grade']['grade_key'] if current_grade_info else 'debutant'
    old_xp = current_grade_info['user_info']['xp'] if current_grade_info else 0
    
    # Ajout de l'XP (fonction existante)
    xp_result = add_user_xp(user_id, action_type, xp_amount, description)
    
    if not xp_result['success']:
        return xp_result
    
    new_xp = xp_result['new_total_xp']
    
    # Vérification des récompenses
    new_rewards = check_and_unlock_rewards(user_id, new_xp)
    
    # Notification de changement de grade
    if xp_result.get('grade_changed'):
        new_grade_name = xp_result.get('new_grade')
        create_user_notification(
            user_id,
            f"🏆 Félicitations ! Vous avez atteint le grade {new_grade_name} !",
            'grade_up'
        )
    
    # Ajout des informations sur les récompenses
    xp_result['new_rewards'] = new_rewards
    xp_result['rewards_count'] = len(new_rewards)
    
    return xp_result

# ============================================================================
# INITIALISATION DES NOUVELLES TABLES
# ============================================================================

def init_advanced_grade_tables():
    """
    Initialise les nouvelles tables pour les fonctionnalités avancées
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des notifications utilisateur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'general',
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des récompenses utilisateur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reward_milestone INTEGER NOT NULL,
                reward_name TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT,
                unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, reward_milestone),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Index pour les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_notifications_user_id ON user_notifications(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_notifications_read ON user_notifications(is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_rewards_user_id ON user_rewards(user_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables avancées des grades initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables avancées: {e}")

# Initialisation automatique des tables
init_grade_tables()
init_advanced_grade_tables()