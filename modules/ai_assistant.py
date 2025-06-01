"""
Assistant IA de Trading - Analyseur intelligent de performances
"""
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class TradingAIAssistant:
    """Assistant IA pour l'analyse des performances de trading"""
    
    def __init__(self):
        self.client = openai_client
    
    def get_basic_trading_tips(self):
        """Conseils de base pour tous les utilisateurs (Gratuit)"""
        tips = [
            {
                "title": "💡 Gestion du Risque",
                "message": "Ne risquez jamais plus de 1-2% de votre capital par trade. C'est la règle d'or du trading professionnel.",
                "category": "risk_management"
            },
            {
                "title": "📊 Plan de Trading",
                "message": "Définissez toujours votre stop loss et take profit AVANT d'entrer en position. L'émotion est l'ennemi du trader.",
                "category": "discipline"
            },
            {
                "title": "📈 Ratio Risk/Reward",
                "message": "Visez un ratio risk/reward d'au moins 1:2. Si vous risquez 50$, visez 100$ de gain minimum.",
                "category": "strategy"
            },
            {
                "title": "⏰ Timing de Marché",
                "message": "Les meilleures opportunités sont souvent pendant les sessions de trading actives : Londres (8h-17h) et New York (13h-22h).",
                "category": "timing"
            },
            {
                "title": "🎯 Patience",
                "message": "Attendez les bonnes configurations. Il vaut mieux manquer un trade que de perdre de l'argent sur un mauvais trade.",
                "category": "psychology"
            }
        ]
        return tips
    
    def analyze_trade_performance(self, trades_data, user_profile=None):
        """Analyse IA des performances (Premium)"""
        if not trades_data:
            return {
                "success": False,
                "message": "Aucune donnée de trading à analyser"
            }
        
        try:
            # Préparer les données pour l'IA
            analysis_prompt = self._prepare_performance_analysis_prompt(trades_data, user_profile)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert en trading forex avec 15 ans d'expérience. Analyse les données de trading et fournis des conseils détaillés et actionnables. Réponds en français et en JSON."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur d'analyse IA: {str(e)}"
            }
    
    def detect_recurring_errors(self, trades_data):
        """Détection des erreurs récurrentes (Premium)"""
        try:
            error_prompt = self._prepare_error_detection_prompt(trades_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un psychologue du trading spécialisé dans l'analyse comportementale. Identifie les patterns d'erreurs récurrentes et propose des solutions concrètes. Réponds en français et en JSON."
                    },
                    {
                        "role": "user",
                        "content": error_prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1200
            )
            
            errors = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur de détection: {str(e)}"
            }
    
    def generate_personalized_plan(self, user_profile, performance_data):
        """Génération d'un plan de trading personnalisé (Premium)"""
        try:
            plan_prompt = self._prepare_trading_plan_prompt(user_profile, performance_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un mentor de trading professionnel. Crée un plan de trading personnalisé et détaillé basé sur le profil et les performances du trader. Réponds en français et en JSON."
                    },
                    {
                        "role": "user",
                        "content": plan_prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            plan = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "plan": plan
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur de génération: {str(e)}"
            }
    
    def get_real_time_advice(self, current_trade_data):
        """Conseils en temps réel pendant le calcul (Gratuit avec limite)"""
        advice = []
        
        if current_trade_data.get('risk_percent', 0) > 2:
            advice.append({
                "type": "warning",
                "message": "⚠️ Risque élevé détecté ! Considérez réduire le pourcentage de risque sous 2%.",
                "category": "risk_management"
            })
        
        rr_ratio = current_trade_data.get('risk_reward_ratio', 0)
        if rr_ratio < 1.5:
            advice.append({
                "type": "suggestion",
                "message": f"📊 Ratio R/R de {rr_ratio:.2f} est faible. Visez au moins 1:2 pour plus de rentabilité.",
                "category": "strategy"
            })
        
        if current_trade_data.get('sl_pips', 0) > 100:
            advice.append({
                "type": "info",
                "message": "🎯 Stop loss large détecté. Assurez-vous que c'est intentionnel pour votre stratégie.",
                "category": "risk_management"
            })
        
        return advice
    
    def chat_with_ai(self, user_message, user_context=None):
        """Chat en temps réel avec l'assistant IA de trading"""
        try:
            system_prompt = """Tu es un assistant IA expert en trading et analyse financière. 
            Tu aides les traders à améliorer leurs performances en répondant à leurs questions sur:
            - L'analyse technique et fondamentale
            - La gestion du risque
            - Les stratégies de trading
            - La psychologie du trading
            - Les paires de devises, crypto, indices, métaux
            
            Réponds toujours de manière concise, pratique et professionnelle. 
            Utilise des émojis appropriés et donne des conseils actionables."""
            
            if user_context:
                system_prompt += f"\n\nContexte utilisateur: {user_context}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "type": "chat_response"
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "Désolé, je rencontre un problème technique. Pouvez-vous reformuler votre question ?",
                "error": str(e),
                "type": "error"
            }
    
    def _prepare_performance_analysis_prompt(self, trades_data, user_profile):
        """Prépare le prompt pour l'analyse de performance"""
        # Calculer les statistiques de base
        total_trades = len(trades_data)
        wins = sum(1 for trade in trades_data if trade.get('profit_loss', 0) > 0)
        losses = total_trades - wins
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(trade.get('profit_loss', 0) for trade in trades_data)
        avg_win = sum(trade.get('profit_loss', 0) for trade in trades_data if trade.get('profit_loss', 0) > 0) / wins if wins > 0 else 0
        avg_loss = sum(trade.get('profit_loss', 0) for trade in trades_data if trade.get('profit_loss', 0) < 0) / losses if losses > 0 else 0
        
        return f"""
        Analyse les données de trading suivantes et fournis une analyse détaillée en JSON:
        
        Statistiques:
        - Total trades: {total_trades}
        - Taux de réussite: {win_rate:.1f}%
        - P&L total: ${total_pnl:.2f}
        - Gain moyen: ${avg_win:.2f}
        - Perte moyenne: ${avg_loss:.2f}
        
        Données détaillées: {json.dumps(trades_data[-10:], default=str)}
        
        Profil utilisateur: {json.dumps(user_profile or {}, default=str)}
        
        Fournis une analyse JSON avec:
        {{
            "performance_generale": "évaluation globale",
            "points_forts": ["liste des forces"],
            "points_faibles": ["liste des faiblesses"],
            "recommandations": ["actions concrètes à prendre"],
            "score_global": "note sur 10",
            "prochaines_etapes": ["étapes prioritaires"]
        }}
        """
    
    def _prepare_error_detection_prompt(self, trades_data):
        """Prépare le prompt pour la détection d'erreurs"""
        # Analyser les patterns de pertes
        losing_trades = [trade for trade in trades_data if trade.get('profit_loss', 0) < 0]
        
        return f"""
        Analyse les trades perdants pour détecter les erreurs récurrentes:
        
        Trades perdants: {json.dumps(losing_trades[-15:], default=str)}
        
        Recherche les patterns d'erreurs et réponds en JSON:
        {{
            "erreurs_detectees": [
                {{
                    "type": "nom de l'erreur",
                    "frequence": "pourcentage",
                    "description": "explication détaillée",
                    "impact": "évaluation de l'impact",
                    "solution": "action corrective concrète"
                }}
            ],
            "priorite_correction": "erreur la plus critique à corriger",
            "plan_amelioration": ["étapes pour s'améliorer"]
        }}
        """
    
    def _prepare_trading_plan_prompt(self, user_profile, performance_data):
        """Prépare le prompt pour le plan de trading"""
        return f"""
        Crée un plan de trading personnalisé basé sur:
        
        Profil utilisateur: {json.dumps(user_profile, default=str)}
        Données de performance: {json.dumps(performance_data, default=str)}
        
        Génère un plan complet en JSON:
        {{
            "objectifs": {{
                "court_terme": "objectifs 1-3 mois",
                "moyen_terme": "objectifs 6-12 mois",
                "long_terme": "objectifs 1-3 ans"
            }},
            "strategie": {{
                "pairs_recommandees": ["liste des paires"],
                "timeframes": ["périodes recommandées"],
                "taille_position": "règles de sizing",
                "gestion_risque": "règles de risk management"
            }},
            "routine_quotidienne": ["étapes de routine"],
            "regles_trading": ["règles strictes à suivre"],
            "indicateurs_suivi": ["KPIs à surveiller"],
            "plan_formation": ["compétences à développer"]
        }}
        """


# Instance globale de l'assistant
ai_assistant = TradingAIAssistant()