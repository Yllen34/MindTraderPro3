"""
Routes Newsletter & Actus - Interface complète pour la gestion des newsletters
Accessible uniquement aux administrateurs via /admin/newsletter
"""

import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, make_response
from functools import wraps

# Import des modules de newsletter
from modules.newsletter_manager import (
    add_newsletter_subscriber, get_all_subscribers, unsubscribe_email,
    create_newsletter, get_newsletter_by_id, get_all_newsletters, send_newsletter,
    get_newsletter_recipients, get_market_info_template, create_partner_block,
    generate_newsletter_preview, export_subscribers_csv, get_newsletter_statistics
)

# Création du blueprint pour les routes newsletter
newsletter_bp = Blueprint('newsletter', __name__)

# ============================================================================
# DÉCORATEURS DE SÉCURITÉ POUR LA NEWSLETTER
# ============================================================================

def admin_required(f):
    """Décorateur pour s'assurer que seuls les admins peuvent accéder aux routes newsletter"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérification stricte de la connexion utilisateur
        if 'user_id' not in session:
            return redirect('/login?message=Connexion requise pour accéder à la gestion newsletter')
        
        # Vérification stricte du rôle administrateur
        user_role = session.get('role', 'standard')
        if user_role != 'admin':
            return redirect('/login?message=Accès administrateur requis pour gérer les newsletters')
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_admin():
    """Récupère les informations de l'administrateur actuel"""
    if 'user_id' in session and session.get('role') == 'admin':
        return {
            'id': session['user_id'], 
            'username': session.get('username', 'Admin'), 
            'role': 'admin'
        }
    return None

# ============================================================================
# INTERFACE PRINCIPALE DE GESTION DES NEWSLETTERS
# ============================================================================

