"""
Admin Manager - Module de gestion administrative pour MindTraderPro
Toutes les fonctions administratives pour la gestion des utilisateurs, trades et système
"""

import os
import sqlite3
import bcrypt
from datetime import datetime

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# GESTION DES UTILISATEURS
# ============================================================================

def get_all_users():
    """
    Récupère tous les utilisateurs avec leurs statistiques
    
    Returns:
        list: Liste de tous les utilisateurs avec leurs informations complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des utilisateurs avec comptage des trades
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.role, u.created_at, u.calc_count, u.calc_limit,
                   COUNT(t.id) as trade_count,
                   MAX(t.created_at) as last_trade
            FROM users u
            LEFT JOIN trading_journal t ON u.id = t.user_id
            GROUP BY u.id, u.username, u.email, u.role, u.created_at, u.calc_count, u.calc_limit
            ORDER BY u.created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': user[4],
                'calc_count': user[5] or 0,
                'calc_limit': user[6] or 3,
                'trade_count': user[7],
                'last_trade': user[8],
                'status': 'active'  # Peut être étendu pour gérer les comptes suspendus
            })
        
        return users_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
        return []

def update_user_role(user_id, new_role, admin_user_id):
    """
    Modifie le rôle d'un utilisateur (admin seulement)
    
    Args:
        user_id (int): ID de l'utilisateur à modifier
        new_role (str): Nouveau rôle (standard, premium, lifetime, admin)
        admin_user_id (int): ID de l'administrateur qui effectue la modification
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        # Validation du rôle
        valid_roles = ['standard', 'premium', 'lifetime', 'admin']
        if new_role not in valid_roles:
            return {'success': False, 'error': 'Rôle invalide'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que l'utilisateur existe
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        # Mise à jour du rôle
        cursor.execute('''
            UPDATE users 
            SET role = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_role, user_id))
        
        # Log de l'action administrative
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'role_change', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, user_id, f'Rôle changé vers: {new_role}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Rôle de {user[0]} mis à jour vers {new_role}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la modification: {str(e)}'}

def reset_user_password(user_id, new_password, admin_user_id):
    """
    Réinitialise le mot de passe d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        new_password (str): Nouveau mot de passe
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        if len(new_password) < 6:
            return {'success': False, 'error': 'Le mot de passe doit contenir au moins 6 caractères'}
        
        # Hashage sécurisé du nouveau mot de passe
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que l'utilisateur existe
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        # Mise à jour du mot de passe
        cursor.execute('''
            UPDATE users 
            SET password = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (password_hash, user_id))
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'password_reset', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, user_id, f'Mot de passe réinitialisé pour {user[0]}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Mot de passe réinitialisé pour {user[0]}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la réinitialisation: {str(e)}'}

def update_user_quota(user_id, new_limit, admin_user_id):
    """
    Modifie le quota de calculs d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        new_limit (int): Nouvelle limite de calculs
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        if new_limit < 0:
            return {'success': False, 'error': 'La limite doit être positive'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification et mise à jour
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        cursor.execute('''
            UPDATE users 
            SET calc_limit = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_limit, user_id))
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'quota_update', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, user_id, f'Quota modifié à {new_limit} pour {user[0]}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Quota mis à jour pour {user[0]}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la modification: {str(e)}'}

def reset_user_calc_count(user_id, admin_user_id):
    """
    Remet à zéro le compteur de calculs d'un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        cursor.execute('''
            UPDATE users 
            SET calc_count = 0, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (user_id,))
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'calc_reset', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, user_id, f'Compteur de calculs réinitialisé pour {user[0]}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Compteur réinitialisé pour {user[0]}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la réinitialisation: {str(e)}'}

