"""
Système d'Objectifs et Récompenses - Gamification pour traders
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class GoalType(Enum):
    TRADE_COUNT = "trade_count"
    WIN_RATE = "win_rate"
    PROFIT_TARGET = "profit_target"
    RISK_MANAGEMENT = "risk_management"
    CONSISTENCY = "consistency"
    DISCIPLINE = "discipline"
    LEARNING = "learning"
    CHECKLIST_USAGE = "checklist_usage"

class GoalPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class RewardType(Enum):
    BADGE = "badge"
    POINTS = "points"
    STREAK = "streak"
    LEVEL_UP = "level_up"
    ACHIEVEMENT = "achievement"

class BadgeRarity(Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

@dataclass
class TradingGoal:
    """Objectif de trading"""
    goal_id: str
    user_session: str
    goal_type: GoalType
    period: GoalPeriod
    
    # Configuration
    title: str
    description: str
    target_value: float
    current_value: float
    
    # Dates
    start_date: datetime
    end_date: datetime
    
    # Récompenses
    reward_points: int
    reward_badges: List[str]
    bonus_multiplier: float
    
    # État
    is_completed: bool
    completion_date: Optional[datetime]
    is_active: bool
    
    created_at: datetime

@dataclass
class Badge:
    """Badge de récompense"""
    badge_id: str
    name: str
    description: str
    icon: str
    rarity: BadgeRarity
    points_value: int
    unlock_condition: str
    category: str
    is_secret: bool

@dataclass
class UserReward:
    """Récompense utilisateur"""
    reward_id: str
    user_session: str
    reward_type: RewardType
    source_goal_id: Optional[str]
    
    # Détails
    title: str
    description: str
    points_earned: int
    badge_earned: Optional[str]
    
    earned_at: datetime

@dataclass
class UserProfile:
    """Profil utilisateur gamifié"""
    user_session: str
    
    # Niveaux et points
    level: int
    total_points: int
    points_current_level: int
    points_next_level: int
    
    # Badges
    badges_earned: List[str]
    badge_count_by_rarity: Dict[str, int]
    
    # Streaks
    current_streak: int
    longest_streak: int
    streak_type: str
    
    # Statistiques
    goals_completed: int
    goals_failed: int
    completion_rate: float
    
    # Rang
    rank_title: str
    rank_progress: float
    
    last_updated: datetime

class GoalsRewardsSystem:
    """Système de gamification avec objectifs et récompenses"""
    
    def __init__(self):
        self.user_goals = {}  # user_session -> List[TradingGoal]
        self.user_rewards = {}  # user_session -> List[UserReward]
        self.user_profiles = {}  # user_session -> UserProfile
        self.available_badges = {}  # badge_id -> Badge
        
        # Initialiser le système
        self._init_badges()
        self._init_rank_system()
        
    def _init_badges(self):
        """Initialise les badges disponibles"""
        
        badges = [
            # Badges de débutant (Common)
            Badge("first_trade", "🎯 Premier Trade", "Votre premier trade enregistré", "🎯", 
                  BadgeRarity.COMMON, 10, "complete_first_trade", "milestone", False),
            Badge("first_week", "📅 Première Semaine", "Une semaine complète de trading", "📅", 
                  BadgeRarity.COMMON, 25, "trade_for_7_days", "milestone", False),
            Badge("risk_manager", "🛡️ Gestionnaire de Risque", "Respecter 2% de risque pendant 10 trades", "🛡️", 
                  BadgeRarity.COMMON, 50, "risk_compliance_10", "discipline", False),
            
            # Badges intermédiaires (Rare)
            Badge("consistent_trader", "📊 Trader Constant", "10 trades gagnants d'affilée", "📊", 
                  BadgeRarity.RARE, 100, "winning_streak_10", "performance", False),
            Badge("profit_hunter", "💰 Chasseur de Profits", "100$ de profit en une semaine", "💰", 
                  BadgeRarity.RARE, 150, "weekly_profit_100", "performance", False),
            Badge("disciplined_mind", "🧠 Esprit Discipliné", "Utiliser les checklists 20 fois", "🧠", 
                  BadgeRarity.RARE, 75, "checklist_usage_20", "discipline", False),
            
            # Badges avancés (Epic)
            Badge("master_trader", "🏆 Maître Trader", "80% de taux de réussite sur 50 trades", "🏆", 
                  BadgeRarity.EPIC, 300, "winrate_80_over_50", "mastery", False),
            Badge("iron_discipline", "⚡ Discipline de Fer", "30 jours sans violer le plan de trading", "⚡", 
                  BadgeRarity.EPIC, 500, "discipline_streak_30", "discipline", False),
            Badge("profit_machine", "🚀 Machine à Profits", "1000$ de profit en un mois", "🚀", 
                  BadgeRarity.EPIC, 400, "monthly_profit_1000", "performance", False),
            
            # Badges légendaires (Legendary)
            Badge("trading_legend", "👑 Légende du Trading", "6 mois consécutifs profitables", "👑", 
                  BadgeRarity.LEGENDARY, 1000, "profitable_months_6", "mastery", False),
            Badge("zen_master", "🕉️ Maître Zen", "Score mental >8 pendant 30 jours", "🕉️", 
                  BadgeRarity.LEGENDARY, 750, "mental_score_8_30days", "psychology", False),
            Badge("risk_ninja", "🥷 Ninja du Risque", "100 trades sans dépasser 2% de risque", "🥷", 
                  BadgeRarity.LEGENDARY, 800, "risk_perfect_100", "discipline", True),
            
            # Badges secrets
            Badge("night_owl", "🦉 Chouette de Nuit", "10 trades profitables après 22h", "🦉", 
                  BadgeRarity.RARE, 100, "night_trading_profits", "special", True),
            Badge("monday_master", "📈 Maître du Lundi", "Lundi profitable 8 semaines consécutives", "📈", 
                  BadgeRarity.EPIC, 250, "monday_streak_8", "special", True)
        ]
        
        for badge in badges:
            self.available_badges[badge.badge_id] = badge
    
    def _init_rank_system(self):
        """Initialise le système de rangs"""
        
        self.ranks = [
            {"title": "Débutant", "min_points": 0, "max_points": 99},
            {"title": "Apprenti", "min_points": 100, "max_points": 299},
            {"title": "Trader", "min_points": 300, "max_points": 599},
            {"title": "Trader Confirmé", "min_points": 600, "max_points": 999},
            {"title": "Expert", "min_points": 1000, "max_points": 1999},
            {"title": "Maître", "min_points": 2000, "max_points": 3999},
            {"title": "Grand Maître", "min_points": 4000, "max_points": 7999},
            {"title": "Légende", "min_points": 8000, "max_points": 15999},
            {"title": "Légende Suprême", "min_points": 16000, "max_points": 99999}
        ]
    
    def create_goal(self, user_session: str, goal_data: Dict) -> str:
        """Crée un nouvel objectif"""
        
        goal_id = f"goal_{int(datetime.now().timestamp())}_{user_session}"
        
        # Calculer les dates selon la période
        start_date = datetime.now()
        if goal_data['period'] == 'daily':
            end_date = start_date + timedelta(days=1)
        elif goal_data['period'] == 'weekly':
            end_date = start_date + timedelta(weeks=1)
        elif goal_data['period'] == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:
            end_date = datetime.fromisoformat(goal_data['end_date'])
        
        # Calculer les récompenses selon le type et la difficulté
        reward_points, reward_badges = self._calculate_goal_rewards(goal_data)
        
        goal = TradingGoal(
            goal_id=goal_id,
            user_session=user_session,
            goal_type=GoalType(goal_data['goal_type']),
            period=GoalPeriod(goal_data['period']),
            title=goal_data['title'],
            description=goal_data['description'],
            target_value=goal_data['target_value'],
            current_value=0.0,
            start_date=start_date,
            end_date=end_date,
            reward_points=reward_points,
            reward_badges=reward_badges,
            bonus_multiplier=goal_data.get('bonus_multiplier', 1.0),
            is_completed=False,
            completion_date=None,
            is_active=True,
            created_at=datetime.now()
        )
        
        if user_session not in self.user_goals:
            self.user_goals[user_session] = []
        
        self.user_goals[user_session].append(goal)
        
        return goal_id
    
    def _calculate_goal_rewards(self, goal_data: Dict) -> tuple:
        """Calcule les récompenses pour un objectif"""
        
        base_points = {
            'daily': 50,
            'weekly': 200,
            'monthly': 800
        }
        
        goal_type = goal_data['goal_type']
        period = goal_data['period']
        target = goal_data['target_value']
        
        points = base_points.get(period, 100)
        badges = []
        
        # Ajustement selon le type d'objectif
        if goal_type == 'win_rate' and target >= 70:
            points *= 1.5
            badges.append('consistent_trader')
        elif goal_type == 'profit_target' and target >= 500:
            points *= 2.0
            badges.append('profit_hunter')
        elif goal_type == 'risk_management':
            points *= 1.2
            badges.append('risk_manager')
        elif goal_type == 'checklist_usage':
            badges.append('disciplined_mind')
        
        return int(points), badges
    
    def update_goal_progress(self, user_session: str, goal_type: str, value: float):
        """Met à jour la progression des objectifs"""
        
        goals = self.user_goals.get(user_session, [])
        
        for goal in goals:
            if (goal.goal_type.value == goal_type and 
                goal.is_active and not goal.is_completed and
                datetime.now() <= goal.end_date):
                
                goal.current_value += value
                
                # Vérifier si l'objectif est atteint
                if goal.current_value >= goal.target_value:
                    self._complete_goal(goal)
    
    def _complete_goal(self, goal: TradingGoal):
        """Complète un objectif et attribue les récompenses"""
        
        goal.is_completed = True
        goal.completion_date = datetime.now()
        
        # Calculer les points avec bonus
        points_earned = int(goal.reward_points * goal.bonus_multiplier)
        
        # Créer la récompense
        reward = UserReward(
            reward_id=f"reward_{int(datetime.now().timestamp())}",
            user_session=goal.user_session,
            reward_type=RewardType.POINTS,
            source_goal_id=goal.goal_id,
            title=f"Objectif accompli: {goal.title}",
            description=f"Félicitations ! Vous avez atteint votre objectif.",
            points_earned=points_earned,
            badge_earned=None,
            earned_at=datetime.now()
        )
        
        # Sauvegarder la récompense
        if goal.user_session not in self.user_rewards:
            self.user_rewards[goal.user_session] = []
        
        self.user_rewards[goal.user_session].append(reward)
        
        # Mettre à jour le profil utilisateur
        self._update_user_profile(goal.user_session, points_earned)
        
        # Vérifier les badges à débloquer
        self._check_badge_unlocks(goal.user_session, goal)
    
    def _update_user_profile(self, user_session: str, points_earned: int):
        """Met à jour le profil utilisateur"""
        
        if user_session not in self.user_profiles:
            self.user_profiles[user_session] = UserProfile(
                user_session=user_session,
                level=1,
                total_points=0,
                points_current_level=0,
                points_next_level=100,
                badges_earned=[],
                badge_count_by_rarity={r.value: 0 for r in BadgeRarity},
                current_streak=0,
                longest_streak=0,
                streak_type="goals",
                goals_completed=0,
                goals_failed=0,
                completion_rate=0.0,
                rank_title="Débutant",
                rank_progress=0.0,
                last_updated=datetime.now()
            )
        
        profile = self.user_profiles[user_session]
        
        # Ajouter les points
        profile.total_points += points_earned
        profile.points_current_level += points_earned
        
        # Vérifier le niveau
        self._check_level_up(profile)
        
        # Mettre à jour les statistiques d'objectifs
        profile.goals_completed += 1
        goals = self.user_goals.get(user_session, [])
        total_goals = len(goals)
        profile.completion_rate = (profile.goals_completed / total_goals * 100) if total_goals > 0 else 0
        
        # Mettre à jour le rang
        self._update_rank(profile)
        
        profile.last_updated = datetime.now()
    
    def _check_level_up(self, profile: UserProfile):
        """Vérifie et gère les montées de niveau"""
        
        while profile.points_current_level >= profile.points_next_level:
            profile.points_current_level -= profile.points_next_level
            profile.level += 1
            
            # Calculer les points nécessaires pour le niveau suivant
            profile.points_next_level = self._calculate_points_for_level(profile.level + 1)
            
            # Créer une récompense de montée de niveau
            level_reward = UserReward(
                reward_id=f"levelup_{int(datetime.now().timestamp())}",
                user_session=profile.user_session,
                reward_type=RewardType.LEVEL_UP,
                source_goal_id=None,
                title=f"🎉 Niveau {profile.level} !",
                description=f"Félicitations ! Vous avez atteint le niveau {profile.level}",
                points_earned=0,
                badge_earned=None,
                earned_at=datetime.now()
            )
            
            if profile.user_session not in self.user_rewards:
                self.user_rewards[profile.user_session] = []
            
            self.user_rewards[profile.user_session].append(level_reward)
    
    def _calculate_points_for_level(self, level: int) -> int:
        """Calcule les points nécessaires pour un niveau"""
        return int(100 * (1.2 ** (level - 1)))
    
    def _update_rank(self, profile: UserProfile):
        """Met à jour le rang de l'utilisateur"""
        
        for rank in self.ranks:
            if rank['min_points'] <= profile.total_points <= rank['max_points']:
                profile.rank_title = rank['title']
                
                # Calculer le progrès dans ce rang
                points_in_rank = profile.total_points - rank['min_points']
                rank_span = rank['max_points'] - rank['min_points']
                profile.rank_progress = (points_in_rank / rank_span * 100) if rank_span > 0 else 100
                
                break
    
    def _check_badge_unlocks(self, user_session: str, completed_goal: TradingGoal):
        """Vérifie les badges à débloquer"""
        
        # Logique simplifiée - en production, analyser l'historique complet
        badges_to_unlock = []
        
        # Vérifier selon le type d'objectif complété
        if completed_goal.goal_type == GoalType.RISK_MANAGEMENT:
            badges_to_unlock.append('risk_manager')
        elif completed_goal.goal_type == GoalType.PROFIT_TARGET:
            badges_to_unlock.append('profit_hunter')
        elif completed_goal.goal_type == GoalType.CHECKLIST_USAGE:
            badges_to_unlock.append('disciplined_mind')
        
        # Débloquer les badges
        for badge_id in badges_to_unlock:
            self._unlock_badge(user_session, badge_id)
    
    def _unlock_badge(self, user_session: str, badge_id: str):
        """Débloque un badge pour l'utilisateur"""
        
        badge = self.available_badges.get(badge_id)
        if not badge:
            return
        
        profile = self.user_profiles.get(user_session)
        if not profile:
            return
        
        # Vérifier si le badge n'est pas déjà débloqué
        if badge_id in profile.badges_earned:
            return
        
        # Ajouter le badge
        profile.badges_earned.append(badge_id)
        profile.badge_count_by_rarity[badge.rarity.value] += 1
        
        # Créer la récompense de badge
        badge_reward = UserReward(
            reward_id=f"badge_{int(datetime.now().timestamp())}",
            user_session=user_session,
            reward_type=RewardType.BADGE,
            source_goal_id=None,
            title=f"🏅 Badge débloqué: {badge.name}",
            description=badge.description,
            points_earned=badge.points_value,
            badge_earned=badge_id,
            earned_at=datetime.now()
        )
        
        if user_session not in self.user_rewards:
            self.user_rewards[user_session] = []
        
        self.user_rewards[user_session].append(badge_reward)
        
        # Ajouter les points du badge
        profile.total_points += badge.points_value
        profile.points_current_level += badge.points_value
        
        # Vérifier montée de niveau
        self._check_level_up(profile)
    
    def get_suggested_goals(self, user_session: str) -> List[Dict]:
        """Génère des suggestions d'objectifs personnalisés"""
        
        suggestions = []
        
        # Objectifs de base pour tous les utilisateurs
        base_goals = [
            {
                'goal_type': 'trade_count',
                'period': 'weekly',
                'title': '🎯 5 Trades Cette Semaine',
                'description': 'Effectuez 5 trades bien analysés cette semaine',
                'target_value': 5,
                'difficulty': 'facile'
            },
            {
                'goal_type': 'risk_management',
                'period': 'weekly',
                'title': '🛡️ Maîtriser le Risque',
                'description': 'Ne pas dépasser 2% de risque par trade pendant 7 jours',
                'target_value': 7,
                'difficulty': 'moyen'
            },
            {
                'goal_type': 'checklist_usage',
                'period': 'weekly',
                'title': '📋 Utiliser les Checklists',
                'description': 'Compléter 5 checklists avant vos trades',
                'target_value': 5,
                'difficulty': 'facile'
            }
        ]
        
        # Objectifs avancés basés sur l'historique
        profile = self.user_profiles.get(user_session)
        if profile and profile.level >= 3:
            advanced_goals = [
                {
                    'goal_type': 'win_rate',
                    'period': 'weekly',
                    'title': '📈 70% de Réussite',
                    'description': 'Atteindre 70% de taux de réussite sur 10 trades',
                    'target_value': 70,
                    'difficulty': 'difficile'
                },
                {
                    'goal_type': 'profit_target',
                    'period': 'monthly',
                    'title': '💰 Objectif 500€',
                    'description': 'Générer 500€ de profit ce mois',
                    'target_value': 500,
                    'difficulty': 'difficile'
                }
            ]
            base_goals.extend(advanced_goals)
        
        # Filtrer les objectifs déjà actifs
        active_goal_types = set()
        active_goals = self.get_active_goals(user_session)
        for goal in active_goals:
            active_goal_types.add(goal['goal_type'])
        
        for goal_data in base_goals:
            if goal_data['goal_type'] not in active_goal_types:
                suggestions.append(goal_data)
        
        return suggestions[:4]  # Maximum 4 suggestions
    
    def get_active_goals(self, user_session: str) -> List[Dict]:
        """Récupère les objectifs actifs"""
        
        goals = self.user_goals.get(user_session, [])
        active_goals = []
        
        for goal in goals:
            if goal.is_active and not goal.is_completed and datetime.now() <= goal.end_date:
                active_goals.append(self._goal_to_dict(goal))
        
        return active_goals
    
    def get_user_profile(self, user_session: str) -> Dict:
        """Récupère le profil gamifié de l'utilisateur"""
        
        profile = self.user_profiles.get(user_session)
        if not profile:
            # Créer un profil par défaut
            profile = UserProfile(
                user_session=user_session,
                level=1,
                total_points=0,
                points_current_level=0,
                points_next_level=100,
                badges_earned=[],
                badge_count_by_rarity={r.value: 0 for r in BadgeRarity},
                current_streak=0,
                longest_streak=0,
                streak_type="goals",
                goals_completed=0,
                goals_failed=0,
                completion_rate=0.0,
                rank_title="Débutant",
                rank_progress=0.0,
                last_updated=datetime.now()
            )
            self.user_profiles[user_session] = profile
        
        return self._profile_to_dict(profile)
    
    def get_recent_rewards(self, user_session: str, days: int = 7) -> List[Dict]:
        """Récupère les récompenses récentes"""
        
        rewards = self.user_rewards.get(user_session, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_rewards = [
            reward for reward in rewards 
            if reward.earned_at > cutoff
        ]
        
        return [self._reward_to_dict(reward) for reward in recent_rewards]
    
    def get_leaderboard(self, metric: str = 'points', limit: int = 10) -> List[Dict]:
        """Récupère le classement des utilisateurs"""
        
        profiles = list(self.user_profiles.values())
        
        if metric == 'points':
            profiles.sort(key=lambda p: p.total_points, reverse=True)
        elif metric == 'level':
            profiles.sort(key=lambda p: p.level, reverse=True)
        elif metric == 'completion_rate':
            profiles.sort(key=lambda p: p.completion_rate, reverse=True)
        
        leaderboard = []
        for i, profile in enumerate(profiles[:limit]):
            leaderboard.append({
                'rank': i + 1,
                'user_session': profile.user_session[:8] + "...",  # Anonymisé
                'level': profile.level,
                'total_points': profile.total_points,
                'rank_title': profile.rank_title,
                'badge_count': len(profile.badges_earned),
                'completion_rate': profile.completion_rate
            })
        
        return leaderboard
    
    def _goal_to_dict(self, goal: TradingGoal) -> Dict:
        """Convertit un objectif en dictionnaire"""
        
        progress_percentage = (goal.current_value / goal.target_value * 100) if goal.target_value > 0 else 0
        
        return {
            'goal_id': goal.goal_id,
            'goal_type': goal.goal_type.value,
            'period': goal.period.value,
            'title': goal.title,
            'description': goal.description,
            'target_value': goal.target_value,
            'current_value': goal.current_value,
            'progress_percentage': min(100, round(progress_percentage, 1)),
            'start_date': goal.start_date.isoformat(),
            'end_date': goal.end_date.isoformat(),
            'reward_points': goal.reward_points,
            'is_completed': goal.is_completed,
            'is_active': goal.is_active,
            'days_remaining': (goal.end_date - datetime.now()).days if goal.end_date > datetime.now() else 0
        }
    
    def _profile_to_dict(self, profile: UserProfile) -> Dict:
        """Convertit un profil en dictionnaire"""
        
        return {
            'level': profile.level,
            'total_points': profile.total_points,
            'points_current_level': profile.points_current_level,
            'points_next_level': profile.points_next_level,
            'level_progress': round((profile.points_current_level / profile.points_next_level * 100), 1),
            'badges_earned': profile.badges_earned,
            'badge_count_total': len(profile.badges_earned),
            'badge_count_by_rarity': profile.badge_count_by_rarity,
            'current_streak': profile.current_streak,
            'longest_streak': profile.longest_streak,
            'goals_completed': profile.goals_completed,
            'completion_rate': round(profile.completion_rate, 1),
            'rank_title': profile.rank_title,
            'rank_progress': round(profile.rank_progress, 1),
            'last_updated': profile.last_updated.isoformat()
        }
    
    def _reward_to_dict(self, reward: UserReward) -> Dict:
        """Convertit une récompense en dictionnaire"""
        
        return {
            'reward_id': reward.reward_id,
            'reward_type': reward.reward_type.value,
            'title': reward.title,
            'description': reward.description,
            'points_earned': reward.points_earned,
            'badge_earned': reward.badge_earned,
            'earned_at': reward.earned_at.isoformat()
        }
    
    def get_available_badges(self) -> List[Dict]:
        """Récupère la liste des badges disponibles"""
        
        return [
            {
                'badge_id': badge.badge_id,
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'rarity': badge.rarity.value,
                'points_value': badge.points_value,
                'category': badge.category,
                'is_secret': badge.is_secret
            }
            for badge in self.available_badges.values()
            if not badge.is_secret  # Masquer les badges secrets
        ]

# Instance globale du système d'objectifs et récompenses
goals_rewards_system = GoalsRewardsSystem()