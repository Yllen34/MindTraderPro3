"""
Module d'intégrations externes pour la plateforme de trading
"""
import os
import json
import base64
from datetime import datetime
from io import BytesIO
import requests

class TradingIntegrations:
    """Gestionnaire des intégrations externes"""
    
    def __init__(self):
        self.telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    
    def generate_trade_share_text(self, trade_data):
        """Génère un texte de partage formaté pour un trade (Gratuit)"""
        direction_emoji = "📈" if trade_data.get('direction', '').upper() == 'BUY' else "📉"
        profit_emoji = "💰" if trade_data.get('profit_loss', 0) > 0 else "📉" if trade_data.get('profit_loss', 0) < 0 else "⏳"
        
        share_text = f"""
{direction_emoji} TRADE {trade_data.get('direction', '').upper()}
━━━━━━━━━━━━━━━━━━━━━━━

📊 Paire: {trade_data.get('pair_symbol', 'N/A')}
🎯 Entry: {trade_data.get('entry_price', 0):.5f}
🛑 Stop Loss: {trade_data.get('stop_loss', 0):.5f}
🎪 Take Profit: {trade_data.get('take_profit', 0):.5f}
💼 Lot Size: {trade_data.get('lot_size', 0):.2f}

📈 Risk/Reward: 1:{trade_data.get('risk_reward_ratio', 0):.2f}
💵 Risque: ${trade_data.get('risk_usd', 0):.2f}

{profit_emoji} Résultat: {f"${trade_data.get('profit_loss', 0):.2f}" if trade_data.get('profit_loss') is not None else "En cours..."}

🚀 Généré avec Trading Calculator Pro
        """
        
        return share_text.strip()
    
    def generate_share_url(self, trade_data):
        """Génère une URL de partage pour un trade (Gratuit)"""
        # Encoder les données du trade en base64 pour l'URL
        trade_encoded = base64.urlsafe_b64encode(
            json.dumps(trade_data).encode()
        ).decode()
        
        # Créer l'URL de partage (hypothétique - à adapter selon votre domaine)
        share_url = f"https://your-domain.replit.app/shared-trade/{trade_encoded}"
        
        return share_url
    
    def generate_statistics_summary(self, stats_data):
        """Génère un résumé des statistiques pour partage (Gratuit)"""
        win_rate = stats_data.get('win_rate', 0)
        total_pnl = stats_data.get('total_pnl', 0)
        total_trades = stats_data.get('total_trades', 0)
        
        profit_emoji = "🚀" if total_pnl > 0 else "📉" if total_pnl < 0 else "⚡"
        
        summary = f"""
📊 MES STATISTIQUES DE TRADING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Total Trades: {total_trades}
🎯 Taux de Réussite: {win_rate:.1f}%
{profit_emoji} P&L Total: ${total_pnl:.2f}
📅 Période: {stats_data.get('period', 'Ce mois')}

💪 Généré avec Trading Calculator Pro
🔗 Rejoignez-moi sur la plateforme !
        """
        
        return summary.strip()
    
    def send_telegram_notification(self, message, chat_id=None):
        """Envoie une notification Telegram (Premium)"""
        if not self.telegram_token:
            return {
                'success': False,
                'error': 'Token Telegram non configuré'
            }
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id or os.environ.get("TELEGRAM_CHAT_ID"),
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Notification Telegram envoyée'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erreur Telegram: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur envoi Telegram: {str(e)}'
            }
    
    def send_discord_notification(self, message):
        """Envoie une notification Discord (Premium)"""
        if not self.discord_webhook:
            return {
                'success': False,
                'error': 'Webhook Discord non configuré'
            }
        
        try:
            payload = {
                'content': message,
                'username': 'Trading Bot',
                'avatar_url': 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png'
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                return {
                    'success': True,
                    'message': 'Notification Discord envoyée'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erreur Discord: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur envoi Discord: {str(e)}'
            }
    
    def create_trade_image(self, trade_data):
        """Crée une image de partage pour un trade (Premium avec fallback gratuit)"""
        # Pour la version gratuite, on génère du SVG
        # Pour la version premium, on pourrait utiliser PIL pour des images plus sophistiquées
        
        direction_color = "#28a745" if trade_data.get('direction', '').upper() == 'BUY' else "#dc3545"
        direction_emoji = "📈" if trade_data.get('direction', '').upper() == 'BUY' else "📉"
        
        svg_content = f"""
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
                </linearGradient>
            </defs>
            
            <!-- Background -->
            <rect width="600" height="400" fill="url(#bg)"/>
            
            <!-- Header -->
            <rect x="0" y="0" width="600" height="80" fill="{direction_color}"/>
            <text x="300" y="35" text-anchor="middle" fill="white" font-family="Arial" font-size="24" font-weight="bold">
                {direction_emoji} TRADE {trade_data.get('direction', '').upper()}
            </text>
            <text x="300" y="60" text-anchor="middle" fill="white" font-family="Arial" font-size="16">
                {trade_data.get('pair_symbol', 'N/A')}
            </text>
            
            <!-- Trade Details -->
            <text x="50" y="130" fill="white" font-family="Arial" font-size="18" font-weight="bold">Détails du Trade:</text>
            
            <text x="50" y="160" fill="#ccc" font-family="Arial" font-size="16">Entry Price:</text>
            <text x="200" y="160" fill="white" font-family="Arial" font-size="16">{trade_data.get('entry_price', 0):.5f}</text>
            
            <text x="50" y="185" fill="#ccc" font-family="Arial" font-size="16">Stop Loss:</text>
            <text x="200" y="185" fill="#ff6b6b" font-family="Arial" font-size="16">{trade_data.get('stop_loss', 0):.5f}</text>
            
            <text x="50" y="210" fill="#ccc" font-family="Arial" font-size="16">Take Profit:</text>
            <text x="200" y="210" fill="#51cf66" font-family="Arial" font-size="16">{trade_data.get('take_profit', 0):.5f}</text>
            
            <text x="50" y="235" fill="#ccc" font-family="Arial" font-size="16">Lot Size:</text>
            <text x="200" y="235" fill="white" font-family="Arial" font-size="16">{trade_data.get('lot_size', 0):.2f}</text>
            
            <!-- Risk Management -->
            <text x="350" y="130" fill="white" font-family="Arial" font-size="18" font-weight="bold">Risk Management:</text>
            
            <text x="350" y="160" fill="#ccc" font-family="Arial" font-size="16">Risk/Reward:</text>
            <text x="480" y="160" fill="white" font-family="Arial" font-size="16">1:{trade_data.get('risk_reward_ratio', 0):.2f}</text>
            
            <text x="350" y="185" fill="#ccc" font-family="Arial" font-size="16">Risk Amount:</text>
            <text x="480" y="185" fill="#ff9f43" font-family="Arial" font-size="16">${trade_data.get('risk_usd', 0):.2f}</text>
            
            <!-- Footer -->
            <rect x="0" y="320" width="600" height="80" fill="#2c2c54"/>
            <text x="300" y="350" text-anchor="middle" fill="white" font-family="Arial" font-size="16">
                🚀 Généré avec Trading Calculator Pro
            </text>
            <text x="300" y="375" text-anchor="middle" fill="#ccc" font-family="Arial" font-size="14">
                {datetime.now().strftime("%d/%m/%Y à %H:%M")}
            </text>
        </svg>
        """
        
        return {
            'success': True,
            'svg_content': svg_content,
            'filename': f"trade_{trade_data.get('pair_symbol', 'unknown')}_{int(datetime.now().timestamp())}.svg"
        }
    
    def sync_with_mt4(self, account_credentials):
        """Synchronisation avec MetaTrader 4 (Premium)"""
        # Placeholder pour intégration MT4
        return {
            'success': False,
            'error': 'Intégration MT4 en développement - Fonctionnalité Premium'
        }
    
    def sync_with_mt5(self, account_credentials):
        """Synchronisation avec MetaTrader 5 (Premium)"""
        # Placeholder pour intégration MT5
        return {
            'success': False,
            'error': 'Intégration MT5 en développement - Fonctionnalité Premium'
        }
    
    def get_integration_status(self):
        """Vérifie le statut des intégrations configurées"""
        status = {
            'telegram': {
                'configured': bool(self.telegram_token),
                'status': 'Actif' if self.telegram_token else 'Non configuré'
            },
            'discord': {
                'configured': bool(self.discord_webhook),
                'status': 'Actif' if self.discord_webhook else 'Non configuré'
            },
            'mt4': {
                'configured': False,
                'status': 'En développement'
            },
            'mt5': {
                'configured': False,
                'status': 'En développement'
            }
        }
        
        return status


# Instance globale des intégrations
trading_integrations = TradingIntegrations()