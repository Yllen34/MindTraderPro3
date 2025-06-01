"""
MindTraderPro - Navigation unifiée moderne
Système de navigation avec détection de session automatique
"""

from flask import session

def get_user_session_info():
    """Récupère les informations de session utilisateur de façon sécurisée"""
    if 'user_id' in session and session.get('is_authenticated', False):
        return {
            'is_authenticated': True,
            'name': session.get('user_name', 'Utilisateur'),
            'first_name': session.get('user_first_name', 'Utilisateur'),
            'role': session.get('role', 'standard'),
            'email': session.get('user_email', ''),
            'user_id': session.get('user_id')
        }
    else:
        return {
            'is_authenticated': False,
            'name': 'Visiteur',
            'first_name': 'Visiteur',
            'role': 'anonymous',
            'email': None,
            'user_id': None
        }

def get_modern_navbar(active_page="home"):
    """Navigation moderne unifiée avec détection de session automatique"""
    user_info = get_user_session_info()
    
    if user_info['is_authenticated']:
        # Navigation pour utilisateur connecté avec menu complet
        return f'''
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/home">
                    <i class="fas fa-chart-line me-2" style="color: #00ff88;"></i>MindTraderPro
                </a>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link {'active fw-bold' if active_page == 'home' else ''}" href="/home">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active fw-bold' if active_page == 'calculator' else ''}" href="/calculator">
                                <i class="fas fa-calculator me-1"></i>Calculateur
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active fw-bold' if active_page == 'journal' else ''}" href="/journal">
                                <i class="fas fa-book me-1"></i>Journal
                            </a>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-trophy me-1"></i>Classements
                            </a>
                            <ul class="dropdown-menu" style="background: rgba(0,0,0,0.95);">
                                <li><a class="dropdown-item text-light" href="/leaderboard"><i class="fas fa-trophy me-2"></i>Traders</a></li>
                                <li><a class="dropdown-item text-light" href="/leaderboard-parrainage"><i class="fas fa-users me-2"></i>Parrains</a></li>
                            </ul>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-cogs me-1"></i>Plus
                            </a>
                            <ul class="dropdown-menu" style="background: rgba(0,0,0,0.95);">
                                <li><a class="dropdown-item text-light" href="/grades"><i class="fas fa-medal me-2"></i>Grades</a></li>
                                <li><a class="dropdown-item text-light" href="/suggestions"><i class="fas fa-lightbulb me-2"></i>Suggestions</a></li>
                                <li><a class="dropdown-item text-light" href="/parrainage"><i class="fas fa-handshake me-2"></i>Parrainage</a></li>
                                <li><a class="dropdown-item text-light" href="/personnalisation"><i class="fas fa-palette me-2"></i>Thèmes</a></li>
                            </ul>
                        </li>
                    </ul>
                    
                    <!-- Badge utilisateur fixe et cliquable -->
                    <div class="d-flex align-items-center">
                        <!-- Badge desktop -->
                        <div class="user-badge me-3 text-center d-none d-lg-block" 
                             onclick="window.location.href='/profil'" 
                             style="min-width: 100px; cursor: pointer; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;"
                             onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.boxShadow='0 4px 15px rgba(0,255,136,0.3)'; this.style.transform='translateY(-2px)';"
                             onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.boxShadow='none'; this.style.transform='translateY(0)';">
                            <small class="text-warning d-block fw-bold" style="font-size: 0.8rem;">2,450 XP</small>
                            <small class="text-muted" style="font-size: 0.7rem;">Trader Régulier</small>
                        </div>
                        
                        <!-- Badge mobile -->
                        <div class="user-badge-mobile me-2 d-lg-none" 
                             onclick="window.location.href='/profil'" 
                             style="cursor: pointer; padding: 6px 10px; border-radius: 6px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;"
                             onmouseover="this.style.background='rgba(255,255,255,0.2)';"
                             onmouseout="this.style.background='rgba(255,255,255,0.1)';">
                            <small class="text-warning fw-bold" style="font-size: 0.7rem;">2,450 XP</small>
                        </div>
                        
                        <div class="dropdown">
                            <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown">
                                <div class="user-avatar me-2" style="width: 32px; height: 32px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                                    <i class="fas fa-user"></i>
                                </div>
                                <div class="d-none d-sm-block text-start">
                                    <div style="font-size: 0.9rem; font-weight: bold;">{user_info['first_name']}</div>
                                    <div style="font-size: 0.7rem; opacity: 0.8; color: #FFD700;">{user_info['role'].title()}</div>
                                </div>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end" style="background: rgba(0,0,0,0.95); border: 1px solid rgba(255,255,255,0.2);">
                                <li><a class="dropdown-item text-light" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i>Mon Dashboard</a></li>
                                <li><a class="dropdown-item text-light" href="/profil"><i class="fas fa-user me-2"></i>Mon Profil</a></li>
                                <li><hr class="dropdown-divider" style="border-color: rgba(255,255,255,0.2);"></li>
                                <li><a class="dropdown-item text-danger" href="/logout"><i class="fas fa-sign-out-alt me-2"></i>Déconnexion</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
        '''
    else:
        # Navigation pour visiteur non connecté (accès limité)
        return f'''
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/home">
                    <i class="fas fa-chart-line me-2" style="color: #00ff88;"></i>MindTraderPro
                </a>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link {'active fw-bold' if active_page == 'home' else ''}" href="/home">
                                <i class="fas fa-home me-1"></i>Accueil
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {'active fw-bold' if active_page == 'calculator' else ''}" href="/calculator">
                                <i class="fas fa-calculator me-1"></i>Calculateur
                            </a>
                        </li>
                    </ul>
                    
                    <div class="d-flex">
                        <a href="/login" class="btn btn-outline-light me-2">
                            <i class="fas fa-sign-in-alt me-1"></i>Connexion
                        </a>
                        <a href="/register" class="btn btn-success">
                            <i class="fas fa-user-plus me-1"></i>Inscription
                        </a>
                    </div>
                </div>
            </div>
        </nav>
        '''

def get_user_status_bar():
    """Barre de statut utilisateur supprimée - maintenant intégrée dans la navbar"""
    return ""

def get_page_template(title, content, active_page="home", include_status_bar=True):
    """Template de page complet avec navigation unifiée"""
    navbar = get_modern_navbar(active_page)
    status_bar = get_user_status_bar() if include_status_bar else ""
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - MindTraderPro</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/mindtraderpro-unified.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            body {{ padding-top: 0; }} /* Suppression espacement pour sticky navbar */
            .user-badge:hover {{ transform: translateY(-2px); }}
            .user-badge-mobile:hover {{ transform: scale(1.05); }}
            .navbar.sticky-top {{ position: sticky !important; top: 0; z-index: 1030; }}
        </style>
    </head>
    <body class="modern-body">
        {navbar}
        {status_bar}
        {content}
    </body>
    </html>
    '''