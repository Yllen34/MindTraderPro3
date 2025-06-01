"""
Lifetime Contribution Manager - Module de gestion des contributions exclusives Lifetime
Permet aux utilisateurs Lifetime de contribuer à l'évolution de MindTraderPro
"""

import sqlite3
import json
import os
from datetime import datetime

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# GESTION DES CONTRIBUTIONS LIFETIME
# ============================================================================

def create_lifetime_contribution(user_id, title, description, attached_file=None):
    """
    Crée une nouvelle contribution d'un utilisateur Lifetime
    
    Args:
        user_id (int): ID de l'utilisateur Lifetime
        title (str): Titre de la contribution
        description (str): Description détaillée
        attached_file (str): Nom du fichier joint optionnel
    
    Returns:
        dict: Résultat de la création
    """
    try:
        # Validation des données obligatoires
        if not all([user_id, title, description]):
            return {'success': False, 'error': 'Titre et description sont requis'}
        
        # Limitation de la taille des données
        if len(title) > 300:
            return {'success': False, 'error': 'Titre limité à 300 caractères'}
        
        if len(description) > 5000:
            return {'success': False, 'error': 'Description limitée à 5000 caractères'}
        
        # Vérification que l'utilisateur est bien Lifetime
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user or user[0] not in ['lifetime', 'admin']:
            conn.close()
            return {'success': False, 'error': 'Accès réservé aux utilisateurs Lifetime'}
        
        # Insertion de la nouvelle contribution
        cursor.execute('''
            INSERT INTO lifetime_contributions 
            (user_id, title, description, attached_file, status, created_at)
            VALUES (?, ?, ?, ?, 'proposed', CURRENT_TIMESTAMP)
        ''', (user_id, title.strip(), description.strip(), attached_file))
        
        contribution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'contribution_id': contribution_id, 
            'message': 'Contribution créée avec succès ! Merci de contribuer à l\'évolution de MindTraderPro.'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la création: {str(e)}'}

