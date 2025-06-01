"""
Routes d'Administration - Interface complète pour les administrateurs
Accès sécurisé et gestion complète du système MindTraderPro
"""

import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from functools import wraps

# Import des modules administratifs
from modules.admin_manager import (
    get_all_users, update_user_role, reset_user_password, update_user_quota,
    reset_user_calc_count, delete_user_account, get_all_trades, admin_delete_trade,
    get_all_partnerships, create_partnership, update_partnership,
    get_system_modules, toggle_system_module, get_admin_logs
)
from modules.grade_manager import (
    get_all_users_grades, manually_adjust_user_xp, manually_set_user_grade,
    get_grade_statistics, get_user_xp_history, add_user_xp_with_notifications
)

# Création du blueprint pour les routes d'administration
admin_bp = Blueprint('admin', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ ADMINISTRATIFS
# ============================================================================

def admin_required(f):
    """Décorateur pour s'assurer que seuls les admins peuvent accéder aux routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérification stricte de la connexion utilisateur
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour accéder à l\'administration')
        
        # Vérification stricte du rôle administrateur
        user_role = session.get('role', 'standard')
        if user_role != 'admin':
            return redirect('/login?message=Accès administrateur requis - Permissions insuffisantes')
        
        # Log de l'accès administrateur pour traçabilité
        admin_username = session.get('username', 'Admin inconnu')
        print(f"🔐 Accès administrateur autorisé pour: {admin_username} (ID: {session['user_id']})")
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_admin():
    """Récupère les informations de l'administrateur actuel"""
    if 'user_id' in session:
        # Cette fonction sera adaptée selon l'implémentation de get_user_by_id
        return {'id': session['user_id'], 'username': 'admin', 'role': 'admin'}
    return None

# ============================================================================
# INTERFACE PRINCIPALE D'ADMINISTRATION
# ============================================================================

@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Dashboard principal d'administration avec vue d'ensemble"""
    try:
        # Récupération des statistiques globales
        users = get_all_users()
        trades = get_all_trades(limit=10)  # 10 derniers trades
        recent_logs = get_admin_logs(limit=10)
        modules_status = get_system_modules()
        
        # Calculs statistiques
        total_users = len(users)
        active_users = len([u for u in users if u['trade_count'] > 0])
        total_trades = sum(u['trade_count'] for u in users)
        
        # Construction de l'interface HTML complète
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Administration - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .admin-header {{
                    background: linear-gradient(135deg, #dc3545, #ffc107);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    transition: transform 0.3s ease;
                    border-left: 4px solid #dc3545;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                .admin-sidebar {{
                    background: #343a40;
                    min-height: 100vh;
                    padding: 20px 0;
                }}
                .admin-nav-link {{
                    color: #adb5bd;
                    text-decoration: none;
                    padding: 10px 20px;
                    display: block;
                    border-radius: 5px;
                    margin: 5px 10px;
                }}
                .admin-nav-link:hover {{
                    background: #495057;
                    color: white;
                }}
                .admin-nav-link.active {{
                    background: #dc3545;
                    color: white;
                }}
                .notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1050;
                }}
                .danger-zone {{
                    border: 2px solid #dc3545;
                    border-radius: 8px;
                    padding: 20px;
                    background: rgba(220, 53, 69, 0.1);
                }}
            </style>
        </head>
        <body>
            <!-- En-tête d'administration -->
            <div class="admin-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h1><i class="fas fa-shield-alt me-3"></i>Panneau d'Administration</h1>
                            <p class="mb-0">MindTraderPro - Interface de gestion complète</p>
                        </div>
                        <div class="col-md-6 text-end">
                            <span class="badge bg-light text-dark fs-6">Admin connecté</span>
                            <a href="/" class="btn btn-outline-light ms-2">
                                <i class="fas fa-home me-1"></i>Retour au site
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container-fluid">
                <div class="row">
                    <!-- Sidebar de navigation -->
                    <div class="col-md-2">
                        <div class="admin-sidebar">
                            <nav>
                                <a href="#dashboard" class="admin-nav-link active" onclick="showSection('dashboard')">
                                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                                </a>
                                <a href="#users" class="admin-nav-link" onclick="showSection('users')">
                                    <i class="fas fa-users me-2"></i>Utilisateurs
                                </a>
                                <a href="#trades" class="admin-nav-link" onclick="showSection('trades')">
                                    <i class="fas fa-chart-line me-2"></i>Journal Global
                                </a>
                                <a href="#partnerships" class="admin-nav-link" onclick="showSection('partnerships')">
                                    <i class="fas fa-handshake me-2"></i>Partenariats
                                </a>
                                <a href="#modules" class="admin-nav-link" onclick="showSection('modules')">
                                    <i class="fas fa-cogs me-2"></i>Modules Système
                                </a>
                                <a href="#logs" class="admin-nav-link" onclick="showSection('logs')">
                                    <i class="fas fa-file-alt me-2"></i>Logs Admin
                                </a>
                            </nav>
                        </div>
                    </div>
                    
                    <!-- Contenu principal -->
                    <div class="col-md-10">
                        <!-- Section Dashboard -->
                        <div id="dashboard-section" class="admin-section">
                            <h2><i class="fas fa-chart-bar me-2"></i>Vue d'ensemble</h2>
                            
                            <!-- Statistiques globales -->
                            <div class="row g-3 mb-4">
                                <div class="col-md-3">
                                    <div class="card stat-card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-users fa-2x text-primary mb-2"></i>
                                            <h3>{total_users}</h3>
                                            <small class="text-muted">Utilisateurs Total</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-user-check fa-2x text-success mb-2"></i>
                                            <h3>{active_users}</h3>
                                            <small class="text-muted">Utilisateurs Actifs</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-chart-line fa-2x text-info mb-2"></i>
                                            <h3>{total_trades}</h3>
                                            <small class="text-muted">Trades Total</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-shield-alt fa-2x text-warning mb-2"></i>
                                            <h3>{len(recent_logs)}</h3>
                                            <small class="text-muted">Actions Récentes</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Actions rapides -->
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5><i class="fas fa-bolt me-2"></i>Actions Rapides</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="d-grid gap-2">
                                                <button class="btn btn-primary" onclick="showSection('users')">
                                                    <i class="fas fa-user-plus me-2"></i>Gérer les Utilisateurs
                                                </button>
                                                <button class="btn btn-success" onclick="showSection('partnerships')">
                                                    <i class="fas fa-plus me-2"></i>Ajouter un Partenariat
                                                </button>
                                                <button class="btn btn-warning" onclick="showSection('modules')">
                                                    <i class="fas fa-toggle-on me-2"></i>Gérer les Modules
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5><i class="fas fa-clock me-2"></i>Activité Récente</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="list-group list-group-flush">'''
        
        # Ajout des logs récents
        for log in recent_logs[:5]:
            html_content += f'''
                                                <div class="list-group-item border-0 px-0">
                                                    <small class="text-muted">{log['created_at']}</small><br>
                                                    <strong>{log['admin_username']}</strong> - {log['action']}<br>
                                                    <span class="text-muted">{log['details']}</span>
                                                </div>'''
        
        html_content += '''
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Section Gestion des Utilisateurs -->
                        <div id="users-section" class="admin-section" style="display: none;">
                            <h2><i class="fas fa-users me-2"></i>Gestion des Utilisateurs</h2>
                            
                            <div class="card">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <h5>Liste des Utilisateurs</h5>
                                    <button class="btn btn-primary" onclick="refreshUsers()">
                                        <i class="fas fa-sync me-1"></i>Actualiser
                                    </button>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-striped" id="usersTable">
                                            <thead class="table-dark">
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Nom d'utilisateur</th>
                                                    <th>Email</th>
                                                    <th>Rôle</th>
                                                    <th>Trades</th>
                                                    <th>Calculs</th>
                                                    <th>Inscription</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="usersTableBody">'''
        
        # Génération du tableau des utilisateurs
        for user in users:
            role_badge_class = {
                'admin': 'bg-danger',
                'lifetime': 'bg-warning',
                'premium': 'bg-success',
                'standard': 'bg-secondary'
            }.get(user['role'], 'bg-secondary')
            
            html_content += f'''
                                                <tr>
                                                    <td>{user['id']}</td>
                                                    <td><strong>{user['username']}</strong></td>
                                                    <td>{user['email']}</td>
                                                    <td><span class="badge {role_badge_class}">{user['role'].upper()}</span></td>
                                                    <td>{user['trade_count']}</td>
                                                    <td>{user['calc_count']}/{user['calc_limit']}</td>
                                                    <td>{user['created_at'][:10] if user['created_at'] else 'N/A'}</td>
                                                    <td>
                                                        <div class="btn-group btn-group-sm">
                                                            <button class="btn btn-info" onclick="editUser({user['id']})">
                                                                <i class="fas fa-edit"></i>
                                                            </button>
                                                            <button class="btn btn-warning" onclick="resetPassword({user['id']})">
                                                                <i class="fas fa-key"></i>
                                                            </button>
                                                            <button class="btn btn-success" onclick="resetCalc({user['id']})">
                                                                <i class="fas fa-undo"></i>
                                                            </button>
                                                            <button class="btn btn-danger" onclick="deleteUser({user['id']})">
                                                                <i class="fas fa-trash"></i>
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>'''
        
        html_content += '''
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Section Journal Global -->
                        <div id="trades-section" class="admin-section" style="display: none;">
                            <h2><i class="fas fa-chart-line me-2"></i>Journal de Trading Global</h2>
                            
                            <!-- Filtres -->
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h6><i class="fas fa-filter me-2"></i>Filtres</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <select class="form-select" id="filterTradeUser">
                                                <option value="">Tous les utilisateurs</option>'''
        
        # Options d'utilisateurs pour le filtre
        for user in users:
            html_content += f'<option value="{user["id"]}">{user["username"]} ({user["email"]})</option>'
        
        html_content += '''
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <select class="form-select" id="filterTradeAsset">
                                                <option value="">Tous les actifs</option>
                                                <option value="EURUSD">EUR/USD</option>
                                                <option value="XAUUSD">XAU/USD</option>
                                                <option value="GBPUSD">GBP/USD</option>
                                            </select>
                                        </div>
                                        <div class="col-md-2">
                                            <input type="date" class="form-control" id="filterTradeDateFrom" placeholder="Date début">
                                        </div>
                                        <div class="col-md-2">
                                            <input type="date" class="form-control" id="filterTradeDateTo" placeholder="Date fin">
                                        </div>
                                        <div class="col-md-2">
                                            <button class="btn btn-primary w-100" onclick="filterTrades()">
                                                <i class="fas fa-search me-1"></i>Filtrer
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <div class="card-header">
                                    <h5>Tous les Trades</h5>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-striped" id="tradesTable">
                                            <thead class="table-dark">
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Utilisateur</th>
                                                    <th>Actif</th>
                                                    <th>Type</th>
                                                    <th>Date</th>
                                                    <th>P&L</th>
                                                    <th>Statut</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="tradesTableBody">'''
        
        # Génération du tableau des trades
        for trade in trades:
            pnl_class = ''
            if trade['result_pnl']:
                pnl_class = 'text-success' if trade['result_pnl'] > 0 else 'text-danger'
            
            html_content += f'''
                                                <tr>
                                                    <td>{trade['id']}</td>
                                                    <td><strong>{trade['username']}</strong><br><small>{trade['user_email']}</small></td>
                                                    <td>{trade['asset']}</td>
                                                    <td><span class="badge {'bg-success' if trade['trade_type'] == 'buy' else 'bg-danger'}">{trade['trade_type'].upper()}</span></td>
                                                    <td>{trade['trade_date'][:10] if trade['trade_date'] else 'N/A'}</td>
                                                    <td class="{pnl_class}">${trade['result_pnl'] or 0}</td>
                                                    <td><span class="badge bg-{'success' if trade['status'] == 'closed' else 'primary'}">{trade['status'].upper()}</span></td>
                                                    <td>
                                                        <button class="btn btn-danger btn-sm" onclick="adminDeleteTrade({trade['id']})">
                                                            <i class="fas fa-trash"></i>
                                                        </button>
                                                    </td>
                                                </tr>'''
        
        html_content += '''
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Section Partenariats -->
                        <div id="partnerships-section" class="admin-section" style="display: none;">
                            <h2><i class="fas fa-handshake me-2"></i>Gestion des Partenariats</h2>
                            
                            <!-- Formulaire d'ajout -->
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h5><i class="fas fa-plus me-2"></i>Ajouter un Partenariat</h5>
                                </div>
                                <div class="card-body">
                                    <form id="partnershipForm">
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Titre</label>
                                                <input type="text" class="form-control" id="partnerTitle" required>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Lien</label>
                                                <input type="url" class="form-control" id="partnerLink" required>
                                            </div>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Description</label>
                                            <textarea class="form-control" id="partnerDescription" rows="3" required></textarea>
                                        </div>
                                        <div class="mb-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="partnerActive" checked>
                                                <label class="form-check-label" for="partnerActive">
                                                    Actif (visible sur le site)
                                                </label>
                                            </div>
                                        </div>
                                        <button type="submit" class="btn btn-success">
                                            <i class="fas fa-save me-2"></i>Créer le Partenariat
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Section Modules Système -->
                        <div id="modules-section" class="admin-section" style="display: none;">
                            <h2><i class="fas fa-cogs me-2"></i>Gestion des Modules Système</h2>
                            
                            <div class="card">
                                <div class="card-header">
                                    <h5>État des Modules</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">'''
        
        # Génération des modules système
        for module_name, module_info in modules_status.items():
            status_class = 'text-success' if module_info['is_active'] else 'text-danger'
            status_icon = 'fa-check-circle' if module_info['is_active'] else 'fa-times-circle'
            
            html_content += f'''
                                        <div class="col-md-6 mb-3">
                                            <div class="card">
                                                <div class="card-body">
                                                    <div class="d-flex justify-content-between align-items-center">
                                                        <div>
                                                            <h6>{module_name.replace('_', ' ').title()}</h6>
                                                            <small class="text-muted">{module_info.get('description', 'Module système')}</small>
                                                        </div>
                                                        <div class="text-end">
                                                            <i class="fas {status_icon} {status_class} fa-lg"></i><br>
                                                            <button class="btn btn-sm {'btn-danger' if module_info['is_active'] else 'btn-success'} mt-2" 
                                                                    onclick="toggleModule('{module_name}', {str(not module_info['is_active']).lower()})">
                                                                {'Désactiver' if module_info['is_active'] else 'Activer'}
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>'''
        
        html_content += '''
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Section Logs Administratifs -->
                        <div id="logs-section" class="admin-section" style="display: none;">
                            <h2><i class="fas fa-file-alt me-2"></i>Logs des Actions Administratives</h2>
                            
                            <div class="card">
                                <div class="card-header">
                                    <h5>Historique des Actions</h5>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-striped">
                                            <thead class="table-dark">
                                                <tr>
                                                    <th>Date</th>
                                                    <th>Admin</th>
                                                    <th>Action</th>
                                                    <th>Cible</th>
                                                    <th>Détails</th>
                                                </tr>
                                            </thead>
                                            <tbody>'''
        
        # Génération des logs
        for log in recent_logs:
            html_content += f'''
                                                <tr>
                                                    <td>{log['created_at']}</td>
                                                    <td><strong>{log['admin_username']}</strong></td>
                                                    <td><span class="badge bg-info">{log['action']}</span></td>
                                                    <td>{log['target_username'] if log['target_username'] else '-'}</td>
                                                    <td>{log['details']}</td>
                                                </tr>'''
        
        html_content += '''
                                            </tbody>
                                        </table>
                                    </div>
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
                // ============================================================================
                // JAVASCRIPT POUR L'INTERFACE D'ADMINISTRATION
                // ============================================================================
                
                // Navigation entre les sections
                function showSection(sectionName) {
                    // Masquer toutes les sections
                    document.querySelectorAll('.admin-section').forEach(section => {
                        section.style.display = 'none';
                    });
                    
                    // Retirer la classe active de tous les liens
                    document.querySelectorAll('.admin-nav-link').forEach(link => {
                        link.classList.remove('active');
                    });
                    
                    // Afficher la section demandée
                    document.getElementById(sectionName + '-section').style.display = 'block';
                    
                    // Activer le lien correspondant
                    event.target.classList.add('active');
                }
                
                // Fonction pour afficher des notifications
                function showNotification(message, type = 'success') {
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
                
                // ============================================================================
                // GESTION DES UTILISATEURS
                // ============================================================================
                
                function editUser(userId) {
                    const newRole = prompt('Nouveau rôle (standard, premium, lifetime, admin):');
                    if (newRole && ['standard', 'premium', 'lifetime', 'admin'].includes(newRole)) {
                        updateUserRole(userId, newRole);
                    }
                }}
                
                async function updateUserRole(userId, newRole) {
                    try {
                        const response = await fetch('/admin/update-user-role', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: userId, new_role: newRole })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            refreshUsers();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                function resetPassword(userId) {
                    const newPassword = prompt('Nouveau mot de passe (minimum 6 caractères):');
                    if (newPassword && newPassword.length >= 6) {
                        resetUserPassword(userId, newPassword);
                    }
                }}
                
                async function resetUserPassword(userId, newPassword) {
                    try {
                        const response = await fetch('/admin/reset-user-password', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: userId, new_password: newPassword })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                function resetCalc(userId) {
                    if (confirm('Remettre à zéro le compteur de calculs ?')) {
                        resetUserCalc(userId);
                    }
                }}
                
                async function resetUserCalc(userId) {
                    try {
                        const response = await fetch('/admin/reset-user-calc', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: userId })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            refreshUsers();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                function deleteUser(userId) {
                    if (confirm('ATTENTION: Supprimer définitivement cet utilisateur et toutes ses données ?')) {
                        deleteUserAccount(userId);
                    }
                }}
                
                async function deleteUserAccount(userId) {
                    try {
                        const response = await fetch('/admin/delete-user', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: userId })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            refreshUsers();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                function refreshUsers() {
                    window.location.reload();
                }}
                
                // ============================================================================
                // GESTION DES TRADES
                // ============================================================================
                
                function adminDeleteTrade(tradeId) {
                    if (confirm('Supprimer ce trade définitivement ?')) {
                        deleteTrade(tradeId);
                    }
                }}
                
                async function deleteTrade(tradeId) {
                    try {
                        const response = await fetch('/admin/delete-trade', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ trade_id: tradeId })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            showSection('trades');
                            window.location.reload();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                // ============================================================================
                // GESTION DES MODULES
                // ============================================================================
                
                async function toggleModule(moduleName, isActive) {
                    try {
                        const response = await fetch('/admin/toggle-module', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ module_name: moduleName, is_active: isActive })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            window.location.reload();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }}
                
                // ============================================================================
                // GESTION DES PARTENARIATS
                // ============================================================================
                
                document.getElementById('partnershipForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const title = document.getElementById('partnerTitle').value;
                    const description = document.getElementById('partnerDescription').value;
                    const link = document.getElementById('partnerLink').value;
                    const isActive = document.getElementById('partnerActive').checked;
                    
                    try {
                        const response = await fetch('/admin/create-partnership', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                title: title,
                                description: description,
                                link: link,
                                is_active: isActive
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ ' + result.message, 'success');
                            document.getElementById('partnershipForm').reset();
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }});
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de l'administration: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES ACTIONS ADMINISTRATIVES
# ============================================================================

@admin_bp.route('/admin/update-user-role', methods=['POST'])
@admin_required
def api_update_user_role():
    """API pour modifier le rôle d'un utilisateur"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        new_role = data.get('new_role')
        
        if not user_id or not new_role:
            return jsonify({'success': False, 'error': 'Paramètres manquants'})
        
        result = update_user_role(user_id, new_role, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/reset-user-password', methods=['POST'])
@admin_required
def api_reset_user_password():
    """API pour réinitialiser le mot de passe d'un utilisateur"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not user_id or not new_password:
            return jsonify({'success': False, 'error': 'Paramètres manquants'})
        
        result = reset_user_password(user_id, new_password, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/reset-user-calc', methods=['POST'])
@admin_required
def api_reset_user_calc():
    """API pour remettre à zéro le compteur de calculs"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID utilisateur requis'})
        
        result = reset_user_calc_count(user_id, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/delete-user', methods=['POST'])
@admin_required
def api_delete_user():
    """API pour supprimer un compte utilisateur"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID utilisateur requis'})
        
        result = delete_user_account(user_id, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/delete-trade', methods=['POST'])
@admin_required
def api_delete_trade():
    """API pour supprimer un trade"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return jsonify({'success': False, 'error': 'ID trade requis'})
        
        result = admin_delete_trade(trade_id, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/create-partnership', methods=['POST'])
@admin_required
def api_create_partnership():
    """API pour créer un partenariat"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        title = data.get('title')
        description = data.get('description')
        link = data.get('link')
        is_active = data.get('is_active', True)
        
        if not all([title, description, link]):
            return jsonify({'success': False, 'error': 'Tous les champs sont requis'})
        
        result = create_partnership(title, description, link, is_active, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/toggle-module', methods=['POST'])
@admin_required
def api_toggle_module():
    """API pour activer/désactiver un module système"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        module_name = data.get('module_name')
        is_active = data.get('is_active')
        
        if not module_name or is_active is None:
            return jsonify({'success': False, 'error': 'Paramètres manquants'})
        
        result = toggle_system_module(module_name, is_active, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# ADMINISTRATION DES GRADES ET XP
# ============================================================================

@admin_bp.route('/admin/grades')
@admin_required
def admin_grades_page():
    """Interface d'administration des grades et XP"""
    try:
        # Récupération des utilisateurs avec leurs grades
        users = get_all_users_grades(limit=100, sort_by='xp_desc')
        
        # Récupération des statistiques
        stats = get_grade_statistics()
        
        # Construction de l'interface HTML d'administration des grades
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Administration - Grades et XP</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                .admin-header {{
                    background: linear-gradient(135deg, #dc3545, #ffc107);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .grade-badge {{
                    display: inline-flex;
                    align-items: center;
                    padding: 8px 12px;
                    border-radius: 20px;
                    color: white;
                    font-weight: bold;
                    margin-right: 10px;
                }}
                .user-row {{
                    border-radius: 8px;
                    margin-bottom: 10px;
                    padding: 15px;
                    background: rgba(255,255,255,0.05);
                    transition: all 0.3s ease;
                }}
                .user-row:hover {{
                    background: rgba(255,255,255,0.1);
                    transform: translateY(-2px);
                }}
                .stats-card {{
                    background: linear-gradient(135deg, #007bff, #6610f2);
                    color: white;
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1050;
                }}
                .chart-container {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <!-- En-tête Admin Grades -->
            <div class="admin-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-trophy me-3"></i>Administration - Grades et XP</h1>
                            <p class="mb-0">Gestion complète du système de progression utilisateur</p>
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
                <!-- Statistiques Globales -->
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-users fa-2x mb-2"></i>
                            <h3>{len(users)}</h3>
                            <small>Utilisateurs Total</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-star fa-2x mb-2"></i>
                            <h3>{stats.get('avg_xp', 0):.0f}</h3>
                            <small>XP Moyen</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-chart-line fa-2x mb-2"></i>
                            <h3>{stats.get('total_xp', 0)}</h3>
                            <small>XP Total Distribué</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-trophy fa-2x mb-2"></i>
                            <h3>{len(stats.get('grade_distribution', []))}</h3>
                            <small>Grades Actifs</small>
                        </div>
                    </div>
                </div>
                
                <!-- Graphiques -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <h5><i class="fas fa-chart-pie me-2"></i>Répartition des Grades</h5>
                            <canvas id="gradeDistributionChart"></canvas>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <h5><i class="fas fa-chart-line me-2"></i>Évolution XP (7 derniers jours)</h5>
                            <canvas id="xpEvolutionChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Actions Rapides -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-tools me-2"></i>Actions Rapides</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <button class="btn btn-primary w-100 mb-2" data-bs-toggle="modal" data-bs-target="#adjustXpModal">
                                    <i class="fas fa-plus-circle me-1"></i>Ajuster XP Utilisateur
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-warning w-100 mb-2" data-bs-toggle="modal" data-bs-target="#changeGradeModal">
                                    <i class="fas fa-exchange-alt me-1"></i>Changer Grade Utilisateur
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-info w-100 mb-2" onclick="refreshStats()">
                                    <i class="fas fa-sync-alt me-1"></i>Actualiser Statistiques
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Liste des Utilisateurs -->
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-users me-2"></i>Gestion des Utilisateurs</h5>
                        <div>
                            <select class="form-select form-select-sm" id="sortUsers" onchange="sortUsersList()">
                                <option value="xp_desc">XP Décroissant</option>
                                <option value="xp_asc">XP Croissant</option>
                                <option value="grade">Par Grade</option>
                                <option value="username">Par Nom</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">'''
        
        # Génération de la liste des utilisateurs
        for user in users:
            html_content += f'''
                        <div class="user-row" data-user-id="{user['id']}">
                            <div class="row align-items-center">
                                <div class="col-md-3">
                                    <div class="d-flex align-items-center">
                                        <div class="grade-badge" style="background: {user['grade_color']};">
                                            {user['grade_icon']} {user['grade_name']}
                                        </div>
                                    </div>
                                    <h6 class="mb-0">{user['username']}</h6>
                                    <small class="text-muted">ID: {user['id']} | Rôle: {user['role']}</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <h5 class="mb-0 text-primary">{user['xp']}</h5>
                                    <small class="text-muted">XP Total</small>
                                </div>
                                <div class="col-md-2 text-center">
                                    <small class="text-muted">Membre depuis</small><br>
                                    <span>{user['created_at'][:10] if user['created_at'] else 'N/A'}</span>
                                </div>
                                <div class="col-md-5 text-end">
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="showUserHistory({user['id']}, '{user['username']}')">
                                            <i class="fas fa-history"></i> Historique
                                        </button>
                                        <button class="btn btn-outline-warning" onclick="quickAdjustXp({user['id']}, '{user['username']}')">
                                            <i class="fas fa-plus"></i> XP
                                        </button>
                                        <button class="btn btn-outline-info" onclick="quickChangeGrade({user['id']}, '{user['username']}')">
                                            <i class="fas fa-trophy"></i> Grade
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>'''
        
        if not users:
            html_content += '''
                        <div class="text-center py-4">
                            <i class="fas fa-users fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">Aucun utilisateur trouvé</h5>
                        </div>'''
        
        html_content += '''
                    </div>
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Modal Ajustement XP -->
            <div class="modal fade" id="adjustXpModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Ajuster XP Utilisateur</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="adjustXpForm">
                                <div class="mb-3">
                                    <label class="form-label">Utilisateur</label>
                                    <select class="form-select" id="userSelectXp" required>
                                        <option value="">Sélectionnez un utilisateur</option>'''
        
        for user in users:
            html_content += f'<option value="{user["id"]}">{user["username"]} (XP: {user["xp"]})</option>'
        
        html_content += '''
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Changement d'XP</label>
                                    <input type="number" class="form-control" id="xpChange" 
                                           placeholder="Ex: +50 ou -20" required>
                                    <div class="form-text">Utilisez + pour ajouter, - pour retirer</div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Raison</label>
                                    <textarea class="form-control" id="xpReason" rows="3" 
                                              placeholder="Raison de l'ajustement..." required></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="submitXpAdjustment()">
                                Ajuster XP
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modal Changement Grade -->
            <div class="modal fade" id="changeGradeModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Changer Grade Utilisateur</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="changeGradeForm">
                                <div class="mb-3">
                                    <label class="form-label">Utilisateur</label>
                                    <select class="form-select" id="userSelectGrade" required>
                                        <option value="">Sélectionnez un utilisateur</option>'''
        
        for user in users:
            html_content += f'<option value="{user["id"]}">{user["username"]} ({user["grade_name"]})</option>'
        
        html_content += '''
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Nouveau Grade</label>
                                    <select class="form-select" id="newGrade" required>
                                        <option value="">Sélectionnez un grade</option>
                                        <option value="debutant">🌱 Débutant</option>
                                        <option value="actif">⚡ Actif</option>
                                        <option value="trader_regulier">📈 Trader Régulier</option>
                                        <option value="expert">🏆 Expert</option>
                                        <option value="legende">👑 Légende</option>
                                        <option value="lifetime">💎 Lifetime VIP</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Raison</label>
                                    <textarea class="form-control" id="gradeReason" rows="3" 
                                              placeholder="Raison du changement..." required></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-warning" onclick="submitGradeChange()">
                                Changer Grade
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // ============================================================================
                // JAVASCRIPT POUR L'ADMINISTRATION DES GRADES
                // ============================================================================
                
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
                
                // Soumission d'ajustement XP
                async function submitXpAdjustment() {
                    const userId = document.getElementById('userSelectXp').value;
                    const xpChange = parseInt(document.getElementById('xpChange').value);
                    const reason = document.getElementById('xpReason').value.trim();
                    
                    if (!userId || !xpChange || !reason) {
                        showNotification('❌ Tous les champs sont requis', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/admin/grades/adjust-xp', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                user_id: userId,
                                xp_change: xpChange,
                                reason: reason
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ XP ajusté avec succès', 'success');
                            bootstrap.Modal.getInstance(document.getElementById('adjustXpModal')).hide();
                            setTimeout(() => { window.location.reload(); }, 2000);
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }
                
                // Soumission de changement de grade
                async function submitGradeChange() {
                    const userId = document.getElementById('userSelectGrade').value;
                    const newGrade = document.getElementById('newGrade').value;
                    const reason = document.getElementById('gradeReason').value.trim();
                    
                    if (!userId || !newGrade || !reason) {
                        showNotification('❌ Tous les champs sont requis', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/admin/grades/change-grade', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                user_id: userId,
                                new_grade: newGrade,
                                reason: reason
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showNotification('✅ Grade changé avec succès', 'success');
                            bootstrap.Modal.getInstance(document.getElementById('changeGradeModal')).hide();
                            setTimeout(() => { window.location.reload(); }, 2000);
                        } else {
                            showNotification('❌ ' + result.error, 'error');
                        }
                    } catch (error) {
                        showNotification('❌ Erreur de connexion', 'error');
                    }
                }
                
                // Actions rapides
                function quickAdjustXp(userId, username) {
                    document.getElementById('userSelectXp').value = userId;
                    new bootstrap.Modal(document.getElementById('adjustXpModal')).show();
                }
                
                function quickChangeGrade(userId, username) {
                    document.getElementById('userSelectGrade').value = userId;
                    new bootstrap.Modal(document.getElementById('changeGradeModal')).show();
                }
                
                function showUserHistory(userId, username) {
                    // TODO: Implémenter la vue de l'historique utilisateur
                    alert(`Historique de ${username} (ID: ${userId})`);
                }
                
                function refreshStats() {
                    window.location.reload();
                }
                
                // Génération des graphiques
                document.addEventListener('DOMContentLoaded', function() {'''
        
        # Données pour les graphiques
        grade_labels = [grade['name'] for grade in stats.get('grade_distribution', [])]
        grade_data = [grade['user_count'] for grade in stats.get('grade_distribution', [])]
        grade_colors = [grade.get('color', '#6c757d') for grade in stats.get('grade_distribution', [])]
        
        daily_labels = [day['date'] for day in stats.get('daily_xp_evolution', [])]
        daily_data = [day['daily_xp'] for day in stats.get('daily_xp_evolution', [])]
        
        html_content += f'''
                    // Graphique de répartition des grades
                    const gradeCtx = document.getElementById('gradeDistributionChart').getContext('2d');
                    new Chart(gradeCtx, {{
                        type: 'doughnut',
                        data: {{
                            labels: {grade_labels},
                            datasets: [{{
                                data: {grade_data},
                                backgroundColor: {grade_colors}
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    position: 'bottom'
                                }}
                            }}
                        }}
                    }});
                    
                    // Graphique d'évolution XP
                    const xpCtx = document.getElementById('xpEvolutionChart').getContext('2d');
                    new Chart(xpCtx, {{
                        type: 'line',
                        data: {{
                            labels: {daily_labels},
                            datasets: [{{
                                label: 'XP Quotidien',
                                data: {daily_data},
                                borderColor: '#007bff',
                                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                fill: true
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            scales: {{
                                y: {{
                                    beginAtZero: true
                                }}
                            }}
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de l'administration des grades: {str(e)}</p>"

@admin_bp.route('/admin/grades/adjust-xp', methods=['POST'])
@admin_required
def api_admin_adjust_xp():
    """API admin pour ajuster l'XP d'un utilisateur"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        xp_change = data.get('xp_change')
        reason = data.get('reason')
        
        if not all([user_id, xp_change is not None, reason]):
            return jsonify({'success': False, 'error': 'Tous les paramètres sont requis'})
        
        result = manually_adjust_user_xp(user_id, xp_change, admin['id'], reason)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/grades/change-grade', methods=['POST'])
@admin_required
def api_admin_change_grade():
    """API admin pour changer le grade d'un utilisateur"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        new_grade = data.get('new_grade')
        reason = data.get('reason')
        
        if not all([user_id, new_grade, reason]):
            return jsonify({'success': False, 'error': 'Tous les paramètres sont requis'})
        
        result = manually_set_user_grade(user_id, new_grade, admin['id'], reason)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

# ============================================================================
# SYSTÈME DE BONUS XP ADMINISTRATEUR
# ============================================================================

@admin_bp.route('/admin/grades/bonus-xp', methods=['POST'])
@admin_required
def admin_award_bonus_xp():
    """Interface admin pour attribuer des bonus XP aux utilisateurs"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_id = data.get('user_id')
        xp_amount = data.get('xp_amount')
        reason = data.get('reason')
        
        # Validation des paramètres
        if not all([user_id, xp_amount, reason]):
            return jsonify({'success': False, 'error': 'Tous les paramètres sont requis'})
        
        if not isinstance(xp_amount, int) or xp_amount <= 0:
            return jsonify({'success': False, 'error': 'Le montant XP doit être un nombre positif'})
        
        if len(reason.strip()) < 5:
            return jsonify({'success': False, 'error': 'Le motif doit contenir au moins 5 caractères'})
        
        # Attribution du bonus XP avec notifications
        result = add_user_xp_with_notifications(
            user_id, 
            'admin_bonus', 
            xp_amount, 
            f"Bonus admin: {reason.strip()}"
        )
        
        if result['success']:
            # Log administratif
            try:
                import sqlite3
                conn = sqlite3.connect('data/mindtraderpro_users.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO admin_logs (admin_id, action_type, target_user_id, details, created_at)
                    VALUES (?, 'bonus_xp', ?, ?, CURRENT_TIMESTAMP)
                ''', (admin['id'], user_id, f"Bonus XP: +{xp_amount} - {reason}"))
                
                conn.commit()
                conn.close()
            except Exception as log_error:
                print(f"⚠️ Erreur lors du log admin: {log_error}")
            
            result['message'] = f'Bonus de {xp_amount} XP attribué avec succès!'
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/grades/bulk-bonus', methods=['POST'])
@admin_required
def admin_bulk_bonus_xp():
    """Attribution de bonus XP en masse pour plusieurs utilisateurs"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        user_ids = data.get('user_ids', [])
        xp_amount = data.get('xp_amount')
        reason = data.get('reason')
        
        if not all([user_ids, xp_amount, reason]):
            return jsonify({'success': False, 'error': 'Tous les paramètres sont requis'})
        
        if not isinstance(user_ids, list) or len(user_ids) == 0:
            return jsonify({'success': False, 'error': 'Liste d\'utilisateurs requise'})
        
        if not isinstance(xp_amount, int) or xp_amount <= 0:
            return jsonify({'success': False, 'error': 'Le montant XP doit être un nombre positif'})
        
        success_count = 0
        failed_users = []
        
        for user_id in user_ids:
            try:
                result = add_user_xp_with_notifications(
                    user_id, 
                    'admin_bonus_bulk', 
                    xp_amount, 
                    f"Bonus admin en masse: {reason.strip()}"
                )
                
                if result['success']:
                    success_count += 1
                else:
                    failed_users.append(user_id)
                    
            except Exception as e:
                failed_users.append(user_id)
                print(f"⚠️ Erreur pour l'utilisateur {user_id}: {e}")
        
        # Log administratif
        try:
            import sqlite3
            conn = sqlite3.connect('data/mindtraderpro_users.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action_type, details, created_at)
                VALUES (?, 'bulk_bonus_xp', ?, CURRENT_TIMESTAMP)
            ''', (admin['id'], f"Bonus XP en masse: +{xp_amount} pour {success_count} utilisateurs - {reason}"))
            
            conn.commit()
            conn.close()
        except Exception as log_error:
            print(f"⚠️ Erreur lors du log admin: {log_error}")
        
        return jsonify({
            'success': True,
            'message': f'Bonus attribué à {success_count} utilisateurs',
            'success_count': success_count,
            'failed_count': len(failed_users),
            'failed_users': failed_users
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@admin_bp.route('/admin/logs/xp-bonuses')
@admin_required
def admin_get_xp_bonus_logs():
    """Récupère l'historique des bonus XP attribués par les admins"""
    try:
        import sqlite3
        conn = sqlite3.connect('data/mindtraderpro_users.db')
        cursor = conn.cursor()
        
        # Requête pour récupérer les logs de bonus XP
        cursor.execute('''
            SELECT al.created_at, al.admin_id, al.target_user_id, al.details,
                   ua.username as admin_username, ut.username as target_username
            FROM admin_logs al
            LEFT JOIN users ua ON al.admin_id = ua.id
            LEFT JOIN users ut ON al.target_user_id = ut.id
            WHERE al.action_type IN ('bonus_xp', 'bulk_bonus_xp')
            ORDER BY al.created_at DESC
            LIMIT 100
        ''')
        
        logs = cursor.fetchall()
        conn.close()
        
        bonus_logs = []
        for log in logs:
            bonus_logs.append({
                'date': log[0],
                'admin_id': log[1],
                'target_user_id': log[2],
                'details': log[3],
                'admin_username': log[4] or 'Admin inconnu',
                'target_username': log[5] or 'Utilisateur inconnu'
            })
        
        return jsonify({'success': True, 'logs': bonus_logs})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400