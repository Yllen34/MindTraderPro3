"""
Système de Blocage Trading - Mode silence et prévention de l'overtrading
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class BlockerType(Enum):
    OVERTRADING_PROTECTION = "overtrading_protection"
    EMOTIONAL_COOLDOWN = "emotional_cooldown"
    LOSS_STREAK_PROTECTION = "loss_streak_protection"
    DAILY_LIMIT_REACHED = "daily_limit_reached"
    MANUAL_PAUSE = "manual_pause"
    REFLECTION_REQUIRED = "reflection_required"

class BlockerSeverity(Enum):
    SOFT_WARNING = "soft_warning"  # Warning mais permet de continuer
    MODERATE_BLOCK = "moderate_block"  # Blocage avec possibilité d'override
    HARD_BLOCK = "hard_block"  # Blocage strict sans override

@dataclass
class TradingBlock:
    """Blocage de trading actif"""
    block_id: str
    user_session: str
    blocker_type: BlockerType
    severity: BlockerSeverity
    
    # Configuration
    title: str
    message: str
    reason: str
    
    # Durée
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    
    # Conditions de levée
    can_override: bool
    override_conditions: List[str]
    reflection_required: bool
    checklist_required: bool
    
    # Métadonnées
    triggered_by: str
    trigger_data: Dict[str, Any]
    
    # État
    is_active: bool
    override_attempts: int
    reflection_completed: bool
    
    created_at: datetime

@dataclass
class ReflectionQuestion:
    """Question de réflexion pour débloquer"""
    question_id: str
    question_text: str
    question_type: str  # text, choice, scale
    options: List[str]
    required: bool
    category: str

@dataclass
class UserReflection:
    """Réflexion utilisateur complétée"""
    reflection_id: str
    user_session: str
    block_id: str
    
    questions_answers: Dict[str, Any]
    insights_gained: List[str]
    commitments_made: List[str]
    
    completed_at: datetime
    quality_score: float

class TradingBlockerSystem:
    """Système de protection contre l'overtrading"""
    
    def __init__(self):
        self.active_blocks = {}  # user_session -> List[TradingBlock]
        self.user_settings = {}  # user_session -> protection_settings
        self.reflection_history = {}  # user_session -> List[UserReflection]
        
        # Initialiser les questions de réflexion
        self._init_reflection_questions()
        
    def _init_reflection_questions(self):
        """Initialise les questions de réflexion"""
        
        self.reflection_questions = {
            'overtrading': [
                ReflectionQuestion(
                    question_id="overtrading_reason",
                    question_text="Pourquoi ressentez-vous le besoin de trader autant aujourd'hui ?",
                    question_type="text",
                    options=[],
                    required=True,
                    category="self_awareness"
                ),
                ReflectionQuestion(
                    question_id="overtrading_trigger",
                    question_text="Qu'est-ce qui vous pousse à continuer de trader ?",
                    question_type="choice",
                    options=[
                        "Récupérer une perte récente",
                        "L'excitation du trading",
                        "Peur de rater une opportunité",
                        "Ennui ou habitude",
                        "Pression financière"
                    ],
                    required=True,
                    category="triggers"
                ),
                ReflectionQuestion(
                    question_id="overtrading_plan",
                    question_text="Sur une échelle de 1 à 10, à quel point respectez-vous votre plan de trading aujourd'hui ?",
                    question_type="scale",
                    options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    required=True,
                    category="discipline"
                )
            ],
            'emotional': [
                ReflectionQuestion(
                    question_id="emotion_current",
                    question_text="Comment vous sentez-vous en ce moment ?",
                    question_type="choice",
                    options=["Calme", "Anxieux", "Frustré", "En colère", "Euphorique", "Déprimé"],
                    required=True,
                    category="emotions"
                ),
                ReflectionQuestion(
                    question_id="emotion_impact",
                    question_text="Comment cet état émotionnel affecte-t-il vos décisions de trading ?",
                    question_type="text",
                    options=[],
                    required=True,
                    category="self_awareness"
                ),
                ReflectionQuestion(
                    question_id="emotion_strategy",
                    question_text="Quelle technique allez-vous utiliser pour retrouver votre équilibre ?",
                    question_type="choice",
                    options=[
                        "Respiration profonde",
                        "Pause de 15 minutes",
                        "Exercice physique",
                        "Méditation",
                        "Arrêter de trader aujourd'hui"
                    ],
                    required=True,
                    category="coping"
                )
            ],
            'loss_streak': [
                ReflectionQuestion(
                    question_id="loss_analysis",
                    question_text="Analysez vos dernières pertes. Quel pattern voyez-vous ?",
                    question_type="text",
                    options=[],
                    required=True,
                    category="analysis"
                ),
                ReflectionQuestion(
                    question_id="loss_mistake",
                    question_text="Quelle erreur principale répétez-vous ?",
                    question_type="choice",
                    options=[
                        "Ne pas respecter le stop loss",
                        "Taille de position trop grande",
                        "Trading contre la tendance",
                        "Entrées précipitées",
                        "Trading des news"
                    ],
                    required=True,
                    category="mistakes"
                ),
                ReflectionQuestion(
                    question_id="loss_action",
                    question_text="Que devez-vous changer concrètement ?",
                    question_type="text",
                    options=[],
                    required=True,
                    category="action_plan"
                )
            ]
        }
    
    def configure_user_protection(self, user_session: str, settings: Dict) -> Dict:
        """Configure les paramètres de protection d'un utilisateur"""
        
        default_settings = {
            'max_daily_trades': 5,
            'max_losing_streak': 3,
            'daily_loss_limit_percent': 5.0,
            'emotional_cooldown_minutes': 30,
            'overtrading_threshold': 8,  # Trades en une session
            'auto_pause_enabled': True,
            'reflection_required': True,
            'hard_block_enabled': True
        }
        
        # Merger avec les paramètres utilisateur
        user_settings = {**default_settings, **settings}
        self.user_settings[user_session] = user_settings
        
        return {
            'success': True,
            'settings': user_settings,
            'message': 'Paramètres de protection configurés'
        }
    
    def check_trading_allowed(self, user_session: str, trade_data: Dict) -> Dict:
        """Vérifie si le trading est autorisé pour cet utilisateur"""
        
        # Vérifier les blocages actifs
        active_blocks = self._get_active_blocks(user_session)
        
        if active_blocks:
            return {
                'allowed': False,
                'blocked': True,
                'blocks': [self._block_to_dict(block) for block in active_blocks],
                'message': 'Trading bloqué - Résolvez les blocages actifs'
            }
        
        # Vérifier les conditions de déclenchement
        settings = self.user_settings.get(user_session, {})
        if not settings:
            return {'allowed': True, 'blocked': False}
        
        # Analyser les conditions actuelles
        triggers = self._analyze_trigger_conditions(user_session, trade_data, settings)
        
        if triggers:
            # Déclencher des blocages
            for trigger in triggers:
                self._create_block(user_session, trigger)
            
            active_blocks = self._get_active_blocks(user_session)
            return {
                'allowed': False,
                'blocked': True,
                'blocks': [self._block_to_dict(block) for block in active_blocks],
                'message': 'Blocages déclenchés pour votre protection'
            }
        
        return {'allowed': True, 'blocked': False}
    
    def _analyze_trigger_conditions(self, user_session: str, trade_data: Dict, settings: Dict) -> List[Dict]:
        """Analyse les conditions qui pourraient déclencher un blocage"""
        
        triggers = []
        
        # Simuler l'analyse des données de trading récentes
        recent_trades = self._get_recent_trades_simulation(user_session)
        
        # 1. Vérifier l'overtrading
        trades_today = len([t for t in recent_trades if t.get('today', False)])
        if trades_today >= settings.get('overtrading_threshold', 8):
            triggers.append({
                'type': BlockerType.OVERTRADING_PROTECTION,
                'severity': BlockerSeverity.MODERATE_BLOCK,
                'duration': 60,  # 1 heure
                'data': {'trades_today': trades_today, 'threshold': settings['overtrading_threshold']}
            })
        
        # 2. Vérifier les pertes consécutives
        recent_losses = [t for t in recent_trades[-5:] if t.get('profit_loss', 0) < 0]
        if len(recent_losses) >= settings.get('max_losing_streak', 3):
            triggers.append({
                'type': BlockerType.LOSS_STREAK_PROTECTION,
                'severity': BlockerSeverity.HARD_BLOCK,
                'duration': 120,  # 2 heures
                'data': {'consecutive_losses': len(recent_losses), 'threshold': settings['max_losing_streak']}
            })
        
        # 3. Vérifier la limite de perte quotidienne
        daily_loss = sum(t.get('profit_loss', 0) for t in recent_trades if t.get('today', False) and t.get('profit_loss', 0) < 0)
        if abs(daily_loss) > (settings.get('daily_loss_limit_percent', 5.0) * 1000):  # Simulation: 1000€ capital
            triggers.append({
                'type': BlockerType.DAILY_LIMIT_REACHED,
                'severity': BlockerSeverity.HARD_BLOCK,
                'duration': 1440,  # 24 heures
                'data': {'daily_loss': daily_loss, 'limit': settings['daily_loss_limit_percent']}
            })
        
        # 4. Vérifier l'état émotionnel (simulation)
        emotional_state = self._get_emotional_state_simulation(user_session)
        if emotional_state.get('stress_level', 0) > 8:
            triggers.append({
                'type': BlockerType.EMOTIONAL_COOLDOWN,
                'severity': BlockerSeverity.MODERATE_BLOCK,
                'duration': settings.get('emotional_cooldown_minutes', 30),
                'data': {'stress_level': emotional_state['stress_level']}
            })
        
        return triggers
    
    def _create_block(self, user_session: str, trigger_data: Dict):
        """Crée un nouveau blocage"""
        
        block_id = f"block_{int(datetime.now().timestamp())}_{user_session}"
        block_type = trigger_data['type']
        severity = trigger_data['severity']
        duration = trigger_data['duration']
        
        # Personnaliser le message selon le type
        messages = {
            BlockerType.OVERTRADING_PROTECTION: {
                'title': '🛑 Protection Overtrading',
                'message': f"Vous avez déjà effectué {trigger_data['data']['trades_today']} trades aujourd'hui.",
                'reason': 'Prévention de l\'overtrading'
            },
            BlockerType.LOSS_STREAK_PROTECTION: {
                'title': '🚨 Protection Série de Pertes',
                'message': f"Vous avez {trigger_data['data']['consecutive_losses']} pertes consécutives.",
                'reason': 'Protection après série de pertes'
            },
            BlockerType.DAILY_LIMIT_REACHED: {
                'title': '⛔ Limite Quotidienne Atteinte',
                'message': f"Vous avez atteint votre limite de perte quotidienne.",
                'reason': 'Protection du capital'
            },
            BlockerType.EMOTIONAL_COOLDOWN: {
                'title': '🧠 Pause Émotionnelle',
                'message': "Votre niveau de stress est élevé. Prenez du recul.",
                'reason': 'Protection psychologique'
            }
        }
        
        message_data = messages.get(block_type, {
            'title': '⏸️ Pause Trading',
            'message': 'Trading temporairement suspendu',
            'reason': 'Protection générale'
        })
        
        # Définir les conditions d'override
        can_override = severity != BlockerSeverity.HARD_BLOCK
        override_conditions = []
        reflection_required = True
        
        if can_override:
            if block_type == BlockerType.OVERTRADING_PROTECTION:
                override_conditions = [
                    "Attendre 30 minutes",
                    "Compléter une réflexion sur votre stratégie",
                    "Réduire la taille de position de 50%"
                ]
            elif block_type == BlockerType.EMOTIONAL_COOLDOWN:
                override_conditions = [
                    "Exercice de respiration (5 min)",
                    "Score mental > 7",
                    "Attendre 15 minutes"
                ]
        
        block = TradingBlock(
            block_id=block_id,
            user_session=user_session,
            blocker_type=block_type,
            severity=severity,
            title=message_data['title'],
            message=message_data['message'],
            reason=message_data['reason'],
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=duration),
            duration_minutes=duration,
            can_override=can_override,
            override_conditions=override_conditions,
            reflection_required=reflection_required,
            checklist_required=block_type == BlockerType.LOSS_STREAK_PROTECTION,
            triggered_by=block_type.value,
            trigger_data=trigger_data['data'],
            is_active=True,
            override_attempts=0,
            reflection_completed=False,
            created_at=datetime.now()
        )
        
        if user_session not in self.active_blocks:
            self.active_blocks[user_session] = []
        
        self.active_blocks[user_session].append(block)
    
    def attempt_override(self, user_session: str, block_id: str, override_data: Dict) -> Dict:
        """Tentative d'override d'un blocage"""
        
        block = self._get_block_by_id(user_session, block_id)
        if not block:
            return {
                'success': False,
                'error': 'Blocage introuvable'
            }
        
        if not block.can_override:
            return {
                'success': False,
                'error': 'Ce blocage ne peut pas être contourné',
                'message': 'Veuillez attendre la fin du blocage'
            }
        
        block.override_attempts += 1
        
        # Vérifier les conditions d'override
        if block.reflection_required and not block.reflection_completed:
            return {
                'success': False,
                'error': 'Réflexion requise',
                'message': 'Complétez d\'abord la réflexion obligatoire',
                'action_required': 'reflection'
            }
        
        # Vérifier les conditions spécifiques
        conditions_met = self._check_override_conditions(block, override_data)
        
        if not conditions_met['all_met']:
            return {
                'success': False,
                'error': 'Conditions non remplies',
                'missing_conditions': conditions_met['missing'],
                'message': 'Toutes les conditions doivent être remplies'
            }
        
        # Override réussi
        block.is_active = False
        
        return {
            'success': True,
            'message': 'Blocage levé avec succès',
            'warning': 'Restez discipliné et respectez votre plan'
        }
    
    def submit_reflection(self, user_session: str, block_id: str, reflection_data: Dict) -> Dict:
        """Soumet une réflexion pour débloquer"""
        
        block = self._get_block_by_id(user_session, block_id)
        if not block:
            return {
                'success': False,
                'error': 'Blocage introuvable'
            }
        
        # Récupérer les questions appropriées
        question_category = self._get_question_category(block.blocker_type)
        questions = self.reflection_questions.get(question_category, [])
        
        # Valider les réponses
        validation_result = self._validate_reflection_answers(questions, reflection_data)
        
        if not validation_result['valid']:
            return {
                'success': False,
                'error': 'Réflexion incomplète',
                'missing_questions': validation_result['missing']
            }
        
        # Créer l'enregistrement de réflexion
        reflection_id = f"reflection_{int(datetime.now().timestamp())}"
        
        reflection = UserReflection(
            reflection_id=reflection_id,
            user_session=user_session,
            block_id=block_id,
            questions_answers=reflection_data,
            insights_gained=reflection_data.get('insights', []),
            commitments_made=reflection_data.get('commitments', []),
            completed_at=datetime.now(),
            quality_score=self._calculate_reflection_quality(reflection_data)
        )
        
        # Sauvegarder la réflexion
        if user_session not in self.reflection_history:
            self.reflection_history[user_session] = []
        
        self.reflection_history[user_session].append(reflection)
        
        # Marquer la réflexion comme complétée sur le blocage
        block.reflection_completed = True
        
        return {
            'success': True,
            'reflection_id': reflection_id,
            'quality_score': reflection.quality_score,
            'message': 'Réflexion complétée avec succès',
            'can_override_now': block.can_override
        }
    
    def create_manual_pause(self, user_session: str, duration_minutes: int, reason: str = "") -> Dict:
        """Crée une pause manuelle"""
        
        block_id = f"manual_{int(datetime.now().timestamp())}_{user_session}"
        
        block = TradingBlock(
            block_id=block_id,
            user_session=user_session,
            blocker_type=BlockerType.MANUAL_PAUSE,
            severity=BlockerSeverity.SOFT_WARNING,
            title="⏸️ Pause Volontaire",
            message=f"Pause de {duration_minutes} minutes activée",
            reason=reason or "Pause volontaire",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=duration_minutes),
            duration_minutes=duration_minutes,
            can_override=True,
            override_conditions=["Désactiver manuellement"],
            reflection_required=False,
            checklist_required=False,
            triggered_by="manual",
            trigger_data={'duration': duration_minutes, 'reason': reason},
            is_active=True,
            override_attempts=0,
            reflection_completed=True,
            created_at=datetime.now()
        )
        
        if user_session not in self.active_blocks:
            self.active_blocks[user_session] = []
        
        self.active_blocks[user_session].append(block)
        
        return {
            'success': True,
            'block_id': block_id,
            'message': f'Pause de {duration_minutes} minutes activée'
        }
    
    def _get_active_blocks(self, user_session: str) -> List[TradingBlock]:
        """Récupère les blocages actifs d'un utilisateur"""
        
        blocks = self.active_blocks.get(user_session, [])
        active_blocks = []
        
        for block in blocks:
            if block.is_active and datetime.now() < block.end_time:
                active_blocks.append(block)
            elif datetime.now() >= block.end_time:
                block.is_active = False  # Expirer automatiquement
        
        return active_blocks
    
    def _get_block_by_id(self, user_session: str, block_id: str) -> Optional[TradingBlock]:
        """Récupère un blocage par son ID"""
        
        blocks = self.active_blocks.get(user_session, [])
        return next((block for block in blocks if block.block_id == block_id), None)
    
    def _get_question_category(self, blocker_type: BlockerType) -> str:
        """Détermine la catégorie de questions selon le type de blocage"""
        
        mapping = {
            BlockerType.OVERTRADING_PROTECTION: 'overtrading',
            BlockerType.EMOTIONAL_COOLDOWN: 'emotional',
            BlockerType.LOSS_STREAK_PROTECTION: 'loss_streak',
            BlockerType.DAILY_LIMIT_REACHED: 'loss_streak'
        }
        
        return mapping.get(blocker_type, 'overtrading')
    
    def _validate_reflection_answers(self, questions: List[ReflectionQuestion], answers: Dict) -> Dict:
        """Valide les réponses de réflexion"""
        
        missing = []
        
        for question in questions:
            if question.required and question.question_id not in answers:
                missing.append(question.question_id)
        
        return {
            'valid': len(missing) == 0,
            'missing': missing
        }
    
    def _calculate_reflection_quality(self, reflection_data: Dict) -> float:
        """Calcule la qualité d'une réflexion"""
        
        base_score = 0.5
        
        # Bonus pour des réponses détaillées
        for answer in reflection_data.values():
            if isinstance(answer, str) and len(answer) > 50:
                base_score += 0.1
        
        # Bonus pour des insights
        if reflection_data.get('insights'):
            base_score += 0.2
        
        # Bonus pour des engagements concrets
        if reflection_data.get('commitments'):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _check_override_conditions(self, block: TradingBlock, override_data: Dict) -> Dict:
        """Vérifie si les conditions d'override sont remplies"""
        
        all_met = True
        missing = []
        
        # Vérifications basiques selon le type
        if block.blocker_type == BlockerType.EMOTIONAL_COOLDOWN:
            if override_data.get('mental_score', 0) < 7:
                all_met = False
                missing.append("Score mental < 7")
        
        # Vérifier la durée minimale écoulée
        min_duration = timedelta(minutes=15)  # 15 minutes minimum
        if datetime.now() - block.start_time < min_duration:
            all_met = False
            missing.append("Durée minimale non écoulée")
        
        return {
            'all_met': all_met,
            'missing': missing
        }
    
    def _get_recent_trades_simulation(self, user_session: str) -> List[Dict]:
        """Simulation des trades récents"""
        
        # En production, récupérer les vrais trades
        return [
            {'profit_loss': -50, 'today': True},
            {'profit_loss': -30, 'today': True},
            {'profit_loss': -25, 'today': True},
            {'profit_loss': 100, 'today': False},
            {'profit_loss': -75, 'today': True}
        ]
    
    def _get_emotional_state_simulation(self, user_session: str) -> Dict:
        """Simulation de l'état émotionnel"""
        
        # En production, récupérer le vrai état émotionnel
        return {
            'stress_level': 6,
            'confidence_level': 4,
            'last_update': datetime.now()
        }
    
    def get_user_blocks(self, user_session: str, include_inactive: bool = False) -> List[Dict]:
        """Récupère les blocages d'un utilisateur"""
        
        blocks = self.active_blocks.get(user_session, [])
        
        if not include_inactive:
            blocks = self._get_active_blocks(user_session)
        
        return [self._block_to_dict(block) for block in blocks]
    
    def get_reflection_questions(self, blocker_type: str) -> List[Dict]:
        """Récupère les questions de réflexion pour un type de blocage"""
        
        category = self._get_question_category(BlockerType(blocker_type))
        questions = self.reflection_questions.get(category, [])
        
        return [
            {
                'question_id': q.question_id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'options': q.options,
                'required': q.required,
                'category': q.category
            }
            for q in questions
        ]
    
    def _block_to_dict(self, block: TradingBlock) -> Dict:
        """Convertit un blocage en dictionnaire"""
        
        time_remaining = max(0, (block.end_time - datetime.now()).total_seconds() / 60)
        
        return {
            'block_id': block.block_id,
            'blocker_type': block.blocker_type.value,
            'severity': block.severity.value,
            'title': block.title,
            'message': block.message,
            'reason': block.reason,
            'start_time': block.start_time.isoformat(),
            'end_time': block.end_time.isoformat(),
            'duration_minutes': block.duration_minutes,
            'time_remaining_minutes': int(time_remaining),
            'can_override': block.can_override,
            'override_conditions': block.override_conditions,
            'reflection_required': block.reflection_required,
            'reflection_completed': block.reflection_completed,
            'checklist_required': block.checklist_required,
            'trigger_data': block.trigger_data,
            'is_active': block.is_active,
            'override_attempts': block.override_attempts
        }

# Instance globale du système de blocage
trading_blocker_system = TradingBlockerSystem()