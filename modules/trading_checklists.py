"""
Checklists Dynamiques de Trading - Validation avant trade avec gamification
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class ChecklistType(Enum):
    SMC = "smart_money_concepts"
    ICT = "ict_concepts"
    BREAKOUT = "breakout"
    TREND_FOLLOWING = "trend_following"
    SCALPING = "scalping"
    CUSTOM = "custom"

class CheckItemStatus(Enum):
    UNCHECKED = "unchecked"
    CHECKED = "checked"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"

@dataclass
class ChecklistItem:
    """Item de checklist de trading"""
    id: str
    title: str
    description: str
    category: str
    importance: str  # critical, important, nice_to_have
    is_required: bool
    status: CheckItemStatus
    validation_rule: Optional[str]  # Règle de validation automatique
    help_text: str

@dataclass
class TradingChecklist:
    """Checklist complète de trading"""
    id: str
    name: str
    description: str
    checklist_type: ChecklistType
    items: List[ChecklistItem]
    completion_score: int
    required_score: int
    is_premium: bool
    created_at: datetime
    last_used: Optional[datetime]

@dataclass
class ChecklistResult:
    """Résultat de validation d'une checklist"""
    checklist_id: str
    completion_score: int
    max_score: int
    completion_percentage: int
    is_valid_to_trade: bool
    failed_critical_items: List[str]
    warnings: List[str]
    recommendations: List[str]
    validation_timestamp: datetime

