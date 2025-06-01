"""
Mode Prop Firm Training - Simulation des règles des firmes propriétaires
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class PropFirmType(Enum):
    FTMO = "ftmo"
    FIVEPERCENTERS = "5%ers"
    MYFUNDEDFX = "myfundedfx"
    THE5ERS = "the5ers"
    TOPSTEP = "topstep"
    CUSTOM = "custom"

class ChallengePhase(Enum):
    CHALLENGE = "challenge"
    VERIFICATION = "verification"
    FUNDED = "funded"

class RuleViolationType(Enum):
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_TOTAL_LOSS = "max_total_loss"
    PROFIT_TARGET = "profit_target"
    MINIMUM_TRADING_DAYS = "minimum_trading_days"
    CONSISTENCY_RULE = "consistency_rule"
    NEWS_TRADING = "news_trading"
    WEEKEND_HOLDING = "weekend_holding"

@dataclass
class PropFirmRules:
    """Règles d'une firme propriétaire"""
    firm_type: PropFirmType
    account_size: float
    
    # Limites de perte
    max_daily_loss_percent: float
    max_total_loss_percent: float
    max_daily_loss_amount: float
    max_total_loss_amount: float
    
    # Objectifs de profit
    profit_target_percent: float
    profit_target_amount: float
    
    # Règles de trading
    minimum_trading_days: int
    maximum_trading_days: int
    consistency_rule_percent: Optional[float]  # Max profit en une journée
    
    # Restrictions
    news_trading_allowed: bool
    weekend_holding_allowed: bool
    hedge_allowed: bool
    ea_allowed: bool
    
    # Règles de vérification (phase 2)
    verification_profit_target_percent: Optional[float]
    verification_minimum_days: Optional[int]

@dataclass
class PropFirmAccount:
    """Compte de simulation prop firm"""
    account_id: str
    user_session: str
    firm_type: PropFirmType
    challenge_phase: ChallengePhase
    
    # Paramètres du compte
    initial_balance: float
    current_balance: float
    current_equity: float
    
    # Tracking des limites
    daily_loss_today: float
    total_loss_from_start: float
    highest_balance: float
    
    # Progression
    current_profit: float
    profit_target_reached: bool
    
    # Statistiques de trading
    trading_days: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    # Violations
    rule_violations: List[str]
    is_active: bool
    failed_reason: Optional[str]
    
    # Dates
    start_date: datetime
    end_date: datetime
    last_trade_date: Optional[datetime]
    
    created_at: datetime

@dataclass
class PropFirmTrade:
    """Trade dans le contexte prop firm"""
    trade_id: str
    account_id: str
    symbol: str
    direction: str
    lot_size: float
    
    # Prix
    open_price: float
    close_price: Optional[float]
    
    # Résultats
    profit_loss: Optional[float]
    commission: float
    swap: float
    
    # Validation prop firm
    violates_rules: bool
    violation_reasons: List[str]
    
    # Dates
    open_time: datetime
    close_time: Optional[datetime]

