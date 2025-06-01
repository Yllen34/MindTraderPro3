"""
Analyse de Performance Avancée - Analytics et détection de patterns
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict
import statistics

@dataclass
class PerformanceMetrics:
    """Métriques de performance d'un trader"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    risk_reward_ratio: float

@dataclass
class TradingPattern:
    """Pattern de trading détecté"""
    pattern_id: str
    name: str
    description: str
    frequency: int
    success_rate: float
    average_profit: float
    conditions: Dict
    recommendations: List[str]

@dataclass
class TimeAnalysis:
    """Analyse temporelle des performances"""
    hour: int
    day_of_week: int
    total_trades: int
    win_rate: float
    average_profit: float
    recommended: bool

class AdvancedAnalytics:
    """Gestionnaire d'analyse de performance avancée"""
    
    def __init__(self):
        self.performance_cache = {}
        
    def calculate_performance_metrics(self, trades_data: List[Dict]) -> PerformanceMetrics:
        """Calcule les métriques de performance détaillées"""
        if not trades_data:
            return self._empty_metrics()
        
        total_trades = len(trades_data)
        winning_trades = len([t for t in trades_data if t.get('profit_loss', 0) > 0])
        losing_trades = len([t for t in trades_data if t.get('profit_loss', 0) < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profits = [t.get('profit_loss', 0) for t in trades_data]
        total_profit = sum(profits)
        
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        average_win = statistics.mean(wins) if wins else 0
        average_loss = abs(statistics.mean(losses)) if losses else 0
        
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else float('inf')
        
        # Calcul du drawdown maximum
        max_drawdown = self._calculate_max_drawdown(profits)
        
        # Calcul du ratio de Sharpe simplifié
        sharpe_ratio = self._calculate_sharpe_ratio(profits)
        
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        # Séries consécutives
        consecutive_wins, consecutive_losses = self._calculate_consecutive_streaks(profits)
        
        # Ratio Risk/Reward moyen
        risk_reward_ratio = (average_win / average_loss) if average_loss > 0 else 0
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            total_profit=round(total_profit, 2),
            average_win=round(average_win, 2),
            average_loss=round(average_loss, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            risk_reward_ratio=round(risk_reward_ratio, 2)
        )
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Retourne des métriques vides"""
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
            total_profit=0, average_win=0, average_loss=0, profit_factor=0,
            max_drawdown=0, sharpe_ratio=0, largest_win=0, largest_loss=0,
            consecutive_wins=0, consecutive_losses=0, risk_reward_ratio=0
        )
    
    def _calculate_max_drawdown(self, profits: List[float]) -> float:
        """Calcule le drawdown maximum"""
        if not profits:
            return 0
        
        cumulative = []
        running_total = 0
        for profit in profits:
            running_total += profit
            cumulative.append(running_total)
        
        max_dd = 0
        peak = cumulative[0] if cumulative else 0
        
        for value in cumulative:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, profits: List[float]) -> float:
        """Calcule un ratio de Sharpe simplifié"""
        if len(profits) < 2:
            return 0
        
        mean_return = statistics.mean(profits)
        std_dev = statistics.stdev(profits)
        
        return (mean_return / std_dev) if std_dev > 0 else 0
    
    def _calculate_consecutive_streaks(self, profits: List[float]) -> Tuple[int, int]:
        """Calcule les séries consécutives de gains/pertes"""
        if not profits:
            return 0, 0
        
        max_wins = current_wins = 0
        max_losses = current_losses = 0
        
        for profit in profits:
            if profit > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif profit < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = current_losses = 0
        
        return max_wins, max_losses
    
    def generate_equity_curve_data(self, trades_data: List[Dict]) -> List[Dict]:
        """Génère les données pour la courbe d'équité"""
        if not trades_data:
            return []
        
        # Trier par date
        sorted_trades = sorted(trades_data, key=lambda x: x.get('entry_date', datetime.now()))
        
        equity_data = []
        running_balance = 1000  # Balance initiale pour la démo
        
        for i, trade in enumerate(sorted_trades):
            profit = trade.get('profit_loss', 0)
            running_balance += profit
            
            equity_data.append({
                'trade_number': i + 1,
                'date': trade.get('entry_date', datetime.now()).isoformat(),
                'balance': round(running_balance, 2),
                'profit_loss': round(profit, 2),
                'pair_symbol': trade.get('pair_symbol', 'UNKNOWN')
            })
        
        return equity_data
    
    def analyze_performance_by_pair(self, trades_data: List[Dict]) -> List[Dict]:
        """Analyse les performances par paire de devises"""
        pair_stats = defaultdict(lambda: {
            'trades': 0, 'wins': 0, 'total_profit': 0, 'profits': []
        })
        
        for trade in trades_data:
            pair = trade.get('pair_symbol', 'UNKNOWN')
            profit = trade.get('profit_loss', 0)
            
            pair_stats[pair]['trades'] += 1
            pair_stats[pair]['total_profit'] += profit
            pair_stats[pair]['profits'].append(profit)
            
            if profit > 0:
                pair_stats[pair]['wins'] += 1
        
        result = []
        for pair, stats in pair_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_profit = stats['total_profit'] / stats['trades'] if stats['trades'] > 0 else 0
            
            result.append({
                'pair_symbol': pair,
                'total_trades': stats['trades'],
                'win_rate': round(win_rate, 2),
                'total_profit': round(stats['total_profit'], 2),
                'average_profit': round(avg_profit, 2),
                'best_trade': max(stats['profits']) if stats['profits'] else 0,
                'worst_trade': min(stats['profits']) if stats['profits'] else 0
            })
        
        return sorted(result, key=lambda x: x['total_profit'], reverse=True)
    
    def analyze_time_patterns(self, trades_data: List[Dict]) -> Dict:
        """Analyse les patterns temporels"""
        hourly_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'total_profit': 0})
        daily_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'total_profit': 0})
        
        for trade in trades_data:
            entry_date = trade.get('entry_date')
            if not entry_date:
                continue
                
            profit = trade.get('profit_loss', 0)
            hour = entry_date.hour
            day_of_week = entry_date.weekday()  # 0=Monday, 6=Sunday
            
            # Statistiques par heure
            hourly_stats[hour]['trades'] += 1
            hourly_stats[hour]['total_profit'] += profit
            if profit > 0:
                hourly_stats[hour]['wins'] += 1
            
            # Statistiques par jour de la semaine
            daily_stats[day_of_week]['trades'] += 1
            daily_stats[day_of_week]['total_profit'] += profit
            if profit > 0:
                daily_stats[day_of_week]['wins'] += 1
        
        # Formater les résultats
        hourly_analysis = []
        for hour in range(24):
            stats = hourly_stats[hour]
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_profit = stats['total_profit'] / stats['trades'] if stats['trades'] > 0 else 0
            
            hourly_analysis.append({
                'hour': hour,
                'trades': stats['trades'],
                'win_rate': round(win_rate, 2),
                'average_profit': round(avg_profit, 2),
                'total_profit': round(stats['total_profit'], 2),
                'recommended': win_rate > 60 and stats['trades'] >= 3
            })
        
        daily_analysis = []
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        for day in range(7):
            stats = daily_stats[day]
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_profit = stats['total_profit'] / stats['trades'] if stats['trades'] > 0 else 0
            
            daily_analysis.append({
                'day': day,
                'day_name': day_names[day],
                'trades': stats['trades'],
                'win_rate': round(win_rate, 2),
                'average_profit': round(avg_profit, 2),
                'total_profit': round(stats['total_profit'], 2),
                'recommended': win_rate > 60 and stats['trades'] >= 3
            })
        
        return {
            'hourly': hourly_analysis,
            'daily': daily_analysis
        }
    
    def detect_trading_patterns(self, trades_data: List[Dict]) -> List[TradingPattern]:
        """Détecte automatiquement les patterns de trading"""
        patterns = []
        
        if len(trades_data) < 10:  # Pas assez de données
            return patterns
        
        # Pattern 1: Trading aux heures d'ouverture des marchés
        london_open_trades = [t for t in trades_data 
                            if t.get('entry_date') and 7 <= t['entry_date'].hour <= 10]
        if london_open_trades:
            success_rate = len([t for t in london_open_trades if t.get('profit_loss', 0) > 0]) / len(london_open_trades) * 100
            avg_profit = statistics.mean([t.get('profit_loss', 0) for t in london_open_trades])
            
            if success_rate > 60:
                patterns.append(TradingPattern(
                    pattern_id="london_open",
                    name="Trading Ouverture Londres",
                    description="Trading pendant l'ouverture du marché londonien (7h-10h)",
                    frequency=len(london_open_trades),
                    success_rate=round(success_rate, 2),
                    average_profit=round(avg_profit, 2),
                    conditions={"time_range": "07:00-10:00", "market": "London"},
                    recommendations=[
                        "Concentrez-vous sur cette période",
                        "Surveillez la volatilité accrue",
                        "Utilisez des stops plus serrés"
                    ]
                ))
        
        # Pattern 2: Trading de paires spécifiques
        pair_performance = self.analyze_performance_by_pair(trades_data)
        best_pairs = [p for p in pair_performance if p['win_rate'] > 65 and p['total_trades'] >= 5]
        
        for pair_data in best_pairs[:3]:  # Top 3 paires
            patterns.append(TradingPattern(
                pattern_id=f"pair_{pair_data['pair_symbol'].lower()}",
                name=f"Spécialisation {pair_data['pair_symbol']}",
                description=f"Excellentes performances sur {pair_data['pair_symbol']}",
                frequency=pair_data['total_trades'],
                success_rate=pair_data['win_rate'],
                average_profit=pair_data['average_profit'],
                conditions={"pair_symbol": pair_data['pair_symbol']},
                recommendations=[
                    f"Augmentez l'exposition sur {pair_data['pair_symbol']}",
                    "Étudiez les spécificités de cette paire",
                    "Développez une stratégie dédiée"
                ]
            ))
        
        # Pattern 3: Risk/Reward élevé
        high_rr_trades = [t for t in trades_data 
                         if t.get('risk_reward_ratio', 0) >= 2.0 and t.get('profit_loss', 0) > 0]
        if len(high_rr_trades) >= 5:
            success_rate = len(high_rr_trades) / len([t for t in trades_data if t.get('risk_reward_ratio', 0) >= 2.0]) * 100
            avg_profit = statistics.mean([t.get('profit_loss', 0) for t in high_rr_trades])
            
            patterns.append(TradingPattern(
                pattern_id="high_risk_reward",
                name="Risk/Reward Élevé",
                description="Trades avec ratio risque/rendement ≥ 2:1",
                frequency=len(high_rr_trades),
                success_rate=round(success_rate, 2),
                average_profit=round(avg_profit, 2),
                conditions={"min_risk_reward": 2.0},
                recommendations=[
                    "Privilégiez les setups R/R ≥ 2:1",
                    "Soyez patient pour de meilleurs points d'entrée",
                    "Acceptez un taux de réussite plus faible"
                ]
            ))
        
        return patterns
    
    def generate_monthly_report(self, trades_data: List[Dict], month: int, year: int) -> Dict:
        """Génère un rapport mensuel détaillé"""
        # Filtrer les trades du mois
        monthly_trades = [
            t for t in trades_data 
            if t.get('entry_date') and 
            t['entry_date'].month == month and 
            t['entry_date'].year == year
        ]
        
        if not monthly_trades:
            return {"error": "Aucun trade trouvé pour cette période"}
        
        metrics = self.calculate_performance_metrics(monthly_trades)
        pair_analysis = self.analyze_performance_by_pair(monthly_trades)
        time_analysis = self.analyze_time_patterns(monthly_trades)
        patterns = self.detect_trading_patterns(monthly_trades)
        equity_curve = self.generate_equity_curve_data(monthly_trades)
        
        # Comparaison avec le mois précédent
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        
        prev_trades = [
            t for t in trades_data 
            if t.get('entry_date') and 
            t['entry_date'].month == prev_month and 
            t['entry_date'].year == prev_year
        ]
        
        prev_metrics = self.calculate_performance_metrics(prev_trades) if prev_trades else None
        
        return {
            "period": f"{month:02d}/{year}",
            "metrics": metrics,
            "pair_analysis": pair_analysis,
            "time_analysis": time_analysis,
            "patterns": patterns,
            "equity_curve": equity_curve,
            "comparison": {
                "previous_period": f"{prev_month:02d}/{prev_year}",
                "profit_change": round(metrics.total_profit - (prev_metrics.total_profit if prev_metrics else 0), 2),
                "win_rate_change": round(metrics.win_rate - (prev_metrics.win_rate if prev_metrics else 0), 2),
                "trades_change": metrics.total_trades - (prev_metrics.total_trades if prev_metrics else 0)
            }
        }
    
    def get_performance_insights(self, metrics: PerformanceMetrics) -> List[str]:
        """Génère des insights basés sur les métriques"""
        insights = []
        
        if metrics.win_rate > 70:
            insights.append("🎯 Excellent taux de réussite ! Votre sélection de trades est très efficace.")
        elif metrics.win_rate < 40:
            insights.append("⚠️ Taux de réussite faible. Revoyez vos critères d'entrée.")
        
        if metrics.profit_factor > 2.0:
            insights.append("💰 Excellent profit factor ! Vos gains dépassent largement vos pertes.")
        elif metrics.profit_factor < 1.0:
            insights.append("📉 Profit factor négatif. Vos pertes dépassent vos gains.")
        
        if metrics.risk_reward_ratio > 2.0:
            insights.append("🎯 Excellent ratio risk/reward ! Vous maximisez vos gains vs vos risques.")
        elif metrics.risk_reward_ratio < 1.0:
            insights.append("⚠️ Ratio risk/reward défavorable. Visez des objectifs plus ambitieux.")
        
        if metrics.max_drawdown > 20:
            insights.append("🔴 Drawdown élevé. Réduisez la taille de vos positions.")
        elif metrics.max_drawdown < 5:
            insights.append("🟢 Drawdown maîtrisé. Excellente gestion du risque.")
        
        if metrics.consecutive_losses > 5:
            insights.append("⏸️ Série de pertes importante. Prenez une pause pour analyser.")
        
        return insights

# Instance globale de l'analyseur de performance
advanced_analytics = AdvancedAnalytics()