"""
Referral Manager - Module de gestion du système de parrainage
Système complet de parrainage avec récompenses et anti-triche pour MindTraderPro
"""

import os
import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
import json

# Configuration de la base de données
DATABASE = 'data/mindtraderpro_users.db'

# ============================================================================
# CONFIGURATION DU SYSTÈME DE PARRAINAGE
# ============================================================================

# Récompenses XP pour le parrain
REFERRAL_XP_REWARDS = {
    'signup': 5,      # XP par inscription
    'validated': 25,  # XP par filleul validé
    'became_referrer': 10  # Bonus si le filleul devient parrain
}

# Badges de parrainage par paliers
REFERRAL_BADGES = {
    5: {'name': 'Parrain Bronze', 'icon': '🥉', 'color': '#cd7f32'},
    10: {'name': 'Parrain Argent', 'icon': '🥈', 'color': '#c0c0c0'},
    20: {'name': 'Parrain Or', 'icon': '🥇', 'color': '#ffd700'},
    50: {'name': 'Parrain Platine', 'icon': '💎', 'color': '#e5e4e2'}
}

# Offres promotionnelles pour filleuls
REFERRAL_OFFERS = {
    'premium_discount': {
        'original_price': 14.99,
        'discounted_price': 4.99,
        'duration_days': 30,
        'description': '1 mois Premium à 4,99€ au lieu de 14,99€'
    },
    'lifetime_discount': {
        'original_price': 299.99,
        'discounted_price': 149.00,
        'duration_days': 30,
        'description': 'Réduction Lifetime à 149€ pendant 30 jours'
    }
}

# ============================================================================
# INITIALISATION DES TABLES
# ============================================================================

