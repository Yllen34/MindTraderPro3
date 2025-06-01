"""
Assistant IA GPT - Coach de Trading Intelligent
Feedback, coaching, détection revenge trading, conseils personnalisés
"""
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI

class AITradingCoach:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.coaching_prompts = {
            'journal_feedback': """Tu es un coach de trading professionnel. Analyse ce journal de trading et donne des conseils constructifs en français.
            
Journal: {journal_data}

Donne un feedback sur:
1. Les points forts du trader
2. Les axes d'amélioration
3. Les patterns identifiés
4. Conseils spécifiques pour la semaine

Sois encourageant mais honest.""",

            'revenge_trading_detection': """Analyse ces trades récents pour détecter des signes de revenge trading:

Trades: {trades_data}

Indicateurs à analyser:
- Augmentation soudaine de la taille des positions
- Trades rapprochés après une perte
- Écart par rapport à la stratégie habituelle
- Émotions dans les notes

Réponds par OUI/NON et explique pourquoi.""",

            'daily_coaching': """Génère un conseil quotidien personnalisé pour ce trader:

Profil: {user_profile}
Performance récente: {recent_performance}
Objectifs: {user_goals}

Donne un conseil motivant et actionnable pour aujourd'hui (max 100 mots).""",

            'setup_analysis': """Analyse ce setup de trading et donne ton avis:

Setup: {setup_data}
Contexte marché: {market_context}

Évalue:
1. Qualité du setup (1-10)
2. Niveau de risque
3. Points d'amélioration
4. Recommandation (GO/NO GO)

Sois précis et éducatif."""
        }
    
    def analyze_journal(self, user_session, period_days=30):
        """Analyse le journal de trading et donne un feedback IA"""
        try:
            # Récupération des trades récents
            trades_data = self._get_user_trades(user_session, period_days)
            
            if not trades_data:
                return {
                    'success': False,
                    'message': 'Pas assez de données pour l\'analyse'
                }
            
            # Préparation des données pour l'IA
            journal_summary = self._prepare_journal_summary(trades_data)
            
            # Appel à GPT
            prompt = self.coaching_prompts['journal_feedback'].format(
                journal_data=journal_summary
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            feedback = response.choices[0].message.content
            
            # Sauvegarde du feedback
            self._save_ai_feedback(user_session, 'journal_analysis', feedback)
            
            return {
                'success': True,
                'feedback': feedback,
                'analysis_date': datetime.now().isoformat(),
                'trades_analyzed': len(trades_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur analyse IA: {str(e)}'
            }
    
    def detect_revenge_trading(self, user_session, last_hours=24):
        """Détecte les signes de revenge trading"""
        try:
            # Récupération des trades récents
            recent_trades = self._get_recent_trades(user_session, last_hours)
            
            if len(recent_trades) < 2:
                return {
                    'revenge_detected': False,
                    'confidence': 0,
                    'message': 'Pas assez de trades pour l\'analyse'
                }
            
            # Analyse des patterns
            revenge_indicators = self._analyze_revenge_patterns(recent_trades)
            
            # Appel IA pour confirmation
            trades_summary = json.dumps(recent_trades, indent=2)
            prompt = self.coaching_prompts['revenge_trading_detection'].format(
                trades_data=trades_summary
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            ai_analysis = response.choices[0].message.content
            revenge_detected = "OUI" in (ai_analysis.upper() if ai_analysis else "")
            
            # Recommandation basée sur la détection
            recommendation = "Prenez une pause de 15 minutes avant de continuer" if revenge_detected else "Continuez votre trading avec prudence"
            
            result = {
                'revenge_detected': revenge_detected,
                'confidence': revenge_indicators['score'],
                'ai_analysis': ai_analysis,
                'indicators': revenge_indicators['details'],
                'recommendation': recommendation
            }
            
            # Log de l'alerte si détectée
            if revenge_detected:
                self._save_ai_feedback(user_session, 'revenge_trading_alert', result)
            
            return result
            
        except Exception as e:
            return {
                'revenge_detected': False,
                'error': f'Erreur détection: {str(e)}'
            }
    
    def generate_daily_coaching(self, user_session):
        """Génère un conseil quotidien personnalisé"""
        try:
            # Récupération du profil utilisateur
            user_profile = self._get_user_profile(user_session)
            recent_performance = self._get_recent_performance_data(user_session)
            
            prompt = self.coaching_prompts['daily_coaching'].format(
                user_profile=user_profile,
                recent_performance=recent_performance,
                user_goals=user_profile.get('goals', 'Améliorer la consistance')
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.8
            )
            
            daily_tip = response.choices[0].message.content
            
            # Sauvegarde du conseil
            self._save_ai_feedback(user_session, 'daily_tip', daily_tip)
            
            return {
                'success': True,
                'tip': daily_tip,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'type': 'daily_coaching'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur coaching: {str(e)}'
            }
    
    def analyze_setup(self, setup_data, market_context=None):
        """Analyse un setup de trading avec l'IA"""
        try:
            prompt = self.coaching_prompts['setup_analysis'].format(
                setup_data=setup_data,
                market_context=market_context or "Contexte normal"
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            
            analysis = response.choices[0].message.content
            
            # Extraction du score et de la recommandation
            score = self._extract_score(analysis)
            recommendation = self._extract_recommendation(analysis)
            
            return {
                'success': True,
                'analysis': analysis,
                'score': score,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur analyse setup: {str(e)}'
            }
    
    def _get_user_trades(self, user_session, days):
        """Récupère les trades de l'utilisateur"""
        try:
            # Simulation de récupération depuis la base de données
            trades_file = f'data/trades_{user_session}.json'
            if os.path.exists(trades_file):
                with open(trades_file, 'r', encoding='utf-8') as f:
                    all_trades = json.load(f)
                
                # Filtrer par date
                cutoff_date = datetime.now() - timedelta(days=days)
                recent_trades = [
                    trade for trade in all_trades 
                    if datetime.fromisoformat(trade.get('date', '2024-01-01')) > cutoff_date
                ]
                return recent_trades
            return []
        except:
            return []
    
    def _get_recent_trades(self, user_session, hours):
        """Récupère les trades des dernières heures"""
        try:
            trades_file = f'data/trades_{user_session}.json'
            if os.path.exists(trades_file):
                with open(trades_file, 'r', encoding='utf-8') as f:
                    all_trades = json.load(f)
                
                cutoff_time = datetime.now() - timedelta(hours=hours)
                recent_trades = [
                    trade for trade in all_trades 
                    if datetime.fromisoformat(trade.get('timestamp', '2024-01-01T00:00:00')) > cutoff_time
                ]
                return recent_trades
            return []
        except:
            return []
    
    def _prepare_journal_summary(self, trades):
        """Prépare un résumé du journal pour l'IA"""
        summary = {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t.get('profit_loss', 0) > 0]),
            'losing_trades': len([t for t in trades if t.get('profit_loss', 0) < 0]),
            'total_pnl': sum(t.get('profit_loss', 0) for t in trades),
            'avg_win': 0,
            'avg_loss': 0,
            'biggest_win': max([t.get('profit_loss', 0) for t in trades] or [0]),
            'biggest_loss': min([t.get('profit_loss', 0) for t in trades] or [0]),
            'most_traded_pairs': {},
            'notes_patterns': []
        }
        
        # Calculs moyennes
        wins = [t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) > 0]
        losses = [t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) < 0]
        
        summary['avg_win'] = sum(wins) / len(wins) if wins else 0
        summary['avg_loss'] = sum(losses) / len(losses) if losses else 0
        summary['win_rate'] = (summary['winning_trades'] / summary['total_trades'] * 100) if summary['total_trades'] > 0 else 0
        
        # Paires les plus tradées
        for trade in trades:
            pair = trade.get('pair_symbol', 'UNKNOWN')
            summary['most_traded_pairs'][pair] = summary['most_traded_pairs'].get(pair, 0) + 1
        
        # Extraction des notes pour patterns émotionnels
        for trade in trades:
            if trade.get('notes'):
                summary['notes_patterns'].append(trade['notes'][:100])
        
        return json.dumps(summary, indent=2)
    
    def _analyze_revenge_patterns(self, trades):
        """Analyse les patterns de revenge trading"""
        score = 0
        details = []
        
        if len(trades) < 2:
            return {'score': 0, 'details': []}
        
        # 1. Vérifier l'augmentation de la taille des positions après perte
        for i in range(1, len(trades)):
            prev_trade = trades[i-1]
            curr_trade = trades[i]
            
            if (prev_trade.get('profit_loss', 0) < 0 and 
                curr_trade.get('lot_size', 0) > prev_trade.get('lot_size', 0) * 1.5):
                score += 30
                details.append("Augmentation significative de la position après perte")
        
        # 2. Trades très rapprochés après perte
        for i in range(1, len(trades)):
            prev_trade = trades[i-1]
            curr_trade = trades[i]
            
            try:
                prev_time = datetime.fromisoformat(prev_trade.get('timestamp', ''))
                curr_time = datetime.fromisoformat(curr_trade.get('timestamp', ''))
                time_diff = (curr_time - prev_time).total_seconds() / 60  # minutes
                
                if prev_trade.get('profit_loss', 0) < 0 and time_diff < 30:
                    score += 25
                    details.append(f"Trade lancé {int(time_diff)} minutes après une perte")
            except:
                pass
        
        # 3. Écart par rapport au risque habituel
        risk_percentages = [t.get('risk_percent', 1) for t in trades]
        avg_risk = sum(risk_percentages) / len(risk_percentages)
        
        for trade in trades[-3:]:  # 3 derniers trades
            if trade.get('risk_percent', 1) > avg_risk * 2:
                score += 20
                details.append("Risque excessif par rapport à l'habitude")
        
        # 4. Mots-clés émotionnels dans les notes
        emotional_keywords = ['revenge', 'récupérer', 'énervé', 'frustré', 'rattraper', 'vite']
        for trade in trades:
            notes = trade.get('notes', '').lower()
            for keyword in emotional_keywords:
                if keyword in notes:
                    score += 15
                    details.append(f"Langage émotionnel détecté: '{keyword}'")
                    break
        
        return {
            'score': min(score, 100),  # Cap à 100
            'details': details
        }
    
    def _save_ai_feedback(self, user_session, feedback_type, content):
        """Sauvegarde le feedback IA"""
        try:
            feedback_data = {
                'user_session': user_session,
                'type': feedback_type,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            
            feedback_file = f'data/ai_feedback_{user_session}.json'
            
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            else:
                feedbacks = []
            
            feedbacks.append(feedback_data)
            feedbacks = feedbacks[-50:]  # Garder seulement les 50 derniers
            
            os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erreur sauvegarde feedback: {e}")
    
    def _get_user_profile(self, user_session):
        """Récupère le profil utilisateur"""
        try:
            profile_file = f'data/profile_{user_session}.json'
            if os.path.exists(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                'experience_level': 'Intermédiaire',
                'trading_style': 'Swing Trading',
                'risk_tolerance': 'Modéré',
                'goals': 'Consistance et croissance'
            }
        except:
            return {}
    
    def _get_recent_performance_data(self, user_session):
        """Récupère les données de performance récentes"""
        try:
            trades = self._get_user_trades(user_session, 7)  # 7 derniers jours
            if not trades:
                return "Aucune donnée de trading récente"
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('profit_loss', 0) > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(t.get('profit_loss', 0) for t in trades)
            
            return f"Trades récents: {total_trades}, Taux de réussite: {win_rate:.1f}%, P&L: {total_pnl:.2f}$"
        except:
            return "Données de performance non disponibles"
    
    def _extract_score(self, analysis):
        """Extrait le score de l'analyse"""
        import re
        score_match = re.search(r'(\d+)/10', analysis)
        return int(score_match.group(1)) if score_match else 5
    
    def _extract_recommendation(self, analysis):
        """Extrait la recommandation"""
        if 'GO' in analysis.upper() and 'NO GO' not in analysis.upper():
            return 'GO'
        elif 'NO GO' in analysis.upper():
            return 'NO GO'
        else:
            return 'NEUTRE'

# Instance globale
ai_coach = AITradingCoach()