"""
Système de Newsletter Intelligente - MindTraderPro
Récap personnalisé + news marché, intégration email
"""
import json
import os
from datetime import datetime, timedelta
from modules.email_service import email_service

class NewsletterSystem:
    def __init__(self):
        self.subscribers_file = 'data/newsletter_subscribers.json'
        self.templates_dir = 'templates/newsletter'
        self.market_news_cache = 'data/market_news_cache.json'
        
    def subscribe_user(self, user_session, email, frequency='weekly', preferences=None):
        """Abonne un utilisateur à la newsletter"""
        try:
            subscribers = self._load_subscribers()
            
            # Vérifier si déjà abonné
            existing = next((s for s in subscribers if s['user_session'] == user_session), None)
            
            if existing:
                # Mettre à jour les préférences
                existing['frequency'] = frequency
                existing['preferences'] = preferences or {}
                existing['updated_at'] = datetime.now().isoformat()
                message = 'Préférences de newsletter mises à jour'
            else:
                # Nouvel abonné
                subscriber = {
                    'user_session': user_session,
                    'email': email,
                    'frequency': frequency,  # daily, weekly, monthly
                    'preferences': preferences or {
                        'performance_recap': True,
                        'market_news': True,
                        'trading_tips': True,
                        'community_highlights': True
                    },
                    'subscribed_at': datetime.now().isoformat(),
                    'active': True,
                    'last_sent': None
                }
                subscribers.append(subscriber)
                message = 'Abonnement à la newsletter réussi'
            
            self._save_subscribers(subscribers)
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur abonnement: {str(e)}'}
    
    def unsubscribe_user(self, user_session):
        """Désabonne un utilisateur"""
        try:
            subscribers = self._load_subscribers()
            
            for subscriber in subscribers:
                if subscriber['user_session'] == user_session:
                    subscriber['active'] = False
                    subscriber['unsubscribed_at'] = datetime.now().isoformat()
                    break
            
            self._save_subscribers(subscribers)
            
            return {
                'success': True,
                'message': 'Désabonnement réussi'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur désabonnement: {str(e)}'}
    
    def generate_personalized_newsletter(self, user_session, period_days=7):
        """Génère une newsletter personnalisée pour un utilisateur"""
        try:
            # Récupération des données utilisateur
            user_data = self._get_user_trading_data(user_session, period_days)
            market_news = self._get_market_news()
            trading_tips = self._get_trading_tips()
            community_data = self._get_community_highlights()
            
            # Construction du contenu
            newsletter_content = {
                'header': {
                    'title': f'Votre récap trading - {datetime.now().strftime("%d/%m/%Y")}',
                    'period': f'Derniers {period_days} jours',
                    'user_name': user_data.get('name', 'Trader')
                },
                'performance_section': self._build_performance_section(user_data),
                'market_section': self._build_market_section(market_news),
                'tips_section': self._build_tips_section(trading_tips),
                'community_section': self._build_community_section(community_data),
                'footer': {
                    'app_stats': self._get_app_stats(),
                    'unsubscribe_link': f"/newsletter/unsubscribe/{user_session}"
                }
            }
            
            return {
                'success': True,
                'content': newsletter_content,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération newsletter: {str(e)}'}
    
    def send_newsletter(self, user_session, content=None):
        """Envoie la newsletter à un utilisateur"""
        try:
            subscribers = self._load_subscribers()
            subscriber = next((s for s in subscribers if s['user_session'] == user_session and s['active']), None)
            
            if not subscriber:
                return {'success': False, 'error': 'Utilisateur non abonné'}
            
            # Générer le contenu si non fourni
            if not content:
                result = self.generate_personalized_newsletter(user_session)
                if not result['success']:
                    return result
                content = result['content']
            
            # Génération HTML
            html_content = self._generate_html_newsletter(content)
            
            # Envoi email
            subject = content['header']['title']
            success = email_service.send_email(
                to_email=subscriber['email'],
                subject=subject,
                html_content=html_content,
                text_content=self._generate_text_newsletter(content)
            )
            
            if success:
                # Mise à jour de la date d'envoi
                subscriber['last_sent'] = datetime.now().isoformat()
                self._save_subscribers(subscribers)
                
                return {
                    'success': True,
                    'message': 'Newsletter envoyée avec succès'
                }
            else:
                return {'success': False, 'error': 'Erreur envoi email'}
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur envoi newsletter: {str(e)}'}
    
    def send_bulk_newsletter(self, frequency='weekly'):
        """Envoie la newsletter à tous les abonnés d'une fréquence"""
        try:
            subscribers = self._load_subscribers()
            results = {'sent': 0, 'failed': 0, 'errors': []}
            
            for subscriber in subscribers:
                if not subscriber['active'] or subscriber['frequency'] != frequency:
                    continue
                
                # Vérifier si il faut envoyer (selon la fréquence)
                if not self._should_send_newsletter(subscriber, frequency):
                    continue
                
                # Envoi
                result = self.send_newsletter(subscriber['user_session'])
                if result['success']:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'user': subscriber['user_session'],
                        'error': result.get('error', 'Erreur inconnue')
                    })
            
            return {
                'success': True,
                'results': results,
                'message': f"Newsletter envoyée à {results['sent']} utilisateurs"
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur envoi groupé: {str(e)}'}
    
    def _get_user_trading_data(self, user_session, period_days):
        """Récupère les données de trading de l'utilisateur"""
        try:
            # Récupération depuis les fichiers de données
            trades_file = f'data/trades_{user_session}.json'
            profile_file = f'data/profile_{user_session}.json'
            
            data = {
                'name': 'Trader',
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0,
                'best_pair': 'N/A',
                'worst_day': 'N/A',
                'best_day': 'N/A',
                'streak': 0
            }
            
            if os.path.exists(trades_file):
                with open(trades_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                
                # Filtrer par période
                cutoff_date = datetime.now() - timedelta(days=period_days)
                recent_trades = [
                    t for t in trades 
                    if datetime.fromisoformat(t.get('date', '2024-01-01')) > cutoff_date
                ]
                
                if recent_trades:
                    data['total_trades'] = len(recent_trades)
                    data['winning_trades'] = len([t for t in recent_trades if t.get('profit_loss', 0) > 0])
                    data['total_profit'] = sum(t.get('profit_loss', 0) for t in recent_trades)
                    
                    # Paire la plus tradée
                    pairs = {}
                    for trade in recent_trades:
                        pair = trade.get('pair_symbol', 'Unknown')
                        pairs[pair] = pairs.get(pair, 0) + 1
                    if pairs:
                        data['best_pair'] = max(pairs, key=pairs.get)
            
            if os.path.exists(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    data['name'] = profile.get('name', 'Trader')
            
            return data
            
        except Exception as e:
            return {'name': 'Trader', 'error': str(e)}
    
    def _get_market_news(self):
        """Récupère les actualités du marché"""
        # Simulation d'actualités - En production, intégrer une API réelle
        return [
            {
                'title': 'EUR/USD: Tendance haussière confirmée',
                'summary': 'La paire européenne continue sa progression suite aux dernières données économiques.',
                'impact': 'high',
                'time': '2h'
            },
            {
                'title': 'Or: Support technique important testé',
                'summary': 'XAUUSD teste le niveau clé de 2000$, surveillance recommandée.',
                'impact': 'medium', 
                'time': '4h'
            },
            {
                'title': 'NFP US vendredi: Attention volatilité',
                'summary': 'Publication des emplois non-agricoles US prévue vendredi 14h30.',
                'impact': 'high',
                'time': '1j'
            }
        ]
    
    def _get_trading_tips(self):
        """Récupère les conseils de trading"""
        return [
            {
                'tip': 'Toujours définir votre stop loss avant d\'entrer en position',
                'category': 'Risk Management'
            },
            {
                'tip': 'Tenez un journal de trading pour analyser vos performances',
                'category': 'Discipline'
            },
            {
                'tip': 'Ne risquez jamais plus de 2% de votre capital par trade',
                'category': 'Money Management'
            }
        ]
    
    def _get_community_highlights(self):
        """Récupère les faits saillants de la communauté"""
        return {
            'top_performer': {
                'username': 'TradePro_X',
                'performance': '+15.2% cette semaine'
            },
            'most_active': {
                'username': 'ConsistentTrader',
                'trades': 47
            },
            'best_tip': {
                'content': 'Patience et discipline sont les clés du succès en trading',
                'author': 'MasterTrader'
            }
        }
    
    def _build_performance_section(self, user_data):
        """Construit la section performance"""
        win_rate = (user_data['winning_trades'] / user_data['total_trades'] * 100) if user_data['total_trades'] > 0 else 0
        
        return {
            'title': 'Votre Performance',
            'stats': [
                {'label': 'Trades exécutés', 'value': user_data['total_trades']},
                {'label': 'Taux de réussite', 'value': f"{win_rate:.1f}%"},
                {'label': 'P&L Total', 'value': f"{user_data['total_profit']:.2f}$"},
                {'label': 'Paire favorite', 'value': user_data['best_pair']}
            ],
            'message': self._get_performance_message(win_rate, user_data['total_profit'])
        }
    
    def _build_market_section(self, news_data):
        """Construit la section actualités marché"""
        return {
            'title': 'Actualités Marché',
            'news': news_data
        }
    
    def _build_tips_section(self, tips_data):
        """Construit la section conseils"""
        return {
            'title': 'Conseils de Trading',
            'tips': tips_data
        }
    
    def _build_community_section(self, community_data):
        """Construit la section communauté"""
        return {
            'title': 'Highlights Communauté',
            'data': community_data
        }
    
    def _get_performance_message(self, win_rate, profit):
        """Génère un message personnalisé basé sur la performance"""
        if win_rate >= 70:
            return "Excellente performance ! Continuez sur cette lancée 🎯"
        elif win_rate >= 50:
            return "Bonne consistance ! Quelques ajustements peuvent optimiser vos résultats 📈"
        elif win_rate >= 30:
            return "Il y a du potentiel ! Analysez vos trades pour identifier les améliorations 💪"
        else:
            return "Restez patient et focalisé sur l'apprentissage. Le succès viendra ! 🚀"
    
    def _generate_html_newsletter(self, content):
        """Génère le HTML de la newsletter"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{content['header']['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .section {{ padding: 20px; border-bottom: 1px solid #eee; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .news-item {{ margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .footer {{ background: #333; color: white; padding: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📈 MindTraderPro</h1>
                    <h2>{content['header']['title']}</h2>
                    <p>Bonjour {content['header']['user_name']} !</p>
                </div>
                
                <div class="section">
                    <h3>🎯 {content['performance_section']['title']}</h3>
                    <div class="stats">
        """
        
        for stat in content['performance_section']['stats']:
            html += f"""
                        <div class="stat">
                            <div class="stat-value">{stat['value']}</div>
                            <div>{stat['label']}</div>
                        </div>
            """
        
        html += f"""
                    </div>
                    <p><strong>{content['performance_section']['message']}</strong></p>
                </div>
                
                <div class="section">
                    <h3>📰 {content['market_section']['title']}</h3>
        """
        
        for news in content['market_section']['news']:
            html += f"""
                    <div class="news-item">
                        <h4>{news['title']}</h4>
                        <p>{news['summary']}</p>
                        <small>Impact: {news['impact']} • {news['time']}</small>
                    </div>
            """
        
        html += f"""
                </div>
                
                <div class="footer">
                    <p>MindTraderPro - Votre partenaire trading intelligent</p>
                    <p><a href="{content['footer']['unsubscribe_link']}" style="color: #ccc;">Se désabonner</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_newsletter(self, content):
        """Génère la version texte de la newsletter"""
        text = f"""
{content['header']['title']}

Bonjour {content['header']['user_name']} !

VOTRE PERFORMANCE ({content['header']['period']})
========================================
"""
        for stat in content['performance_section']['stats']:
            text += f"{stat['label']}: {stat['value']}\n"
        
        text += f"\n{content['performance_section']['message']}\n\n"
        
        text += "ACTUALITÉS MARCHÉ\n================\n"
        for news in content['market_section']['news']:
            text += f"• {news['title']}\n  {news['summary']}\n\n"
        
        text += "CONSEILS DE TRADING\n==================\n"
        for tip in content['tips_section']['tips']:
            text += f"• {tip['tip']} ({tip['category']})\n"
        
        text += f"\n\nMindTraderPro - Votre partenaire trading intelligent\nSe désabonner: {content['footer']['unsubscribe_link']}"
        
        return text
    
    def _should_send_newsletter(self, subscriber, frequency):
        """Détermine si il faut envoyer la newsletter"""
        if not subscriber.get('last_sent'):
            return True
        
        last_sent = datetime.fromisoformat(subscriber['last_sent'])
        now = datetime.now()
        
        if frequency == 'daily':
            return (now - last_sent).days >= 1
        elif frequency == 'weekly':
            return (now - last_sent).days >= 7
        elif frequency == 'monthly':
            return (now - last_sent).days >= 30
        
        return False
    
    def _get_app_stats(self):
        """Récupère les statistiques de l'application"""
        return {
            'total_users': '2,500+',
            'trades_calculated': '15,000+',
            'success_rate': '78%'
        }
    
    def _load_subscribers(self):
        """Charge les abonnés"""
        try:
            if os.path.exists(self.subscribers_file):
                with open(self.subscribers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_subscribers(self, subscribers):
        """Sauvegarde les abonnés"""
        try:
            os.makedirs(os.path.dirname(self.subscribers_file), exist_ok=True)
            with open(self.subscribers_file, 'w', encoding='utf-8') as f:
                json.dump(subscribers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde abonnés: {e}")

# Instance globale
newsletter_system = NewsletterSystem()