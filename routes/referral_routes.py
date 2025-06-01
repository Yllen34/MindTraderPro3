"""
Routes de Parrainage - Interface utilisateur et administration
Système complet de parrainage avec récompenses et gestion des filleuls
"""

import os
from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

# Import des modules de parrainage
from modules.referral_manager import (
    get_referral_link, get_user_referral_stats, get_referral_leaderboard,
    process_referral_signup, check_auto_validation, validate_referral,
    get_all_referrals_admin, update_referral_status_admin, get_referral_fraud_logs
)

# Création du blueprint pour les routes de parrainage
referral_bp = Blueprint('referrals', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ
# ============================================================================

def login_required(f):
    """Décorateur pour s'assurer que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour s'assurer que seuls les admins peuvent accéder"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect('/login?message=Accès administrateur requis')
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Récupère les informations de l'utilisateur actuel"""
    if 'user_id' not in session:
        return None
    
    return {
        'id': session['user_id'],
        'username': session.get('username', 'Utilisateur'),
        'email': session.get('email', ''),
        'role': session.get('role', 'standard')
    }

# ============================================================================
# PAGE PRINCIPALE DE PARRAINAGE
# ============================================================================

@referral_bp.route('/parrainage')
@login_required
def parrainage_page():
    """Page principale de parrainage pour les utilisateurs"""
    try:
        user = get_current_user()
        
        # Récupération des statistiques de parrainage
        stats_result = get_user_referral_stats(user['id'])
        if not stats_result['success']:
            return f"Erreur: {stats_result['error']}"
        
        stats = stats_result
        
        # Génération du lien de parrainage
        link_result = get_referral_link(user['id'])
        if not link_result['success']:
            return f"Erreur: {link_result['error']}"
        
        referral_link = link_result['link']
        referral_code = link_result['code']
        
        # Construction de l'interface HTML
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Parrainage - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .referral-header {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 30px 0;
                    margin-bottom: 30px;
                }}
                .stats-card {{
                    border-radius: 15px;
                    padding: 25px;
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                    margin-bottom: 20px;
                    transition: transform 0.3s ease;
                }}
                .stats-card:hover {{
                    transform: translateY(-5px);
                }}
                .stat-number {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #28a745;
                }}
                .referral-link-box {{
                    background: rgba(40, 167, 69, 0.1);
                    border: 2px solid #28a745;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .badge-earned {{
                    background: linear-gradient(135deg, #ffd700, #ff8c00);
                    color: #000;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    margin: 5px;
                    display: inline-block;
                }}
                .next-badge {{
                    background: rgba(255,255,255,0.1);
                    border: 2px dashed #6c757d;
                    color: #6c757d;
                    padding: 8px 16px;
                    border-radius: 20px;
                    margin: 5px;
                    display: inline-block;
                }}
                .referral-item {{
                    background: rgba(255,255,255,0.05);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-left: 4px solid #28a745;
                }}
                .status-pending {{
                    color: #ffc107;
                }}
                .status-registered {{
                    color: #17a2b8;
                }}
                .status-validated {{
                    color: #28a745;
                }}
                .status-blocked {{
                    color: #dc3545;
                }}
                .copy-btn {{
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .copy-btn:hover {{
                    background: #28a745 !important;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Parrainage -->
            <div class="referral-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-users me-3"></i>Programme de Parrainage</h1>
                            <p class="mb-0">Invitez vos amis et gagnez des récompenses exclusives</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/" class="btn btn-outline-light me-2">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                            <a href="/leaderboard-parrainage" class="btn btn-warning">
                                <i class="fas fa-trophy me-1"></i>Classement
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Statistiques Personnelles -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <div class="stat-number">{stats['stats']['total_referrals']}</div>
                            <div class="text-muted">Total Filleuls</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <div class="stat-number">{stats['stats']['validated']}</div>
                            <div class="text-muted">Validés</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <div class="stat-number">{stats['total_xp']}</div>
                            <div class="text-muted">XP Gagnés</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <div class="stat-number">{len(stats['badges'])}</div>
                            <div class="text-muted">Badges</div>
                        </div>
                    </div>
                </div>
                
                <!-- Lien de Parrainage -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-link me-2"></i>Votre Lien de Parrainage</h5>
                    </div>
                    <div class="card-body">
                        <div class="referral-link-box">
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <div class="mb-2">
                                        <strong>Code:</strong> <span class="badge bg-success fs-6">{referral_code}</span>
                                    </div>
                                    <div class="input-group">
                                        <input type="text" class="form-control" id="referralLink" value="{referral_link}" readonly>
                                        <button class="btn btn-success copy-btn" onclick="copyReferralLink()">
                                            <i class="fas fa-copy me-1"></i>Copier
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-4 text-center">
                                    <h6>Partagez et gagnez:</h6>
                                    <div class="mb-2">📝 <strong>+5 XP</strong> par inscription</div>
                                    <div>✅ <strong>+25 XP</strong> par validation</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Badges et Récompenses -->
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-medal me-2"></i>Badges Débloqués</h5>
                            </div>
                            <div class="card-body">'''
        
        # Affichage des badges débloqués
        if stats['badges']:
            for badge in stats['badges']:
                html_content += f'<span class="badge-earned">{badge}</span>'
        else:
            html_content += '<p class="text-muted">Aucun badge débloqué pour le moment</p>'
        
        # Prochain badge
        if stats['next_badge']:
            next_badge = stats['next_badge']
            html_content += f'''
                                <div class="mt-3">
                                    <h6>Prochain objectif:</h6>
                                    <span class="next-badge">{next_badge['name']} ({next_badge['remaining']} filleuls restants)</span>
                                </div>'''
        
        html_content += '''
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-gift me-2"></i>Offres pour vos Filleuls</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <i class="fas fa-star text-warning me-2"></i>
                                    <strong>Premium 1 mois:</strong> 4,99€ au lieu de 14,99€
                                </div>
                                <div class="mb-3">
                                    <i class="fas fa-crown text-warning me-2"></i>
                                    <strong>Lifetime:</strong> 149€ au lieu de 299€ (30 jours)
                                </div>
                                <small class="text-muted">Vos filleuls bénéficient automatiquement de ces offres</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des Filleuls -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list me-2"></i>Mes Filleuls ({stats['stats']['total_referrals']})</h5>
                    </div>
                    <div class="card-body">'''
        
        # Affichage des filleuls récents
        if stats['recent_referrals']:
            for referral in stats['recent_referrals']:
                status_class = f"status-{referral['status']}"
                status_icon = {
                    'pending': '⏳',
                    'registered': '📝',
                    'validated': '✅',
                    'blocked': '❌'
                }.get(referral['status'], '❓')
                
                signup_date = referral['signup_date'][:10] if referral['signup_date'] else 'N/A'
                
                html_content += f'''
                        <div class="referral-item">
                            <div class="row align-items-center">
                                <div class="col-md-4">
                                    <h6 class="mb-0">{referral['username']}</h6>
                                    <small class="text-muted">Inscrit le {signup_date}</small>
                                </div>
                                <div class="col-md-3">
                                    <span class="{status_class}">
                                        {status_icon} {referral['status'].title()}
                                    </span>
                                </div>
                                <div class="col-md-3">
                                    {'✅ Validé le ' + referral['validation_date'][:10] if referral['validation_date'] else '⏳ En attente'}
                                </div>
                                <div class="col-md-2 text-end">
                                    {'+25 XP' if referral['status'] == 'validated' else '+5 XP' if referral['status'] == 'registered' else '0 XP'}
                                </div>
                            </div>
                        </div>'''
        else:
            html_content += '''
                        <div class="text-center py-5">
                            <i class="fas fa-user-plus fa-4x text-muted mb-3"></i>
                            <h4 class="text-muted">Aucun filleul pour le moment</h4>
                            <p class="text-muted">Partagez votre lien pour commencer à gagner des récompenses !</p>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                function copyReferralLink() {
                    const linkInput = document.getElementById('referralLink');
                    linkInput.select();
                    linkInput.setSelectionRange(0, 99999);
                    document.execCommand('copy');
                    
                    // Feedback visuel
                    const btn = document.querySelector('.copy-btn');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-check me-1"></i>Copié !';
                    btn.classList.add('btn-outline-success');
                    btn.classList.remove('btn-success');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.classList.remove('btn-outline-success');
                        btn.classList.add('btn-success');
                    }, 2000);
                }
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de la page de parrainage: {str(e)}</p>"

# ============================================================================
# LEADERBOARD DES PARRAINS
# ============================================================================

@referral_bp.route('/leaderboard-parrainage')
def referral_leaderboard_page():
    """Page publique du leaderboard des parrains"""
    try:
        # Récupération du leaderboard
        leaderboard_result = get_referral_leaderboard(20)
        if not leaderboard_result['success']:
            return f"Erreur: {leaderboard_result['error']}"
        
        leaderboard = leaderboard_result['leaderboard']
        
        # Construction de l'interface HTML
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Leaderboard Parrainage - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .leaderboard-header {{
                    background: linear-gradient(135deg, #28a745, #20c997);
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
                .badge-display {{
                    display: inline-flex;
                    align-items: center;
                    padding: 4px 8px;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Leaderboard -->
            <div class="leaderboard-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-trophy me-3"></i>Leaderboard Parrainage</h1>
                            <p class="mb-0">Classement des meilleurs parrains de MindTraderPro</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/" class="btn btn-outline-light me-2">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                            <a href="/parrainage" class="btn btn-warning">
                                <i class="fas fa-users me-1"></i>Mon Parrainage
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">'''
        
        # Podium (Top 3)
        if len(leaderboard) >= 3:
            html_content += '''
                <!-- Podium (Top 3) -->
                <div class="row mb-5">
                    <div class="col-12">
                        <h3 class="text-center mb-4"><i class="fas fa-medal me-2"></i>Podium des Parrains</h3>
                    </div>'''
            
            # Affichage du podium (positions 1, 2, 3)
            podium_order = [1, 0, 2]  # 2e, 1er, 3e pour l'effet visuel
            podium_classes = ['podium-2', 'podium-1', 'podium-3']
            rank_classes = ['rank-2', 'rank-1', 'rank-3']
            
            for i, pos in enumerate(podium_order):
                if pos < len(leaderboard):
                    user = leaderboard[pos]
                    badge_display = ""
                    if user['current_badge']:
                        badge = user['current_badge']
                        badge_display = f'<div class="badge-display" style="background: {badge["color"]}; color: white;">{badge["icon"]} {badge["name"]}</div>'
                    
                    html_content += f'''
                    <div class="col-md-4">
                        <div class="podium-card {podium_classes[i]}">
                            <div class="rank-badge {rank_classes[i]}">#{user['rank']}</div>
                            {badge_display}
                            <h4 class="mb-2 mt-3">{user['username']}</h4>
                            <h3 class="mb-2">{user['validated_referrals']} validés</h3>
                            <div class="mb-2">{user['total_xp_earned']} XP gagnés</div>
                            <small>{user['total_referrals']} filleuls total</small>
                        </div>
                    </div>'''
            
            html_content += '</div>'
        
        html_content += '''
                <!-- Classement Complet -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list-ol me-2"></i>Classement Complet des Parrains</h5>
                    </div>
                    <div class="card-body">'''
        
        # Affichage de tous les parrains
        current_user_id = session.get('user_id')
        for user in leaderboard:
            is_current_user = current_user_id == user['user_id']
            current_user_class = 'border border-warning' if is_current_user else ''
            
            # Icône de classement
            if user['rank'] == 1:
                rank_icon = '🥇'
            elif user['rank'] == 2:
                rank_icon = '🥈'
            elif user['rank'] == 3:
                rank_icon = '🥉'
            else:
                rank_icon = f"#{user['rank']}"
            
            # Badge de parrainage
            badge_display = ""
            if user['current_badge']:
                badge = user['current_badge']
                badge_display = f'<span class="badge-display" style="background: {badge["color"]}; color: white;">{badge["icon"]} {badge["name"]}</span>'
            
            html_content += f'''
                        <div class="user-row {current_user_class}">
                            <div class="row align-items-center">
                                <div class="col-md-1 text-center">
                                    <h4 class="mb-0">{rank_icon}</h4>
                                </div>
                                <div class="col-md-3">
                                    <div class="d-flex align-items-center">
                                        <div>
                                            <h6 class="mb-0">{user['username']} {'👑' if is_current_user else ''}</h6>
                                            {badge_display}
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h5 class="mb-0 text-success">{user['validated_referrals']}</h5>
                                    <small class="text-muted">Validés</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h6 class="mb-0">{user['total_referrals']}</h6>
                                    <small class="text-muted">Total</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h6 class="mb-0 text-warning">{user['total_xp_earned']}</h6>
                                    <small class="text-muted">XP</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <span class="badge bg-{'warning' if user['role'] == 'premium' else 'primary' if user['role'] == 'lifetime' else 'secondary'} text-{'dark' if user['role'] == 'premium' else 'white'}">
                                        {user['role'].upper()}
                                    </span>
                                </div>
                            </div>
                        </div>'''
        
        if not leaderboard:
            html_content += '''
                        <div class="text-center py-5">
                            <i class="fas fa-users fa-4x text-muted mb-3"></i>
                            <h4 class="text-muted">Aucun parrain dans le classement</h4>
                            <p class="text-muted">Soyez le premier à parrainer des amis !</p>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement du leaderboard: {str(e)}</p>"

# ============================================================================
# API POUR LE PARRAINAGE
# ============================================================================

@referral_bp.route('/api/referral/generate-link', methods=['POST'])
@login_required
def api_generate_referral_link():
    """API pour générer ou récupérer le lien de parrainage"""
    try:
        user = get_current_user()
        result = get_referral_link(user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@referral_bp.route('/api/referral/stats')
@login_required
def api_get_referral_stats():
    """API pour récupérer les statistiques de parrainage"""
    try:
        user = get_current_user()
        result = get_user_referral_stats(user['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# ADMINISTRATION DU PARRAINAGE
# ============================================================================

@referral_bp.route('/admin/parrainage')
@admin_required
def admin_referral_page():
    """Page d'administration du système de parrainage"""
    try:
        # Récupération des parrainages
        referrals_result = get_all_referrals_admin(50, 0)
        if not referrals_result['success']:
            return f"Erreur: {referrals_result['error']}"
        
        referrals = referrals_result['referrals']
        
        # Construction de l'interface d'administration
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Administration Parrainage - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .admin-header {{
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .status-badge {{
                    padding: 6px 12px;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    font-weight: bold;
                }}
                .status-pending {{ background: #ffc107; color: #000; }}
                .status-registered {{ background: #17a2b8; color: white; }}
                .status-validated {{ background: #28a745; color: white; }}
                .status-blocked {{ background: #dc3545; color: white; }}
                .referral-row {{
                    background: rgba(255,255,255,0.05);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-left: 4px solid #28a745;
                }}
                .fraud-indicator {{
                    background: rgba(220, 53, 69, 0.1);
                    border: 1px solid #dc3545;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 0.8rem;
                    color: #dc3545;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Administration -->
            <div class="admin-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-cogs me-3"></i>Administration Parrainage</h1>
                            <p class="mb-0">Gestion complète du système de parrainage</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/admin" class="btn btn-outline-light me-2">
                                <i class="fas fa-arrow-left me-1"></i>Admin
                            </a>
                            <a href="/leaderboard-parrainage" class="btn btn-warning">
                                <i class="fas fa-trophy me-1"></i>Leaderboard
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <!-- Statistiques Globales -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-success">{len([r for r in referrals if r['status'] == 'validated'])}</h3>
                                <small class="text-muted">Parrainages Validés</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-info">{len([r for r in referrals if r['status'] == 'registered'])}</h3>
                                <small class="text-muted">En Attente</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-danger">{len([r for r in referrals if r['status'] == 'blocked'])}</h3>
                                <small class="text-muted">Bloqués</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-primary">{len(referrals)}</h3>
                                <small class="text-muted">Total Parrainages</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Filtres et Actions -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-filter me-2"></i>Filtres et Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-3">
                                <label class="form-label">Filtrer par statut:</label>
                                <select class="form-select" id="statusFilter" onchange="filterReferrals()">
                                    <option value="">Tous</option>
                                    <option value="pending">En attente</option>
                                    <option value="registered">Inscrits</option>
                                    <option value="validated">Validés</option>
                                    <option value="blocked">Bloqués</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Actions en masse:</label>
                                <div class="d-grid">
                                    <button class="btn btn-warning" onclick="validateSelected()">
                                        <i class="fas fa-check me-1"></i>Valider Sélectionnés
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Export:</label>
                                <div class="d-grid">
                                    <button class="btn btn-info" onclick="exportReferrals()">
                                        <i class="fas fa-download me-1"></i>Export CSV
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Logs de fraude:</label>
                                <div class="d-grid">
                                    <button class="btn btn-danger" onclick="viewFraudLogs()">
                                        <i class="fas fa-shield-alt me-1"></i>Voir Logs
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des Parrainages -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list me-2"></i>Parrainages Récents ({len(referrals)})</h5>
                    </div>
                    <div class="card-body" id="referralsList">'''
        
        # Affichage des parrainages
        for referral in referrals:
            status_class = f"status-{referral['status']}"
            signup_date = referral['signup_date'][:10] if referral['signup_date'] else 'N/A'
            
            # Indicateurs de fraude potentielle
            fraud_indicators = []
            if not referral['email_verified']:
                fraud_indicators.append('Email non vérifié')
            if not referral['payment_made']:
                fraud_indicators.append('Pas de paiement')
            
            html_content += f'''
                        <div class="referral-row" data-status="{referral['status']}">
                            <div class="row align-items-center">
                                <div class="col-md-1">
                                    <input type="checkbox" class="form-check-input referral-checkbox" value="{referral['id']}">
                                </div>
                                <div class="col-md-2">
                                    <h6 class="mb-0">{referral['referrer_username']}</h6>
                                    <small class="text-muted">{referral['referrer_role']}</small>
                                </div>
                                <div class="col-md-2">
                                    <div class="mb-1">{referral['referee_username'] or 'N/A'}</div>
                                    <small class="text-muted">{referral['referee_email'] or 'N/A'}</small>
                                </div>
                                <div class="col-md-1">
                                    <span class="status-badge {status_class}">{referral['status'].upper()}</span>
                                </div>
                                <div class="col-md-2">
                                    <div class="mb-1">{signup_date}</div>
                                    <small class="text-muted">IP: {referral['signup_ip'] or 'N/A'}</small>
                                </div>
                                <div class="col-md-2">
                                    {'✅ Validé le ' + referral['validation_date'][:10] if referral['validation_date'] else '⏳ En attente'}
                                </div>
                                <div class="col-md-2">'''
            
            # Affichage des indicateurs de fraude
            if fraud_indicators:
                html_content += f'<div class="fraud-indicator mb-2">⚠️ {", ".join(fraud_indicators)}</div>'
            
            html_content += f'''
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-success btn-sm" onclick="changeStatus({referral['id']}, 'validated')">
                                            <i class="fas fa-check"></i>
                                        </button>
                                        <button class="btn btn-danger btn-sm" onclick="changeStatus({referral['id']}, 'blocked')">
                                            <i class="fas fa-ban"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>'''
        
        if not referrals:
            html_content += '''
                        <div class="text-center py-5">
                            <i class="fas fa-users fa-4x text-muted mb-3"></i>
                            <h4 class="text-muted">Aucun parrainage trouvé</h4>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                function filterReferrals() {
                    const filter = document.getElementById('statusFilter').value;
                    const rows = document.querySelectorAll('.referral-row');
                    
                    rows.forEach(row => {
                        if (!filter || row.dataset.status === filter) {
                            row.style.display = 'block';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }
                
                function changeStatus(referralId, newStatus) {
                    const reason = prompt(`Raison du changement vers "${newStatus}":`);
                    if (!reason) return;
                    
                    fetch('/admin/api/referral/change-status', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            referral_id: referralId,
                            new_status: newStatus,
                            reason: reason
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert('Erreur: ' + data.error);
                        }
                    });
                }
                
                function validateSelected() {
                    const selected = Array.from(document.querySelectorAll('.referral-checkbox:checked')).map(cb => cb.value);
                    if (selected.length === 0) {
                        alert('Aucun parrainage sélectionné');
                        return;
                    }
                    
                    const reason = prompt('Raison de la validation en masse:');
                    if (!reason) return;
                    
                    // Implementation de la validation en masse
                    console.log('Validation en masse:', selected, reason);
                }
                
                function exportReferrals() {
                    window.location.href = '/admin/api/referral/export-csv';
                }
                
                function viewFraudLogs() {
                    // Redirection vers la page des logs de fraude
                    window.location.href = '/admin/parrainage/fraud-logs';
                }
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de l'administration: {str(e)}</p>"

# ============================================================================
# API ADMINISTRATION
# ============================================================================

@referral_bp.route('/admin/api/referral/change-status', methods=['POST'])
@admin_required
def admin_change_referral_status():
    """API pour changer le statut d'un parrainage"""
    try:
        admin = get_current_user()
        data = request.get_json()
        
        referral_id = data.get('referral_id')
        new_status = data.get('new_status')
        reason = data.get('reason')
        
        if not all([referral_id, new_status, reason]):
            return jsonify({'success': False, 'error': 'Paramètres manquants'})
        
        result = update_referral_status_admin(referral_id, new_status, admin['id'], reason)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@referral_bp.route('/admin/api/referral/export-csv')
@admin_required
def admin_export_referrals_csv():
    """Export CSV des parrainages"""
    try:
        from flask import Response
        import io
        import csv
        
        # Récupération de tous les parrainages
        referrals_result = get_all_referrals_admin(1000, 0)
        if not referrals_result['success']:
            return f"Erreur: {referrals_result['error']}"
        
        referrals = referrals_result['referrals']
        
        # Création du CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'ID', 'Code Parrainage', 'Parrain', 'Filleul', 'Email Filleul',
            'Statut', 'Date Inscription', 'Date Validation', 'IP Inscription',
            'Email Vérifié', 'Paiement Effectué'
        ])
        
        # Données
        for ref in referrals:
            writer.writerow([
                ref['id'], ref['referral_code'], ref['referrer_username'],
                ref['referee_username'], ref['referee_email'], ref['status'],
                ref['signup_date'], ref['validation_date'], ref['signup_ip'],
                'Oui' if ref['email_verified'] else 'Non',
                'Oui' if ref['payment_made'] else 'Non'
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=parrainages_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        return f"Erreur lors de l'export: {str(e)}"