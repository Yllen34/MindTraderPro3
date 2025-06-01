"""
Système de monétisation avec plans freemium, premium mensuel et achat unique
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class PlanType(Enum):
    FREE = "free"
    PREMIUM_MONTHLY = "premium_monthly" 
    LIFETIME = "lifetime"

class FeatureAccess(Enum):
    BLOCKED = "blocked"
    LIMITED = "limited"
    UNLIMITED = "unlimited"

@dataclass
class PricingPlan:
    """Définition d'un plan tarifaire"""
    plan_type: PlanType
    name: str
    price: float
    currency: str
    billing_period: Optional[str]  # monthly, yearly, lifetime
    features: Dict[str, FeatureAccess]
    limits: Dict[str, int]
    description: str
    popular: bool = False

@dataclass
class UserSubscription:
    """Abonnement utilisateur"""
    user_session: str
    plan_type: PlanType
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    payment_method: str
    transaction_id: str
    auto_renew: bool = True

class MonetizationManager:
    """Gestionnaire de la monétisation"""
    
    def __init__(self):
        self.pricing_plans = self._initialize_pricing_plans()
        self.feature_matrix = self._initialize_feature_matrix()
        
    def _initialize_pricing_plans(self) -> Dict[PlanType, PricingPlan]:
        """Initialise les plans tarifaires"""
        return {
            PlanType.FREE: PricingPlan(
                plan_type=PlanType.FREE,
                name="Plan Gratuit",
                price=0.0,
                currency="EUR",
                billing_period=None,
                features={
                    "lot_calculator": FeatureAccess.UNLIMITED,
                    "basic_journal": FeatureAccess.LIMITED,
                    "price_alerts": FeatureAccess.LIMITED,
                    "ai_tips": FeatureAccess.LIMITED,
                    "glossary": FeatureAccess.UNLIMITED,
                    "basic_articles": FeatureAccess.UNLIMITED,
                    "economic_calendar": FeatureAccess.LIMITED,
                    "trade_sharing": FeatureAccess.UNLIMITED,
                    "risk_management": FeatureAccess.LIMITED
                },
                limits={
                    "journal_entries": 10,
                    "price_alerts": 2,
                    "ai_requests_daily": 5,
                    "economic_events": 10,
                    "risk_profiles": 1
                },
                description="Parfait pour découvrir le trading avec les outils essentiels"
            ),
            
            PlanType.PREMIUM_MONTHLY: PricingPlan(
                plan_type=PlanType.PREMIUM_MONTHLY,
                name="Premium Mensuel",
                price=9.99,
                currency="EUR",
                billing_period="monthly",
                features={
                    "lot_calculator": FeatureAccess.UNLIMITED,
                    "advanced_journal": FeatureAccess.UNLIMITED,
                    "price_alerts": FeatureAccess.UNLIMITED,
                    "ai_analysis": FeatureAccess.UNLIMITED,
                    "video_tutorials": FeatureAccess.UNLIMITED,
                    "quiz_certification": FeatureAccess.UNLIMITED,
                    "premium_articles": FeatureAccess.UNLIMITED,
                    "economic_calendar": FeatureAccess.UNLIMITED,
                    "advanced_sharing": FeatureAccess.UNLIMITED,
                    "risk_management": FeatureAccess.UNLIMITED,
                    "mt4_integration": FeatureAccess.UNLIMITED,
                    "telegram_notifications": FeatureAccess.UNLIMITED,
                    "priority_support": FeatureAccess.UNLIMITED
                },
                limits={
                    "journal_entries": -1,  # illimité
                    "price_alerts": -1,
                    "ai_requests_daily": -1,
                    "economic_events": -1,
                    "risk_profiles": -1
                },
                description="Accès complet à tous les outils professionnels",
                popular=True
            ),
            
            PlanType.LIFETIME: PricingPlan(
                plan_type=PlanType.LIFETIME,
                name="Achat à Vie",
                price=149.99,
                currency="EUR",
                billing_period="lifetime",
                features={
                    "lot_calculator": FeatureAccess.UNLIMITED,
                    "advanced_journal": FeatureAccess.UNLIMITED,
                    "price_alerts": FeatureAccess.UNLIMITED,
                    "ai_analysis": FeatureAccess.UNLIMITED,
                    "video_tutorials": FeatureAccess.UNLIMITED,
                    "quiz_certification": FeatureAccess.UNLIMITED,
                    "premium_articles": FeatureAccess.UNLIMITED,
                    "economic_calendar": FeatureAccess.UNLIMITED,
                    "advanced_sharing": FeatureAccess.UNLIMITED,
                    "risk_management": FeatureAccess.UNLIMITED,
                    "mt4_integration": FeatureAccess.UNLIMITED,
                    "telegram_notifications": FeatureAccess.UNLIMITED,
                    "priority_support": FeatureAccess.UNLIMITED,
                    "lifetime_updates": FeatureAccess.UNLIMITED,
                    "exclusive_strategies": FeatureAccess.UNLIMITED
                },
                limits={
                    "journal_entries": -1,
                    "price_alerts": -1,
                    "ai_requests_daily": -1,
                    "economic_events": -1,
                    "risk_profiles": -1
                },
                description="Tous les outils premium + mises à jour à vie + stratégies exclusives"
            )
        }
    
    def _initialize_feature_matrix(self) -> Dict[str, Dict[PlanType, Dict]]:
        """Matrice des fonctionnalités par plan"""
        return {
            "calculateur_lots": {
                PlanType.FREE: {"access": True, "limit": None, "description": "Calculateur de base"},
                PlanType.PREMIUM_MONTHLY: {"access": True, "limit": None, "description": "Calculateur avancé + API"},
                PlanType.LIFETIME: {"access": True, "limit": None, "description": "Calculateur pro + intégrations"}
            },
            "journal_trading": {
                PlanType.FREE: {"access": True, "limit": 10, "description": "10 trades max"},
                PlanType.PREMIUM_MONTHLY: {"access": True, "limit": None, "description": "Trades illimités + analytics"},
                PlanType.LIFETIME: {"access": True, "limit": None, "description": "Tout premium + export avancé"}
            },
            "alertes_prix": {
                PlanType.FREE: {"access": True, "limit": 2, "description": "2 alertes actives"},
                PlanType.PREMIUM_MONTHLY: {"access": True, "limit": None, "description": "Alertes illimitées + SMS"},
                PlanType.LIFETIME: {"access": True, "limit": None, "description": "Tout premium + alertes IA"}
            },
            "assistant_ia": {
                PlanType.FREE: {"access": True, "limit": 5, "description": "5 questions/jour"},
                PlanType.PREMIUM_MONTHLY: {"access": True, "limit": None, "description": "IA illimitée + analyses"},
                PlanType.LIFETIME: {"access": True, "limit": None, "description": "IA avancée + stratégies exclusives"}
            },
            "centre_apprentissage": {
                PlanType.FREE: {"access": True, "limit": "basic", "description": "Glossaire + articles de base"},
                PlanType.PREMIUM_MONTHLY: {"access": True, "limit": None, "description": "Vidéos + quiz + certificats"},
                PlanType.LIFETIME: {"access": True, "limit": None, "description": "Contenu exclusif + coaching"}
            }
        }
    
    def get_user_plan(self, user_session: str) -> PlanType:
        """Récupère le plan de l'utilisateur"""
        # En pratique, récupérer depuis la base de données
        # Pour la démo, on retourne FREE par défaut
        return PlanType.FREE
    
    def check_feature_access(self, user_session: str, feature: str) -> Dict:
        """Vérifie l'accès à une fonctionnalité"""
        user_plan = self.get_user_plan(user_session)
        
        if feature in self.feature_matrix:
            feature_info = self.feature_matrix[feature][user_plan]
            return {
                "has_access": feature_info["access"],
                "limit": feature_info["limit"],
                "description": feature_info["description"],
                "user_plan": user_plan.value
            }
        
        return {"has_access": False, "limit": 0, "description": "Fonctionnalité non trouvée"}
    
    def get_upgrade_suggestion(self, feature: str, user_plan: PlanType) -> Dict:
        """Suggère une mise à niveau pour une fonctionnalité"""
        suggestions = {
            PlanType.FREE: {
                "target_plan": PlanType.PREMIUM_MONTHLY,
                "savings": "Économisez 60% vs achat séparé des fonctionnalités",
                "benefits": [
                    "Alertes de prix illimitées",
                    "Journal de trading avancé", 
                    "Assistant IA complet",
                    "Tutoriels vidéo exclusifs",
                    "Support prioritaire"
                ]
            }
        }
        
        if user_plan in suggestions:
            suggestion = suggestions[user_plan]
            target_plan_info = self.pricing_plans[suggestion["target_plan"]]
            
            return {
                "recommended_plan": target_plan_info.name,
                "price": target_plan_info.price,
                "currency": target_plan_info.currency,
                "billing": target_plan_info.billing_period,
                "savings": suggestion["savings"],
                "benefits": suggestion["benefits"],
                "upgrade_url": f"/upgrade?plan={suggestion['target_plan'].value}"
            }
        
        return {}
    
    def calculate_usage_stats(self, user_session: str) -> Dict:
        """Calcule les statistiques d'utilisation vs limites"""
        user_plan = self.get_user_plan(user_session)
        plan_info = self.pricing_plans[user_plan]
        
        # En pratique, récupérer depuis la base de données
        current_usage = {
            "journal_entries": 8,
            "price_alerts": 2,
            "ai_requests_daily": 4,
            "economic_events": 8
        }
        
        usage_stats = {}
        for feature, current in current_usage.items():
            limit = plan_info.limits.get(feature, 0)
            if limit == -1:  # illimité
                usage_stats[feature] = {
                    "current": current,
                    "limit": "illimité",
                    "percentage": 0,
                    "near_limit": False
                }
            else:
                percentage = (current / limit * 100) if limit > 0 else 0
                usage_stats[feature] = {
                    "current": current,
                    "limit": limit,
                    "percentage": round(percentage, 1),
                    "near_limit": percentage >= 80
                }
        
        return usage_stats
    
    def get_pricing_page_data(self) -> Dict:
        """Données pour la page de tarification"""
        plans_data = []
        
        for plan_type, plan in self.pricing_plans.items():
            # Fonctionnalités principales à afficher
            key_features = []
            if plan_type == PlanType.FREE:
                key_features = [
                    "Calculateur de lots",
                    "10 trades en journal",
                    "2 alertes de prix",
                    "5 questions IA/jour",
                    "Glossaire complet",
                    "Articles de base"
                ]
            elif plan_type == PlanType.PREMIUM_MONTHLY:
                key_features = [
                    "Tout du plan gratuit",
                    "Journal illimité + analytics",
                    "Alertes de prix illimitées",
                    "Assistant IA complet",
                    "Tutoriels vidéo HD",
                    "Quiz + certifications",
                    "Intégrations MT4/MT5",
                    "Support prioritaire"
                ]
            elif plan_type == PlanType.LIFETIME:
                key_features = [
                    "Tout du plan premium",
                    "Accès à vie garanti",
                    "Mises à jour gratuites",
                    "Stratégies exclusives",
                    "Coaching personnalisé",
                    "API complète",
                    "Support VIP"
                ]
            
            plans_data.append({
                "type": plan_type.value,
                "name": plan.name,
                "price": plan.price,
                "currency": plan.currency,
                "billing_period": plan.billing_period,
                "description": plan.description,
                "features": key_features,
                "popular": plan.popular,
                "savings": self._calculate_savings(plan_type)
            })
        
        return {
            "plans": plans_data,
            "currency": "EUR",
            "money_back_guarantee": "Satisfait ou remboursé 30 jours",
            "secure_payment": "Paiement sécurisé SSL",
            "instant_access": "Accès immédiat après paiement"
        }
    
    def _calculate_savings(self, plan_type: PlanType) -> Optional[str]:
        """Calcule les économies par rapport aux autres plans"""
        if plan_type == PlanType.PREMIUM_MONTHLY:
            return None
        elif plan_type == PlanType.LIFETIME:
            monthly_price = self.pricing_plans[PlanType.PREMIUM_MONTHLY].price
            lifetime_price = self.pricing_plans[PlanType.LIFETIME].price
            months_to_break_even = lifetime_price / monthly_price
            return f"Rentabilisé en {int(months_to_break_even)} mois"
        
        return None
    
    def validate_payment(self, payment_data: Dict) -> Dict:
        """Valide un paiement (intégration future avec Stripe/PayPal)"""
        # Simulation de validation de paiement
        return {
            "success": True,
            "transaction_id": f"txn_{int(datetime.now().timestamp())}",
            "message": "Paiement validé avec succès"
        }
    
    def activate_subscription(self, user_session: str, plan_type: PlanType, transaction_id: str) -> Dict:
        """Active un abonnement utilisateur"""
        start_date = datetime.now()
        
        if plan_type == PlanType.PREMIUM_MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan_type == PlanType.LIFETIME:
            end_date = None  # Pas d'expiration
        else:
            end_date = None
        
        subscription = UserSubscription(
            user_session=user_session,
            plan_type=plan_type,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            payment_method="card",
            transaction_id=transaction_id
        )
        
        # En pratique, sauvegarder en base de données
        
        return {
            "success": True,
            "subscription": {
                "plan": plan_type.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "features_unlocked": list(self.pricing_plans[plan_type].features.keys())
            }
        }

# Instance globale du gestionnaire de monétisation
monetization_manager = MonetizationManager()