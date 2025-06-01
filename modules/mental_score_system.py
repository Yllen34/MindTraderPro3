"""
Système de Score Mental - Analyse psychologique et impact sur performance
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import statistics

class MentalState(Enum):
    EXCELLENT = "excellent"  # 9-10
    GOOD = "good"           # 7-8
    AVERAGE = "average"     # 5-6
    POOR = "poor"          # 3-4
    CRITICAL = "critical"   # 1-2

class AlertType(Enum):
    PERFORMANCE_DROP = "performance_drop"
    HIGH_STRESS = "high_stress"
    LOW_CONFIDENCE = "low_confidence"
    EMOTIONAL_INSTABILITY = "emotional_instability"
    TRADING_FREQUENCY = "trading_frequency"

@dataclass
class MentalStateEntry:
    """Entrée d'état mental pour un trade"""
    trade_id: str
    user_session: str
    timestamp: datetime
    
    # États mentaux (1-10)
    confidence_level: int
    stress_level: int
    focus_level: int
    energy_level: int
    patience_level: int
    
    # États émotionnels
    emotional_state: str
    pre_trade_feeling: str
    post_trade_feeling: Optional[str]
    
    # Contexte
    sleep_quality: Optional[int]  # 1-10
    life_stress: Optional[int]    # 1-10
    market_pressure: int          # 1-10
    
    # Résultats du trade
    trade_result: Optional[float]
    trade_success: Optional[bool]
    
    # Score mental calculé
    mental_score: float
    performance_impact: float

@dataclass
class MentalAlert:
    """Alerte basée sur l'état mental"""
    alert_type: AlertType
    severity: str  # low, medium, high, critical
    message: str
    recommendation: str
    should_block_trading: bool
    created_at: datetime

