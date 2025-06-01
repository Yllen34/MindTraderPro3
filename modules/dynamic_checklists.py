"""
Checklists Dynamiques - Validation pré-trade avec gamification
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TradingStrategy(Enum):
    SMC = "smc"
    ICT = "ict"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    CUSTOM = "custom"

class CheckItemType(Enum):
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    CHOICE = "choice"
    TEXT = "text"
    TIME_CHECK = "time_check"

class CheckItemPriority(Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"

@dataclass
class ChecklistItem:
    """Item de checklist"""
    item_id: str
    title: str
    description: str
    item_type: CheckItemType
    priority: CheckItemPriority
    
    # Configuration
    options: List[str]  # Pour type CHOICE
    min_value: Optional[float]  # Pour type NUMERIC
    max_value: Optional[float]
    required: bool
    
    # Scoring
    points: int
    penalty_points: int
    
    # Aide contextuelle
    help_text: str
    examples: List[str]

@dataclass
class TradingChecklist:
    """Checklist de trading complète"""
    checklist_id: str
    name: str
    strategy: TradingStrategy
    description: str
    
    # Items organisés par catégorie
    market_structure: List[ChecklistItem]
    entry_confirmation: List[ChecklistItem]
    risk_management: List[ChecklistItem]
    psychology: List[ChecklistItem]
    timing: List[ChecklistItem]
    
    # Configuration
    min_score_to_trade: int
    max_score: int
    is_custom: bool
    created_by: str
    
    created_at: datetime
    last_modified: datetime

@dataclass
class ChecklistResult:
    """Résultat d'une checklist complétée"""
    result_id: str
    user_session: str
    checklist_id: str
    trade_symbol: str
    
    # Réponses
    responses: Dict[str, Any]
    
    # Scoring
    total_score: int
    max_possible_score: int
    score_percentage: float
    
    # Validation
    is_validated: bool
    critical_items_passed: bool
    recommendation: str
    
    # Catégories de score
    market_structure_score: int
    entry_confirmation_score: int
    risk_management_score: int
    psychology_score: int
    timing_score: int
    
    completed_at: datetime
    trade_executed: bool
    trade_outcome: Optional[str]