@newsletter_bp.route('/admin/newsletter')
@admin_required
def newsletter_dashboard():
    """Interface principale de gestion des newsletters"""
    try:
        # Récupération des données pour l'interface
        subscribers = get_all_subscribers()
        newsletters = get_all_newsletters(limit=20)
        stats = get_newsletter_statistics()
        market_template = get_market_info_template()
        
        # Construction de l'interface HTML complète
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Newsletter & Actus - MindTraderPro Admin</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .newsletter-header {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }}
                .newsletter-nav {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .newsletter-nav .nav-link {{
                    color: #495057;
                    font-weight: 500;
                    border-radius: 5px;
                    margin: 0 5px;
                }}
                .newsletter-nav .nav-link.active {{
                    background: #28a745;
                    color: white;
                }}
                .newsletter-section {{
                    display: none;
                }}
                .newsletter-section.active {{
                    display: block;
                }}
                .subscriber-card {{
                    transition: transform 0.3s ease;
                }}
                .subscriber-card:hover {{
                    transform: translateY(-2px);
                }}
                .newsletter-preview {{
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    max-height: 500px;
                    overflow-y: auto;
                }}
                .partner-block {{
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 10px 0;
                    background: #f8f9fa;
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
            <!-- En-tête Newsletter -->
            <div class="newsletter-header">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-envelope me-3"></i>Newsletter & Actualités</h1>
                            <p class="mb-0">Gestion complète des abonnés et création de newsletters</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="/admin" class="btn btn-outline-light">
                                <i class="fas fa-arrow-left me-1"></i>Retour Admin
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container-fluid">
                <!-- Navigation par onglets -->
                <div class="newsletter-nav">
                    <ul class="nav nav-pills">
                        <li class="nav-item">
                            <a class="nav-link active" href="#" onclick="showNewsletterSection('dashboard')">
                                <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="showNewsletterSection('subscribers')">
                                <i class="fas fa-users me-2"></i>Abonnés ({stats.get('total_subscribers', 0)})
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="showNewsletterSection('create')">
                                <i class="fas fa-plus-circle me-2"></i>Créer Newsletter
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="showNewsletterSection('history')">
                                <i class="fas fa-history me-2"></i>Historique ({stats.get('total_newsletters', 0)})
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="showNewsletterSection('templates')">
                                <i class="fas fa-newspaper me-2"></i>Templates Marchés
                            </a>
                        </li>
                    </ul>
                </div>
                
                <!-- Section Dashboard -->
                <div id="dashboard-section" class="newsletter-section active">
                    <h2><i class="fas fa-chart-bar me-2"></i>Vue d'ensemble Newsletter</h2>
                    
                    <!-- Statistiques -->
                    <div class="row g-3 mb-4">
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="fas fa-users fa-2x text-primary mb-2"></i>
                                    <h3>{stats.get('total_subscribers', 0)}</h3>
                                    <small class="text-muted">Abonnés Actifs</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="fas fa-envelope fa-2x text-success mb-2"></i>
                                    <h3>{stats.get('sent_newsletters', 0)}</h3>
                                    <small class="text-muted">Newsletters Envoyées</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="fas fa-edit fa-2x text-warning mb-2"></i>
                                    <h3>{stats.get('draft_newsletters', 0)}</h3>
                                    <small class="text-muted">Brouillons</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="fas fa-crown fa-2x text-info mb-2"></i>
                                    <h3>{stats.get('subscribers_by_type', {}).get('premium', 0) + stats.get('subscribers_by_type', {}).get('lifetime', 0)}</h3>
                                    <small class="text-muted">Abonnés Premium</small>
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
                                        <button class="btn btn-success" onclick="showNewsletterSection('create')">
                                            <i class="fas fa-plus me-2"></i>Créer une Newsletter
                                        </button>
                                        <button class="btn btn-primary" onclick="showNewsletterSection('subscribers')">
                                            <i class="fas fa-users me-2"></i>Gérer les Abonnés
                                        </button>
                                        <button class="btn btn-info" onclick="exportSubscribers()">
                                            <i class="fas fa-download me-2"></i>Export Abonnés CSV
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-chart-pie me-2"></i>Répartition des Abonnés</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row text-center">'''
        
        # Répartition des abonnés par type
        for sub_type, count in stats.get('subscribers_by_type', {}).items():
            type_labels = {
                'manual': 'Inscription Manuelle',
                'registration': 'Inscription Auto',
                'premium': 'Utilisateurs Premium',
                'lifetime': 'Utilisateurs Lifetime'
            }
            
            html_content += f'''
                                        <div class="col-6 mb-2">
                                            <strong>{count}</strong><br>
                                            <small class="text-muted">{type_labels.get(sub_type, sub_type.title())}</small>
                                        </div>'''
        
        html_content += '''
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section Gestion des Abonnés -->
                <div id="subscribers-section" class="newsletter-section">
                    <h2><i class="fas fa-users me-2"></i>Gestion des Abonnés</h2>
                    
                    <!-- Formulaire d'ajout manuel d'abonné -->
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-user-plus me-2"></i>Ajouter un Abonné</h5>
                        </div>
                        <div class="card-body">
                            <form id="addSubscriberForm" class="row g-3">
                                <div class="col-md-8">
                                    <input type="email" class="form-control" id="subscriberEmail" placeholder="email@exemple.com" required>
                                </div>
                                <div class="col-md-4">
                                    <button type="submit" class="btn btn-success w-100">
                                        <i class="fas fa-plus me-2"></i>Ajouter
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                    
                    <!-- Liste des abonnés -->
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5>Liste des Abonnés</h5>
                            <div>
                                <select class="form-select form-select-sm" id="filterSubscribers" onchange="filterSubscribersList()">
                                    <option value="all">Tous les abonnés</option>
                                    <option value="manual">Inscription manuelle</option>
                                    <option value="premium">Utilisateurs Premium</option>
                                    <option value="lifetime">Utilisateurs Lifetime</option>
                                </select>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped" id="subscribersTable">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Email</th>
                                            <th>Utilisateur</th>
                                            <th>Type</th>
                                            <th>Date d'inscription</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="subscribersTableBody">'''
        
        # Génération du tableau des abonnés
        for subscriber in subscribers[:50]:  # Limitation à 50 pour la performance
            user_badge = 'bg-success' if subscriber['user_role'] in ['premium', 'lifetime'] else 'bg-secondary'
            type_badge = {
                'manual': 'bg-info',
                'registration': 'bg-primary', 
                'premium': 'bg-success',
                'lifetime': 'bg-warning'
            }.get(subscriber['subscription_type'], 'bg-secondary')
            
            html_content += f'''
                                        <tr data-subscriber-type="{subscriber['subscription_type']}">
                                            <td><strong>{subscriber['email']}</strong></td>
                                            <td>
                                                {subscriber['username']}
                                                <br><span class="badge {user_badge}">{subscriber['user_role'].upper()}</span>
                                            </td>
                                            <td><span class="badge {type_badge}">{subscriber['subscription_type'].upper()}</span></td>
                                            <td>{subscriber['subscribed_at'][:10] if subscriber['subscribed_at'] else 'N/A'}</td>
                                            <td>
                                                <button class="btn btn-danger btn-sm" onclick="unsubscribeEmail('{subscriber['email']}')">
                                                    <i class="fas fa-user-times"></i> Désabonner
                                                </button>
                                            </td>
                                        </tr>'''
        
        if not subscribers:
            html_content += '''
                                        <tr>
                                            <td colspan="5" class="text-center py-4">
                                                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                                                <h5 class="text-muted">Aucun abonné</h5>
                                                <p class="text-muted">Les premiers abonnés apparaîtront ici.</p>
                                            </td>
                                        </tr>'''
        
        html_content += '''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section Création de Newsletter -->
                <div id="create-section" class="newsletter-section">
                    <h2><i class="fas fa-plus-circle me-2"></i>Créer une Newsletter</h2>
                    
                    <div class="row">
                        <div class="col-lg-8">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-edit me-2"></i>Éditeur de Newsletter</h5>
                                </div>
                                <div class="card-body">
                                    <form id="createNewsletterForm">
                                        <!-- Informations de base -->
                                        <div class="mb-3">
                                            <label class="form-label">Titre de la Newsletter <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="newsletterTitle" required placeholder="Ex: Actualités Trading - Semaine du 24 Mai">
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Public Cible <span class="text-danger">*</span></label>
                                            <select class="form-select" id="targetAudience" required>
                                                <option value="">Sélectionner le public</option>
                                                <option value="all">Tous les abonnés</option>
                                                <option value="premium">Utilisateurs Premium uniquement</option>
                                                <option value="lifetime">Utilisateurs Lifetime uniquement</option>
                                                <option value="manual">Abonnés manuels uniquement</option>
                                            </select>
                                        </div>
                                        
                                        <!-- Contenu principal -->
                                        <div class="mb-3">
                                            <label class="form-label">Contenu Principal <span class="text-danger">*</span></label>
                                            <textarea class="form-control" id="newsletterContent" rows="6" required 
                                                placeholder="Écrivez le contenu principal de votre newsletter..."></textarea>
                                        </div>
                                        
                                        <!-- Section Marchés -->
                                        <div class="mb-3">
                                            <label class="form-label">Informations Marchés <small class="text-muted">(optionnel)</small></label>
                                            <textarea class="form-control" id="marketInfo" rows="4" 
                                                placeholder="Analyses des marchés, crypto, forex pour cette semaine..."></textarea>
                                        </div>
                                        
                                        <!-- Blocs Partenaires -->
                                        <div class="mb-3">
                                            <label class="form-label">Offres Partenaires <small class="text-muted">(optionnel)</small></label>
                                            <div id="partnerBlocks">
                                                <!-- Les blocs partenaires seront ajoutés ici dynamiquement -->
                                            </div>
                                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="addPartnerBlock()">
                                                <i class="fas fa-plus me-1"></i>Ajouter une Offre Partenaire
                                            </button>
                                        </div>
                                        
                                        <!-- Actions -->
                                        <div class="d-flex gap-2">
                                            <button type="button" class="btn btn-info" onclick="previewNewsletter()">
                                                <i class="fas fa-eye me-2"></i>Prévisualiser
                                            </button>
                                            <button type="submit" class="btn btn-success">
                                                <i class="fas fa-save me-2"></i>Créer en Brouillon
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-lg-4">
                            <!-- Aide et conseils -->
                            <div class="card">
                                <div class="card-header">
                                    <h6><i class="fas fa-lightbulb me-2"></i>Conseils de Rédaction</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Titre accrocheur et spécifique</li>
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Contenu concis et actionnable</li>
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Informations marchés actualisées</li>
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Maximum 2-3 offres partenaires</li>
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Call-to-action clair</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <!-- Aperçu destinataires -->
                            <div class="card mt-3">
                                <div class="card-header">
                                    <h6><i class="fas fa-users me-2"></i>Aperçu Destinataires</h6>
                                </div>
                                <div class="card-body">
                                    <div id="recipientsPreview">
                                        <p class="text-muted">Sélectionnez un public cible pour voir le nombre de destinataires.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section Historique -->
                <div id="history-section" class="newsletter-section">
                    <h2><i class="fas fa-history me-2"></i>Historique des Newsletters</h2>
                    
                    <div class="card">
                        <div class="card-header">
                            <h5>Newsletters Créées</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Titre</th>
                                            <th>Public Cible</th>
                                            <th>Statut</th>
                                            <th>Créée le</th>
                                            <th>Envoyée le</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>'''
        
        # Génération de l'historique des newsletters
        for newsletter in newsletters:
            status_badge = {
                'draft': 'badge bg-warning',
                'sent': 'badge bg-success',
                'scheduled': 'badge bg-info'
            }.get(newsletter['status'], 'badge bg-secondary')
            
            audience_labels = {
                'all': 'Tous',
                'premium': 'Premium',
                'lifetime': 'Lifetime', 
                'manual': 'Manuels'
            }
            
            html_content += f'''
                                        <tr>
                                            <td><strong>{newsletter['title']}</strong></td>
                                            <td>{audience_labels.get(newsletter['target_audience'], newsletter['target_audience'])}</td>
                                            <td><span class="{status_badge}">{newsletter['status'].upper()}</span></td>
                                            <td>{newsletter['created_at'][:10] if newsletter['created_at'] else 'N/A'}</td>
                                            <td>{newsletter['sent_at'][:10] if newsletter['sent_at'] else '-'}</td>
                                            <td>
                                                <div class="btn-group btn-group-sm">
                                                    <button class="btn btn-info" onclick="previewNewsletterById({newsletter['id']})">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                    {'<button class="btn btn-success" onclick="sendNewsletterById(' + str(newsletter['id']) + ')"><i class="fas fa-paper-plane"></i></button>' if newsletter['status'] == 'draft' else ''}
                                                </div>
                                            </td>
                                        </tr>'''
        
        if not newsletters:
            html_content += '''
                                        <tr>
                                            <td colspan="6" class="text-center py-4">
                                                <i class="fas fa-newspaper fa-3x text-muted mb-3"></i>
                                                <h5 class="text-muted">Aucune newsletter</h5>
                                                <p class="text-muted">Créez votre première newsletter pour commencer.</p>
                                            </td>
                                        </tr>'''
        
        html_content += '''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section Templates Marchés -->
                <div id="templates-section" class="newsletter-section">
                    <h2><i class="fas fa-newspaper me-2"></i>Templates Marchés & Actualités</h2>
                    
                    <div class="row">'''
        
        # Génération des templates de marchés
        for section_key, section_data in market_template.items():
            html_content += f'''
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-header">
                                    <h6>{section_data['title']}</h6>
                                </div>
                                <div class="card-body">
                                    <p class="text-muted">{section_data['content']}</p>
                                    <button class="btn btn-outline-primary btn-sm" onclick="useTemplate('{section_key}')">
                                        <i class="fas fa-copy me-1"></i>Utiliser ce Template
                                    </button>
                                </div>
                            </div>
                        </div>'''
        
        html_content += '''
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle me-2"></i>Guide des Templates</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>📈 Section Forex</h6>
                                    <p>Analysez les principales paires EUR/USD, GBP/USD, USD/JPY avec les événements de la semaine qui impactent les devises.</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>₿ Section Crypto</h6>
                                    <p>Couvrez Bitcoin, Ethereum et les altcoins majeurs avec les news réglementaires et adoptions institutionnelles.</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>🥇 Matières Premières</h6>
                                    <p>Or, argent, pétrole, et leur relation avec l'inflation et les tensions géopolitiques.</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>📅 Calendrier Économique</h6>
                                    <p>Événements clés: NFP, inflation, décisions banques centrales, PIB des pays majeurs.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <!-- Modal de prévisualisation -->
            <div class="modal fade" id="previewModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Aperçu de la Newsletter</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="newsletterPreviewContent" class="newsletter-preview">
                                <!-- Le contenu de prévisualisation sera inséré ici -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                            <button type="button" class="btn btn-success" onclick="sendCurrentNewsletter()">
                                <i class="fas fa-paper-plane me-2"></i>Envoyer Maintenant
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // ============================================================================
                // JAVASCRIPT POUR LA GESTION DES NEWSLETTERS
                // ============================================================================
                
                let currentNewsletterId = null;
                
                // Navigation entre les sections
                function showNewsletterSection(sectionName) {{
                    // Masquer toutes les sections
                    document.querySelectorAll('.newsletter-section').forEach(section => {{
                        section.classList.remove('active');
                    }});
                    
                    // Retirer la classe active de tous les liens
                    document.querySelectorAll('.newsletter-nav .nav-link').forEach(link => {{
                        link.classList.remove('active');
                    }});
                    
                    // Afficher la section demandée
                    document.getElementById(sectionName + '-section').classList.add('active');
                    
                    // Activer le lien correspondant
                    event.target.classList.add('active');
                }}
                
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
                
                // ============================================================================
                // GESTION DES ABONNÉS
                // ============================================================================
                
                // Ajout d'un abonné
                document.getElementById('addSubscriberForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const email = document.getElementById('subscriberEmail').value;
                    
                    try {{
                        const response = await fetch('/admin/newsletter/add-subscriber', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ email: email }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            document.getElementById('subscriberEmail').value = '';
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }});
                
                // Désabonnement d'un email
                async function unsubscribeEmail(email) {{
                    if (confirm(`Désabonner ${{email}} de la newsletter ?`)) {{
                        try {{
                            const response = await fetch('/admin/newsletter/unsubscribe', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ email: email }})
                            }});
                            
                            const result = await response.json();
                            
                            if (result.success) {{
                                showNotification('✅ ' + result.message, 'success');
                                setTimeout(() => {{ window.location.reload(); }}, 2000);
                            }} else {{
                                showNotification('❌ ' + result.error, 'error');
                            }}
                        }} catch (error) {{
                            showNotification('❌ Erreur de connexion', 'error');
                        }}
                    }}
                }}
                
                // Filtrage des abonnés
                function filterSubscribersList() {{
                    const filterValue = document.getElementById('filterSubscribers').value;
                    const rows = document.querySelectorAll('#subscribersTableBody tr');
                    
                    rows.forEach(row => {{
                        if (filterValue === 'all') {{
                            row.style.display = '';
                        }} else {{
                            const subscriberType = row.getAttribute('data-subscriber-type');
                            row.style.display = subscriberType === filterValue ? '' : 'none';
                        }}
                    }});
                }}
                
                // Export CSV des abonnés
                function exportSubscribers() {{
                    window.location.href = '/admin/newsletter/export-subscribers';
                }}
                
                // ============================================================================
                // CRÉATION DE NEWSLETTERS
                // ============================================================================
                
                // Soumission du formulaire de création
                document.getElementById('createNewsletterForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const formData = {{
                        title: document.getElementById('newsletterTitle').value,
                        content: document.getElementById('newsletterContent').value,
                        target_audience: document.getElementById('targetAudience').value,
                        market_info: document.getElementById('marketInfo').value,
                        partner_blocks: collectPartnerBlocks()
                    }};
                    
                    try {{
                        const response = await fetch('/admin/newsletter/create', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(formData)
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showNotification('✅ ' + result.message, 'success');
                            document.getElementById('createNewsletterForm').reset();
                            currentNewsletterId = result.newsletter_id;
                        }} else {{
                            showNotification('❌ ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }});
                
                // Aperçu du nombre de destinataires
                document.getElementById('targetAudience').addEventListener('change', async function() {{
                    const audience = this.value;
                    if (audience) {{
                        try {{
                            const response = await fetch(`/admin/newsletter/recipients-count?audience=${{audience}}`);
                            const result = await response.json();
                            
                            document.getElementById('recipientsPreview').innerHTML = `
                                <div class="alert alert-info">
                                    <i class="fas fa-users me-2"></i>
                                    <strong>${{result.count}} destinataires</strong> recevront cette newsletter
                                </div>
                            `;
                        }} catch (error) {{
                            console.error('Erreur:', error);
                        }}
                    }}
                }});
                
                // Prévisualisation de la newsletter
                async function previewNewsletter() {{
                    const formData = {{
                        title: document.getElementById('newsletterTitle').value,
                        content: document.getElementById('newsletterContent').value,
                        target_audience: document.getElementById('targetAudience').value,
                        market_info: document.getElementById('marketInfo').value,
                        partner_blocks: collectPartnerBlocks()
                    }};
                    
                    if (!formData.title || !formData.content) {{
                        showNotification('❌ Titre et contenu requis pour la prévisualisation', 'error');
                        return;
                    }}
                    
                    try {{
                        const response = await fetch('/admin/newsletter/preview', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(formData)
                        }});
                        
                        const html = await response.text();
                        document.getElementById('newsletterPreviewContent').innerHTML = html;
                        new bootstrap.Modal(document.getElementById('previewModal')).show();
                    }} catch (error) {{
                        showNotification('❌ Erreur lors de la prévisualisation', 'error');
                    }}
                }}
                
                // Prévisualisation d'une newsletter existante
                async function previewNewsletterById(newsletterId) {{
                    try {{
                        const response = await fetch(`/admin/newsletter/preview/${{newsletterId}}`);
                        const html = await response.text();
                        document.getElementById('newsletterPreviewContent').innerHTML = html;
                        currentNewsletterId = newsletterId;
                        new bootstrap.Modal(document.getElementById('previewModal')).show();
                    }} catch (error) {{
                        showNotification('❌ Erreur lors de la prévisualisation', 'error');
                    }}
                }}
                
                // Envoi d'une newsletter
                async function sendNewsletterById(newsletterId) {{
                    if (confirm('Envoyer cette newsletter maintenant ? Cette action est irréversible.')) {{
                        try {{
                            const response = await fetch('/admin/newsletter/send', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ newsletter_id: newsletterId }})
                            }});
                            
                            const result = await response.json();
                            
                            if (result.success) {{
                                showNotification('✅ ' + result.message, 'success');
                                setTimeout(() => {{ window.location.reload(); }}, 3000);
                            }} else {{
                                showNotification('❌ ' + result.error, 'error');
                            }}
                        }} catch (error) {{
                            showNotification('❌ Erreur lors de l\'envoi', 'error');
                        }}
                    }}
                }}
                
                // Envoi de la newsletter courante depuis la prévisualisation
                function sendCurrentNewsletter() {{
                    if (currentNewsletterId) {{
                        sendNewsletterById(currentNewsletterId);
                        bootstrap.Modal.getInstance(document.getElementById('previewModal')).hide();
                    }}
                }}
                
                // ============================================================================
                // GESTION DES BLOCS PARTENAIRES
                // ============================================================================
                
                let partnerBlockCount = 0;
                
                function addPartnerBlock() {{
                    partnerBlockCount++;
                    const blockHtml = `
                        <div class="partner-block" id="partnerBlock${{partnerBlockCount}}">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6>Offre Partenaire #${{partnerBlockCount}}</h6>
                                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removePartnerBlock(${{partnerBlockCount}})">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <input type="text" class="form-control form-control-sm" placeholder="Titre de l'offre" data-field="title">
                                </div>
                                <div class="col-md-6 mb-2">
                                    <input type="url" class="form-control form-control-sm" placeholder="Lien d'affiliation" data-field="link">
                                </div>
                                <div class="col-md-8 mb-2">
                                    <textarea class="form-control form-control-sm" placeholder="Description de l'offre" rows="2" data-field="description"></textarea>
                                </div>
                                <div class="col-md-4 mb-2">
                                    <input type="text" class="form-control form-control-sm" placeholder="Code promo" data-field="discount_code">
                                    <div class="form-check mt-1">
                                        <input class="form-check-input" type="checkbox" data-field="is_featured">
                                        <label class="form-check-label">Offre vedette</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('partnerBlocks').insertAdjacentHTML('beforeend', blockHtml);
                }}
                
                function removePartnerBlock(blockId) {{
                    document.getElementById(`partnerBlock${{blockId}}`).remove();
                }}
                
                function collectPartnerBlocks() {{
                    const blocks = [];
                    document.querySelectorAll('.partner-block').forEach(block => {{
                        const blockData = {{}};
                        block.querySelectorAll('[data-field]').forEach(field => {{
                            const fieldName = field.getAttribute('data-field');
                            if (field.type === 'checkbox') {{
                                blockData[fieldName] = field.checked;
                            }} else {{
                                blockData[fieldName] = field.value;
                            }}
                        }});
                        
                        if (blockData.title && blockData.description) {{
                            blocks.push(blockData);
                        }}
                    }});
                    return blocks;
                }}
                
                // ============================================================================
                // TEMPLATES DE MARCHÉS
                // ============================================================================
                
                function useTemplate(templateKey) {{
                    const templates = {json.dumps(market_template)};
                    const template = templates[templateKey];
                    
                    if (template) {{
                        const currentContent = document.getElementById('marketInfo').value;
                        const newlineChars = '\\n\\n';
                        const colonChar = ':\\n';
                        const newContent = currentContent ? 
                            currentContent + newlineChars + template.title + colonChar + template.content :
                            template.title + colonChar + template.content;
                        
                        document.getElementById('marketInfo').value = newContent;
                        showNotification('✅ Template "' + template.title + '" ajouté', 'success');
                    }}
                }}
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement de l'interface newsletter: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES ACTIONS NEWSLETTER
# ============================================================================

@newsletter_bp.route('/admin/newsletter/add-subscriber', methods=['POST'])
@admin_required
def api_add_subscriber():
    """API pour ajouter un abonné manuellement"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email requis'})
        
        result = add_newsletter_subscriber(email, subscription_type='manual')
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@newsletter_bp.route('/admin/newsletter/unsubscribe', methods=['POST'])
@admin_required
def api_unsubscribe():
    """API pour désabonner un email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email requis'})
        
        result = unsubscribe_email(email)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@newsletter_bp.route('/admin/newsletter/create', methods=['POST'])
@admin_required
def api_create_newsletter():
    """API pour créer une nouvelle newsletter"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        title = data.get('title')
        content = data.get('content')
        target_audience = data.get('target_audience')
        market_info = data.get('market_info')
        partner_blocks = data.get('partner_blocks', [])
        
        if not all([title, content, target_audience]):
            return jsonify({'success': False, 'error': 'Titre, contenu et audience requis'})
        
        result = create_newsletter(title, content, target_audience, market_info, partner_blocks, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@newsletter_bp.route('/admin/newsletter/send', methods=['POST'])
@admin_required
def api_send_newsletter():
    """API pour envoyer une newsletter"""
    try:
        admin = get_current_admin()
        data = request.get_json()
        
        newsletter_id = data.get('newsletter_id')
        
        if not newsletter_id:
            return jsonify({'success': False, 'error': 'ID newsletter requis'})
        
        result = send_newsletter(newsletter_id, admin['id'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@newsletter_bp.route('/admin/newsletter/preview', methods=['POST'])
@admin_required
def api_preview_newsletter():
    """API pour générer une prévisualisation de newsletter"""
    try:
        data = request.get_json()
        
        # Création temporaire pour prévisualisation
        temp_newsletter = {
            'title': data.get('title'),
            'content': data.get('content'),
            'market_info': data.get('market_info'),
            'partner_blocks': data.get('partner_blocks', [])
        }
        
        # Génération du HTML de prévisualisation directement
        from modules.newsletter_manager import generate_market_section_html, generate_partner_blocks_html
        
        # Génération du contenu de prévisualisation
        title = temp_newsletter.get('title', '')
        content = temp_newsletter.get('content', '').replace('\n', '<br>') if temp_newsletter.get('content') else ''
        market_section = generate_market_section_html(temp_newsletter.get('market_info', ''))
        partner_section = generate_partner_blocks_html(temp_newsletter.get('partner_blocks', []))
        
        html_preview = f'''
        <div style="font-family: Arial, sans-serif;">
            <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
                <h1>📈 MindTraderPro Newsletter</h1>
                <h2>{title}</h2>
            </div>
            
            <div style="padding: 20px;">
                <p>{content}</p>
                
                {market_section}
                
                {partner_section}
            </div>
            
            <div style="background: #343a40; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p>📧 Vous recevez cet email car vous êtes abonné à la newsletter MindTraderPro</p>
            </div>
        </div>
        '''
        
        return html_preview
        
    except Exception as e:
        return f"<p>Erreur lors de la prévisualisation: {str(e)}</p>"

@newsletter_bp.route('/admin/newsletter/preview/<int:newsletter_id>')
@admin_required
def api_preview_newsletter_by_id(newsletter_id):
    """API pour prévisualiser une newsletter existante"""
    try:
        html_preview = generate_newsletter_preview(newsletter_id)
        return html_preview
        
    except Exception as e:
        return f"<p>Erreur lors de la prévisualisation: {str(e)}</p>"

@newsletter_bp.route('/admin/newsletter/recipients-count')
@admin_required
def api_recipients_count():
    """API pour obtenir le nombre de destinataires selon l'audience"""
    try:
        audience = request.args.get('audience')
        recipients = get_newsletter_recipients(audience)
        
        return jsonify({'count': len(recipients)})
        
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)}), 400

@newsletter_bp.route('/admin/newsletter/export-subscribers')
@admin_required
def api_export_subscribers():
    """API pour exporter les abonnés en CSV"""
    try:
        csv_content = export_subscribers_csv()
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=newsletter_subscribers.csv'
        
        return response
        
    except Exception as e:
        return f"Erreur lors de l'export: {str(e)}", 400

# ============================================================================
# ROUTE PUBLIQUE POUR L'ABONNEMENT
# ============================================================================

@newsletter_bp.route('/newsletter/subscribe', methods=['POST'])
def public_subscribe():
    """Route publique pour l'abonnement à la newsletter"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email requis'})
        
        # Vérification si l'utilisateur est connecté
        user_id = session.get('user_id')
        subscription_type = 'registration' if user_id else 'manual'
        
        result = add_newsletter_subscriber(email, user_id, subscription_type)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400