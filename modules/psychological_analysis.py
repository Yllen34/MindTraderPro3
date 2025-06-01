"""
Analyse Psychologique - Suivi des émotions et impact sur la performance
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class EmotionType(Enum):
    CALM = "calme"
    CONFIDENT = "confiant"
    ANXIOUS = "anxieux"
    FEARFUL = "peureux"
    GREEDY = "cupide"
    FRUSTRATED = "frustré"
    EXCITED = "excité"
    DEPRESSED = "déprimé"
    ANGRY = "en_colère"
    EUPHORIC = "euphorique"

class TradingPhase(Enum):
    BEFORE_TRADE = "avant_trade"
    DURING_TRADE = "pendant_trade"
    AFTER_TRADE = "apres_trade"

@dataclass
class EmotionalRecord:
    """Enregistrement émotionnel"""
    record_id: str
    user_session: str
    trade_id: Optional[str]
    timestamp: datetime
    phase: TradingPhase
    
    # États émotionnels (1-10)
    confidence_level: int
    stress_level: int
    fear_level: int
    greed_level: int
    patience_level: int
    
    # Émotions principales
    primary_emotion: EmotionType
    secondary_emotions: List[EmotionType]
    
    # Contexte
    market_conditions: str
    time_of_day: str
    sleep_quality: int  # 1-10
    external_stress: int  # 1-10
    
    # Notes libres
    emotional_notes: str
    trigger_events: List[str]

@dataclass
class PsychologicalProfile:
    """Profil psychologique du trader"""
    user_session: str
    
    # Scores moyens
    avg_confidence: float
    avg_stress: float
    avg_fear: float
    avg_greed: float
    avg_patience: float
    
    # Émotions dominantes
    dominant_emotions: List[EmotionType]
    problematic_emotions: List[EmotionType]
    
    # Patterns identifiés
    best_emotional_state: Dict[str, Any]
    worst_emotional_state: Dict[str, Any]
    
    # Corrélations performance-émotion
    emotion_performance_correlation: Dict[str, float]
    
    # Recommandations
    recommendations: List[str]
    
    created_at: datetime
    last_updated: datetime

class PsychologicalAnalyzer:
    """Analyseur psychologique pour traders"""
    
    def __init__(self):
        self.emotional_records = {}  # user_session -> List[EmotionalRecord]
        self.psychological_profiles = {}  # user_session -> PsychologicalProfile
        self.mental_score_history = {}  # user_session -> List[score_data]
        
    def record_emotional_state(self, user_session: str, emotional_data: Dict) -> str:
        """Enregistre l'état émotionnel d'un trader"""
        
        record_id = f"emotion_{int(datetime.now().timestamp())}_{user_session}"
        
        record = EmotionalRecord(
            record_id=record_id,
            user_session=user_session,
            trade_id=emotional_data.get('trade_id'),
            timestamp=datetime.now(),
            phase=TradingPhase(emotional_data.get('phase', 'before_trade')),
            confidence_level=emotional_data.get('confidence_level', 5),
            stress_level=emotional_data.get('stress_level', 5),
            fear_level=emotional_data.get('fear_level', 5),
            greed_level=emotional_data.get('greed_level', 5),
            patience_level=emotional_data.get('patience_level', 5),
            primary_emotion=EmotionType(emotional_data.get('primary_emotion', 'calm')),
            secondary_emotions=[EmotionType(e) for e in emotional_data.get('secondary_emotions', [])],
            market_conditions=emotional_data.get('market_conditions', 'normal'),
            time_of_day=emotional_data.get('time_of_day', 'morning'),
            sleep_quality=emotional_data.get('sleep_quality', 7),
            external_stress=emotional_data.get('external_stress', 3),
            emotional_notes=emotional_data.get('emotional_notes', ''),
            trigger_events=emotional_data.get('trigger_events', [])
        )
        
        # Sauvegarder l'enregistrement
        if user_session not in self.emotional_records:
            self.emotional_records[user_session] = []
        
        self.emotional_records[user_session].append(record)
        
        # Mettre à jour le profil psychologique
        self._update_psychological_profile(user_session)
        
        return record_id
    
    def calculate_mental_score(self, user_session: str, emotional_data: Dict) -> Dict:
        """Calcule le score mental global (1-10)"""
        
        # Facteurs positifs
        confidence = emotional_data.get('confidence_level', 5)
        patience = emotional_data.get('patience_level', 5)
        sleep_quality = emotional_data.get('sleep_quality', 7)
        
        # Facteurs négatifs
        stress = emotional_data.get('stress_level', 5)
        fear = emotional_data.get('fear_level', 5)
        greed = emotional_data.get('greed_level', 5)
        external_stress = emotional_data.get('external_stress', 3)
        
        # Calcul du score mental (pondéré)
        positive_score = (confidence * 0.3 + patience * 0.3 + sleep_quality * 0.2) / 3
        negative_score = (stress * 0.25 + fear * 0.25 + greed * 0.25 + external_stress * 0.25) / 4
        
        mental_score = max(1, min(10, positive_score - (negative_score - 5)))
        
        # Déterminer la qualité de l'état mental
        if mental_score >= 8:
            mental_state = "excellent"
            trade_recommendation = "Conditions optimales pour trader"
            color = "success"
        elif mental_score >= 6:
            mental_state = "bon"
            trade_recommendation = "État mental favorable pour le trading"
            color = "info"
        elif mental_score >= 4:
            mental_state = "moyen"
            trade_recommendation = "Soyez prudent, état mental mitigé"
            color = "warning"
        else:
            mental_state = "problématique"
            trade_recommendation = "Évitez de trader, état mental défavorable"
            color = "danger"
        
        score_data = {
            'mental_score': round(mental_score, 1),
            'mental_state': mental_state,
            'trade_recommendation': trade_recommendation,
            'color': color,
            'timestamp': datetime.now().isoformat(),
            'factors': {
                'positive': {
                    'confidence': confidence,
                    'patience': patience,
                    'sleep_quality': sleep_quality
                },
                'negative': {
                    'stress': stress,
                    'fear': fear,
                    'greed': greed,
                    'external_stress': external_stress
                }
            }
        }
        
        # Sauvegarder l'historique
        if user_session not in self.mental_score_history:
            self.mental_score_history[user_session] = []
        
        self.mental_score_history[user_session].append(score_data)
        
        return score_data
    
    def generate_psychological_report(self, user_session: str) -> Dict:
        """Génère un rapport psychologique complet"""
        
        records = self.emotional_records.get(user_session, [])
        if not records:
            return {
                'success': False,
                'error': 'Aucune donnée émotionnelle disponible'
            }
        
        # Analyser les 30 derniers jours
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_records = [r for r in records if r.timestamp > cutoff_date]
        
        if not recent_records:
            return {
                'success': False,
                'error': 'Aucune donnée récente disponible'
            }
        
        # Calculs statistiques
        avg_confidence = sum(r.confidence_level for r in recent_records) / len(recent_records)
        avg_stress = sum(r.stress_level for r in recent_records) / len(recent_records)
        avg_fear = sum(r.fear_level for r in recent_records) / len(recent_records)
        avg_patience = sum(r.patience_level for r in recent_records) / len(recent_records)
        
        # Émotions les plus fréquentes
        emotion_counts = {}
        for record in recent_records:
            emotion = record.primary_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyse des patterns temporels
        time_patterns = self._analyze_time_patterns(recent_records)
        
        # Corrélations émotions-performance
        performance_correlations = self._analyze_emotion_performance(user_session, recent_records)
        
        # Recommandations personnalisées
        recommendations = self._generate_recommendations(recent_records, performance_correlations)
        
        report = {
            'success': True,
            'period': '30 derniers jours',
            'total_records': len(recent_records),
            'emotional_summary': {
                'avg_confidence': round(avg_confidence, 1),
                'avg_stress': round(avg_stress, 1),
                'avg_fear': round(avg_fear, 1),
                'avg_patience': round(avg_patience, 1),
                'dominant_emotions': dominant_emotions
            },
            'time_patterns': time_patterns,
            'performance_correlations': performance_correlations,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _analyze_time_patterns(self, records: List[EmotionalRecord]) -> Dict:
        """Analyse les patterns temporels des émotions"""
        
        # Analyse par moment de la journée
        time_emotions = {}
        for record in records:
            time_period = record.time_of_day
            if time_period not in time_emotions:
                time_emotions[time_period] = {
                    'confidence': [],
                    'stress': [],
                    'count': 0
                }
            
            time_emotions[time_period]['confidence'].append(record.confidence_level)
            time_emotions[time_period]['stress'].append(record.stress_level)
            time_emotions[time_period]['count'] += 1
        
        # Calculer les moyennes
        time_analysis = {}
        for period, data in time_emotions.items():
            if data['count'] > 0:
                time_analysis[period] = {
                    'avg_confidence': round(sum(data['confidence']) / len(data['confidence']), 1),
                    'avg_stress': round(sum(data['stress']) / len(data['stress']), 1),
                    'sample_size': data['count']
                }
        
        return time_analysis
    
    def _analyze_emotion_performance(self, user_session: str, records: List[EmotionalRecord]) -> Dict:
        """Analyse la corrélation entre émotions et performance"""
        
        # Simulation de corrélations (en production, utiliser les vraies performances)
        correlations = {
            'confidence_vs_performance': 0.75,
            'stress_vs_performance': -0.45,
            'fear_vs_performance': -0.60,
            'patience_vs_performance': 0.80,
            'sleep_quality_vs_performance': 0.65
        }
        
        return correlations
    
    def _generate_recommendations(self, records: List[EmotionalRecord], correlations: Dict) -> List[str]:
        """Génère des recommandations personnalisées"""
        
        recommendations = []
        
        # Analyser les niveaux moyens
        avg_stress = sum(r.stress_level for r in records) / len(records)
        avg_confidence = sum(r.confidence_level for r in records) / len(records)
        avg_patience = sum(r.patience_level for r in records) / len(records)
        
        if avg_stress > 7:
            recommendations.append("🧘 Votre niveau de stress est élevé. Essayez des techniques de relaxation avant de trader.")
        
        if avg_confidence < 5:
            recommendations.append("💪 Travaillez sur votre confiance en vous. Commencez par des positions plus petites.")
        
        if avg_patience < 5:
            recommendations.append("⏰ Développez votre patience. Les meilleures opportunités demandent d'attendre.")
        
        # Recommandations basées sur les corrélations
        if correlations.get('sleep_quality_vs_performance', 0) > 0.5:
            recommendations.append("😴 Votre sommeil impacte vos performances. Visez 7-8h de sommeil par nuit.")
        
        # Analyse des émotions dominantes
        emotion_counts = {}
        for record in records:
            emotion = record.primary_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        if emotion_counts.get('anxieux', 0) > len(records) * 0.3:
            recommendations.append("😰 Vous ressentez souvent de l'anxiété. Réduisez la taille de vos positions.")
        
        if emotion_counts.get('cupide', 0) > len(records) * 0.2:
            recommendations.append("💰 Attention à la cupidité. Respectez vos objectifs de Take Profit.")
        
        if not recommendations:
            recommendations.append("🎯 Votre équilibre émotionnel semble bon. Continuez ainsi !")
        
        return recommendations
    
    def _update_psychological_profile(self, user_session: str):
        """Met à jour le profil psychologique"""
        
        records = self.emotional_records.get(user_session, [])
        if len(records) < 5:  # Besoin d'au moins 5 enregistrements
            return
        
        # Calculer les moyennes sur les 30 derniers jours
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_records = [r for r in records if r.timestamp > cutoff_date]
        
        if not recent_records:
            return
        
        avg_confidence = sum(r.confidence_level for r in recent_records) / len(recent_records)
        avg_stress = sum(r.stress_level for r in recent_records) / len(recent_records)
        avg_fear = sum(r.fear_level for r in recent_records) / len(recent_records)
        avg_greed = sum(r.greed_level for r in recent_records) / len(recent_records)
        avg_patience = sum(r.patience_level for r in recent_records) / len(recent_records)
        
        # Identifier les émotions dominantes
        emotion_counts = {}
        for record in recent_records:
            emotion = record.primary_emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotions = sorted(emotion_counts.keys(), key=lambda x: emotion_counts[x], reverse=True)[:3]
        
        # Identifier les émotions problématiques (stress, peur, cupidité élevés)
        problematic_emotions = []
        if avg_stress > 7:
            problematic_emotions.append(EmotionType.ANXIOUS)
        if avg_fear > 7:
            problematic_emotions.append(EmotionType.FEARFUL)
        if avg_greed > 7:
            problematic_emotions.append(EmotionType.GREEDY)
        
        profile = PsychologicalProfile(
            user_session=user_session,
            avg_confidence=avg_confidence,
            avg_stress=avg_stress,
            avg_fear=avg_fear,
            avg_greed=avg_greed,
            avg_patience=avg_patience,
            dominant_emotions=dominant_emotions,
            problematic_emotions=problematic_emotions,
            best_emotional_state={
                'confidence': max(r.confidence_level for r in recent_records),
                'stress': min(r.stress_level for r in recent_records),
                'description': 'État optimal identifié'
            },
            worst_emotional_state={
                'confidence': min(r.confidence_level for r in recent_records),
                'stress': max(r.stress_level for r in recent_records),
                'description': 'État problématique identifié'
            },
            emotion_performance_correlation={
                'confidence': 0.75,  # Simulation
                'stress': -0.45,
                'patience': 0.80
            },
            recommendations=self._generate_recommendations(recent_records, {}),
            created_at=datetime.now() if user_session not in self.psychological_profiles else self.psychological_profiles[user_session].created_at,
            last_updated=datetime.now()
        )
        
        self.psychological_profiles[user_session] = profile
    
    def get_mental_score_history(self, user_session: str, days: int = 30) -> List[Dict]:
        """Récupère l'historique des scores mentaux"""
        
        history = self.mental_score_history.get(user_session, [])
        
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            history = [
                score for score in history 
                if datetime.fromisoformat(score['timestamp']) > cutoff_date
            ]
        
        return history
    
    def get_emotional_insights(self, user_session: str) -> Dict:
        """Génère des insights émotionnels rapides"""
        
        records = self.emotional_records.get(user_session, [])
        if not records:
            return {
                'message': 'Commencez à enregistrer vos émotions pour recevoir des insights !',
                'insights': []
            }
        
        recent_records = records[-10:] if len(records) >= 10 else records
        
        insights = []
        
        # Analyse de tendance
        if len(recent_records) >= 5:
            recent_confidence = [r.confidence_level for r in recent_records[-5:]]
            if recent_confidence[-1] > recent_confidence[0]:
                insights.append("📈 Votre confiance s'améliore ces derniers temps !")
            elif recent_confidence[-1] < recent_confidence[0]:
                insights.append("📉 Votre confiance diminue. Prenez du recul.")
        
        # Analyse du stress
        avg_stress = sum(r.stress_level for r in recent_records) / len(recent_records)
        if avg_stress > 7:
            insights.append("🚨 Votre niveau de stress est élevé. Réduisez la taille de vos positions.")
        elif avg_stress < 4:
            insights.append("😌 Vous gérez bien votre stress. Excellente discipline !")
        
        # Analyse des patterns
        if len(recent_records) >= 3:
            morning_records = [r for r in recent_records if r.time_of_day == 'morning']
            if len(morning_records) >= 2:
                avg_morning_confidence = sum(r.confidence_level for r in morning_records) / len(morning_records)
                if avg_morning_confidence > 7:
                    insights.append("🌅 Vous êtes plus confiant le matin. Privilégiez cette période !")
        
        return {
            'message': f'Analyse basée sur vos {len(recent_records)} derniers enregistrements',
            'insights': insights
        }

# Instance globale de l'analyseur psychologique
psychological_analyzer = PsychologicalAnalyzer()