"""
Centre d'Apprentissage - Formation trading avec freemium
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class GlossaryTerm:
    """Terme du glossaire trading"""
    id: str
    term: str
    definition: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    examples: List[str]
    related_terms: List[str]

@dataclass
class Article:
    """Article éducatif"""
    id: str
    title: str
    content: str
    category: str
    difficulty: str
    reading_time: int  # en minutes
    author: str
    date_published: datetime
    is_premium: bool
    tags: List[str]
    summary: str

@dataclass
class VideoTutorial:
    """Tutoriel vidéo (Premium)"""
    id: str
    title: str
    description: str
    duration: int  # en secondes
    thumbnail_url: str
    video_url: str
    category: str
    difficulty: str
    is_premium: bool = True

@dataclass
class QuizQuestion:
    """Question de quiz (Premium)"""
    id: str
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    difficulty: str
    category: str

@dataclass
class Quiz:
    """Quiz complet (Premium)"""
    id: str
    title: str
    description: str
    questions: List[QuizQuestion]
    category: str
    difficulty: str
    passing_score: int

class LearningCenter:
    """Gestionnaire du centre d'apprentissage"""
    
    def __init__(self):
        self.glossary_terms = self._load_glossary()
        self.articles = self._load_articles()
        self.video_tutorials = self._load_video_tutorials()
        self.quizzes = self._load_quizzes()
    
    def _load_glossary(self) -> List[GlossaryTerm]:
        """Charge le glossaire trading (Gratuit)"""
        return [
            GlossaryTerm(
                id="pip",
                term="Pip",
                definition="Unité de mesure la plus petite d'une devise. Pour la plupart des paires, 1 pip = 0.0001.",
                category="bases",
                difficulty="beginner",
                examples=["EURUSD passe de 1.1000 à 1.1001 = +1 pip"],
                related_terms=["spread", "lot", "point"]
            ),
            GlossaryTerm(
                id="lot",
                term="Lot",
                definition="Unité de trading standard. 1 lot standard = 100 000 unités de la devise de base.",
                category="bases",
                difficulty="beginner",
                examples=["1 lot EURUSD = 100 000 EUR", "0.1 lot = 10 000 unités"],
                related_terms=["pip", "volume", "mini-lot"]
            ),
            GlossaryTerm(
                id="spread",
                term="Spread",
                definition="Différence entre le prix d'achat (ask) et le prix de vente (bid) d'une paire de devises.",
                category="bases",
                difficulty="beginner",
                examples=["EURUSD Bid: 1.1000, Ask: 1.1002 = Spread de 2 pips"],
                related_terms=["bid", "ask", "commission"]
            ),
            GlossaryTerm(
                id="leverage",
                term="Effet de levier",
                definition="Mécanisme permettant de trader avec plus d'argent que ce que vous possédez réellement.",
                category="risque",
                difficulty="intermediate",
                examples=["Avec un levier 1:100, 1000€ permettent de trader 100 000€"],
                related_terms=["marge", "appel-de-marge", "liquidation"]
            ),
            GlossaryTerm(
                id="stop-loss",
                term="Stop Loss",
                definition="Ordre automatique pour fermer une position en perte à un niveau prédéfini.",
                category="gestion-risque",
                difficulty="beginner",
                examples=["Achat EURUSD à 1.1000, Stop Loss à 1.0950 = -50 pips max"],
                related_terms=["take-profit", "trailing-stop", "gestion-risque"]
            ),
            GlossaryTerm(
                id="take-profit",
                term="Take Profit",
                definition="Ordre automatique pour fermer une position en profit à un niveau prédéfini.",
                category="gestion-risque",
                difficulty="beginner",
                examples=["Achat EURUSD à 1.1000, Take Profit à 1.1100 = +100 pips"],
                related_terms=["stop-loss", "risk-reward", "objectif"]
            ),
            GlossaryTerm(
                id="support",
                term="Support",
                definition="Niveau de prix où la demande est suffisamment forte pour empêcher la baisse.",
                category="analyse-technique",
                difficulty="intermediate",
                examples=["XAUUSD rebondit plusieurs fois sur 1900, c'est un support"],
                related_terms=["resistance", "cassure", "rebond"]
            ),
            GlossaryTerm(
                id="resistance",
                term="Résistance",
                definition="Niveau de prix où l'offre est suffisamment forte pour empêcher la hausse.",
                category="analyse-technique",
                difficulty="intermediate",
                examples=["EURUSD rejette plusieurs fois 1.1200, c'est une résistance"],
                related_terms=["support", "cassure", "sommet"]
            ),
            GlossaryTerm(
                id="trend",
                term="Tendance",
                definition="Direction générale du mouvement des prix sur une période donnée.",
                category="analyse-technique",
                difficulty="beginner",
                examples=["Tendance haussière: sommets et creux de plus en plus hauts"],
                related_terms=["support", "resistance", "retournement"]
            ),
            GlossaryTerm(
                id="volatilite",
                term="Volatilité",
                definition="Mesure de l'amplitude des variations de prix d'un instrument financier.",
                category="analyse",
                difficulty="intermediate",
                examples=["GBP/USD plus volatil que EUR/USD pendant Brexit"],
                related_terms=["atr", "range", "ecart-type"]
            )
        ]
    
    def _load_articles(self) -> List[Article]:
        """Charge les articles éducatifs"""
        return [
            Article(
                id="basics-forex",
                title="Les bases du trading Forex : Guide complet pour débutants",
                content="""
# Les bases du trading Forex

Le marché des changes (Forex) est le plus grand marché financier au monde avec plus de 6 000 milliards de dollars échangés quotidiennement.

## Qu'est-ce que le Forex ?

Le Forex consiste à échanger une devise contre une autre dans l'espoir de réaliser un profit sur les variations de taux de change.

### Les paires de devises principales :
- **EUR/USD** : Euro contre Dollar US (la plus tradée)
- **GBP/USD** : Livre Sterling contre Dollar US
- **USD/JPY** : Dollar US contre Yen Japonais
- **USD/CHF** : Dollar US contre Franc Suisse

## Comment fonctionne le trading Forex ?

Quand vous tradez le Forex, vous achetez une devise et vendez simultanément l'autre.

**Exemple pratique :**
Si vous pensez que l'Euro va se renforcer face au Dollar, vous achetez EUR/USD.
- Prix d'achat : 1.1000
- Si le prix monte à 1.1100, vous gagnez 100 pips
- Si le prix descend à 1.0950, vous perdez 50 pips

## Les concepts essentiels à maîtriser

### 1. Le Pip
Un pip est la plus petite unité de mesure d'une paire de devises.
- Pour EUR/USD : 1 pip = 0.0001
- Pour USD/JPY : 1 pip = 0.01

### 2. Le Lot
Unité de trading standard :
- 1 lot standard = 100 000 unités
- 1 mini lot = 10 000 unités
- 1 micro lot = 1 000 unités

### 3. L'effet de levier
Permet de trader avec plus d'argent que votre capital :
- Levier 1:100 = 1000€ permettent de trader 100 000€
- **ATTENTION** : augmente les gains ET les pertes !

## Gestion du risque : LA RÈGLE D'OR

⚠️ **Ne jamais risquer plus de 1-2% de son capital par trade**

Utilisez toujours :
- **Stop Loss** : limite vos pertes
- **Take Profit** : sécurise vos gains
- **Ratio Risk/Reward** : visez au minimum 1:2

## Les heures de trading

Le Forex est ouvert 24h/24, 5j/7 :
- **Session Asiatique** : 00h-09h (Paris)
- **Session Européenne** : 08h-17h (Paris)
- **Session Américaine** : 14h-23h (Paris)

Les meilleurs moments : chevauchements entre sessions (8h-12h et 14h-18h).

## Conseil pour débuter

1. **Formez-vous** d'abord (livres, cours, démo)
2. **Tradez en démo** pendant au moins 3 mois
3. **Commencez petit** avec un capital que vous pouvez perdre
4. **Tenez un journal** de tous vos trades
5. **Restez discipliné** et suivez votre plan

> "Les traders qui réussissent ne sont pas ceux qui gagnent tout le temps, mais ceux qui savent gérer leurs pertes."

Le trading Forex demande du temps, de la discipline et une formation continue. Commencez doucement et construisez votre expérience progressivement.
                """,
                category="bases",
                difficulty="beginner",
                reading_time=8,
                author="Équipe Trading Pro",
                date_published=datetime(2024, 1, 15),
                is_premium=False,
                tags=["forex", "débutant", "bases", "paires-devises"],
                summary="Guide complet pour débuter en trading Forex : paires de devises, pips, lots, effet de levier et gestion du risque."
            ),
            Article(
                id="risk-management",
                title="Gestion du risque : La clé du succès en trading",
                content="""
# Gestion du risque en trading

La gestion du risque n'est pas optionnelle - c'est LA compétence qui différencie les traders qui réussissent de ceux qui perdent tout.

## Règle n°1 : Ne jamais risquer plus de 1-2% par trade

Cette règle fondamentale vous permet de survivre aux séries de pertes inévitables.

**Calcul pratique :**
- Capital : 10 000€
- Risque max par trade : 2% = 200€
- Si Stop Loss à 50 pips : Lot size = 200€ ÷ 50 pips = 0.4 lot

## Les outils de gestion du risque

### Stop Loss obligatoire
- **Jamais de trade sans Stop Loss**
- Placez-le AVANT d'entrer en position
- Ne le déplacez JAMAIS contre vous

### Position Sizing (taille de position)
Formule : Taille position = (Capital × %Risque) ÷ (Stop Loss en €)

### Ratio Risk/Reward minimum 1:2
- Risque 50 pips pour gagner 100 pips minimum
- Sur 10 trades : même avec 60% de pertes, vous êtes profitable

## Les erreurs fatales à éviter

❌ **Moyenner à la baisse** : ajouter quand vous perdez
❌ **Déplacer le Stop Loss** contre vous
❌ **Trader sans plan** défini à l'avance
❌ **Risquer plus après une perte** pour "récupérer"
❌ **Trader avec l'argent du loyer**

## Gestion psychologique

Le trading est 80% mental :
- **Acceptez vos pertes** comme faisant partie du jeu
- **Tenez un journal** pour analyser vos erreurs
- **Prenez des pauses** après des séries de pertes
- **Restez humble** même après des gains

## Plan de trading type

1. **Avant d'entrer :**
   - Identifiez votre setup
   - Définissez Stop Loss et Take Profit
   - Calculez votre taille de position

2. **Pendant le trade :**
   - Ne touchez à rien
   - Laissez le marché décider

3. **Après la clôture :**
   - Analysez dans votre journal
   - Qu'avez-vous bien/mal fait ?

## Exemple concret

**Trade EURUSD :**
- Capital : 5000€
- Risque max : 2% = 100€
- Setup : Cassure résistance à 1.1000
- Stop Loss : 1.0950 (50 pips)
- Take Profit : 1.1100 (100 pips)
- Taille position : 100€ ÷ 50 pips = 0.2 lot

**Résultats possibles :**
- ✅ Gain : +200€ (ratio 1:2 respecté)
- ❌ Perte : -100€ (risque contrôlé)

La gestion du risque n'est pas sexy, mais c'est ce qui vous permettra de trader dans 5 ans encore !
                """,
                category="gestion-risque",
                difficulty="intermediate",
                reading_time=6,
                author="Expert Risk Manager",
                date_published=datetime(2024, 2, 1),
                is_premium=False,
                tags=["gestion-risque", "stop-loss", "position-sizing"],
                summary="Guide complet de gestion du risque : règles essentielles, calculs pratiques et erreurs à éviter."
            ),
            Article(
                id="advanced-strategies",
                title="Stratégies avancées : Scalping et Swing Trading",
                content="""
# Stratégies de trading avancées

## Le Scalping : Profits rapides, risques contrôlés

Le scalping consiste à réaliser de nombreux petits profits sur des mouvements de prix de courte durée.

### Caractéristiques du scalping :
- Durée : quelques secondes à quelques minutes
- Objectif : 5-20 pips par trade
- Fréquence : 20-100 trades par jour
- Marchés : majors avec spread faible

### Setup scalping efficace :
1. **Timeframe** : M1, M5
2. **Indicateurs** : EMA 9/21, RSI, MACD
3. **Sessions** : Londres/New York (volatilité)
4. **Paires** : EUR/USD, GBP/USD, USD/JPY

**Exemple de setup :**
- Prix au-dessus EMA 21
- RSI > 50 (momentum haussier)
- Cassure niveau résistance intraday
- Entry : cassure + 2 pips
- Stop : -10 pips / Target : +15 pips

### Avantages/Inconvénients scalping :

**✅ Avantages :**
- Profits quotidiens réguliers
- Exposition réduite aux gaps
- Beaucoup d'opportunités

**❌ Inconvénients :**
- Stress intense
- Coûts de transaction élevés
- Concentration maximale requise

## Le Swing Trading : Suivre les tendances

Le swing trading capture les mouvements de prix sur plusieurs jours à semaines.

### Caractéristiques du swing trading :
- Durée : 2-10 jours
- Objectif : 100-500 pips
- Fréquence : 5-20 trades par mois
- Analyse : technique + fondamentale

### Setup swing trading :
1. **Timeframe** : H4, Daily
2. **Indicateurs** : MM 50/200, Support/Résistance
3. **Entrée** : retournement sur support/résistance
4. **Gestion** : trailing stop

**Exemple concret :**
- EURUSD en tendance haussière (Daily)
- Prix revient sur support MM50
- Formation hammer/doji
- Entry : cassure high de la bougie
- Stop : sous le support
- Target : résistance suivante

### Money Management swing :
- Risque : 1-3% par position
- Diversification : 3-5 paires max
- Corrélation : éviter EUR/USD + EUR/GBP

## Stratégie Price Action pure

Trading basé uniquement sur l'action des prix, sans indicateurs.

### Patterns essentiels :
- **Pin bar** : rejet d'un niveau
- **Inside bar** : consolidation
- **Engulfing** : retournement puissant

### Règles Price Action :
1. Support/Résistance marqués
2. Confluence de niveaux
3. Volume de confirmation
4. Gestion stricte du risque

Cette approche demande beaucoup d'expérience mais offre une lecture pure du marché.

## Automatisation et algorithmes

### Expert Advisors (EA) :
- Trading automatique 24h/24
- Émotions éliminées
- Backtesting possible

### Paramètres clés EA :
- Drawdown maximum : 15%
- Profit factor > 1.3
- Plus de 100 trades testés

**Important :** Même automatisé, surveillez et ajustez vos systèmes !

## Conseils pour stratégies avancées

1. **Backtestez** tout sur données historiques
2. **Forward testez** en démo 3 mois minimum
3. **Diversifiez** vos approches
4. **Adaptez-vous** aux conditions de marché
5. **Restez simple** : complexe ≠ profitable

Le succès en trading avancé vient de la maîtrise parfaite d'une stratégie plutôt que de connaître 10 stratégies imparfaitement.
                """,
                category="strategies",
                difficulty="advanced",
                reading_time=12,
                author="Trader Professionnel",
                date_published=datetime(2024, 3, 1),
                is_premium=True,
                tags=["scalping", "swing-trading", "strategies-avancees"],
                summary="Stratégies avancées de trading : scalping rapide, swing trading tendanciel et price action pure."
            )
        ]
    
    def _load_video_tutorials(self) -> List[VideoTutorial]:
        """Charge les tutoriels vidéo (Premium)"""
        return [
            VideoTutorial(
                id="setup-metatrader",
                title="Configuration complète de MetaTrader 5",
                description="Apprenez à configurer MT5 de A à Z : installation, indicateurs, Expert Advisors et trading automatique.",
                duration=1800,  # 30 minutes
                thumbnail_url="/static/thumbnails/mt5_setup.jpg",
                video_url="https://example.com/videos/mt5_setup.mp4",
                category="outils",
                difficulty="beginner"
            ),
            VideoTutorial(
                id="scalping-strategy",
                title="Stratégie de scalping rentable sur EURUSD",
                description="Stratégie complète de scalping avec 75% de réussite. Setup, entrée, sortie et gestion du risque.",
                duration=2400,  # 40 minutes
                thumbnail_url="/static/thumbnails/scalping.jpg",
                video_url="https://example.com/videos/scalping_strategy.mp4",
                category="strategies",
                difficulty="advanced"
            ),
            VideoTutorial(
                id="risk-psychology",
                title="Psychologie du trading et gestion émotionnelle",
                description="Comment contrôler ses émotions, gérer le stress et développer une mentalité de trader gagnant.",
                duration=3000,  # 50 minutes
                thumbnail_url="/static/thumbnails/psychology.jpg",
                video_url="https://example.com/videos/trading_psychology.mp4",
                category="psychologie",
                difficulty="intermediate"
            )
        ]
    
    def _load_quizzes(self) -> List[Quiz]:
        """Charge les quiz éducatifs (Premium)"""
        questions_forex_basics = [
            QuizQuestion(
                id="q1",
                question="Que signifie un pip pour la paire EUR/USD ?",
                options=["0.01", "0.001", "0.0001", "0.00001"],
                correct_answer=2,
                explanation="Pour les paires majeures comme EUR/USD, 1 pip = 0.0001 (4ème décimale).",
                difficulty="beginner",
                category="bases"
            ),
            QuizQuestion(
                id="q2",
                question="Avec un effet de levier 1:100, combien pouvez-vous trader avec 1000€ ?",
                options=["10 000€", "50 000€", "100 000€", "1 000 000€"],
                correct_answer=2,
                explanation="Levier 1:100 signifie que 1000€ permettent de contrôler 100 000€.",
                difficulty="beginner",
                category="bases"
            ),
            QuizQuestion(
                id="q3",
                question="Quel pourcentage maximum de votre capital devriez-vous risquer par trade ?",
                options=["5%", "10%", "1-2%", "Peu importe"],
                correct_answer=2,
                explanation="La règle d'or : ne jamais risquer plus de 1-2% de son capital par trade.",
                difficulty="beginner",
                category="gestion-risque"
            )
        ]
        
        return [
            Quiz(
                id="forex-basics",
                title="Quiz : Les bases du Forex",
                description="Testez vos connaissances sur les concepts fondamentaux du trading Forex",
                questions=questions_forex_basics,
                category="bases",
                difficulty="beginner",
                passing_score=70
            )
        ]
    
    # Méthodes publiques
    def get_glossary_terms(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> List[GlossaryTerm]:
        """Récupère les termes du glossaire avec filtres optionnels"""
        terms = self.glossary_terms
        
        if category:
            terms = [term for term in terms if term.category == category]
        
        if difficulty:
            terms = [term for term in terms if term.difficulty == difficulty]
        
        return sorted(terms, key=lambda x: x.term)
    
    def search_glossary(self, query: str) -> List[GlossaryTerm]:
        """Recherche dans le glossaire"""
        query_lower = query.lower()
        results = []
        
        for term in self.glossary_terms:
            if (query_lower in term.term.lower() or 
                query_lower in term.definition.lower() or
                any(query_lower in example.lower() for example in term.examples)):
                results.append(term)
        
        return results
    
    def get_articles(self, category: Optional[str] = None, is_premium: Optional[bool] = None) -> List[Article]:
        """Récupère les articles avec filtres"""
        articles = self.articles
        
        if category:
            articles = [article for article in articles if article.category == category]
        
        if is_premium is not None:
            articles = [article for article in articles if article.is_premium == is_premium]
        
        return sorted(articles, key=lambda x: x.date_published, reverse=True)
    
    def get_free_articles(self) -> List[Article]:
        """Récupère uniquement les articles gratuits"""
        return self.get_articles(is_premium=False)
    
    def get_premium_content(self) -> Dict:
        """Récupère tout le contenu premium"""
        return {
            'articles': self.get_articles(is_premium=True),
            'videos': self.video_tutorials,
            'quizzes': self.quizzes
        }
    
    def get_learning_path(self, level: str) -> List[Dict]:
        """Génère un parcours d'apprentissage personnalisé"""
        if level == "beginner":
            return [
                {"type": "glossary", "category": "bases", "title": "Maîtrisez le vocabulaire"},
                {"type": "article", "id": "basics-forex", "title": "Les bases du Forex"},
                {"type": "article", "id": "risk-management", "title": "Gestion du risque"},
                {"type": "quiz", "id": "forex-basics", "title": "Testez vos connaissances", "premium": True}
            ]
        elif level == "intermediate":
            return [
                {"type": "glossary", "category": "analyse-technique", "title": "Analyse technique"},
                {"type": "video", "id": "setup-metatrader", "title": "Configuration MT5", "premium": True},
                {"type": "article", "id": "advanced-strategies", "title": "Stratégies avancées", "premium": True}
            ]
        
        return []

# Instance globale du centre d'apprentissage
learning_center = LearningCenter()