def delete_user_account(user_id, admin_user_id):
    """
    Supprime complètement un compte utilisateur et toutes ses données
    
    Args:
        user_id (int): ID de l'utilisateur à supprimer
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des informations utilisateur avant suppression
        cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'error': 'Utilisateur non trouvé'}
        
        # Suppression des trades associés
        cursor.execute('DELETE FROM trading_journal WHERE user_id = ?', (user_id,))
        
        # Suppression de l'utilisateur
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        # Log de l'action critique
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'user_deletion', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, user_id, f'Suppression complète de {user[0]} ({user[1]})'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Utilisateur {user[0]} supprimé définitivement'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}

# ============================================================================
# GESTION DU JOURNAL DE TRADING GLOBAL
# ============================================================================

def get_all_trades(limit=100, offset=0, filters=None):
    """
    Récupère tous les trades de tous les utilisateurs (admin seulement)
    
    Args:
        limit (int): Nombre de trades à récupérer
        offset (int): Décalage pour la pagination
        filters (dict): Filtres à appliquer
    
    Returns:
        list: Liste de tous les trades avec informations utilisateur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête avec jointure utilisateur
        query = '''
            SELECT t.id, t.user_id, u.username, u.email, t.asset, t.trade_type, 
                   t.trade_date, t.entry_price, t.exit_price, t.lot_size, 
                   t.result_pnl, t.result_pips, t.trading_style, t.emotions,
                   t.notes, t.status, t.created_at
            FROM trading_journal t
            JOIN users u ON t.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        # Application des filtres
        if filters:
            if filters.get('user_id'):
                query += ' AND t.user_id = ?'
                params.append(filters['user_id'])
            
            if filters.get('asset'):
                query += ' AND t.asset = ?'
                params.append(filters['asset'])
            
            if filters.get('date_from'):
                query += ' AND date(t.trade_date) >= ?'
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                query += ' AND date(t.trade_date) <= ?'
                params.append(filters['date_to'])
        
        query += ' ORDER BY t.created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        trades = cursor.fetchall()
        conn.close()
        
        trades_list = []
        for trade in trades:
            trades_list.append({
                'id': trade[0],
                'user_id': trade[1],
                'username': trade[2],
                'user_email': trade[3],
                'asset': trade[4],
                'trade_type': trade[5],
                'trade_date': trade[6],
                'entry_price': trade[7],
                'exit_price': trade[8],
                'lot_size': trade[9],
                'result_pnl': trade[10],
                'result_pips': trade[11],
                'trading_style': trade[12],
                'emotions': trade[13],
                'notes': trade[14],
                'status': trade[15],
                'created_at': trade[16]
            })
        
        return trades_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des trades: {e}")
        return []

def admin_delete_trade(trade_id, admin_user_id):
    """
    Supprime un trade (admin seulement)
    
    Args:
        trade_id (int): ID du trade à supprimer
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des informations du trade avant suppression
        cursor.execute('''
            SELECT t.id, t.user_id, u.username, t.asset, t.trade_type
            FROM trading_journal t
            JOIN users u ON t.user_id = u.id
            WHERE t.id = ?
        ''', (trade_id,))
        
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            return {'success': False, 'error': 'Trade non trouvé'}
        
        # Suppression du trade
        cursor.execute('DELETE FROM trading_journal WHERE id = ?', (trade_id,))
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'trade_deletion', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, trade[1], f'Suppression trade {trade[3]} {trade[4]} de {trade[2]}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Trade supprimé avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}

# ============================================================================
# GESTION DES PARTENARIATS
# ============================================================================

def get_all_partnerships():
    """
    Récupère toutes les offres partenaires
    
    Returns:
        list: Liste des partenariats
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, link, is_active, created_at, updated_at
            FROM partnerships
            ORDER BY is_active DESC, created_at DESC
        ''')
        
        partnerships = cursor.fetchall()
        conn.close()
        
        partnerships_list = []
        for partnership in partnerships:
            partnerships_list.append({
                'id': partnership[0],
                'title': partnership[1],
                'description': partnership[2],
                'link': partnership[3],
                'is_active': partnership[4],
                'created_at': partnership[5],
                'updated_at': partnership[6]
            })
        
        return partnerships_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des partenariats: {e}")
        return []

