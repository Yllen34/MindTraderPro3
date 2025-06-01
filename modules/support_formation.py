"""
Support et Formation - Tutoriels, webinaires et support utilisateur
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ContentType(Enum):
    VIDEO_TUTORIAL = "video_tutorial"
    WRITTEN_GUIDE = "written_guide"
    INTERACTIVE_DEMO = "interactive_demo"
    WEBINAR = "webinar"
    FAQ = "faq"
    QUICK_TIP = "quick_tip"

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SupportCategory(Enum):
    GETTING_STARTED = "getting_started"
    CALCULATOR_USAGE = "calculator_usage"
    RISK_MANAGEMENT = "risk_management"
    PSYCHOLOGY = "psychology"
    TECHNICAL_ANALYSIS = "technical_analysis"
    PLATFORM_FEATURES = "platform_features"
    TROUBLESHOOTING = "troubleshooting"

@dataclass
class LearningContent:
    """Contenu d'apprentissage"""
    content_id: str
    title: str
    description: str
    content_type: ContentType
    category: SupportCategory
    skill_level: SkillLevel
    
    # Contenu
    content_url: Optional[str]
    content_text: Optional[str]
    duration_minutes: int
    
    # Métadonnées
    tags: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    
    # Statistiques
    view_count: int
    rating: float
    is_premium: bool
    
    created_at: datetime
    last_updated: datetime

@dataclass
class Webinar:
    """Webinaire en direct ou enregistré"""
    webinar_id: str
    title: str
    description: str
    instructor_name: str
    instructor_bio: str
    
    # Planning
    scheduled_date: datetime
    duration_minutes: int
    timezone: str
    
    # Contenu
    agenda: List[str]
    materials: List[str]
    recording_url: Optional[str]
    
    # Accès
    is_live: bool
    is_premium: bool
    max_participants: int
    registered_count: int
    
    created_at: datetime

@dataclass
class UserProgress:
    """Progression d'apprentissage utilisateur"""
    user_session: str
    completed_content: List[str]  # IDs du contenu terminé
    current_learning_path: Optional[str]
    skill_assessments: Dict[str, float]
    certificates_earned: List[str]
    total_learning_hours: float
    last_activity: datetime