def init_referral_tables():
    """Initialise les tables du système de parrainage"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des parrainages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referee_id INTEGER,
                referral_code TEXT UNIQUE NOT NULL,
                signup_ip TEXT,
                signup_device_fingerprint TEXT,
                status TEXT DEFAULT 'pending',
                signup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                validation_date DATETIME,
                validation_reason TEXT,
                payment_made BOOLEAN DEFAULT 0,
                email_verified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referee_id) REFERENCES users (id)
            )
        ''')
        
        # Table des récompenses de parrainage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                referral_id INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                xp_amount INTEGER DEFAULT 0,
                badge_earned TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (referral_id) REFERENCES referrals (id)
            )
        ''')
        
        # Table des règles de parrainage (configuration admin)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT UNIQUE NOT NULL,
                rule_value TEXT NOT NULL,
                description TEXT,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (updated_by) REFERENCES users (id)
            )
        ''')
        
        # Table des logs anti-triche
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_fraud_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                device_fingerprint TEXT,
                email TEXT,
                referral_code TEXT,
                fraud_type TEXT,
                details TEXT,
                blocked BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index pour les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_rewards_user ON referral_rewards(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fraud_logs_ip ON referral_fraud_logs(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fraud_logs_email ON referral_fraud_logs(email)')
        
        # Insertion des règles par défaut
        default_rules = [
            ('max_referrals_per_ip', '3', 'Nombre maximum de parrainages par IP'),
            ('validation_requires_payment', 'true', 'Validation nécessite un paiement'),
            ('validation_requires_email', 'true', 'Validation nécessite email vérifié'),
            ('xp_signup', '5', 'XP par inscription'),
            ('xp_validated', '25', 'XP par filleul validé'),
            ('offer_duration_days', '30', 'Durée des offres en jours')
        ]
        
        for rule_name, rule_value, description in default_rules:
            cursor.execute('''
                INSERT OR IGNORE INTO referral_rules (rule_name, rule_value, description)
                VALUES (?, ?, ?)
            ''', (rule_name, rule_value, description))
        
        conn.commit()
        conn.close()
        
        print("✅ Tables de parrainage initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables de parrainage: {e}")

# ============================================================================
# GÉNÉRATION ET GESTION DES CODES DE PARRAINAGE
# ============================================================================

def generate_referral_code(user_id):
    """Génère un code de parrainage unique pour un utilisateur"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification si l'utilisateur a déjà un code
        cursor.execute('SELECT referral_code FROM referrals WHERE referrer_id = ? AND referee_id IS NULL', (user_id,))
        existing_code = cursor.fetchone()
        
        if existing_code:
            conn.close()
            return {'success': True, 'code': existing_code[0], 'existing': True}
        
        # Génération d'un code unique
        attempts = 0
        while attempts < 10:
            # Code basé sur l'ID utilisateur + token aléatoire
            raw_code = f"{user_id}_{secrets.token_urlsafe(8)}"
            code_hash = hashlib.md5(raw_code.encode()).hexdigest()[:8].upper()
            
            # Vérification de l'unicité
            cursor.execute('SELECT id FROM referrals WHERE referral_code = ?', (code_hash,))
            if not cursor.fetchone():
                # Insertion du nouveau code
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referral_code)
                    VALUES (?, ?)
                ''', (user_id, code_hash))
                
                conn.commit()
                conn.close()
                
                return {'success': True, 'code': code_hash, 'existing': False}
            
            attempts += 1
        
        conn.close()
        return {'success': False, 'error': 'Impossible de générer un code unique'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def get_referral_link(user_id, base_url="https://mindtraderpro.com"):
    """Génère le lien de parrainage complet pour un utilisateur"""
    try:
        code_result = generate_referral_code(user_id)
        
        if not code_result['success']:
            return code_result
        
        referral_code = code_result['code']
        referral_link = f"{base_url}/register?ref={referral_code}"
        
        return {
            'success': True,
            'code': referral_code,
            'link': referral_link,
            'existing': code_result.get('existing', False)
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

# ============================================================================
# GESTION DES INSCRIPTIONS VIA PARRAINAGE
# ============================================================================

def process_referral_signup(referral_code, new_user_id, signup_ip, device_fingerprint, email):
    """Traite l'inscription d'un nouveau membre via parrainage"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification de l'existence du code de parrainage
        cursor.execute('''
            SELECT id, referrer_id FROM referrals 
            WHERE referral_code = ? AND referee_id IS NULL
        ''', (referral_code,))
        
        referral_data = cursor.fetchone()
        if not referral_data:
            conn.close()
            return {'success': False, 'error': 'Code de parrainage invalide'}
        
        referral_id, referrer_id = referral_data
        
        # Vérifications anti-triche
        fraud_check = check_fraud_indicators(signup_ip, device_fingerprint, email, referral_code, cursor)
        
        if fraud_check['blocked']:
            conn.close()
            return {
                'success': False, 
                'error': 'Inscription bloquée pour suspicion de fraude',
                'fraud_reason': fraud_check['reason']
            }
        
        # Mise à jour du parrainage avec les informations du filleul
        cursor.execute('''
            UPDATE referrals 
            SET referee_id = ?, signup_ip = ?, signup_device_fingerprint = ?, status = 'registered'
            WHERE id = ?
        ''', (new_user_id, signup_ip, device_fingerprint, referral_id))
        
        # Attribution de l'XP au parrain pour l'inscription
        from modules.grade_manager import add_user_xp_with_notifications
        xp_result = add_user_xp_with_notifications(
            referrer_id, 
            'referral_signup', 
            REFERRAL_XP_REWARDS['signup'],
            f'Parrainage: Inscription de #{new_user_id}'
        )
        
        # Enregistrement de la récompense
        cursor.execute('''
            INSERT INTO referral_rewards (user_id, referral_id, reward_type, xp_amount, description)
            VALUES (?, ?, 'signup', ?, 'XP pour inscription via parrainage')
        ''', (referrer_id, referral_id, REFERRAL_XP_REWARDS['signup']))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'referrer_id': referrer_id,
            'referral_id': referral_id,
            'xp_awarded': REFERRAL_XP_REWARDS['signup']
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def check_fraud_indicators(ip_address, device_fingerprint, email, referral_code, cursor):
    """Vérifie les indicateurs de fraude pour un parrainage"""
    try:
        fraud_indicators = []
        
        # Vérification des doublons d'IP
        cursor.execute('''
            SELECT COUNT(*) FROM referrals 
            WHERE signup_ip = ? AND status != 'blocked'
        ''', (ip_address,))
        ip_count = cursor.fetchone()[0]
        
        if ip_count >= 3:  # Limite configurable
            fraud_indicators.append(f'Trop de parrainages depuis cette IP ({ip_count})')
        
        # Vérification des doublons d'empreinte d'appareil
        if device_fingerprint:
            cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE signup_device_fingerprint = ? AND status != 'blocked'
            ''', (device_fingerprint,))
            device_count = cursor.fetchone()[0]
            
            if device_count >= 2:
                fraud_indicators.append(f'Appareil déjà utilisé ({device_count} fois)')
        
        # Vérification des doublons d'email (domaine temporaire, etc.)
        if email:
            # Domaines suspects
            suspicious_domains = ['10minutemail.com', 'mailinator.com', 'guerrillamail.com', 'tempmail.org']
            email_domain = email.split('@')[-1].lower()
            
            if email_domain in suspicious_domains:
                fraud_indicators.append(f'Email temporaire détecté: {email_domain}')
        
        # Enregistrement des tentatives suspectes
        if fraud_indicators:
            cursor.execute('''
                INSERT INTO referral_fraud_logs 
                (ip_address, device_fingerprint, email, referral_code, fraud_type, details)
                VALUES (?, ?, ?, ?, 'signup_fraud', ?)
            ''', (ip_address, device_fingerprint, email, referral_code, ' | '.join(fraud_indicators)))
        
        return {
            'blocked': len(fraud_indicators) > 0,
            'reason': ' | '.join(fraud_indicators) if fraud_indicators else None,
            'indicators': fraud_indicators
        }
        
    except Exception as e:
        return {'blocked': False, 'reason': None, 'error': str(e)}

