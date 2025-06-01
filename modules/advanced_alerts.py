"""
Système d'Alertes Avancé - SMS, Email, Push et Notifications Intelligentes
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class AlertType(Enum):
    PRICE_TARGET = "price_target"
    RISK_MANAGEMENT = "risk_management"
    PERFORMANCE = "performance"
    NEWS_EVENT = "news_event"
    TECHNICAL_SIGNAL = "technical_signal"

class NotificationChannel(Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    DISCORD = "discord"
    TELEGRAM = "telegram"

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PriceAlert:
    """Alerte de prix intelligente"""
    alert_id: str
    user_session: str
    pair_symbol: str
    target_price: float
    direction: str  # above, below, touch
    current_price: float
    alert_type: AlertType
    priority: AlertPriority
    
    # Canaux de notification
    notification_channels: List[NotificationChannel]
    
    # Messages personnalisés
    custom_message: Optional[str]
    alert_title: str
    
    # Paramètres avancés
    is_active: bool
    is_recurring: bool
    max_triggers: int
    trigger_count: int
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime]
    last_triggered: Optional[datetime]
    
    # Contexte trading
    associated_trade_id: Optional[str]
    risk_level: str
    strategy_context: Optional[str]

@dataclass
class NotificationResult:
    """Résultat d'envoi de notification"""
    channel: NotificationChannel
    success: bool
    message_id: Optional[str]
    error: Optional[str]
    delivery_time: datetime
    cost: float  # Coût en crédits