class DynamicChecklistManager:
    """Gestionnaire de checklists dynamiques"""
    
    def __init__(self):
        self.checklists = {}  # checklist_id -> TradingChecklist
        self.user_results = {}  # user_session -> List[ChecklistResult]
        self.user_preferences = {}  # user_session -> preferences
        
        # Initialiser les checklists par défaut
        self._init_default_checklists()
    
    def _init_default_checklists(self):
        """Initialise les checklists par défaut"""
        
        # Checklist SMC (Smart Money Concepts)
        smc_checklist = self._create_smc_checklist()
        self.checklists[smc_checklist.checklist_id] = smc_checklist
        
        # Checklist ICT
        ict_checklist = self._create_ict_checklist()
        self.checklists[ict_checklist.checklist_id] = ict_checklist
        
        # Checklist Breakout
        breakout_checklist = self._create_breakout_checklist()
        self.checklists[breakout_checklist.checklist_id] = breakout_checklist
    
    def _create_smc_checklist(self) -> TradingChecklist:
        """Crée la checklist SMC"""
        
        # Structure de marché
        market_structure = [
            ChecklistItem(
                item_id="smc_structure_trend",
                title="📈 Tendance Higher Timeframe",
                description="La tendance sur H4/D1 est-elle claire ?",
                item_type=CheckItemType.CHOICE,
                priority=CheckItemPriority.CRITICAL,
                options=["Haussière claire", "Baissière claire", "Range/Indécise"],
                min_value=None,
                max_value=None,
                required=True,
                points=25,
                penalty_points=50,
                help_text="Analysez la structure sur H4 et D1 pour identifier la tendance dominante",
                examples=["Série de HH/HL = Haussière", "Série de LL/LH = Baissière"]
            ),
            ChecklistItem(
                item_id="smc_bos_choch",
                title="🔄 BOS ou CHoCH identifié",
                description="Y a-t-il une cassure de structure récente ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=20,
                penalty_points=40,
                help_text="BOS = continuation, CHoCH = retournement",
                examples=["BOS haussier après pullback", "CHoCH baissier confirmé"]
            ),
            ChecklistItem(
                item_id="smc_liquidity_sweep",
                title="💧 Liquidité balayée",
                description="Les liquidités ont-elles été prises ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=False,
                points=15,
                penalty_points=0,
                help_text="Recherchez le balayage des highs/lows précédents",
                examples=["Sweep des highs récents", "Prise de liquidité sous support"]
            )
        ]
        
        # Confirmation d'entrée
        entry_confirmation = [
            ChecklistItem(
                item_id="smc_order_block",
                title="📦 Order Block identifié",
                description="Êtes-vous dans une zone d'Order Block valide ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=25,
                penalty_points=50,
                help_text="Order Block = zone où les institutions ont passé des ordres",
                examples=["OB bullish non mitigé", "OB bearish fraîchement formé"]
            ),
            ChecklistItem(
                item_id="smc_fvg",
                title="📊 Fair Value Gap",
                description="Y a-t-il un FVG à combler ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=False,
                points=15,
                penalty_points=0,
                help_text="FVG = inefficience de prix à remplir",
                examples=["FVG bullish en attente", "Combo OB + FVG"]
            ),
            ChecklistItem(
                item_id="smc_confluence",
                title="🎯 Confluence des niveaux",
                description="Combien de confluences avez-vous ? (0-5)",
                item_type=CheckItemType.NUMERIC,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=0,
                max_value=5,
                required=True,
                points=20,
                penalty_points=10,
                help_text="Plus de confluences = probabilité plus élevée",
                examples=["OB + Support + Fibonacci", "Résistance + Volume + Temps"]
            )
        ]
        
        # Gestion du risque
        risk_management = [
            ChecklistItem(
                item_id="smc_stop_loss",
                title="🛡️ Stop Loss défini",
                description="Votre SL est-il placé correctement ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=30,
                penalty_points=100,
                help_text="SL au-delà de la zone d'invalidation",
                examples=["SL sous Order Block", "SL au-delà du swing"]
            ),
            ChecklistItem(
                item_id="smc_risk_percent",
                title="💰 Risque par trade",
                description="Quel pourcentage risquez-vous ? (0.1-5%)",
                item_type=CheckItemType.NUMERIC,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=0.1,
                max_value=5.0,
                required=True,
                points=25,
                penalty_points=50,
                help_text="Maximum 2% recommandé pour les comptes < 10k",
                examples=["1% pour débutant", "2% pour expérimenté"]
            ),
            ChecklistItem(
                item_id="smc_rr_ratio",
                title="📊 Ratio Risque/Récompense",
                description="Quel est votre ratio R/R ? (1:1 à 1:10)",
                item_type=CheckItemType.NUMERIC,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=1.0,
                max_value=10.0,
                required=True,
                points=20,
                penalty_points=15,
                help_text="Minimum 1:2 recommandé",
                examples=["1:3 = excellent", "1:5 = exceptionnel"]
            )
        ]
        
        # Psychologie
        psychology = [
            ChecklistItem(
                item_id="smc_emotional_state",
                title="🧠 État mental",
                description="Comment vous sentez-vous ? (1-10)",
                item_type=CheckItemType.NUMERIC,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=1,
                max_value=10,
                required=True,
                points=15,
                penalty_points=25,
                help_text="Ne tradez pas si score < 6",
                examples=["8-10 = excellent", "6-7 = acceptable", "< 6 = repos"]
            ),
            ChecklistItem(
                item_id="smc_revenge_trading",
                title="😤 Trading de revanche",
                description="Tradez-vous pour récupérer une perte ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=0,
                penalty_points=75,
                help_text="Si OUI, ne tradez pas ! Prenez une pause",
                examples=["Pause après 2 pertes consécutives"]
            )
        ]
        
        # Timing
        timing = [
            ChecklistItem(
                item_id="smc_session",
                title="⏰ Session de trading",
                description="Êtes-vous dans une session active ?",
                item_type=CheckItemType.CHOICE,
                priority=CheckItemPriority.IMPORTANT,
                options=["London (02:00-05:00)", "New York (07:00-10:00)", "Asian (20:00-00:00)", "Autre"],
                min_value=None,
                max_value=None,
                required=True,
                points=10,
                penalty_points=5,
                help_text="Sessions principales = plus de volatilité",
                examples=["London Killzone idéal", "Overlap London-NY excellent"]
            ),
            ChecklistItem(
                item_id="smc_news_impact",
                title="📰 Impact des nouvelles",
                description="Y a-t-il des news importantes dans les 2h ?",
                item_type=CheckItemType.CHOICE,
                priority=CheckItemPriority.IMPORTANT,
                options=["Aucune news", "News faible impact", "News fort impact"],
                min_value=None,
                max_value=None,
                required=True,
                points=10,
                penalty_points=20,
                help_text="Évitez les trades avant news fort impact",
                examples=["NFP, FOMC, CPI = fort impact"]
            )
        ]
        
        return TradingChecklist(
            checklist_id="smc_pro_v1",
            name="SMC Professionnel",
            strategy=TradingStrategy.SMC,
            description="Checklist complète pour Smart Money Concepts",
            market_structure=market_structure,
            entry_confirmation=entry_confirmation,
            risk_management=risk_management,
            psychology=psychology,
            timing=timing,
            min_score_to_trade=80,
            max_score=200,
            is_custom=False,
            created_by="system",
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
    
    def _create_ict_checklist(self) -> TradingChecklist:
        """Crée la checklist ICT"""
        
        # Version simplifiée pour ICT
        market_structure = [
            ChecklistItem(
                item_id="ict_market_structure",
                title="📊 Structure du marché",
                description="La structure est-elle favorable ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=25,
                penalty_points=50,
                help_text="Analysez les swing highs/lows",
                examples=["Structure haussière intacte"]
            )
        ]
        
        entry_confirmation = [
            ChecklistItem(
                item_id="ict_pda",
                title="📈 PDA Array",
                description="Êtes-vous dans un PDA valide ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=25,
                penalty_points=40,
                help_text="Premium/Discount Array selon ICT",
                examples=["Zone de discount validée"]
            )
        ]
        
        risk_management = [
            ChecklistItem(
                item_id="ict_risk_management",
                title="🛡️ Gestion du risque",
                description="Risque contrôlé ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=30,
                penalty_points=60,
                help_text="Maximum 1-2% par trade",
                examples=["SL défini selon la méthode"]
            )
        ]
        
        psychology = [
            ChecklistItem(
                item_id="ict_mental_state",
                title="🧠 État mental ICT",
                description="Mental préparé ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=15,
                penalty_points=20,
                help_text="Calme et discipliné",
                examples=["Pas d'émotions négatives"]
            )
        ]
        
        timing = [
            ChecklistItem(
                item_id="ict_killzone",
                title="⚡ Killzone",
                description="Dans une killzone ICT ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=False,
                points=15,
                penalty_points=0,
                help_text="London/NY Killzones préférées",
                examples=["02:00-05:00 EST optimal"]
            )
        ]
        
        return TradingChecklist(
            checklist_id="ict_essentials_v1",
            name="ICT Essentials",
            strategy=TradingStrategy.ICT,
            description="Checklist basée sur les concepts ICT",
            market_structure=market_structure,
            entry_confirmation=entry_confirmation,
            risk_management=risk_management,
            psychology=psychology,
            timing=timing,
            min_score_to_trade=75,
            max_score=110,
            is_custom=False,
            created_by="system",
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
    
    def _create_breakout_checklist(self) -> TradingChecklist:
        """Crée la checklist Breakout"""
        
        market_structure = [
            ChecklistItem(
                item_id="breakout_range",
                title="📊 Range identifié",
                description="Y a-t-il un range clair à casser ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=25,
                penalty_points=50,
                help_text="Range minimum 2-3 heures",
                examples=["Consolidation de 4h", "Range quotidien"]
            )
        ]
        
        entry_confirmation = [
            ChecklistItem(
                item_id="breakout_volume",
                title="📈 Volume de cassure",
                description="Le volume confirme-t-il la cassure ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=False,
                points=20,
                penalty_points=0,
                help_text="Volume élevé = cassure valide",
                examples=["Volume 2x supérieur à la moyenne"]
            )
        ]
        
        risk_management = [
            ChecklistItem(
                item_id="breakout_risk",
                title="🛡️ SL dans le range",
                description="SL placé dans l'ancien range ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.CRITICAL,
                options=[],
                min_value=None,
                max_value=None,
                required=True,
                points=30,
                penalty_points=60,
                help_text="SL = milieu du range ou plus conservateur",
                examples=["SL au milieu du range cassé"]
            )
        ]
        
        psychology = [
            ChecklistItem(
                item_id="breakout_patience",
                title="⏳ Patience pour retest",
                description="Attendrez-vous un retest ?",
                item_type=CheckItemType.CHOICE,
                priority=CheckItemPriority.IMPORTANT,
                options=["Entrée immédiate", "Attendre retest", "Les deux selon contexte"],
                min_value=None,
                max_value=None,
                required=True,
                points=15,
                penalty_points=10,
                help_text="Retest augmente la probabilité",
                examples=["Retest réussi = entrée plus sûre"]
            )
        ]
        
        timing = [
            ChecklistItem(
                item_id="breakout_session",
                title="⚡ Session active",
                description="Cassure pendant session active ?",
                item_type=CheckItemType.BOOLEAN,
                priority=CheckItemPriority.IMPORTANT,
                options=[],
                min_value=None,
                max_value=None,
                required=False,
                points=10,
                penalty_points=5,
                help_text="Sessions principales plus efficaces",
                examples=["Breakout pendant London"]
            )
        ]
        
        return TradingChecklist(
            checklist_id="breakout_classic_v1",
            name="Breakout Classique",
            strategy=TradingStrategy.BREAKOUT,
            description="Checklist pour trading de cassures",
            market_structure=market_structure,
            entry_confirmation=entry_confirmation,
            risk_management=risk_management,
            psychology=psychology,
            timing=timing,
            min_score_to_trade=70,
            max_score=100,
            is_custom=False,
            created_by="system",
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
    
    def get_available_checklists(self) -> List[Dict]:
        """Récupère les checklists disponibles"""
        
        return [
            {
                'checklist_id': checklist.checklist_id,
                'name': checklist.name,
                'strategy': checklist.strategy.value,
                'description': checklist.description,
                'min_score_to_trade': checklist.min_score_to_trade,
                'max_score': checklist.max_score,
                'total_items': self._count_total_items(checklist),
                'critical_items': self._count_critical_items(checklist),
                'is_custom': checklist.is_custom
            }
            for checklist in self.checklists.values()
        ]
    
    def get_checklist_details(self, checklist_id: str) -> Optional[Dict]:
        """Récupère les détails d'une checklist"""
        
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return None
        
        return {
            'checklist_id': checklist.checklist_id,
            'name': checklist.name,
            'strategy': checklist.strategy.value,
            'description': checklist.description,
            'categories': {
                'market_structure': [self._item_to_dict(item) for item in checklist.market_structure],
                'entry_confirmation': [self._item_to_dict(item) for item in checklist.entry_confirmation],
                'risk_management': [self._item_to_dict(item) for item in checklist.risk_management],
                'psychology': [self._item_to_dict(item) for item in checklist.psychology],
                'timing': [self._item_to_dict(item) for item in checklist.timing]
            },
            'scoring': {
                'min_score_to_trade': checklist.min_score_to_trade,
                'max_score': checklist.max_score
            }
        }
    
    def submit_checklist(self, user_session: str, checklist_id: str, responses: Dict, trade_symbol: str) -> Dict:
        """Soumet une checklist complétée et calcule le score"""
        
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return {
                'success': False,
                'error': 'Checklist introuvable'
            }
        
        # Calculer le score
        scoring_result = self._calculate_score(checklist, responses)
        
        # Créer le résultat
        result = ChecklistResult(
            result_id=f"result_{int(datetime.now().timestamp())}_{user_session}",
            user_session=user_session,
            checklist_id=checklist_id,
            trade_symbol=trade_symbol,
            responses=responses,
            total_score=scoring_result['total_score'],
            max_possible_score=scoring_result['max_score'],
            score_percentage=scoring_result['percentage'],
            is_validated=scoring_result['is_validated'],
            critical_items_passed=scoring_result['critical_passed'],
            recommendation=scoring_result['recommendation'],
            market_structure_score=scoring_result['category_scores']['market_structure'],
            entry_confirmation_score=scoring_result['category_scores']['entry_confirmation'],
            risk_management_score=scoring_result['category_scores']['risk_management'],
            psychology_score=scoring_result['category_scores']['psychology'],
            timing_score=scoring_result['category_scores']['timing'],
            completed_at=datetime.now(),
            trade_executed=False,
            trade_outcome=None
        )
        
        # Sauvegarder
        if user_session not in self.user_results:
            self.user_results[user_session] = []
        
        self.user_results[user_session].append(result)
        
        return {
            'success': True,
            'result': self._result_to_dict(result),
            'detailed_scoring': scoring_result
        }
    
    def _calculate_score(self, checklist: TradingChecklist, responses: Dict) -> Dict:
        """Calcule le score d'une checklist"""
        
        total_score = 0
        max_score = 0
        category_scores = {
            'market_structure': 0,
            'entry_confirmation': 0,
            'risk_management': 0,
            'psychology': 0,
            'timing': 0
        }
        
        critical_items_passed = True
        failed_critical = []
        
        # Évaluer chaque catégorie
        categories = {
            'market_structure': checklist.market_structure,
            'entry_confirmation': checklist.entry_confirmation,
            'risk_management': checklist.risk_management,
            'psychology': checklist.psychology,
            'timing': checklist.timing
        }
        
        for category_name, items in categories.items():
            category_score = 0
            category_max = 0
            
            for item in items:
                response = responses.get(item.item_id)
                item_score = self._score_item(item, response)
                
                # Vérifier les items critiques
                if item.priority == CheckItemPriority.CRITICAL:
                    if item_score < 0:  # Échec critique
                        critical_items_passed = False
                        failed_critical.append(item.title)
                
                category_score += max(0, item_score)  # Pas de score négatif dans le total
                category_max += item.points
                
            category_scores[category_name] = category_score
            total_score += category_score
            max_score += category_max
        
        # Calculer le pourcentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Déterminer la validation
        is_validated = (total_score >= checklist.min_score_to_trade and critical_items_passed)
        
        # Générer la recommandation
        recommendation = self._generate_recommendation(total_score, checklist.min_score_to_trade, 
                                                     critical_items_passed, failed_critical)
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'is_validated': is_validated,
            'critical_passed': critical_items_passed,
            'failed_critical': failed_critical,
            'recommendation': recommendation,
            'category_scores': category_scores
        }
    
    def _score_item(self, item: ChecklistItem, response: Any) -> int:
        """Score un item individuel"""
        
        if response is None:
            return -item.penalty_points if item.required else 0
        
        if item.item_type == CheckItemType.BOOLEAN:
            if item.item_id == "smc_revenge_trading":  # Item spécial inversé
                return -item.penalty_points if response else item.points
            return item.points if response else -item.penalty_points
        
        elif item.item_type == CheckItemType.CHOICE:
            # Scoring basé sur le choix
            if item.item_id == "smc_structure_trend":
                if response in ["Haussière claire", "Baissière claire"]:
                    return item.points
                else:
                    return -item.penalty_points
            elif item.item_id == "smc_news_impact":
                scores = {
                    "Aucune news": item.points,
                    "News faible impact": item.points // 2,
                    "News fort impact": -item.penalty_points
                }
                return scores.get(response, 0)
            else:
                return item.points  # Score par défaut pour les choix
        
        elif item.item_type == CheckItemType.NUMERIC:
            try:
                value = float(response)
                
                # Validation des limites
                if item.min_value is not None and value < item.min_value:
                    return -item.penalty_points
                if item.max_value is not None and value > item.max_value:
                    return -item.penalty_points
                
                # Scoring spécialisé par item
                if item.item_id == "smc_risk_percent":
                    if value <= 1.0:
                        return item.points
                    elif value <= 2.0:
                        return item.points * 0.8
                    elif value <= 3.0:
                        return item.points * 0.5
                    else:
                        return -item.penalty_points
                
                elif item.item_id == "smc_rr_ratio":
                    if value >= 3.0:
                        return item.points
                    elif value >= 2.0:
                        return item.points * 0.8
                    elif value >= 1.5:
                        return item.points * 0.5
                    else:
                        return -item.penalty_points
                
                elif item.item_id == "smc_emotional_state":
                    if value >= 8:
                        return item.points
                    elif value >= 6:
                        return item.points * 0.7
                    elif value >= 4:
                        return item.points * 0.3
                    else:
                        return -item.penalty_points
                
                elif item.item_id == "smc_confluence":
                    return int(item.points * (value / 5))  # Score proportionnel
                
                else:
                    return item.points  # Score par défaut
                    
            except (ValueError, TypeError):
                return -item.penalty_points
        
        return 0
    
    def _generate_recommendation(self, score: int, min_score: int, critical_passed: bool, failed_critical: List[str]) -> str:
        """Génère une recommandation basée sur le score"""
        
        if not critical_passed:
            return f"❌ TRADE REJETÉ - Items critiques échoués: {', '.join(failed_critical[:2])}"
        
        if score >= min_score:
            percentage = (score / min_score) * 100
            if percentage >= 120:
                return "🚀 TRADE EXCELLENT - Configuration parfaite, exécutez avec confiance !"
            elif percentage >= 100:
                return "✅ TRADE VALIDÉ - Tous les critères respectés, vous pouvez trader"
            else:
                return "✅ TRADE ACCEPTABLE - Score minimum atteint, tradez prudemment"
        else:
            deficit = min_score - score
            return f"⚠️ TRADE NON VALIDÉ - Il manque {deficit} points. Améliorez votre setup"
    
    def _count_total_items(self, checklist: TradingChecklist) -> int:
        """Compte le nombre total d'items"""
        return (len(checklist.market_structure) + len(checklist.entry_confirmation) + 
                len(checklist.risk_management) + len(checklist.psychology) + len(checklist.timing))
    
    def _count_critical_items(self, checklist: TradingChecklist) -> int:
        """Compte le nombre d'items critiques"""
        count = 0
        for category in [checklist.market_structure, checklist.entry_confirmation, 
                        checklist.risk_management, checklist.psychology, checklist.timing]:
            count += sum(1 for item in category if item.priority == CheckItemPriority.CRITICAL)
        return count
    
    def _item_to_dict(self, item: ChecklistItem) -> Dict:
        """Convertit un item en dictionnaire"""
        return {
            'item_id': item.item_id,
            'title': item.title,
            'description': item.description,
            'item_type': item.item_type.value,
            'priority': item.priority.value,
            'options': item.options,
            'min_value': item.min_value,
            'max_value': item.max_value,
            'required': item.required,
            'points': item.points,
            'help_text': item.help_text,
            'examples': item.examples
        }
    
    def _result_to_dict(self, result: ChecklistResult) -> Dict:
        """Convertit un résultat en dictionnaire"""
        return {
            'result_id': result.result_id,
            'checklist_id': result.checklist_id,
            'trade_symbol': result.trade_symbol,
            'total_score': result.total_score,
            'max_possible_score': result.max_possible_score,
            'score_percentage': result.score_percentage,
            'is_validated': result.is_validated,
            'critical_items_passed': result.critical_items_passed,
            'recommendation': result.recommendation,
            'category_scores': {
                'market_structure': result.market_structure_score,
                'entry_confirmation': result.entry_confirmation_score,
                'risk_management': result.risk_management_score,
                'psychology': result.psychology_score,
                'timing': result.timing_score
            },
            'completed_at': result.completed_at.isoformat(),
            'trade_executed': result.trade_executed
        }
    
    def get_user_checklist_history(self, user_session: str, days: int = 30) -> List[Dict]:
        """Récupère l'historique des checklists d'un utilisateur"""
        
        results = self.user_results.get(user_session, [])
        
        if days > 0:
            cutoff = datetime.now() - timedelta(days=days)
            results = [r for r in results if r.completed_at > cutoff]
        
        return [self._result_to_dict(result) for result in results]
    
    def get_user_checklist_stats(self, user_session: str) -> Dict:
        """Récupère les statistiques de checklist d'un utilisateur"""
        
        results = self.user_results.get(user_session, [])
        
        if not results:
            return {
                'total_checklists': 0,
                'validation_rate': 0,
                'average_score': 0,
                'most_used_strategy': None,
                'improvement_areas': []
            }
        
        total = len(results)
        validated = sum(1 for r in results if r.is_validated)
        validation_rate = (validated / total * 100) if total > 0 else 0
        
        average_score = sum(r.score_percentage for r in results) / total
        
        # Stratégie la plus utilisée
        strategies = {}
        for result in results:
            checklist = self.checklists.get(result.checklist_id)
            if checklist:
                strategy = checklist.strategy.value
                strategies[strategy] = strategies.get(strategy, 0) + 1
        
        most_used = max(strategies.items(), key=lambda x: x[1])[0] if strategies else None
        
        # Zones d'amélioration
        category_averages = {
            'market_structure': sum(r.market_structure_score for r in results) / total,
            'entry_confirmation': sum(r.entry_confirmation_score for r in results) / total,
            'risk_management': sum(r.risk_management_score for r in results) / total,
            'psychology': sum(r.psychology_score for r in results) / total,
            'timing': sum(r.timing_score for r in results) / total
        }
        
        # Identifier les 2 plus faibles catégories
        improvement_areas = sorted(category_averages.items(), key=lambda x: x[1])[:2]
        
        return {
            'total_checklists': total,
            'validation_rate': round(validation_rate, 1),
            'average_score': round(average_score, 1),
            'most_used_strategy': most_used,
            'improvement_areas': [area[0] for area in improvement_areas],
            'category_averages': {k: round(v, 1) for k, v in category_averages.items()}
        }

# Instance globale du gestionnaire de checklists
dynamic_checklist_manager = DynamicChecklistManager()