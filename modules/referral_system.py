"""
Système de Parrainage - Réductions progressives et fonctionnalités exclusives
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid

class ReferralTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    LEGENDARY = "legendary"

class ReferralStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREMIUM_CONVERTED = "premium_converted"
    CHURNED = "churned"

@dataclass
class ReferralReward:
    """Récompense de parrainage"""
    reward_id: str
    tier: ReferralTier
    min_referrals: int
    
    # Réductions d'abonnement
    discount_percent: float
    months_free: int
    lifetime_unlock: bool
    
    # Fonctionnalités exclusives
    exclusive_features: List[str]
    priority_support: bool
    beta_access: bool
    
    # Récompenses spéciales
    bonus_credits: int
    special_badge: str
    custom_title: str
    
    # Description
    name: str
    description: str
    icon: str

@dataclass
class ReferralCode:
    """Code de parrainage"""
    code: str
    user_session: str
    created_at: datetime
    expires_at: Optional[datetime]
    usage_limit: Optional[int]
    usage_count: int
    is_active: bool
    custom_message: Optional[str]

@dataclass
class Referral:
    """Parrainage effectué"""
    referral_id: str
    referrer_session: str
    referred_session: str
    referral_code: str
    
    # Dates importantes
    referred_at: datetime
    confirmed_at: Optional[datetime]
    premium_converted_at: Optional[datetime]
    
    # Statut et récompenses
    status: ReferralStatus
    rewards_given: List[str]
    
    # Métadonnées
    referrer_ip: Optional[str]
    referred_ip: Optional[str]
    source: str  # web, mobile, social

@dataclass
class ReferralStats:
    """Statistiques de parrainage"""
    user_session: str
    
    # Compteurs
    total_referrals: int
    confirmed_referrals: int
    premium_conversions: int
    active_referrals: int
    
    # Tier actuel
    current_tier: ReferralTier
    next_tier: Optional[ReferralTier]
    referrals_to_next_tier: int
    
    # Économies
    total_discount_earned: float
    lifetime_savings: float
    current_monthly_discount: float
    
    # Récompenses
    unlocked_features: List[str]
    earned_rewards: List[str]
    
    last_updated: datetime

class ReferralSystem:
    """Système de parrainage avec progression"""
    
    def __init__(self):
        self.referral_codes = {}  # code -> ReferralCode
        self.user_codes = {}  # user_session -> List[ReferralCode]
        self.referrals = {}  # user_session -> List[Referral]
        self.referral_stats = {}  # user_session -> ReferralStats
        
        # Initialiser les tiers et récompenses
        self._init_referral_tiers()
        
    def _init_referral_tiers(self):
        """Initialise les tiers de parrainage et leurs récompenses"""
        
        self.referral_tiers = {
            ReferralTier.BRONZE: ReferralReward(
                reward_id="bronze_tier",
                tier=ReferralTier.BRONZE,
                min_referrals=1,
                discount_percent=10.0,
                months_free=0,
                lifetime_unlock=False,
                exclusive_features=["priority_customer_service"],
                priority_support=True,
                beta_access=False,
                bonus_credits=50,
                special_badge="🥉 Ambassadeur Bronze",
                custom_title="Ambassadeur Bronze",
                name="Tier Bronze",
                description="Premier parrainage - 10% de réduction permanente",
                icon="🥉"
            ),
            
            ReferralTier.SILVER: ReferralReward(
                reward_id="silver_tier",
                tier=ReferralTier.SILVER,
                min_referrals=3,
                discount_percent=25.0,
                months_free=1,
                lifetime_unlock=False,
                exclusive_features=["advanced_analytics_preview", "custom_themes", "priority_customer_service"],
                priority_support=True,
                beta_access=True,
                bonus_credits=150,
                special_badge="🥈 Ambassadeur Silver",
                custom_title="Ambassadeur Silver",
                name="Tier Silver",
                description="3 parrainages - 25% de réduction + 1 mois gratuit",
                icon="🥈"
            ),
            
            ReferralTier.GOLD: ReferralReward(
                reward_id="gold_tier",
                tier=ReferralTier.GOLD,
                min_referrals=5,
                discount_percent=40.0,
                months_free=3,
                lifetime_unlock=False,
                exclusive_features=["exclusive_webinars", "advanced_analytics_preview", "custom_themes", "priority_customer_service", "vip_discord_access"],
                priority_support=True,
                beta_access=True,
                bonus_credits=300,
                special_badge="🥇 Ambassadeur Gold",
                custom_title="Ambassadeur Gold",
                name="Tier Gold",
                description="5 parrainages - 40% de réduction + 3 mois gratuits",
                icon="🥇"
            ),
            
            ReferralTier.PLATINUM: ReferralReward(
                reward_id="platinum_tier",
                tier=ReferralTier.PLATINUM,
                min_referrals=10,
                discount_percent=60.0,
                months_free=6,
                lifetime_unlock=False,
                exclusive_features=["exclusive_webinars", "advanced_analytics_preview", "custom_themes", "priority_customer_service", "vip_discord_access", "monthly_1on1_coaching", "exclusive_strategies"],
                priority_support=True,
                beta_access=True,
                bonus_credits=600,
                special_badge="💎 Ambassadeur Platinum",
                custom_title="Ambassadeur Platinum",
                name="Tier Platinum",
                description="10 parrainages - 60% de réduction + 6 mois gratuits + coaching mensuel",
                icon="💎"
            ),
            
            ReferralTier.DIAMOND: ReferralReward(
                reward_id="diamond_tier",
                tier=ReferralTier.DIAMOND,
                min_referrals=20,
                discount_percent=80.0,
                months_free=12,
                lifetime_unlock=False,
                exclusive_features=["all_platinum_features", "custom_indicators", "api_access", "white_label_option", "revenue_sharing"],
                priority_support=True,
                beta_access=True,
                bonus_credits=1200,
                special_badge="💠 Ambassadeur Diamond",
                custom_title="Ambassadeur Diamond",
                name="Tier Diamond",
                description="20 parrainages - 80% de réduction + 1 an gratuit + partage revenus",
                icon="💠"
            ),
            
            ReferralTier.LEGENDARY: ReferralReward(
                reward_id="legendary_tier",
                tier=ReferralTier.LEGENDARY,
                min_referrals=50,
                discount_percent=100.0,
                months_free=0,
                lifetime_unlock=True,
                exclusive_features=["all_features", "lifetime_access", "revenue_sharing", "co_branding", "affiliate_program_access"],
                priority_support=True,
                beta_access=True,
                bonus_credits=5000,
                special_badge="👑 Légende du Parrainage",
                custom_title="Légende",
                name="Tier Legendary",
                description="50 parrainages - GRATUIT À VIE + partage revenus + co-branding",
                icon="👑"
            )
        }
    
    def generate_referral_code(self, user_session: str, custom_code: Optional[str] = None, custom_message: Optional[str] = None) -> Dict:
        """Génère un code de parrainage pour un utilisateur"""
        
        # Générer un code unique
        if custom_code and len(custom_code) >= 4:
            if custom_code.upper() in self.referral_codes:
                return {
                    'success': False,
                    'error': 'Ce code personnalisé est déjà pris'
                }
            code = custom_code.upper()
        else:
            # Code automatique basé sur l'utilisateur
            base_code = f"TC{user_session[-4:].upper()}"
            counter = 1
            code = base_code
            while code in self.referral_codes:
                code = f"{base_code}{counter}"
                counter += 1
        
        # Créer le code de parrainage
        referral_code = ReferralCode(
            code=code,
            user_session=user_session,
            created_at=datetime.now(),
            expires_at=None,  # Pas d'expiration par défaut
            usage_limit=None,  # Pas de limite par défaut
            usage_count=0,
            is_active=True,
            custom_message=custom_message
        )
        
        # Sauvegarder
        self.referral_codes[code] = referral_code
        
        if user_session not in self.user_codes:
            self.user_codes[user_session] = []
        self.user_codes[user_session].append(referral_code)
        
        return {
            'success': True,
            'referral_code': code,
            'referral_url': f"https://tradingcalculatorpro.com/register?ref={code}",
            'message': f'Code de parrainage {code} créé avec succès!'
        }
    
    def process_referral(self, referral_code: str, referred_user_session: str, source: str = "web") -> Dict:
        """Traite un nouveau parrainage"""
        
        # Vérifier que le code existe
        code_obj = self.referral_codes.get(referral_code.upper())
        if not code_obj:
            return {
                'success': False,
                'error': 'Code de parrainage invalide'
            }
        
        if not code_obj.is_active:
            return {
                'success': False,
                'error': 'Code de parrainage expiré ou désactivé'
            }
        
        # Vérifier les limites d'usage
        if code_obj.usage_limit and code_obj.usage_count >= code_obj.usage_limit:
            return {
                'success': False,
                'error': 'Code de parrainage épuisé'
            }
        
        # Éviter l'auto-parrainage
        if code_obj.user_session == referred_user_session:
            return {
                'success': False,
                'error': 'Vous ne pouvez pas utiliser votre propre code'
            }
        
        # Vérifier si l'utilisateur a déjà été parrainé
        existing_referrals = []
        for referrals_list in self.referrals.values():
            for ref in referrals_list:
                if ref.referred_session == referred_user_session:
                    existing_referrals.append(ref)
        
        if existing_referrals:
            return {
                'success': False,
                'error': 'Cet utilisateur a déjà été parrainé'
            }
        
        # Créer le parrainage
        referral_id = f"ref_{int(datetime.now().timestamp())}_{referred_user_session}"
        
        referral = Referral(
            referral_id=referral_id,
            referrer_session=code_obj.user_session,
            referred_session=referred_user_session,
            referral_code=referral_code.upper(),
            referred_at=datetime.now(),
            confirmed_at=None,
            premium_converted_at=None,
            status=ReferralStatus.PENDING,
            rewards_given=[],
            referrer_ip=None,
            referred_ip=None,
            source=source
        )
        
        # Sauvegarder le parrainage
        if code_obj.user_session not in self.referrals:
            self.referrals[code_obj.user_session] = []
        self.referrals[code_obj.user_session].append(referral)
        
        # Mettre à jour le compteur d'usage
        code_obj.usage_count += 1
        
        return {
            'success': True,
            'referral_id': referral_id,
            'referrer': code_obj.user_session,
            'welcome_message': code_obj.custom_message or f"Bienvenue ! Vous avez été parrainé par un ambassadeur {self._get_user_tier_title(code_obj.user_session)}",
            'pending_confirmation': True
        }
    
    def confirm_referral(self, referred_user_session: str) -> Dict:
        """Confirme un parrainage (quand l'utilisateur s'inscrit vraiment)"""
        
        # Trouver le parrainage en attente
        referral = None
        referrer_session = None
        
        for user_session, referrals_list in self.referrals.items():
            for ref in referrals_list:
                if ref.referred_session == referred_user_session and ref.status == ReferralStatus.PENDING:
                    referral = ref
                    referrer_session = user_session
                    break
            if referral:
                break
        
        if not referral:
            return {
                'success': False,
                'error': 'Aucun parrainage en attente trouvé'
            }
        
        # Confirmer le parrainage
        referral.status = ReferralStatus.CONFIRMED
        referral.confirmed_at = datetime.now()
        
        # Mettre à jour les statistiques du parrain
        self._update_referrer_stats(referrer_session)
        
        # Vérifier les nouvelles récompenses débloquées
        rewards_unlocked = self._check_tier_upgrades(referrer_session)
        
        return {
            'success': True,
            'referral_confirmed': True,
            'referrer_rewards': rewards_unlocked,
            'message': 'Parrainage confirmé avec succès!'
        }
    
    def convert_to_premium(self, referred_user_session: str) -> Dict:
        """Marque qu'un filleul est passé premium"""
        
        # Trouver le parrainage confirmé
        referral = None
        referrer_session = None
        
        for user_session, referrals_list in self.referrals.items():
            for ref in referrals_list:
                if ref.referred_session == referred_user_session and ref.status == ReferralStatus.CONFIRMED:
                    referral = ref
                    referrer_session = user_session
                    break
            if referral:
                break
        
        if not referral:
            return {
                'success': False,
                'error': 'Aucun parrainage confirmé trouvé'
            }
        
        # Marquer comme converti premium
        referral.status = ReferralStatus.PREMIUM_CONVERTED
        referral.premium_converted_at = datetime.now()
        
        # Bonus spécial pour conversion premium
        bonus_reward = {
            'type': 'premium_conversion_bonus',
            'credits': 100,
            'message': f'Bonus +100 crédits : {referred_user_session[:8]} est passé Premium !'
        }
        
        # Mettre à jour les stats
        self._update_referrer_stats(referrer_session)
        
        return {
            'success': True,
            'premium_conversion': True,
            'bonus_reward': bonus_reward,
            'message': 'Conversion premium enregistrée!'
        }
    
    def get_referral_dashboard(self, user_session: str) -> Dict:
        """Récupère le tableau de bord de parrainage"""
        
        # Récupérer ou créer les statistiques
        if user_session not in self.referral_stats:
            self._update_referrer_stats(user_session)
        
        stats = self.referral_stats.get(user_session)
        if not stats:
            # Créer des stats par défaut
            stats = ReferralStats(
                user_session=user_session,
                total_referrals=0,
                confirmed_referrals=0,
                premium_conversions=0,
                active_referrals=0,
                current_tier=ReferralTier.BRONZE if self._get_confirmed_referrals_count(user_session) >= 1 else None,
                next_tier=ReferralTier.BRONZE,
                referrals_to_next_tier=1,
                total_discount_earned=0.0,
                lifetime_savings=0.0,
                current_monthly_discount=0.0,
                unlocked_features=[],
                earned_rewards=[],
                last_updated=datetime.now()
            )
            self.referral_stats[user_session] = stats
        
        # Récupérer les codes de parrainage
        user_codes = self.user_codes.get(user_session, [])
        
        # Récupérer les parrainages
        user_referrals = self.referrals.get(user_session, [])
        
        # Informations sur le tier actuel et suivant
        current_tier_info = None
        next_tier_info = None
        
        if stats.current_tier:
            current_tier_info = self.referral_tiers[stats.current_tier]
        
        if stats.next_tier:
            next_tier_info = self.referral_tiers[stats.next_tier]
        
        return {
            'success': True,
            'stats': self._stats_to_dict(stats),
            'current_tier': self._tier_reward_to_dict(current_tier_info) if current_tier_info else None,
            'next_tier': self._tier_reward_to_dict(next_tier_info) if next_tier_info else None,
            'referral_codes': [self._code_to_dict(code) for code in user_codes],
            'recent_referrals': [self._referral_to_dict(ref) for ref in user_referrals[-5:]],
            'all_tiers': [self._tier_reward_to_dict(tier) for tier in self.referral_tiers.values()]
        }
    
    def _update_referrer_stats(self, user_session: str):
        """Met à jour les statistiques d'un parrain"""
        
        # Compter les parrainages
        user_referrals = self.referrals.get(user_session, [])
        
        total_referrals = len(user_referrals)
        confirmed_referrals = len([r for r in user_referrals if r.status in [ReferralStatus.CONFIRMED, ReferralStatus.PREMIUM_CONVERTED]])
        premium_conversions = len([r for r in user_referrals if r.status == ReferralStatus.PREMIUM_CONVERTED])
        active_referrals = len([r for r in user_referrals if r.status in [ReferralStatus.CONFIRMED, ReferralStatus.PREMIUM_CONVERTED]])
        
        # Déterminer le tier actuel
        current_tier = None
        for tier in reversed(list(ReferralTier)):
            if confirmed_referrals >= self.referral_tiers[tier].min_referrals:
                current_tier = tier
                break
        
        # Déterminer le tier suivant
        next_tier = None
        referrals_to_next = 0
        
        for tier in ReferralTier:
            if tier.value != current_tier.value if current_tier else True:
                tier_requirement = self.referral_tiers[tier].min_referrals
                if confirmed_referrals < tier_requirement:
                    next_tier = tier
                    referrals_to_next = tier_requirement - confirmed_referrals
                    break
        
        # Calculer les économies
        current_discount = 0.0
        lifetime_savings = 0.0
        
        if current_tier:
            tier_reward = self.referral_tiers[current_tier]
            current_discount = tier_reward.discount_percent
            
            # Simulation des économies (en production, calculer selon l'historique réel)
            monthly_price = 9.99  # Prix mensuel de base
            monthly_savings = monthly_price * (current_discount / 100)
            lifetime_savings = monthly_savings * 12  # Estimation annuelle
        
        # Fonctionnalités débloquées
        unlocked_features = []
        earned_rewards = []
        
        if current_tier:
            tier_reward = self.referral_tiers[current_tier]
            unlocked_features = tier_reward.exclusive_features
            earned_rewards = [tier_reward.special_badge]
        
        # Créer ou mettre à jour les stats
        stats = ReferralStats(
            user_session=user_session,
            total_referrals=total_referrals,
            confirmed_referrals=confirmed_referrals,
            premium_conversions=premium_conversions,
            active_referrals=active_referrals,
            current_tier=current_tier,
            next_tier=next_tier,
            referrals_to_next_tier=referrals_to_next,
            total_discount_earned=current_discount,
            lifetime_savings=lifetime_savings,
            current_monthly_discount=current_discount,
            unlocked_features=unlocked_features,
            earned_rewards=earned_rewards,
            last_updated=datetime.now()
        )
        
        self.referral_stats[user_session] = stats
    
    def _check_tier_upgrades(self, user_session: str) -> List[Dict]:
        """Vérifie si de nouvelles récompenses sont débloquées"""
        
        previous_stats = self.referral_stats.get(user_session)
        self._update_referrer_stats(user_session)
        new_stats = self.referral_stats[user_session]
        
        rewards_unlocked = []
        
        # Vérifier si le tier a changé
        if not previous_stats or previous_stats.current_tier != new_stats.current_tier:
            if new_stats.current_tier:
                tier_reward = self.referral_tiers[new_stats.current_tier]
                rewards_unlocked.append({
                    'type': 'tier_upgrade',
                    'tier': tier_reward.tier.value,
                    'name': tier_reward.name,
                    'badge': tier_reward.special_badge,
                    'discount': tier_reward.discount_percent,
                    'features': tier_reward.exclusive_features,
                    'message': f'Félicitations ! Vous êtes maintenant {tier_reward.custom_title} !'
                })
        
        return rewards_unlocked
    
    def _get_confirmed_referrals_count(self, user_session: str) -> int:
        """Compte les parrainages confirmés"""
        user_referrals = self.referrals.get(user_session, [])
        return len([r for r in user_referrals if r.status in [ReferralStatus.CONFIRMED, ReferralStatus.PREMIUM_CONVERTED]])
    
    def _get_user_tier_title(self, user_session: str) -> str:
        """Récupère le titre du tier d'un utilisateur"""
        confirmed_count = self._get_confirmed_referrals_count(user_session)
        
        for tier in reversed(list(ReferralTier)):
            if confirmed_count >= self.referral_tiers[tier].min_referrals:
                return self.referral_tiers[tier].custom_title
        
        return "Trader"
    
    def get_user_discount_rate(self, user_session: str) -> float:
        """Récupère le taux de réduction actuel d'un utilisateur"""
        
        if user_session in self.referral_stats:
            return self.referral_stats[user_session].current_monthly_discount
        
        confirmed_count = self._get_confirmed_referrals_count(user_session)
        
        for tier in reversed(list(ReferralTier)):
            if confirmed_count >= self.referral_tiers[tier].min_referrals:
                return self.referral_tiers[tier].discount_percent
        
        return 0.0
    
    def has_lifetime_access(self, user_session: str) -> bool:
        """Vérifie si l'utilisateur a accès à vie"""
        
        confirmed_count = self._get_confirmed_referrals_count(user_session)
        legendary_tier = self.referral_tiers[ReferralTier.LEGENDARY]
        
        return confirmed_count >= legendary_tier.min_referrals
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Récupère le classement des meilleurs parrains"""
        
        leaderboard = []
        
        for user_session, referrals_list in self.referrals.items():
            confirmed_count = len([r for r in referrals_list if r.status in [ReferralStatus.CONFIRMED, ReferralStatus.PREMIUM_CONVERTED]])
            premium_count = len([r for r in referrals_list if r.status == ReferralStatus.PREMIUM_CONVERTED])
            
            if confirmed_count > 0:
                tier_title = self._get_user_tier_title(user_session)
                
                leaderboard.append({
                    'user_id': user_session[:8] + "...",  # Anonymisé
                    'tier_title': tier_title,
                    'confirmed_referrals': confirmed_count,
                    'premium_conversions': premium_count,
                    'success_rate': (premium_count / confirmed_count * 100) if confirmed_count > 0 else 0
                })
        
        # Trier par nombre de parrainages confirmés
        leaderboard.sort(key=lambda x: x['confirmed_referrals'], reverse=True)
        
        # Ajouter les rangs
        for i, entry in enumerate(leaderboard[:limit]):
            entry['rank'] = i + 1
        
        return leaderboard[:limit]
    
    def _stats_to_dict(self, stats: ReferralStats) -> Dict:
        """Convertit les stats en dictionnaire"""
        
        return {
            'total_referrals': stats.total_referrals,
            'confirmed_referrals': stats.confirmed_referrals,
            'premium_conversions': stats.premium_conversions,
            'active_referrals': stats.active_referrals,
            'current_tier': stats.current_tier.value if stats.current_tier else None,
            'next_tier': stats.next_tier.value if stats.next_tier else None,
            'referrals_to_next_tier': stats.referrals_to_next_tier,
            'total_discount_earned': stats.total_discount_earned,
            'lifetime_savings': stats.lifetime_savings,
            'current_monthly_discount': stats.current_monthly_discount,
            'unlocked_features': stats.unlocked_features,
            'earned_rewards': stats.earned_rewards,
            'last_updated': stats.last_updated.isoformat()
        }
    
    def _tier_reward_to_dict(self, tier_reward: ReferralReward) -> Dict:
        """Convertit une récompense de tier en dictionnaire"""
        
        return {
            'tier': tier_reward.tier.value,
            'min_referrals': tier_reward.min_referrals,
            'discount_percent': tier_reward.discount_percent,
            'months_free': tier_reward.months_free,
            'lifetime_unlock': tier_reward.lifetime_unlock,
            'exclusive_features': tier_reward.exclusive_features,
            'priority_support': tier_reward.priority_support,
            'beta_access': tier_reward.beta_access,
            'bonus_credits': tier_reward.bonus_credits,
            'special_badge': tier_reward.special_badge,
            'custom_title': tier_reward.custom_title,
            'name': tier_reward.name,
            'description': tier_reward.description,
            'icon': tier_reward.icon
        }
    
    def _code_to_dict(self, code: ReferralCode) -> Dict:
        """Convertit un code de parrainage en dictionnaire"""
        
        return {
            'code': code.code,
            'created_at': code.created_at.isoformat(),
            'expires_at': code.expires_at.isoformat() if code.expires_at else None,
            'usage_count': code.usage_count,
            'usage_limit': code.usage_limit,
            'is_active': code.is_active,
            'custom_message': code.custom_message,
            'referral_url': f"https://tradingcalculatorpro.com/register?ref={code.code}"
        }
    
    def _referral_to_dict(self, referral: Referral) -> Dict:
        """Convertit un parrainage en dictionnaire"""
        
        return {
            'referral_id': referral.referral_id,
            'referred_session': referral.referred_session[:8] + "...",  # Anonymisé
            'referral_code': referral.referral_code,
            'referred_at': referral.referred_at.isoformat(),
            'confirmed_at': referral.confirmed_at.isoformat() if referral.confirmed_at else None,
            'premium_converted_at': referral.premium_converted_at.isoformat() if referral.premium_converted_at else None,
            'status': referral.status.value,
            'source': referral.source
        }

# Instance globale du système de parrainage
referral_system = ReferralSystem()