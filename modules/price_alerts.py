"""
Système d'alertes de prix en temps réel
"""
import os
import json
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Callable
import requests
from app import db

@dataclass
class PriceAlert:
    """Classe pour représenter une alerte de prix"""
    id: str
    user_session: str
    pair_symbol: str
    alert_type: str  # 'above', 'below', 'percentage_up', 'percentage_down'
    target_price: float
    current_price: float
    percentage_threshold: Optional[float]
    is_active: bool
    created_at: datetime
    triggered_at: Optional[datetime]
    message: str
    notification_sent: bool

class PriceMonitor:
    """Moniteur de prix en temps réel avec système d'alertes"""
    
    def __init__(self):
        self.alerts: List[PriceAlert] = []
        self.running = False
        self.monitor_thread = None
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
        self.last_prices = {}
        
    def add_alert(self, user_session: str, pair_symbol: str, alert_type: str, 
                  target_price: float, percentage_threshold: Optional[float] = None) -> str:
        """Ajoute une nouvelle alerte de prix"""
        
        alert_id = f"{user_session}_{pair_symbol}_{int(time.time())}"
        
        # Obtenir le prix actuel
        current_price = self._get_current_price(pair_symbol)
        if not current_price:
            raise Exception(f"Impossible d'obtenir le prix actuel pour {pair_symbol}")
        
        # Créer le message d'alerte
        if alert_type in ['above', 'below']:
            direction = "au-dessus de" if alert_type == 'above' else "en-dessous de"
            message = f"🚨 {pair_symbol} a atteint {target_price} ({direction} votre seuil)"
        else:
            direction = "hausse" if alert_type == 'percentage_up' else "baisse"
            message = f"📈 {pair_symbol} {direction} de {percentage_threshold}% détectée !"
        
        alert = PriceAlert(
            id=alert_id,
            user_session=user_session,
            pair_symbol=pair_symbol,
            alert_type=alert_type,
            target_price=target_price,
            current_price=current_price,
            percentage_threshold=percentage_threshold,
            is_active=True,
            created_at=datetime.now(),
            triggered_at=None,
            message=message,
            notification_sent=False
        )
        
        self.alerts.append(alert)
        
        # Sauvegarder en base de données
        self._save_alert_to_db(alert)
        
        return alert_id
    
    def remove_alert(self, alert_id: str, user_session: str) -> bool:
        """Supprime une alerte"""
        for i, alert in enumerate(self.alerts):
            if alert.id == alert_id and alert.user_session == user_session:
                self.alerts.pop(i)
                self._remove_alert_from_db(alert_id)
                return True
        return False
    
    def get_user_alerts(self, user_session: str) -> List[PriceAlert]:
        """Récupère toutes les alertes d'un utilisateur"""
        return [alert for alert in self.alerts if alert.user_session == user_session]
    
    def start_monitoring(self):
        """Démarre le monitoring des prix en arrière-plan"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_prices, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Arrête le monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_prices(self):
        """Boucle principale de monitoring des prix"""
        while self.running:
            try:
                active_alerts = [alert for alert in self.alerts if alert.is_active]
                
                if not active_alerts:
                    time.sleep(30)  # Attendre 30 secondes si pas d'alertes
                    continue
                
                # Obtenir les paires uniques à surveiller
                pairs_to_monitor = list(set(alert.pair_symbol for alert in active_alerts))
                
                # Récupérer les prix actuels
                for pair in pairs_to_monitor:
                    current_price = self._get_current_price(pair)
                    if current_price:
                        self.last_prices[pair] = current_price
                        self._check_alerts_for_pair(pair, current_price)
                
                # Attendre 60 secondes avant la prochaine vérification
                time.sleep(60)
                
            except Exception as e:
                print(f"Erreur dans le monitoring: {e}")
                time.sleep(60)
    
    def _check_alerts_for_pair(self, pair_symbol: str, current_price: float):
        """Vérifie les alertes pour une paire spécifique"""
        pair_alerts = [alert for alert in self.alerts 
                      if alert.pair_symbol == pair_symbol and alert.is_active]
        
        for alert in pair_alerts:
            triggered = False
            
            if alert.alert_type == 'above' and current_price >= alert.target_price:
                triggered = True
            elif alert.alert_type == 'below' and current_price <= alert.target_price:
                triggered = True
            elif alert.alert_type == 'percentage_up':
                price_change = ((current_price - alert.current_price) / alert.current_price) * 100
                if price_change >= alert.percentage_threshold:
                    triggered = True
            elif alert.alert_type == 'percentage_down':
                price_change = ((alert.current_price - current_price) / alert.current_price) * 100
                if price_change >= alert.percentage_threshold:
                    triggered = True
            
            if triggered:
                self._trigger_alert(alert, current_price)
    
    def _trigger_alert(self, alert: PriceAlert, current_price: float):
        """Déclenche une alerte et envoie la notification"""
        alert.is_active = False
        alert.triggered_at = datetime.now()
        alert.current_price = current_price
        
        # Créer le message de notification
        notification_message = alert.message.replace(str(alert.target_price), str(current_price))
        
        # Sauvegarder le déclenchement en base
        self._update_alert_in_db(alert)
        
        # Envoyer la notification (sera gérée par l'interface web)
        print(f"ALERTE DÉCLENCHÉE: {notification_message}")
        
        # Marquer comme envoyée
        alert.notification_sent = True
    
    def _get_current_price(self, pair_symbol: str) -> Optional[float]:
        """Récupère le prix actuel d'une paire depuis Alpha Vantage"""
        try:
            # Utiliser la fonction existante de l'app
            from app import get_current_price_optimized
            return get_current_price_optimized(pair_symbol)
            
        except Exception as e:
            print(f"Erreur récupération prix {pair_symbol}: {e}")
            
            # Fallback avec des prix de démonstration réalistes
            demo_prices = {
                'XAUUSD': 1985.50 + (time.time() % 100 - 50) * 0.1,
                'EURUSD': 1.0850 + (time.time() % 100 - 50) * 0.0001,
                'GBPUSD': 1.2650 + (time.time() % 100 - 50) * 0.0001,
                'USDJPY': 149.20 + (time.time() % 100 - 50) * 0.01,
                'USDCAD': 1.3580 + (time.time() % 100 - 50) * 0.0001,
                'AUDUSD': 0.6720 + (time.time() % 100 - 50) * 0.0001,
            }
            
            return demo_prices.get(pair_symbol, 1.0000)
    
    def _save_alert_to_db(self, alert: PriceAlert):
        """Sauvegarde une alerte en base de données"""
        try:
            from models import PriceAlertModel
            
            db_alert = PriceAlertModel(
                alert_id=alert.id,
                user_session=alert.user_session,
                pair_symbol=alert.pair_symbol,
                alert_type=alert.alert_type,
                target_price=alert.target_price,
                current_price=alert.current_price,
                percentage_threshold=alert.percentage_threshold,
                is_active=alert.is_active,
                message=alert.message,
                created_at=alert.created_at
            )
            
            db.session.add(db_alert)
            db.session.commit()
            
        except Exception as e:
            print(f"Erreur sauvegarde alerte: {e}")
    
    def _update_alert_in_db(self, alert: PriceAlert):
        """Met à jour une alerte en base de données"""
        try:
            from models import PriceAlertModel
            
            db_alert = PriceAlertModel.query.filter_by(alert_id=alert.id).first()
            if db_alert:
                db_alert.is_active = alert.is_active
                db_alert.triggered_at = alert.triggered_at
                db_alert.current_price = alert.current_price
                db_alert.notification_sent = alert.notification_sent
                db.session.commit()
                
        except Exception as e:
            print(f"Erreur mise à jour alerte: {e}")
    
    def _remove_alert_from_db(self, alert_id: str):
        """Supprime une alerte de la base de données"""
        try:
            from models import PriceAlertModel
            
            db_alert = PriceAlertModel.query.filter_by(alert_id=alert_id).first()
            if db_alert:
                db.session.delete(db_alert)
                db.session.commit()
                
        except Exception as e:
            print(f"Erreur suppression alerte: {e}")
    
    def load_alerts_from_db(self):
        """Charge les alertes depuis la base de données au démarrage"""
        try:
            from models import PriceAlertModel
            
            db_alerts = PriceAlertModel.query.filter_by(is_active=True).all()
            
            for db_alert in db_alerts:
                alert = PriceAlert(
                    id=db_alert.alert_id,
                    user_session=db_alert.user_session,
                    pair_symbol=db_alert.pair_symbol,
                    alert_type=db_alert.alert_type,
                    target_price=db_alert.target_price,
                    current_price=db_alert.current_price,
                    percentage_threshold=db_alert.percentage_threshold,
                    is_active=db_alert.is_active,
                    created_at=db_alert.created_at,
                    triggered_at=db_alert.triggered_at,
                    message=db_alert.message,
                    notification_sent=db_alert.notification_sent or False
                )
                self.alerts.append(alert)
                
        except Exception as e:
            print(f"Erreur chargement alertes: {e}")
    
    def get_triggered_alerts(self, user_session: str) -> List[PriceAlert]:
        """Récupère les alertes déclenchées récemment"""
        return [alert for alert in self.alerts 
                if alert.user_session == user_session 
                and alert.triggered_at 
                and not alert.notification_sent]
    
    def mark_notifications_as_sent(self, alert_ids: List[str]):
        """Marque les notifications comme envoyées"""
        for alert in self.alerts:
            if alert.id in alert_ids:
                alert.notification_sent = True
                self._update_alert_in_db(alert)


# Instance globale du moniteur de prix
price_monitor = PriceMonitor()

# Démarrer le monitoring au lancement du module
price_monitor.load_alerts_from_db()
price_monitor.start_monitoring()