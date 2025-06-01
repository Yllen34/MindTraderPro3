"""
Routes Journal de Trading - Module séparé pour toutes les routes du journal
Architecture modulaire pour une meilleure organisation du code
"""

import os
import csv
import io
from flask import Blueprint, request, jsonify, session, redirect, url_for, make_response
from functools import wraps

# Import des modules internes
from modules.journal_manager import (
    add_trade_to_journal, update_trade_result, update_trade_details, delete_trade,
    get_user_trades, get_single_trade, get_trading_statistics, save_audio_note, get_available_assets
)

# Création du blueprint pour les routes du journal
journal_bp = Blueprint('journal', __name__)

# ============================================================================
# DÉCORATEURS POUR LA SÉCURITÉ ET LES PERMISSIONS
# ============================================================================

def get_user_by_id(user_id):
    """Fonction helper pour récupérer un utilisateur (doit être importée depuis l'app principale)"""
    # Cette fonction sera définie dans l'app principale et passée au blueprint
    pass

def login_required(f):
    """Décorateur pour s'assurer que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Connexion requise'}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles):
    """Décorateur pour vérifier les rôles utilisateur (Premium/Lifetime uniquement)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Connexion requise'}), 401
            
            # Cette vérification sera adaptée selon l'implémentation de get_user_by_id
            user_id = session['user_id']
            # user = get_user_by_id(user_id)
            # if not user or user['role'] not in required_roles:
            #     return jsonify({'success': False, 'error': 'Accès non autorisé - Upgrade requis'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ROUTES PRINCIPALES DU JOURNAL
# ============================================================================

