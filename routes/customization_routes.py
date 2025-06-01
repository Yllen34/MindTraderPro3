"""
Routes de Personnalisation Visuelle - Interface utilisateur pour la customisation
Permet aux utilisateurs de personnaliser leur expérience visuelle dans MindTraderPro
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

# Import des modules de personnalisation
from modules.customization_manager import (
    get_user_customization, save_user_customization, get_available_options,
    generate_user_profile_card, get_customization_statistics, generate_theme_css,
    AVAILABLE_THEMES, PREMIUM_THEMES, BASE_AVATARS, PREMIUM_AVATARS, AVATAR_FRAMES
)

# Création du blueprint pour les routes de personnalisation
customization_bp = Blueprint('customization', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ
# ============================================================================

def login_required(f):
    """Décorateur pour s'assurer que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour accéder à la personnalisation')
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
# INTERFACE PRINCIPALE DE PERSONNALISATION
# ============================================================================

@customization_bp.route('/personnalisation')
@login_required
def customization_page():
    """Page principale de personnalisation visuelle"""
    try:
        user = get_current_user()
        
        # Récupération des préférences actuelles
        current_prefs = get_user_customization(user['id'])
        
        # Récupération des options disponibles selon le rôle
        available_options = get_available_options(user['role'])
        
        # Construction de l'interface HTML complète
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Personnalisation - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .customization-header {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .option-card {{
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    border-radius: 12px;
                    cursor: pointer;
                    margin-bottom: 15px;
                    position: relative;
                }}
                .option-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                .option-card.selected {{
                    border: 2px solid #28a745;
                    background: rgba(40, 167, 69, 0.1);
                }}
                .premium-badge {{
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: linear-gradient(45deg, #ffd700, #ffed4e);
                    color: #000;
                    padding: 4px 8px;
                    border-radius: 50px;
                    font-size: 0.7rem;
                    font-weight: bold;
                }}
                .theme-preview {{
                    width: 100%;
                    height: 60px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                }}
                .avatar-preview {{
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                    color: white;
                    margin: 0 auto 10px;
                }}
                .frame-preview {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                    margin: 0 auto 10px;
                    position: relative;
                }}
                .preview-section {{
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 20px;
                    border: 2px dashed #dee2e6;
                }}
                .notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1050;
                }}
                .role-badge-premium {{
                    background: linear-gradient(45deg, #ffc107, #ffed4e);
                    color: #000;
                }}
                .role-badge-lifetime {{
                    background: linear-gradient(45deg, #007bff, #6610f2);
                    color: white;
                }}
                
                /* Animations pour les cadres */
                @keyframes frameGlow {{
                    0% {{ box-shadow: 0 0 5px currentColor; }}
                    50% {{ box-shadow: 0 0 20px currentColor; }}
                    100% {{ box-shadow: 0 0 5px currentColor; }}
                }}
                
                @keyframes frameSparkle {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                
                @keyframes rainbowShift {{
                    0% {{ border-color: #ff6b6b; }}
                    25% {{ border-color: #4ecdc4; }}
                    50% {{ border-color: #45b7d1; }}
                    75% {{ border-color: #96ceb4; }}
                    100% {{ border-color: #feca57; }}
                }}
                
                .animated-frame.frame-gold-shine {{ animation: frameGlow 2s ease-in-out infinite; }}
                .animated-frame.frame-premium-glow {{ animation: frameGlow 1.5s ease-in-out infinite; }}
                .animated-frame.frame-diamond-sparkle {{ animation: frameSparkle 3s linear infinite; }}
                .animated-frame.frame-rainbow-elite {{ animation: rainbowShift 2s ease-in-out infinite; }}
                .animated-frame.frame-cosmic-legend {{ 
                    animation: frameGlow 2s ease-in-out infinite, frameSparkle 4s linear infinite; 
                    background: linear-gradient(45deg, #667eea, #764ba2);
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Personnalisation -->
            <div class="customization-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-palette me-3"></i>Personnalisation</h1>
                            <p class="mb-0">Customisez votre expérience visuelle dans MindTraderPro</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-light text-dark fs-6 me-2">
                                <i class="fas fa-user me-1"></i>{user['username']}
                            </span>
                            <span class="badge {'role-badge-premium' if user['role'] == 'premium' else 'role-badge-lifetime' if user['role'] == 'lifetime' else 'bg-secondary'} fs-6">
                                {user['role'].upper()}
                            </span>
                            <a href="/" class="btn btn-outline-light ms-2">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="row">
                    <!-- Section Aperçu -->
                    <div class="col-lg-4 order-lg-2">
                        <div class="preview-section">
                            <h5 class="text-center mb-3">
                                <i class="fas fa-eye me-2"></i>Aperçu de votre Profil
                            </h5>
                            <div id="profilePreview">
                                {generate_user_profile_card(user['id'], user['username'], user['role'], current_prefs)}
                            </div>
                            <div class="text-center mt-3">
                                <button class="btn btn-success btn-lg" id="saveChanges" onclick="saveAllChanges()">
                                    <i class="fas fa-save me-2"></i>Sauvegarder
                                </button>
                            </div>
                        </div>
                        
                        {'<div class="alert alert-info"><h6><i class="fas fa-crown me-2"></i>Accès Premium</h6><p class="mb-0">Vous avez accès aux options exclusives Premium !</p></div>' if user['role'] in ['premium', 'lifetime'] else ''}
                        {'<div class="alert alert-primary"><h6><i class="fas fa-gem me-2"></i>Accès Lifetime</h6><p class="mb-0">Vous avez accès à toutes les options de personnalisation !</p></div>' if user['role'] == 'lifetime' else ''}
                    </div>
                    
                    <!-- Section Options -->
                    <div class="col-lg-8 order-lg-1">
                        <!-- Choix du Thème -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-brush me-2"></i>Thèmes</h5>
                                <small class="text-muted">Choisissez l'apparence générale de l'interface</small>
                            </div>
                            <div class="card-body">
                                <div class="row g-3" id="themesContainer">'''
        
        # Génération des cartes de thèmes
        for theme_id, theme_info in available_options['themes'].items():
            is_selected = 'selected' if theme_id == current_prefs['theme'] else ''
            is_premium = theme_info.get('premium_only', False)
            premium_badge = '<span class="premium-badge">PREMIUM</span>' if is_premium else ''
            
            html_content += f'''
                                    <div class="col-md-6 col-lg-4">
                                        <div class="card option-card {is_selected}" onclick="selectTheme('{theme_id}')" data-theme="{theme_id}">
                                            {premium_badge}
                                            <div class="card-body text-center p-3">
                                                <div class="theme-preview" style="background: {theme_info['preview_color']};">
                                                    <i class="{theme_info['icon']} me-2"></i>{theme_info['name']}
                                                </div>
                                                <h6 class="card-title mb-1">{theme_info['name']}</h6>
                                                <small class="text-muted">{theme_info['description']}</small>
                                            </div>
                                        </div>
                                    </div>'''
        
        html_content += '''
                                </div>
                            </div>
                        </div>
                        
                        <!-- Choix de l'Avatar -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-user-circle me-2"></i>Avatars</h5>
                                <small class="text-muted">Sélectionnez votre avatar de profil</small>
                            </div>
                            <div class="card-body">
                                <div class="row g-3" id="avatarsContainer">'''
        
        # Génération des cartes d'avatars
        for avatar_id, avatar_info in available_options['avatars'].items():
            is_selected = 'selected' if avatar_id == current_prefs['avatar'] else ''
            is_premium = avatar_info.get('premium_only', False)
            premium_badge = '<span class="premium-badge">PREMIUM</span>' if is_premium else ''
            
            html_content += f'''
                                    <div class="col-md-4 col-lg-3">
                                        <div class="card option-card {is_selected}" onclick="selectAvatar('{avatar_id}')" data-avatar="{avatar_id}">
                                            {premium_badge}
                                            <div class="card-body text-center p-3">
                                                <div class="avatar-preview" style="background: {avatar_info['color']};">
                                                    <i class="{avatar_info['icon']}"></i>
                                                </div>
                                                <h6 class="card-title mb-1" style="font-size: 0.8rem;">{avatar_info['name']}</h6>
                                            </div>
                                        </div>
                                    </div>'''
        
        html_content += '''
                                </div>
                            </div>
                        </div>
                        
                        <!-- Choix du Cadre -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-crown me-2"></i>Cadres d'Avatar</h5>
                                <small class="text-muted">Choisissez le cadre de votre avatar (selon votre rôle)</small>
                            </div>
                            <div class="card-body">
                                <div class="row g-3" id="framesContainer">'''
        
        # Génération des cartes de cadres
        for frame_id, frame_info in available_options['frames'].items():
            is_selected = 'selected' if frame_id == current_prefs['avatar_frame'] else ''
            is_animated = frame_info.get('animated', False)
            animation_class = 'animated-frame' if is_animated else ''
            animation_badge = '<span class="badge bg-info">ANIMÉ</span>' if is_animated else ''
            
            html_content += f'''
                                    <div class="col-md-4 col-lg-3">
                                        <div class="card option-card {is_selected}" onclick="selectFrame('{frame_id}')" data-frame="{frame_id}">
                                            <div class="card-body text-center p-3">
                                                <div class="frame-preview {frame_info['css_class']} {animation_class}" style="border: 3px solid {frame_info['color']};">
                                                    <i class="fas fa-user"></i>
                                                </div>
                                                <h6 class="card-title mb-1" style="font-size: 0.8rem;">{frame_info['name']}</h6>
                                                {animation_badge}
                                            </div>
                                        </div>
                                    </div>'''
        
        html_content += '''
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Variables globales pour les sélections
                let selectedTheme = '{current_prefs['theme']}';
                let selectedAvatar = '{current_prefs['avatar']}';
                let selectedFrame = '{current_prefs['avatar_frame']}';
                
                // ============================================================================
                // JAVASCRIPT POUR LA PERSONNALISATION
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
                
                // Sélection d'un thème
                function selectTheme(themeId) {{
                    // Retirer la sélection précédente
                    document.querySelectorAll('[data-theme]').forEach(card => {{
                        card.classList.remove('selected');
                    }});
                    
                    // Ajouter la sélection au nouveau thème
                    document.querySelector(`[data-theme="${{themeId}}"]`).classList.add('selected');
                    selectedTheme = themeId;
                    
                    // Mettre à jour l'aperçu
                    updatePreview();
                }}
                
                // Sélection d'un avatar
                function selectAvatar(avatarId) {{
                    // Retirer la sélection précédente
                    document.querySelectorAll('[data-avatar]').forEach(card => {{
                        card.classList.remove('selected');
                    }});
                    
                    // Ajouter la sélection au nouvel avatar
                    document.querySelector(`[data-avatar="${{avatarId}}"]`).classList.add('selected');
                    selectedAvatar = avatarId;
                    
                    // Mettre à jour l'aperçu
                    updatePreview();
                }}
                
                // Sélection d'un cadre
                function selectFrame(frameId) {{
                    // Retirer la sélection précédente
                    document.querySelectorAll('[data-frame]').forEach(card => {{
                        card.classList.remove('selected');
                    }});
                    
                    // Ajouter la sélection au nouveau cadre
                    document.querySelector(`[data-frame="${{frameId}}"]`).classList.add('selected');
                    selectedFrame = frameId;
                    
                    // Mettre à jour l'aperçu
                    updatePreview();
                }}
                
                // Mise à jour de l'aperçu en temps réel
                async function updatePreview() {{
                    try {{
                        const response = await fetch('/personnalisation/preview', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                theme: selectedTheme,
                                avatar: selectedAvatar,
                                avatar_frame: selectedFrame
                            }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            document.getElementById('profilePreview').innerHTML = result.preview_html;
                        }}
                    }} catch (error) {{
                        console.log('Erreur lors de la mise à jour de l\'aperçu:', error);
                    }}
                }}
                
                // Sauvegarde de toutes les modifications
                async function saveAllChanges() {{
                    try {{
                        const response = await fetch('/personnalisation/save', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                theme: selectedTheme,
                                avatar: selectedAvatar,
                                avatar_frame: selectedFrame
                            }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            
                            // Redirection pour appliquer les changements
                            setTimeout(() => {{
                                window.location.reload();
                            }}, 2000);
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur lors de la sauvegarde', 'error');
                    }}
                }}
                
                // Initialisation de la page
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('Page de personnalisation chargée');
                    
                    // Marquer les options actuellement sélectionnées
                    if (selectedTheme) {{
                        const themeCard = document.querySelector(`[data-theme="${{selectedTheme}}"]`);
                        if (themeCard) themeCard.classList.add('selected');
                    }}
                    
                    if (selectedAvatar) {{
                        const avatarCard = document.querySelector(`[data-avatar="${{selectedAvatar}}"]`);
                        if (avatarCard) avatarCard.classList.add('selected');
                    }}
                    
                    if (selectedFrame) {{
                        const frameCard = document.querySelector(`[data-frame="${{selectedFrame}}"]`);
                        if (frameCard) frameCard.classList.add('selected');
                    }}
                }});
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de la personnalisation: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LA PERSONNALISATION
# ============================================================================

@customization_bp.route('/personnalisation/preview', methods=['POST'])
@login_required
def api_preview_customization():
    """API pour prévisualiser les modifications de personnalisation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Récupération des paramètres temporaires
        temp_preferences = {
            'theme': data.get('theme', 'dark'),
            'avatar': data.get('avatar', 'trader_1'),
            'avatar_frame': data.get('avatar_frame', 'simple'),
            'custom_settings': {}
        }
        
        # Génération de l'aperçu avec les nouveaux paramètres
        preview_html = generate_user_profile_card(
            user['id'], 
            user['username'], 
            user['role'], 
            temp_preferences
        )
        
        return jsonify({
            'success': True,
            'preview_html': preview_html
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@customization_bp.route('/personnalisation/save', methods=['POST'])
@login_required
def api_save_customization():
    """API pour sauvegarder les préférences de personnalisation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        theme = data.get('theme')
        avatar = data.get('avatar')
        avatar_frame = data.get('avatar_frame')
        
        # Validation des options selon le rôle utilisateur
        available_options = get_available_options(user['role'])
        
        # Vérification que le thème est disponible
        if theme and theme not in available_options['themes']:
            return jsonify({'success': False, 'error': 'Thème non disponible pour votre rôle'})
        
        # Vérification que l'avatar est disponible
        if avatar and avatar not in available_options['avatars']:
            return jsonify({'success': False, 'error': 'Avatar non disponible pour votre rôle'})
        
        # Vérification que le cadre est disponible
        if avatar_frame and avatar_frame not in available_options['frames']:
            return jsonify({'success': False, 'error': 'Cadre non disponible pour votre rôle'})
        
        # Sauvegarde des préférences
        result = save_user_customization(
            user['id'],
            theme=theme,
            avatar=avatar,
            avatar_frame=avatar_frame
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@customization_bp.route('/personnalisation/css/<theme_name>')
def api_theme_css(theme_name):
    """API pour récupérer le CSS d'un thème spécifique"""
    try:
        css_content = generate_theme_css(theme_name)
        
        return css_content, 200, {'Content-Type': 'text/css'}
        
    except Exception as e:
        return f"/* Erreur lors de la génération du CSS: {str(e)} */", 400

@customization_bp.route('/personnalisation/reset', methods=['POST'])
@login_required
def api_reset_customization():
    """API pour réinitialiser les préférences aux valeurs par défaut"""
    try:
        user = get_current_user()
        
        # Réinitialisation aux valeurs par défaut
        result = save_user_customization(
            user['id'],
            theme='dark',
            avatar='trader_1',
            avatar_frame='simple',
            custom_settings={}
        )
        
        if result['success']:
            result['message'] = 'Préférences réinitialisées aux valeurs par défaut'
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@customization_bp.route('/personnalisation/export', methods=['GET'])
@login_required
def api_export_customization():
    """API pour exporter les préférences de personnalisation"""
    try:
        user = get_current_user()
        preferences = get_user_customization(user['id'])
        
        export_data = {
            'user_id': user['id'],
            'username': user['username'],
            'preferences': preferences,
            'export_date': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400