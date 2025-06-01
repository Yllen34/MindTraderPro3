"""
Système de validation d'entrées pour MindTraderPro
Validation stricte de tous les inputs utilisateur
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any

class InputValidator:
    """Validateur d'entrées sécurisé"""
    
    def __init__(self):
        # Patterns de validation
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'username': r'^[a-zA-Z0-9_]{3,20}$',
            'currency_pair': r'^[A-Z]{6}$',  # Ex: EURUSD
            'phone': r'^\+?[1-9]\d{1,14}$'
        }
        
        # Listes blanches pour les valeurs autorisées
        self.allowed_values = {
            'trading_directions': ['buy', 'sell', 'long', 'short'],
            'timeframes': ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1'],
            'order_types': ['market', 'limit', 'stop', 'stop_limit'],
            'currencies': ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'],
            'account_types': ['demo', 'live', 'contest']
        }
    
    def validate_trading_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Valide les données de trading"""
        errors = []
        
        # Validation du capital
        capital = self._validate_number(data.get('capital'), 'capital', min_val=1, max_val=10_000_000)
        if capital['error']:
            errors.append(capital['error'])
        
        # Validation du pourcentage de risque
        risk = self._validate_number(data.get('risk_percent'), 'risque', min_val=0.01, max_val=10.0)
        if risk['error']:
            errors.append(risk['error'])
        
        # Validation des prix
        entry_price = self._validate_number(data.get('entry_price'), 'prix d\'entrée', min_val=0.00001)
        if entry_price['error']:
            errors.append(entry_price['error'])
        
        stop_loss = self._validate_number(data.get('stop_loss'), 'stop loss', min_val=0.00001)
        if stop_loss['error']:
            errors.append(stop_loss['error'])
        
        # Validation de la direction
        direction = data.get('direction', '').lower()
        if direction not in self.allowed_values['trading_directions']:
            errors.append("Direction de trade invalide")
        
        # Validation de la paire de devises
        pair = data.get('pair_symbol', '').upper()
        if not self._validate_currency_pair(pair):
            errors.append("Paire de devises invalide")
        
        return len(errors) == 0, errors
    
    def validate_user_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Valide les données utilisateur"""
        errors = []
        
        # Validation email
        email = data.get('email', '').strip().lower()
        if not re.match(self.patterns['email'], email):
            errors.append("Format d'email invalide")
        
        # Validation mot de passe
        password = data.get('password', '')
        password_valid, password_error = self._validate_password(password)
        if not password_valid:
            errors.append(password_error)
        
        # Validation nom d'utilisateur
        username = data.get('username', '').strip()
        if not re.match(self.patterns['username'], username):
            errors.append("Nom d'utilisateur invalide (3-20 caractères, lettres/chiffres/_)")
        
        return len(errors) == 0, errors
    
    def validate_journal_entry(self, data: Dict) -> Tuple[bool, List[str]]:
        """Valide une entrée de journal de trading"""
        errors = []
        
        # Validation de la date
        trade_date = data.get('trade_date')
        if not self._validate_date(trade_date):
            errors.append("Date de trade invalide")
        
        # Validation du profit/perte
        pnl = self._validate_number(data.get('profit_loss'), 'profit/perte', allow_negative=True)
        if pnl['error']:
            errors.append(pnl['error'])
        
        # Validation de la taille de lot
        lot_size = self._validate_number(data.get('lot_size'), 'taille de lot', min_val=0.01, max_val=100)
        if lot_size['error']:
            errors.append(lot_size['error'])
        
        # Validation des notes (longueur limitée)
        notes = data.get('notes', '')
        if len(notes) > 1000:
            errors.append("Notes trop longues (max 1000 caractères)")
        
        return len(errors) == 0, errors
    
    def validate_alert_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Valide les données d'alerte de prix"""
        errors = []
        
        # Validation du prix cible
        target_price = self._validate_number(data.get('target_price'), 'prix cible', min_val=0.00001)
        if target_price['error']:
            errors.append(target_price['error'])
        
        # Validation de la condition
        condition = data.get('condition', '').lower()
        if condition not in ['above', 'below', 'equal']:
            errors.append("Condition d'alerte invalide")
        
        # Validation de la paire
        pair = data.get('pair_symbol', '').upper()
        if not self._validate_currency_pair(pair):
            errors.append("Paire de devises invalide")
        
        return len(errors) == 0, errors
    
    def sanitize_text_input(self, text: str, max_length: int = 255) -> str:
        """Nettoie et limite le texte d'entrée"""
        if not text:
            return ""
        
        # Supprime les caractères dangereux
        cleaned = re.sub(r'[<>"\'\&]', '', str(text))
        
        # Limite la longueur
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned.strip()
    
    def _validate_number(self, value: Any, field_name: str, min_val: float = None, 
                        max_val: float = None, allow_negative: bool = False) -> Dict:
        """Valide un nombre"""
        try:
            num = float(value) if value is not None else None
            
            if num is None:
                return {'error': f"{field_name} requis"}
            
            if not allow_negative and num < 0:
                return {'error': f"{field_name} ne peut pas être négatif"}
            
            if min_val is not None and num < min_val:
                return {'error': f"{field_name} doit être supérieur à {min_val}"}
            
            if max_val is not None and num > max_val:
                return {'error': f"{field_name} doit être inférieur à {max_val}"}
            
            return {'value': num, 'error': None}
            
        except (ValueError, TypeError):
            return {'error': f"{field_name} doit être un nombre valide"}
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Valide la force du mot de passe"""
        if len(password) < 8:
            return False, "Mot de passe trop court (min 8 caractères)"
        
        if len(password) > 128:
            return False, "Mot de passe trop long (max 128 caractères)"
        
        if not re.search(r'[A-Z]', password):
            return False, "Mot de passe doit contenir une majuscule"
        
        if not re.search(r'[a-z]', password):
            return False, "Mot de passe doit contenir une minuscule"
        
        if not re.search(r'[0-9]', password):
            return False, "Mot de passe doit contenir un chiffre"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Mot de passe doit contenir un caractère spécial"
        
        return True, "Mot de passe valide"
    
    def _validate_currency_pair(self, pair: str) -> bool:
        """Valide une paire de devises"""
        if not pair or len(pair) != 6:
            return False
        
        base_currency = pair[:3]
        quote_currency = pair[3:]
        
        return (base_currency in self.allowed_values['currencies'] and 
                quote_currency in self.allowed_values['currencies'])
    
    def _validate_date(self, date_string: str) -> bool:
        """Valide un format de date"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            try:
                datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                return True
            except (ValueError, TypeError):
                return False

# Instance globale
validator = InputValidator()