@journal_bp.route('/journal')
@login_required
def journal_page():
    """Page principale du journal de trading avec interface complète"""
    try:
        # Récupération de l'ID utilisateur depuis la session
        user_id = session['user_id']
        
        # Récupération des données pour la page
        trades = get_user_trades(user_id, limit=20)
        stats = get_trading_statistics(user_id)
        assets = get_available_assets()
        
        # Préparation des données pour les graphiques
        wins = [t for t in trades if t['status'] == 'closed' and t['result_pnl'] and t['result_pnl'] > 0]
        losses = [t for t in trades if t['status'] == 'closed' and t['result_pnl'] and t['result_pnl'] < 0]
        
        # Construction du HTML complet avec toutes les fonctionnalités
        html_content = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Journal de Trading - MindTraderPro</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                .win-row {{ background-color: rgba(40, 167, 69, 0.1) !important; }}
                .loss-row {{ background-color: rgba(220, 53, 69, 0.1) !important; }}
                .trade-icon-buy {{ color: #28a745; }}
                .trade-icon-sell {{ color: #dc3545; }}
                .audio-player {{ max-width: 200px; }}
                .notification {{ position: fixed; top: 20px; right: 20px; z-index: 1050; }}
                .stats-card {{ transition: transform 0.3s ease; }}
                .stats-card:hover {{ transform: translateY(-5px); }}
                .filter-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <!-- Notifications -->
            <div id="notification-area"></div>
            
            <div class="container-fluid mt-4">
                <!-- En-tête -->
                <div class="row mb-4">
                    <div class="col-12">
                        <h1 class="display-6 fw-bold">
                            <i class="fas fa-book text-success me-3"></i>Journal de Trading
                        </h1>
                        <p class="lead text-muted">Gestion complète de vos trades et performances</p>
                    </div>
                </div>
                
                <!-- Statistiques -->
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white stats-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-chart-line fa-2x mb-2"></i>
                                <h3>{stats.get('total_trades', 0)}</h3>
                                <small>Trades Total</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white stats-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-percentage fa-2x mb-2"></i>
                                <h3>{stats.get('winrate', 0)}%</h3>
                                <small>Taux de Réussite</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white stats-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-dollar-sign fa-2x mb-2"></i>
                                <h3>${stats.get('total_pnl', 0)}</h3>
                                <small>P&L Total</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-dark stats-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-trending-down fa-2x mb-2"></i>
                                <h3>${stats.get('max_drawdown', 0)}</h3>
                                <small>Drawdown Max</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Filtres et recherche -->
                <div class="filter-section">
                    <div class="row align-items-end">
                        <div class="col-md-2">
                            <label class="form-label">Actif</label>
                            <select class="form-select" id="filterAsset">
                                <option value="">Tous les actifs</option>'''
        
        # Ajout des options d'actifs
        for asset in assets:
            html_content += f'<option value="{asset["symbol"]}">{asset["name"]}</option>'
        
        html_content += '''
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Type</label>
                            <select class="form-select" id="filterType">
                                <option value="">Tous types</option>
                                <option value="buy">Achat</option>
                                <option value="sell">Vente</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Résultat</label>
                            <select class="form-select" id="filterResult">
                                <option value="">Tous</option>
                                <option value="win">Gagnants</option>
                                <option value="loss">Perdants</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Date début</label>
                            <input type="date" class="form-control" id="filterDateFrom">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Date fin</label>
                            <input type="date" class="form-control" id="filterDateTo">
                        </div>
                        <div class="col-md-2">
                            <div class="d-grid gap-2">
                                <button class="btn btn-primary" onclick="applyFilters()">
                                    <i class="fas fa-filter me-1"></i>Filtrer
                                </button>
                                <button class="btn btn-outline-secondary" onclick="resetFilters()">
                                    <i class="fas fa-undo me-1"></i>Reset
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Formulaire d'ajout -->
                <div class="row mb-4">
                    <div class="col-lg-8">
                        <div class="card">
                            <div class="card-header">
                                <h4><i class="fas fa-plus-circle me-2"></i>Ajouter un Nouveau Trade</h4>
                            </div>
                            <div class="card-body">
                                <form id="addTradeForm">
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Actif <span class="text-danger">*</span></label>
                                            <select class="form-select" id="asset" required>
                                                <option value="">Sélectionner un actif</option>'''
        
        # Options d'actifs pour le formulaire
        for asset in assets:
            html_content += f'<option value="{asset["symbol"]}">{asset["name"]}</option>'
        
        html_content += '''
                                            </select>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Type <span class="text-danger">*</span></label>
                                            <select class="form-select" id="trade_type" required>
                                                <option value="">Sélectionner</option>
                                                <option value="buy">Achat (Buy)</option>
                                                <option value="sell">Vente (Sell)</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Date & Heure <span class="text-danger">*</span></label>
                                            <input type="datetime-local" class="form-control" id="trade_date" required>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Taille de lot <span class="text-danger">*</span></label>
                                            <input type="number" class="form-control" id="lot_size" step="0.01" min="0.01" required>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-4 mb-3">
                                            <label class="form-label">Prix d'entrée <span class="text-danger">*</span></label>
                                            <input type="number" class="form-control" id="entry_price" step="0.00001" required>
                                        </div>
                                        <div class="col-md-4 mb-3">
                                            <label class="form-label">Stop Loss</label>
                                            <input type="number" class="form-control" id="stop_loss" step="0.00001">
                                        </div>
                                        <div class="col-md-4 mb-3">
                                            <label class="form-label">Take Profit</label>
                                            <input type="number" class="form-control" id="take_profit" step="0.00001">
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Style de Trading</label>
                                            <select class="form-select" id="trading_style">
                                                <option value="">Sélectionner un style</option>
                                                <option value="scalping">Scalping</option>
                                                <option value="day_trading">Day Trading</option>
                                                <option value="swing">Swing Trading</option>
                                                <option value="position">Position Trading</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">État Émotionnel</label>
                                            <select class="form-select" id="emotions">
                                                <option value="">Sélectionner une émotion</option>
                                                <option value="confident">Confiant</option>
                                                <option value="nervous">Nerveux</option>
                                                <option value="greedy">Cupide</option>
                                                <option value="fearful">Craintif</option>
                                                <option value="calm">Calme</option>
                                                <option value="frustrated">Frustré</option>
                                                <option value="excited">Excité</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Notes</label>
                                        <textarea class="form-control" id="notes" rows="3" placeholder="Décrivez votre analyse, votre stratégie ou vos observations..." maxlength="1000"></textarea>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Note Vocale (Audio)</label>
                                        <input type="file" class="form-control" id="audio_note" accept="audio/*">
                                        <small class="text-muted">Formats acceptés: MP3, WAV, M4A (max 10MB)</small>
                                    </div>
                                    
                                    <div class="d-grid">
                                        <button type="submit" class="btn btn-success btn-lg">
                                            <i class="fas fa-save me-2"></i>Enregistrer le Trade
                                        </button>
                                    </div>
                                </form>
                                
                                <div id="addTradeResult" class="mt-3" style="display: none;"></div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Statistiques détaillées -->
                    <div class="col-lg-4">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-bar me-2"></i>Statistiques Détaillées</h5>
                            </div>
                            <div class="card-body">
                                <div class="row text-center mb-3">
                                    <div class="col-6">
                                        <h6 class="text-success">Trades Gagnants</h6>
                                        <h4 class="text-success">{stats.get('winning_trades', 0)}</h4>
                                    </div>
                                    <div class="col-6">
                                        <h6 class="text-danger">Trades Perdants</h6>
                                        <h4 class="text-danger">{stats.get('losing_trades', 0)}</h4>
                                    </div>
                                </div>
                                
                                <hr>
                                
                                <div class="mb-2">
                                    <small class="text-muted">Gain Moyen:</small>
                                    <span class="float-end text-success">${stats.get('average_win', 0)}</span>
                                </div>
                                <div class="mb-2">
                                    <small class="text-muted">Perte Moyenne:</small>
                                    <span class="float-end text-danger">${stats.get('average_loss', 0)}</span>
                                </div>
                                <div class="mb-2">
                                    <small class="text-muted">Facteur de Profit:</small>
                                    <span class="float-end fw-bold">{stats.get('profit_factor', 0)}</span>
                                </div>
                                <div class="mb-2">
                                    <small class="text-muted">Meilleur Trade:</small>
                                    <span class="float-end text-success">${stats.get('best_trade', 0)}</span>
                                </div>
                                <div class="mb-2">
                                    <small class="text-muted">Pire Trade:</small>
                                    <span class="float-end text-danger">${stats.get('worst_trade', 0)}</span>
                                </div>
                                
                                <hr>
                                
                                <div class="d-grid gap-2">
                                    <button class="btn btn-outline-primary" onclick="exportTrades()">
                                        <i class="fas fa-download me-2"></i>Export CSV
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Graphique -->
                        <div class="card mt-3">
                            <div class="card-header">
                                <h6><i class="fas fa-chart-pie me-2"></i>Répartition Win/Loss</h6>
                            </div>
                            <div class="card-body">
                                <canvas id="winLossChart" width="300" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Historique des trades -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h4><i class="fas fa-history me-2"></i>Historique des Trades</h4>
                                <input type="text" class="form-control" id="searchTrades" placeholder="Rechercher..." style="width: 300px;">
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover" id="tradesTable">
                                        <thead class="table-dark">
                                            <tr>
                                                <th>Actif</th>
                                                <th>Type</th>
                                                <th>Date</th>
                                                <th>Entrée</th>
                                                <th>Sortie</th>
                                                <th>Lot</th>
                                                <th>P&L</th>
                                                <th>Pips</th>
                                                <th>Style</th>
                                                <th>Émotion</th>
                                                <th>Audio</th>
                                                <th>Statut</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="tradesTableBody">'''
        
        # Génération des lignes du tableau avec coloration conditionnelle
        for trade in trades:
            # Détermination de la classe CSS pour la couleur de ligne
            row_class = ''
            if trade['result_pnl']:
                row_class = 'win-row' if trade['result_pnl'] > 0 else 'loss-row'
            
            # Icône selon le type de trade
            trade_icon = f'<i class="fas fa-arrow-up trade-icon-buy" title="Achat"></i>' if trade['trade_type'] == 'buy' else f'<i class="fas fa-arrow-down trade-icon-sell" title="Vente"></i>'
            
            # Badge de statut
            status_badges = {
                'open': 'badge bg-primary',
                'closed': 'badge bg-success',
                'cancelled': 'badge bg-secondary'
            }
            status_badge = status_badges.get(trade['status'], 'badge bg-secondary')
            
            # Couleur du P&L
            pnl_class = ''
            if trade['result_pnl']:
                pnl_class = 'text-success fw-bold' if trade['result_pnl'] > 0 else 'text-danger fw-bold'
            
            # Icône émotionnelle
            emotion_icons = {
                'confident': 'fas fa-smile text-success',
                'nervous': 'fas fa-grimace text-warning',
                'greedy': 'fas fa-dollar-sign text-warning',
                'fearful': 'fas fa-frown text-danger',
                'calm': 'fas fa-zen text-info',
                'frustrated': 'fas fa-angry text-danger',
                'excited': 'fas fa-grin-stars text-success'
            }
            emotion_icon = emotion_icons.get(trade['emotions'], 'fas fa-meh text-muted')
            
            # Lecteur audio intégré si disponible
            audio_player = ''
            if trade['audio_note_path']:
                audio_player = f'''
                    <audio controls class="audio-player">
                        <source src="/static/audio/{trade['audio_note_path']}" type="audio/mpeg">
                        Non supporté
                    </audio>
                '''
            else:
                audio_player = '<span class="text-muted">-</span>'
            
            html_content += f'''
                                            <tr class="{row_class}" data-trade-id="{trade['id']}">
                                                <td><strong>{trade['asset']}</strong></td>
                                                <td>{trade_icon} {trade['trade_type'].upper()}</td>
                                                <td>{trade['trade_date'][:16] if trade['trade_date'] else 'N/A'}</td>
                                                <td>{trade['entry_price']}</td>
                                                <td>{trade['exit_price'] or '-'}</td>
                                                <td>{trade['lot_size']}</td>
                                                <td class="{pnl_class}">${trade['result_pnl'] or 0}</td>
                                                <td class="{pnl_class}">{trade['result_pips'] or 0}</td>
                                                <td>{trade['trading_style'] or '-'}</td>
                                                <td><i class="{emotion_icon}" title="{trade['emotions'] or 'N/A'}"></i></td>
                                                <td>{audio_player}</td>
                                                <td><span class="{status_badge}">{trade['status'].upper()}</span></td>
                                                <td>
                                                    <div class="btn-group btn-group-sm">'''
            
            # Boutons d'action conditionnels
            if trade['status'] == 'open':
                html_content += f'''
                                                        <button class="btn btn-warning btn-sm" onclick="closeTradeModal({trade['id']})" title="Clôturer">
                                                            <i class="fas fa-check"></i>
                                                        </button>'''
            
            html_content += f'''
                                                        <button class="btn btn-info btn-sm" onclick="editTradeModal({trade['id']})" title="Modifier">
                                                            <i class="fas fa-edit"></i>
                                                        </button>
                                                        <button class="btn btn-danger btn-sm" onclick="deleteTradeConfirm({trade['id']})" title="Supprimer">
                                                            <i class="fas fa-trash"></i>
                                                        </button>
                                                        <button class="btn btn-outline-secondary btn-sm" onclick="showTradeDetails({trade['id']})" title="Détails">
                                                            <i class="fas fa-eye"></i>
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>'''
        
        if not trades:
            html_content += '''
                                            <tr>
                                                <td colspan="13" class="text-center py-4">
                                                    <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                                                    <h5 class="text-muted">Aucun trade enregistré</h5>
                                                    <p class="text-muted">Commencez par ajouter votre premier trade ci-dessus.</p>
                                                </td>
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
            
            <!-- Modals -->
            <!-- Modal pour clôturer un trade -->
            <div class="modal fade" id="closeTradeModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Clôturer le Trade</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="closeTradeForm">
                                <input type="hidden" id="closeTradeId">
                                <div class="mb-3">
                                    <label class="form-label">Prix de sortie <span class="text-danger">*</span></label>
                                    <input type="number" class="form-control" id="close_exit_price" step="0.00001" required>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Résultat P&L ($)</label>
                                        <input type="number" class="form-control" id="close_result_pnl" step="0.01">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Résultat (Pips)</label>
                                        <input type="number" class="form-control" id="close_result_pips" step="0.1">
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-success" onclick="submitCloseTrade()">Clôturer</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modal pour modifier un trade -->
            <div class="modal fade" id="editTradeModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Modifier le Trade</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editTradeForm">
                                <input type="hidden" id="editTradeId">
                                <!-- Formulaire similaire à l'ajout mais avec des IDs différents -->
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Actif</label>
                                        <select class="form-select" id="edit_asset" required>'''
        
        # Options pour le formulaire de modification
        for asset in assets:
            html_content += f'<option value="{asset["symbol"]}">{asset["name"]}</option>'
        
        html_content += '''
                                        </select>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Type</label>
                                        <select class="form-select" id="edit_trade_type" required>
                                            <option value="buy">Achat (Buy)</option>
                                            <option value="sell">Vente (Sell)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Date & Heure</label>
                                        <input type="datetime-local" class="form-control" id="edit_trade_date" required>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Taille de lot</label>
                                        <input type="number" class="form-control" id="edit_lot_size" step="0.01" min="0.01" required>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Prix d'entrée</label>
                                        <input type="number" class="form-control" id="edit_entry_price" step="0.00001" required>
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Stop Loss</label>
                                        <input type="number" class="form-control" id="edit_stop_loss" step="0.00001">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Take Profit</label>
                                        <input type="number" class="form-control" id="edit_take_profit" step="0.00001">
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Style de Trading</label>
                                        <select class="form-select" id="edit_trading_style">
                                            <option value="">Sélectionner un style</option>
                                            <option value="scalping">Scalping</option>
                                            <option value="day_trading">Day Trading</option>
                                            <option value="swing">Swing Trading</option>
                                            <option value="position">Position Trading</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">État Émotionnel</label>
                                        <select class="form-select" id="edit_emotions">
                                            <option value="">Sélectionner une émotion</option>
                                            <option value="confident">Confiant</option>
                                            <option value="nervous">Nerveux</option>
                                            <option value="greedy">Cupide</option>
                                            <option value="fearful">Craintif</option>
                                            <option value="calm">Calme</option>
                                            <option value="frustrated">Frustré</option>
                                            <option value="excited">Excité</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Notes</label>
                                    <textarea class="form-control" id="edit_notes" rows="3" maxlength="1000"></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="submitEditTrade()">Modifier</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Scripts JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                // ============================================================================
                // JAVASCRIPT POUR LE JOURNAL DE TRADING COMPLET
                // ============================================================================
                
                // Configuration automatique de la date actuelle
                document.addEventListener('DOMContentLoaded', function() {{
                    const now = new Date();
                    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                    document.getElementById('trade_date').value = now.toISOString().slice(0, 16);
                }});
                
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
                    
                    // Auto-suppression après 5 secondes
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            notification.remove();
                        }}
                    }}, 5000);
                }}
                
                // Soumission du formulaire d'ajout de trade
                document.getElementById('addTradeForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const formData = new FormData();
                    formData.append('asset', document.getElementById('asset').value);
                    formData.append('trade_type', document.getElementById('trade_type').value);
                    formData.append('trade_date', document.getElementById('trade_date').value);
                    formData.append('entry_price', document.getElementById('entry_price').value);
                    formData.append('stop_loss', document.getElementById('stop_loss').value);
                    formData.append('take_profit', document.getElementById('take_profit').value);
                    formData.append('lot_size', document.getElementById('lot_size').value);
                    formData.append('trading_style', document.getElementById('trading_style').value);
                    formData.append('emotions', document.getElementById('emotions').value);
                    formData.append('notes', document.getElementById('notes').value);
                    
                    const audioFile = document.getElementById('audio_note').files[0];
                    if (audioFile) {{
                        formData.append('audio_note', audioFile);
                    }}
                    
                    try {{
                        const response = await fetch('/journal/add-trade', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showNotification('✅ Trade ajouté avec succès !', 'success');
                            document.getElementById('addTradeForm').reset();
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ Erreur: ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }});
                
                // Graphique Win/Loss
                const ctx = document.getElementById('winLossChart').getContext('2d');
                const winLossChart = new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Trades Gagnants', 'Trades Perdants'],
                        datasets: [{{
                            data: [{stats.get('winning_trades', 0)}, {stats.get('losing_trades', 0)}],
                            backgroundColor: ['#28a745', '#dc3545'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});
                
                // Fonction pour clôturer un trade
                function closeTradeModal(tradeId) {{
                    document.getElementById('closeTradeId').value = tradeId;
                    new bootstrap.Modal(document.getElementById('closeTradeModal')).show();
                }}
                
                async function submitCloseTrade() {{
                    const tradeId = document.getElementById('closeTradeId').value;
                    const exitPrice = document.getElementById('close_exit_price').value;
                    const resultPnl = document.getElementById('close_result_pnl').value;
                    const resultPips = document.getElementById('close_result_pips').value;
                    
                    try {{
                        const response = await fetch('/journal/close-trade', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                trade_id: tradeId,
                                exit_price: parseFloat(exitPrice),
                                result_pnl: parseFloat(resultPnl),
                                result_pips: parseFloat(resultPips)
                            }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            bootstrap.Modal.getInstance(document.getElementById('closeTradeModal')).hide();
                            showNotification('✅ Trade clôturé avec succès !', 'success');
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ Erreur: ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }}
                
                // Fonction pour modifier un trade
                function editTradeModal(tradeId) {{
                    document.getElementById('editTradeId').value = tradeId;
                    
                    // Récupération des données du trade
                    fetch(`/journal/get-trade/${{tradeId}}`)
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                const trade = data.trade;
                                document.getElementById('edit_asset').value = trade.asset;
                                document.getElementById('edit_trade_type').value = trade.trade_type;
                                document.getElementById('edit_trade_date').value = trade.trade_date.slice(0, 16);
                                document.getElementById('edit_entry_price').value = trade.entry_price;
                                document.getElementById('edit_stop_loss').value = trade.stop_loss || '';
                                document.getElementById('edit_take_profit').value = trade.take_profit || '';
                                document.getElementById('edit_lot_size').value = trade.lot_size;
                                document.getElementById('edit_trading_style').value = trade.trading_style || '';
                                document.getElementById('edit_emotions').value = trade.emotions || '';
                                document.getElementById('edit_notes').value = trade.notes || '';
                                
                                new bootstrap.Modal(document.getElementById('editTradeModal')).show();
                            }}
                        }});
                }}
                
                async function submitEditTrade() {{
                    const tradeId = document.getElementById('editTradeId').value;
                    
                    const tradeData = {{
                        trade_id: tradeId,
                        asset: document.getElementById('edit_asset').value,
                        trade_type: document.getElementById('edit_trade_type').value,
                        trade_date: document.getElementById('edit_trade_date').value,
                        entry_price: parseFloat(document.getElementById('edit_entry_price').value),
                        stop_loss: parseFloat(document.getElementById('edit_stop_loss').value) || null,
                        take_profit: parseFloat(document.getElementById('edit_take_profit').value) || null,
                        lot_size: parseFloat(document.getElementById('edit_lot_size').value),
                        trading_style: document.getElementById('edit_trading_style').value,
                        emotions: document.getElementById('edit_emotions').value,
                        notes: document.getElementById('edit_notes').value
                    }};
                    
                    try {{
                        const response = await fetch('/journal/edit-trade', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(tradeData)
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            bootstrap.Modal.getInstance(document.getElementById('editTradeModal')).hide();
                            showNotification('✅ Trade modifié avec succès !', 'success');
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ Erreur: ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }}
                
                // Fonction pour supprimer un trade avec confirmation
                function deleteTradeConfirm(tradeId) {{
                    if (confirm('Êtes-vous sûr de vouloir supprimer ce trade ? Cette action est irréversible.')) {{
                        deleteTrade(tradeId);
                    }}
                }}
                
                async function deleteTrade(tradeId) {{
                    try {{
                        const response = await fetch('/journal/delete-trade', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ trade_id: tradeId }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showNotification('✅ Trade supprimé avec succès !', 'success');
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }} else {{
                            showNotification('❌ Erreur: ' + result.error, 'error');
                        }}
                    }} catch (error) {{
                        showNotification('❌ Erreur de connexion', 'error');
                    }}
                }}
                
                // Recherche dans le tableau
                document.getElementById('searchTrades').addEventListener('input', function() {{
                    const searchTerm = this.value.toLowerCase();
                    const rows = document.querySelectorAll('#tradesTableBody tr');
                    
                    rows.forEach(row => {{
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(searchTerm) ? '' : 'none';
                    }});
                }});
                
                // Application des filtres
                function applyFilters() {{
                    const filters = {{
                        asset: document.getElementById('filterAsset').value,
                        trade_type: document.getElementById('filterType').value,
                        result_type: document.getElementById('filterResult').value,
                        date_from: document.getElementById('filterDateFrom').value,
                        date_to: document.getElementById('filterDateTo').value
                    }};
                    
                    // Construction de l'URL avec paramètres
                    const params = new URLSearchParams();
                    Object.keys(filters).forEach(key => {{
                        if (filters[key]) {{
                            params.append(key, filters[key]);
                        }}
                    }});
                    
                    // Rechargement avec filtres
                    window.location.href = '/journal?' + params.toString();
                }}
                
                // Réinitialisation des filtres
                function resetFilters() {{
                    document.getElementById('filterAsset').value = '';
                    document.getElementById('filterType').value = '';
                    document.getElementById('filterResult').value = '';
                    document.getElementById('filterDateFrom').value = '';
                    document.getElementById('filterDateTo').value = '';
                    window.location.href = '/journal';
                }}
                
                // Export CSV
                function exportTrades() {{
                    window.location.href = '/journal/export';
                }}
                
                // Fonction pour afficher les détails
                function showTradeDetails(tradeId) {{
                    // Peut être implémentée pour afficher un modal avec tous les détails
                    console.log('Affichage des détails du trade:', tradeId);
                }}
            </script>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"<h1>Erreur</h1><p>Erreur lors du chargement du journal: {str(e)}</p>"

# ============================================================================
# ROUTES API POUR LES ACTIONS DU JOURNAL
# ============================================================================

@journal_bp.route('/journal/add-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def add_trade_api():
    """API pour ajouter un nouveau trade au journal avec validation stricte"""
    try:
        user_id = session['user_id']
        
        # Récupération et validation des données du formulaire
        asset = request.form.get('asset')
        trade_type = request.form.get('trade_type')
        trade_date = request.form.get('trade_date')
        entry_price = request.form.get('entry_price')
        stop_loss = request.form.get('stop_loss')
        take_profit = request.form.get('take_profit')
        lot_size = request.form.get('lot_size')
        trading_style = request.form.get('trading_style')
        emotions = request.form.get('emotions')
        notes = request.form.get('notes')
        
        # Validation des champs obligatoires
        if not all([asset, trade_type, trade_date, entry_price, lot_size]):
            return jsonify({'success': False, 'error': 'Tous les champs obligatoires doivent être renseignés'})
        
        # Conversion des types numériques avec gestion d'erreur
        try:
            entry_price = float(entry_price)
            lot_size = float(lot_size)
            stop_loss = float(stop_loss) if stop_loss else None
            take_profit = float(take_profit) if take_profit else None
        except ValueError:
            return jsonify({'success': False, 'error': 'Valeurs numériques invalides'})
        
        # Gestion du fichier audio avec sécurité
        audio_note_path = None
        if 'audio_note' in request.files:
            audio_file = request.files['audio_note']
            if audio_file.filename:
                audio_note_path = save_audio_note(audio_file, user_id)
                if audio_note_path is None:
                    return jsonify({'success': False, 'error': 'Format audio non valide ou fichier trop volumineux'})
        
        # Ajout du trade avec toutes les validations
        result = add_trade_to_journal(
            user_id, asset, trade_type, trade_date, entry_price, 
            stop_loss, take_profit, lot_size, trading_style, 
            emotions, notes, audio_note_path
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de l\'ajout: {str(e)}'}), 400

@journal_bp.route('/journal/close-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def close_trade_api():
    """API pour clôturer un trade ouvert avec validation"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        trade_id = data.get('trade_id')
        exit_price = data.get('exit_price')
        result_pnl = data.get('result_pnl')
        result_pips = data.get('result_pips')
        
        # Validation des données obligatoires
        if not trade_id or not exit_price:
            return jsonify({'success': False, 'error': 'ID du trade et prix de sortie requis'})
        
        # Mise à jour du trade avec vérification de propriété
        result = update_trade_result(trade_id, user_id, exit_price, result_pnl, result_pips)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de la clôture: {str(e)}'}), 400

@journal_bp.route('/journal/edit-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def edit_trade_api():
    """API pour modifier un trade existant"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        trade_id = data.get('trade_id')
        asset = data.get('asset')
        trade_type = data.get('trade_type')
        trade_date = data.get('trade_date')
        entry_price = data.get('entry_price')
        stop_loss = data.get('stop_loss')
        take_profit = data.get('take_profit')
        lot_size = data.get('lot_size')
        trading_style = data.get('trading_style')
        emotions = data.get('emotions')
        notes = data.get('notes')
        
        # Validation des champs obligatoires
        if not all([trade_id, asset, trade_type, trade_date, entry_price, lot_size]):
            return jsonify({'success': False, 'error': 'Tous les champs obligatoires doivent être renseignés'})
        
        # Modification du trade avec validation de propriété
        result = update_trade_details(
            trade_id, user_id, asset, trade_type, trade_date, entry_price,
            stop_loss, take_profit, lot_size, trading_style, emotions, notes
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de la modification: {str(e)}'}), 400

@journal_bp.route('/journal/delete-trade', methods=['POST'])
@login_required
@role_required(['premium', 'lifetime'])
def delete_trade_api():
    """API pour supprimer un trade avec vérification de sécurité"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return jsonify({'success': False, 'error': 'ID du trade requis'})
        
        # Suppression sécurisée du trade
        result = delete_trade(trade_id, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}), 400

@journal_bp.route('/journal/get-trade/<int:trade_id>')
@login_required
@role_required(['premium', 'lifetime'])
def get_trade_api(trade_id):
    """API pour récupérer les détails d'un trade spécifique"""
    try:
        user_id = session['user_id']
        
        # Récupération sécurisée du trade
        trade = get_single_trade(trade_id, user_id)
        
        if trade:
            return jsonify({'success': True, 'trade': trade})
        else:
            return jsonify({'success': False, 'error': 'Trade non trouvé ou accès non autorisé'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@journal_bp.route('/journal/trades-data')
@login_required
@role_required(['premium', 'lifetime'])
def get_trades_data():
    """API pour récupérer les données des trades avec filtres"""
    try:
        user_id = session['user_id']
        
        # Paramètres de pagination et filtres
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        # Construction des filtres depuis les paramètres URL
        filters = {}
        if request.args.get('asset'):
            filters['asset'] = request.args.get('asset')
        if request.args.get('trade_type'):
            filters['trade_type'] = request.args.get('trade_type')
        if request.args.get('result_type'):
            filters['result_type'] = request.args.get('result_type')
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        # Récupération des trades avec filtres
        trades = get_user_trades(user_id, limit, offset, filters if filters else None)
        stats = get_trading_statistics(user_id)
        
        return jsonify({
            'success': True,
            'trades': trades,
            'stats': stats,
            'page': page,
            'has_more': len(trades) == limit
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur: {str(e)}'}), 400

@journal_bp.route('/journal/export')
@login_required
@role_required(['premium', 'lifetime'])
def export_trades():
    """Export sécurisé des trades en CSV"""
    try:
        user_id = session['user_id']
        trades = get_user_trades(user_id, limit=1000)  # Export de tous les trades
        
        # Création du CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes CSV
        writer.writerow([
            'ID', 'Actif', 'Type', 'Date', 'Prix Entrée', 'Stop Loss', 'Take Profit',
            'Prix Sortie', 'Lot Size', 'P&L', 'Pips', 'Style', 'Émotions', 'Notes', 'Statut'
        ])
        
        # Données des trades
        for trade in trades:
            writer.writerow([
                trade['id'], trade['asset'], trade['trade_type'], trade['trade_date'],
                trade['entry_price'], trade['stop_loss'], trade['take_profit'],
                trade['exit_price'], trade['lot_size'], trade['result_pnl'],
                trade['result_pips'], trade['trading_style'], trade['emotions'],
                trade['notes'], trade['status']
            ])
        
        # Préparation de la réponse
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=trades_export_user_{user_id}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur export: {str(e)}'}), 400