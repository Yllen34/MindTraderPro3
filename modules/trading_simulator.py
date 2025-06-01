"""
Simulateur de Trading - Backtesting et Paper Trading en temps réel
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math

class SimulationType(Enum):
    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    STRATEGY_TEST = "strategy_test"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class TimeFrame(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

@dataclass
class PriceData:
    """Données de prix OHLCV"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class SimulatedOrder:
    """Ordre simulé"""
    order_id: str
    symbol: str
    order_type: OrderType
    direction: str  # BUY/SELL
    quantity: float
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime]
    filled_price: Optional[float]

@dataclass
class SimulatedPosition:
    """Position simulée"""
    position_id: str
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime

@dataclass
class BacktestResult:
    """Résultats de backtest"""
    strategy_name: str
    symbol: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    
    # Métriques de performance
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Résultats financiers
    initial_balance: float
    final_balance: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    
    # Métriques avancées
    sharpe_ratio: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    # Données détaillées
    equity_curve: List[Tuple[datetime, float]]
    trade_list: List[Dict]

class TradingStrategy:
    """Stratégie de trading de base"""
    
    def __init__(self, name: str, parameters: Dict = None):
        self.name = name
        self.parameters = parameters or {}
        
    def should_buy(self, data: List[PriceData], current_index: int) -> bool:
        """Détermine si on doit acheter"""
        return False
        
    def should_sell(self, data: List[PriceData], current_index: int) -> bool:
        """Détermine si on doit vendre"""
        return False
        
    def calculate_position_size(self, balance: float, risk_percent: float) -> float:
        """Calcule la taille de position"""
        return balance * (risk_percent / 100)

class MovingAverageCrossStrategy(TradingStrategy):
    """Stratégie de croisement de moyennes mobiles"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        super().__init__("MA Cross", {
            "fast_period": fast_period,
            "slow_period": slow_period
        })
        
    def _calculate_sma(self, data: List[PriceData], period: int, end_index: int) -> float:
        """Calcule la moyenne mobile simple"""
        if end_index < period - 1:
            return 0
        
        prices = [data[i].close for i in range(end_index - period + 1, end_index + 1)]
        return sum(prices) / len(prices)
        
    def should_buy(self, data: List[PriceData], current_index: int) -> bool:
        """Signal d'achat : MA rapide croise au-dessus MA lente"""
        if current_index < self.parameters["slow_period"]:
            return False
            
        fast_ma_current = self._calculate_sma(data, self.parameters["fast_period"], current_index)
        slow_ma_current = self._calculate_sma(data, self.parameters["slow_period"], current_index)
        
        fast_ma_previous = self._calculate_sma(data, self.parameters["fast_period"], current_index - 1)
        slow_ma_previous = self._calculate_sma(data, self.parameters["slow_period"], current_index - 1)
        
        return (fast_ma_current > slow_ma_current and 
                fast_ma_previous <= slow_ma_previous)
                
    def should_sell(self, data: List[PriceData], current_index: int) -> bool:
        """Signal de vente : MA rapide croise en-dessous MA lente"""
        if current_index < self.parameters["slow_period"]:
            return False
            
        fast_ma_current = self._calculate_sma(data, self.parameters["fast_period"], current_index)
        slow_ma_current = self._calculate_sma(data, self.parameters["slow_period"], current_index)
        
        fast_ma_previous = self._calculate_sma(data, self.parameters["fast_period"], current_index - 1)
        slow_ma_previous = self._calculate_sma(data, self.parameters["slow_period"], current_index - 1)
        
        return (fast_ma_current < slow_ma_current and 
                fast_ma_previous >= slow_ma_previous)

