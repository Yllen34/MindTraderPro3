"""
Suggestion Manager - Module de gestion des suggestions communautaires
Permet aux utilisateurs de proposer des idées et de voter pour celles des autres
"""

import sqlite3
from datetime import datetime

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# GESTION DES SUGGESTIONS
# ============================================================================

def create_suggestion(user_id, title, description):
    """
    Crée une nouvelle suggestion d'utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur qui propose
        title (str): Titre de la suggestion
        description (str): Description détaillée
    
    Returns:
        dict: Résultat de la création
    """
    try:
        # Validation des données obligatoires
        if not all([user_id, title, description]):
            return {'success': False, 'error': 'Titre et description sont requis'}
        
        # Limitation de la taille des données
        if len(title) > 200:
            return {'success': False, 'error': 'Titre limité à 200 caractères'}
        
        if len(description) > 2000:
            return {'success': False, 'error': 'Description limitée à 2000 caractères'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Insertion de la nouvelle suggestion
        cursor.execute('''
            INSERT INTO suggestions (user_id, title, description, status, created_at)
            VALUES (?, ?, ?, 'proposed', CURRENT_TIMESTAMP)
        ''', (user_id, title.strip(), description.strip()))
        
        suggestion_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'suggestion_id': suggestion_id, 'message': 'Suggestion créée avec succès !'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la création: {str(e)}'}

def get_all_suggestions(limit=50, offset=0, sort_by='recent', user_id=None, filter_type='all'):
    """
    Récupère toutes les suggestions avec tri et filtres
    
    Args:
        limit (int): Nombre de suggestions à récupérer
        offset (int): Décalage pour la pagination
        sort_by (str): Type de tri ('recent', 'popular', 'my_ideas')
        user_id (int): ID de l'utilisateur pour filtres personnalisés
        filter_type (str): Filtre par statut ('all', 'proposed', 'accepted', 'refused')
    
    Returns:
        list: Liste des suggestions avec informations complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête de base avec jointures
        query = '''
            SELECT s.id, s.user_id, u.username, s.title, s.description, s.status,
                   s.created_at, s.updated_at,
                   COUNT(v.id) as vote_count,
                   CASE WHEN uv.user_id IS NOT NULL THEN 1 ELSE 0 END as user_has_voted
            FROM suggestions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            LEFT JOIN suggestion_votes uv ON s.id = uv.suggestion_id AND uv.user_id = ?
            WHERE 1=1
        '''
        params = [user_id or 0]
        
        # Application des filtres
        if filter_type != 'all':
            query += ' AND s.status = ?'
            params.append(filter_type)
        
        # Filtrage pour "mes idées"
        if sort_by == 'my_ideas' and user_id:
            query += ' AND s.user_id = ?'
            params.append(user_id)
        
        # Regroupement pour compter les votes
        query += ' GROUP BY s.id, s.user_id, u.username, s.title, s.description, s.status, s.created_at, s.updated_at, uv.user_id'
        
        # Application du tri
        if sort_by == 'popular':
            query += ' ORDER BY vote_count DESC, s.created_at DESC'
        elif sort_by == 'recent':
            query += ' ORDER BY s.created_at DESC'
        else:  # my_ideas ou défaut
            query += ' ORDER BY s.created_at DESC'
        
        # Limite et offset
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        suggestions = cursor.fetchall()
        conn.close()
        
        suggestions_list = []
        for suggestion in suggestions:
            suggestions_list.append({
                'id': suggestion[0],
                'user_id': suggestion[1],
                'username': suggestion[2],
                'title': suggestion[3],
                'description': suggestion[4],
                'status': suggestion[5],
                'created_at': suggestion[6],
                'updated_at': suggestion[7],
                'vote_count': suggestion[8],
                'user_has_voted': bool(suggestion[9])
            })
        
        return suggestions_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des suggestions: {e}")
        return []

def get_suggestion_by_id(suggestion_id, user_id=None):
    """
    Récupère une suggestion spécifique avec ses détails
    
    Args:
        suggestion_id (int): ID de la suggestion
        user_id (int): ID de l'utilisateur pour vérifier s'il a voté
    
    Returns:
        dict: Détails de la suggestion ou None
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, s.user_id, u.username, s.title, s.description, s.status,
                   s.created_at, s.updated_at,
                   COUNT(v.id) as vote_count,
                   CASE WHEN uv.user_id IS NOT NULL THEN 1 ELSE 0 END as user_has_voted
            FROM suggestions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            LEFT JOIN suggestion_votes uv ON s.id = uv.suggestion_id AND uv.user_id = ?
            WHERE s.id = ?
            GROUP BY s.id, s.user_id, u.username, s.title, s.description, s.status, s.created_at, s.updated_at, uv.user_id
        ''', (user_id or 0, suggestion_id))
        
        suggestion = cursor.fetchone()
        conn.close()
        
        if suggestion:
            return {
                'id': suggestion[0],
                'user_id': suggestion[1],
                'username': suggestion[2],
                'title': suggestion[3],
                'description': suggestion[4],
                'status': suggestion[5],
                'created_at': suggestion[6],
                'updated_at': suggestion[7],
                'vote_count': suggestion[8],
                'user_has_voted': bool(suggestion[9])
            }
        
        return None
        
    except Exception as e:
        print(f"Erreur lors de la récupération de la suggestion: {e}")
        return None

def update_suggestion(suggestion_id, user_id, title, description):
    """
    Met à jour une suggestion (seul l'auteur peut modifier)
    
    Args:
        suggestion_id (int): ID de la suggestion
        user_id (int): ID de l'utilisateur (vérification de propriété)
        title (str): Nouveau titre
        description (str): Nouvelle description
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        # Validation des données
        if not all([suggestion_id, user_id, title, description]):
            return {'success': False, 'error': 'Tous les champs sont requis'}
        
        if len(title) > 200:
            return {'success': False, 'error': 'Titre limité à 200 caractères'}
        
        if len(description) > 2000:
            return {'success': False, 'error': 'Description limitée à 2000 caractères'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que l'utilisateur est propriétaire de la suggestion
        cursor.execute('SELECT user_id FROM suggestions WHERE id = ?', (suggestion_id,))
        suggestion = cursor.fetchone()
        
        if not suggestion:
            conn.close()
            return {'success': False, 'error': 'Suggestion non trouvée'}
        
        if suggestion[0] != user_id:
            conn.close()
            return {'success': False, 'error': 'Vous ne pouvez modifier que vos propres suggestions'}
        
        # Mise à jour de la suggestion
        cursor.execute('''
            UPDATE suggestions 
            SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (title.strip(), description.strip(), suggestion_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Suggestion mise à jour avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def delete_suggestion(suggestion_id, user_id):
    """
    Supprime une suggestion (seul l'auteur peut supprimer)
    
    Args:
        suggestion_id (int): ID de la suggestion
        user_id (int): ID de l'utilisateur (vérification de propriété)
    
    Returns:
        dict: Résultat de la suppression
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification de propriété
        cursor.execute('SELECT user_id FROM suggestions WHERE id = ?', (suggestion_id,))
        suggestion = cursor.fetchone()
        
        if not suggestion:
            conn.close()
            return {'success': False, 'error': 'Suggestion non trouvée'}
        
        if suggestion[0] != user_id:
            conn.close()
            return {'success': False, 'error': 'Vous ne pouvez supprimer que vos propres suggestions'}
        
        # Suppression des votes associés
        cursor.execute('DELETE FROM suggestion_votes WHERE suggestion_id = ?', (suggestion_id,))
        
        # Suppression de la suggestion
        cursor.execute('DELETE FROM suggestions WHERE id = ? AND user_id = ?', (suggestion_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Suggestion supprimée avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}

# ============================================================================
# GESTION DES VOTES
# ============================================================================

def toggle_vote(suggestion_id, user_id):
    """
    Ajoute ou retire un vote d'un utilisateur pour une suggestion
    
    Args:
        suggestion_id (int): ID de la suggestion
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Résultat de l'action avec nouveau statut
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que la suggestion existe
        cursor.execute('SELECT id FROM suggestions WHERE id = ?', (suggestion_id,))
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Suggestion non trouvée'}
        
        # Vérification si l'utilisateur a déjà voté
        cursor.execute('SELECT id FROM suggestion_votes WHERE suggestion_id = ? AND user_id = ?', 
                      (suggestion_id, user_id))
        existing_vote = cursor.fetchone()
        
        if existing_vote:
            # Retirer le vote
            cursor.execute('DELETE FROM suggestion_votes WHERE suggestion_id = ? AND user_id = ?', 
                          (suggestion_id, user_id))
            action = 'removed'
            message = 'Vote retiré'
        else:
            # Ajouter le vote
            cursor.execute('''
                INSERT INTO suggestion_votes (suggestion_id, user_id, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (suggestion_id, user_id))
            action = 'added'
            message = 'Vote ajouté'
        
        # Récupération du nouveau compte de votes
        cursor.execute('SELECT COUNT(*) FROM suggestion_votes WHERE suggestion_id = ?', (suggestion_id,))
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

def get_user_votes(user_id):
    """
    Récupère toutes les suggestions pour lesquelles un utilisateur a voté
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        list: Liste des IDs des suggestions votées
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT suggestion_id FROM suggestion_votes WHERE user_id = ?', (user_id,))
        votes = cursor.fetchall()
        conn.close()
        
        return [vote[0] for vote in votes]
        
    except Exception as e:
        print(f"Erreur lors de la récupération des votes: {e}")
        return []

# ============================================================================
# GESTION ADMINISTRATIVE DES SUGGESTIONS
# ============================================================================

def update_suggestion_status(suggestion_id, new_status, admin_id):
    """
    Met à jour le statut d'une suggestion (admin seulement)
    
    Args:
        suggestion_id (int): ID de la suggestion
        new_status (str): Nouveau statut ('proposed', 'accepted', 'refused', 'archived')
        admin_id (int): ID de l'administrateur
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        valid_statuses = ['proposed', 'accepted', 'refused', 'archived']
        if new_status not in valid_statuses:
            return {'success': False, 'error': 'Statut invalide'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification que la suggestion existe
        cursor.execute('SELECT title, user_id FROM suggestions WHERE id = ?', (suggestion_id,))
        suggestion = cursor.fetchone()
        
        if not suggestion:
            conn.close()
            return {'success': False, 'error': 'Suggestion non trouvée'}
        
        # Mise à jour du statut
        cursor.execute('''
            UPDATE suggestions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, suggestion_id))
        
        # Log de l'action administrative
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details, created_at)
            VALUES (?, 'suggestion_status_change', ?, ?, CURRENT_TIMESTAMP)
        ''', (admin_id, suggestion[1], f'Suggestion "{suggestion[0]}" - Statut changé vers: {new_status}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Statut mis à jour vers: {new_status}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def get_suggestions_statistics():
    """
    Récupère les statistiques des suggestions pour l'administration
    
    Returns:
        dict: Statistiques complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Statistiques par statut
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM suggestions 
            GROUP BY status
        ''')
        status_stats = dict(cursor.fetchall())
        
        # Total des suggestions
        cursor.execute('SELECT COUNT(*) FROM suggestions')
        total_suggestions = cursor.fetchone()[0]
        
        # Total des votes
        cursor.execute('SELECT COUNT(*) FROM suggestion_votes')
        total_votes = cursor.fetchone()[0]
        
        # Suggestions les plus populaires
        cursor.execute('''
            SELECT s.id, s.title, COUNT(v.id) as vote_count
            FROM suggestions s
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            GROUP BY s.id, s.title
            ORDER BY vote_count DESC
            LIMIT 5
        ''')
        popular_suggestions = cursor.fetchall()
        
        # Utilisateurs les plus actifs
        cursor.execute('''
            SELECT u.username, COUNT(s.id) as suggestion_count
            FROM users u
            JOIN suggestions s ON u.id = s.user_id
            GROUP BY u.id, u.username
            ORDER BY suggestion_count DESC
            LIMIT 5
        ''')
        active_users = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_suggestions': total_suggestions,
            'total_votes': total_votes,
            'status_stats': status_stats,
            'popular_suggestions': popular_suggestions,
            'active_users': active_users
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

