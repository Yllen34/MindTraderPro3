"""
Routes de l'analyse psychologique
"""

from flask import Blueprint, render_template, request, jsonify, session
from modules.psychological_analysis import PsychologicalAnalyzer
from datetime import datetime

psychology_bp = Blueprint('psychology', __name__)

# Initialiser le système d'analyse psychologique
psych_engine = PsychologicalAnalyzer()

@psychology_bp.route('/')
def psychology():
    """Page de l'analyse psychologique"""
    user_id = session.get('user_id', 'anonymous')
    
    try:
        # Récupérer le profil psychologique
        profile = psych_engine.get_user_psychological_profile(user_id)
        return render_template('psychology.html', profile=profile)
    except:
        return render_template('psychology.html', profile={})

@psychology_bp.route('/update-emotions', methods=['POST'])
def update_emotions():
    """Mettre à jour l'état émotionnel"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'anonymous')
        
        emotions = data.get('emotions', {})
        result = psych_engine.record_emotional_state(user_id, emotions)
        
        return jsonify({
            'success': True,
            'mental_score': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur psychologique: {str(e)}'
        }), 400

@psychology_bp.route('/mental-score')
def get_mental_score():
    """Récupérer le score mental actuel"""
    try:
        user_id = session.get('user_id', 'anonymous')
        score = psych_engine.calculate_mental_score(user_id)
        
        return jsonify({
            'success': True,
            'mental_score': score
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }), 400