class PropFirmTrainingSystem:
    """Système d'entraînement aux règles des prop firms"""
    
    def __init__(self):
        self.prop_firm_rules = {}  # firm_type -> PropFirmRules
        self.user_accounts = {}  # user_session -> List[PropFirmAccount]
        self.account_trades = {}  # account_id -> List[PropFirmTrade]
        
        # Initialiser les règles des principales firmes
        self._init_prop_firm_rules()
    
    def _init_prop_firm_rules(self):
        """Initialise les règles des principales prop firms"""
        
        # FTMO
        ftmo_rules = PropFirmRules(
            firm_type=PropFirmType.FTMO,
            account_size=100000,
            max_daily_loss_percent=5.0,
            max_total_loss_percent=10.0,
            max_daily_loss_amount=5000,
            max_total_loss_amount=10000,
            profit_target_percent=10.0,
            profit_target_amount=10000,
            minimum_trading_days=4,
            maximum_trading_days=30,
            consistency_rule_percent=None,
            news_trading_allowed=True,
            weekend_holding_allowed=True,
            hedge_allowed=False,
            ea_allowed=True,
            verification_profit_target_percent=5.0,
            verification_minimum_days=4
        )
        self.prop_firm_rules[PropFirmType.FTMO] = ftmo_rules
        
        # The5%ers
        five_percent_rules = PropFirmRules(
            firm_type=PropFirmType.FIVEPERCENTERS,
            account_size=100000,
            max_daily_loss_percent=5.0,
            max_total_loss_percent=6.0,
            max_daily_loss_amount=5000,
            max_total_loss_amount=6000,
            profit_target_percent=8.0,
            profit_target_amount=8000,
            minimum_trading_days=4,
            maximum_trading_days=60,
            consistency_rule_percent=50.0,  # Max 50% du profit target en une journée
            news_trading_allowed=False,
            weekend_holding_allowed=False,
            hedge_allowed=False,
            ea_allowed=True,
            verification_profit_target_percent=5.0,
            verification_minimum_days=4
        )
        self.prop_firm_rules[PropFirmType.FIVEPERCENTERS] = five_percent_rules
        
        # MyFundedFX
        myfunded_rules = PropFirmRules(
            firm_type=PropFirmType.MYFUNDEDFX,
            account_size=100000,
            max_daily_loss_percent=5.0,
            max_total_loss_percent=12.0,
            max_daily_loss_amount=5000,
            max_total_loss_amount=12000,
            profit_target_percent=8.0,
            profit_target_amount=8000,
            minimum_trading_days=5,
            maximum_trading_days=30,
            consistency_rule_percent=None,
            news_trading_allowed=True,
            weekend_holding_allowed=True,
            hedge_allowed=True,
            ea_allowed=True,
            verification_profit_target_percent=5.0,
            verification_minimum_days=5
        )
        self.prop_firm_rules[PropFirmType.MYFUNDEDFX] = myfunded_rules
    
    def create_prop_account(self, user_session: str, firm_type: str, account_size: float = None) -> Dict:
        """Crée un nouveau compte prop firm"""
        
        try:
            firm_enum = PropFirmType(firm_type)
        except ValueError:
            return {
                'success': False,
                'error': 'Type de firme non supporté'
            }
        
        rules = self.prop_firm_rules.get(firm_enum)
        if not rules:
            return {
                'success': False,
                'error': 'Règles de firme non disponibles'
            }
        
        # Utiliser la taille par défaut ou personnalisée
        initial_balance = account_size if account_size else rules.account_size
        
        account_id = f"prop_{firm_type}_{int(datetime.now().timestamp())}"
        
        account = PropFirmAccount(
            account_id=account_id,
            user_session=user_session,
            firm_type=firm_enum,
            challenge_phase=ChallengePhase.CHALLENGE,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            current_equity=initial_balance,
            daily_loss_today=0.0,
            total_loss_from_start=0.0,
            highest_balance=initial_balance,
            current_profit=0.0,
            profit_target_reached=False,
            trading_days=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            rule_violations=[],
            is_active=True,
            failed_reason=None,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=rules.maximum_trading_days),
            last_trade_date=None,
            created_at=datetime.now()
        )
        
        # Sauvegarder le compte
        if user_session not in self.user_accounts:
            self.user_accounts[user_session] = []
        
        self.user_accounts[user_session].append(account)
        self.account_trades[account_id] = []
        
        return {
            'success': True,
            'account_id': account_id,
            'account_details': self._account_to_dict(account),
            'rules': self._rules_to_dict(rules)
        }
    
    def execute_prop_trade(self, account_id: str, trade_data: Dict) -> Dict:
        """Exécute un trade dans le contexte prop firm"""
        
        account = self._get_account_by_id(account_id)
        if not account:
            return {
                'success': False,
                'error': 'Compte introuvable'
            }
        
        if not account.is_active:
            return {
                'success': False,
                'error': 'Compte inactif ou échoué'
            }
        
        rules = self.prop_firm_rules[account.firm_type]
        
        # Créer le trade
        trade_id = f"trade_{int(datetime.now().timestamp())}"
        
        trade = PropFirmTrade(
            trade_id=trade_id,
            account_id=account_id,
            symbol=trade_data['symbol'],
            direction=trade_data['direction'],
            lot_size=trade_data['lot_size'],
            open_price=trade_data['open_price'],
            close_price=trade_data.get('close_price'),
            profit_loss=trade_data.get('profit_loss'),
            commission=trade_data.get('commission', 0),
            swap=trade_data.get('swap', 0),
            violates_rules=False,
            violation_reasons=[],
            open_time=datetime.now(),
            close_time=datetime.fromisoformat(trade_data['close_time']) if trade_data.get('close_time') else None
        )
        
        # Valider le trade selon les règles
        validation_result = self._validate_trade(account, trade, rules)
        trade.violates_rules = not validation_result['valid']
        trade.violation_reasons = validation_result['violations']
        
        # Si le trade est fermé, mettre à jour le compte
        if trade.close_price and trade.profit_loss is not None:
            self._update_account_after_trade(account, trade, rules)
        
        # Sauvegarder le trade
        self.account_trades[account_id].append(trade)
        
        return {
            'success': True,
            'trade_id': trade_id,
            'trade_valid': not trade.violates_rules,
            'violations': trade.violation_reasons,
            'account_status': self._get_account_status(account, rules)
        }
    
    def _validate_trade(self, account: PropFirmAccount, trade: PropFirmTrade, rules: PropFirmRules) -> Dict:
        """Valide un trade selon les règles prop firm"""
        
        violations = []
        
        # Vérifier le trading de news (si interdit)
        if not rules.news_trading_allowed:
            # Simuler la vérification de news (en production, vérifier un calendrier économique)
            current_hour = datetime.now().hour
            if 12 <= current_hour <= 14:  # Exemple: news à 13h30
                violations.append("Trading pendant les news interdit")
        
        # Vérifier le holding de weekend (si interdit)
        if not rules.weekend_holding_allowed and trade.close_time is None:
            current_weekday = datetime.now().weekday()
            if current_weekday >= 4:  # Vendredi ou weekend
                violations.append("Positions ouvertes le weekend interdites")
        
        # Vérifier le hedging (si interdit)
        if not rules.hedge_allowed:
            existing_trades = self.account_trades.get(account.account_id, [])
            for existing_trade in existing_trades:
                if (existing_trade.symbol == trade.symbol and 
                    existing_trade.direction != trade.direction and
                    existing_trade.close_time is None):
                    violations.append("Hedging interdit")
                    break
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    def _update_account_after_trade(self, account: PropFirmAccount, trade: PropFirmTrade, rules: PropFirmRules):
        """Met à jour le compte après un trade fermé"""
        
        # Mettre à jour le solde
        net_pnl = trade.profit_loss + trade.commission + trade.swap
        account.current_balance += net_pnl
        account.current_equity = account.current_balance
        
        # Mettre à jour les statistiques
        account.total_trades += 1
        if trade.profit_loss > 0:
            account.winning_trades += 1
        else:
            account.losing_trades += 1
        
        # Mettre à jour les métriques de tracking
        if account.current_balance > account.highest_balance:
            account.highest_balance = account.current_balance
        
        # Calculer le profit actuel
        account.current_profit = account.current_balance - account.initial_balance
        
        # Calculer la perte totale depuis le début
        account.total_loss_from_start = max(0, account.initial_balance - account.current_balance)
        
        # Calculer la perte quotidienne
        today = datetime.now().date()
        if account.last_trade_date and account.last_trade_date.date() != today:
            account.daily_loss_today = 0  # Nouveau jour, reset
        
        if net_pnl < 0:
            account.daily_loss_today += abs(net_pnl)
        
        account.last_trade_date = datetime.now()
        
        # Vérifier les violations de règles
        self._check_rule_violations(account, rules)
        
        # Vérifier si l'objectif de profit est atteint
        if account.current_profit >= rules.profit_target_amount:
            account.profit_target_reached = True
            
            # Passer à la phase de vérification ou funded
            if account.challenge_phase == ChallengePhase.CHALLENGE:
                if rules.verification_profit_target_percent:
                    account.challenge_phase = ChallengePhase.VERIFICATION
                    # Reset pour la phase de vérification
                    account.trading_days = 0
                    account.current_profit = 0
                    account.profit_target_reached = False
                else:
                    account.challenge_phase = ChallengePhase.FUNDED
            elif account.challenge_phase == ChallengePhase.VERIFICATION:
                account.challenge_phase = ChallengePhase.FUNDED
    
    def _check_rule_violations(self, account: PropFirmAccount, rules: PropFirmRules):
        """Vérifie les violations de règles"""
        
        violations = []
        
        # Vérifier la perte quotidienne maximale
        if account.daily_loss_today > rules.max_daily_loss_amount:
            violations.append(f"Perte quotidienne maximale dépassée: ${account.daily_loss_today:.2f} > ${rules.max_daily_loss_amount}")
            account.is_active = False
            account.failed_reason = "Violation: Perte quotidienne maximale"
        
        # Vérifier la perte totale maximale
        if account.total_loss_from_start > rules.max_total_loss_amount:
            violations.append(f"Perte totale maximale dépassée: ${account.total_loss_from_start:.2f} > ${rules.max_total_loss_amount}")
            account.is_active = False
            account.failed_reason = "Violation: Perte totale maximale"
        
        # Vérifier la règle de consistance (The5%ers)
        if rules.consistency_rule_percent and account.current_profit > 0:
            max_daily_profit = rules.profit_target_amount * (rules.consistency_rule_percent / 100)
            # Simulation simple - en production, calculer le profit quotidien réel
            if account.current_profit > max_daily_profit:
                violations.append(f"Règle de consistance violée: Profit quotidien > {rules.consistency_rule_percent}% de l'objectif")
        
        # Ajouter les nouvelles violations
        for violation in violations:
            if violation not in account.rule_violations:
                account.rule_violations.append(violation)
    
    def get_account_dashboard(self, account_id: str) -> Dict:
        """Récupère le tableau de bord d'un compte prop firm"""
        
        account = self._get_account_by_id(account_id)
        if not account:
            return {
                'success': False,
                'error': 'Compte introuvable'
            }
        
        rules = self.prop_firm_rules[account.firm_type]
        
        # Calculer les métriques
        days_elapsed = (datetime.now() - account.start_date).days + 1
        days_remaining = (account.end_date - datetime.now()).days
        
        # Calculer les limites restantes
        daily_loss_remaining = rules.max_daily_loss_amount - account.daily_loss_today
        total_loss_remaining = rules.max_total_loss_amount - account.total_loss_from_start
        
        # Calculer la progression vers l'objectif
        current_target = rules.profit_target_amount
        if account.challenge_phase == ChallengePhase.VERIFICATION and rules.verification_profit_target_percent:
            current_target = account.initial_balance * (rules.verification_profit_target_percent / 100)
        
        profit_progress = (account.current_profit / current_target * 100) if current_target > 0 else 0
        
        # Statistiques de trading
        win_rate = (account.winning_trades / account.total_trades * 100) if account.total_trades > 0 else 0
        
        return {
            'success': True,
            'account': self._account_to_dict(account),
            'rules': self._rules_to_dict(rules),
            'metrics': {
                'days_elapsed': days_elapsed,
                'days_remaining': max(0, days_remaining),
                'trading_days_required': rules.minimum_trading_days,
                'daily_loss_remaining': max(0, daily_loss_remaining),
                'total_loss_remaining': max(0, total_loss_remaining),
                'profit_target_current': current_target,
                'profit_progress_percent': min(100, round(profit_progress, 1)),
                'win_rate': round(win_rate, 1)
            },
            'status': self._get_account_status(account, rules)
        }
    
    def _get_account_status(self, account: PropFirmAccount, rules: PropFirmRules) -> Dict:
        """Détermine le statut du compte"""
        
        if not account.is_active:
            return {
                'status': 'failed',
                'message': account.failed_reason or 'Compte échoué',
                'color': 'danger'
            }
        
        # Vérifier si passé en phase suivante
        if account.profit_target_reached:
            if account.challenge_phase == ChallengePhase.CHALLENGE:
                return {
                    'status': 'verification',
                    'message': 'Challenge réussi ! Phase de vérification',
                    'color': 'warning'
                }
            elif account.challenge_phase == ChallengePhase.VERIFICATION:
                return {
                    'status': 'funded',
                    'message': 'Félicitations ! Compte financé',
                    'color': 'success'
                }
            elif account.challenge_phase == ChallengePhase.FUNDED:
                return {
                    'status': 'funded',
                    'message': 'Compte financé actif',
                    'color': 'success'
                }
        
        # Vérifier les violations récentes
        if account.rule_violations:
            return {
                'status': 'warning',
                'message': f'Attention: {len(account.rule_violations)} violation(s)',
                'color': 'warning'
            }
        
        # Vérifier la proximité des limites
        daily_limit_used = (account.daily_loss_today / rules.max_daily_loss_amount * 100)
        total_limit_used = (account.total_loss_from_start / rules.max_total_loss_amount * 100)
        
        if daily_limit_used > 80 or total_limit_used > 80:
            return {
                'status': 'danger',
                'message': 'Proche des limites de perte',
                'color': 'danger'
            }
        elif daily_limit_used > 60 or total_limit_used > 60:
            return {
                'status': 'caution',
                'message': 'Attention aux limites de perte',
                'color': 'warning'
            }
        
        return {
            'status': 'active',
            'message': f'Challenge en cours - Phase {account.challenge_phase.value}',
            'color': 'primary'
        }
    
    def get_user_prop_accounts(self, user_session: str) -> List[Dict]:
        """Récupère tous les comptes prop firm d'un utilisateur"""
        
        accounts = self.user_accounts.get(user_session, [])
        return [self._account_to_dict(account) for account in accounts]
    
    def get_available_firms(self) -> List[Dict]:
        """Récupère la liste des firmes disponibles"""
        
        return [
            {
                'firm_type': rules.firm_type.value,
                'name': self._get_firm_display_name(rules.firm_type),
                'account_size': rules.account_size,
                'profit_target': rules.profit_target_percent,
                'max_daily_loss': rules.max_daily_loss_percent,
                'max_total_loss': rules.max_total_loss_percent,
                'minimum_days': rules.minimum_trading_days,
                'has_verification': rules.verification_profit_target_percent is not None,
                'news_trading': rules.news_trading_allowed,
                'weekend_holding': rules.weekend_holding_allowed
            }
            for rules in self.prop_firm_rules.values()
        ]
    
    def _get_firm_display_name(self, firm_type: PropFirmType) -> str:
        """Retourne le nom d'affichage de la firme"""
        
        names = {
            PropFirmType.FTMO: "FTMO",
            PropFirmType.FIVEPERCENTERS: "The 5%ers",
            PropFirmType.MYFUNDEDFX: "MyFundedFX",
            PropFirmType.THE5ERS: "The5ers",
            PropFirmType.TOPSTEP: "TopStep"
        }
        return names.get(firm_type, firm_type.value.upper())
    
    def _get_account_by_id(self, account_id: str) -> Optional[PropFirmAccount]:
        """Récupère un compte par son ID"""
        
        for accounts in self.user_accounts.values():
            for account in accounts:
                if account.account_id == account_id:
                    return account
        return None
    
    def _account_to_dict(self, account: PropFirmAccount) -> Dict:
        """Convertit un compte en dictionnaire"""
        
        return {
            'account_id': account.account_id,
            'firm_type': account.firm_type.value,
            'challenge_phase': account.challenge_phase.value,
            'initial_balance': account.initial_balance,
            'current_balance': account.current_balance,
            'current_equity': account.current_equity,
            'daily_loss_today': account.daily_loss_today,
            'total_loss_from_start': account.total_loss_from_start,
            'highest_balance': account.highest_balance,
            'current_profit': account.current_profit,
            'profit_target_reached': account.profit_target_reached,
            'trading_days': account.trading_days,
            'total_trades': account.total_trades,
            'winning_trades': account.winning_trades,
            'losing_trades': account.losing_trades,
            'rule_violations': account.rule_violations,
            'is_active': account.is_active,
            'failed_reason': account.failed_reason,
            'start_date': account.start_date.isoformat(),
            'end_date': account.end_date.isoformat(),
            'created_at': account.created_at.isoformat()
        }
    
    def _rules_to_dict(self, rules: PropFirmRules) -> Dict:
        """Convertit les règles en dictionnaire"""
        
        return {
            'firm_type': rules.firm_type.value,
            'account_size': rules.account_size,
            'max_daily_loss_percent': rules.max_daily_loss_percent,
            'max_total_loss_percent': rules.max_total_loss_percent,
            'max_daily_loss_amount': rules.max_daily_loss_amount,
            'max_total_loss_amount': rules.max_total_loss_amount,
            'profit_target_percent': rules.profit_target_percent,
            'profit_target_amount': rules.profit_target_amount,
            'minimum_trading_days': rules.minimum_trading_days,
            'maximum_trading_days': rules.maximum_trading_days,
            'consistency_rule_percent': rules.consistency_rule_percent,
            'news_trading_allowed': rules.news_trading_allowed,
            'weekend_holding_allowed': rules.weekend_holding_allowed,
            'hedge_allowed': rules.hedge_allowed,
            'ea_allowed': rules.ea_allowed,
            'verification_profit_target_percent': rules.verification_profit_target_percent,
            'verification_minimum_days': rules.verification_minimum_days
        }

# Instance globale du système prop firm
prop_firm_training_system = PropFirmTrainingSystem()