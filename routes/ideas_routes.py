"""
Routes pour le module Boîte à idées et messages utilisateurs - MindTraderPro
Système complet de feedback et suggestions utilisateurs
"""

import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash

ideas_bp = Blueprint('ideas', __name__)

# Configuration des chemins de stockage
DATA_FOLDER = 'data'
IDEAS_FILE = os.path.join(DATA_FOLDER, 'ideas.json')
MESSAGES_FILE = os.path.join(DATA_FOLDER, 'messages.json')
ADMIN_PASSWORD = 'admin123'  # Mot de passe simple pour commencer

def ensure_data_folder():
    """Crée le dossier data s'il n'existe pas"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

def load_json_file(filename):
    """Charge un fichier JSON, retourne une liste vide si le fichier n'existe pas"""
    ensure_data_folder()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_json_file(filename, data):
    """Sauvegarde des données dans un fichier JSON"""
    ensure_data_folder()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_client_ip():
    """Récupère l'IP du client pour éviter les votes multiples"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))

# =============================================================================
# 📨 1. PAGE CONTACT
# =============================================================================

@ideas_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Page de contact pour les messages utilisateurs"""
    if request.method == 'GET':
        return render_template('contact.html')
    
    try:
        # Récupération des données du formulaire
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation du message (obligatoire)
        if not message:
            flash('Le message est obligatoire !', 'error')
            return render_template('contact.html')
        
        # Création du message
        new_message = {
            'id': str(uuid.uuid4()),
            'name': name if name else 'Anonyme',
            'email': email if email else 'Non fourni',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'ip': get_client_ip(),
            'read': False
        }
        
        # Chargement et sauvegarde
        messages = load_json_file(MESSAGES_FILE)
        messages.append(new_message)
        save_json_file(MESSAGES_FILE, messages)
        
        flash('✅ Votre message a été envoyé avec succès ! Merci pour votre retour.', 'success')
        return redirect(url_for('ideas.contact'))
        
    except Exception as e:
        flash(f'❌ Erreur lors de l\'envoi: {str(e)}', 'error')
        return render_template('contact.html')

# =============================================================================
# 💡 2. PAGE PROPOSER UNE IDÉE
# =============================================================================

@ideas_bp.route('/ideas', methods=['GET', 'POST'])
def submit_idea():
    """Page pour proposer une nouvelle idée"""
    if request.method == 'GET':
        return render_template('submit_idea.html')
    
    try:
        # Récupération des données du formulaire
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'suggestion').strip()
        username = request.form.get('username', '').strip()
        
        # Validation des champs obligatoires
        if not title or not description:
            flash('Le titre et la description sont obligatoires !', 'error')
            return render_template('submit_idea.html')
        
        # Création de l'idée
        new_idea = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'category': category,
            'username': username if username else 'Utilisateur anonyme',
            'votes': 0,
            'voters': [],  # Liste des IPs qui ont voté
            'status': 'pending',  # pending, accepted, rejected, in_development
            'timestamp': datetime.now().isoformat(),
            'ip': get_client_ip()
        }
        
        # Chargement et sauvegarde
        ideas = load_json_file(IDEAS_FILE)
        ideas.append(new_idea)
        save_json_file(IDEAS_FILE, ideas)
        
        flash('✅ Votre idée a été soumise avec succès ! Elle apparaîtra bientôt dans la liste.', 'success')
        return redirect(url_for('ideas.list_ideas'))
        
    except Exception as e:
        flash(f'❌ Erreur lors de la soumission: {str(e)}', 'error')
        return render_template('submit_idea.html')

# =============================================================================
# 👍 3. PAGE VOIR LES IDÉES
# =============================================================================

@ideas_bp.route('/ideas/list')
def list_ideas():
    """Affiche toutes les idées avec possibilité de voter"""
    ideas = load_json_file(IDEAS_FILE)
    
    # Filtrer les idées (ne pas afficher les refusées)
    visible_ideas = [idea for idea in ideas if idea.get('status') != 'rejected']
    
    # Tri par nombre de votes (décroissant)
    visible_ideas.sort(key=lambda x: x.get('votes', 0), reverse=True)
    
    # Ajouter l'information si l'utilisateur a déjà voté
    client_ip = get_client_ip()
    for idea in visible_ideas:
        idea['user_voted'] = client_ip in idea.get('voters', [])
    
    return render_template('list_ideas.html', ideas=visible_ideas)

