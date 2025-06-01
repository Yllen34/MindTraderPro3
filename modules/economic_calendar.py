"""
Calendrier Économique - Événements financiers en temps réel
"""
import os
import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class EconomicEvent:
    """Classe pour représenter un événement économique"""
    id: str
    title: str
    country: str
    currency: str
    date: datetime
    time: str
    impact: str  # low, medium, high
    forecast: Optional[str]
    previous: Optional[str]
    actual: Optional[str]
    description: str
    category: str

class EconomicCalendarAPI:
    """Gestionnaire du calendrier économique"""
    
    def __init__(self):
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
        self.trading_economics_key = os.environ.get("TRADING_ECONOMICS_API_KEY")
        
    def get_economic_events(self, days_ahead: int = 7) -> List[EconomicEvent]:
        """Récupère les événements économiques pour les prochains jours"""
        events = []
        
        # Essayer Alpha Vantage d'abord
        alpha_events = self._get_alpha_vantage_events()
        if alpha_events:
            events.extend(alpha_events)
        
        # Ajouter des événements de Trading Economics si disponible
        if self.trading_economics_key:
            te_events = self._get_trading_economics_events(days_ahead)
            events.extend(te_events)
        
        # Si aucune API n'est disponible, utiliser des données de démonstration
        if not events:
            events = self._get_demo_events()
        
        # Trier par date
        events.sort(key=lambda x: x.date)
        
        return events
    
    def _get_alpha_vantage_events(self) -> List[EconomicEvent]:
        """Récupère les événements depuis Alpha Vantage"""
        try:
            # Alpha Vantage n'a pas d'endpoint calendrier économique direct
            # On utilisera leur fonction NEWS & SENTIMENT pour les événements majeurs
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'topics': 'economy_fiscal,economy_monetary',
                'apikey': self.alpha_vantage_key,
                'limit': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = []
                
                if 'feed' in data:
                    for item in data['feed'][:10]:  # Limiter à 10 événements
                        # Convertir les nouvelles en événements économiques
                        event = EconomicEvent(
                            id=item.get('url', '')[-10:],
                            title=item.get('title', ''),
                            country='US',  # Par défaut
                            currency='USD',
                            date=self._parse_date(item.get('time_published', '')),
                            time='09:00',
                            impact='medium',
                            forecast=None,
                            previous=None,
                            actual=None,
                            description=item.get('summary', '')[:200] + '...',
                            category='news'
                        )
                        events.append(event)
                
                return events
                
        except Exception as e:
            print(f"Erreur Alpha Vantage: {e}")
            return []
    
    def _get_trading_economics_events(self, days_ahead: int) -> List[EconomicEvent]:
        """Récupère les événements depuis Trading Economics"""
        try:
            # API Trading Economics pour le calendrier économique
            url = f"https://api.tradingeconomics.com/calendar"
            headers = {
                'Authorization': f'Client {self.trading_economics_key}'
            }
            
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            params = {
                'c': 'guest:guest',
                'f': 'json',
                'd1': datetime.now().strftime('%Y-%m-%d'),
                'd2': end_date
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = []
                
                for item in data:
                    event = EconomicEvent(
                        id=str(item.get('CalendarId', '')),
                        title=item.get('Event', ''),
                        country=item.get('Country', ''),
                        currency=item.get('Currency', ''),
                        date=self._parse_date(item.get('Date', '')),
                        time=item.get('Time', ''),
                        impact=self._normalize_impact(item.get('Importance', '')),
                        forecast=item.get('Forecast'),
                        previous=item.get('Previous'),
                        actual=item.get('Actual'),
                        description=item.get('Event', ''),
                        category='economic'
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            print(f"Erreur Trading Economics: {e}")
            return []
    
    def _get_demo_events(self) -> List[EconomicEvent]:
        """Génère des événements de démonstration avec données réalistes"""
        base_date = datetime.now()
        
        demo_events = [
            {
                'title': 'Non-Farm Payrolls (NFP)',
                'country': 'US',
                'currency': 'USD',
                'days_offset': 2,
                'time': '14:30',
                'impact': 'high',
                'forecast': '180K',
                'previous': '175K',
                'description': 'Emplois non-agricoles créés le mois dernier aux États-Unis'
            },
            {
                'title': 'Taux Directeur BCE',
                'country': 'EU',
                'currency': 'EUR',
                'days_offset': 3,
                'time': '13:45',
                'impact': 'high',
                'forecast': '4.50%',
                'previous': '4.50%',
                'description': 'Décision de politique monétaire de la Banque Centrale Européenne'
            },
            {
                'title': 'Inflation CPI (YoY)',
                'country': 'US',
                'currency': 'USD',
                'days_offset': 1,
                'time': '14:30',
                'impact': 'high',
                'forecast': '3.2%',
                'previous': '3.4%',
                'description': 'Indice des prix à la consommation annuel américain'
            },
            {
                'title': 'GDP Preliminary',
                'country': 'GB',
                'currency': 'GBP',
                'days_offset': 4,
                'time': '09:30',
                'impact': 'medium',
                'forecast': '0.3%',
                'previous': '0.1%',
                'description': 'Produit Intérieur Brut préliminaire du Royaume-Uni'
            },
            {
                'title': 'Retail Sales',
                'country': 'US',
                'currency': 'USD',
                'days_offset': 5,
                'time': '14:30',
                'impact': 'medium',
                'forecast': '0.4%',
                'previous': '0.6%',
                'description': 'Ventes au détail mensuelles aux États-Unis'
            },
            {
                'title': 'Unemployment Rate',
                'country': 'CA',
                'currency': 'CAD',
                'days_offset': 6,
                'time': '14:30',
                'impact': 'medium',
                'forecast': '6.1%',
                'previous': '6.2%',
                'description': 'Taux de chômage canadien'
            }
        ]
        
        events = []
        for i, event_data in enumerate(demo_events):
            event_date = base_date + timedelta(days=event_data['days_offset'])
            
            event = EconomicEvent(
                id=f"demo_{i}",
                title=event_data['title'],
                country=event_data['country'],
                currency=event_data['currency'],
                date=event_date,
                time=event_data['time'],
                impact=event_data['impact'],
                forecast=event_data['forecast'],
                previous=event_data['previous'],
                actual=None,  # Pas encore publié
                description=event_data['description'],
                category='economic'
            )
            events.append(event)
        
        return events
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse différents formats de date"""
        try:
            # Format Alpha Vantage: 20241122T143000
            if 'T' in date_str and len(date_str) > 10:
                return datetime.strptime(date_str[:8], '%Y%m%d')
            
            # Format ISO: 2024-11-22
            if '-' in date_str:
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
            
            # Défaut: aujourd'hui
            return datetime.now()
            
        except:
            return datetime.now()
    
    def _normalize_impact(self, impact: str) -> str:
        """Normalise l'importance de l'événement"""
        impact = impact.lower()
        
        if impact in ['3', 'high', 'red']:
            return 'high'
        elif impact in ['2', 'medium', 'orange', 'yellow']:
            return 'medium'
        else:
            return 'low'
    
    def get_events_by_impact(self, impact: str) -> List[EconomicEvent]:
        """Filtre les événements par impact"""
        all_events = self.get_economic_events()
        return [event for event in all_events if event.impact == impact]
    
    def get_events_by_currency(self, currency: str) -> List[EconomicEvent]:
        """Filtre les événements par devise"""
        all_events = self.get_economic_events()
        return [event for event in all_events if event.currency == currency]
    
    def get_upcoming_high_impact_events(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Récupère les événements à fort impact dans les prochaines heures"""
        all_events = self.get_economic_events()
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)
        
        return [
            event for event in all_events 
            if event.impact == 'high' and event.date <= cutoff_time
        ]


# Instance globale du calendrier économique
economic_calendar = EconomicCalendarAPI()