def simulate_feature_implementation(suggestion_id):
    """
    Simule l'implémentation automatique d'une fonctionnalité acceptée
    
    Args:
        suggestion_id (int): ID de la suggestion acceptée
    
    Returns:
        dict: Résultat de la simulation
    """
    try:
        suggestion = get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return {'success': False, 'error': 'Suggestion non trouvée'}
        
        if suggestion['status'] != 'accepted':
            return {'success': False, 'error': 'Seules les suggestions acceptées peuvent être implémentées'}
        
        # Simulation de l'implémentation
        implementation_steps = [
            "Analyse des exigences techniques",
            "Planification du développement",
            "Création de l'architecture",
            "Développement des fonctionnalités",
            "Tests et validation",
            "Déploiement en production"
        ]
        
        return {
            'success': True,
            'message': f'Implémentation simulée pour: {suggestion["title"]}',
            'steps': implementation_steps,
            'estimated_time': '2-4 semaines',
            'priority': 'Haute' if suggestion['vote_count'] > 10 else 'Normale'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la simulation: {str(e)}'}

# ============================================================================
# INITIALISATION DES TABLES SUGGESTIONS
# ============================================================================

def init_suggestions_tables():
    """
    Initialise les tables nécessaires pour les suggestions communautaires
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des suggestions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'proposed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des votes sur les suggestions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(suggestion_id, user_id),
                FOREIGN KEY (suggestion_id) REFERENCES suggestions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_created_at ON suggestions(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestion_votes_suggestion_id ON suggestion_votes(suggestion_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables suggestions initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables suggestions: {e}")

# Initialisation automatique des tables
init_suggestions_tables()