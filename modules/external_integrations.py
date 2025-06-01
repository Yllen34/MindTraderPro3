"""
Intégrations avec Outils Externes - MT4/MT5, TradingView, Export, Partage Social
"""
import os
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import base64

class IntegrationType(Enum):
    MT4 = "metatrader4"
    MT5 = "metatrader5"
    TRADINGVIEW = "tradingview"
    CTRADER = "ctrader"
    NINJATRADER = "ninjatrader"

class ExportFormat(Enum):
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"

class SocialPlatform(Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"

@dataclass
class TradingPlatformConnection:
    """Connexion à une plateforme de trading"""
    connection_id: str
    user_session: str
    platform_type: IntegrationType
    account_number: str
    server_name: str
    login_credentials: Dict[str, str]
    is_active: bool
    last_sync: Optional[datetime]
    sync_frequency: int  # minutes
    auto_import_enabled: bool
    created_at: datetime

@dataclass
class ImportedTrade:
    """Trade importé depuis une plateforme externe"""
    external_id: str
    platform: IntegrationType
    symbol: str
    direction: str
    lot_size: float
    open_price: float
    close_price: Optional[float]
    open_time: datetime
    close_time: Optional[datetime]
    profit_loss: Optional[float]
    commission: float
    swap: float
    comment: str
    magic_number: Optional[int]

class ExternalIntegrationsManager:
    """Gestionnaire des intégrations externes"""
    
    def __init__(self):
        self.platform_connections = {}  # user_session -> List[TradingPlatformConnection]
        self.import_history = {}        # user_session -> List[ImportedTrade]
        self.export_cache = {}          # user_session -> Dict[format, data]
        
        # Configuration des APIs sociales
        self.setup_social_apis()
        
    def setup_social_apis(self):
        """Configuration des APIs de réseaux sociaux"""
        self.twitter_api_key = os.environ.get("TWITTER_API_KEY")
        self.twitter_api_secret = os.environ.get("TWITTER_API_SECRET")
        self.twitter_access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        self.twitter_access_secret = os.environ.get("TWITTER_ACCESS_SECRET")
        
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    def connect_trading_platform(self, user_session: str, platform_data: Dict) -> str:
        """Connecte une plateforme de trading"""
        
        connection_id = f"conn_{int(datetime.now().timestamp())}_{platform_data['platform_type']}"
        
        connection = TradingPlatformConnection(
            connection_id=connection_id,
            user_session=user_session,
            platform_type=IntegrationType(platform_data['platform_type']),
            account_number=platform_data['account_number'],
            server_name=platform_data.get('server_name', ''),
            login_credentials={
                'login': platform_data.get('login', ''),
                'password': platform_data.get('password', ''),
                'api_key': platform_data.get('api_key', '')
            },
            is_active=True,
            last_sync=None,
            sync_frequency=platform_data.get('sync_frequency', 60),
            auto_import_enabled=platform_data.get('auto_import', True),
            created_at=datetime.now()
        )
        
        if user_session not in self.platform_connections:
            self.platform_connections[user_session] = []
        
        self.platform_connections[user_session].append(connection)
        
        # Test de connexion
        test_result = self._test_platform_connection(connection)
        
        return {
            'connection_id': connection_id,
            'status': 'connected' if test_result['success'] else 'failed',
            'message': test_result['message']
        }
    
    def _test_platform_connection(self, connection: TradingPlatformConnection) -> Dict:
        """Test la connexion à une plateforme"""
        
        try:
            if connection.platform_type == IntegrationType.MT4:
                return self._test_mt4_connection(connection)
            elif connection.platform_type == IntegrationType.MT5:
                return self._test_mt5_connection(connection)
            elif connection.platform_type == IntegrationType.TRADINGVIEW:
                return self._test_tradingview_connection(connection)
            else:
                return {'success': False, 'message': 'Plateforme non supportée'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erreur de connexion: {str(e)}'}
    
    def _test_mt4_connection(self, connection: TradingPlatformConnection) -> Dict:
        """Test la connexion MT4"""
        
        # En production, utiliser MetaTrader5 ou une API similaire
        try:
            # Simulation de test MT4
            if connection.account_number and len(connection.account_number) >= 5:
                return {
                    'success': True,
                    'message': f'Connexion MT4 réussie pour le compte {connection.account_number}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Numéro de compte MT4 invalide'
                }
                
        except Exception as e:
            return {'success': False, 'message': f'Erreur MT4: {str(e)}'}
    
    def _test_mt5_connection(self, connection: TradingPlatformConnection) -> Dict:
        """Test la connexion MT5"""
        
        try:
            # En production, utiliser la vraie API MT5
            # import MetaTrader5 as mt5
            
            # Simulation pour la démonstration
            if connection.login_credentials.get('login') and connection.login_credentials.get('password'):
                return {
                    'success': True,
                    'message': f'Connexion MT5 établie pour {connection.account_number}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Identifiants MT5 manquants'
                }
                
        except Exception as e:
            return {'success': False, 'message': f'Erreur MT5: {str(e)}'}
    
    def _test_tradingview_connection(self, connection: TradingPlatformConnection) -> Dict:
        """Test la connexion TradingView"""
        
        try:
            api_key = connection.login_credentials.get('api_key')
            
            if not api_key:
                return {
                    'success': False,
                    'message': 'Clé API TradingView requise'
                }
            
            # En production, tester la vraie API TradingView
            return {
                'success': True,
                'message': 'Connexion TradingView simulée avec succès'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erreur TradingView: {str(e)}'}
    
    def import_trades_from_platform(self, user_session: str, connection_id: str, date_from: Optional[datetime] = None) -> Dict:
        """Importe les trades depuis une plateforme connectée"""
        
        connection = self._get_connection(user_session, connection_id)
        if not connection:
            return {'success': False, 'error': 'Connexion introuvable'}
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        
        try:
            if connection.platform_type == IntegrationType.MT4:
                trades = self._import_mt4_trades(connection, date_from)
            elif connection.platform_type == IntegrationType.MT5:
                trades = self._import_mt5_trades(connection, date_from)
            elif connection.platform_type == IntegrationType.TRADINGVIEW:
                trades = self._import_tradingview_trades(connection, date_from)
            else:
                return {'success': False, 'error': 'Plateforme non supportée pour l\'import'}
            
            # Sauvegarder l'historique
            if user_session not in self.import_history:
                self.import_history[user_session] = []
            
            self.import_history[user_session].extend(trades)
            connection.last_sync = datetime.now()
            
            return {
                'success': True,
                'imported_count': len(trades),
                'trades': [self._trade_to_dict(trade) for trade in trades]
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur d\'import: {str(e)}'}
    
    def _import_mt4_trades(self, connection: TradingPlatformConnection, date_from: datetime) -> List[ImportedTrade]:
        """Importe les trades depuis MT4"""
        
        # Simulation d'import MT4 - en production utiliser la vraie API
        demo_trades = [
            ImportedTrade(
                external_id="MT4_123456",
                platform=IntegrationType.MT4,
                symbol="XAUUSD",
                direction="BUY",
                lot_size=0.1,
                open_price=1985.50,
                close_price=2010.25,
                open_time=datetime.now() - timedelta(hours=2),
                close_time=datetime.now() - timedelta(hours=1),
                profit_loss=247.50,
                commission=-2.50,
                swap=0.0,
                comment="Auto import MT4",
                magic_number=12345
            ),
            ImportedTrade(
                external_id="MT4_123457",
                platform=IntegrationType.MT4,
                symbol="EURUSD",
                direction="SELL",
                lot_size=0.5,
                open_price=1.0875,
                close_price=1.0825,
                open_time=datetime.now() - timedelta(hours=6),
                close_time=datetime.now() - timedelta(hours=4),
                profit_loss=250.00,
                commission=-5.00,
                swap=-1.50,
                comment="Trend following",
                magic_number=12346
            )
        ]
        
        return demo_trades
    
    def _import_mt5_trades(self, connection: TradingPlatformConnection, date_from: datetime) -> List[ImportedTrade]:
        """Importe les trades depuis MT5"""
        
        # En production, utiliser MetaTrader5 library
        demo_trades = [
            ImportedTrade(
                external_id="MT5_789012",
                platform=IntegrationType.MT5,
                symbol="BTCUSD",
                direction="BUY",
                lot_size=0.05,
                open_price=44500.00,
                close_price=45200.00,
                open_time=datetime.now() - timedelta(hours=8),
                close_time=datetime.now() - timedelta(hours=3),
                profit_loss=350.00,
                commission=-10.00,
                swap=0.0,
                comment="Crypto breakout",
                magic_number=54321
            )
        ]
        
        return demo_trades
    
    def _import_tradingview_trades(self, connection: TradingPlatformConnection, date_from: datetime) -> List[ImportedTrade]:
        """Importe les trades depuis TradingView"""
        
        # Simulation - en production utiliser l'API TradingView
        demo_trades = [
            ImportedTrade(
                external_id="TV_ABC123",
                platform=IntegrationType.TRADINGVIEW,
                symbol="SPX500",
                direction="BUY",
                lot_size=1.0,
                open_price=4150.00,
                close_price=4180.00,
                open_time=datetime.now() - timedelta(hours=12),
                close_time=datetime.now() - timedelta(hours=6),
                profit_loss=300.00,
                commission=-15.00,
                swap=0.0,
                comment="Index breakout",
                magic_number=None
            )
        ]
        
        return demo_trades
    
    def export_trading_data(self, user_session: str, export_format: ExportFormat, data_type: str = "all") -> Dict:
        """Exporte les données de trading dans différents formats"""
        
        try:
            # Récupérer les données selon le type
            if data_type == "trades":
                data = self._get_user_trades_for_export(user_session)
            elif data_type == "alerts":
                data = self._get_user_alerts_for_export(user_session)
            elif data_type == "calculations":
                data = self._get_user_calculations_for_export(user_session)
            else:  # all
                data = self._get_all_user_data_for_export(user_session)
            
            if export_format == ExportFormat.CSV:
                return self._export_to_csv(data, data_type)
            elif export_format == ExportFormat.PDF:
                return self._export_to_pdf(data, data_type)
            elif export_format == ExportFormat.EXCEL:
                return self._export_to_excel(data, data_type)
            elif export_format == ExportFormat.JSON:
                return self._export_to_json(data, data_type)
            else:
                return {'success': False, 'error': 'Format d\'export non supporté'}
                
        except Exception as e:
            return {'success': False, 'error': f'Erreur d\'export: {str(e)}'}
    
    def _export_to_csv(self, data: Dict, data_type: str) -> Dict:
        """Export en format CSV"""
        
        output = io.StringIO()
        
        if data_type == "trades" and 'trades' in data:
            fieldnames = ['Date', 'Paire', 'Direction', 'Lot Size', 'Prix Entrée', 'Prix Sortie', 
                         'Profit/Perte', 'Commission', 'Notes']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in data['trades']:
                writer.writerow({
                    'Date': trade.get('open_time', ''),
                    'Paire': trade.get('symbol', ''),
                    'Direction': trade.get('direction', ''),
                    'Lot Size': trade.get('lot_size', ''),
                    'Prix Entrée': trade.get('open_price', ''),
                    'Prix Sortie': trade.get('close_price', ''),
                    'Profit/Perte': trade.get('profit_loss', ''),
                    'Commission': trade.get('commission', ''),
                    'Notes': trade.get('comment', '')
                })
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            'success': True,
            'format': 'csv',
            'content': csv_content,
            'filename': f'trading_data_{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    
    def _export_to_pdf(self, data: Dict, data_type: str) -> Dict:
        """Export en format PDF"""
        
        try:
            # En production, utiliser reportlab ou weasyprint
            html_content = self._generate_html_report(data, data_type)
            
            # Simulation de génération PDF
            pdf_content = f"PDF Report Generated for {data_type} - {datetime.now()}"
            
            return {
                'success': True,
                'format': 'pdf',
                'content': base64.b64encode(pdf_content.encode()).decode(),
                'filename': f'trading_report_{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération PDF: {str(e)}'}
    
    def _export_to_excel(self, data: Dict, data_type: str) -> Dict:
        """Export en format Excel"""
        
        try:
            # En production, utiliser openpyxl ou xlsxwriter
            excel_content = f"Excel Report Generated for {data_type} - {datetime.now()}"
            
            return {
                'success': True,
                'format': 'excel',
                'content': base64.b64encode(excel_content.encode()).decode(),
                'filename': f'trading_data_{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération Excel: {str(e)}'}
    
    def _export_to_json(self, data: Dict, data_type: str) -> Dict:
        """Export en format JSON"""
        
        try:
            json_content = json.dumps(data, indent=2, default=str)
            
            return {
                'success': True,
                'format': 'json',
                'content': json_content,
                'filename': f'trading_data_{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération JSON: {str(e)}'}
    
    def share_on_social_media(self, user_session: str, platform: SocialPlatform, content_data: Dict) -> Dict:
        """Partage du contenu sur les réseaux sociaux"""
        
        try:
            if platform == SocialPlatform.TWITTER:
                return self._share_on_twitter(content_data)
            elif platform == SocialPlatform.TELEGRAM:
                return self._share_on_telegram(content_data)
            elif platform == SocialPlatform.DISCORD:
                return self._share_on_discord(content_data)
            else:
                return {'success': False, 'error': 'Plateforme sociale non supportée'}
                
        except Exception as e:
            return {'success': False, 'error': f'Erreur partage: {str(e)}'}
    
    def _share_on_twitter(self, content_data: Dict) -> Dict:
        """Partage sur Twitter"""
        
        if not all([self.twitter_api_key, self.twitter_api_secret, 
                   self.twitter_access_token, self.twitter_access_secret]):
            return {'success': False, 'error': 'Configuration Twitter manquante'}
        
        try:
            # En production, utiliser tweepy ou requests
            tweet_text = self._generate_tweet_text(content_data)
            
            # Simulation d'envoi
            return {
                'success': True,
                'platform': 'twitter',
                'message': 'Tweet envoyé avec succès',
                'content': tweet_text
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur Twitter: {str(e)}'}
    
    def _share_on_telegram(self, content_data: Dict) -> Dict:
        """Partage sur Telegram"""
        
        if not self.telegram_bot_token:
            return {'success': False, 'error': 'Token Telegram Bot manquant'}
        
        try:
            message_text = self._generate_telegram_message(content_data)
            
            # En production, envoyer via l'API Telegram
            return {
                'success': True,
                'platform': 'telegram',
                'message': 'Message Telegram envoyé',
                'content': message_text
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur Telegram: {str(e)}'}
    
    def _share_on_discord(self, content_data: Dict) -> Dict:
        """Partage sur Discord"""
        
        if not self.discord_webhook_url:
            return {'success': False, 'error': 'Webhook Discord manquant'}
        
        try:
            embed_data = self._generate_discord_embed(content_data)
            
            # En production, envoyer via webhook Discord
            return {
                'success': True,
                'platform': 'discord',
                'message': 'Message Discord envoyé',
                'content': embed_data
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur Discord: {str(e)}'}
    
    def _generate_tweet_text(self, content_data: Dict) -> str:
        """Génère le texte pour Twitter"""
        
        if content_data.get('type') == 'trade_result':
            trade = content_data['trade']
            profit_emoji = "🟢" if trade['profit_loss'] > 0 else "🔴"
            
            return f"""
{profit_emoji} Trade fermé sur {trade['symbol']}

Direction: {trade['direction']}
Profit/Perte: {trade['profit_loss']}€
R/R: {trade.get('rr_ratio', 'N/A')}

#Trading #Forex #TradingResults
            """.strip()
        
        elif content_data.get('type') == 'performance':
            stats = content_data['stats']
            
            return f"""
📊 Performances de trading

✅ Trades gagnants: {stats['winning_trades']}%
💰 Profit total: {stats['total_profit']}€
📈 Meilleur mois: {stats['best_month']}

#TradingPerformance #Forex
            """.strip()
        
        return "🎯 Nouveau résultat de trading partagé depuis Trading Calculator Pro"
    
    def _generate_telegram_message(self, content_data: Dict) -> str:
        """Génère le message pour Telegram"""
        
        if content_data.get('type') == 'trade_result':
            trade = content_data['trade']
            
            return f"""
🎯 *RÉSULTAT DE TRADE*

📊 *Paire:* `{trade['symbol']}`
🔄 *Direction:* `{trade['direction']}`
💰 *Profit/Perte:* `{trade['profit_loss']}€`
⚡ *Ratio R/R:* `{trade.get('rr_ratio', 'N/A')}`

_{trade.get('comment', 'Trade exécuté avec Trading Calculator Pro')}_
            """.strip()
        
        return "📈 Nouveau partage depuis Trading Calculator Pro"
    
    def _generate_discord_embed(self, content_data: Dict) -> Dict:
        """Génère l'embed pour Discord"""
        
        if content_data.get('type') == 'trade_result':
            trade = content_data['trade']
            color = 0x28a745 if trade['profit_loss'] > 0 else 0xdc3545
            
            return {
                "title": f"🎯 Trade: {trade['symbol']}",
                "color": color,
                "fields": [
                    {
                        "name": "Direction",
                        "value": trade['direction'],
                        "inline": True
                    },
                    {
                        "name": "Profit/Perte",
                        "value": f"{trade['profit_loss']}€",
                        "inline": True
                    },
                    {
                        "name": "Ratio R/R",
                        "value": trade.get('rr_ratio', 'N/A'),
                        "inline": True
                    }
                ],
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Trading Calculator Pro"
                }
            }
        
        return {
            "title": "📊 Partage Trading",
            "description": "Nouveau contenu partagé depuis Trading Calculator Pro",
            "color": 0x007bff
        }
    
    def _get_connection(self, user_session: str, connection_id: str) -> Optional[TradingPlatformConnection]:
        """Récupère une connexion spécifique"""
        connections = self.platform_connections.get(user_session, [])
        return next((conn for conn in connections if conn.connection_id == connection_id), None)
    
    def _trade_to_dict(self, trade: ImportedTrade) -> Dict:
        """Convertit un trade en dictionnaire"""
        return {
            'external_id': trade.external_id,
            'platform': trade.platform.value,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'lot_size': trade.lot_size,
            'open_price': trade.open_price,
            'close_price': trade.close_price,
            'open_time': trade.open_time.isoformat(),
            'close_time': trade.close_time.isoformat() if trade.close_time else None,
            'profit_loss': trade.profit_loss,
            'commission': trade.commission,
            'swap': trade.swap,
            'comment': trade.comment
        }
    
    def _get_user_trades_for_export(self, user_session: str) -> Dict:
        """Récupère les trades pour export"""
        trades = self.import_history.get(user_session, [])
        return {'trades': [self._trade_to_dict(trade) for trade in trades]}
    
    def _get_user_alerts_for_export(self, user_session: str) -> Dict:
        """Récupère les alertes pour export"""
        # Simulation - en production, récupérer depuis le système d'alertes
        return {'alerts': []}
    
    def _get_user_calculations_for_export(self, user_session: str) -> Dict:
        """Récupère les calculs pour export"""
        # Simulation - en production, récupérer depuis le calculateur
        return {'calculations': []}
    
    def _get_all_user_data_for_export(self, user_session: str) -> Dict:
        """Récupère toutes les données utilisateur pour export"""
        return {
            'trades': self._get_user_trades_for_export(user_session)['trades'],
            'alerts': self._get_user_alerts_for_export(user_session)['alerts'],
            'calculations': self._get_user_calculations_for_export(user_session)['calculations'],
            'export_date': datetime.now().isoformat(),
            'user_session': user_session
        }
    
    def _generate_html_report(self, data: Dict, data_type: str) -> str:
        """Génère un rapport HTML"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Report - {data_type}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Trading Calculator Pro</h1>
                <h2>Rapport de {data_type}</h2>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            <div class="content">
                <p>Rapport détaillé des données de trading exportées.</p>
                <!-- Contenu du rapport ici -->
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_platform_connections(self, user_session: str) -> List[Dict]:
        """Récupère les connexions d'un utilisateur"""
        connections = self.platform_connections.get(user_session, [])
        return [
            {
                'connection_id': conn.connection_id,
                'platform_type': conn.platform_type.value,
                'account_number': conn.account_number,
                'server_name': conn.server_name,
                'is_active': conn.is_active,
                'last_sync': conn.last_sync.isoformat() if conn.last_sync else None,
                'auto_import_enabled': conn.auto_import_enabled,
                'created_at': conn.created_at.isoformat()
            }
            for conn in connections
        ]
    
    def get_import_history(self, user_session: str, days: int = 30) -> List[Dict]:
        """Récupère l'historique des imports"""
        cutoff = datetime.now() - timedelta(days=days)
        trades = self.import_history.get(user_session, [])
        
        recent_trades = [
            trade for trade in trades 
            if trade.open_time > cutoff
        ]
        
        return [self._trade_to_dict(trade) for trade in recent_trades]

# Instance globale du gestionnaire d'intégrations
external_integrations = ExternalIntegrationsManager()