def get_all_lifetime_contributions(limit=50, offset=0, sort_by='recent', user_id=None, filter_status='all'):
    """
    Récupère toutes les contributions Lifetime avec tri et filtres
    
    Args:
        limit (int): Nombre de contributions à récupérer
        offset (int): Décalage pour la pagination
        sort_by (str): Type de tri ('recent', 'popular', 'my_contributions')
        user_id (int): ID de l'utilisateur pour filtres personnalisés
        filter_status (str): Filtre par statut ('all', 'proposed', 'accepted', 'in_development', 'completed', 'refused')
    
    Returns:
        list: Liste des contributions avec informations complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête de base avec jointures
        query = '''
            SELECT lc.id, lc.user_id, u.username, lc.title, lc.description, 
                   lc.attached_file, lc.status, lc.created_at, lc.updated_at,
                   COUNT(lcv.id) as vote_count,
                   CASE WHEN ucv.user_id IS NOT NULL THEN 1 ELSE 0 END as user_has_voted
            FROM lifetime_contributions lc
            JOIN users u ON lc.user_id = u.id
            LEFT JOIN lifetime_contribution_votes lcv ON lc.id = lcv.contribution_id
            LEFT JOIN lifetime_contribution_votes ucv ON lc.id = ucv.contribution_id AND ucv.user_id = ?
            WHERE u.role IN ('lifetime', 'admin')
        '''
        params = [user_id or 0]
        
        # Application des filtres
        if filter_status != 'all':
            query += ' AND lc.status = ?'
            params.append(filter_status)
        
        # Filtrage pour "mes contributions"
        if sort_by == 'my_contributions' and user_id:
            query += ' AND lc.user_id = ?'
            params.append(user_id)
        
        # Regroupement pour compter les votes
        query += ' GROUP BY lc.id, lc.user_id, u.username, lc.title, lc.description, lc.attached_file, lc.status, lc.created_at, lc.updated_at, ucv.user_id'
        
        # Application du tri
        if sort_by == 'popular':
            query += ' ORDER BY vote_count DESC, lc.created_at DESC'
        elif sort_by == 'recent':
            query += ' ORDER BY lc.created_at DESC'
        else:  # my_contributions ou défaut
            query += ' ORDER BY lc.created_at DESC'
        
        # Limite et offset
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        contributions = cursor.fetchall()
        conn.close()
        
        contributions_list = []
        for contribution in contributions:
            contributions_list.append({
                'id': contribution[0],
                'user_id': contribution[1],
                'username': contribution[2],
                'title': contribution[3],
                'description': contribution[4],
                'attached_file': contribution[5],
                'status': contribution[6],
                'created_at': contribution[7],
                'updated_at': contribution[8],
                'vote_count': contribution[9],
                'user_has_voted': bool(contribution[10])
            })
        
        return contributions_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des contributions: {e}")
        return []

def get_lifetime_contribution_by_id(contribution_id, user_id=None):
    """
    Récupère une contribution spécifique avec ses détails
    
    Args:
        contribution_id (int): ID de la contribution
        user_id (int): ID de l'utilisateur pour vérifier s'il a voté
    
    Returns:
        dict: Détails de la contribution ou None
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT lc.id, lc.user_id, u.username, lc.title, lc.description, 
                   lc.attached_file, lc.status, lc.created_at, lc.updated_at,
                   COUNT(lcv.id) as vote_count,
                   CASE WHEN ucv.user_id IS NOT NULL THEN 1 ELSE 0 END as user_has_voted
            FROM lifetime_contributions lc
            JOIN users u ON lc.user_id = u.id
            LEFT JOIN lifetime_contribution_votes lcv ON lc.id = lcv.contribution_id
            LEFT JOIN lifetime_contribution_votes ucv ON lc.id = ucv.contribution_id AND ucv.user_id = ?
            WHERE lc.id = ? AND u.role IN ('lifetime', 'admin')
            GROUP BY lc.id, lc.user_id, u.username, lc.title, lc.description, lc.attached_file, lc.status, lc.created_at, lc.updated_at, ucv.user_id
        ''', (user_id or 0, contribution_id))
        
        contribution = cursor.fetchone()
        conn.close()
        
        if contribution:
            return {
                'id': contribution[0],
                'user_id': contribution[1],
                'username': contribution[2],
                'title': contribution[3],
                'description': contribution[4],
                'attached_file': contribution[5],
                'status': contribution[6],
                'created_at': contribution[7],
                'updated_at': contribution[8],
                'vote_count': contribution[9],
                'user_has_voted': bool(contribution[10])
            }
        
        return None
        
    except Exception as e:
        print(f"Erreur lors de la récupération de la contribution: {e}")
        return None

def update_lifetime_contribution(contribution_id, user_id, title, description):
    """
    Met à jour une contribution (seul l'auteur peut modifier)
    
    Args:
        contribution_id (int): ID de la contribution
        user_id (int): ID de l'utilisateur (vérification de propriété)
        title (str): Nouveau titre
        description (str): Nouvelle description
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        # Validation des données
        if not all([contribution_id, user_id, title, description]):
            return {'success': False, 'error': 'Tous les champs sont requis'}
        
        if len(title) > 300:
            return {'success': False, 'error': 'Titre limité à 300 caractères'}
        
        if len(description) > 5000:
            return {'success': False, 'error': 'Description limitée à 5000 caractères'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que l'utilisateur est propriétaire de la contribution
        cursor.execute('SELECT user_id, status FROM lifetime_contributions WHERE id = ?', (contribution_id,))
        contribution = cursor.fetchone()
        
        if not contribution:
            conn.close()
            return {'success': False, 'error': 'Contribution non trouvée'}
        
        if contribution[0] != user_id:
            conn.close()
            return {'success': False, 'error': 'Vous ne pouvez modifier que vos propres contributions'}
        
        # Vérification que la contribution peut encore être modifiée
        if contribution[1] in ['in_development', 'completed']:
            conn.close()
            return {'success': False, 'error': 'Cette contribution ne peut plus être modifiée (en développement ou terminée)'}
        
        # Mise à jour de la contribution
        cursor.execute('''
            UPDATE lifetime_contributions 
            SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (title.strip(), description.strip(), contribution_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Contribution mise à jour avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def delete_lifetime_contribution(contribution_id, user_id):
    """
    Supprime une contribution (seul l'auteur peut supprimer, uniquement si pas encore acceptée)
    
    Args:
        contribution_id (int): ID de la contribution
        user_id (int): ID de l'utilisateur (vérification de propriété)
    
    Returns:
        dict: Résultat de la suppression
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification de propriété et de statut
        cursor.execute('SELECT user_id, status FROM lifetime_contributions WHERE id = ?', (contribution_id,))
        contribution = cursor.fetchone()
        
        if not contribution:
            conn.close()
            return {'success': False, 'error': 'Contribution non trouvée'}
        
        if contribution[0] != user_id:
            conn.close()
            return {'success': False, 'error': 'Vous ne pouvez supprimer que vos propres contributions'}
        
        if contribution[1] != 'proposed':
            conn.close()
            return {'success': False, 'error': 'Seules les contributions "proposées" peuvent être supprimées'}
        
        # Suppression des votes associés
        cursor.execute('DELETE FROM lifetime_contribution_votes WHERE contribution_id = ?', (contribution_id,))
        
        # Suppression de la contribution
        cursor.execute('DELETE FROM lifetime_contributions WHERE id = ? AND user_id = ?', (contribution_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Contribution supprimée avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}

# ============================================================================
# GESTION DES VOTES LIFETIME
# ============================================================================

def toggle_lifetime_contribution_vote(contribution_id, user_id):
    """
    Ajoute ou retire un vote d'un utilisateur Lifetime pour une contribution
    
    Args:
        contribution_id (int): ID de la contribution
        user_id (int): ID de l'utilisateur Lifetime
    
    Returns:
        dict: Résultat de l'action avec nouveau statut
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que l'utilisateur est bien Lifetime
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user or user[0] not in ['lifetime', 'admin']:
            conn.close()
            return {'success': False, 'error': 'Seuls les utilisateurs Lifetime peuvent voter'}
        
        # Vérification que la contribution existe
        cursor.execute('SELECT id FROM lifetime_contributions WHERE id = ?', (contribution_id,))
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Contribution non trouvée'}
        
        # Vérification si l'utilisateur a déjà voté
        cursor.execute('SELECT id FROM lifetime_contribution_votes WHERE contribution_id = ? AND user_id = ?', 
                      (contribution_id, user_id))
        existing_vote = cursor.fetchone()
        
        if existing_vote:
            # Retirer le vote
            cursor.execute('DELETE FROM lifetime_contribution_votes WHERE contribution_id = ? AND user_id = ?', 
                          (contribution_id, user_id))
            action = 'removed'
            message = 'Vote retiré'
        else:
            # Ajouter le vote
            cursor.execute('''
                INSERT INTO lifetime_contribution_votes (contribution_id, user_id, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (contribution_id, user_id))
            action = 'added'
            message = 'Vote ajouté'
        
        # Récupération du nouveau compte de votes
        cursor.execute('SELECT COUNT(*) FROM lifetime_contribution_votes WHERE contribution_id = ?', (contribution_id,))
        new_vote_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'action': action, 
            'message': message,
            'new_vote_count': new_vote_count,
            'user_has_voted': action == 'added'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors du vote: {str(e)}'}

# ============================================================================
# GESTION ADMINISTRATIVE DES CONTRIBUTIONS LIFETIME
# ============================================================================

def update_lifetime_contribution_status(contribution_id, new_status, admin_id, admin_comment=None):
    """
    Met à jour le statut d'une contribution Lifetime (admin seulement)
    
    Args:
        contribution_id (int): ID de la contribution
        new_status (str): Nouveau statut ('proposed', 'accepted', 'in_development', 'completed', 'refused')
        admin_id (int): ID de l'administrateur
        admin_comment (str): Commentaire administratif optionnel
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        valid_statuses = ['proposed', 'accepted', 'in_development', 'completed', 'refused']
        if new_status not in valid_statuses:
            return {'success': False, 'error': 'Statut invalide'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que la contribution existe
        cursor.execute('SELECT title, user_id FROM lifetime_contributions WHERE id = ?', (contribution_id,))
        contribution = cursor.fetchone()
        
        if not contribution:
            conn.close()
            return {'success': False, 'error': 'Contribution non trouvée'}
        
        # Mise à jour du statut
        cursor.execute('''
            UPDATE lifetime_contributions 
            SET status = ?, admin_comment = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, admin_comment, contribution_id))
        
        # Log de l'action administrative
        admin_details = f'Contribution "{contribution[0]}" - Statut changé vers: {new_status}'
        if admin_comment:
            admin_details += f' - Commentaire: {admin_comment}'
        
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'lifetime_contribution_status_change', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_id, contribution[1], admin_details))
        
        conn.commit()
        conn.close()
        
        status_messages = {
            'accepted': 'Contribution acceptée ! Elle sera développée prochainement.',
            'in_development': 'Contribution en cours de développement.',
            'completed': 'Contribution implémentée avec succès !',
            'refused': 'Contribution refusée après évaluation.'
        }
        
        return {
            'success': True, 
            'message': status_messages.get(new_status, f'Statut mis à jour vers: {new_status}')
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def get_lifetime_contributions_statistics():
    """
    Récupère les statistiques des contributions Lifetime pour l'administration
    
    Returns:
        dict: Statistiques complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Statistiques par statut
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM lifetime_contributions 
            GROUP BY status
        ''')
        status_stats = dict(cursor.fetchall())
        
        # Total des contributions
        cursor.execute('SELECT COUNT(*) FROM lifetime_contributions')
        total_contributions = cursor.fetchone()[0]
        
        # Total des votes
        cursor.execute('SELECT COUNT(*) FROM lifetime_contribution_votes')
        total_votes = cursor.fetchone()[0]
        
        # Contributions les plus populaires
        cursor.execute('''
            SELECT lc.id, lc.title, COUNT(lcv.id) as vote_count
            FROM lifetime_contributions lc
            LEFT JOIN lifetime_contribution_votes lcv ON lc.id = lcv.contribution_id
            GROUP BY lc.id, lc.title
            ORDER BY vote_count DESC
            LIMIT 5
        ''')
        popular_contributions = cursor.fetchall()
        
        # Contributeurs les plus actifs
        cursor.execute('''
            SELECT u.username, COUNT(lc.id) as contribution_count
            FROM users u
            JOIN lifetime_contributions lc ON u.id = lc.user_id
            WHERE u.role = 'lifetime'
            GROUP BY u.id, u.username
            ORDER BY contribution_count DESC
            LIMIT 5
        ''')
        active_contributors = cursor.fetchall()
        
        # Nombre d'utilisateurs Lifetime
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "lifetime"')
        lifetime_users_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_contributions': total_contributions,
            'total_votes': total_votes,
            'status_stats': status_stats,
            'popular_contributions': popular_contributions,
            'active_contributors': active_contributors,
            'lifetime_users_count': lifetime_users_count
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

def get_user_lifetime_profile(user_id):
    """
    Récupère le profil détaillé d'un utilisateur Lifetime avec ses contributions
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Profil Lifetime complet
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Informations de base de l'utilisateur
        cursor.execute('SELECT username, email, role, created_at FROM users WHERE id = ?', (user_id,))
        user_info = cursor.fetchone()
        
        if not user_info or user_info[2] not in ['lifetime', 'admin']:
            conn.close()
            return None
        
        # Statistiques des contributions
        cursor.execute('SELECT COUNT(*) FROM lifetime_contributions WHERE user_id = ?', (user_id,))
        total_contributions = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM lifetime_contributions 
            WHERE user_id = ? AND status = 'accepted'
        ''', (user_id,))
        accepted_contributions = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM lifetime_contributions 
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        implemented_contributions = cursor.fetchone()[0]
        
        # Total des votes reçus
        cursor.execute('''
            SELECT COUNT(lcv.id) 
            FROM lifetime_contribution_votes lcv
            JOIN lifetime_contributions lc ON lcv.contribution_id = lc.id
            WHERE lc.user_id = ?
        ''', (user_id,))
        total_votes_received = cursor.fetchone()[0]
        
        # Contributions récentes
        cursor.execute('''
            SELECT id, title, status, created_at 
            FROM lifetime_contributions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (user_id,))
        recent_contributions = cursor.fetchall()
        
        conn.close()
        
        # Calcul du niveau de contribution
        contribution_level = "Nouveau Contributeur"
        if total_contributions >= 10:
            contribution_level = "Contributeur Expert"
        elif total_contributions >= 5:
            contribution_level = "Contributeur Actif"
        elif total_contributions >= 1:
            contribution_level = "Contributeur"
        
        if implemented_contributions >= 3:
            contribution_level = "Contributeur Légende"
        
        return {
            'user_info': {
                'username': user_info[0],
                'email': user_info[1],
                'role': user_info[2],
                'member_since': user_info[3]
            },
            'contribution_stats': {
                'total_contributions': total_contributions,
                'accepted_contributions': accepted_contributions,
                'implemented_contributions': implemented_contributions,
                'total_votes_received': total_votes_received,
                'contribution_level': contribution_level
            },
            'recent_contributions': recent_contributions
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération du profil Lifetime: {e}")
        return None

# ============================================================================
# INITIALISATION DES TABLES LIFETIME CONTRIBUTIONS
# ============================================================================

def init_lifetime_contribution_tables():
    """
    Initialise les tables nécessaires pour les contributions Lifetime
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des contributions Lifetime
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lifetime_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                attached_file TEXT,
                status TEXT DEFAULT 'proposed',
                admin_comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des votes sur les contributions Lifetime
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lifetime_contribution_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contribution_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contribution_id, user_id),
                FOREIGN KEY (contribution_id) REFERENCES lifetime_contributions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lifetime_contributions_user_id ON lifetime_contributions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lifetime_contributions_status ON lifetime_contributions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lifetime_contributions_created_at ON lifetime_contributions(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lifetime_contribution_votes_contribution_id ON lifetime_contribution_votes(contribution_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables contributions Lifetime initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables contributions Lifetime: {e}")

# Initialisation automatique des tables
init_lifetime_contribution_tables()