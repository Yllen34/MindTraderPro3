"""
Journal de Trading Intelligent avec enregistrement automatique et analyse avancée
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class TradeStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PENDING = "pending"

class EmotionalState(Enum):
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    FEARFUL = "fearful"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    EUPHORIC = "euphoric"

class TradeStrategy(Enum):
    SCALPING = "scalping"
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    BREAKOUT = "breakout"
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    SMC = "smart_money_concepts"
    ICT = "ict_concepts"

@dataclass
class SmartTradeEntry:
    """Entrée de trade intelligente avec métadonnées complètes"""
    # Informations de base
    trade_id: str
    user_session: str
    pair_symbol: str
    direction: str
    lot_size: float
    
    # Prix et timing
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    entry_time: datetime
    exit_time: Optional[datetime]
    
    # Résultats
    profit_loss: Optional[float]
    profit_loss_pips: Optional[float]
    status: TradeStatus
    
    # Métadonnées intelligentes
    strategy: Optional[TradeStrategy]
    market_context: str
    confluence_factors: List[str]
    emotional_state: EmotionalState
    confidence_level: int  # 1-10
    stress_level: int  # 1-10
    
    # Notes et tags
    notes: str
    tags: List[str]
    screenshots: List[str]
    
    # Analyse technique
    timeframe: str
    market_structure: str  # uptrend, downtrend, sideways
    key_levels: List[float]
    volume_analysis: str
    
    # Import automatique
    imported_from: Optional[str]  # MT4, MT5, TradingView, Manual
    import_timestamp: Optional[datetime]
    
    # Scoring
    setup_quality: int  # 1-10
    execution_quality: int  # 1-10
    risk_reward_ratio: float
    
    created_at: datetime
    updated_at: datetime

class SmartJournalManager:
    """Gestionnaire intelligent du journal de trading"""
    
    def __init__(self):
        self.trades = {}
        self.filters = {}
        self.auto_import_enabled = True
        
    def add_trade(self, trade_data: Dict) -> str:
        """Ajoute un nouveau trade avec validation intelligente"""
        
        # Génération ID unique
        trade_id = f"trade_{int(datetime.now().timestamp())}_{trade_data.get('pair_symbol', 'XXX')}"
        
        # Validation et enrichissement automatique
        enriched_data = self._enrich_trade_data(trade_data)
        
        # Création de l'entrée de trade
        trade_entry = SmartTradeEntry(
            trade_id=trade_id,
            user_session=trade_data.get('user_session', 'default'),
            pair_symbol=trade_data['pair_symbol'],
            direction=trade_data['direction'],
            lot_size=trade_data['lot_size'],
            entry_price=trade_data['entry_price'],
            exit_price=trade_data.get('exit_price'),
            stop_loss=trade_data['stop_loss'],
            take_profit=trade_data['take_profit'],
            entry_time=trade_data.get('entry_time', datetime.now()),
            exit_time=trade_data.get('exit_time'),
            profit_loss=trade_data.get('profit_loss'),
            profit_loss_pips=trade_data.get('profit_loss_pips'),
            status=TradeStatus(trade_data.get('status', 'open')),
            strategy=TradeStrategy(trade_data.get('strategy', 'day_trading')),
            market_context=enriched_data['market_context'],
            confluence_factors=trade_data.get('confluence_factors', []),
            emotional_state=EmotionalState(trade_data.get('emotional_state', 'calm')),
            confidence_level=trade_data.get('confidence_level', 5),
            stress_level=trade_data.get('stress_level', 3),
            notes=trade_data.get('notes', ''),
            tags=trade_data.get('tags', []),
            screenshots=trade_data.get('screenshots', []),
            timeframe=trade_data.get('timeframe', 'H1'),
            market_structure=enriched_data['market_structure'],
            key_levels=trade_data.get('key_levels', []),
            volume_analysis=trade_data.get('volume_analysis', ''),
            imported_from=trade_data.get('imported_from'),
            import_timestamp=trade_data.get('import_timestamp'),
            setup_quality=trade_data.get('setup_quality', 7),
            execution_quality=trade_data.get('execution_quality', 7),
            risk_reward_ratio=enriched_data['risk_reward_ratio'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Sauvegarde
        self.trades[trade_id] = trade_entry
        self._save_to_database(trade_entry)
        
        # Analyse automatique post-ajout
        self._analyze_trade_patterns(trade_entry)
        
        return trade_id
    
    def _enrich_trade_data(self, trade_data: Dict) -> Dict:
        """Enrichit automatiquement les données du trade"""
        
        # Calcul du Risk/Reward ratio
        entry_price = trade_data['entry_price']
        stop_loss = trade_data['stop_loss']
        take_profit = trade_data['take_profit']
        
        if trade_data['direction'].upper() == 'BUY':
            risk_pips = abs(entry_price - stop_loss)
            reward_pips = abs(take_profit - entry_price)
        else:
            risk_pips = abs(stop_loss - entry_price)
            reward_pips = abs(entry_price - take_profit)
        
        risk_reward_ratio = reward_pips / risk_pips if risk_pips > 0 else 0
        
        # Analyse du contexte de marché (simulation intelligente)
        market_context = self._analyze_market_context(trade_data['pair_symbol'], trade_data.get('entry_time', datetime.now()))
        
        # Détermination de la structure de marché
        market_structure = self._determine_market_structure(trade_data['pair_symbol'])
        
        return {
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'market_context': market_context,
            'market_structure': market_structure
        }
    
    def _analyze_market_context(self, pair_symbol: str, entry_time: datetime) -> str:
        """Analyse le contexte de marché au moment du trade"""
        
        # Analyse des sessions de trading
        hour = entry_time.hour
        day_of_week = entry_time.weekday()
        
        sessions = []
        if 7 <= hour <= 16:
            sessions.append("Londres")
        if 13 <= hour <= 22:
            sessions.append("New York")
        if 0 <= hour <= 9:
            sessions.append("Asie")
        
        # Analyse de la volatilité attendue
        volatility = "normale"
        if day_of_week == 4:  # Vendredi
            volatility = "réduite"
        elif 8 <= hour <= 12:  # Overlap Londres-NY
            volatility = "élevée"
        
        # Événements économiques (simulation)
        economic_impact = "aucun événement majeur"
        if hour in [14, 15, 16]:  # Heures typiques des annonces US
            economic_impact = "possible volatilité sur annonces"
        
        return f"Sessions: {', '.join(sessions) if sessions else 'Hors session'}. " \
               f"Volatilité: {volatility}. {economic_impact}."
    
    def _determine_market_structure(self, pair_symbol: str) -> str:
        """Détermine la structure de marché (simulation)"""
        # En production, ceci ferait appel à une analyse technique réelle
        structures = ["uptrend", "downtrend", "sideways", "consolidation"]
        # Simulation basée sur la paire
        if "USD" in pair_symbol:
            return "uptrend" if pair_symbol.startswith("USD") else "downtrend"
        return "sideways"
    
    def _analyze_trade_patterns(self, trade: SmartTradeEntry):
        """Analyse automatique des patterns après ajout d'un trade"""
        
        # Cette fonction pourrait déclencher :
        # - Mise à jour des statistiques
        # - Détection de nouveaux patterns
        # - Suggestions d'amélioration
        # - Alertes sur le comportement de trading
        
        user_trades = self.get_user_trades(trade.user_session)
        
        # Exemple d'analyse simple
        if len(user_trades) >= 5:
            recent_trades = user_trades[-5:]
            
            # Analyse des heures de trading
            hours = [t.entry_time.hour for t in recent_trades]
            most_common_hour = max(set(hours), key=hours.count)
            
            # Analyse des émotions
            emotions = [t.emotional_state.value for t in recent_trades]
            
            # Ici on pourrait déclencher des insights automatiques
            print(f"Pattern détecté: Trading fréquent à {most_common_hour}h")
    
    def get_user_trades(self, user_session: str, filters: Optional[Dict] = None) -> List[SmartTradeEntry]:
        """Récupère les trades d'un utilisateur avec filtres optionnels"""
        
        user_trades = [trade for trade in self.trades.values() 
                      if trade.user_session == user_session]
        
        if not filters:
            return sorted(user_trades, key=lambda x: x.created_at, reverse=True)
        
        # Application des filtres
        filtered_trades = user_trades
        
        if 'strategy' in filters:
            filtered_trades = [t for t in filtered_trades 
                             if t.strategy and t.strategy.value == filters['strategy']]
        
        if 'pair_symbol' in filters:
            filtered_trades = [t for t in filtered_trades 
                             if t.pair_symbol == filters['pair_symbol']]
        
        if 'status' in filters:
            filtered_trades = [t for t in filtered_trades 
                             if t.status.value == filters['status']]
        
        if 'date_from' in filters:
            date_from = datetime.fromisoformat(filters['date_from'])
            filtered_trades = [t for t in filtered_trades 
                             if t.entry_time >= date_from]
        
        if 'date_to' in filters:
            date_to = datetime.fromisoformat(filters['date_to'])
            filtered_trades = [t for t in filtered_trades 
                             if t.entry_time <= date_to]
        
        if 'tags' in filters:
            filter_tags = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
            filtered_trades = [t for t in filtered_trades 
                             if any(tag in t.tags for tag in filter_tags)]
        
        if 'min_profit' in filters:
            filtered_trades = [t for t in filtered_trades 
                             if t.profit_loss and t.profit_loss >= filters['min_profit']]
        
        if 'emotional_state' in filters:
            filtered_trades = [t for t in filtered_trades 
                             if t.emotional_state.value == filters['emotional_state']]
        
        return sorted(filtered_trades, key=lambda x: x.created_at, reverse=True)
    
    def search_trades(self, user_session: str, search_query: str) -> List[SmartTradeEntry]:
        """Recherche intelligente dans les trades"""
        
        user_trades = self.get_user_trades(user_session)
        search_query = search_query.lower()
        
        matching_trades = []
        
        for trade in user_trades:
            # Recherche dans les notes
            if search_query in trade.notes.lower():
                matching_trades.append(trade)
                continue
            
            # Recherche dans les tags
            if any(search_query in tag.lower() for tag in trade.tags):
                matching_trades.append(trade)
                continue
            
            # Recherche par paire
            if search_query in trade.pair_symbol.lower():
                matching_trades.append(trade)
                continue
            
            # Recherche par stratégie
            if trade.strategy and search_query in trade.strategy.value.lower():
                matching_trades.append(trade)
                continue
        
        return matching_trades
    
    def update_trade(self, trade_id: str, updates: Dict) -> bool:
        """Met à jour un trade existant"""
        
        if trade_id not in self.trades:
            return False
        
        trade = self.trades[trade_id]
        
        # Mise à jour des champs modifiables
        for field, value in updates.items():
            if hasattr(trade, field):
                if field == 'status':
                    setattr(trade, field, TradeStatus(value))
                elif field == 'strategy':
                    setattr(trade, field, TradeStrategy(value))
                elif field == 'emotional_state':
                    setattr(trade, field, EmotionalState(value))
                else:
                    setattr(trade, field, value)
        
        trade.updated_at = datetime.now()
        
        # Recalcul automatique du R/R si les prix changent
        if any(field in updates for field in ['exit_price', 'stop_loss', 'take_profit']):
            self._recalculate_metrics(trade)
        
        # Sauvegarde
        self._save_to_database(trade)
        
        return True
    
    def _recalculate_metrics(self, trade: SmartTradeEntry):
        """Recalcule les métriques après modification"""
        
        if trade.exit_price:
            # Calcul du profit/perte
            if trade.direction.upper() == 'BUY':
                trade.profit_loss_pips = (trade.exit_price - trade.entry_price) * 10000
            else:
                trade.profit_loss_pips = (trade.entry_price - trade.exit_price) * 10000
            
            # Simulation du profit en USD (à adapter selon le lot size)
            trade.profit_loss = trade.profit_loss_pips * trade.lot_size * 1.0  # Approximation
    
    def get_trading_insights(self, user_session: str) -> Dict:
        """Génère des insights intelligents sur le trading"""
        
        user_trades = self.get_user_trades(user_session)
        
        if len(user_trades) < 5:
            return {"message": "Pas assez de trades pour générer des insights"}
        
        insights = {}
        
        # Analyse des heures préférées
        hours = [t.entry_time.hour for t in user_trades]
        most_active_hour = max(set(hours), key=hours.count)
        insights['best_trading_hour'] = f"Vous tradez le plus à {most_active_hour}h"
        
        # Analyse des émotions vs performance
        emotional_performance = {}
        for trade in user_trades:
            if trade.profit_loss:
                emotion = trade.emotional_state.value
                if emotion not in emotional_performance:
                    emotional_performance[emotion] = []
                emotional_performance[emotion].append(trade.profit_loss)
        
        best_emotion = None
        best_avg = float('-inf')
        for emotion, profits in emotional_performance.items():
            avg_profit = sum(profits) / len(profits)
            if avg_profit > best_avg:
                best_avg = avg_profit
                best_emotion = emotion
        
        if best_emotion:
            insights['best_emotional_state'] = f"Vous performez mieux quand vous êtes {best_emotion}"
        
        # Analyse des paires
        pair_performance = {}
        for trade in user_trades:
            if trade.profit_loss:
                pair = trade.pair_symbol
                if pair not in pair_performance:
                    pair_performance[pair] = []
                pair_performance[pair].append(trade.profit_loss)
        
        best_pair = None
        best_pair_avg = float('-inf')
        for pair, profits in pair_performance.items():
            if len(profits) >= 3:  # Au moins 3 trades
                avg_profit = sum(profits) / len(profits)
                if avg_profit > best_pair_avg:
                    best_pair_avg = avg_profit
                    best_pair = pair
        
        if best_pair:
            insights['best_pair'] = f"Votre meilleure paire est {best_pair}"
        
        return insights
    
    def _save_to_database(self, trade: SmartTradeEntry):
        """Sauvegarde en base de données"""
        # En pratique, ceci sauvegarderait dans la vraie base de données
        # Pour l'instant, on garde en mémoire
        pass
    
    def import_from_mt4(self, user_session: str, mt4_data: Dict) -> List[str]:
        """Import automatique depuis MetaTrader 4"""
        imported_trades = []
        
        # Simulation d'import MT4
        for trade_data in mt4_data.get('trades', []):
            enriched_data = {
                'user_session': user_session,
                'pair_symbol': trade_data['symbol'],
                'direction': 'BUY' if trade_data['type'] == 0 else 'SELL',
                'lot_size': trade_data['lots'],
                'entry_price': trade_data['open_price'],
                'exit_price': trade_data.get('close_price'),
                'stop_loss': trade_data.get('sl', 0),
                'take_profit': trade_data.get('tp', 0),
                'entry_time': datetime.fromtimestamp(trade_data['open_time']),
                'exit_time': datetime.fromtimestamp(trade_data['close_time']) if trade_data.get('close_time') else None,
                'profit_loss': trade_data.get('profit'),
                'status': 'closed' if trade_data.get('close_time') else 'open',
                'imported_from': 'MT4',
                'import_timestamp': datetime.now(),
                'notes': f"Import automatique MT4 - Ticket #{trade_data.get('ticket', 'N/A')}"
            }
            
            trade_id = self.add_trade(enriched_data)
            imported_trades.append(trade_id)
        
        return imported_trades
    
    def export_to_csv(self, user_session: str, filters: Optional[Dict] = None) -> str:
        """Export des trades au format CSV"""
        trades = self.get_user_trades(user_session, filters)
        
        csv_content = "Trade_ID,Pair,Direction,Lot_Size,Entry_Price,Exit_Price,Stop_Loss,Take_Profit," \
                     "Entry_Time,Exit_Time,Profit_Loss,Profit_Loss_Pips,Status,Strategy,Emotional_State," \
                     "Confidence,Stress,Risk_Reward,Notes,Tags\n"
        
        for trade in trades:
            csv_content += f"{trade.trade_id},{trade.pair_symbol},{trade.direction},{trade.lot_size}," \
                          f"{trade.entry_price},{trade.exit_price or ''}," \
                          f"{trade.stop_loss},{trade.take_profit}," \
                          f"{trade.entry_time.isoformat()},{trade.exit_time.isoformat() if trade.exit_time else ''}," \
                          f"{trade.profit_loss or ''},{trade.profit_loss_pips or ''}," \
                          f"{trade.status.value},{trade.strategy.value if trade.strategy else ''}," \
                          f"{trade.emotional_state.value},{trade.confidence_level},{trade.stress_level}," \
                          f"{trade.risk_reward_ratio},\"{trade.notes}\",\"{';'.join(trade.tags)}\"\n"
        
        return csv_content

# Instance globale du journal intelligent
smart_journal = SmartJournalManager()