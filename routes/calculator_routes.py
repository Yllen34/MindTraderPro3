"""
Routes du calculateur de lot - Trading Calculator Pro
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app, redirect
from modules.advanced_calculator import AdvancedPositionCalculator, CalculationInput, AssetType, CalculationType
from datetime import datetime

calculator_bp = Blueprint('calculator', __name__)

# Initialiser le calculateur
calculator_engine = AdvancedPositionCalculator()

@calculator_bp.route('/')
def calculator():
    """Page principale du calculateur"""
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect('/auth/login')
    return render_template('calculator.html')

@calculator_bp.route('/calculate', methods=['POST'])
def calculate():
    """API de calcul de position utilisant votre module advanced_calculator"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'anonymous')
        
        # Créer l'input de calcul avec votre classe CalculationInput
        calc_input = CalculationInput(
            calculation_id=f"calc_{int(datetime.now().timestamp())}_{user_id}",
            user_session=str(user_id),
            calculation_type=CalculationType.POSITION_SIZE,
            asset_symbol=data.get('symbol', 'XAUUSD'),
            timestamp=datetime.now(),
            account_capital=float(data.get('capital', 10000)),
            risk_percentage=float(data.get('risk_percent', 1)),
            risk_amount_usd=None,
            entry_price=float(data.get('entry_price')),
            stop_loss=float(data.get('stop_loss')),
            take_profit=float(data.get('take_profit')) if data.get('take_profit') else None,
            current_price=None,
            leverage=float(data.get('leverage', 100)),
            commission_rate=0.0,
            swap_rate=None,
            strategy=data.get('strategy'),
            notes=data.get('notes'),
            tags=[]
        )
        
        # Utiliser votre calculateur avancé
        result = calculator_engine.calculate_position(calc_input)
        
        if result.success:
            return jsonify({
                'success': True,
                'lot_size': result.recommended_lot_size,
                'risk_amount': result.risk_amount,
                'pip_value': result.pip_value,
                'pip_difference': result.stop_loss_pips,
                'potential_profit': result.potential_profit,
                'risk_reward_ratio': result.risk_reward_ratio,
                'margin_required': result.margin_required,
                'risk_level': result.risk_level,
                'recommendations': result.recommendations,
                'warnings': result.warnings
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur de calcul'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur de calcul: {str(e)}'
        }), 400