class RSIStrategy(TradingStrategy):
    """Stratégie basée sur le RSI"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI Strategy", {
            "period": period,
            "oversold": oversold,
            "overbought": overbought
        })
        
    def _calculate_rsi(self, data: List[PriceData], period: int, end_index: int) -> float:
        """Calcule le RSI"""
        if end_index < period:
            return 50
            
        gains = []
        losses = []
        
        for i in range(end_index - period + 1, end_index + 1):
            if i > 0:
                change = data[i].close - data[i-1].close
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def should_buy(self, data: List[PriceData], current_index: int) -> bool:
        """Signal d'achat : RSI sort de la zone de survente"""
        rsi_current = self._calculate_rsi(data, self.parameters["period"], current_index)
        rsi_previous = self._calculate_rsi(data, self.parameters["period"], current_index - 1)
        
        return (rsi_previous <= self.parameters["oversold"] and 
                rsi_current > self.parameters["oversold"])
                
    def should_sell(self, data: List[PriceData], current_index: int) -> bool:
        """Signal de vente : RSI entre en zone de surachat"""
        rsi_current = self._calculate_rsi(data, self.parameters["period"], current_index)
        
        return rsi_current >= self.parameters["overbought"]

class BreakoutStrategy(TradingStrategy):
    """Stratégie de cassure"""
    
    def __init__(self, lookback_period: int = 20, min_breakout_percent: float = 0.5):
        super().__init__("Breakout Strategy", {
            "lookback_period": lookback_period,
            "min_breakout_percent": min_breakout_percent
        })
        
    def should_buy(self, data: List[PriceData], current_index: int) -> bool:
        """Signal d'achat : cassure de résistance"""
        if current_index < self.parameters["lookback_period"]:
            return False
            
        # Trouver le plus haut des X dernières bougies
        lookback_highs = [data[i].high for i in range(
            current_index - self.parameters["lookback_period"], current_index)]
        resistance = max(lookback_highs)
        
        current_price = data[current_index].close
        breakout_threshold = resistance * (1 + self.parameters["min_breakout_percent"] / 100)
        
        return current_price > breakout_threshold
        
    def should_sell(self, data: List[PriceData], current_index: int) -> bool:
        """Signal de vente : cassure de support"""
        if current_index < self.parameters["lookback_period"]:
            return False
            
        # Trouver le plus bas des X dernières bougies
        lookback_lows = [data[i].low for i in range(
            current_index - self.parameters["lookback_period"], current_index)]
        support = min(lookback_lows)
        
        current_price = data[current_index].close
        breakout_threshold = support * (1 - self.parameters["min_breakout_percent"] / 100)
        
        return current_price < breakout_threshold

