"""
Scanner de Journal Intelligent - Analyse avancée des patterns et insights automatiques
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
import statistics

class InsightType(Enum):
    TIME_PATTERN = "time_pattern"
    SYMBOL_PERFORMANCE = "symbol_performance"
    EMOTIONAL_CORRELATION = "emotional_correlation"
    RISK_BEHAVIOR = "risk_behavior"
    STRATEGY_EFFECTIVENESS = "strategy_effectiveness"
    MARKET_CONDITION = "market_condition"
    LEARNING_OPPORTUNITY = "learning_opportunity"

class InsightPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class TradingInsight:
    """Insight généré par l'analyse intelligente"""
    insight_id: str
    user_session: str
    insight_type: InsightType
    priority: InsightPriority
    
    # Contenu
    title: str
    description: str
    recommendation: str
    
    # Données supportant l'insight
    supporting_data: Dict[str, Any]
    confidence_score: float
    
    # Métadonnées
    data_period: str
    trades_analyzed: int
    
    generated_at: datetime
    is_actionable: bool
    tags: List[str]

@dataclass
class PatternAnalysis:
    """Analyse de pattern détaillée"""
    pattern_type: str
    pattern_strength: float
    sample_size: int
    statistical_significance: float
    details: Dict[str, Any]

class IntelligentJournalScanner:
    """Scanner intelligent pour analyser les patterns de trading"""
    
    def __init__(self):
        self.user_insights = {}  # user_session -> List[TradingInsight]
        self.pattern_cache = {}  # Cache des analyses récentes
        
    def analyze_trading_patterns(self, user_session: str, trades_data: List[Dict], 
                               analysis_period: int = 30) -> Dict:
        """Analyse complète des patterns de trading"""
        
        if not trades_data:
            return {
                'success': False,
                'error': 'Aucune donnée de trading disponible'
            }
        
        # Filtrer les trades de la période
        cutoff_date = datetime.now() - timedelta(days=analysis_period)
        recent_trades = [
            trade for trade in trades_data 
            if datetime.fromisoformat(trade.get('open_time', '2023-01-01')) > cutoff_date
        ]
        
        if len(recent_trades) < 5:
            return {
                'success': False,
                'error': 'Données insuffisantes pour l\'analyse (minimum 5 trades)'
            }
        
        # Effectuer les différentes analyses
        insights = []
        
        # 1. Analyse des patterns temporels
        time_insights = self._analyze_time_patterns(user_session, recent_trades)
        insights.extend(time_insights)
        
        # 2. Analyse des performances par symbole
        symbol_insights = self._analyze_symbol_performance(user_session, recent_trades)
        insights.extend(symbol_insights)
        
        # 3. Analyse des corrélations émotionnelles
        emotional_insights = self._analyze_emotional_patterns(user_session, recent_trades)
        insights.extend(emotional_insights)
        
        # 4. Analyse du comportement de risque
        risk_insights = self._analyze_risk_behavior(user_session, recent_trades)
        insights.extend(risk_insights)
        
        # 5. Analyse de l'efficacité des stratégies
        strategy_insights = self._analyze_strategy_effectiveness(user_session, recent_trades)
        insights.extend(strategy_insights)
        
        # 6. Opportunités d'apprentissage
        learning_insights = self._identify_learning_opportunities(user_session, recent_trades)
        insights.extend(learning_insights)
        
        # Trier par priorité et confiance
        insights.sort(key=lambda x: (x.priority.value, -x.confidence_score))
        
        # Sauvegarder les insights
        self.user_insights[user_session] = insights
        
        return {
            'success': True,
            'insights_count': len(insights),
            'insights': [self._insight_to_dict(insight) for insight in insights[:10]],  # Top 10
            'analysis_summary': self._generate_analysis_summary(recent_trades, insights),
            'recommendations': self._generate_top_recommendations(insights)
        }
    
    def _analyze_time_patterns(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Analyse les patterns temporels de trading"""
        
        insights = []
        
        # Analyser par heure de la journée
        hourly_performance = defaultdict(list)
        for trade in trades:
            if trade.get('close_time') and trade.get('profit_loss') is not None:
                hour = datetime.fromisoformat(trade['open_time']).hour
                hourly_performance[hour].append(float(trade['profit_loss']))
        
        # Identifier les meilleures et pires heures
        hourly_stats = {}
        for hour, profits in hourly_performance.items():
            if len(profits) >= 3:  # Minimum 3 trades pour être significatif
                win_rate = len([p for p in profits if p > 0]) / len(profits) * 100
                avg_profit = sum(profits) / len(profits)
                hourly_stats[hour] = {
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'trade_count': len(profits),
                    'total_profit': sum(profits)
                }
        
        if hourly_stats:
            # Meilleure heure
            best_hour = max(hourly_stats.items(), key=lambda x: x[1]['win_rate'])
            if best_hour[1]['win_rate'] > 70 and best_hour[1]['trade_count'] >= 3:
                insights.append(TradingInsight(
                    insight_id=f"time_best_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.TIME_PATTERN,
                    priority=InsightPriority.HIGH,
                    title=f"🕐 Vous excellez à {best_hour[0]:02d}h00",
                    description=f"Votre taux de réussite à {best_hour[0]:02d}h00 est de {best_hour[1]['win_rate']:.1f}% sur {best_hour[1]['trade_count']} trades.",
                    recommendation=f"Concentrez vos efforts de trading autour de {best_hour[0]:02d}h00 pour maximiser vos performances.",
                    supporting_data={
                        'hour': best_hour[0],
                        'win_rate': best_hour[1]['win_rate'],
                        'avg_profit': best_hour[1]['avg_profit'],
                        'trade_count': best_hour[1]['trade_count']
                    },
                    confidence_score=0.85,
                    data_period="30 derniers jours",
                    trades_analyzed=best_hour[1]['trade_count'],
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["timing", "performance", "optimization"]
                ))
            
            # Pire heure
            worst_hour = min(hourly_stats.items(), key=lambda x: x[1]['win_rate'])
            if worst_hour[1]['win_rate'] < 40 and worst_hour[1]['trade_count'] >= 3:
                insights.append(TradingInsight(
                    insight_id=f"time_worst_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.TIME_PATTERN,
                    priority=InsightPriority.MEDIUM,
                    title=f"⚠️ Difficultés à {worst_hour[0]:02d}h00",
                    description=f"Votre taux de réussite à {worst_hour[0]:02d}h00 n'est que de {worst_hour[1]['win_rate']:.1f}%.",
                    recommendation=f"Évitez de trader à {worst_hour[0]:02d}h00 ou analysez pourquoi cette période est difficile.",
                    supporting_data={
                        'hour': worst_hour[0],
                        'win_rate': worst_hour[1]['win_rate'],
                        'avg_profit': worst_hour[1]['avg_profit'],
                        'trade_count': worst_hour[1]['trade_count']
                    },
                    confidence_score=0.75,
                    data_period="30 derniers jours",
                    trades_analyzed=worst_hour[1]['trade_count'],
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["timing", "risk", "avoidance"]
                ))
        
        # Analyser par jour de la semaine
        daily_performance = defaultdict(list)
        for trade in trades:
            if trade.get('close_time') and trade.get('profit_loss') is not None:
                weekday = datetime.fromisoformat(trade['open_time']).weekday()
                daily_performance[weekday].append(float(trade['profit_loss']))
        
        # Identifier le meilleur jour
        daily_stats = {}
        weekday_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        for day, profits in daily_performance.items():
            if len(profits) >= 2:
                win_rate = len([p for p in profits if p > 0]) / len(profits) * 100
                daily_stats[day] = {
                    'win_rate': win_rate,
                    'avg_profit': sum(profits) / len(profits),
                    'trade_count': len(profits)
                }
        
        if daily_stats:
            best_day = max(daily_stats.items(), key=lambda x: x[1]['win_rate'])
            if best_day[1]['win_rate'] > 65:
                insights.append(TradingInsight(
                    insight_id=f"day_best_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.TIME_PATTERN,
                    priority=InsightPriority.MEDIUM,
                    title=f"📅 Le {weekday_names[best_day[0]]} vous réussit",
                    description=f"Votre taux de réussite le {weekday_names[best_day[0]]} est de {best_day[1]['win_rate']:.1f}%.",
                    recommendation=f"Planifiez vos trades les plus importants le {weekday_names[best_day[0]]}.",
                    supporting_data={
                        'weekday': best_day[0],
                        'weekday_name': weekday_names[best_day[0]],
                        'win_rate': best_day[1]['win_rate'],
                        'trade_count': best_day[1]['trade_count']
                    },
                    confidence_score=0.70,
                    data_period="30 derniers jours",
                    trades_analyzed=best_day[1]['trade_count'],
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["timing", "weekly", "planning"]
                ))
        
        return insights
    
    def _analyze_symbol_performance(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Analyse les performances par symbole"""
        
        insights = []
        symbol_stats = defaultdict(lambda: {'profits': [], 'trades': 0, 'wins': 0})
        
        for trade in trades:
            if trade.get('close_time') and trade.get('profit_loss') is not None:
                symbol = trade.get('symbol', 'UNKNOWN')
                profit = float(trade['profit_loss'])
                
                symbol_stats[symbol]['profits'].append(profit)
                symbol_stats[symbol]['trades'] += 1
                if profit > 0:
                    symbol_stats[symbol]['wins'] += 1
        
        # Analyser chaque symbole avec suffisamment de trades
        for symbol, stats in symbol_stats.items():
            if stats['trades'] >= 3:
                win_rate = (stats['wins'] / stats['trades']) * 100
                avg_profit = sum(stats['profits']) / len(stats['profits'])
                total_profit = sum(stats['profits'])
                
                # Symbole performant
                if win_rate > 70 and total_profit > 0:
                    insights.append(TradingInsight(
                        insight_id=f"symbol_good_{symbol}_{int(datetime.now().timestamp())}",
                        user_session=user_session,
                        insight_type=InsightType.SYMBOL_PERFORMANCE,
                        priority=InsightPriority.HIGH,
                        title=f"🎯 Excellent sur {symbol}",
                        description=f"Votre taux de réussite sur {symbol} est de {win_rate:.1f}% avec {total_profit:.2f}€ de profit total.",
                        recommendation=f"Augmentez votre exposition sur {symbol} et analysez ce qui fonctionne bien sur cette paire.",
                        supporting_data={
                            'symbol': symbol,
                            'win_rate': win_rate,
                            'total_profit': total_profit,
                            'avg_profit': avg_profit,
                            'trade_count': stats['trades']
                        },
                        confidence_score=0.80,
                        data_period="30 derniers jours",
                        trades_analyzed=stats['trades'],
                        generated_at=datetime.now(),
                        is_actionable=True,
                        tags=["symbol", "performance", "focus"]
                    ))
                
                # Symbole problématique
                elif win_rate < 40 or (total_profit < -100 and stats['trades'] >= 5):
                    insights.append(TradingInsight(
                        insight_id=f"symbol_bad_{symbol}_{int(datetime.now().timestamp())}",
                        user_session=user_session,
                        insight_type=InsightType.SYMBOL_PERFORMANCE,
                        priority=InsightPriority.HIGH,
                        title=f"🚨 Difficultés sur {symbol}",
                        description=f"Votre taux de réussite sur {symbol} n'est que de {win_rate:.1f}% avec {total_profit:.2f}€ de résultat.",
                        recommendation=f"Évitez temporairement {symbol} ou révisez votre approche sur cette paire.",
                        supporting_data={
                            'symbol': symbol,
                            'win_rate': win_rate,
                            'total_profit': total_profit,
                            'avg_profit': avg_profit,
                            'trade_count': stats['trades']
                        },
                        confidence_score=0.85,
                        data_period="30 derniers jours",
                        trades_analyzed=stats['trades'],
                        generated_at=datetime.now(),
                        is_actionable=True,
                        tags=["symbol", "risk", "avoidance"]
                    ))
        
        return insights
    
    def _analyze_emotional_patterns(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Analyse les corrélations entre émotions et performance"""
        
        insights = []
        
        # Simuler l'analyse émotionnelle (en production, utiliser vraies données)
        emotion_performance = {
            'calm': {'trades': 8, 'wins': 6, 'avg_profit': 45.2},
            'confident': {'trades': 12, 'wins': 8, 'avg_profit': 32.1},
            'anxious': {'trades': 6, 'wins': 2, 'avg_profit': -23.5},
            'frustrated': {'trades': 4, 'wins': 1, 'avg_profit': -45.0}
        }
        
        for emotion, stats in emotion_performance.items():
            if stats['trades'] >= 3:
                win_rate = (stats['wins'] / stats['trades']) * 100
                
                if emotion in ['calm', 'confident'] and win_rate > 65:
                    insights.append(TradingInsight(
                        insight_id=f"emotion_good_{emotion}_{int(datetime.now().timestamp())}",
                        user_session=user_session,
                        insight_type=InsightType.EMOTIONAL_CORRELATION,
                        priority=InsightPriority.MEDIUM,
                        title=f"😌 Vous tradez mieux quand vous êtes {emotion}",
                        description=f"Quand vous vous sentez {emotion}, votre taux de réussite est de {win_rate:.1f}%.",
                        recommendation=f"Attendez d'être dans un état {emotion} avant de trader ou travaillez à maintenir cet état.",
                        supporting_data={
                            'emotion': emotion,
                            'win_rate': win_rate,
                            'avg_profit': stats['avg_profit'],
                            'trade_count': stats['trades']
                        },
                        confidence_score=0.75,
                        data_period="30 derniers jours",
                        trades_analyzed=stats['trades'],
                        generated_at=datetime.now(),
                        is_actionable=True,
                        tags=["emotion", "psychology", "optimization"]
                    ))
                
                elif emotion in ['anxious', 'frustrated'] and win_rate < 40:
                    insights.append(TradingInsight(
                        insight_id=f"emotion_bad_{emotion}_{int(datetime.now().timestamp())}",
                        user_session=user_session,
                        insight_type=InsightType.EMOTIONAL_CORRELATION,
                        priority=InsightPriority.HIGH,
                        title=f"😰 Évitez de trader quand vous êtes {emotion}",
                        description=f"Votre taux de réussite chute à {win_rate:.1f}% quand vous vous sentez {emotion}.",
                        recommendation=f"Prenez une pause quand vous êtes {emotion}. Utilisez des techniques de relaxation.",
                        supporting_data={
                            'emotion': emotion,
                            'win_rate': win_rate,
                            'avg_profit': stats['avg_profit'],
                            'trade_count': stats['trades']
                        },
                        confidence_score=0.80,
                        data_period="30 derniers jours",
                        trades_analyzed=stats['trades'],
                        generated_at=datetime.now(),
                        is_actionable=True,
                        tags=["emotion", "psychology", "risk"]
                    ))
        
        return insights
    
    def _analyze_risk_behavior(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Analyse le comportement de gestion du risque"""
        
        insights = []
        
        # Analyser le respect du stop loss
        sl_respected = 0
        sl_moved = 0
        total_with_sl = 0
        
        risk_percentages = []
        
        for trade in trades:
            if trade.get('stop_loss'):
                total_with_sl += 1
                # Simulation de l'analyse SL (en production, analyser vraiment)
                if trade.get('sl_respected', True):  # Simulation
                    sl_respected += 1
                else:
                    sl_moved += 1
            
            if trade.get('risk_percent'):
                risk_percentages.append(float(trade['risk_percent']))
        
        # Insight sur le respect du SL
        if total_with_sl >= 5:
            sl_respect_rate = (sl_respected / total_with_sl) * 100
            
            if sl_respect_rate < 70:
                insights.append(TradingInsight(
                    insight_id=f"risk_sl_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.RISK_BEHAVIOR,
                    priority=InsightPriority.CRITICAL,
                    title="🚨 Problème de discipline avec les Stop Loss",
                    description=f"Vous ne respectez vos Stop Loss que dans {sl_respect_rate:.1f}% des cas.",
                    recommendation="Utilisez des ordres stop automatiques ou réduisez la taille de vos positions.",
                    supporting_data={
                        'sl_respect_rate': sl_respect_rate,
                        'sl_respected': sl_respected,
                        'sl_moved': sl_moved,
                        'total_with_sl': total_with_sl
                    },
                    confidence_score=0.90,
                    data_period="30 derniers jours",
                    trades_analyzed=total_with_sl,
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["risk", "discipline", "critical"]
                ))
        
        # Analyser les pourcentages de risque
        if risk_percentages:
            avg_risk = statistics.mean(risk_percentages)
            max_risk = max(risk_percentages)
            over_limit = len([r for r in risk_percentages if r > 2.0])
            
            if avg_risk > 2.5:
                insights.append(TradingInsight(
                    insight_id=f"risk_high_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.RISK_BEHAVIOR,
                    priority=InsightPriority.HIGH,
                    title="⚠️ Risque moyen trop élevé",
                    description=f"Votre risque moyen par trade est de {avg_risk:.1f}%, au-dessus de la limite recommandée de 2%.",
                    recommendation="Réduisez systématiquement vos tailles de position pour rester sous 2% par trade.",
                    supporting_data={
                        'avg_risk': avg_risk,
                        'max_risk': max_risk,
                        'over_limit_count': over_limit,
                        'total_trades': len(risk_percentages)
                    },
                    confidence_score=0.85,
                    data_period="30 derniers jours",
                    trades_analyzed=len(risk_percentages),
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["risk", "money-management", "discipline"]
                ))
        
        return insights
    
    def _analyze_strategy_effectiveness(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Analyse l'efficacité des différentes stratégies"""
        
        insights = []
        strategy_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'profits': []})
        
        for trade in trades:
            if trade.get('close_time') and trade.get('profit_loss') is not None:
                strategy = trade.get('strategy', 'unknown')
                profit = float(trade['profit_loss'])
                
                strategy_stats[strategy]['trades'] += 1
                strategy_stats[strategy]['profits'].append(profit)
                if profit > 0:
                    strategy_stats[strategy]['wins'] += 1
        
        for strategy, stats in strategy_stats.items():
            if stats['trades'] >= 3 and strategy != 'unknown':
                win_rate = (stats['wins'] / stats['trades']) * 100
                total_profit = sum(stats['profits'])
                
                if win_rate > 70 and total_profit > 0:
                    insights.append(TradingInsight(
                        insight_id=f"strategy_good_{strategy}_{int(datetime.now().timestamp())}",
                        user_session=user_session,
                        insight_type=InsightType.STRATEGY_EFFECTIVENESS,
                        priority=InsightPriority.MEDIUM,
                        title=f"📈 La stratégie {strategy} fonctionne bien",
                        description=f"Votre stratégie {strategy} a un taux de réussite de {win_rate:.1f}%.",
                        recommendation=f"Concentrez-vous davantage sur la stratégie {strategy} et perfectionnez-la.",
                        supporting_data={
                            'strategy': strategy,
                            'win_rate': win_rate,
                            'total_profit': total_profit,
                            'trade_count': stats['trades']
                        },
                        confidence_score=0.75,
                        data_period="30 derniers jours",
                        trades_analyzed=stats['trades'],
                        generated_at=datetime.now(),
                        is_actionable=True,
                        tags=["strategy", "performance", "focus"]
                    ))
        
        return insights
    
    def _identify_learning_opportunities(self, user_session: str, trades: List[Dict]) -> List[TradingInsight]:
        """Identifie les opportunités d'apprentissage"""
        
        insights = []
        
        # Analyser les trades perdants pour identifier des patterns
        losing_trades = [t for t in trades if t.get('profit_loss', 0) < 0]
        
        if len(losing_trades) >= 3:
            # Analyser les raisons de perte les plus communes
            loss_reasons = Counter()
            for trade in losing_trades:
                reason = trade.get('loss_reason', 'non_specified')
                loss_reasons[reason] += 1
            
            most_common_reason = loss_reasons.most_common(1)
            if most_common_reason and most_common_reason[0][1] >= 2:
                reason, count = most_common_reason[0]
                
                insights.append(TradingInsight(
                    insight_id=f"learning_{reason}_{int(datetime.now().timestamp())}",
                    user_session=user_session,
                    insight_type=InsightType.LEARNING_OPPORTUNITY,
                    priority=InsightPriority.MEDIUM,
                    title=f"📚 Opportunité d'apprentissage: {reason}",
                    description=f"Vous avez {count} trades perdants liés à '{reason}'. C'est une zone d'amélioration claire.",
                    recommendation=f"Étudiez spécifiquement comment éviter les pertes liées à '{reason}'. Consultez nos ressources d'apprentissage.",
                    supporting_data={
                        'loss_reason': reason,
                        'occurrence_count': count,
                        'total_losing_trades': len(losing_trades)
                    },
                    confidence_score=0.70,
                    data_period="30 derniers jours",
                    trades_analyzed=len(losing_trades),
                    generated_at=datetime.now(),
                    is_actionable=True,
                    tags=["learning", "improvement", "education"]
                ))
        
        return insights
    
    def _generate_analysis_summary(self, trades: List[Dict], insights: List[TradingInsight]) -> Dict:
        """Génère un résumé de l'analyse"""
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('profit_loss', 0) > 0])
        total_profit = sum(float(t.get('profit_loss', 0)) for t in trades)
        
        critical_insights = len([i for i in insights if i.priority == InsightPriority.CRITICAL])
        high_insights = len([i for i in insights if i.priority == InsightPriority.HIGH])
        
        return {
            'total_trades_analyzed': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_profit': total_profit,
            'insights_generated': len(insights),
            'critical_issues': critical_insights,
            'high_priority_opportunities': high_insights,
            'analysis_date': datetime.now().isoformat()
        }
    
    def _generate_top_recommendations(self, insights: List[TradingInsight]) -> List[str]:
        """Génère les recommandations prioritaires"""
        
        # Prendre les 3 insights les plus prioritaires et actionnables
        top_insights = [i for i in insights if i.is_actionable][:3]
        
        return [insight.recommendation for insight in top_insights]
    
    def get_user_insights(self, user_session: str, priority: Optional[str] = None) -> List[Dict]:
        """Récupère les insights d'un utilisateur"""
        
        insights = self.user_insights.get(user_session, [])
        
        if priority:
            try:
                priority_enum = InsightPriority(priority)
                insights = [i for i in insights if i.priority == priority_enum]
            except ValueError:
                pass
        
        return [self._insight_to_dict(insight) for insight in insights]
    
    def _insight_to_dict(self, insight: TradingInsight) -> Dict:
        """Convertit un insight en dictionnaire"""
        
        return {
            'insight_id': insight.insight_id,
            'insight_type': insight.insight_type.value,
            'priority': insight.priority.value,
            'title': insight.title,
            'description': insight.description,
            'recommendation': insight.recommendation,
            'supporting_data': insight.supporting_data,
            'confidence_score': insight.confidence_score,
            'data_period': insight.data_period,
            'trades_analyzed': insight.trades_analyzed,
            'generated_at': insight.generated_at.isoformat(),
            'is_actionable': insight.is_actionable,
            'tags': insight.tags
        }

# Instance globale du scanner intelligent
intelligent_journal_scanner = IntelligentJournalScanner()