# ============================================================================
# VALIDATION DES FILLEULS
# ============================================================================

def validate_referral(referral_id, validation_reason="Manuel"):
    """Valide un parrainage et attribue les récompenses finales"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des informations du parrainage
        cursor.execute('''
            SELECT referrer_id, referee_id, status FROM referrals 
            WHERE id = ?
        ''', (referral_id,))
        
        referral_data = cursor.fetchone()
        if not referral_data:
            conn.close()
            return {'success': False, 'error': 'Parrainage non trouvé'}
        
        referrer_id, referee_id, current_status = referral_data
        
        if current_status == 'validated':
            conn.close()
            return {'success': False, 'error': 'Parrainage déjà validé'}
        
        # Mise à jour du statut
        cursor.execute('''
            UPDATE referrals 
            SET status = 'validated', validation_date = CURRENT_TIMESTAMP, validation_reason = ?
            WHERE id = ?
        ''', (validation_reason, referral_id))
        
        # Attribution de l'XP de validation au parrain
        from modules.grade_manager import add_user_xp_with_notifications
        xp_result = add_user_xp_with_notifications(
            referrer_id, 
            'referral_validated', 
            REFERRAL_XP_REWARDS['validated'],
            f'Parrainage validé: #{referee_id}'
        )
        
        # Vérification des badges de parrainage
        cursor.execute('''
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND status = 'validated'
        ''', (referrer_id,))
        validated_count = cursor.fetchone()[0]
        
        badge_earned = None
        for threshold, badge_info in REFERRAL_BADGES.items():
            if validated_count == threshold:
                badge_earned = badge_info['name']
                break
        
        # Enregistrement de la récompense de validation
        cursor.execute('''
            INSERT INTO referral_rewards (user_id, referral_id, reward_type, xp_amount, badge_earned, description)
            VALUES (?, ?, 'validation', ?, ?, 'XP pour parrainage validé')
        ''', (referrer_id, referral_id, REFERRAL_XP_REWARDS['validated'], badge_earned))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'xp_awarded': REFERRAL_XP_REWARDS['validated'],
            'badge_earned': badge_earned,
            'validated_count': validated_count
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def check_auto_validation(user_id):
    """Vérifie si un filleul peut être automatiquement validé"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération des paramètres de validation
        cursor.execute('''
            SELECT rule_value FROM referral_rules 
            WHERE rule_name IN ('validation_requires_payment', 'validation_requires_email')
        ''')
        rules = cursor.fetchall()
        
        requires_payment = any(rule[0].lower() == 'true' for rule in rules if 'payment' in str(rule))
        requires_email = any(rule[0].lower() == 'true' for rule in rules if 'email' in str(rule))
        
        # Vérification du statut utilisateur
        cursor.execute('''
            SELECT email_verified, has_made_payment FROM users WHERE id = ?
        ''', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return {'can_validate': False, 'reason': 'Utilisateur non trouvé'}
        
        email_verified, has_made_payment = user_data
        
        # Vérification des conditions
        validation_issues = []
        
        if requires_email and not email_verified:
            validation_issues.append('Email non vérifié')
        
        if requires_payment and not has_made_payment:
            validation_issues.append('Aucun paiement effectué')
        
        can_validate = len(validation_issues) == 0
        
        # Auto-validation si possible
        if can_validate:
            cursor.execute('''
                SELECT id FROM referrals 
                WHERE referee_id = ? AND status = 'registered'
            ''', (user_id,))
            
            referral_to_validate = cursor.fetchone()
            if referral_to_validate:
                validation_result = validate_referral(referral_to_validate[0], "Auto-validation")
                conn.close()
                return {
                    'can_validate': True,
                    'auto_validated': True,
                    'validation_result': validation_result
                }
        
        conn.close()
        return {
            'can_validate': can_validate,
            'auto_validated': False,
            'issues': validation_issues
        }
        
    except Exception as e:
        return {'can_validate': False, 'error': f'Erreur: {str(e)}'}

# ============================================================================
# STATISTIQUES ET INFORMATIONS DE PARRAINAGE
# ============================================================================

def get_user_referral_stats(user_id):
    """Récupère les statistiques de parrainage d'un utilisateur"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Code de parrainage de l'utilisateur
        cursor.execute('''
            SELECT referral_code FROM referrals 
            WHERE referrer_id = ? AND referee_id IS NULL
        ''', (user_id,))
        referral_code_result = cursor.fetchone()
        referral_code = referral_code_result[0] if referral_code_result else None
        
        # Statistiques de base
        cursor.execute('''
            SELECT 
                COUNT(*) as total_referrals,
                SUM(CASE WHEN status = 'registered' THEN 1 ELSE 0 END) as registered,
                SUM(CASE WHEN status = 'validated' THEN 1 ELSE 0 END) as validated,
                SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked
            FROM referrals 
            WHERE referrer_id = ? AND referee_id IS NOT NULL
        ''', (user_id,))
        
        stats = cursor.fetchone()
        
        # XP total gagné via parrainage
        cursor.execute('''
            SELECT SUM(xp_amount) FROM referral_rewards 
            WHERE user_id = ?
        ''', (user_id,))
        total_xp_result = cursor.fetchone()
        total_xp = total_xp_result[0] or 0
        
        # Badges débloqués
        cursor.execute('''
            SELECT DISTINCT badge_earned FROM referral_rewards 
            WHERE user_id = ? AND badge_earned IS NOT NULL
        ''', (user_id,))
        badges = [row[0] for row in cursor.fetchall()]
        
        # Prochain badge
        validated_count = stats[2] if stats else 0
        next_badge = None
        for threshold, badge_info in REFERRAL_BADGES.items():
            if validated_count < threshold:
                next_badge = {
                    'threshold': threshold,
                    'name': badge_info['name'],
                    'remaining': threshold - validated_count
                }
                break
        
        # Liste des filleuls récents
        cursor.execute('''
            SELECT r.referee_id, u.username, r.status, r.signup_date, r.validation_date
            FROM referrals r
            LEFT JOIN users u ON r.referee_id = u.id
            WHERE r.referrer_id = ? AND r.referee_id IS NOT NULL
            ORDER BY r.signup_date DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_referrals = []
        for row in cursor.fetchall():
            recent_referrals.append({
                'referee_id': row[0],
                'username': row[1] or 'Utilisateur inconnu',
                'status': row[2],
                'signup_date': row[3],
                'validation_date': row[4]
            })
        
        conn.close()
        
        return {
            'success': True,
            'referral_code': referral_code,
            'stats': {
                'total_referrals': stats[0] if stats else 0,
                'registered': stats[1] if stats else 0,
                'validated': stats[2] if stats else 0,
                'blocked': stats[3] if stats else 0
            },
            'total_xp': total_xp,
            'badges': badges,
            'next_badge': next_badge,
            'recent_referrals': recent_referrals
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def get_referral_leaderboard(limit=20):
    """Récupère le leaderboard des meilleurs parrains"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id, u.username, u.role,
                COUNT(r.id) as total_referrals,
                SUM(CASE WHEN r.status = 'validated' THEN 1 ELSE 0 END) as validated_referrals,
                COALESCE(SUM(rr.xp_amount), 0) as total_xp_earned,
                MAX(rr.created_at) as last_reward_date
            FROM users u
            LEFT JOIN referrals r ON u.id = r.referrer_id AND r.referee_id IS NOT NULL
            LEFT JOIN referral_rewards rr ON u.id = rr.user_id
            GROUP BY u.id, u.username, u.role
            HAVING total_referrals > 0
            ORDER BY validated_referrals DESC, total_xp_earned DESC
            LIMIT ?
        ''', (limit,))
        
        leaderboard = []
        for i, row in enumerate(cursor.fetchall(), 1):
            # Détermination du badge actuel
            validated_count = row[4]
            current_badge = None
            for threshold, badge_info in sorted(REFERRAL_BADGES.items(), reverse=True):
                if validated_count >= threshold:
                    current_badge = badge_info
                    break
            
            leaderboard.append({
                'rank': i,
                'user_id': row[0],
                'username': row[1],
                'role': row[2],
                'total_referrals': row[3],
                'validated_referrals': row[4],
                'total_xp_earned': row[5],
                'last_reward_date': row[6],
                'current_badge': current_badge
            })
        
        conn.close()
        
        return {'success': True, 'leaderboard': leaderboard}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

# ============================================================================
# ADMINISTRATION DU SYSTÈME DE PARRAINAGE
# ============================================================================

def get_all_referrals_admin(limit=50, offset=0, status_filter=None):
    """Récupère tous les parrainages pour l'administration"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                r.id, r.referral_code, r.status, r.signup_date, r.validation_date,
                ur.username as referrer_username, ur.role as referrer_role,
                uf.username as referee_username, uf.email as referee_email,
                r.signup_ip, r.payment_made, r.email_verified
            FROM referrals r
            LEFT JOIN users ur ON r.referrer_id = ur.id
            LEFT JOIN users uf ON r.referee_id = uf.id
            WHERE r.referee_id IS NOT NULL
        '''
        params = []
        
        if status_filter:
            query += ' AND r.status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY r.signup_date DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        referrals = cursor.fetchall()
        
        # Comptage total
        count_query = '''
            SELECT COUNT(*) FROM referrals r 
            WHERE r.referee_id IS NOT NULL
        '''
        count_params = []
        
        if status_filter:
            count_query += ' AND r.status = ?'
            count_params.append(status_filter)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        referral_list = []
        for row in referrals:
            referral_list.append({
                'id': row[0],
                'referral_code': row[1],
                'status': row[2],
                'signup_date': row[3],
                'validation_date': row[4],
                'referrer_username': row[5],
                'referrer_role': row[6],
                'referee_username': row[7],
                'referee_email': row[8],
                'signup_ip': row[9],
                'payment_made': bool(row[10]),
                'email_verified': bool(row[11])
            })
        
        return {
            'success': True,
            'referrals': referral_list,
            'total_count': total_count,
            'has_more': offset + limit < total_count
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def update_referral_status_admin(referral_id, new_status, admin_id, reason):
    """Met à jour le statut d'un parrainage (admin)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification de l'existence du parrainage
        cursor.execute('SELECT status FROM referrals WHERE id = ?', (referral_id,))
        current_status_result = cursor.fetchone()
        
        if not current_status_result:
            conn.close()
            return {'success': False, 'error': 'Parrainage non trouvé'}
        
        current_status = current_status_result[0]
        
        # Mise à jour du statut
        cursor.execute('''
            UPDATE referrals 
            SET status = ?, validation_date = CASE WHEN ? = 'validated' THEN CURRENT_TIMESTAMP ELSE validation_date END,
                validation_reason = ?
            WHERE id = ?
        ''', (new_status, new_status, reason, referral_id))
        
        # Log administratif
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action_type, target_id, details, created_at)
            VALUES (?, 'referral_status_change', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_id, referral_id, f"Statut changé: {current_status} → {new_status}. Raison: {reason}"))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'old_status': current_status, 'new_status': new_status}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

def get_referral_fraud_logs(limit=100):
    """Récupère les logs de fraude pour l'administration"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address, device_fingerprint, email, referral_code, fraud_type, details, created_at
            FROM referral_fraud_logs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'ip_address': row[0],
                'device_fingerprint': row[1],
                'email': row[2],
                'referral_code': row[3],
                'fraud_type': row[4],
                'details': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        
        return {'success': True, 'fraud_logs': logs}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur: {str(e)}'}

# ============================================================================
# INITIALISATION AUTOMATIQUE
# ============================================================================

# Initialisation automatique des tables
init_referral_tables()