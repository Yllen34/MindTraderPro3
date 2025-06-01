"""
Newsletter Manager - Module de gestion de la newsletter et des actualités
Gestion complète des abonnés, création et envoi de newsletters pour MindTraderPro
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# GESTION DES ABONNÉS À LA NEWSLETTER
# ============================================================================

def add_newsletter_subscriber(email, user_id=None, subscription_type='manual'):
    """
    Ajoute un nouvel abonné à la newsletter
    
    Args:
        email (str): Adresse email de l'abonné
        user_id (int): ID utilisateur si connecté (optionnel)
        subscription_type (str): Type d'abonnement ('manual', 'registration', 'premium')
    
    Returns:
        dict: Résultat de l'ajout
    """
    try:
        # Validation de l'email
        if not email or '@' not in email or '.' not in email:
            return {'success': False, 'error': 'Adresse email invalide'}
        
        email = email.lower().strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Vérification si l'email existe déjà
        cursor.execute('SELECT id FROM newsletter_subscribers WHERE email = ?', (email,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return {'success': False, 'error': 'Cet email est déjà abonné à la newsletter'}
        
        # Ajout du nouvel abonné
        cursor.execute('''
            INSERT INTO newsletter_subscribers (email, user_id, subscription_type, subscribed_at, is_active)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (email, user_id, subscription_type))
        
        subscriber_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'subscriber_id': subscriber_id, 'message': 'Abonnement à la newsletter confirmé !'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'abonnement: {str(e)}'}

def get_all_subscribers(filter_type=None):
    """
    Récupère tous les abonnés à la newsletter
    
    Args:
        filter_type (str): Filtre par type d'abonnement (optionnel)
    
    Returns:
        list: Liste des abonnés avec leurs informations
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête avec jointure utilisateur optionnelle
        query = '''
            SELECT ns.id, ns.email, ns.user_id, u.username, u.role, 
                   ns.subscription_type, ns.subscribed_at, ns.is_active
            FROM newsletter_subscribers ns
            LEFT JOIN users u ON ns.user_id = u.id
            WHERE ns.is_active = 1
        '''
        params = []
        
        # Application du filtre si fourni
        if filter_type:
            if filter_type in ['premium', 'lifetime']:
                query += ' AND u.role = ?'
                params.append(filter_type)
            elif filter_type == 'manual':
                query += ' AND ns.subscription_type = ?'
                params.append(filter_type)
        
        query += ' ORDER BY ns.subscribed_at DESC'
        
        cursor.execute(query, params)
        subscribers = cursor.fetchall()
        conn.close()
        
        subscribers_list = []
        for sub in subscribers:
            subscribers_list.append({
                'id': sub[0],
                'email': sub[1],
                'user_id': sub[2],
                'username': sub[3] if sub[3] else 'Non connecté',
                'user_role': sub[4] if sub[4] else 'guest',
                'subscription_type': sub[5],
                'subscribed_at': sub[6],
                'is_active': sub[7]
            })
        
        return subscribers_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des abonnés: {e}")
        return []