class DynamicChecklistManager:
    """Gestionnaire des checklists dynamiques de trading"""
    
    def __init__(self):
        self.checklists = self._initialize_default_checklists()
        self.user_checklists = {}
        self.completion_history = {}
        
    def _initialize_default_checklists(self) -> Dict[str, TradingChecklist]:
        """Initialise les checklists par défaut"""
        
        checklists = {}
        
        # Checklist SMC (Smart Money Concepts)
        smc_items = [
            ChecklistItem(
                id="market_structure",
                title="Structure de marché identifiée",
                description="La tendance est-elle claire (haussière/baissière/range) ?",
                category="structure",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="market_structure != ''",
                help_text="Analysez les sommets et creux pour identifier la structure"
            ),
            ChecklistItem(
                id="liquidity_zones",
                title="Zones de liquidité repérées",
                description="Avez-vous identifié les zones de liquidité (supports/résistances) ?",
                category="liquidity",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="confluence_factors includes 'support'",
                help_text="Cherchez les anciens supports/résistances où le prix a réagi"
            ),
            ChecklistItem(
                id="orderblocks",
                title="Order Blocks marqués",
                description="Les order blocks (zones d'ordres institutionnels) sont-ils identifiés ?",
                category="orderflow",
                importance="important",
                is_required=False,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Order blocks = dernière bougie avant un mouvement impulsif"
            ),
            ChecklistItem(
                id="fair_value_gaps",
                title="Fair Value Gaps (FVG) analysés",
                description="Y a-t-il des gaps de prix à combler ?",
                category="imbalance",
                importance="important",
                is_required=False,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Les FVG sont des zones où le prix pourrait revenir"
            ),
            ChecklistItem(
                id="time_session",
                title="Session de trading appropriée",
                description="Êtes-vous dans une session volatile (Londres/New York) ?",
                category="timing",
                importance="important",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="trading_session in ['london', 'ny']",
                help_text="Évitez les sessions asiatiques pour SMC (sauf stratégie spécifique)"
            ),
            ChecklistItem(
                id="risk_reward",
                title="Risk/Reward minimum 1:2",
                description="Le ratio risque/rendement est-il au moins de 1:2 ?",
                category="risk",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="risk_reward_ratio >= 2.0",
                help_text="Minimum 1:2 pour compenser les trades perdants"
            ),
            ChecklistItem(
                id="confluence",
                title="Minimum 3 confluences",
                description="Avez-vous au moins 3 facteurs de confluence ?",
                category="confluence",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="len(confluence_factors) >= 3",
                help_text="Plus de confluences = plus de probabilité de succès"
            )
        ]
        
        checklists["smc"] = TradingChecklist(
            id="smc",
            name="Smart Money Concepts",
            description="Checklist complète pour les concepts Smart Money",
            checklist_type=ChecklistType.SMC,
            items=smc_items,
            completion_score=0,
            required_score=80,
            is_premium=False,
            created_at=datetime.now(),
            last_used=None
        )
        
        # Checklist Breakout
        breakout_items = [
            ChecklistItem(
                id="key_level",
                title="Niveau clé identifié",
                description="Le niveau de support/résistance est-il clairement défini ?",
                category="level",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Le niveau doit avoir été testé au moins 2-3 fois"
            ),
            ChecklistItem(
                id="volume_confirmation",
                title="Volume de confirmation",
                description="Y a-t-il une augmentation du volume lors de la cassure ?",
                category="volume",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule="confluence_factors includes 'volume'",
                help_text="Sans volume, la cassure peut être un faux signal"
            ),
            ChecklistItem(
                id="breakout_strength",
                title="Force de la cassure",
                description="La cassure est-elle franche (bougie de clôture au-delà) ?",
                category="strength",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Attendez la clôture de bougie pour confirmer"
            ),
            ChecklistItem(
                id="retest_zone",
                title="Zone de retest définie",
                description="Avez-vous identifié où placer votre entrée en cas de retest ?",
                category="entry",
                importance="important",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Le retest du niveau cassé offre souvent une meilleure entrée"
            ),
            ChecklistItem(
                id="market_context",
                title="Contexte de marché favorable",
                description="Le breakout va-t-il dans le sens de la tendance générale ?",
                category="context",
                importance="important",
                is_required=False,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Breakouts dans le sens de la tendance ont plus de succès"
            )
        ]
        
        checklists["breakout"] = TradingChecklist(
            id="breakout",
            name="Stratégie Breakout",
            description="Validation pour les trades de cassure",
            checklist_type=ChecklistType.BREAKOUT,
            items=breakout_items,
            completion_score=0,
            required_score=75,
            is_premium=False,
            created_at=datetime.now(),
            last_used=None
        )
        
        # Checklist Scalping (Premium)
        scalping_items = [
            ChecklistItem(
                id="tight_spread",
                title="Spread serré",
                description="Le spread est-il inférieur à 2 pips ?",
                category="cost",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Spread élevé = coûts trop importants pour le scalping"
            ),
            ChecklistItem(
                id="high_volatility",
                title="Volatilité élevée",
                description="Êtes-vous dans une période de forte volatilité ?",
                category="volatility",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Scalpez pendant les overlaps Londres-NY (14h-17h)"
            ),
            ChecklistItem(
                id="quick_execution",
                title="Exécution rapide prête",
                description="Pouvez-vous exécuter et gérer le trade rapidement ?",
                category="execution",
                importance="critical",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Le scalping demande une réaction immédiate"
            ),
            ChecklistItem(
                id="small_target",
                title="Objectif raisonnable",
                description="Votre objectif est-il de 5-15 pips maximum ?",
                category="target",
                importance="important",
                is_required=True,
                status=CheckItemStatus.UNCHECKED,
                validation_rule=None,
                help_text="Ne soyez pas trop gourmand en scalping"
            )
        ]
        
        checklists["scalping"] = TradingChecklist(
            id="scalping",
            name="Scalping Professionnel",
            description="Checklist spécialisée pour le scalping",
            checklist_type=ChecklistType.SCALPING,
            items=scalping_items,
            completion_score=0,
            required_score=90,
            is_premium=True,
            created_at=datetime.now(),
            last_used=None
        )
        
        return checklists
    
    def get_checklist(self, checklist_id: str) -> Optional[TradingChecklist]:
        """Récupère une checklist par ID"""
        return self.checklists.get(checklist_id)
    
    def get_available_checklists(self, is_premium_user: bool = False) -> List[TradingChecklist]:
        """Récupère les checklists disponibles selon le statut utilisateur"""
        available = []
        
        for checklist in self.checklists.values():
            if not checklist.is_premium or is_premium_user:
                available.append(checklist)
        
        return available
    
    def validate_checklist(self, checklist_id: str, trade_data: Dict, checked_items: List[str]) -> ChecklistResult:
        """Valide une checklist avec les données du trade"""
        
        if checklist_id not in self.checklists:
            raise ValueError(f"Checklist {checklist_id} non trouvée")
        
        checklist = self.checklists[checklist_id]
        
        # Mise à jour du statut des items
        for item in checklist.items:
            if item.id in checked_items:
                item.status = CheckItemStatus.CHECKED
            else:
                item.status = CheckItemStatus.UNCHECKED
        
        # Validation automatique basée sur les règles
        self._auto_validate_items(checklist, trade_data)
        
        # Calcul du score
        total_score = 0
        max_score = 0
        failed_critical = []
        warnings = []
        recommendations = []
        
        for item in checklist.items:
            # Points selon l'importance
            if item.importance == "critical":
                points = 30
            elif item.importance == "important":
                points = 20
            else:
                points = 10
            
            max_score += points
            
            if item.status == CheckItemStatus.CHECKED:
                total_score += points
            elif item.is_required and item.status != CheckItemStatus.CHECKED:
                if item.importance == "critical":
                    failed_critical.append(item.title)
                else:
                    warnings.append(f"Item manquant: {item.title}")
        
        # Génération des recommandations
        if failed_critical:
            recommendations.append("🛑 Éléments critiques manquants - Ne pas trader")
        elif total_score < checklist.required_score:
            recommendations.append("⚠️ Score insuffisant - Revoir l'analyse")
        else:
            recommendations.append("✅ Checklist validée - Trade autorisé")
        
        completion_percentage = int((total_score / max_score) * 100) if max_score > 0 else 0
        is_valid = len(failed_critical) == 0 and total_score >= checklist.required_score
        
        result = ChecklistResult(
            checklist_id=checklist_id,
            completion_score=total_score,
            max_score=max_score,
            completion_percentage=completion_percentage,
            is_valid_to_trade=is_valid,
            failed_critical_items=failed_critical,
            warnings=warnings,
            recommendations=recommendations,
            validation_timestamp=datetime.now()
        )
        
        # Mise à jour de l'historique
        checklist.completion_score = total_score
        checklist.last_used = datetime.now()
        
        return result
    
    def _auto_validate_items(self, checklist: TradingChecklist, trade_data: Dict):
        """Validation automatique des items avec règles"""
        
        for item in checklist.items:
            if not item.validation_rule:
                continue
            
            try:
                # Évaluation des règles simples
                if item.validation_rule == "market_structure != ''":
                    if trade_data.get('market_structure'):
                        item.status = CheckItemStatus.CHECKED
                
                elif item.validation_rule == "confluence_factors includes 'support'":
                    confluence = trade_data.get('confluence_factors', [])
                    if 'support' in confluence or 'resistance' in confluence:
                        item.status = CheckItemStatus.CHECKED
                
                elif item.validation_rule == "risk_reward_ratio >= 2.0":
                    rr_ratio = trade_data.get('risk_reward_ratio', 0)
                    if rr_ratio >= 2.0:
                        item.status = CheckItemStatus.CHECKED
                
                elif item.validation_rule == "len(confluence_factors) >= 3":
                    confluence = trade_data.get('confluence_factors', [])
                    if len(confluence) >= 3:
                        item.status = CheckItemStatus.CHECKED
                
                elif item.validation_rule == "trading_session in ['london', 'ny']":
                    current_hour = datetime.now().hour
                    if 7 <= current_hour <= 16 or 13 <= current_hour <= 22:
                        item.status = CheckItemStatus.CHECKED
                
                elif item.validation_rule == "confluence_factors includes 'volume'":
                    confluence = trade_data.get('confluence_factors', [])
                    if 'volume' in confluence:
                        item.status = CheckItemStatus.CHECKED
                
            except Exception:
                # En cas d'erreur dans la règle, garder le statut manuel
                pass
    
    def create_custom_checklist(self, user_session: str, checklist_data: Dict) -> str:
        """Crée une checklist personnalisée (Premium)"""
        
        checklist_id = f"custom_{user_session}_{int(datetime.now().timestamp())}"
        
        items = []
        for item_data in checklist_data.get('items', []):
            item = ChecklistItem(
                id=item_data['id'],
                title=item_data['title'],
                description=item_data['description'],
                category=item_data.get('category', 'custom'),
                importance=item_data.get('importance', 'important'),
                is_required=item_data.get('is_required', False),
                status=CheckItemStatus.UNCHECKED,
                validation_rule=item_data.get('validation_rule'),
                help_text=item_data.get('help_text', '')
            )
            items.append(item)
        
        checklist = TradingChecklist(
            id=checklist_id,
            name=checklist_data['name'],
            description=checklist_data['description'],
            checklist_type=ChecklistType.CUSTOM,
            items=items,
            completion_score=0,
            required_score=checklist_data.get('required_score', 80),
            is_premium=True,
            created_at=datetime.now(),
            last_used=None
        )
        
        if user_session not in self.user_checklists:
            self.user_checklists[user_session] = {}
        
        self.user_checklists[user_session][checklist_id] = checklist
        
        return checklist_id
    
    def get_user_checklists(self, user_session: str) -> List[TradingChecklist]:
        """Récupère les checklists personnalisées d'un utilisateur"""
        if user_session not in self.user_checklists:
            return []
        
        return list(self.user_checklists[user_session].values())
    
    def get_checklist_stats(self, user_session: str) -> Dict:
        """Statistiques d'utilisation des checklists"""
        
        if user_session not in self.completion_history:
            return {"message": "Aucune utilisation de checklist enregistrée"}
        
        history = self.completion_history[user_session]
        
        total_uses = len(history)
        successful_validations = len([h for h in history if h['result'].is_valid_to_trade])
        avg_completion = sum(h['result'].completion_percentage for h in history) / total_uses
        
        # Checklist la plus utilisée
        checklist_usage = {}
        for entry in history:
            checklist_id = entry['result'].checklist_id
            checklist_usage[checklist_id] = checklist_usage.get(checklist_id, 0) + 1
        
        most_used = max(checklist_usage.items(), key=lambda x: x[1]) if checklist_usage else None
        
        return {
            'total_uses': total_uses,
            'successful_validations': successful_validations,
            'success_rate': f"{(successful_validations/total_uses)*100:.1f}%" if total_uses > 0 else "0%",
            'average_completion': f"{avg_completion:.1f}%",
            'most_used_checklist': most_used[0] if most_used else None,
            'discipline_score': min(100, avg_completion + (successful_validations/total_uses)*20)
        }
    
    def get_gamification_rewards(self, user_session: str) -> Dict:
        """Système de récompenses gamifié"""
        
        stats = self.get_checklist_stats(user_session)
        
        if isinstance(stats, dict) and 'message' in stats:
            return {"level": 1, "next_reward": "Utilisez votre première checklist"}
        
        total_uses = stats['total_uses']
        success_rate = float(stats['success_rate'].rstrip('%'))
        
        # Calcul du niveau
        level = min(10, 1 + (total_uses // 5))
        
        # Badges débloqués
        badges = []
        if total_uses >= 1:
            badges.append("🎯 Premier Contrôle")
        if total_uses >= 10:
            badges.append("📋 Utilisateur Régulier")
        if total_uses >= 25:
            badges.append("🏆 Maître des Checklists")
        if success_rate >= 80:
            badges.append("💎 Trader Discipliné")
        if success_rate >= 95:
            badges.append("👑 Perfectionniste")
        
        # Récompense suivante
        next_rewards = {
            1: "5 utilisations → Badge Utilisateur Régulier",
            2: "10 utilisations → Déblocage checklist avancée",
            3: "25 utilisations → Badge Maître des Checklists",
            4: "80% de réussite → Badge Trader Discipliné"
        }
        
        next_reward = next_rewards.get(level, "Maximum atteint !")
        
        return {
            'level': level,
            'badges': badges,
            'next_reward': next_reward,
            'total_uses': total_uses,
            'success_rate': f"{success_rate:.1f}%"
        }

# Instance globale du gestionnaire de checklists
checklist_manager = DynamicChecklistManager()