def create_partnership(title, description, link, is_active, admin_user_id):
    """
    Crée un nouveau partenariat
    
    Args:
        title (str): Titre du partenariat
        description (str): Description
        link (str): Lien vers l'offre
        is_active (bool): Statut d'activation
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        if not all([title, description, link]):
            return {'success': False, 'error': 'Tous les champs sont requis'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO partnerships (title, description, link, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (title, description, link, is_active))
        
        partnership_id = cursor.lastrowid
        
        # Log de l'action
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, details, created_at)
            VALUES (?, 'partnership_creation', ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, f'Nouveau partenariat créé: {title}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'partnership_id': partnership_id, 'message': 'Partenariat créé avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la création: {str(e)}'}

def update_partnership(partnership_id, title, description, link, is_active, admin_user_id):
    """
    Met à jour un partenariat existant
    
    Args:
        partnership_id (int): ID du partenariat
        title (str): Nouveau titre
        description (str): Nouvelle description
        link (str): Nouveau lien
        is_active (bool): Nouveau statut
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE partnerships 
            SET title = ?, description = ?, link = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, description, link, is_active, partnership_id))
        
        if cursor.rowcount > 0:
            # Log de l'action
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action, details, created_at)
                VALUES (?, 'partnership_update', ?, CURRENT_TIMESTAMP)
            ''', (admin_user_id, f'Partenariat mis à jour: {title}'))
            
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Partenariat mis à jour avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Partenariat non trouvé'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

# ============================================================================
# GESTION DES MODULES SYSTÈME
# ============================================================================

def get_system_modules():
    """
    Récupère l'état de tous les modules système
    
    Returns:
        dict: État des modules
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT module_name, is_active, description, last_updated
            FROM system_modules
            ORDER BY module_name
        ''')
        
        modules = cursor.fetchall()
        conn.close()
        
        modules_dict = {}
        for module in modules:
            modules_dict[module[0]] = {
                'is_active': module[1],
                'description': module[2],
                'last_updated': module[3]
            }
        
        # Modules par défaut s'ils n'existent pas encore
        default_modules = {
            'journal': {'is_active': True, 'description': 'Journal de trading premium'},
            'newsletter': {'is_active': True, 'description': 'Système de newsletter'},
            'ai_assistant': {'is_active': True, 'description': 'Assistant IA de trading'},
            'partnerships': {'is_active': True, 'description': 'Offres partenaires'},
            'analytics': {'is_active': True, 'description': 'Analytics et statistiques'},
        }
        
        for module_name, default_config in default_modules.items():
            if module_name not in modules_dict:
                modules_dict[module_name] = default_config
        
        return modules_dict
        
    except Exception as e:
        print(f"Erreur lors de la récupération des modules: {e}")
        return {}

def toggle_system_module(module_name, is_active, admin_user_id):
    """
    Active ou désactive un module système
    
    Args:
        module_name (str): Nom du module
        is_active (bool): Nouvel état
        admin_user_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de l'opération
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Mise à jour ou insertion du module
        cursor.execute('''
            INSERT OR REPLACE INTO system_modules (module_name, is_active, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (module_name, is_active))
        
        # Log de l'action
        status = 'activé' if is_active else 'désactivé'
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, details, created_at)
            VALUES (?, 'module_toggle', ?, CURRENT_TIMESTAMP)
        ''', (admin_user_id, f'Module {module_name} {status}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Module {module_name} {status} avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la modification: {str(e)}'}

# ============================================================================
# GESTION DES LOGS ADMINISTRATIFS
# ============================================================================

def get_admin_logs(limit=50):
    """
    Récupère les logs des actions administratives
    
    Args:
        limit (int): Nombre de logs à récupérer
    
    Returns:
        list: Liste des logs administratifs
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT al.id, al.admin_id, u1.username as admin_username, 
                   al.action, al.target_user_id, u2.username as target_username,
                   al.details, al.created_at
            FROM admin_logs al
            JOIN users u1 ON al.admin_id = u1.id
            LEFT JOIN users u2 ON al.target_user_id = u2.id
            ORDER BY al.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        logs_list = []
        for log in logs:
            logs_list.append({
                'id': log[0],
                'admin_id': log[1],
                'admin_username': log[2],
                'action': log[3],
                'target_user_id': log[4],
                'target_username': log[5],
                'details': log[6],
                'created_at': log[7]
            })
        
        return logs_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des logs: {e}")
        return []

# ============================================================================
# INITIALISATION DES TABLES ADMINISTRATIVES
# ============================================================================

def init_admin_tables():
    """
    Initialise les tables nécessaires pour l'administration
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des logs administratifs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_user_id INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users (id),
                FOREIGN KEY (target_user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des partenariats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partnerships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                link TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des modules système
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                description TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables administratives initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables admin: {e}")

# Initialisation automatique des tables
init_admin_tables()