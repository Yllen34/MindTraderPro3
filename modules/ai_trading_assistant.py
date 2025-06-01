"""
Assistant IA de Trading Intelligent - Validation de plan et suggestions personnalisées
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class PlanCompliance(Enum):
    PERFECT = "perfect"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    RISKY = "risky"
    DANGEROUS = "dangerous"

@dataclass
class TradingPlan:
    """Plan de trading utilisateur"""
    user_session: str
    max_risk_per_trade: float  # Pourcentage max par trade
    min_risk_reward_ratio: float  # Ratio R/R minimum
    preferred_timeframes: List[str]
    preferred_pairs: List[str]
    trading_sessions: List[str]  # london, ny, asian
    max_trades_per_day: int
    strategies_allowed: List[str]
    emotional_rules: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class TradeValidationResult:
    """Résultat de validation d'un trade"""
    compliance_level: PlanCompliance
    compliance_score: int  # 0-100
    plan_violations: List[str]
    plan_confirmations: List[str]
    ai_recommendation: str
    risk_analysis: Dict[str, Any]
    market_context_analysis: str
    suggestions: List[str]
    should_take_trade: bool
    confidence_level: int  # 0-100

class SmartTradingAssistant:
    """Assistant IA de trading intelligent"""
    
    def __init__(self):
        self.user_plans = {}
        self.validation_history = {}
        
    def create_trading_plan(self, user_session: str, plan_data: Dict) -> str:
        """Crée un plan de trading personnalisé"""
        
        plan = TradingPlan(
            user_session=user_session,
            max_risk_per_trade=plan_data.get('max_risk_per_trade', 2.0),
            min_risk_reward_ratio=plan_data.get('min_risk_reward_ratio', 2.0),
            preferred_timeframes=plan_data.get('preferred_timeframes', ['H1', 'H4']),
            preferred_pairs=plan_data.get('preferred_pairs', ['XAUUSD', 'EURUSD']),
            trading_sessions=plan_data.get('trading_sessions', ['london', 'ny']),
            max_trades_per_day=plan_data.get('max_trades_per_day', 3),
            strategies_allowed=plan_data.get('strategies_allowed', ['breakout', 'trend_following']),
            emotional_rules=plan_data.get('emotional_rules', {
                'min_confidence': 7,
                'max_stress': 4,
                'forbidden_emotions': ['euphoric', 'frustrated']
            }),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.user_plans[user_session] = plan
        return "Plan de trading créé avec succès"
    
    def validate_trade_against_plan(self, user_session: str, trade_data: Dict) -> TradeValidationResult:
        """Valide un trade contre le plan de trading utilisateur"""
        
        if user_session not in self.user_plans:
            # Créer un plan par défaut si aucun n'existe
            self.create_trading_plan(user_session, {})
        
        plan = self.user_plans[user_session]
        
        # Analyse de conformité
        violations = []
        confirmations = []
        score = 100
        
        # 1. Vérification du risque par trade
        risk_percent = trade_data.get('risk_percent', 1.0)
        if risk_percent > plan.max_risk_per_trade:
            violations.append(f"Risque {risk_percent}% > limite de {plan.max_risk_per_trade}%")
            score -= 25
        else:
            confirmations.append(f"Risque {risk_percent}% respecte la limite de {plan.max_risk_per_trade}%")
        
        # 2. Vérification du ratio Risk/Reward
        rr_ratio = trade_data.get('risk_reward_ratio', 1.0)
        if rr_ratio < plan.min_risk_reward_ratio:
            violations.append(f"R/R {rr_ratio:.1f} < minimum de {plan.min_risk_reward_ratio:.1f}")
            score -= 20
        else:
            confirmations.append(f"R/R {rr_ratio:.1f} respecte le minimum de {plan.min_risk_reward_ratio:.1f}")
        
        # 3. Vérification de la paire
        pair_symbol = trade_data.get('pair_symbol')
        if pair_symbol not in plan.preferred_pairs:
            violations.append(f"{pair_symbol} n'est pas dans vos paires préférées")
            score -= 10
        else:
            confirmations.append(f"{pair_symbol} fait partie de vos paires préférées")
        
        # 4. Vérification du timeframe
        timeframe = trade_data.get('timeframe')
        if timeframe not in plan.preferred_timeframes:
            violations.append(f"Timeframe {timeframe} non recommandé pour votre plan")
            score -= 10
        else:
            confirmations.append(f"Timeframe {timeframe} conforme à votre plan")
        
        # 5. Vérification de la stratégie
        strategy = trade_data.get('strategy')
        if strategy and strategy not in plan.strategies_allowed:
            violations.append(f"Stratégie {strategy} non autorisée dans votre plan")
            score -= 15
        elif strategy in plan.strategies_allowed:
            confirmations.append(f"Stratégie {strategy} autorisée dans votre plan")
        
        # 6. Vérification de l'état émotionnel
        emotional_state = trade_data.get('emotional_state')
        confidence = trade_data.get('confidence_level', 5)
        stress = trade_data.get('stress_level', 5)
        
        if confidence < plan.emotional_rules.get('min_confidence', 7):
            violations.append(f"Confiance {confidence}/10 < minimum de {plan.emotional_rules['min_confidence']}/10")
            score -= 15
        else:
            confirmations.append(f"Niveau de confiance {confidence}/10 satisfaisant")
        
        if stress > plan.emotional_rules.get('max_stress', 4):
            violations.append(f"Stress {stress}/10 > maximum de {plan.emotional_rules['max_stress']}/10")
            score -= 15
        else:
            confirmations.append(f"Niveau de stress {stress}/10 acceptable")
        
        if emotional_state in plan.emotional_rules.get('forbidden_emotions', []):
            violations.append(f"État émotionnel '{emotional_state}' déconseillé")
            score -= 20
        
        # 7. Vérification du nombre de trades quotidiens
        today_trades = self._count_today_trades(user_session)
        if today_trades >= plan.max_trades_per_day:
            violations.append(f"Limite quotidienne atteinte: {today_trades}/{plan.max_trades_per_day} trades")
            score -= 30
        else:
            confirmations.append(f"Trades du jour: {today_trades}/{plan.max_trades_per_day}")
        
        # 8. Analyse de la session de trading
        current_hour = datetime.now().hour
        session_analysis = self._analyze_trading_session(current_hour, plan.trading_sessions)
        if not session_analysis['is_preferred']:
            violations.append(f"Heure de trading non optimale: {session_analysis['message']}")
            score -= 10
        else:
            confirmations.append(f"Session de trading: {session_analysis['message']}")
        
        # Détermination du niveau de conformité
        if score >= 90:
            compliance = PlanCompliance.PERFECT
        elif score >= 75:
            compliance = PlanCompliance.GOOD
        elif score >= 60:
            compliance = PlanCompliance.ACCEPTABLE
        elif score >= 40:
            compliance = PlanCompliance.RISKY
        else:
            compliance = PlanCompliance.DANGEROUS
        
        # Génération des recommandations IA
        ai_recommendation = self._generate_ai_recommendation(compliance, violations, trade_data)
        
        # Analyse du risque
        risk_analysis = self._analyze_trade_risk(trade_data, plan)
        
        # Analyse du contexte de marché
        market_context = self._analyze_market_context(trade_data)
        
        # Suggestions d'amélioration
        suggestions = self._generate_suggestions(violations, trade_data, plan)
        
        # Décision finale
        should_take_trade = compliance in [PlanCompliance.PERFECT, PlanCompliance.GOOD] and len(violations) <= 2
        
        # Niveau de confiance de l'IA
        confidence_level = max(10, min(95, score - 5))
        
        result = TradeValidationResult(
            compliance_level=compliance,
            compliance_score=max(0, score),
            plan_violations=violations,
            plan_confirmations=confirmations,
            ai_recommendation=ai_recommendation,
            risk_analysis=risk_analysis,
            market_context_analysis=market_context,
            suggestions=suggestions,
            should_take_trade=should_take_trade,
            confidence_level=confidence_level
        )
        
        # Sauvegarder dans l'historique
        if user_session not in self.validation_history:
            self.validation_history[user_session] = []
        self.validation_history[user_session].append({
            'timestamp': datetime.now(),
            'trade_data': trade_data,
            'result': result
        })
        
        return result
    
    def _count_today_trades(self, user_session: str) -> int:
        """Compte les trades d'aujourd'hui pour un utilisateur"""
        # En pratique, ceci interrogerait la base de données
        # Pour l'instant, simulation
        if user_session not in self.validation_history:
            return 0
        
        today = datetime.now().date()
        today_validations = [
            v for v in self.validation_history[user_session]
            if v['timestamp'].date() == today and v['result'].should_take_trade
        ]
        
        return len(today_validations)
    
    def _analyze_trading_session(self, hour: int, preferred_sessions: List[str]) -> Dict:
        """Analyse la session de trading actuelle"""
        
        sessions = {
            'asian': (0, 9),
            'london': (7, 16),
            'ny': (13, 22)
        }
        
        current_sessions = []
        for session, (start, end) in sessions.items():
            if start <= hour <= end:
                current_sessions.append(session)
        
        is_preferred = any(session in preferred_sessions for session in current_sessions)
        
        if not current_sessions:
            message = "Hors des principales sessions de trading"
        else:
            session_names = {'asian': 'Asie', 'london': 'Londres', 'ny': 'New York'}
            current_names = [session_names[s] for s in current_sessions]
            message = f"Session(s) active(s): {', '.join(current_names)}"
        
        return {
            'is_preferred': is_preferred,
            'current_sessions': current_sessions,
            'message': message
        }
    
    def _generate_ai_recommendation(self, compliance: PlanCompliance, violations: List[str], trade_data: Dict) -> str:
        """Génère une recommandation IA personnalisée"""
        
        pair = trade_data.get('pair_symbol', 'UNKNOWN')
        direction = trade_data.get('direction', 'UNKNOWN')
        
        if compliance == PlanCompliance.PERFECT:
            return f"🎯 EXCELLENT TRADE ! Votre analyse {direction} sur {pair} respecte parfaitement votre plan de trading. L'IA recommande de procéder avec confiance."
        
        elif compliance == PlanCompliance.GOOD:
            return f"✅ BON TRADE. Votre {direction} sur {pair} est globalement conforme à votre plan. Quelques ajustements mineurs pourraient l'améliorer."
        
        elif compliance == PlanCompliance.ACCEPTABLE:
            return f"⚠️ TRADE ACCEPTABLE. Votre {direction} sur {pair} respecte les éléments essentiels mais présente des déviations. Considérez les violations avant de procéder."
        
        elif compliance == PlanCompliance.RISKY:
            return f"🔸 TRADE RISQUÉ. Votre {direction} sur {pair} viole plusieurs éléments de votre plan. L'IA recommande de revoir votre analyse ou d'attendre une meilleure opportunité."
        
        else:  # DANGEROUS
            return f"🛑 TRADE DANGEREUX ! Votre {direction} sur {pair} va à l'encontre de votre plan de trading. L'IA recommande fortement d'éviter ce trade."
    
    def _analyze_trade_risk(self, trade_data: Dict, plan: TradingPlan) -> Dict:
        """Analyse détaillée du risque du trade"""
        
        risk_percent = trade_data.get('risk_percent', 1.0)
        lot_size = trade_data.get('lot_size', 1.0)
        rr_ratio = trade_data.get('risk_reward_ratio', 1.0)
        
        # Calcul du risque en USD (simulation)
        capital_estimation = 10000  # En pratique, récupérer le vrai capital
        risk_usd = capital_estimation * (risk_percent / 100)
        potential_profit = risk_usd * rr_ratio
        
        risk_level = "faible" if risk_percent <= 1 else "modéré" if risk_percent <= 2 else "élevé"
        
        return {
            'risk_percentage': risk_percent,
            'risk_usd': round(risk_usd, 2),
            'potential_profit': round(potential_profit, 2),
            'risk_level': risk_level,
            'position_size': lot_size,
            'max_loss_scenario': f"Perte maximale: {risk_usd:.2f}€ ({risk_percent}% du capital)",
            'win_scenario': f"Gain potentiel: {potential_profit:.2f}€ (ratio {rr_ratio:.1f}:1)"
        }
    
    def _analyze_market_context(self, trade_data: Dict) -> str:
        """Analyse le contexte de marché pour le trade"""
        
        pair = trade_data.get('pair_symbol')
        direction = trade_data.get('direction')
        timeframe = trade_data.get('timeframe')
        market_structure = trade_data.get('market_structure')
        confluence_factors = trade_data.get('confluence_factors', [])
        
        context_parts = []
        
        # Analyse de la paire
        if pair == 'XAUUSD':
            context_parts.append("L'or est sensible aux données économiques US et aux tensions géopolitiques")
        elif 'USD' in pair:
            context_parts.append("Paire liée au Dollar US - surveillez les annonces de la FED")
        
        # Analyse de la direction vs structure
        if market_structure and direction:
            if (market_structure == 'uptrend' and direction == 'BUY') or \
               (market_structure == 'downtrend' and direction == 'SELL'):
                context_parts.append("✅ Direction alignée avec la structure de marché")
            else:
                context_parts.append("⚠️ Direction contre la structure de marché dominante")
        
        # Analyse de la confluence
        if len(confluence_factors) >= 3:
            context_parts.append(f"🎯 Excellente confluence avec {len(confluence_factors)} facteurs")
        elif len(confluence_factors) >= 2:
            context_parts.append(f"✅ Bonne confluence avec {len(confluence_factors)} facteurs")
        else:
            context_parts.append("⚠️ Confluence limitée - setup moins robuste")
        
        # Analyse du timeframe
        if timeframe in ['H4', 'D1']:
            context_parts.append("📊 Timeframe adapté pour une analyse de qualité")
        elif timeframe in ['M5', 'M15']:
            context_parts.append("⚡ Timeframe court - risque de bruit accru")
        
        return " | ".join(context_parts) if context_parts else "Contexte de marché standard"
    
    def _generate_suggestions(self, violations: List[str], trade_data: Dict, plan: TradingPlan) -> List[str]:
        """Génère des suggestions d'amélioration personnalisées"""
        
        suggestions = []
        
        # Suggestions basées sur les violations
        if any('Risque' in v for v in violations):
            suggestions.append(f"💡 Réduisez votre taille de position pour respecter la limite de {plan.max_risk_per_trade}%")
        
        if any('R/R' in v for v in violations):
            suggestions.append(f"🎯 Ajustez votre Take Profit pour atteindre un ratio de {plan.min_risk_reward_ratio:.1f}:1 minimum")
        
        if any('paires préférées' in v for v in violations):
            suggestions.append(f"📊 Concentrez-vous sur vos paires maîtrisées: {', '.join(plan.preferred_pairs[:3])}")
        
        if any('Confiance' in v for v in violations):
            suggestions.append("🧘 Attendez d'être plus confiant avant de trader - la confiance améliore les résultats")
        
        if any('Stress' in v for v in violations):
            suggestions.append("😌 Prenez une pause pour réduire votre stress - le stress nuit à la prise de décision")
        
        if any('Limite quotidienne' in v for v in violations):
            suggestions.append("⏸️ Vous avez atteint votre limite quotidienne - respectez votre discipline")
        
        if any('Session' in v for v in violations):
            sessions_names = {'london': 'Londres (8h-17h)', 'ny': 'New York (14h-23h)', 'asian': 'Asie (0h-9h)'}
            preferred_sessions = [sessions_names.get(s, s) for s in plan.trading_sessions]
            suggestions.append(f"⏰ Tradez pendant vos sessions optimales: {', '.join(preferred_sessions)}")
        
        # Suggestions générales d'amélioration
        confluence_count = len(trade_data.get('confluence_factors', []))
        if confluence_count < 3:
            suggestions.append("🔍 Cherchez plus de facteurs de confluence pour renforcer votre setup")
        
        if trade_data.get('setup_quality', 7) < 8:
            suggestions.append("⭐ Attendez des setups de qualité supérieure (8/10 minimum)")
        
        # Suggestion basée sur l'historique (simulation)
        suggestions.append("📈 Analysez vos trades passés pour identifier vos patterns gagnants")
        
        return suggestions[:5]  # Limiter à 5 suggestions maximum
    
    def get_user_plan(self, user_session: str) -> Optional[TradingPlan]:
        """Récupère le plan de trading d'un utilisateur"""
        return self.user_plans.get(user_session)
    
    def update_user_plan(self, user_session: str, updates: Dict) -> bool:
        """Met à jour le plan de trading d'un utilisateur"""
        if user_session not in self.user_plans:
            return False
        
        plan = self.user_plans[user_session]
        
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        plan.updated_at = datetime.now()
        return True
    
    def get_personalized_insights(self, user_session: str) -> Dict:
        """Génère des insights personnalisés basés sur l'historique"""
        
        if user_session not in self.validation_history:
            return {"message": "Pas assez de données pour générer des insights"}
        
        history = self.validation_history[user_session]
        
        if len(history) < 5:
            return {"message": "Continuez à utiliser l'assistant pour recevoir des insights personnalisés"}
        
        insights = {}
        
        # Analyse des violations fréquentes
        all_violations = []
        for entry in history[-10:]:  # Dernières 10 validations
            all_violations.extend(entry['result'].plan_violations)
        
        if all_violations:
            from collections import Counter
            common_violations = Counter(all_violations).most_common(3)
            insights['frequent_violations'] = [
                f"Problème récurrent: {violation} (x{count})"
                for violation, count in common_violations
            ]
        
        # Analyse des patterns de trading
        recent_trades = history[-5:]
        emotions = [entry['trade_data'].get('emotional_state') for entry in recent_trades]
        
        from collections import Counter
        emotion_counter = Counter(emotions)
        most_common_emotion = emotion_counter.most_common(1)[0][0] if emotions else None
        
        if most_common_emotion:
            insights['emotional_pattern'] = f"Vous tradez souvent en étant '{most_common_emotion}'"
        
        # Analyse des heures de trading
        hours = [entry['timestamp'].hour for entry in recent_trades]
        if hours:
            avg_hour = sum(hours) / len(hours)
            insights['trading_time_pattern'] = f"Vous tradez principalement vers {int(avg_hour)}h"
        
        # Score de discipline moyen
        recent_scores = [entry['result'].compliance_score for entry in recent_trades]
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            insights['discipline_score'] = f"Score de discipline moyen: {avg_score:.0f}/100"
        
        return insights
    
    def ask_trade_question(self, user_session: str, trade_data: Dict) -> Dict:
        """Fonction principale: 'Est-ce que ce trade respecte mon plan?'"""
        
        validation_result = self.validate_trade_against_plan(user_session, trade_data)
        
        # Réponse structurée à la question
        response = {
            'question': "Est-ce que ce trade respecte mon plan ?",
            'answer': validation_result.ai_recommendation,
            'compliance_score': validation_result.compliance_score,
            'should_take_trade': validation_result.should_take_trade,
            'plan_summary': self._get_plan_summary(user_session),
            'violations': validation_result.plan_violations,
            'confirmations': validation_result.plan_confirmations,
            'risk_analysis': validation_result.risk_analysis,
            'market_context': validation_result.market_context_analysis,
            'suggestions': validation_result.suggestions,
            'confidence': validation_result.confidence_level
        }
        
        return response
    
    def _get_plan_summary(self, user_session: str) -> Dict:
        """Résumé du plan de trading utilisateur"""
        
        if user_session not in self.user_plans:
            return {"error": "Aucun plan de trading défini"}
        
        plan = self.user_plans[user_session]
        
        return {
            'max_risk_per_trade': f"{plan.max_risk_per_trade}%",
            'min_risk_reward': f"{plan.min_risk_reward_ratio}:1",
            'preferred_pairs': ', '.join(plan.preferred_pairs[:3]),
            'trading_sessions': ', '.join(plan.trading_sessions),
            'max_daily_trades': plan.max_trades_per_day,
            'emotional_rules': {
                'min_confidence': f"{plan.emotional_rules.get('min_confidence', 7)}/10",
                'max_stress': f"{plan.emotional_rules.get('max_stress', 4)}/10"
            }
        }

# Instance globale de l'assistant IA
smart_ai_assistant = SmartTradingAssistant()