def unsubscribe_email(email):
    """
    Désabonne un email de la newsletter
    
    Args:
        email (str): Adresse email à désabonner
    
    Returns:
        dict: Résultat du désabonnement
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE newsletter_subscribers 
            SET is_active = 0, unsubscribed_at = CURRENT_TIMESTAMP 
            WHERE email = ? AND is_active = 1
        ''', (email.lower().strip(),))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Désabonnement effectué avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Email non trouvé ou déjà désabonné'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors du désabonnement: {str(e)}'}

# ============================================================================
# GESTION DES NEWSLETTERS
# ============================================================================

def create_newsletter(title, content, target_audience, market_info=None, partner_blocks=None, admin_id=None):
    """
    Crée une nouvelle newsletter
    
    Args:
        title (str): Titre de la newsletter
        content (str): Contenu principal
        target_audience (str): Public cible ('all', 'premium', 'lifetime', 'manual')
        market_info (str): Informations sur les marchés (optionnel)
        partner_blocks (list): Blocs partenaires avec offres (optionnel)
        admin_id (int): ID de l'admin créateur
    
    Returns:
        dict: Résultat de la création
    """
    try:
        # Validation des données obligatoires
        if not all([title, content, target_audience]):
            return {'success': False, 'error': 'Titre, contenu et audience cible sont requis'}
        
        # Validation de l'audience
        valid_audiences = ['all', 'premium', 'lifetime', 'manual']
        if target_audience not in valid_audiences:
            return {'success': False, 'error': 'Audience cible invalide'}
        
        # Préparation des données JSON
        newsletter_data = {
            'market_info': market_info,
            'partner_blocks': partner_blocks or [],
            'created_by': admin_id,
            'creation_timestamp': datetime.now().isoformat()
        }
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Insertion de la newsletter
        cursor.execute('''
            INSERT INTO newsletters (title, content, target_audience, newsletter_data, 
                                   created_at, status, created_by)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'draft', ?)
        ''', (title, content, target_audience, json.dumps(newsletter_data), admin_id))
        
        newsletter_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'newsletter_id': newsletter_id, 'message': 'Newsletter créée avec succès'}
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la création: {str(e)}'}

def get_newsletter_by_id(newsletter_id):
    """
    Récupère une newsletter par son ID
    
    Args:
        newsletter_id (int): ID de la newsletter
    
    Returns:
        dict: Données de la newsletter ou None
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, target_audience, newsletter_data, 
                   created_at, sent_at, status, created_by
            FROM newsletters
            WHERE id = ?
        ''', (newsletter_id,))
        
        newsletter = cursor.fetchone()
        conn.close()
        
        if newsletter:
            # Parse des données JSON
            newsletter_data = json.loads(newsletter[4]) if newsletter[4] else {}
            
            return {
                'id': newsletter[0],
                'title': newsletter[1],
                'content': newsletter[2],
                'target_audience': newsletter[3],
                'market_info': newsletter_data.get('market_info'),
                'partner_blocks': newsletter_data.get('partner_blocks', []),
                'created_at': newsletter[5],
                'sent_at': newsletter[6],
                'status': newsletter[7],
                'created_by': newsletter[8]
            }
        
        return None
        
    except Exception as e:
        print(f"Erreur lors de la récupération de la newsletter: {e}")
        return None

def get_all_newsletters(limit=50):
    """
    Récupère toutes les newsletters avec pagination
    
    Args:
        limit (int): Nombre maximum de newsletters à récupérer
    
    Returns:
        list: Liste des newsletters
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT n.id, n.title, n.target_audience, n.created_at, n.sent_at, 
                   n.status, u.username as created_by_name
            FROM newsletters n
            LEFT JOIN users u ON n.created_by = u.id
            ORDER BY n.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        newsletters = cursor.fetchall()
        conn.close()
        
        newsletters_list = []
        for newsletter in newsletters:
            newsletters_list.append({
                'id': newsletter[0],
                'title': newsletter[1],
                'target_audience': newsletter[2],
                'created_at': newsletter[3],
                'sent_at': newsletter[4],
                'status': newsletter[5],
                'created_by_name': newsletter[6] or 'Admin'
            })
        
        return newsletters_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération des newsletters: {e}")
        return []

def send_newsletter(newsletter_id, admin_id):
    """
    Marque une newsletter comme envoyée et simule l'envoi
    
    Args:
        newsletter_id (int): ID de la newsletter à envoyer
        admin_id (int): ID de l'admin qui envoie
    
    Returns:
        dict: Résultat de l'envoi avec statistiques
    """
    try:
        # Récupération de la newsletter
        newsletter = get_newsletter_by_id(newsletter_id)
        if not newsletter:
            return {'success': False, 'error': 'Newsletter non trouvée'}
        
        if newsletter['status'] == 'sent':
            return {'success': False, 'error': 'Cette newsletter a déjà été envoyée'}
        
        # Récupération des destinataires selon l'audience cible
        target_audience = newsletter['target_audience']
        recipients = get_newsletter_recipients(target_audience)
        
        if not recipients:
            return {'success': False, 'error': 'Aucun destinataire trouvé pour cette audience'}
        
        # Mise à jour du statut de la newsletter
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE newsletters 
            SET status = 'sent', sent_at = CURRENT_TIMESTAMP, sent_by = ?, recipients_count = ?
            WHERE id = ?
        ''', (admin_id, len(recipients), newsletter_id))
        
        # Enregistrement de l'envoi dans les logs
        cursor.execute('''
            INSERT INTO newsletter_sends (newsletter_id, admin_id, recipients_count, sent_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (newsletter_id, admin_id, len(recipients)))
        
        conn.commit()
        conn.close()
        
        # Simulation de l'envoi (logs détaillés)
        print(f"📧 ENVOI DE NEWSLETTER SIMULÉ")
        print(f"📧 Newsletter: {newsletter['title']}")
        print(f"📧 Audience: {target_audience}")
        print(f"📧 Destinataires: {len(recipients)}")
        print(f"📧 Admin: {admin_id}")
        print(f"📧 Date: {datetime.now()}")
        
        return {
            'success': True, 
            'message': f'Newsletter envoyée avec succès à {len(recipients)} destinataires',
            'recipients_count': len(recipients),
            'recipients_emails': [r['email'] for r in recipients[:10]]  # 10 premiers emails pour vérification
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'envoi: {str(e)}'}

def get_newsletter_recipients(target_audience):
    """
    Récupère la liste des destinataires selon l'audience cible
    
    Args:
        target_audience (str): Type d'audience ('all', 'premium', 'lifetime', 'manual')
    
    Returns:
        list: Liste des emails destinataires
    """
    try:
        if target_audience == 'all':
            return get_all_subscribers()
        elif target_audience in ['premium', 'lifetime']:
            return get_all_subscribers(filter_type=target_audience)
        elif target_audience == 'manual':
            return get_all_subscribers(filter_type='manual')
        else:
            return []
    except Exception as e:
        print(f"Erreur lors de la récupération des destinataires: {e}")
        return []

# ============================================================================
# GESTION DU CONTENU AUTOMATISÉ
# ============================================================================

def get_market_info_template():
    """
    Retourne un template d'informations de marché pour la semaine
    
    Returns:
        dict: Template avec sections prédéfinies
    """
    return {
        'forex_highlights': {
            'title': 'Forex - Points Clés de la Semaine',
            'content': 'EUR/USD, GBP/USD, USD/JPY - Analyse des mouvements principaux et perspectives'
        },
        'crypto_updates': {
            'title': 'Crypto - Actualités Importantes',
            'content': 'Bitcoin, Ethereum, altcoins - Événements marquants et impact sur les prix'
        },
        'commodities': {
            'title': 'Matières Premières',
            'content': 'Or, Pétrole, Métaux précieux - Tendances et facteurs d\'influence'
        },
        'economic_calendar': {
            'title': 'Calendrier Économique',
            'content': 'Événements économiques majeurs à surveiller cette semaine'
        }
    }

def create_partner_block(title, description, link, discount_code=None, is_featured=False):
    """
    Crée un bloc partenaire pour la newsletter
    
    Args:
        title (str): Titre de l'offre partenaire
        description (str): Description de l'offre
        link (str): Lien d'affiliation
        discount_code (str): Code promo (optionnel)
        is_featured (bool): Offre mise en avant
    
    Returns:
        dict: Bloc partenaire formaté
    """
    return {
        'title': title,
        'description': description,
        'link': link,
        'discount_code': discount_code,
        'is_featured': is_featured,
        'created_at': datetime.now().isoformat()
    }

def generate_newsletter_preview(newsletter_id):
    """
    Génère un aperçu HTML de la newsletter
    
    Args:
        newsletter_id (int): ID de la newsletter
    
    Returns:
        str: HTML de prévisualisation
    """
    try:
        newsletter = get_newsletter_by_id(newsletter_id)
        if not newsletter:
            return "<p>Newsletter non trouvée</p>"
        
        # Template HTML de base pour la newsletter
        title = newsletter['title']
        content = newsletter['content'].replace('\n', '<br>')
        market_section = generate_market_section_html(newsletter.get('market_info', ''))
        partner_section = generate_partner_blocks_html(newsletter.get('partner_blocks', []))
        
        html_preview = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .market-section {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .partner-block {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .featured {{ border-color: #ffc107; background: #fff3cd; }}
                .footer {{ background: #343a40; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 MindTraderPro Newsletter</h1>
                <h2>{title}</h2>
            </div>
            
            <div class="content">
                <p>{content}</p>
                
                {market_section}
                
                {partner_section}
            </div>
            
            <div class="footer">
                <p>📧 Vous recevez cet email car vous êtes abonné à la newsletter MindTraderPro</p>
                <p>🔗 <a href="#" style="color: #ffc107;">Se désabonner</a> | <a href="#" style="color: #ffc107;">Voir en ligne</a></p>
            </div>
        </body>
        </html>
        '''
        
        return html_preview
        
    except Exception as e:
        return f"<p>Erreur lors de la génération de l'aperçu: {str(e)}</p>"

def generate_market_section_html(market_info):
    """Génère le HTML pour la section marchés"""
    if not market_info:
        return ""
    
    content = market_info.replace('\n', '<br>')
    return f'''
    <div class="market-section">
        <h3>📊 Actualités des Marchés</h3>
        <p>{content}</p>
    </div>
    '''

def generate_partner_blocks_html(partner_blocks):
    """Génère le HTML pour les blocs partenaires"""
    if not partner_blocks:
        return ""
    
    html = '<h3>🤝 Offres Partenaires</h3>'
    
    for block in partner_blocks:
        featured_class = 'featured' if block.get('is_featured') else ''
        discount_html = f"<p><strong>Code promo: {block['discount_code']}</strong></p>" if block.get('discount_code') else ""
        
        html += f'''
        <div class="partner-block {featured_class}">
            <h4>{block['title']}</h4>
            <p>{block['description']}</p>
            {discount_html}
            <p><a href="{block['link']}" style="color: #dc3545; font-weight: bold;">Découvrir l'offre →</a></p>
        </div>
        '''
    
    return html

# ============================================================================
# EXPORT ET STATISTIQUES
# ============================================================================

def export_subscribers_csv():
    """
    Génère un export CSV des abonnés
    
    Returns:
        str: Contenu CSV des abonnés
    """
    try:
        subscribers = get_all_subscribers()
        
        csv_content = "Email,Type_Abonnement,Date_Inscription,Utilisateur,Role\n"
        
        for sub in subscribers:
            csv_content += f"{sub['email']},{sub['subscription_type']},{sub['subscribed_at']},{sub['username']},{sub['user_role']}\n"
        
        return csv_content
        
    except Exception as e:
        print(f"Erreur lors de l'export CSV: {e}")
        return "Email,Erreur\nErreur lors de l'export des données"

def get_newsletter_statistics():
    """
    Récupère les statistiques de la newsletter
    
    Returns:
        dict: Statistiques complètes
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Statistiques des abonnés
        cursor.execute('SELECT COUNT(*) FROM newsletter_subscribers WHERE is_active = 1')
        total_subscribers = cursor.fetchone()[0]
        
        cursor.execute('SELECT subscription_type, COUNT(*) FROM newsletter_subscribers WHERE is_active = 1 GROUP BY subscription_type')
        subscribers_by_type = dict(cursor.fetchall())
        
        # Statistiques des newsletters
        cursor.execute('SELECT COUNT(*) FROM newsletters')
        total_newsletters = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM newsletters WHERE status = "sent"')
        sent_newsletters = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_subscribers': total_subscribers,
            'subscribers_by_type': subscribers_by_type,
            'total_newsletters': total_newsletters,
            'sent_newsletters': sent_newsletters,
            'draft_newsletters': total_newsletters - sent_newsletters
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

# ============================================================================
# INITIALISATION DES TABLES NEWSLETTER
# ============================================================================

def init_newsletter_tables():
    """
    Initialise les tables nécessaires pour la newsletter
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des abonnés newsletter
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                subscription_type TEXT DEFAULT 'manual',
                subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                unsubscribed_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des newsletters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                newsletter_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sent_at DATETIME,
                status TEXT DEFAULT 'draft',
                created_by INTEGER,
                sent_by INTEGER,
                recipients_count INTEGER DEFAULT 0,
                FOREIGN KEY (created_by) REFERENCES users (id),
                FOREIGN KEY (sent_by) REFERENCES users (id)
            )
        ''')
        
        # Table des envois newsletter (pour statistiques)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_sends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                newsletter_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                recipients_count INTEGER NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (newsletter_id) REFERENCES newsletters (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Tables newsletter initialisées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation des tables newsletter: {e}")

# Initialisation automatique des tables
init_newsletter_tables()