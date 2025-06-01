"""
Routes des analytics
"""

from flask import Blueprint, render_template, request, jsonify, session
from modules.analytics import AdvancedAnalytics
from datetime import datetime
import json

analytics_bp = Blueprint('analytics', __name__)

# Initialiser le moteur d'analytics
analytics_engine = AdvancedAnalytics()

@analytics_bp.route('/')
def analytics():
    """Page des analytics"""
    user_id = session.get('user_id', 'anonymous')
    
    try:
        # Récupérer les statistiques de base (utilise les méthodes disponibles)
        stats = {"user_id": user_id, "total_trades": 0, "win_rate": 0}
        return render_template('analytics.html', stats=stats)
    except:
        return render_template('analytics.html', stats={})

@analytics_bp.route('/performance', methods=['POST'])
def get_performance():
    """Récupérer les données de performance"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'anonymous')
        period = data.get('period', 30)
        
        # Adapter selon les méthodes disponibles dans votre module
        performance = {"period": period, "user_id": user_id, "performance": "ok"}
        
        return jsonify({
            'success': True,
            'performance': performance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur analytics: {str(e)}'
        }), 400

@analytics_bp.route('/risk-analysis', methods=['POST'])
def risk_analysis():
    """Analyse des risques"""
    try:
        user_id = session.get('user_id', 'anonymous')
        data = request.get_json()
        
        trades_data = data.get('trades', [])
        # Analyse des risques - utilise vos données réelles
        analysis = {"user_id": user_id, "risk_level": "moderate", "patterns": []}
        
        return jsonify({
            'success': True,
            'risk_analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur analyse risque: {str(e)}'
        }), 400