"""
Routes Grades - Interface utilisateur pour la progression et les grades
Permet aux utilisateurs de voir leur progression XP et leurs grades
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

# Import des modules de grades
from modules.grade_manager import (
    get_user_grade_info, get_user_xp_history, add_user_xp, add_user_xp_with_notifications,
    get_user_notifications, mark_notification_as_read, get_unread_notifications_count,
    get_user_rewards, get_available_rewards, get_global_leaderboard, get_user_leaderboard_position
)

# Création du blueprint pour les routes grades
grade_bp = Blueprint('grades', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ
# ============================================================================

def login_required(f):
    """Décorateur pour s'assurer que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour voir votre progression')
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
# PAGE PRINCIPALE DES GRADES
# ============================================================================

@grade_bp.route('/grades')
@login_required
def grades_page():
    """Page principale de progression des grades"""
    try:
        user = get_current_user()
        
        # Récupération des informations de grade
        grade_info = get_user_grade_info(user['id'])
        
        if not grade_info:
            return redirect('/?message=Erreur lors du chargement de votre progression')
        
        # Récupération de l'historique XP récent
        xp_history = get_user_xp_history(user['id'], limit=20)
        
        # Construction de l'interface HTML
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ma Progression - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .grades-header {{
                    background: linear-gradient(135deg, {grade_info['current_grade']['color']}, #667eea);
                    color: white;
                    padding: 30px 0;
                    margin-bottom: 30px;
                }}
                .grade-card {{
                    background: linear-gradient(135deg, {grade_info['current_grade']['color']}, rgba(255,255,255,0.1));
                    color: white;
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                    position: relative;
                    overflow: hidden;
                }}
                .grade-card::before {{
                    content: '{grade_info['current_grade']['icon']}';
                    position: absolute;
                    top: -20px;
                    right: -20px;
                    font-size: 8rem;
                    opacity: 0.1;
                }}
                .progress-container {{
                    background: rgba(255,255,255,0.2);
                    border-radius: 50px;
                    padding: 5px;
                    margin: 20px 0;
                }}
                .progress-bar {{
                    background: linear-gradient(45deg, #ffd700, #ffed4e);
                    height: 20px;
                    border-radius: 50px;
                    transition: width 1s ease-in-out;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #000;
                    font-weight: bold;
                    font-size: 0.8rem;
                }}
                .xp-history-item {{
                    border-left: 4px solid;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    background: rgba(255,255,255,0.05);
                }}
                .xp-positive {{ border-left-color: #28a745; }}
                .xp-neutral {{ border-left-color: #6c757d; }}
                .next-grade-card {{
                    border: 2px dashed #dee2e6;
                    border-radius: 15px;
                    padding: 20px;
                    text-align: center;
                    background: rgba(255,255,255,0.02);
                }}
                .grade-icon {{
                    font-size: 3rem;
                    margin-bottom: 15px;
                }}
                .stats-card {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Grades -->
            <div class="grades-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-trophy me-3"></i>Ma Progression</h1>
                            <p class="mb-0">Suivez votre évolution et débloquez de nouveaux grades</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <h3 class="mb-0">{grade_info['user_info']['username']}</h3>
                            <span class="badge bg-light text-dark">{grade_info['user_info']['xp']} XP</span>
                            <div class="mt-2">
                                <a href="/" class="btn btn-outline-light me-2">
                                    <i class="fas fa-home me-1"></i>Accueil
                                </a>
                                <a href="/profile" class="btn btn-warning">
                                    <i class="fas fa-user me-1"></i>Profil
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="row">
                    <!-- Grade Actuel -->
                    <div class="col-lg-8">
                        <div class="grade-card">
                            <div class="grade-icon">{grade_info['current_grade']['icon']}</div>
                            <h2 class="mb-3">{grade_info['current_grade']['name']}</h2>
                            <p class="mb-3">{grade_info['current_grade']['description']}</p>
                            <h4 class="mb-4">{grade_info['user_info']['xp']} XP Total</h4>
                            
                            <!-- Progression vers le grade suivant -->'''
        
        # Affichage de la progression si un grade suivant existe
        if grade_info['next_grade'] and not grade_info['current_grade']['is_fixed']:
            progress_width = min(100, grade_info['progress_to_next'])
            html_content += f'''
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {progress_width}%;">
                                    {progress_width:.0f}%
                                </div>
                            </div>
                            <p class="mb-0">
                                Prochain grade: <strong>{grade_info['next_grade']['name']}</strong><br>
                                Il vous reste <strong>{grade_info['xp_needed']} XP</strong> à gagner
                            </p>'''
        elif grade_info['current_grade']['is_fixed']:
            html_content += '''
                            <div class="alert alert-warning text-dark">
                                <i class="fas fa-crown me-2"></i>
                                <strong>Grade Spécial :</strong> Votre grade est fixe et ne change pas avec l'XP
                            </div>'''
        else:
            html_content += '''
                            <div class="alert alert-success text-dark">
                                <i class="fas fa-star me-2"></i>
                                <strong>Grade Maximum Atteint !</strong> Vous êtes au sommet de la progression
                            </div>'''
        
        html_content += f'''
                        </div>
                        
                        <!-- Avantages du Grade -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-gift me-2"></i>Avantages de votre Grade</h5>
                            </div>
                            <div class="card-body">
                                <p>{grade_info['current_grade']['advantages']}</p>
                            </div>
                        </div>
                        
                        <!-- Comment Gagner de l'XP -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-lightbulb me-2"></i>Comment Gagner de l'XP</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <ul class="list-unstyled">
                                            <li class="mb-2"><i class="fas fa-calculator text-primary me-2"></i>Utiliser le calculateur (+5 XP)</li>
                                            <li class="mb-2"><i class="fas fa-book text-success me-2"></i>Ajouter un trade (+10 XP)</li>
                                            <li class="mb-2"><i class="fas fa-lightbulb text-warning me-2"></i>Proposer une suggestion (+20 XP)</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <ul class="list-unstyled">
                                            <li class="mb-2"><i class="fas fa-vote-yea text-info me-2"></i>Voter sur une suggestion (+3 XP)</li>
                                            <li class="mb-2"><i class="fas fa-sign-in-alt text-secondary me-2"></i>Connexion quotidienne (+2 XP)</li>
                                            <li class="mb-2"><i class="fas fa-palette text-purple me-2"></i>Personnaliser son profil (+15 XP)</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Sidebar -->
                    <div class="col-lg-4">
                        <!-- Grade Suivant -->'''
        
        if grade_info['next_grade'] and not grade_info['current_grade']['is_fixed']:
            html_content += f'''
                        <div class="next-grade-card mb-4">
                            <h6 class="text-muted mb-3">Prochain Grade</h6>
                            <div class="grade-icon" style="color: {grade_info['next_grade']['color']};">
                                {grade_info['next_grade']['icon']}
                            </div>
                            <h5 style="color: {grade_info['next_grade']['color']};">{grade_info['next_grade']['name']}</h5>
                            <p class="text-muted small">{grade_info['next_grade']['description']}</p>
                            <div class="mt-3">
                                <span class="badge bg-primary">{grade_info['next_grade']['xp_threshold']} XP requis</span>
                            </div>
                        </div>'''
        
        # Statistiques personnelles
        total_actions = len(xp_history)
        recent_xp = sum(action['xp_change'] for action in xp_history[:7] if action['xp_change'] > 0)
        
        html_content += f'''
                        <!-- Statistiques -->
                        <div class="stats-card">
                            <h6 class="mb-3"><i class="fas fa-chart-line me-2"></i>Vos Statistiques</h6>
                            <div class="row g-3">
                                <div class="col-6 text-center">
                                    <h4 class="text-primary">{total_actions}</h4>
                                    <small class="text-muted">Actions Total</small>
                                </div>
                                <div class="col-6 text-center">
                                    <h4 class="text-success">{recent_xp}</h4>
                                    <small class="text-muted">XP cette semaine</small>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Actions Rapides -->
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-bolt me-2"></i>Actions Rapides</h6>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <a href="/calculator" class="btn btn-primary btn-sm">
                                        <i class="fas fa-calculator me-1"></i>Calculateur (+5 XP)
                                    </a>
                                    <a href="/journal" class="btn btn-success btn-sm">
                                        <i class="fas fa-book me-1"></i>Journal (+10 XP)
                                    </a>
                                    <a href="/suggestions" class="btn btn-warning btn-sm">
                                        <i class="fas fa-lightbulb me-1"></i>Suggestions (+20 XP)
                                    </a>
                                    <a href="/personnalisation" class="btn btn-info btn-sm">
                                        <i class="fas fa-palette me-1"></i>Personnalisation (+15 XP)
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Historique XP -->
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-history me-2"></i>Historique de vos Actions</h5>
                            </div>
                            <div class="card-body">'''
        
        # Affichage de l'historique XP
        if xp_history:
            for action in xp_history:
                xp_class = 'xp-positive' if action['xp_change'] > 0 else 'xp-neutral'
                xp_icon = 'fas fa-plus-circle text-success' if action['xp_change'] > 0 else 'fas fa-minus-circle text-danger'
                
                # Formatage de la date
                try:
                    action_date = datetime.strptime(action['created_at'][:19], '%Y-%m-%d %H:%M:%S')
                    formatted_date = action_date.strftime('%d/%m/%Y à %H:%M')
                except:
                    formatted_date = action['created_at'][:16] if action['created_at'] else 'Date inconnue'
                
                html_content += f'''
                                <div class="xp-history-item {xp_class}">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="mb-1">
                                                <i class="{xp_icon} me-2"></i>
                                                {action['description']}
                                            </h6>
                                            <small class="text-muted">
                                                <i class="fas fa-calendar-alt me-1"></i>
                                                {formatted_date}
                                            </small>
                                        </div>
                                        <div class="text-end">
                                            <span class="badge {'bg-success' if action['xp_change'] > 0 else 'bg-secondary'}">
                                                {'+' if action['xp_change'] > 0 else ''}{action['xp_change']} XP
                                            </span>
                                        </div>
                                    </div>
                                </div>'''
        else:
            html_content += '''
                                <div class="text-center py-4">
                                    <i class="fas fa-history fa-3x text-muted mb-3"></i>
                                    <h5 class="text-muted">Aucune action pour le moment</h5>
                                    <p class="text-muted">Commencez à utiliser MindTraderPro pour gagner de l'XP !</p>
                                </div>'''
        
        html_content += '''
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Animation de la barre de progression
                document.addEventListener('DOMContentLoaded', function() {
                    const progressBar = document.querySelector('.progress-bar');
                    if (progressBar) {
                        setTimeout(() => {
                            progressBar.style.width = progressBar.style.width;
                        }, 500);
                    }
                });
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de la progression: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES GRADES
# ============================================================================

@grade_bp.route('/grades/api/user-info')
@login_required
def api_user_grade_info():
    """API pour récupérer les informations de grade de l'utilisateur"""
    try:
        user = get_current_user()
        grade_info = get_user_grade_info(user['id'])
        
        if grade_info:
            return jsonify({'success': True, 'grade_info': grade_info})
        else:
            return jsonify({'success': False, 'error': 'Informations de grade non trouvées'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@grade_bp.route('/grades/api/award-xp', methods=['POST'])
@login_required
def api_award_xp():
    """API pour attribuer de l'XP à l'utilisateur actuel"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        action_type = data.get('action_type')
        custom_xp = data.get('custom_xp')
        description = data.get('description')
        
        if not action_type:
            return jsonify({'success': False, 'error': 'Type d\'action requis'})
        
        result = add_user_xp(user['id'], action_type, custom_xp, description)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@grade_bp.route('/grades/api/history')
@login_required
def api_user_xp_history():
    """API pour récupérer l'historique XP de l'utilisateur"""
    try:
        user = get_current_user()
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        history = get_user_xp_history(user['id'], limit, offset)
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# LEADERBOARD GLOBAL PUBLIC
# ============================================================================

@grade_bp.route('/leaderboard')
def leaderboard_page():
    """Page publique du leaderboard global"""
    try:
        # Paramètres de tri et filtrage
        sort_by = request.args.get('sort', 'xp')  # xp, actions, date
        role_filter = request.args.get('role', 'all')  # all, standard, premium, lifetime
        
        # Récupération du leaderboard
        leaderboard = get_global_leaderboard(limit=20, sort_by=sort_by, role_filter=role_filter)
        
        # Position de l'utilisateur connecté (si connecté)
        user_position = None
        if 'user_id' in session:
            user_position = get_user_leaderboard_position(session['user_id'])
        
        # Construction de l'interface HTML
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Leaderboard - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .leaderboard-header {{
                    background: linear-gradient(135deg, #ffd700, #ff8c00);
                    color: white;
                    padding: 30px 0;
                    margin-bottom: 30px;
                }}
                .podium-card {{
                    border-radius: 15px;
                    padding: 25px;
                    text-align: center;
                    margin-bottom: 20px;
                    position: relative;
                    overflow: hidden;
                }}
                .podium-1 {{
                    background: linear-gradient(135deg, #ffd700, #ffed4e);
                    color: #000;
                    transform: scale(1.05);
                }}
                .podium-2 {{
                    background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
                    color: #000;
                }}
                .podium-3 {{
                    background: linear-gradient(135deg, #cd7f32, #daa520);
                    color: white;
                }}
                .rank-badge {{
                    position: absolute;
                    top: -10px;
                    left: -10px;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 1.2rem;
                }}
                .rank-1 {{ background: #ffd700; color: #000; }}
                .rank-2 {{ background: #c0c0c0; color: #000; }}
                .rank-3 {{ background: #cd7f32; color: white; }}
                .rank-other {{ background: #6c757d; color: white; }}
                .user-row {{
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                    background: rgba(255,255,255,0.05);
                    transition: all 0.3s ease;
                }}
                .user-row:hover {{
                    background: rgba(255,255,255,0.1);
                    transform: translateY(-2px);
                }}
                .grade-badge {{
                    display: inline-flex;
                    align-items: center;
                    padding: 6px 12px;
                    border-radius: 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 0.8rem;
                }}
                .current-user {{
                    border: 2px solid #ffd700;
                    background: rgba(255, 215, 0, 0.1);
                }}
                .filter-section {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 30px;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Leaderboard -->
            <div class="leaderboard-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-trophy me-3"></i>Leaderboard Global</h1>
                            <p class="mb-0">Classement des meilleurs traders de MindTraderPro</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/" class="btn btn-outline-light me-2">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                            {'<a href="/grades" class="btn btn-warning"><i class="fas fa-user me-1"></i>Ma Progression</a>' if 'user_id' in session else '<a href="/login" class="btn btn-success"><i class="fas fa-sign-in-alt me-1"></i>Connexion</a>'}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Position de l'utilisateur connecté -->'''
        
        if user_position and 'user_id' in session:
            html_content += f'''
                <div class="alert alert-info mb-4">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h5><i class="fas fa-user me-2"></i>Votre Position</h5>
                            <p class="mb-0">
                                Vous êtes classé <strong>#{user_position['position']}</strong> sur {user_position['total_users']} traders
                                avec <strong>{user_position['user_xp']} XP</strong>
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-primary fs-6">Top {user_position['percentile']}%</span>
                        </div>
                    </div>
                </div>'''
        
        html_content += f'''
                <!-- Filtres -->
                <div class="filter-section">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <label class="form-label text-white">Trier par :</label>
                            <select class="form-select" id="sortBy" onchange="applyFilters()">
                                <option value="xp" {'selected' if sort_by == 'xp' else ''}>XP Total</option>
                                <option value="actions" {'selected' if sort_by == 'actions' else ''}>Nombre d'Actions</option>
                                <option value="date" {'selected' if sort_by == 'date' else ''}>Plus Récent</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label text-white">Filtrer par rôle :</label>
                            <select class="form-select" id="roleFilter" onchange="applyFilters()">
                                <option value="all" {'selected' if role_filter == 'all' else ''}>Tous</option>
                                <option value="standard" {'selected' if role_filter == 'standard' else ''}>Standard</option>
                                <option value="premium" {'selected' if role_filter == 'premium' else ''}>Premium</option>
                                <option value="lifetime" {'selected' if role_filter == 'lifetime' else ''}>Lifetime</option>
                            </select>
                        </div>
                        <div class="col-md-6 text-end">
                            <button class="btn btn-outline-light" onclick="window.location.reload()">
                                <i class="fas fa-sync-alt me-1"></i>Actualiser
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Podium (Top 3) -->'''
        
        if len(leaderboard) >= 3:
            html_content += '''
                <div class="row mb-5">
                    <div class="col-12">
                        <h3 class="text-center mb-4"><i class="fas fa-medal me-2"></i>Podium</h3>
                    </div>'''
            
            # Affichage du podium (positions 1, 2, 3)
            podium_order = [1, 0, 2]  # 2e, 1er, 3e pour l'effet visuel
            podium_classes = ['podium-2', 'podium-1', 'podium-3']
            rank_classes = ['rank-2', 'rank-1', 'rank-3']
            
            for i, pos in enumerate(podium_order):
                if pos < len(leaderboard):
                    user = leaderboard[pos]
                    html_content += f'''
                    <div class="col-md-4">
                        <div class="podium-card {podium_classes[i]}">
                            <div class="rank-badge {rank_classes[i]}">#{user['rank']}</div>
                            <div class="mb-3">
                                <div class="grade-badge" style="background: {user['grade_color']};">
                                    {user['grade_icon']} {user['grade_name']}
                                </div>
                            </div>
                            <h4 class="mb-2">{user['username']}</h4>
                            <h3 class="mb-2">{user['xp']} XP</h3>
                            <small>{user['action_count']} actions</small>
                            <div class="mt-2">
                                <span class="badge bg-{'warning' if user['role'] == 'premium' else 'primary' if user['role'] == 'lifetime' else 'secondary'} text-{'dark' if user['role'] == 'premium' else 'white'}">
                                    {user['role'].upper()}
                                </span>
                            </div>
                        </div>
                    </div>'''
            
            html_content += '</div>'
        
        html_content += '''
                <!-- Classement Complet -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list-ol me-2"></i>Classement Complet</h5>
                    </div>
                    <div class="card-body">'''
        
        # Affichage de tous les utilisateurs
        current_user_id = session.get('user_id')
        for user in leaderboard:
            is_current_user = current_user_id == user['id']
            current_user_class = 'current-user' if is_current_user else ''
            
            # Icône de classement
            if user['rank'] == 1:
                rank_icon = '🥇'
            elif user['rank'] == 2:
                rank_icon = '🥈'
            elif user['rank'] == 3:
                rank_icon = '🥉'
            else:
                rank_icon = f"#{user['rank']}"
            
            html_content += f'''
                        <div class="user-row {current_user_class}">
                            <div class="row align-items-center">
                                <div class="col-md-1 text-center">
                                    <h4 class="mb-0">{rank_icon}</h4>
                                </div>
                                <div class="col-md-4">
                                    <div class="d-flex align-items-center">
                                        <div class="grade-badge me-3" style="background: {user['grade_color']};">
                                            {user['grade_icon']}
                                        </div>
                                        <div>
                                            <h6 class="mb-0">{user['username']} {'👑' if is_current_user else ''}</h6>
                                            <small class="text-muted">{user['grade_name']}</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h5 class="mb-0 text-warning">{user['xp']}</h5>
                                    <small class="text-muted">XP Total</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h6 class="mb-0">{user['action_count']}</h6>
                                    <small class="text-muted">Actions</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <span class="badge bg-{'warning' if user['role'] == 'premium' else 'primary' if user['role'] == 'lifetime' else 'secondary'} text-{'dark' if user['role'] == 'premium' else 'white'}">
                                        {user['role'].upper()}
                                    </span>
                                </div>
                                <div class="col-md-1 text-center">
                                    <small class="text-muted">{user['created_at'][:10] if user['created_at'] else 'N/A'}</small>
                                </div>
                            </div>
                        </div>'''
        
        if not leaderboard:
            html_content += '''
                        <div class="text-center py-5">
                            <i class="fas fa-trophy fa-4x text-muted mb-3"></i>
                            <h4 class="text-muted">Aucun trader dans le classement</h4>
                            <p class="text-muted">Soyez le premier à gagner de l'XP !</p>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Application des filtres
                function applyFilters() {
                    const sortBy = document.getElementById('sortBy').value;
                    const roleFilter = document.getElementById('roleFilter').value;
                    
                    const params = new URLSearchParams();
                    if (sortBy) params.append('sort', sortBy);
                    if (roleFilter && roleFilter !== 'all') params.append('role', roleFilter);
                    
                    window.location.href = '/leaderboard?' + params.toString();
                }
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement du leaderboard: {str(e)}</p>"

# ============================================================================
# SYSTÈME DE NOTIFICATIONS
# ============================================================================

@grade_bp.route('/grades/api/notifications')
@login_required
def api_get_notifications():
    """API pour récupérer les notifications de l'utilisateur"""
    try:
        user = get_current_user()
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 10, type=int)
        
        notifications = get_user_notifications(user['id'], unread_only, limit)
        unread_count = get_unread_notifications_count(user['id'])
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@grade_bp.route('/grades/api/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notification_read():
    """API pour marquer une notification comme lue"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return jsonify({'success': False, 'error': 'ID notification requis'})
        
        result = mark_notification_as_read(notification_id, user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# SYSTÈME DE RÉCOMPENSES
# ============================================================================

@grade_bp.route('/grades/api/rewards')
@login_required
def api_get_user_rewards():
    """API pour récupérer les récompenses de l'utilisateur"""
    try:
        user = get_current_user()
        
        # Récupération des récompenses débloquées
        user_rewards = get_user_rewards(user['id'])
        
        # Récupération de l'XP actuel pour les récompenses disponibles
        grade_info = get_user_grade_info(user['id'])
        current_xp = grade_info['user_info']['xp'] if grade_info else 0
        
        available_rewards = get_available_rewards(current_xp)
        
        return jsonify({
            'success': True,
            'user_rewards': user_rewards,
            'available_rewards': available_rewards['available'],
            'upcoming_rewards': available_rewards['upcoming']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400