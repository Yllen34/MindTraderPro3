"""
Routes de l'assistant IA
"""

from flask import Blueprint, render_template, request, jsonify, session
from modules.ai_assistant import TradingAIAssistant
from datetime import datetime
import json

ai_bp = Blueprint('ai', __name__)

# Initialiser l'assistant IA
ai_engine = TradingAIAssistant()

@ai_bp.route('/')
def ai_assistant():
    """Page de l'assistant IA"""
    return render_template('ai_assistant.html')

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """Chat avec l'assistant IA"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = session.get('user_id')
        
        # Utiliser votre assistant IA
        response = ai_engine.chat_with_ai(user_message, user_context={'user_id': user_id})
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': str(datetime.now())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur IA: {str(e)}'
        }), 400

@ai_bp.route('/analyze', methods=['POST'])
def analyze_performance():
    """Analyse des performances par l'IA"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Simuler des données de trades pour l'analyse
        trades_data = data.get('trades', [])
        user_profile = data.get('profile', {})
        
        analysis = ai_engine.analyze_trade_performance(trades_data, user_profile)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur d\'analyse: {str(e)}'
        }), 400