class TradingSimulator:
    """Simulateur de trading principal"""
    
    def __init__(self):
        self.simulations = {}  # user_session -> List[simulation_data]
        self.paper_accounts = {}  # user_session -> account_data
        self.strategies = {
            "ma_cross": MovingAverageCrossStrategy,
            "rsi": RSIStrategy,
            "breakout": BreakoutStrategy
        }
        
    def create_paper_account(self, user_session: str, initial_balance: float = 10000) -> Dict:
        """Crée un compte de paper trading"""
        
        account = {
            'user_session': user_session,
            'balance': initial_balance,
            'equity': initial_balance,
            'margin_used': 0,
            'free_margin': initial_balance,
            'positions': {},
            'orders': {},
            'trade_history': [],
            'created_at': datetime.now(),
            'last_update': datetime.now()
        }
        
        self.paper_accounts[user_session] = account
        
        return {
            'success': True,
            'account_id': user_session,
            'initial_balance': initial_balance,
            'message': 'Compte de paper trading créé'
        }
    
    def place_paper_order(self, user_session: str, order_data: Dict) -> Dict:
        """Place un ordre en paper trading"""
        
        if user_session not in self.paper_accounts:
            self.create_paper_account(user_session)
        
        account = self.paper_accounts[user_session]
        
        order_id = f"order_{int(datetime.now().timestamp())}_{order_data['symbol']}"
        
        order = SimulatedOrder(
            order_id=order_id,
            symbol=order_data['symbol'],
            order_type=OrderType(order_data.get('order_type', 'market')),
            direction=order_data['direction'],
            quantity=order_data['quantity'],
            price=order_data.get('price'),
            stop_loss=order_data.get('stop_loss'),
            take_profit=order_data.get('take_profit'),
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            filled_at=None,
            filled_price=None
        )
        
        # Simulation d'exécution immédiate pour ordre market
        if order.order_type == OrderType.MARKET:
            current_price = self._get_current_price(order.symbol)
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            order.filled_price = current_price
            
            # Créer la position
            self._create_position(account, order)
        
        account['orders'][order_id] = order
        account['last_update'] = datetime.now()
        
        return {
            'success': True,
            'order_id': order_id,
            'status': order.status.value,
            'filled_price': order.filled_price
        }
    
    def _create_position(self, account: Dict, order: SimulatedOrder):
        """Crée une position à partir d'un ordre"""
        
        position_id = f"pos_{order.order_id}"
        
        position = SimulatedPosition(
            position_id=position_id,
            symbol=order.symbol,
            direction=order.direction,
            quantity=order.quantity,
            entry_price=order.filled_price,
            current_price=order.filled_price,
            unrealized_pnl=0,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            opened_at=order.filled_at
        )
        
        account['positions'][position_id] = position
    
    def _get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel (simulation)"""
        # Prix simulés - en production, récupérer les vrais prix
        base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'XAUUSD': 2000.00,
            'BTCUSD': 45000.00
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        # Ajouter une variation aléatoire de ±0.1%
        variation = random.uniform(-0.001, 0.001)
        return base_price * (1 + variation)
    
    def generate_historical_data(self, symbol: str, timeframe: TimeFrame, 
                               days: int = 365) -> List[PriceData]:
        """Génère des données historiques simulées"""
        
        data = []
        base_price = self._get_current_price(symbol)
        current_time = datetime.now() - timedelta(days=days)
        
        # Calcul de l'intervalle selon le timeframe
        interval_minutes = {
            TimeFrame.M1: 1,
            TimeFrame.M5: 5,
            TimeFrame.M15: 15,
            TimeFrame.M30: 30,
            TimeFrame.H1: 60,
            TimeFrame.H4: 240,
            TimeFrame.D1: 1440
        }
        
        interval = interval_minutes[timeframe]
        total_bars = (days * 24 * 60) // interval
        
        price = base_price
        
        for i in range(total_bars):
            # Simulation de mouvement de prix réaliste
            volatility = 0.002  # 0.2% de volatilité par barre
            
            # Tendance légère (drift)
            drift = random.uniform(-0.0001, 0.0001)
            
            # Mouvement aléatoire
            random_move = random.gauss(0, volatility)
            
            # Nouveau prix
            new_price = price * (1 + drift + random_move)
            
            # Génération OHLC réaliste
            high_low_range = abs(new_price - price) * random.uniform(1.5, 3.0)
            
            if new_price > price:  # Mouvement haussier
                open_price = price
                close_price = new_price
                high_price = close_price + random.uniform(0, high_low_range * 0.3)
                low_price = open_price - random.uniform(0, high_low_range * 0.2)
            else:  # Mouvement baissier
                open_price = price
                close_price = new_price
                high_price = open_price + random.uniform(0, high_low_range * 0.2)
                low_price = close_price - random.uniform(0, high_low_range * 0.3)
            
            # Volume simulé
            volume = random.uniform(1000, 10000)
            
            data.append(PriceData(
                timestamp=current_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            ))
            
            price = close_price
            current_time += timedelta(minutes=interval)
        
        return data
    
    def run_backtest(self, user_session: str, backtest_config: Dict) -> BacktestResult:
        """Exécute un backtest"""
        
        # Configuration
        symbol = backtest_config['symbol']
        strategy_name = backtest_config['strategy']
        timeframe = TimeFrame(backtest_config['timeframe'])
        start_date = datetime.fromisoformat(backtest_config['start_date'])
        end_date = datetime.fromisoformat(backtest_config['end_date'])
        initial_balance = backtest_config.get('initial_balance', 10000)
        risk_per_trade = backtest_config.get('risk_per_trade', 2.0)
        
        # Créer la stratégie
        strategy_params = backtest_config.get('strategy_params', {})
        strategy = self._create_strategy(strategy_name, strategy_params)
        
        # Générer les données historiques
        days = (end_date - start_date).days
        historical_data = self.generate_historical_data(symbol, timeframe, days)
        
        # Variables de simulation
        balance = initial_balance
        equity_curve = [(start_date, balance)]
        trade_list = []
        positions = []
        
        max_balance = balance
        max_drawdown = 0
        
        # Simulation bar par bar
        for i, current_bar in enumerate(historical_data):
            if current_bar.timestamp < start_date:
                continue
            if current_bar.timestamp > end_date:
                break
            
            # Vérifier les signaux de la stratégie
            if not positions:  # Pas de position ouverte
                if strategy.should_buy(historical_data, i):
                    # Ouvrir position LONG
                    position_size = strategy.calculate_position_size(balance, risk_per_trade)
                    quantity = position_size / current_bar.close
                    
                    position = {
                        'type': 'LONG',
                        'entry_price': current_bar.close,
                        'entry_time': current_bar.timestamp,
                        'quantity': quantity,
                        'position_value': position_size
                    }
                    positions.append(position)
                    
                elif strategy.should_sell(historical_data, i):
                    # Ouvrir position SHORT
                    position_size = strategy.calculate_position_size(balance, risk_per_trade)
                    quantity = position_size / current_bar.close
                    
                    position = {
                        'type': 'SHORT',
                        'entry_price': current_bar.close,
                        'entry_time': current_bar.timestamp,
                        'quantity': quantity,
                        'position_value': position_size
                    }
                    positions.append(position)
            
            else:  # Position ouverte - vérifier signaux de sortie
                position = positions[0]
                should_close = False
                close_reason = ""
                
                if position['type'] == 'LONG' and strategy.should_sell(historical_data, i):
                    should_close = True
                    close_reason = "Signal de vente"
                elif position['type'] == 'SHORT' and strategy.should_buy(historical_data, i):
                    should_close = True
                    close_reason = "Signal d'achat"
                
                if should_close:
                    # Fermer la position
                    exit_price = current_bar.close
                    
                    if position['type'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * position['quantity']
                    else:  # SHORT
                        pnl = (position['entry_price'] - exit_price) * position['quantity']
                    
                    balance += pnl
                    
                    # Enregistrer le trade
                    trade = {
                        'symbol': symbol,
                        'direction': position['type'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'entry_time': position['entry_time'],
                        'exit_time': current_bar.timestamp,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'return_percent': (pnl / position['position_value']) * 100,
                        'close_reason': close_reason
                    }
                    trade_list.append(trade)
                    
                    positions.clear()
            
            # Mettre à jour l'equity curve
            current_equity = balance
            if positions:  # Ajouter P&L non réalisé
                position = positions[0]
                if position['type'] == 'LONG':
                    unrealized_pnl = (current_bar.close - position['entry_price']) * position['quantity']
                else:
                    unrealized_pnl = (position['entry_price'] - current_bar.close) * position['quantity']
                current_equity += unrealized_pnl
            
            equity_curve.append((current_bar.timestamp, current_equity))
            
            # Calculer drawdown
            if current_equity > max_balance:
                max_balance = current_equity
            else:
                drawdown = max_balance - current_equity
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # Calculer les métriques
        winning_trades = len([t for t in trade_list if t['pnl'] > 0])
        losing_trades = len([t for t in trade_list if t['pnl'] <= 0])
        total_trades = len(trade_list)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_return = balance - initial_balance
        total_return_percent = (total_return / initial_balance * 100) if initial_balance > 0 else 0
        
        max_drawdown_percent = (max_drawdown / max_balance * 100) if max_balance > 0 else 0
        
        # Métriques avancées
        wins = [t['pnl'] for t in trade_list if t['pnl'] > 0]
        losses = [abs(t['pnl']) for t in trade_list if t['pnl'] <= 0]
        
        average_win = sum(wins) / len(wins) if wins else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = max(losses) if losses else 0
        
        profit_factor = sum(wins) / sum(losses) if losses and sum(losses) > 0 else 0
        
        # Sharpe ratio simplifié
        returns = [t['return_percent'] for t in trade_list]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            return_std = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1))
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        result = BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            initial_balance=initial_balance,
            final_balance=balance,
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            equity_curve=equity_curve,
            trade_list=trade_list
        )
        
        # Sauvegarder le résultat
        if user_session not in self.simulations:
            self.simulations[user_session] = []
        
        self.simulations[user_session].append({
            'type': 'backtest',
            'result': result,
            'created_at': datetime.now()
        })
        
        return result
    
    def _create_strategy(self, strategy_name: str, params: Dict) -> TradingStrategy:
        """Crée une instance de stratégie"""
        
        if strategy_name == "ma_cross":
            return MovingAverageCrossStrategy(
                fast_period=params.get('fast_period', 10),
                slow_period=params.get('slow_period', 20)
            )
        elif strategy_name == "rsi":
            return RSIStrategy(
                period=params.get('period', 14),
                oversold=params.get('oversold', 30),
                overbought=params.get('overbought', 70)
            )
        elif strategy_name == "breakout":
            return BreakoutStrategy(
                lookback_period=params.get('lookback_period', 20),
                min_breakout_percent=params.get('min_breakout_percent', 0.5)
            )
        else:
            return MovingAverageCrossStrategy()
    
    def get_user_simulations(self, user_session: str) -> List[Dict]:
        """Récupère les simulations d'un utilisateur"""
        return self.simulations.get(user_session, [])
    
    def get_paper_account(self, user_session: str) -> Dict:
        """Récupère le compte de paper trading"""
        account = self.paper_accounts.get(user_session)
        if not account:
            return {'error': 'Compte de paper trading non trouvé'}
        
        # Mettre à jour les positions avec les prix actuels
        self._update_paper_positions(account)
        
        return {
            'balance': account['balance'],
            'equity': account['equity'],
            'margin_used': account['margin_used'],
            'free_margin': account['free_margin'],
            'unrealized_pnl': account['equity'] - account['balance'],
            'positions': list(account['positions'].values()),
            'open_orders': [o for o in account['orders'].values() if o.status == OrderStatus.PENDING],
            'trade_count': len(account['trade_history'])
        }
    
    def _update_paper_positions(self, account: Dict):
        """Met à jour les positions avec les prix actuels"""
        total_unrealized = 0
        
        for position in account['positions'].values():
            current_price = self._get_current_price(position.symbol)
            position.current_price = current_price
            
            if position.direction == 'BUY':
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:
                position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
            
            total_unrealized += position.unrealized_pnl
        
        account['equity'] = account['balance'] + total_unrealized
        account['last_update'] = datetime.now()
    
    def get_available_strategies(self) -> List[Dict]:
        """Retourne la liste des stratégies disponibles"""
        return [
            {
                'id': 'ma_cross',
                'name': 'Croisement de Moyennes Mobiles',
                'description': 'Stratégie basée sur le croisement de deux moyennes mobiles',
                'parameters': [
                    {'name': 'fast_period', 'type': 'number', 'default': 10, 'description': 'Période MA rapide'},
                    {'name': 'slow_period', 'type': 'number', 'default': 20, 'description': 'Période MA lente'}
                ]
            },
            {
                'id': 'rsi',
                'name': 'RSI (Relative Strength Index)',
                'description': 'Stratégie basée sur les zones de surachat/survente du RSI',
                'parameters': [
                    {'name': 'period', 'type': 'number', 'default': 14, 'description': 'Période RSI'},
                    {'name': 'oversold', 'type': 'number', 'default': 30, 'description': 'Seuil de survente'},
                    {'name': 'overbought', 'type': 'number', 'default': 70, 'description': 'Seuil de surachat'}
                ]
            },
            {
                'id': 'breakout',
                'name': 'Stratégie de Cassure',
                'description': 'Détecte les cassures de supports et résistances',
                'parameters': [
                    {'name': 'lookback_period', 'type': 'number', 'default': 20, 'description': 'Période de recherche'},
                    {'name': 'min_breakout_percent', 'type': 'number', 'default': 0.5, 'description': 'Seuil de cassure (%)'}
                ]
            }
        ]

# Instance globale du simulateur
trading_simulator = TradingSimulator()