class AdvancedAlertSystem:
    """Système d'alertes avancé multi-canaux"""
    
    def __init__(self):
        self.active_alerts = {}  # alert_id -> PriceAlert
        self.user_alerts = {}    # user_session -> List[alert_id]
        self.notification_history = {}  # user_session -> List[NotificationResult]
        self.user_preferences = {}  # user_session -> Dict
        
        # Configuration des services
        self.setup_notification_services()
        
    def setup_notification_services(self):
        """Configuration des services de notification"""
        
        # Twilio SMS
        self.twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # SendGrid Email
        self.sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
        
        # Discord Webhook
        self.discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        
        # Telegram Bot
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
    def create_price_alert(self, alert_data: Dict) -> str:
        """Crée une nouvelle alerte de prix"""
        
        alert_id = f"alert_{int(datetime.now().timestamp())}_{alert_data['pair_symbol']}"
        
        # Validation du prix cible
        current_price = self._get_current_price(alert_data['pair_symbol'])
        if not current_price:
            raise ValueError(f"Impossible de récupérer le prix actuel pour {alert_data['pair_symbol']}")
        
        # Détermination de la priorité automatique
        price_diff_percent = abs(alert_data['target_price'] - current_price) / current_price * 100
        
        if price_diff_percent < 0.5:
            priority = AlertPriority.CRITICAL
        elif price_diff_percent < 2:
            priority = AlertPriority.HIGH
        elif price_diff_percent < 5:
            priority = AlertPriority.MEDIUM
        else:
            priority = AlertPriority.LOW
        
        # Création de l'alerte
        alert = PriceAlert(
            alert_id=alert_id,
            user_session=alert_data['user_session'],
            pair_symbol=alert_data['pair_symbol'],
            target_price=alert_data['target_price'],
            direction=alert_data.get('direction', 'touch'),
            current_price=current_price,
            alert_type=AlertType.PRICE_TARGET,
            priority=priority,
            notification_channels=[NotificationChannel(ch) for ch in alert_data.get('channels', ['email'])],
            custom_message=alert_data.get('custom_message'),
            alert_title=alert_data.get('title', f"Alerte {alert_data['pair_symbol']}"),
            is_active=True,
            is_recurring=alert_data.get('is_recurring', False),
            max_triggers=alert_data.get('max_triggers', 1),
            trigger_count=0,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=alert_data.get('expires_days', 30)),
            last_triggered=None,
            associated_trade_id=alert_data.get('trade_id'),
            risk_level=self._calculate_risk_level(price_diff_percent),
            strategy_context=alert_data.get('strategy')
        )
        
        # Sauvegarde
        self.active_alerts[alert_id] = alert
        
        user_session = alert_data['user_session']
        if user_session not in self.user_alerts:
            self.user_alerts[user_session] = []
        self.user_alerts[user_session].append(alert_id)
        
        # Notification de confirmation
        self._send_alert_confirmation(alert)
        
        return alert_id
    
    def check_price_alerts(self):
        """Vérifie toutes les alertes de prix actives"""
        
        triggered_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            if not alert.is_active:
                continue
                
            # Vérifier l'expiration
            if alert.expires_at and datetime.now() > alert.expires_at:
                alert.is_active = False
                continue
            
            # Récupérer le prix actuel
            current_price = self._get_current_price(alert.pair_symbol)
            if not current_price:
                continue
            
            alert.current_price = current_price
            
            # Vérifier si l'alerte est déclenchée
            is_triggered = self._check_alert_condition(alert, current_price)
            
            if is_triggered:
                triggered_alerts.append(alert)
                self._trigger_alert(alert)
        
        return triggered_alerts
    
    def _check_alert_condition(self, alert: PriceAlert, current_price: float) -> bool:
        """Vérifie si les conditions d'alerte sont remplies"""
        
        if alert.direction == "above":
            return current_price >= alert.target_price
        elif alert.direction == "below":
            return current_price <= alert.target_price
        elif alert.direction == "touch":
            # Tolérance de 0.1% pour "touch"
            tolerance = alert.target_price * 0.001
            return abs(current_price - alert.target_price) <= tolerance
        
        return False
    
    def _trigger_alert(self, alert: PriceAlert):
        """Déclenche une alerte et envoie les notifications"""
        
        alert.trigger_count += 1
        alert.last_triggered = datetime.now()
        
        # Préparer le message
        message = self._prepare_alert_message(alert)
        
        # Envoyer sur tous les canaux configurés
        notification_results = []
        
        for channel in alert.notification_channels:
            try:
                result = self._send_notification(channel, alert, message)
                notification_results.append(result)
            except Exception as e:
                notification_results.append(NotificationResult(
                    channel=channel,
                    success=False,
                    message_id=None,
                    error=str(e),
                    delivery_time=datetime.now(),
                    cost=0
                ))
        
        # Sauvegarder l'historique
        user_session = alert.user_session
        if user_session not in self.notification_history:
            self.notification_history[user_session] = []
        self.notification_history[user_session].extend(notification_results)
        
        # Gérer la récurrence
        if not alert.is_recurring or alert.trigger_count >= alert.max_triggers:
            alert.is_active = False
    
    def _prepare_alert_message(self, alert: PriceAlert) -> Dict[str, str]:
        """Prépare les messages d'alerte personnalisés"""
        
        # Message personnalisé ou automatique
        if alert.custom_message:
            main_message = alert.custom_message
        else:
            direction_text = {
                "above": "a dépassé",
                "below": "est tombé sous",
                "touch": "a atteint"
            }
            
            main_message = f"{alert.pair_symbol} {direction_text.get(alert.direction, 'a atteint')} {alert.target_price}"
        
        # Message détaillé
        detailed_message = f"""
🎯 ALERTE DE PRIX DÉCLENCHÉE

📊 Paire: {alert.pair_symbol}
💰 Prix cible: {alert.target_price}
📈 Prix actuel: {alert.current_price}
⏰ Heure: {alert.last_triggered.strftime('%H:%M:%S')}

{main_message}

🔗 Ouvrir Trading Calculator Pro pour plus de détails
        """.strip()
        
        # Messages adaptés par canal
        return {
            'title': alert.alert_title,
            'short': main_message,
            'detailed': detailed_message,
            'sms': f"🎯 {alert.pair_symbol}: {main_message}",
            'email_subject': f"Alerte Prix: {alert.pair_symbol}",
            'email_body': detailed_message,
            'push_title': alert.alert_title,
            'push_body': main_message
        }
    
    def _send_notification(self, channel: NotificationChannel, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie une notification sur un canal spécifique"""
        
        if channel == NotificationChannel.SMS:
            return self._send_sms(alert, message)
        elif channel == NotificationChannel.EMAIL:
            return self._send_email(alert, message)
        elif channel == NotificationChannel.PUSH:
            return self._send_push_notification(alert, message)
        elif channel == NotificationChannel.DISCORD:
            return self._send_discord_notification(alert, message)
        elif channel == NotificationChannel.TELEGRAM:
            return self._send_telegram_notification(alert, message)
        
        raise ValueError(f"Canal de notification non supporté: {channel}")
    
    def _send_sms(self, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie un SMS via Twilio"""
        
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
            raise ValueError("Configuration Twilio manquante")
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Récupérer le numéro de téléphone utilisateur
            user_phone = self._get_user_phone(alert.user_session)
            if not user_phone:
                raise ValueError("Numéro de téléphone utilisateur manquant")
            
            message_obj = client.messages.create(
                body=message['sms'],
                from_=self.twilio_phone_number,
                to=user_phone
            )
            
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=True,
                message_id=message_obj.sid,
                error=None,
                delivery_time=datetime.now(),
                cost=0.02  # Coût approximatif SMS
            )
            
        except Exception as e:
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=False,
                message_id=None,
                error=str(e),
                delivery_time=datetime.now(),
                cost=0
            )
    
    def _send_email(self, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie un email via SendGrid"""
        
        if not self.sendgrid_api_key:
            raise ValueError("Configuration SendGrid manquante")
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            # Récupérer l'email utilisateur
            user_email = self._get_user_email(alert.user_session)
            if not user_email:
                raise ValueError("Email utilisateur manquant")
            
            # Créer un email HTML riche
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                    <h1>🎯 Trading Calculator Pro</h1>
                    <h2>Alerte de Prix Déclenchée</h2>
                </div>
                
                <div style="padding: 20px; background: #f8f9fa;">
                    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h3 style="color: #28a745; margin-top: 0;">📊 {alert.pair_symbol}</h3>
                        
                        <div style="display: flex; justify-content: space-between; margin: 15px 0;">
                            <div>
                                <strong>Prix cible:</strong><br>
                                <span style="font-size: 18px; color: #007bff;">{alert.target_price}</span>
                            </div>
                            <div>
                                <strong>Prix actuel:</strong><br>
                                <span style="font-size: 18px; color: #28a745;">{alert.current_price}</span>
                            </div>
                        </div>
                        
                        <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <p style="margin: 0; font-size: 16px;"><strong>{message['short']}</strong></p>
                        </div>
                        
                        <p><strong>Heure:</strong> {alert.last_triggered.strftime('%d/%m/%Y à %H:%M:%S')}</p>
                        
                        {f"<p><strong>Stratégie:</strong> {alert.strategy_context}</p>" if alert.strategy_context else ""}
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="https://your-app-url.replit.app" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                📱 Ouvrir l'Application
                            </a>
                        </div>
                    </div>
                </div>
                
                <div style="background: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px;">
                    Trading Calculator Pro - Votre assistant de trading intelligent
                </div>
            </div>
            """
            
            mail = Mail(
                from_email="alerts@tradingcalculator.pro",
                to_emails=user_email,
                subject=message['email_subject'],
                html_content=html_content
            )
            
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(mail)
            
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=True,
                message_id=response.headers.get('X-Message-Id'),
                error=None,
                delivery_time=datetime.now(),
                cost=0.001  # Coût approximatif email
            )
            
        except Exception as e:
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                message_id=None,
                error=str(e),
                delivery_time=datetime.now(),
                cost=0
            )
    
    def _send_push_notification(self, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie une notification push"""
        
        # Simulation de notification push (à intégrer avec un service comme OneSignal)
        try:
            # En production, ici vous utiliseriez un service comme OneSignal, FCM, etc.
            push_data = {
                'title': message['push_title'],
                'body': message['push_body'],
                'icon': 'https://your-app-url.replit.app/static/icon.png',
                'badge': 'https://your-app-url.replit.app/static/badge.png',
                'data': {
                    'alert_id': alert.alert_id,
                    'pair_symbol': alert.pair_symbol,
                    'price': alert.current_price
                }
            }
            
            # Simulation réussie
            return NotificationResult(
                channel=NotificationChannel.PUSH,
                success=True,
                message_id=f"push_{int(datetime.now().timestamp())}",
                error=None,
                delivery_time=datetime.now(),
                cost=0.001
            )
            
        except Exception as e:
            return NotificationResult(
                channel=NotificationChannel.PUSH,
                success=False,
                message_id=None,
                error=str(e),
                delivery_time=datetime.now(),
                cost=0
            )
    
    def _send_discord_notification(self, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie une notification Discord via webhook"""
        
        if not self.discord_webhook_url:
            raise ValueError("Discord webhook URL manquante")
        
        try:
            import requests
            
            # Déterminer la couleur selon la priorité
            color_map = {
                AlertPriority.LOW: 0x6c757d,      # Gris
                AlertPriority.MEDIUM: 0xffc107,   # Jaune
                AlertPriority.HIGH: 0xfd7e14,     # Orange
                AlertPriority.CRITICAL: 0xdc3545  # Rouge
            }
            
            embed = {
                "title": f"🎯 Alerte: {alert.pair_symbol}",
                "description": message['short'],
                "color": color_map.get(alert.priority, 0x007bff),
                "fields": [
                    {
                        "name": "💰 Prix cible",
                        "value": str(alert.target_price),
                        "inline": True
                    },
                    {
                        "name": "📈 Prix actuel", 
                        "value": str(alert.current_price),
                        "inline": True
                    },
                    {
                        "name": "⏰ Heure",
                        "value": alert.last_triggered.strftime('%H:%M:%S'),
                        "inline": True
                    }
                ],
                "timestamp": alert.last_triggered.isoformat(),
                "footer": {
                    "text": "Trading Calculator Pro"
                }
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(self.discord_webhook_url, json=payload)
            response.raise_for_status()
            
            return NotificationResult(
                channel=NotificationChannel.DISCORD,
                success=True,
                message_id=f"discord_{int(datetime.now().timestamp())}",
                error=None,
                delivery_time=datetime.now(),
                cost=0
            )
            
        except Exception as e:
            return NotificationResult(
                channel=NotificationChannel.DISCORD,
                success=False,
                message_id=None,
                error=str(e),
                delivery_time=datetime.now(),
                cost=0
            )
    
    def _send_telegram_notification(self, alert: PriceAlert, message: Dict[str, str]) -> NotificationResult:
        """Envoie une notification Telegram"""
        
        if not self.telegram_bot_token:
            raise ValueError("Token Telegram Bot manquant")
        
        try:
            import requests
            
            # Récupérer le chat_id utilisateur
            chat_id = self._get_user_telegram_chat_id(alert.user_session)
            if not chat_id:
                raise ValueError("Chat ID Telegram utilisateur manquant")
            
            # Message formaté en Markdown
            telegram_message = f"""
🎯 *ALERTE DE PRIX*

📊 *Paire:* `{alert.pair_symbol}`
💰 *Prix cible:* `{alert.target_price}`
📈 *Prix actuel:* `{alert.current_price}`
⏰ *Heure:* `{alert.last_triggered.strftime('%H:%M:%S')}`

_{message['short']}_

[📱 Ouvrir l'App](https://your-app-url.replit.app)
            """.strip()
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': telegram_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return NotificationResult(
                channel=NotificationChannel.TELEGRAM,
                success=True,
                message_id=str(result.get('result', {}).get('message_id')),
                error=None,
                delivery_time=datetime.now(),
                cost=0
            )
            
        except Exception as e:
            return NotificationResult(
                channel=NotificationChannel.TELEGRAM,
                success=False,
                message_id=None,
                error=str(e),
                delivery_time=datetime.now(),
                cost=0
            )
    
    def _get_current_price(self, pair_symbol: str) -> Optional[float]:
        """Récupère le prix actuel d'une paire"""
        # Simulation - en production, utiliser une vraie API de prix
        prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'XAUUSD': 2000.00,
            'BTCUSD': 45000.00,
            'ETHUSD': 2800.00
        }
        return prices.get(pair_symbol)
    
    def _calculate_risk_level(self, price_diff_percent: float) -> str:
        """Calcule le niveau de risque de l'alerte"""
        if price_diff_percent < 1:
            return "critical"
        elif price_diff_percent < 3:
            return "high"
        elif price_diff_percent < 7:
            return "medium"
        else:
            return "low"
    
    def _get_user_phone(self, user_session: str) -> Optional[str]:
        """Récupère le numéro de téléphone utilisateur"""
        # En production, récupérer depuis la base de données
        user_prefs = self.user_preferences.get(user_session, {})
        return user_prefs.get('phone_number')
    
    def _get_user_email(self, user_session: str) -> Optional[str]:
        """Récupère l'email utilisateur"""
        user_prefs = self.user_preferences.get(user_session, {})
        return user_prefs.get('email')
    
    def _get_user_telegram_chat_id(self, user_session: str) -> Optional[str]:
        """Récupère le chat ID Telegram utilisateur"""
        user_prefs = self.user_preferences.get(user_session, {})
        return user_prefs.get('telegram_chat_id')
    
    def _send_alert_confirmation(self, alert: PriceAlert):
        """Envoie une confirmation de création d'alerte"""
        
        confirmation_message = {
            'title': 'Alerte Créée',
            'short': f"Alerte créée pour {alert.pair_symbol} à {alert.target_price}",
            'sms': f"✅ Alerte {alert.pair_symbol} créée à {alert.target_price}",
            'email_subject': 'Confirmation - Alerte Créée',
            'email_body': f"Votre alerte pour {alert.pair_symbol} à {alert.target_price} a été créée avec succès."
        }
        
        # Envoyer uniquement par email pour confirmation
        try:
            if NotificationChannel.EMAIL in alert.notification_channels:
                self._send_notification(NotificationChannel.EMAIL, alert, confirmation_message)
        except:
            pass  # Pas critique si la confirmation échoue
    
    def get_user_alerts(self, user_session: str, active_only: bool = True) -> List[PriceAlert]:
        """Récupère les alertes d'un utilisateur"""
        
        user_alert_ids = self.user_alerts.get(user_session, [])
        alerts = []
        
        for alert_id in user_alert_ids:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                if not active_only or alert.is_active:
                    alerts.append(alert)
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def delete_alert(self, user_session: str, alert_id: str) -> bool:
        """Supprime une alerte"""
        
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        if alert.user_session != user_session:
            return False
        
        alert.is_active = False
        return True
    
    def set_user_preferences(self, user_session: str, preferences: Dict):
        """Configure les préférences utilisateur"""
        
        self.user_preferences[user_session] = {
            'phone_number': preferences.get('phone_number'),
            'email': preferences.get('email'),
            'telegram_chat_id': preferences.get('telegram_chat_id'),
            'discord_user_id': preferences.get('discord_user_id'),
            'preferred_channels': preferences.get('preferred_channels', ['email']),
            'notification_hours': preferences.get('notification_hours', [9, 18]),  # Heures préférées
            'timezone': preferences.get('timezone', 'UTC')
        }
    
    def get_notification_stats(self, user_session: str) -> Dict:
        """Statistiques des notifications utilisateur"""
        
        history = self.notification_history.get(user_session, [])
        
        if not history:
            return {"message": "Aucune notification envoyée"}
        
        stats = {
            'total_notifications': len(history),
            'successful_notifications': len([n for n in history if n.success]),
            'failed_notifications': len([n for n in history if not n.success]),
            'total_cost': sum(n.cost for n in history),
            'channels_used': list(set(n.channel.value for n in history)),
            'last_notification': max(history, key=lambda x: x.delivery_time).delivery_time.isoformat()
        }
        
        return stats

# Instance globale du système d'alertes
advanced_alert_system = AdvancedAlertSystem()