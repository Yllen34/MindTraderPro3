"""
Routes Suggestions Communautaires - Interface pour les utilisateurs
Permet de proposer des idées et voter pour celles des autres
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps

# Import des modules de suggestions
from modules.suggestion_manager import (
    create_suggestion, get_all_suggestions, get_suggestion_by_id,
    update_suggestion, delete_suggestion, toggle_vote, get_user_votes,
    update_suggestion_status, get_suggestions_statistics, simulate_feature_implementation
)

# Création du blueprint pour les routes suggestions
suggestion_bp = Blueprint('suggestions', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ
# ============================================================================

def login_required(f):
    """Décorateur pour s'assurer que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour accéder aux suggestions')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour les fonctionnalités administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise')
        
        user_role = session.get('role', 'standard')
        if user_role != 'admin':
            return redirect('/suggestions?message=Accès administrateur requis')
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Récupère les informations de l'utilisateur actuel"""
    if 'user_id' in session:
        return {
            'id': session['user_id'],
            'username': session.get('username', 'Utilisateur'),
            'role': session.get('role', 'standard')
        }
    return None

# ============================================================================
# INTERFACE PRINCIPALE DES SUGGESTIONS
# ============================================================================

@suggestion_bp.route('/suggestions')
@login_required
def suggestions_page():
    """Page principale des suggestions communautaires"""
    try:
        user = get_current_user()
        
        # Récupération des paramètres de tri et filtrage
        sort_by = request.args.get('sort', 'recent')  # recent, popular, my_ideas
        filter_type = request.args.get('filter', 'all')  # all, proposed, accepted, refused
        
        # Récupération des suggestions selon les filtres
        suggestions = get_all_suggestions(
            limit=50, 
            offset=0, 
            sort_by=sort_by, 
            user_id=user['id'], 
            filter_type=filter_type
        )
        
        # Construction de l'interface HTML complète
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Suggestions Communautaires - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .suggestions-header {{
                    background: linear-gradient(135deg, #6f42c1, #e83e8c);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .suggestion-card {{
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .suggestion-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                .vote-button {{
                    transition: all 0.3s ease;
                }}
                .vote-button:hover {{
                    transform: scale(1.1);
                }}
                .vote-button.voted {{
                    background: #28a745;
                    border-color: #28a745;
                    color: white;
                }}
                .status-badge {{
                    font-size: 0.75rem;
                    padding: 4px 8px;
                }}
                .suggestion-description {{
                    max-height: 150px;
                    overflow-y: auto;
                }}
                .filter-section {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1050;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Suggestions -->
            <div class="suggestions-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-lightbulb me-3"></i>Suggestions Communautaires</h1>
                            <p class="mb-0">Proposez vos idées et votez pour celles des autres traders</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-light text-dark fs-6">
                                <i class="fas fa-user me-1"></i>{user['username']}
                            </span>
                            <a href="/" class="btn btn-outline-light ms-2">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Section filtres et tri -->
                <div class="filter-section">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <label class="form-label">Trier par :</label>
                            <select class="form-select" id="sortBy" onchange="applySortFilter()">
                                <option value="recent" {'selected' if sort_by == 'recent' else ''}>Plus récent</option>
                                <option value="popular" {'selected' if sort_by == 'popular' else ''}>Plus populaire</option>
                                <option value="my_ideas" {'selected' if sort_by == 'my_ideas' else ''}>Mes idées</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Filtrer par statut :</label>
                            <select class="form-select" id="filterBy" onchange="applySortFilter()">
                                <option value="all" {'selected' if filter_type == 'all' else ''}>Toutes</option>
                                <option value="proposed" {'selected' if filter_type == 'proposed' else ''}>Proposées</option>
                                <option value="accepted" {'selected' if filter_type == 'accepted' else ''}>Acceptées</option>
                                <option value="refused" {'selected' if filter_type == 'refused' else ''}>Refusées</option>
                            </select>
                        </div>
                        <div class="col-md-6 text-end">
                            <button class="btn btn-success btn-lg" data-bs-toggle="modal" data-bs-target="#addSuggestionModal">
                                <i class="fas fa-plus me-2"></i>Proposer une Idée
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des suggestions -->
                <div class="row" id="suggestionsContainer">'''
        
        # Génération des cartes de suggestions
        for suggestion in suggestions:
            # Détermination du badge de statut
            status_badges = {
                'proposed': 'badge bg-primary status-badge',
                'accepted': 'badge bg-success status-badge',
                'refused': 'badge bg-danger status-badge',
                'archived': 'badge bg-secondary status-badge'
            }
            status_badge = status_badges.get(suggestion['status'], 'badge bg-secondary status-badge')
            
            # Classes CSS pour le bouton de vote
            vote_class = 'vote-button voted' if suggestion['user_has_voted'] else 'vote-button'
            vote_icon = 'fas fa-heart' if suggestion['user_has_voted'] else 'far fa-heart'
            
            # Boutons d'action pour l'auteur
            author_actions = ''
            if suggestion['user_id'] == user['id']:
                author_actions = f'''
                    <button class="btn btn-outline-primary btn-sm me-1" onclick="editSuggestion({suggestion['id']})">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="btn btn-outline-danger btn-sm" onclick="deleteSuggestion({suggestion['id']})">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                '''
            
            html_content += f'''
                    <div class="col-lg-6 mb-4">
                        <div class="card suggestion-card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">{suggestion['title']}</h6>
                                    <small class="text-muted">par <strong>{suggestion['username']}</strong></small>
                                </div>
                                <span class="{status_badge}">{suggestion['status'].upper()}</span>
                            </div>
                            <div class="card-body">
                                <div class="suggestion-description">
                                    <p class="card-text">{suggestion['description']}</p>
                                </div>
                                
                                <div class="d-flex justify-content-between align-items-center mt-3">
                                    <div class="d-flex align-items-center">
                                        <button class="btn btn-outline-success {vote_class}" 
                                                onclick="toggleVote({suggestion['id']}, this)"
                                                data-suggestion-id="{suggestion['id']}">
                                            <i class="{vote_icon} me-1"></i>
                                            <span class="vote-count">{suggestion['vote_count']}</span>
                                        </button>
                                        <small class="text-muted ms-3">
                                            <i class="fas fa-calendar-alt me-1"></i>
                                            {suggestion['created_at'][:10] if suggestion['created_at'] else 'N/A'}
                                        </small>
                                    </div>
                                    <div>
                                        {author_actions}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>'''
        
        if not suggestions:
            html_content += '''
                    <div class="col-12">
                        <div class="text-center py-5">
                            <i class="fas fa-lightbulb fa-4x text-muted mb-3"></i>
                            <h4 class="text-muted">Aucune suggestion trouvée</h4>
                            <p class="text-muted">Soyez le premier à proposer une idée innovante !</p>
                            <button class="btn btn-success btn-lg" data-bs-toggle="modal" data-bs-target="#addSuggestionModal">
                                <i class="fas fa-plus me-2"></i>Proposer une Idée
                            </button>
                        </div>
                    </div>'''
        
        html_content += '''
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Modal d'ajout de suggestion -->
            <div class="modal fade" id="addSuggestionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-lightbulb me-2"></i>Proposer une Nouvelle Idée
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addSuggestionForm">
                                <div class="mb-3">
                                    <label class="form-label">Titre de l'idée <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" id="suggestionTitle" 
                                           placeholder="Ex: Alertes de prix par SMS" maxlength="200" required>
                                    <div class="form-text">Maximum 200 caractères</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description détaillée <span class="text-danger">*</span></label>
                                    <textarea class="form-control" id="suggestionDescription" rows="6" 
                                              placeholder="Décrivez votre idée en détail : comment ça fonctionnerait, pourquoi c'est utile, etc." 
                                              maxlength="2000" required></textarea>
                                    <div class="form-text">Maximum 2000 caractères</div>
                                </div>
                                
                                <div class="alert alert-info">
                                    <h6><i class="fas fa-info-circle me-2"></i>Conseils pour une bonne suggestion</h6>
                                    <ul class="mb-0">
                                        <li>Soyez précis sur le problème à résoudre</li>
                                        <li>Expliquez comment votre idée améliorerait l'expérience</li>
                                        <li>Donnez des exemples concrets d'utilisation</li>
                                        <li>Mentionnez si d'autres plateformes ont des fonctionnalités similaires</li>
                                    </ul>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Annuler
                            </button>
                            <button type="button" class="btn btn-success" onclick="submitSuggestion()">
                                <i class="fas fa-paper-plane me-1"></i>Proposer l'Idée
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modal de modification -->
            <div class="modal fade" id="editSuggestionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-edit me-2"></i>Modifier la Suggestion
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editSuggestionForm">
                                <input type="hidden" id="editSuggestionId">
                                <div class="mb-3">
                                    <label class="form-label">Titre <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" id="editSuggestionTitle" 
                                           maxlength="200" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description <span class="text-danger">*</span></label>
                                    <textarea class="form-control" id="editSuggestionDescription" rows="6" 
                                              maxlength="2000" required></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="submitEditSuggestion()">
                                <i class="fas fa-save me-1"></i>Sauvegarder
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // ============================================================================
                // JAVASCRIPT POUR LES SUGGESTIONS COMMUNAUTAIRES
                // ============================================================================
                
                // Fonction pour afficher des notifications
                function showNotification(message, type = 'success') {{
                    const notificationArea = document.getElementById('notification-area');
                    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
                    
                    const notification = document.createElement('div');
                    notification.className = `alert ${{alertClass}} alert-dismissible fade show notification`;
                    notification.innerHTML = `
                        ${{message}}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    
                    notificationArea.appendChild(notification);
                    
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            notification.remove();
                        }}
                    }}, 5000);
                }}
                
                // Application des filtres et tri
                function applySortFilter() {{
                    const sortBy = document.getElementById('sortBy').value;
                    const filterBy = document.getElementById('filterBy').value;
                    
                    const params = new URLSearchParams();
                    if (sortBy) params.append('sort', sortBy);
                    if (filterBy && filterBy !== 'all') params.append('filter', filterBy);
                    
                    window.location.href = '/suggestions?' + params.toString();
                }}
                
                // Soumission d'une nouvelle suggestion
                function submitSuggestion() {{
                    const title = document.getElementById('suggestionTitle').value.trim();
                    const description = document.getElementById('suggestionDescription').value.trim();
                    
                    if (!title || !description) {{
                        showNotification('❌ Titre et description sont requis', 'error');
                        return;
                    }}
                    
                    const formData = {{
                        title: title,
                        description: description
                    }};
                    
                    fetch('/suggestions/create', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(formData)
                    }})
                    .then(response => response.json())
                    .then(result => {{
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            bootstrap.Modal.getInstance(document.getElementById('addSuggestionModal')).hide();
                            document.getElementById('addSuggestionForm').reset();
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }})
                    .catch(error => {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }});
                }}
                
                // Toggle vote sur une suggestion
                async function toggleVote(suggestionId, buttonElement) {{
                    try {{
                        const response = await fetch('/suggestions/vote', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ suggestion_id: suggestionId }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            // Mise à jour de l'interface
                            const voteCount = buttonElement.querySelector('.vote-count');
                            const icon = buttonElement.querySelector('i');
                            
                            voteCount.textContent = result.new_vote_count;
                            
                            if (result.user_has_voted) {{
                                buttonElement.classList.add('voted');
                                icon.className = 'fas fa-heart me-1';
                            }} else {{
                                buttonElement.classList.remove('voted');
                                icon.className = 'far fa-heart me-1';
                            }}
                            
                            showNotification('✅ ' + result.message, 'success');
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur lors du vote', 'error');
                    }}
                }}
                
                // Modification d'une suggestion
                function editSuggestion(suggestionId) {{
                    fetch(`/suggestions/get/${{suggestionId}}`)
                    .then(response => response.json())
                    .then(result => {{
                        if (result.success) {{
                            const suggestion = result.suggestion;
                            document.getElementById('editSuggestionId').value = suggestionId;
                            document.getElementById('editSuggestionTitle').value = suggestion.title;
                            document.getElementById('editSuggestionDescription').value = suggestion.description;
                            
                            new bootstrap.Modal(document.getElementById('editSuggestionModal')).show();
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }});
                }}
                
                // Soumission de la modification
                function submitEditSuggestion() {{
                    const suggestionId = document.getElementById('editSuggestionId').value;
                    const title = document.getElementById('editSuggestionTitle').value.trim();
                    const description = document.getElementById('editSuggestionDescription').value.trim();
                    
                    if (!title || !description) {{
                        showNotification('❌ Titre et description sont requis', 'error');
                        return;
                    }}
                    
                    fetch('/suggestions/update', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            suggestion_id: suggestionId,
                            title: title,
                            description: description
                        }})
                    }})
                    .then(response => response.json())
                    .then(result => {{
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            bootstrap.Modal.getInstance(document.getElementById('editSuggestionModal')).hide();
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }});
                }}
                
                // Suppression d'une suggestion
                function deleteSuggestion(suggestionId) {{
                    if (confirm('Êtes-vous sûr de vouloir supprimer cette suggestion ? Cette action est irréversible.')) {{
                        fetch('/suggestions/delete', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ suggestion_id: suggestionId }})
                        }})
                        .then(response => response.json())
                        .then(result => {{
                            if (result.success) {{
                                showNotification('✅ ' + result.message, 'success');
                                setTimeout(() => {{ window.location.reload(); }}, 2000);
                            }} else {{
                                showNotification('❌ ' + result.error, 'error');
                            }}
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement des suggestions: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES ACTIONS SUR LES SUGGESTIONS
# ============================================================================

@suggestion_bp.route('/suggestions/create', methods=['POST'])
@login_required
def api_create_suggestion():
    """API pour créer une nouvelle suggestion"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        title = data.get('title')
        description = data.get('description')
        
        if not title or not description:
            return jsonify({'success': False, 'error': 'Titre et description requis'})
        
        result = create_suggestion(user['id'], title, description)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@suggestion_bp.route('/suggestions/vote', methods=['POST'])
@login_required
def api_vote_suggestion():
    """API pour voter ou retirer son vote sur une suggestion"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        suggestion_id = data.get('suggestion_id')
        
        if not suggestion_id:
            return jsonify({'success': False, 'error': 'ID suggestion requis'})
        
        result = toggle_vote(suggestion_id, user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@suggestion_bp.route('/suggestions/get/<int:suggestion_id>')
@login_required
def api_get_suggestion(suggestion_id):
    """API pour récupérer une suggestion spécifique"""
    try:
        user = get_current_user()
        suggestion = get_suggestion_by_id(suggestion_id, user['id'])
        
        if suggestion:
            return jsonify({'success': True, 'suggestion': suggestion})
        else:
            return jsonify({'success': False, 'error': 'Suggestion non trouvée'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@suggestion_bp.route('/suggestions/update', methods=['POST'])
@login_required
def api_update_suggestion():
    """API pour modifier une suggestion"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        suggestion_id = data.get('suggestion_id')
        title = data.get('title')
        description = data.get('description')
        
        if not all([suggestion_id, title, description]):
            return jsonify({'success': False, 'error': 'Tous les champs sont requis'})
        
        result = update_suggestion(suggestion_id, user['id'], title, description)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@suggestion_bp.route('/suggestions/delete', methods=['POST'])
@login_required
def api_delete_suggestion():
    """API pour supprimer une suggestion"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        suggestion_id = data.get('suggestion_id')
        
        if not suggestion_id:
            return jsonify({'success': False, 'error': 'ID suggestion requis'})
        
        result = delete_suggestion(suggestion_id, user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# ROUTES ADMINISTRATIVES (INTÉGRÉES)
# ============================================================================

@suggestion_bp.route('/admin/suggestions')
@admin_required
def admin_suggestions_page():
    """Interface d'administration des suggestions"""
    try:
        # Récupération de toutes les suggestions pour l'admin
        suggestions = get_all_suggestions(limit=100, sort_by='recent')
        stats = get_suggestions_statistics()
        
        # Construction de l'interface admin
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Administration - Suggestions Communautaires</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .admin-header {{
                    background: linear-gradient(135deg, #dc3545, #ffc107);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .suggestion-admin-card {{
                    margin-bottom: 15px;
                    border-radius: 8px;
                }}
                .status-proposed {{ border-left: 4px solid #007bff; }}
                .status-accepted {{ border-left: 4px solid #28a745; }}
                .status-refused {{ border-left: 4px solid #dc3545; }}
                .status-archived {{ border-left: 4px solid #6c757d; }}
                .notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1050;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Admin -->
            <div class="admin-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-cogs me-3"></i>Administration - Suggestions</h1>
                            <p class="mb-0">Gestion des suggestions communautaires</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/admin" class="btn btn-outline-light">
                                <i class="fas fa-arrow-left me-1"></i>Retour Admin
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Statistiques -->
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <i class="fas fa-lightbulb fa-2x text-primary mb-2"></i>
                                <h3>{stats.get('total_suggestions', 0)}</h3>
                                <small class="text-muted">Suggestions Total</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <i class="fas fa-heart fa-2x text-danger mb-2"></i>
                                <h3>{stats.get('total_votes', 0)}</h3>
                                <small class="text-muted">Votes Total</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                                <h3>{stats.get('status_stats', {}).get('accepted', 0)}</h3>
                                <small class="text-muted">Acceptées</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <i class="fas fa-clock fa-2x text-warning mb-2"></i>
                                <h3>{stats.get('status_stats', {}).get('proposed', 0)}</h3>
                                <small class="text-muted">En Attente</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des suggestions pour administration -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list me-2"></i>Toutes les Suggestions</h5>
                    </div>
                    <div class="card-body">'''
        
        # Génération des suggestions pour l'admin
        for suggestion in suggestions:
            status_class = f"status-{suggestion['status']}"
            
            html_content += f'''
                        <div class="card suggestion-admin-card {status_class}">
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-8">
                                        <h6 class="card-title">{suggestion['title']}</h6>
                                        <p class="card-text text-muted">{suggestion['description'][:200]}{'...' if len(suggestion['description']) > 200 else ''}</p>
                                        <small class="text-muted">
                                            Par <strong>{suggestion['username']}</strong> | 
                                            {suggestion['vote_count']} votes | 
                                            {suggestion['created_at'][:10] if suggestion['created_at'] else 'N/A'}
                                        </small>
                                    </div>
                                    <div class="col-md-4 text-end">
                                        <div class="mb-2">
                                            <span class="badge bg-{{'primary' if suggestion['status'] == 'proposed' else 'success' if suggestion['status'] == 'accepted' else 'danger' if suggestion['status'] == 'refused' else 'secondary'}}">
                                                {suggestion['status'].upper()}
                                            </span>
                                        </div>
                                        <div class="btn-group-vertical btn-group-sm">
                                            <button class="btn btn-success" onclick="updateStatus({suggestion['id']}, 'accepted')">
                                                <i class="fas fa-check"></i> Accepter
                                            </button>
                                            <button class="btn btn-danger" onclick="updateStatus({suggestion['id']}, 'refused')">
                                                <i class="fas fa-times"></i> Refuser
                                            </button>
                                            <button class="btn btn-secondary" onclick="updateStatus({suggestion['id']}, 'archived')">
                                                <i class="fas fa-archive"></i> Archiver
                                            </button>
                                            {'<button class="btn btn-warning" onclick="simulateImplementation(' + str(suggestion['id']) + ')"><i class="fas fa-cog"></i> Implémenter</button>' if suggestion['status'] == 'accepted' else ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>'''
        
        if not suggestions:
            html_content += '''
                        <div class="text-center py-4">
                            <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">Aucune suggestion</h5>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Fonction pour afficher des notifications
                function showNotification(message, type = 'success') {
                    const notificationArea = document.getElementById('notification-area');
                    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
                    
                    const notification = document.createElement('div');
                    notification.className = `alert ${alertClass} alert-dismissible fade show notification`;
                    notification.innerHTML = `
                        ${message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    
                    notificationArea.appendChild(notification);
                    
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 5000);
                }
                
                // Mise à jour du statut d'une suggestion
                async function updateStatus(suggestionId, newStatus) {
                    try {
                        const response = await fetch('/suggestions/admin/update-status', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                suggestion_id: suggestionId,
                                new_status: newStatus
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            setTimeout(() => { window.location.reload(); }, 2000);
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }
                
                // Simulation d'implémentation
                async function simulateImplementation(suggestionId) {
                    try {
                        const response = await fetch('/suggestions/admin/simulate-implementation', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ suggestion_id: suggestionId })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            let message = '🚀 ' + result.message + '\\n\\n';
                            message += 'Étapes prévues:\\n';
                            result.steps.forEach((step, index) => {
                                message += `${index + 1}. ${step}\\n`;
                            });
                            message += `\\nTemps estimé: ${result.estimated_time}`;
                            message += `\\nPriorité: ${result.priority}`;
                            
                            alert(message);
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de l'admin suggestions: {str(e)}</p>"

@suggestion_bp.route('/suggestions/admin/update-status', methods=['POST'])
@admin_required
def api_admin_update_status():
    """API admin pour changer le statut d'une suggestion"""
    try:
        admin = get_current_user()
        data = request.get_json()
        
        suggestion_id = data.get('suggestion_id')
        new_status = data.get('new_status')
        
        if not suggestion_id or not new_status:
            return jsonify({'success': False, 'error': 'Paramètres requis manquants'})
        
        result = update_suggestion_status(suggestion_id, new_status, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@suggestion_bp.route('/suggestions/admin/simulate-implementation', methods=['POST'])
@admin_required
def api_admin_simulate_implementation():
    """API admin pour simuler l'implémentation d'une suggestion"""
    try:
        data = request.get_json()
        suggestion_id = data.get('suggestion_id')
        
        if not suggestion_id:
            return jsonify({'success': False, 'error': 'ID suggestion requis'})
        
        result = simulate_feature_implementation(suggestion_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400