class SupportFormationManager:
    """Gestionnaire de support et formation"""
    
    def __init__(self):
        self.learning_content = {}  # content_id -> LearningContent
        self.webinars = {}  # webinar_id -> Webinar
        self.user_progress = {}  # user_session -> UserProgress
        self.faq_database = {}  # category -> List[faq_items]
        
        # Initialiser le contenu par défaut
        self._init_default_content()
        self._init_faq_database()
        
    def _init_default_content(self):
        """Initialise le contenu d'apprentissage par défaut"""
        
        default_content = [
            {
                "content_id": "getting_started_001",
                "title": "🚀 Premiers Pas avec Trading Calculator Pro",
                "description": "Découvrez comment utiliser votre calculateur de trading pour optimiser vos positions",
                "content_type": ContentType.VIDEO_TUTORIAL,
                "category": SupportCategory.GETTING_STARTED,
                "skill_level": SkillLevel.BEGINNER,
                "content_text": """
# 🚀 Premiers Pas avec Trading Calculator Pro

## Introduction
Bienvenue dans Trading Calculator Pro ! Ce guide vous accompagnera dans vos premiers pas.

## Étape 1: Configuration de Base
1. **Sélectionnez votre paire de trading** (ex: XAUUSD, EURUSD)
2. **Définissez votre capital** de trading
3. **Choisissez votre pourcentage de risque** (recommandé: 1-2%)

## Étape 2: Calcul de Position
1. Entrez votre **prix d'entrée**
2. Définissez votre **stop loss**
3. Le calculateur détermine automatiquement votre **lot size optimal**

## Étape 3: Gestion du Risque
- Ne risquez jamais plus de 2% par trade
- Respectez toujours votre stop loss
- Diversifiez vos positions

## Conseils d'Expert
✅ Commencez petit et augmentez progressivement
✅ Tenez un journal de vos trades
✅ Restez discipliné sur votre plan de trading
                """,
                "duration_minutes": 15,
                "tags": ["débutant", "configuration", "premiers-pas"],
                "prerequisites": [],
                "learning_objectives": [
                    "Comprendre les bases du calcul de position",
                    "Configurer correctement le calculateur",
                    "Appliquer les principes de gestion du risque"
                ],
                "is_premium": False
            },
            {
                "content_id": "risk_management_001",
                "title": "💰 Maîtriser la Gestion du Risque",
                "description": "Apprenez les techniques avancées de gestion du risque pour protéger votre capital",
                "content_type": ContentType.WRITTEN_GUIDE,
                "category": SupportCategory.RISK_MANAGEMENT,
                "skill_level": SkillLevel.INTERMEDIATE,
                "content_text": """
# 💰 Maîtriser la Gestion du Risque

## La Règle d'Or: Ne Jamais Risquer Plus de 2%

### Pourquoi 2% Maximum ?
- Permet de survivre à 50 trades perdants consécutifs
- Préserve le capital pour les opportunités futures
- Évite les émotions destructrices

### Calcul du Risque
```
Risque USD = Capital × (% Risque / 100)
Lot Size = Risque USD / (Stop Loss en pips × Pip Value)
```

## Techniques Avancées

### 1. Position Sizing Dynamique
Ajustez la taille selon la volatilité du marché

### 2. Corrélation des Paires
Évitez de risquer sur des paires corrélées simultanément

### 3. Risque Portfolio
Limitez le risque total à 6-8% du capital

## Gestion des Drawdowns
- Réduisez la taille des positions après 3 pertes consécutives
- Arrêtez de trader après 5% de drawdown quotidien
- Analysez vos erreurs avant de reprendre
                """,
                "duration_minutes": 25,
                "tags": ["gestion-risque", "money-management", "protection-capital"],
                "prerequisites": ["getting_started_001"],
                "learning_objectives": [
                    "Maîtriser la règle des 2%",
                    "Calculer les tailles de position optimales",
                    "Gérer les périodes de drawdown"
                ],
                "is_premium": True
            },
            {
                "content_id": "psychology_001",
                "title": "🧠 Psychologie du Trading Profitable",
                "description": "Développez l'état d'esprit gagnant et gérez vos émotions",
                "content_type": ContentType.INTERACTIVE_DEMO,
                "category": SupportCategory.PSYCHOLOGY,
                "skill_level": SkillLevel.INTERMEDIATE,
                "content_text": """
# 🧠 Psychologie du Trading Profitable

## Les 4 Émotions Destructrices

### 1. La Peur 😰
- **Symptômes**: Hésitation à entrer en position, sortie prématurée
- **Solution**: Plan de trading détaillé, position sizing approprié

### 2. La Cupidité 🤑
- **Symptômes**: Positions trop grandes, non-respect du TP
- **Solution**: Objectifs fixes, discipline stricte

### 3. L'Espoir 🙏
- **Symptômes**: Ne pas couper ses pertes, déplacer le SL
- **Solution**: SL automatique, règles strictes

### 4. La Revanche 😤
- **Symptômes**: Trading impulsif après une perte
- **Solution**: Pause obligatoire, analyse post-trade

## Techniques de Maîtrise Émotionnelle

### Score Mental Quotidien
Évaluez votre état avant de trader (1-10):
- Stress, confiance, patience, fatigue
- Ne tradez pas si score < 6

### Routine Pré-Trading
1. Méditation 5 minutes
2. Révision du plan
3. Vérification des conditions de marché
4. Validation de l'état mental

### Journal Émotionnel
Notez après chaque trade:
- Émotion ressentie
- Respect du plan
- Leçons apprises
                """,
                "duration_minutes": 30,
                "tags": ["psychologie", "émotions", "discipline", "mental"],
                "prerequisites": ["getting_started_001"],
                "learning_objectives": [
                    "Identifier les émotions destructrices",
                    "Développer des techniques de contrôle",
                    "Créer une routine de trading disciplinée"
                ],
                "is_premium": True
            },
            {
                "content_id": "technical_analysis_001",
                "title": "📊 Analyse Technique Moderne",
                "description": "Maîtrisez les concepts SMC, ICT et l'analyse institutionnelle",
                "content_type": ContentType.VIDEO_TUTORIAL,
                "category": SupportCategory.TECHNICAL_ANALYSIS,
                "skill_level": SkillLevel.ADVANCED,
                "content_text": """
# 📊 Analyse Technique Moderne

## Smart Money Concepts (SMC)

### Structure de Marché
- **BOS**: Break of Structure (cassure de structure)
- **CHoCH**: Change of Character (changement de caractère)
- **MSS**: Market Structure Shift

### Zones d'Intérêt
- **Order Blocks**: Zones où les institutions ont passé des ordres
- **Fair Value Gaps**: Inefficiences de prix à combler
- **Liquidity Zones**: Zones de liquidité institutionnelle

## ICT Concepts

### Sessions de Trading
- **London Killzone**: 02:00-05:00 EST
- **New York Killzone**: 07:00-10:00 EST
- **Asian Session**: 20:00-00:00 EST

### Modèles de Prix
- **Accumulation**: Phase de collecte institutionnelle
- **Manipulation**: Faux mouvements pour liquider les retailers
- **Distribution**: Phase de vente institutionnelle

## Application Pratique

### 1. Identification de Bias
- Analyse de la structure higher timeframe
- Identification du flux institutionnel
- Validation avec les niveaux clés

### 2. Entrées Précises
- Attendre le retour sur Order Block
- Confirmer avec divergence ou pattern
- Valider le timing avec les sessions

### 3. Gestion de Position
- SL au-delà de la zone d'invalidation
- TP sur prochain niveau de résistance/support
- Trailing avec structure de marché
                """,
                "duration_minutes": 45,
                "tags": ["SMC", "ICT", "analyse-technique", "institutionnel"],
                "prerequisites": ["risk_management_001"],
                "learning_objectives": [
                    "Comprendre les concepts SMC et ICT",
                    "Identifier les zones institutionnelles",
                    "Appliquer l'analyse moderne au trading"
                ],
                "is_premium": True
            }
        ]
        
        for content_data in default_content:
            content = LearningContent(
                content_id=content_data["content_id"],
                title=content_data["title"],
                description=content_data["description"],
                content_type=content_data["content_type"],
                category=content_data["category"],
                skill_level=content_data["skill_level"],
                content_url=content_data.get("content_url"),
                content_text=content_data["content_text"],
                duration_minutes=content_data["duration_minutes"],
                tags=content_data["tags"],
                prerequisites=content_data["prerequisites"],
                learning_objectives=content_data["learning_objectives"],
                view_count=0,
                rating=4.8,
                is_premium=content_data["is_premium"],
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.learning_content[content.content_id] = content
    
    def _init_faq_database(self):
        """Initialise la base de données FAQ"""
        
        self.faq_database = {
            "getting_started": [
                {
                    "question": "Comment calculer la taille de ma position ?",
                    "answer": "Utilisez la formule: Lot Size = (Capital × % Risque) / (Stop Loss en pips × Pip Value). Notre calculateur fait ce calcul automatiquement pour vous."
                },
                {
                    "question": "Quel pourcentage de risque recommandez-vous ?",
                    "answer": "Pour les débutants: 0.5-1% maximum. Pour les traders expérimentés: 1-2% maximum. Ne dépassez jamais 2% par trade."
                },
                {
                    "question": "Comment définir mon stop loss ?",
                    "answer": "Placez votre stop loss selon l'analyse technique: au-delà d'un support/résistance, sous/sur un Order Block, ou selon la volatilité du marché (ATR)."
                }
            ],
            "risk_management": [
                {
                    "question": "Que faire après plusieurs trades perdants ?",
                    "answer": "Réduisez temporairement votre taille de position de 50%, analysez vos erreurs, et reprenez progressivement. Arrêtez de trader si vous atteignez 5% de drawdown quotidien."
                },
                {
                    "question": "Puis-je trader plusieurs paires en même temps ?",
                    "answer": "Oui, mais attention aux corrélations. Évitez de risquer sur EURUSD et GBPUSD simultanément (corrélées). Limitez le risque total à 6-8% de votre capital."
                }
            ],
            "platform_features": [
                {
                    "question": "Comment exporter mon journal de trading ?",
                    "answer": "Allez dans le Journal Intelligent > Export CSV. Vous recevrez un fichier avec tous vos trades, analyses et statistiques."
                },
                {
                    "question": "Comment configurer les alertes de prix ?",
                    "answer": "Dans Alertes Avancées > Nouvelle Alerte, définissez votre paire, prix cible, et canaux de notification (SMS, Email, Discord, Telegram)."
                }
            ],
            "troubleshooting": [
                {
                    "question": "Les prix ne se mettent pas à jour",
                    "answer": "Vérifiez votre connexion internet. Actualisez la page (F5). Si le problème persiste, contactez le support."
                },
                {
                    "question": "Je ne reçois pas mes alertes",
                    "answer": "Vérifiez vos paramètres de notification dans Alertes > Préférences. Assurez-vous que vos contacts (email, téléphone) sont corrects."
                }
            ]
        }
    
    def get_learning_content(self, category: Optional[str] = None, skill_level: Optional[str] = None, is_premium: Optional[bool] = None) -> List[Dict]:
        """Récupère le contenu d'apprentissage filtré"""
        
        content_list = list(self.learning_content.values())
        
        # Filtrer par catégorie
        if category:
            content_list = [c for c in content_list if c.category.value == category]
        
        # Filtrer par niveau
        if skill_level:
            content_list = [c for c in content_list if c.skill_level.value == skill_level]
        
        # Filtrer par premium
        if is_premium is not None:
            content_list = [c for c in content_list if c.is_premium == is_premium]
        
        return [self._content_to_dict(content) for content in content_list]
    
    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """Récupère un contenu spécifique"""
        
        content = self.learning_content.get(content_id)
        return self._content_to_dict(content) if content else None
    
    def get_faq_by_category(self, category: str) -> List[Dict]:
        """Récupère les FAQ d'une catégorie"""
        
        return self.faq_database.get(category, [])
    
    def search_content(self, query: str) -> List[Dict]:
        """Recherche dans le contenu d'apprentissage"""
        
        query_lower = query.lower()
        results = []
        
        for content in self.learning_content.values():
            # Recherche dans le titre, description et tags
            if (query_lower in content.title.lower() or 
                query_lower in content.description.lower() or
                any(query_lower in tag.lower() for tag in content.tags)):
                results.append(self._content_to_dict(content))
        
        return results
    
    def track_user_progress(self, user_session: str, content_id: str) -> Dict:
        """Enregistre la progression utilisateur"""
        
        if user_session not in self.user_progress:
            self.user_progress[user_session] = UserProgress(
                user_session=user_session,
                completed_content=[],
                current_learning_path=None,
                skill_assessments={},
                certificates_earned=[],
                total_learning_hours=0.0,
                last_activity=datetime.now()
            )
        
        progress = self.user_progress[user_session]
        
        if content_id not in progress.completed_content:
            progress.completed_content.append(content_id)
            
            # Ajouter les heures d'apprentissage
            content = self.learning_content.get(content_id)
            if content:
                progress.total_learning_hours += content.duration_minutes / 60.0
        
        progress.last_activity = datetime.now()
        
        return self._progress_to_dict(progress)
    
    def get_user_progress(self, user_session: str) -> Dict:
        """Récupère la progression d'un utilisateur"""
        
        progress = self.user_progress.get(user_session)
        if not progress:
            return {
                'completed_content': [],
                'total_learning_hours': 0,
                'completion_percentage': 0,
                'next_recommended': []
            }
        
        # Calculer le pourcentage de completion
        total_content = len(self.learning_content)
        completed_count = len(progress.completed_content)
        completion_percentage = (completed_count / total_content * 100) if total_content > 0 else 0
        
        # Recommandations basées sur les prérequis
        next_recommended = self._get_next_recommendations(progress)
        
        return {
            'completed_content': progress.completed_content,
            'total_learning_hours': round(progress.total_learning_hours, 1),
            'completion_percentage': round(completion_percentage, 1),
            'next_recommended': next_recommended,
            'certificates_earned': progress.certificates_earned,
            'last_activity': progress.last_activity.isoformat()
        }
    
    def _get_next_recommendations(self, progress: UserProgress) -> List[Dict]:
        """Génère des recommandations de contenu"""
        
        completed = set(progress.completed_content)
        recommendations = []
        
        for content in self.learning_content.values():
            if content.content_id in completed:
                continue
            
            # Vérifier si les prérequis sont remplis
            prerequisites_met = all(prereq in completed for prereq in content.prerequisites)
            
            if prerequisites_met:
                recommendations.append({
                    'content_id': content.content_id,
                    'title': content.title,
                    'description': content.description,
                    'duration_minutes': content.duration_minutes,
                    'skill_level': content.skill_level.value,
                    'is_premium': content.is_premium
                })
        
        # Trier par niveau de compétence et popularité
        recommendations.sort(key=lambda x: (x['skill_level'], -x.get('rating', 0)))
        
        return recommendations[:5]  # Top 5 recommandations
    
    def create_webinar(self, webinar_data: Dict) -> str:
        """Crée un nouveau webinaire"""
        
        webinar_id = f"webinar_{int(datetime.now().timestamp())}"
        
        webinar = Webinar(
            webinar_id=webinar_id,
            title=webinar_data['title'],
            description=webinar_data['description'],
            instructor_name=webinar_data['instructor_name'],
            instructor_bio=webinar_data.get('instructor_bio', ''),
            scheduled_date=datetime.fromisoformat(webinar_data['scheduled_date']),
            duration_minutes=webinar_data['duration_minutes'],
            timezone=webinar_data.get('timezone', 'UTC'),
            agenda=webinar_data.get('agenda', []),
            materials=webinar_data.get('materials', []),
            recording_url=webinar_data.get('recording_url'),
            is_live=webinar_data.get('is_live', False),
            is_premium=webinar_data.get('is_premium', True),
            max_participants=webinar_data.get('max_participants', 100),
            registered_count=0,
            created_at=datetime.now()
        )
        
        self.webinars[webinar_id] = webinar
        
        return webinar_id
    
    def get_upcoming_webinars(self) -> List[Dict]:
        """Récupère les webinaires à venir"""
        
        now = datetime.now()
        upcoming = []
        
        for webinar in self.webinars.values():
            if webinar.scheduled_date > now:
                upcoming.append(self._webinar_to_dict(webinar))
        
        # Trier par date
        upcoming.sort(key=lambda x: x['scheduled_date'])
        
        return upcoming
    
    def _content_to_dict(self, content: LearningContent) -> Dict:
        """Convertit un contenu en dictionnaire"""
        
        return {
            'content_id': content.content_id,
            'title': content.title,
            'description': content.description,
            'content_type': content.content_type.value,
            'category': content.category.value,
            'skill_level': content.skill_level.value,
            'content_text': content.content_text,
            'duration_minutes': content.duration_minutes,
            'tags': content.tags,
            'prerequisites': content.prerequisites,
            'learning_objectives': content.learning_objectives,
            'view_count': content.view_count,
            'rating': content.rating,
            'is_premium': content.is_premium,
            'created_at': content.created_at.isoformat(),
            'last_updated': content.last_updated.isoformat()
        }
    
    def _webinar_to_dict(self, webinar: Webinar) -> Dict:
        """Convertit un webinaire en dictionnaire"""
        
        return {
            'webinar_id': webinar.webinar_id,
            'title': webinar.title,
            'description': webinar.description,
            'instructor_name': webinar.instructor_name,
            'instructor_bio': webinar.instructor_bio,
            'scheduled_date': webinar.scheduled_date.isoformat(),
            'duration_minutes': webinar.duration_minutes,
            'timezone': webinar.timezone,
            'agenda': webinar.agenda,
            'is_live': webinar.is_live,
            'is_premium': webinar.is_premium,
            'registered_count': webinar.registered_count,
            'max_participants': webinar.max_participants,
            'created_at': webinar.created_at.isoformat()
        }
    
    def _progress_to_dict(self, progress: UserProgress) -> Dict:
        """Convertit une progression en dictionnaire"""
        
        return {
            'user_session': progress.user_session,
            'completed_content': progress.completed_content,
            'total_learning_hours': progress.total_learning_hours,
            'certificates_earned': progress.certificates_earned,
            'last_activity': progress.last_activity.isoformat()
        }

# Instance globale du gestionnaire de support et formation
support_formation_manager = SupportFormationManager()