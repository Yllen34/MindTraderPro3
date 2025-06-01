"""
Routes Lifetime - Interface exclusive pour les utilisateurs Lifetime
Permet aux utilisateurs Lifetime de contribuer à l'évolution de MindTraderPro
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

# Import des modules Lifetime
from modules.lifetime_contribution_manager import (
    create_lifetime_contribution, get_all_lifetime_contributions, get_lifetime_contribution_by_id,
    update_lifetime_contribution, delete_lifetime_contribution, toggle_lifetime_contribution_vote,
    get_user_lifetime_profile, get_lifetime_contributions_statistics
)

# Création du blueprint pour les routes Lifetime
lifetime_bp = Blueprint('lifetime', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ LIFETIME
# ============================================================================

def lifetime_required(f):
    """Décorateur pour s'assurer que l'utilisateur est Lifetime ou Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour accéder aux fonctionnalités Lifetime')
        
        user_role = session.get('role', 'standard')
        if user_role not in ['lifetime', 'admin']:
            return redirect('/?message=Accès réservé aux utilisateurs Lifetime')
        
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
# PROFIL LIFETIME EXCLUSIF
# ============================================================================

@lifetime_bp.route('/profile')
@lifetime_required
def lifetime_profile():
    """Page de profil exclusif pour les utilisateurs Lifetime"""
    try:
        user = get_current_user()
        
        # Récupération du profil Lifetime complet
        lifetime_profile = get_user_lifetime_profile(user['id'])
        
        if not lifetime_profile:
            return redirect('/?message=Erreur lors du chargement du profil Lifetime')
        
        # Construction de l'interface HTML du profil
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Profil Lifetime VIP - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .lifetime-header {{
                    background: linear-gradient(135deg, #667eea, #764ba2, #ffd700);
                    color: white;
                    padding: 30px 0;
                    margin-bottom: 30px;
                    position: relative;
                    overflow: hidden;
                }}
                .lifetime-header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
                    animation: sparkle 3s linear infinite;
                }}
                @keyframes sparkle {{
                    0% {{ transform: translateY(0); }}
                    100% {{ transform: translateY(-100px); }}
                }}
                .lifetime-badge {{
                    background: linear-gradient(45deg, #ffd700, #ffed4e);
                    color: #000;
                    padding: 8px 16px;
                    border-radius: 25px;
                    font-weight: bold;
                    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
                    animation: glow 2s ease-in-out infinite alternate;
                }}
                @keyframes glow {{
                    from {{ box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4); }}
                    to {{ box-shadow: 0 6px 25px rgba(255, 215, 0, 0.8); }}
                }}
                .stats-card {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border-radius: 15px;
                    transition: transform 0.3s ease;
                }}
                .stats-card:hover {{
                    transform: translateY(-10px);
                }}
                .contribution-level {{
                    background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: bold;
                    font-size: 1.2rem;
                }}
                .recent-contribution {{
                    border-left: 4px solid #ffd700;
                    background: rgba(255, 215, 0, 0.1);
                    margin-bottom: 10px;
                    padding: 15px;
                    border-radius: 8px;
                }}
                .status-proposed {{ border-left-color: #007bff; }}
                .status-accepted {{ border-left-color: #28a745; }}
                .status-in_development {{ border-left-color: #ffc107; }}
                .status-completed {{ border-left-color: #17a2b8; }}
                .status-refused {{ border-left-color: #dc3545; }}
            </style>
        </head>
        <body>
            <!-- En-tête Lifetime VIP -->
            <div class="lifetime-header">
                <div class="container position-relative">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-crown me-3"></i>Profil Lifetime VIP</h1>
                            <p class="mb-3">Accès exclusif et contributions privilégiées</p>
                            <span class="lifetime-badge">
                                👑 LIFETIME VIP - Accès Illimité
                            </span>
                        </div>
                        <div class="col-md-4 text-end">
                            <h3 class="mb-0">{lifetime_profile['user_info']['username']}</h3>
                            <small>Membre depuis {lifetime_profile['user_info']['member_since'][:10] if lifetime_profile['user_info']['member_since'] else 'N/A'}</small>
                            <div class="mt-2">
                                <a href="/" class="btn btn-outline-light me-2">
                                    <i class="fas fa-home me-1"></i>Accueil
                                </a>
                                <a href="/contribution" class="btn btn-warning">
                                    <i class="fas fa-lightbulb me-1"></i>Contribuer
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Niveau de Contribution -->
                <div class="row mb-4">
                    <div class="col-12 text-center">
                        <h2 class="contribution-level">
                            🏆 {lifetime_profile['contribution_stats']['contribution_level']}
                        </h2>
                        <p class="text-muted">Votre statut de contributeur dans la communauté MindTraderPro</p>
                    </div>
                </div>
                
                <!-- Statistiques de Contribution -->
                <div class="row g-4 mb-5">
                    <div class="col-md-3">
                        <div class="card stats-card h-100 text-center p-4">
                            <i class="fas fa-lightbulb fa-3x mb-3"></i>
                            <h3>{lifetime_profile['contribution_stats']['total_contributions']}</h3>
                            <p class="mb-0">Contributions Totales</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card h-100 text-center p-4">
                            <i class="fas fa-check-circle fa-3x mb-3"></i>
                            <h3>{lifetime_profile['contribution_stats']['accepted_contributions']}</h3>
                            <p class="mb-0">Contributions Acceptées</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card h-100 text-center p-4">
                            <i class="fas fa-rocket fa-3x mb-3"></i>
                            <h3>{lifetime_profile['contribution_stats']['implemented_contributions']}</h3>
                            <p class="mb-0">Fonctionnalités Implémentées</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card h-100 text-center p-4">
                            <i class="fas fa-heart fa-3x mb-3"></i>
                            <h3>{lifetime_profile['contribution_stats']['total_votes_received']}</h3>
                            <p class="mb-0">Votes Reçus</p>
                        </div>
                    </div>
                </div>
                
                <!-- Privilèges Lifetime -->
                <div class="row mb-5">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-star me-2"></i>Vos Privilèges Lifetime</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <ul class="list-unstyled">
                                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Accès à tous les modules Premium</li>
                                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Calculateur de lot illimité</li>
                                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Journal de trading avancé</li>
                                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Personnalisation exclusive</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <ul class="list-unstyled">
                                            <li class="mb-2"><i class="fas fa-crown text-warning me-2"></i>Statut "Contributeur Officiel"</li>
                                            <li class="mb-2"><i class="fas fa-crown text-warning me-2"></i>Influence sur les nouvelles fonctionnalités</li>
                                            <li class="mb-2"><i class="fas fa-crown text-warning me-2"></i>Accès anticipé aux nouveautés</li>
                                            <li class="mb-2"><i class="fas fa-crown text-warning me-2"></i>Support prioritaire</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Contributions Récentes -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5><i class="fas fa-history me-2"></i>Vos Contributions Récentes</h5>
                                <a href="/contribution" class="btn btn-primary">
                                    <i class="fas fa-plus me-1"></i>Nouvelle Contribution
                                </a>
                            </div>
                            <div class="card-body">'''
        
        # Affichage des contributions récentes
        if lifetime_profile['recent_contributions']:
            for contribution in lifetime_profile['recent_contributions']:
                status_class = f"status-{contribution[2]}"
                status_badges = {
                    'proposed': ('Proposée', 'bg-primary'),
                    'accepted': ('Acceptée', 'bg-success'),
                    'in_development': ('En Développement', 'bg-warning'),
                    'completed': ('Terminée', 'bg-info'),
                    'refused': ('Refusée', 'bg-danger')
                }
                status_info = status_badges.get(contribution[2], ('Inconnue', 'bg-secondary'))
                
                html_content += f'''
                                <div class="recent-contribution {status_class}">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h6 class="mb-1">{contribution[1]}</h6>
                                            <small class="text-muted">
                                                <i class="fas fa-calendar-alt me-1"></i>
                                                {contribution[3][:10] if contribution[3] else 'N/A'}
                                            </small>
                                        </div>
                                        <span class="badge {status_info[1]}">{status_info[0]}</span>
                                    </div>
                                </div>'''
        else:
            html_content += '''
                                <div class="text-center py-4">
                                    <i class="fas fa-lightbulb fa-3x text-muted mb-3"></i>
                                    <h5 class="text-muted">Aucune contribution pour le moment</h5>
                                    <p class="text-muted">Commencez à contribuer à l'évolution de MindTraderPro !</p>
                                    <a href="/contribution" class="btn btn-primary btn-lg">
                                        <i class="fas fa-plus me-2"></i>Faire une Contribution
                                    </a>
                                </div>'''
        
        html_content += '''
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement du profil Lifetime: {str(e)}</p>"

# ============================================================================
# INTERFACE DE CONTRIBUTION LIFETIME
# ============================================================================

@lifetime_bp.route('/contribution')
@lifetime_required
def contribution_page():
    """Page principale des contributions Lifetime"""
    try:
        user = get_current_user()
        
        # Récupération des paramètres de tri et filtrage
        sort_by = request.args.get('sort', 'recent')  # recent, popular, my_contributions
        filter_status = request.args.get('filter', 'all')  # all, proposed, accepted, in_development, completed, refused
        
        # Récupération des contributions selon les filtres
        contributions = get_all_lifetime_contributions(
            limit=50, 
            offset=0, 
            sort_by=sort_by, 
            user_id=user['id'], 
            filter_status=filter_status
        )
        
        # Construction de l'interface HTML complète
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contributions Lifetime - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .contribution-header {{
                    background: linear-gradient(135deg, #667eea, #764ba2, #ffd700);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .contribution-card {{
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    border-left: 4px solid #ffd700;
                }}
                .contribution-card:hover {{
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
                    background: linear-gradient(45deg, #ffd700, #ffed4e);
                    border-color: #ffd700;
                    color: #000;
                }}
                .status-badge {{
                    font-size: 0.75rem;
                    padding: 4px 8px;
                }}
                .lifetime-exclusive {{
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
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
            <!-- En-tête Contributions -->
            <div class="contribution-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-crown me-3"></i>Contributions Lifetime</h1>
                            <p class="mb-0">Participez à l'évolution de MindTraderPro</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-warning text-dark fs-6 me-2">
                                👑 {user['username']}
                            </span>
                            <a href="/profile" class="btn btn-outline-light">
                                <i class="fas fa-user me-1"></i>Profil VIP
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Message exclusif Lifetime -->
                <div class="lifetime-exclusive">
                    <div class="row align-items-center">
                        <div class="col-md-9">
                            <h5><i class="fas fa-star me-2"></i>Espace Exclusif Lifetime</h5>
                            <p class="mb-0">En tant qu'utilisateur Lifetime, vos contributions ont un impact direct sur l'évolution de MindTraderPro. Proposez vos idées et votez pour celles des autres membres VIP.</p>
                        </div>
                        <div class="col-md-3 text-end">
                            <button class="btn btn-warning btn-lg" data-bs-toggle="modal" data-bs-target="#addContributionModal">
                                <i class="fas fa-plus me-2"></i>Contribuer
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Section filtres et tri -->
                <div class="card mb-4">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-3">
                                <label class="form-label">Trier par :</label>
                                <select class="form-select" id="sortBy" onchange="applySortFilter()">
                                    <option value="recent" {'selected' if sort_by == 'recent' else ''}>Plus récent</option>
                                    <option value="popular" {'selected' if sort_by == 'popular' else ''}>Plus populaire</option>
                                    <option value="my_contributions" {'selected' if sort_by == 'my_contributions' else ''}>Mes contributions</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Filtrer par statut :</label>
                                <select class="form-select" id="filterBy" onchange="applySortFilter()">
                                    <option value="all" {'selected' if filter_status == 'all' else ''}>Toutes</option>
                                    <option value="proposed" {'selected' if filter_status == 'proposed' else ''}>Proposées</option>
                                    <option value="accepted" {'selected' if filter_status == 'accepted' else ''}>Acceptées</option>
                                    <option value="in_development" {'selected' if filter_status == 'in_development' else ''}>En Développement</option>
                                    <option value="completed" {'selected' if filter_status == 'completed' else ''}>Terminées</option>
                                </select>
                            </div>
                            <div class="col-md-6 text-end">
                                <button class="btn btn-info" onclick="window.location.href='/profile'">
                                    <i class="fas fa-chart-line me-1"></i>Mes Statistiques
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des contributions -->
                <div class="row" id="contributionsContainer">'''
        
        # Génération des cartes de contributions
        for contribution in contributions:
            # Détermination du badge de statut
            status_badges = {
                'proposed': 'badge bg-primary status-badge',
                'accepted': 'badge bg-success status-badge',
                'in_development': 'badge bg-warning status-badge',
                'completed': 'badge bg-info status-badge',
                'refused': 'badge bg-danger status-badge'
            }
            status_badge = status_badges.get(contribution['status'], 'badge bg-secondary status-badge')
            
            # Classes CSS pour le bouton de vote
            vote_class = 'vote-button voted' if contribution['user_has_voted'] else 'vote-button'
            vote_icon = 'fas fa-crown' if contribution['user_has_voted'] else 'far fa-crown'
            
            # Boutons d'action pour l'auteur
            author_actions = ''
            if contribution['user_id'] == user['id'] and contribution['status'] in ['proposed', 'accepted']:
                author_actions = f'''
                    <button class="btn btn-outline-primary btn-sm me-1" onclick="editContribution({contribution['id']})">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    {'<button class="btn btn-outline-danger btn-sm" onclick="deleteContribution(' + str(contribution['id']) + ')"><i class="fas fa-trash"></i> Supprimer</button>' if contribution['status'] == 'proposed' else ''}
                '''
            
            # Indicateur de fichier joint
            file_indicator = ''
            if contribution['attached_file']:
                file_indicator = '<i class="fas fa-paperclip text-warning me-2" title="Fichier joint"></i>'
            
            html_content += f'''
                    <div class="col-lg-6 mb-4">
                        <div class="card contribution-card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">
                                        {file_indicator}{contribution['title']}
                                    </h6>
                                    <small class="text-muted">
                                        par <strong>👑 {contribution['username']}</strong>
                                    </small>
                                </div>
                                <span class="{status_badge}">{contribution['status'].upper().replace('_', ' ')}</span>
                            </div>
                            <div class="card-body">
                                <div class="mb-3" style="max-height: 120px; overflow-y: auto;">
                                    <p class="card-text">{contribution['description'][:300]}{'...' if len(contribution['description']) > 300 else ''}</p>
                                </div>
                                
                                <div class="d-flex justify-content-between align-items-center">
                                    <div class="d-flex align-items-center">
                                        <button class="btn btn-outline-warning {vote_class}" 
                                                onclick="toggleVote({contribution['id']}, this)"
                                                data-contribution-id="{contribution['id']}">
                                            <i class="{vote_icon} me-1"></i>
                                            <span class="vote-count">{contribution['vote_count']}</span>
                                        </button>
                                        <small class="text-muted ms-3">
                                            <i class="fas fa-calendar-alt me-1"></i>
                                            {contribution['created_at'][:10] if contribution['created_at'] else 'N/A'}
                                        </small>
                                    </div>
                                    <div>
                                        {author_actions}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>'''
        
        if not contributions:
            html_content += '''
                    <div class="col-12">
                        <div class="text-center py-5">
                            <i class="fas fa-crown fa-4x text-warning mb-3"></i>
                            <h4 class="text-muted">Aucune contribution trouvée</h4>
                            <p class="text-muted">Soyez le premier à proposer une idée révolutionnaire !</p>
                            <button class="btn btn-warning btn-lg" data-bs-toggle="modal" data-bs-target="#addContributionModal">
                                <i class="fas fa-plus me-2"></i>Première Contribution
                            </button>
                        </div>
                    </div>'''
        
        html_content += '''
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Modal d'ajout de contribution -->
            <div class="modal fade" id="addContributionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-crown me-2"></i>Nouvelle Contribution Lifetime
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addContributionForm" enctype="multipart/form-data">
                                <div class="mb-3">
                                    <label class="form-label">Titre de la contribution <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" id="contributionTitle" 
                                           placeholder="Ex: Système d'alertes avancées avec IA" maxlength="300" required>
                                    <div class="form-text">Maximum 300 caractères</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description détaillée <span class="text-danger">*</span></label>
                                    <textarea class="form-control" id="contributionDescription" rows="8" 
                                              placeholder="Décrivez votre idée en détail : fonctionnalités, avantages, implémentation technique, etc." 
                                              maxlength="5000" required></textarea>
                                    <div class="form-text">Maximum 5000 caractères</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Fichier joint (optionnel)</label>
                                    <input type="file" class="form-control" id="contributionFile" 
                                           accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg">
                                    <div class="form-text">Formats acceptés : PDF, DOC, TXT, images (max 10MB)</div>
                                </div>
                                
                                <div class="alert alert-warning">
                                    <h6><i class="fas fa-crown me-2"></i>Privilège Lifetime</h6>
                                    <ul class="mb-0">
                                        <li>Vos contributions ont la priorité dans l'évaluation</li>
                                        <li>Accès direct à l'équipe de développement</li>
                                        <li>Suivi personnalisé de l'implémentation</li>
                                        <li>Crédit en tant que "Contributeur Officiel"</li>
                                    </ul>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Annuler
                            </button>
                            <button type="button" class="btn btn-warning" onclick="submitContribution()">
                                <i class="fas fa-crown me-1"></i>Soumettre la Contribution
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // ============================================================================
                // JAVASCRIPT POUR LES CONTRIBUTIONS LIFETIME
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
                    
                    window.location.href = '/contribution?' + params.toString();
                }}
                
                // Soumission d'une nouvelle contribution
                function submitContribution() {{
                    const title = document.getElementById('contributionTitle').value.trim();
                    const description = document.getElementById('contributionDescription').value.trim();
                    const fileInput = document.getElementById('contributionFile');
                    
                    if (!title || !description) {{
                        showNotification('❌ Titre et description sont requis', 'error');
                        return;
                    }}
                    
                    const formData = new FormData();
                    formData.append('title', title);
                    formData.append('description', description);
                    
                    if (fileInput.files[0]) {{
                        formData.append('file', fileInput.files[0]);
                    }}
                    
                    fetch('/contribution/create', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(result => {{
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            bootstrap.Modal.getInstance(document.getElementById('addContributionModal')).hide();
                            document.getElementById('addContributionForm').reset();
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }})
                    .catch(error => {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }});
                }}
                
                // Toggle vote sur une contribution
                async function toggleVote(contributionId, buttonElement) {{
                    try {{
                        const response = await fetch('/contribution/vote', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ contribution_id: contributionId }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            // Mise à jour de l'interface
                            const voteCount = buttonElement.querySelector('.vote-count');
                            const icon = buttonElement.querySelector('i');
                            
                            voteCount.textContent = result.new_vote_count;
                            
                            if (result.user_has_voted) {{
                                buttonElement.classList.add('voted');
                                icon.className = 'fas fa-crown me-1';
                            }} else {{
                                buttonElement.classList.remove('voted');
                                icon.className = 'far fa-crown me-1';
                            }}
                            
                            showNotification('✅ ' + result.message, 'success');
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur lors du vote', 'error');
                    }}
                }}
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement des contributions: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES CONTRIBUTIONS LIFETIME
# ============================================================================

@lifetime_bp.route('/contribution/create', methods=['POST'])
@lifetime_required
def api_create_contribution():
    """API pour créer une nouvelle contribution Lifetime"""
    try:
        user = get_current_user()
        
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Gestion du fichier joint
        attached_file = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                # Ici on pourrait sauvegarder le fichier
                # Pour la démo, on stocke juste le nom
                attached_file = file.filename
        
        if not title or not description:
            return jsonify({'success': False, 'error': 'Titre et description requis'})
        
        result = create_lifetime_contribution(user['id'], title, description, attached_file)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@lifetime_bp.route('/contribution/vote', methods=['POST'])
@lifetime_required
def api_vote_contribution():
    """API pour voter ou retirer son vote sur une contribution"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        contribution_id = data.get('contribution_id')
        
        if not contribution_id:
            return jsonify({'success': False, 'error': 'ID contribution requis'})
        
        result = toggle_lifetime_contribution_vote(contribution_id, user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400