class MentalScoreAnalyzer:
    """Analyseur de score mental et impact sur performance"""
    
    def __init__(self):
        self.mental_entries = {}  # user_session -> List[MentalStateEntry]
        self.active_alerts = {}   # user_session -> List[MentalAlert]
        self.mental_patterns = {}
        
    def record_mental_state(self, trade_data: Dict) -> float:
        """Enregistre l'état mental et calcule le score"""
        
        user_session = trade_data['user_session']
        trade_id = trade_data.get('trade_id', f"trade_{int(datetime.now().timestamp())}")
        
        # Création de l'entrée d'état mental
        entry = MentalStateEntry(
            trade_id=trade_id,
            user_session=user_session,
            timestamp=datetime.now(),
            confidence_level=trade_data.get('confidence_level', 5),
            stress_level=trade_data.get('stress_level', 5),
            focus_level=trade_data.get('focus_level', 7),
            energy_level=trade_data.get('energy_level', 7),
            patience_level=trade_data.get('patience_level', 7),
            emotional_state=trade_data.get('emotional_state', 'calm'),
            pre_trade_feeling=trade_data.get('pre_trade_feeling', 'neutral'),
            post_trade_feeling=None,
            sleep_quality=trade_data.get('sleep_quality'),
            life_stress=trade_data.get('life_stress'),
            market_pressure=trade_data.get('market_pressure', 5),
            trade_result=trade_data.get('profit_loss'),
            trade_success=trade_data.get('profit_loss', 0) > 0 if trade_data.get('profit_loss') is not None else None,
            mental_score=0,
            performance_impact=0
        )
        
        # Calcul du score mental
        entry.mental_score = self._calculate_mental_score(entry)
        
        # Calcul de l'impact sur la performance
        entry.performance_impact = self._calculate_performance_impact(entry)
        
        # Sauvegarde
        if user_session not in self.mental_entries:
            self.mental_entries[user_session] = []
        self.mental_entries[user_session].append(entry)
        
        # Vérification des alertes
        self._check_mental_alerts(user_session, entry)
        
        return entry.mental_score
    
    def _calculate_mental_score(self, entry: MentalStateEntry) -> float:
        """Calcule le score mental global (0-10)"""
        
        # Pondération des différents facteurs
        confidence_weight = 0.25
        stress_weight = 0.20  # Inversé (moins de stress = mieux)
        focus_weight = 0.20
        energy_weight = 0.15
        patience_weight = 0.20
        
        # Normalisation du stress (inverse)
        normalized_stress = 11 - entry.stress_level
        
        # Calcul pondéré
        weighted_score = (
            entry.confidence_level * confidence_weight +
            normalized_stress * stress_weight +
            entry.focus_level * focus_weight +
            entry.energy_level * energy_weight +
            entry.patience_level * patience_weight
        )
        
        # Ajustements émotionnels
        emotional_modifiers = {
            'confident': 0.5,
            'calm': 0.3,
            'excited': 0.0,
            'anxious': -0.5,
            'fearful': -1.0,
            'frustrated': -0.8,
            'euphoric': -0.3  # Dangereux car peut mener à l'overtrading
        }
        
        emotional_adjustment = emotional_modifiers.get(entry.emotional_state, 0)
        
        # Ajustements contextuels
        context_adjustment = 0
        if entry.sleep_quality and entry.sleep_quality < 6:
            context_adjustment -= 0.5
        if entry.life_stress and entry.life_stress > 7:
            context_adjustment -= 0.3
        if entry.market_pressure > 8:
            context_adjustment -= 0.2
        
        final_score = weighted_score + emotional_adjustment + context_adjustment
        
        return max(1.0, min(10.0, final_score))
    
    def _calculate_performance_impact(self, entry: MentalStateEntry) -> float:
        """Calcule l'impact estimé sur la performance (0-1)"""
        
        # Score parfait = impact positif maximal
        if entry.mental_score >= 9:
            return 0.95
        elif entry.mental_score >= 8:
            return 0.85
        elif entry.mental_score >= 7:
            return 0.75
        elif entry.mental_score >= 6:
            return 0.60
        elif entry.mental_score >= 5:
            return 0.45
        elif entry.mental_score >= 4:
            return 0.30
        elif entry.mental_score >= 3:
            return 0.15
        else:
            return 0.05
    
    def _check_mental_alerts(self, user_session: str, entry: MentalStateEntry):
        """Vérifie et génère les alertes basées sur l'état mental"""
        
        if user_session not in self.active_alerts:
            self.active_alerts[user_session] = []
        
        alerts = []
        
        # Alerte stress élevé
        if entry.stress_level >= 8:
            alerts.append(MentalAlert(
                alert_type=AlertType.HIGH_STRESS,
                severity="high" if entry.stress_level >= 9 else "medium",
                message=f"Niveau de stress élevé détecté: {entry.stress_level}/10",
                recommendation="Prenez une pause de 30 minutes et pratiquez la respiration profonde",
                should_block_trading=entry.stress_level >= 9,
                created_at=datetime.now()
            ))
        
        # Alerte confiance faible
        if entry.confidence_level <= 3:
            alerts.append(MentalAlert(
                alert_type=AlertType.LOW_CONFIDENCE,
                severity="high" if entry.confidence_level <= 2 else "medium",
                message=f"Confiance très faible: {entry.confidence_level}/10",
                recommendation="Évitez de trader quand votre confiance est si faible. Analysez vos derniers succès.",
                should_block_trading=entry.confidence_level <= 2,
                created_at=datetime.now()
            ))
        
        # Alerte état émotionnel dangereux
        dangerous_emotions = ['euphoric', 'frustrated', 'fearful']
        if entry.emotional_state in dangerous_emotions:
            alerts.append(MentalAlert(
                alert_type=AlertType.EMOTIONAL_INSTABILITY,
                severity="high" if entry.emotional_state in ['euphoric', 'frustrated'] else "medium",
                message=f"État émotionnel risqué détecté: {entry.emotional_state}",
                recommendation="Les émotions extrêmes nuisent à la prise de décision. Attendez d'être plus calme.",
                should_block_trading=entry.emotional_state in ['euphoric', 'frustrated'],
                created_at=datetime.now()
            ))
        
        # Alerte score mental critique
        if entry.mental_score <= 4:
            alerts.append(MentalAlert(
                alert_type=AlertType.PERFORMANCE_DROP,
                severity="critical",
                message=f"Score mental critique: {entry.mental_score:.1f}/10",
                recommendation="ARRÊTEZ de trader. Votre état mental risque de causer des pertes importantes.",
                should_block_trading=True,
                created_at=datetime.now()
            ))
        
        # Alerte fréquence de trading
        recent_entries = self._get_recent_entries(user_session, hours=2)
        if len(recent_entries) >= 5:
            alerts.append(MentalAlert(
                alert_type=AlertType.TRADING_FREQUENCY,
                severity="medium",
                message=f"{len(recent_entries)} trades en 2 heures - Possible overtrading",
                recommendation="Ralentissez le rythme. L'overtrading est souvent signe de stress ou d'euphorie.",
                should_block_trading=len(recent_entries) >= 8,
                created_at=datetime.now()
            ))
        
        # Ajouter les nouvelles alertes
        self.active_alerts[user_session].extend(alerts)
        
        # Nettoyer les anciennes alertes (> 24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.active_alerts[user_session] = [
            alert for alert in self.active_alerts[user_session]
            if alert.created_at > cutoff
        ]
    
    def _get_recent_entries(self, user_session: str, hours: int = 24) -> List[MentalStateEntry]:
        """Récupère les entrées récentes"""
        if user_session not in self.mental_entries:
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            entry for entry in self.mental_entries[user_session]
            if entry.timestamp > cutoff
        ]
    
    def get_mental_analysis(self, user_session: str, days: int = 30) -> Dict:
        """Analyse complète de l'état mental et performance"""
        
        if user_session not in self.mental_entries:
            return {"message": "Aucune donnée d'état mental enregistrée"}
        
        entries = self.mental_entries[user_session]
        
        if len(entries) < 3:
            return {"message": "Pas assez de données pour une analyse significative"}
        
        # Filtrer par période
        cutoff = datetime.now() - timedelta(days=days)
        recent_entries = [e for e in entries if e.timestamp > cutoff]
        
        if not recent_entries:
            return {"message": f"Aucune donnée dans les {days} derniers jours"}
        
        # Calculs statistiques
        mental_scores = [e.mental_score for e in recent_entries]
        confidence_levels = [e.confidence_level for e in recent_entries]
        stress_levels = [e.stress_level for e in recent_entries]
        
        avg_mental_score = statistics.mean(mental_scores)
        avg_confidence = statistics.mean(confidence_levels)
        avg_stress = statistics.mean(stress_levels)
        
        # Analyse de performance vs état mental
        performance_correlation = self._analyze_performance_correlation(recent_entries)
        
        # Patterns temporels
        time_patterns = self._analyze_time_patterns(recent_entries)
        
        # Recommandations
        recommendations = self._generate_mental_recommendations(recent_entries)
        
        # État mental actuel
        current_state = self._determine_mental_state(avg_mental_score)
        
        return {
            'period': f"{days} derniers jours",
            'total_entries': len(recent_entries),
            'average_mental_score': round(avg_mental_score, 1),
            'average_confidence': round(avg_confidence, 1),
            'average_stress': round(avg_stress, 1),
            'current_mental_state': current_state.value,
            'performance_correlation': performance_correlation,
            'time_patterns': time_patterns,
            'recommendations': recommendations,
            'active_alerts': len(self.active_alerts.get(user_session, [])),
            'mental_stability': self._calculate_stability(mental_scores)
        }
    
    def _analyze_performance_correlation(self, entries: List[MentalStateEntry]) -> Dict:
        """Analyse la corrélation entre état mental et performance"""
        
        # Séparer les trades avec résultats
        successful_trades = [e for e in entries if e.trade_success is True]
        failed_trades = [e for e in entries if e.trade_success is False]
        
        if not successful_trades or not failed_trades:
            return {"message": "Pas assez de données pour analyser la corrélation"}
        
        avg_score_success = statistics.mean([e.mental_score for e in successful_trades])
        avg_score_failure = statistics.mean([e.mental_score for e in failed_trades])
        
        correlation_strength = abs(avg_score_success - avg_score_failure)
        
        return {
            'avg_mental_score_winning_trades': round(avg_score_success, 1),
            'avg_mental_score_losing_trades': round(avg_score_failure, 1),
            'correlation_strength': round(correlation_strength, 1),
            'insight': f"Vous performez {'significativement ' if correlation_strength > 1.5 else ''}mieux avec un score mental de {avg_score_success:.1f} vs {avg_score_failure:.1f}"
        }
    
    def _analyze_time_patterns(self, entries: List[MentalStateEntry]) -> Dict:
        """Analyse les patterns temporels d'état mental"""
        
        hourly_scores = {}
        daily_scores = {}
        
        for entry in entries:
            hour = entry.timestamp.hour
            day = entry.timestamp.strftime('%A')
            
            if hour not in hourly_scores:
                hourly_scores[hour] = []
            hourly_scores[hour].append(entry.mental_score)
            
            if day not in daily_scores:
                daily_scores[day] = []
            daily_scores[day].append(entry.mental_score)
        
        # Trouver les meilleures heures/jours
        best_hour = max(hourly_scores.items(), key=lambda x: statistics.mean(x[1])) if hourly_scores else None
        worst_hour = min(hourly_scores.items(), key=lambda x: statistics.mean(x[1])) if hourly_scores else None
        
        best_day = max(daily_scores.items(), key=lambda x: statistics.mean(x[1])) if daily_scores else None
        worst_day = min(daily_scores.items(), key=lambda x: statistics.mean(x[1])) if daily_scores else None
        
        return {
            'best_trading_hour': f"{best_hour[0]}h (score: {statistics.mean(best_hour[1]):.1f})" if best_hour else None,
            'worst_trading_hour': f"{worst_hour[0]}h (score: {statistics.mean(worst_hour[1]):.1f})" if worst_hour else None,
            'best_trading_day': f"{best_day[0]} (score: {statistics.mean(best_day[1]):.1f})" if best_day else None,
            'worst_trading_day': f"{worst_day[0]} (score: {statistics.mean(worst_day[1]):.1f})" if worst_day else None
        }
    
    def _generate_mental_recommendations(self, entries: List[MentalStateEntry]) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        
        recommendations = []
        
        avg_scores = {
            'confidence': statistics.mean([e.confidence_level for e in entries]),
            'stress': statistics.mean([e.stress_level for e in entries]),
            'focus': statistics.mean([e.focus_level for e in entries]),
            'mental': statistics.mean([e.mental_score for e in entries])
        }
        
        # Recommandations basées sur les moyennes
        if avg_scores['confidence'] < 6:
            recommendations.append("🎯 Travaillez votre confiance : analysez vos succès passés et tenez un journal des réussites")
        
        if avg_scores['stress'] > 6:
            recommendations.append("😌 Gérez votre stress : pratiquez la méditation ou la respiration profonde avant de trader")
        
        if avg_scores['focus'] < 7:
            recommendations.append("🧘 Améliorez votre concentration : éliminez les distractions et créez un environnement de trading dédié")
        
        if avg_scores['mental'] < 6:
            recommendations.append("⚠️ Score mental général faible : considérez réduire la fréquence de trading et vous concentrer sur la qualité")
        
        # Recommandations basées sur les patterns émotionnels
        emotions = [e.emotional_state for e in entries]
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        if emotion_counts.get('anxious', 0) > len(entries) * 0.3:
            recommendations.append("😰 Anxiété fréquente détectée : consultez des ressources sur la psychologie du trading")
        
        if emotion_counts.get('euphoric', 0) > 0:
            recommendations.append("🚨 Évitez l'euphorie : elle mène souvent à l'overtrading et aux erreurs")
        
        return recommendations[:5]  # Limiter à 5 recommandations
    
    def _determine_mental_state(self, avg_score: float) -> MentalState:
        """Détermine l'état mental global"""
        if avg_score >= 9:
            return MentalState.EXCELLENT
        elif avg_score >= 7:
            return MentalState.GOOD
        elif avg_score >= 5:
            return MentalState.AVERAGE
        elif avg_score >= 3:
            return MentalState.POOR
        else:
            return MentalState.CRITICAL
    
    def _calculate_stability(self, scores: List[float]) -> Dict:
        """Calcule la stabilité de l'état mental"""
        if len(scores) < 3:
            return {"stability": "insufficient_data"}
        
        std_dev = statistics.stdev(scores)
        
        if std_dev < 1:
            stability = "très_stable"
        elif std_dev < 2:
            stability = "stable"
        elif std_dev < 3:
            stability = "modérément_variable"
        else:
            stability = "très_variable"
        
        return {
            "stability": stability,
            "standard_deviation": round(std_dev, 2),
            "interpretation": f"Écart-type de {std_dev:.1f} - état mental {stability.replace('_', ' ')}"
        }
    
    def get_active_alerts(self, user_session: str) -> List[MentalAlert]:
        """Récupère les alertes actives"""
        return self.active_alerts.get(user_session, [])
    
    def should_block_trading(self, user_session: str) -> Tuple[bool, List[str]]:
        """Détermine si le trading doit être bloqué"""
        alerts = self.get_active_alerts(user_session)
        
        blocking_alerts = [alert for alert in alerts if alert.should_block_trading]
        
        if not blocking_alerts:
            return False, []
        
        reasons = [alert.message for alert in blocking_alerts]
        return True, reasons
    
    def update_trade_result(self, user_session: str, trade_id: str, result: float, success: bool):
        """Met à jour le résultat d'un trade pour l'analyse"""
        if user_session not in self.mental_entries:
            return
        
        for entry in self.mental_entries[user_session]:
            if entry.trade_id == trade_id:
                entry.trade_result = result
                entry.trade_success = success
                break

# Instance globale de l'analyseur de score mental
mental_analyzer = MentalScoreAnalyzer()