@ideas_bp.route('/ideas/vote/<idea_id>', methods=['POST'])
def vote_idea(idea_id):
    """Permet de voter pour une idée (1 vote par IP)"""
    try:
        client_ip = get_client_ip()
        ideas = load_json_file(IDEAS_FILE)
        
        # Trouver l'idée
        idea_found = False
        for idea in ideas:
            if idea['id'] == idea_id:
                idea_found = True
                
                # Vérifier si l'utilisateur a déjà voté
                if client_ip in idea.get('voters', []):
                    return jsonify({
                        'success': False, 
                        'message': 'Vous avez déjà voté pour cette idée !'
                    })
                
                # Ajouter le vote
                if 'voters' not in idea:
                    idea['voters'] = []
                idea['voters'].append(client_ip)
                idea['votes'] = len(idea['voters'])
                break
        
        if not idea_found:
            return jsonify({'success': False, 'message': 'Idée introuvable'})
        
        # Sauvegarder
        save_json_file(IDEAS_FILE, ideas)
        
        return jsonify({
            'success': True, 
            'message': '✅ Vote enregistré !', 
            'new_votes': idea['votes']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# =============================================================================
# 🛠️ 4. PAGE ADMIN IDÉES
# =============================================================================

@ideas_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion admin"""
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        flash('✅ Connexion admin réussie !', 'success')
        return redirect(url_for('ideas.admin_ideas'))
    else:
        flash('❌ Mot de passe incorrect !', 'error')
        return render_template('admin_login.html')

@ideas_bp.route('/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.pop('admin_logged_in', None)
    flash('✅ Déconnexion réussie !', 'success')
    return redirect(url_for('ideas.admin_login'))

@ideas_bp.route('/admin/ideas')
def admin_ideas():
    """Page d'administration des idées (protégée par mot de passe)"""
    if not session.get('admin_logged_in'):
        flash('⚠️ Accès refusé. Connexion admin requise.', 'error')
        return redirect(url_for('ideas.admin_login'))
    
    ideas = load_json_file(IDEAS_FILE)
    messages = load_json_file(MESSAGES_FILE)
    
    # Tri des idées par votes décroissants
    ideas.sort(key=lambda x: x.get('votes', 0), reverse=True)
    
    # Statistiques
    stats = {
        'total_ideas': len(ideas),
        'pending': len([i for i in ideas if i.get('status') == 'pending']),
        'accepted': len([i for i in ideas if i.get('status') == 'accepted']),
        'in_development': len([i for i in ideas if i.get('status') == 'in_development']),
        'rejected': len([i for i in ideas if i.get('status') == 'rejected']),
        'total_messages': len(messages),
        'unread_messages': len([m for m in messages if not m.get('read', False)])
    }
    
    return render_template('admin_ideas.html', ideas=ideas, messages=messages, stats=stats)

@ideas_bp.route('/admin/ideas/update_status', methods=['POST'])
def update_idea_status():
    """Met à jour le statut d'une idée"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Accès refusé'})
    
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        new_status = data.get('status')
        
        if new_status not in ['pending', 'accepted', 'rejected', 'in_development']:
            return jsonify({'success': False, 'message': 'Statut invalide'})
        
        ideas = load_json_file(IDEAS_FILE)
        
        # Mettre à jour l'idée
        idea_found = False
        for idea in ideas:
            if idea['id'] == idea_id:
                idea['status'] = new_status
                idea['updated_at'] = datetime.now().isoformat()
                idea_found = True
                break
        
        if not idea_found:
            return jsonify({'success': False, 'message': 'Idée introuvable'})
        
        save_json_file(IDEAS_FILE, ideas)
        
        return jsonify({
            'success': True, 
            'message': f'✅ Statut mis à jour: {new_status}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@ideas_bp.route('/admin/messages/mark_read', methods=['POST'])
def mark_message_read():
    """Marque un message comme lu"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Accès refusé'})
    
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        
        messages = load_json_file(MESSAGES_FILE)
        
        # Marquer comme lu
        message_found = False
        for message in messages:
            if message['id'] == message_id:
                message['read'] = True
                message['read_at'] = datetime.now().isoformat()
                message_found = True
                break
        
        if not message_found:
            return jsonify({'success': False, 'message': 'Message introuvable'})
        
        save_json_file(MESSAGES_FILE, messages)
        
        return jsonify({'success': True, 'message': '✅ Message marqué comme lu'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})