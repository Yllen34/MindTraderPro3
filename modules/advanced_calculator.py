"""
Calculateur de Position Avancé - Multi-actifs avec historique et paramètres flexibles
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from enum import Enum
import json

class AssetType(Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    INDICES = "indices"
    COMMODITIES = "commodities"
    METALS = "metals"

class CalculationType(Enum):
    POSITION_SIZE = "position_size"
    RISK_REWARD = "risk_reward"
    PROFIT_LOSS = "profit_loss"
    MARGIN = "margin"
    COMPOUND = "compound"

@dataclass
class AssetSpecification:
    """Spécifications d'un actif"""
    symbol: str
    asset_type: AssetType
    pip_size: float
    pip_value_base: float  # Valeur pip pour 1 lot standard
    min_lot_size: float
    max_lot_size: float
    lot_step: float
    margin_requirement: float  # Pourcentage de marge requis
    spread_typical: float  # Spread typique en pips
    trading_hours: str
    currency_base: str
    currency_quote: str

@dataclass
class CalculationInput:
    """Paramètres d'entrée pour un calcul"""
    calculation_id: str
    user_session: str
    calculation_type: CalculationType
    asset_symbol: str
    timestamp: datetime
    
    # Paramètres financiers
    account_capital: float
    risk_percentage: float
    risk_amount_usd: Optional[float]
    
    # Prix et niveaux
    entry_price: float
    stop_loss: float
    take_profit: Optional[float]
    current_price: Optional[float]
    
    # Gestion avancée
    leverage: float
    commission_rate: float  # % ou fixe
    swap_rate: Optional[float]
    
    # Métadonnées
    strategy: Optional[str]
    notes: Optional[str]
    tags: List[str]

@dataclass
class CalculationResult:
    """Résultat d'un calcul de position"""
    calculation_id: str
    success: bool
    
    # Résultats principaux
    recommended_lot_size: float
    position_value_usd: float
    margin_required: float
    risk_amount: float
    potential_profit: float
    risk_reward_ratio: float
    
    # Détails avancés
    pip_value: float
    stop_loss_pips: float
    take_profit_pips: Optional[float]
    spread_cost: float
    commission_cost: float
    
    # Analyse
    risk_level: str  # low, medium, high, extreme
    recommendations: List[str]
    warnings: List[str]
    
    # Performance si prix de sortie fourni
    actual_profit_loss: Optional[float]
    actual_pips: Optional[float]
    
    # Métadonnées
    calculation_time: datetime
    asset_type: AssetType

class AdvancedPositionCalculator:
    """Calculateur de position avancé multi-actifs"""
    
    def __init__(self):
        self.asset_specs = self._initialize_asset_specifications()
        self.calculation_history = {}  # user_session -> List[CalculationResult]
        self.user_preferences = {}  # user_session -> Dict
        
    def _initialize_asset_specifications(self) -> Dict[str, AssetSpecification]:
        """Initialise les spécifications des actifs"""
        
        specs = {}
        
        # FOREX MAJORS
        specs["EURUSD"] = AssetSpecification(
            symbol="EURUSD",
            asset_type=AssetType.FOREX,
            pip_size=0.0001,
            pip_value_base=10.0,  # $10 per pip pour 1 lot standard
            min_lot_size=0.01,
            max_lot_size=100.0,
            lot_step=0.01,
            margin_requirement=3.33,  # 30:1 leverage = 3.33%
            spread_typical=1.2,
            trading_hours="24h (fermé weekend)",
            currency_base="EUR",
            currency_quote="USD"
        )
        
        specs["GBPUSD"] = AssetSpecification(
            symbol="GBPUSD",
            asset_type=AssetType.FOREX,
            pip_size=0.0001,
            pip_value_base=10.0,
            min_lot_size=0.01,
            max_lot_size=100.0,
            lot_step=0.01,
            margin_requirement=3.33,
            spread_typical=1.5,
            trading_hours="24h (fermé weekend)",
            currency_base="GBP",
            currency_quote="USD"
        )
        
        specs["USDJPY"] = AssetSpecification(
            symbol="USDJPY",
            asset_type=AssetType.FOREX,
            pip_size=0.01,  # JPY pairs
            pip_value_base=9.1,  # Variable selon le taux USD/JPY
            min_lot_size=0.01,
            max_lot_size=100.0,
            lot_step=0.01,
            margin_requirement=3.33,
            spread_typical=1.1,
            trading_hours="24h (fermé weekend)",
            currency_base="USD",
            currency_quote="JPY"
        )
        
        # MÉTAUX PRÉCIEUX
        specs["XAUUSD"] = AssetSpecification(
            symbol="XAUUSD",
            asset_type=AssetType.METALS,
            pip_size=0.1,  # 0.1 USD par once
            pip_value_base=10.0,  # $10 per pip pour 1 lot (100 oz)
            min_lot_size=0.01,
            max_lot_size=50.0,
            lot_step=0.01,
            margin_requirement=2.0,  # 50:1 leverage
            spread_typical=3.5,
            trading_hours="23h/24 (fermé 1h)",
            currency_base="XAU",
            currency_quote="USD"
        )
        
        specs["XAGUSD"] = AssetSpecification(
            symbol="XAGUSD",
            asset_type=AssetType.METALS,
            pip_size=0.001,
            pip_value_base=50.0,  # $50 per pip pour 1 lot (5000 oz)
            min_lot_size=0.01,
            max_lot_size=30.0,
            lot_step=0.01,
            margin_requirement=2.5,
            spread_typical=4.0,
            trading_hours="23h/24 (fermé 1h)",
            currency_base="XAG",
            currency_quote="USD"
        )
        
        # CRYPTO-MONNAIES
        specs["BTCUSD"] = AssetSpecification(
            symbol="BTCUSD",
            asset_type=AssetType.CRYPTO,
            pip_size=1.0,  # $1 per point
            pip_value_base=1.0,
            min_lot_size=0.001,
            max_lot_size=10.0,
            lot_step=0.001,
            margin_requirement=10.0,  # 10:1 leverage
            spread_typical=50.0,
            trading_hours="24h/7",
            currency_base="BTC",
            currency_quote="USD"
        )
        
        specs["ETHUSD"] = AssetSpecification(
            symbol="ETHUSD",
            asset_type=AssetType.CRYPTO,
            pip_size=0.1,
            pip_value_base=0.1,
            min_lot_size=0.01,
            max_lot_size=50.0,
            lot_step=0.01,
            margin_requirement=10.0,
            spread_typical=3.0,
            trading_hours="24h/7",
            currency_base="ETH",
            currency_quote="USD"
        )
        
        # INDICES
        specs["SPX500"] = AssetSpecification(
            symbol="SPX500",
            asset_type=AssetType.INDICES,
            pip_size=0.1,  # 0.1 point
            pip_value_base=1.0,  # $1 per 0.1 point
            min_lot_size=0.1,
            max_lot_size=100.0,
            lot_step=0.1,
            margin_requirement=5.0,  # 20:1 leverage
            spread_typical=0.7,
            trading_hours="Lun-Ven 9h30-16h",
            currency_base="USD",
            currency_quote="USD"
        )
        
        # MATIÈRES PREMIÈRES
        specs["USOIL"] = AssetSpecification(
            symbol="USOIL",
            asset_type=AssetType.COMMODITIES,
            pip_size=0.01,  # $0.01 per barrel
            pip_value_base=10.0,  # $10 per pip pour 1000 barrels
            min_lot_size=0.01,
            max_lot_size=20.0,
            lot_step=0.01,
            margin_requirement=3.33,
            spread_typical=3.0,
            trading_hours="Lun-Ven 23h-22h",
            currency_base="USD",
            currency_quote="USD"
        )
        
        return specs
    
    def calculate_position(self, calc_input: CalculationInput) -> CalculationResult:
        """Calcule la taille de position optimale"""
        
        try:
            # Vérification de l'actif
            if calc_input.asset_symbol not in self.asset_specs:
                return self._create_error_result(calc_input.calculation_id, "Actif non supporté")
            
            asset_spec = self.asset_specs[calc_input.asset_symbol]
            
            # Calcul du risque en USD
            if calc_input.risk_amount_usd:
                risk_usd = calc_input.risk_amount_usd
            else:
                risk_usd = calc_input.account_capital * (calc_input.risk_percentage / 100)
            
            # Calcul des pips de stop loss
            if calc_input.stop_loss == 0:
                return self._create_error_result(calc_input.calculation_id, "Stop loss requis")
            
            if asset_spec.symbol.endswith("JPY"):
                stop_loss_pips = abs(calc_input.entry_price - calc_input.stop_loss) / asset_spec.pip_size
            else:
                stop_loss_pips = abs(calc_input.entry_price - calc_input.stop_loss) / asset_spec.pip_size
            
            if stop_loss_pips == 0:
                return self._create_error_result(calc_input.calculation_id, "Distance de stop loss invalide")
            
            # Calcul de la valeur du pip ajustée
            pip_value = self._calculate_pip_value(asset_spec, calc_input.entry_price)
            
            # Calcul de la taille de position recommandée
            recommended_lot_size = risk_usd / (stop_loss_pips * pip_value)
            
            # Ajustement selon les contraintes de l'actif
            recommended_lot_size = max(asset_spec.min_lot_size, 
                                     min(asset_spec.max_lot_size, recommended_lot_size))
            
            # Arrondir selon le step
            recommended_lot_size = round(recommended_lot_size / asset_spec.lot_step) * asset_spec.lot_step
            
            # Calculs financiers
            position_value = recommended_lot_size * calc_input.entry_price * self._get_contract_size(asset_spec)
            margin_required = position_value * (asset_spec.margin_requirement / 100)
            
            # Calcul du take profit si fourni
            take_profit_pips = None
            potential_profit = 0
            risk_reward_ratio = 0
            
            if calc_input.take_profit:
                if asset_spec.symbol.endswith("JPY"):
                    take_profit_pips = abs(calc_input.take_profit - calc_input.entry_price) / asset_spec.pip_size
                else:
                    take_profit_pips = abs(calc_input.take_profit - calc_input.entry_price) / asset_spec.pip_size
                
                potential_profit = take_profit_pips * pip_value * recommended_lot_size
                risk_reward_ratio = potential_profit / risk_usd if risk_usd > 0 else 0
            
            # Calcul des coûts
            spread_cost = asset_spec.spread_typical * pip_value * recommended_lot_size
            commission_cost = self._calculate_commission(asset_spec, recommended_lot_size, calc_input.commission_rate)
            
            # Analyse du niveau de risque
            risk_percentage_actual = (risk_usd / calc_input.account_capital) * 100
            risk_level = self._determine_risk_level(risk_percentage_actual, margin_required, calc_input.account_capital)
            
            # Génération des recommandations et avertissements
            recommendations, warnings = self._generate_recommendations(
                calc_input, asset_spec, recommended_lot_size, risk_percentage_actual, 
                margin_required, risk_reward_ratio
            )
            
            # Calcul de performance si prix de sortie fourni
            actual_profit_loss = None
            actual_pips = None
            if calc_input.current_price:
                if asset_spec.symbol.endswith("JPY"):
                    actual_pips = (calc_input.current_price - calc_input.entry_price) / asset_spec.pip_size
                else:
                    actual_pips = (calc_input.current_price - calc_input.entry_price) / asset_spec.pip_size
                
                # Ajuster selon la direction du trade
                direction = 1 if calc_input.entry_price < calc_input.stop_loss else -1
                actual_pips *= direction
                actual_profit_loss = actual_pips * pip_value * recommended_lot_size
            
            result = CalculationResult(
                calculation_id=calc_input.calculation_id,
                success=True,
                recommended_lot_size=round(recommended_lot_size, 3),
                position_value_usd=round(position_value, 2),
                margin_required=round(margin_required, 2),
                risk_amount=round(risk_usd, 2),
                potential_profit=round(potential_profit, 2),
                risk_reward_ratio=round(risk_reward_ratio, 2),
                pip_value=round(pip_value, 2),
                stop_loss_pips=round(stop_loss_pips, 1),
                take_profit_pips=round(take_profit_pips, 1) if take_profit_pips else None,
                spread_cost=round(spread_cost, 2),
                commission_cost=round(commission_cost, 2),
                risk_level=risk_level,
                recommendations=recommendations,
                warnings=warnings,
                actual_profit_loss=round(actual_profit_loss, 2) if actual_profit_loss else None,
                actual_pips=round(actual_pips, 1) if actual_pips else None,
                calculation_time=datetime.now(),
                asset_type=asset_spec.asset_type
            )
            
            # Sauvegarde dans l'historique
            self._save_to_history(calc_input.user_session, result)
            
            return result
            
        except Exception as e:
            return self._create_error_result(calc_input.calculation_id, f"Erreur de calcul: {str(e)}")
    
    def _calculate_pip_value(self, asset_spec: AssetSpecification, entry_price: float) -> float:
        """Calcule la valeur du pip selon l'actif"""
        
        base_pip_value = asset_spec.pip_value_base
        
        # Ajustement pour les paires JPY
        if asset_spec.symbol.endswith("JPY"):
            # La valeur du pip dépend du taux USD/JPY actuel
            base_pip_value = base_pip_value * (100 / entry_price)
        
        return base_pip_value
    
    def _get_contract_size(self, asset_spec: AssetSpecification) -> float:
        """Retourne la taille du contrat pour l'actif"""
        
        if asset_spec.asset_type == AssetType.FOREX:
            return 100000  # 1 lot standard = 100,000 unités
        elif asset_spec.asset_type == AssetType.METALS:
            if asset_spec.symbol == "XAUUSD":
                return 100  # 100 onces d'or
            elif asset_spec.symbol == "XAGUSD":
                return 5000  # 5000 onces d'argent
        elif asset_spec.asset_type == AssetType.CRYPTO:
            return 1  # 1 unité de crypto
        elif asset_spec.asset_type == AssetType.INDICES:
            return 1  # 1 point d'indice
        elif asset_spec.asset_type == AssetType.COMMODITIES:
            return 1000  # 1000 barils pour pétrole
        
        return 100000  # Défaut
    
    def _calculate_commission(self, asset_spec: AssetSpecification, lot_size: float, commission_rate: float) -> float:
        """Calcule la commission pour le trade"""
        
        if commission_rate == 0:
            return 0
        
        if asset_spec.asset_type == AssetType.FOREX:
            # Commission par lot round-trip (ouverture + fermeture)
            return lot_size * commission_rate * 2
        elif asset_spec.asset_type == AssetType.CRYPTO:
            # Commission en pourcentage du volume
            position_value = lot_size * 1000  # Estimation
            return position_value * (commission_rate / 100)
        else:
            # Commission fixe par trade
            return commission_rate
    
    def _determine_risk_level(self, risk_percentage: float, margin_required: float, account_capital: float) -> str:
        """Détermine le niveau de risque du trade"""
        
        margin_percentage = (margin_required / account_capital) * 100
        
        if risk_percentage > 5 or margin_percentage > 50:
            return "extreme"
        elif risk_percentage > 3 or margin_percentage > 30:
            return "high"
        elif risk_percentage > 1.5 or margin_percentage > 15:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, calc_input: CalculationInput, asset_spec: AssetSpecification, 
                                lot_size: float, risk_percentage: float, margin_required: float, 
                                risk_reward_ratio: float) -> tuple:
        """Génère des recommandations et avertissements personnalisés"""
        
        recommendations = []
        warnings = []
        
        # Analyse du risque
        if risk_percentage > 3:
            warnings.append(f"Risque élevé: {risk_percentage:.1f}% du capital - Réduisez la taille de position")
        elif risk_percentage < 0.5:
            recommendations.append("Risque très conservateur - Vous pourriez augmenter légèrement la position")
        else:
            recommendations.append(f"Risque optimal: {risk_percentage:.1f}% du capital")
        
        # Analyse du ratio Risk/Reward
        if risk_reward_ratio < 1.5:
            warnings.append(f"Ratio R/R faible: {risk_reward_ratio:.1f} - Recherchez un meilleur ratio (>2:1)")
        elif risk_reward_ratio >= 3:
            recommendations.append(f"Excellent ratio R/R: {risk_reward_ratio:.1f}:1")
        
        # Analyse de la marge
        margin_percentage = (margin_required / calc_input.account_capital) * 100
        if margin_percentage > 30:
            warnings.append(f"Marge importante: {margin_percentage:.1f}% du capital - Risque de margin call")
        
        # Recommandations spécifiques à l'actif
        if asset_spec.asset_type == AssetType.CRYPTO:
            recommendations.append("Crypto: Forte volatilité - Surveillez les news et la volatilité")
        elif asset_spec.asset_type == AssetType.METALS:
            recommendations.append("Métaux précieux: Considérez les données économiques US et l'inflation")
        elif asset_spec.symbol.endswith("JPY"):
            recommendations.append("Paire JPY: Surveillez les annonces de la Banque du Japon")
        
        # Analyse des heures de trading
        current_hour = datetime.now().hour
        if asset_spec.asset_type == AssetType.FOREX and (current_hour < 7 or current_hour > 17):
            recommendations.append("Trading hors heures principales - Liquidité réduite possible")
        
        # Recommandations de lot size
        if lot_size == asset_spec.min_lot_size:
            recommendations.append("Taille minimum atteinte - Capital limité ou stop loss trop serré")
        elif lot_size == asset_spec.max_lot_size:
            warnings.append("Taille maximum atteinte - Risque très élevé")
        
        return recommendations, warnings
    
    def _create_error_result(self, calculation_id: str, error_message: str) -> CalculationResult:
        """Crée un résultat d'erreur"""
        return CalculationResult(
            calculation_id=calculation_id,
            success=False,
            recommended_lot_size=0,
            position_value_usd=0,
            margin_required=0,
            risk_amount=0,
            potential_profit=0,
            risk_reward_ratio=0,
            pip_value=0,
            stop_loss_pips=0,
            take_profit_pips=None,
            spread_cost=0,
            commission_cost=0,
            risk_level="unknown",
            recommendations=[],
            warnings=[error_message],
            actual_profit_loss=None,
            actual_pips=None,
            calculation_time=datetime.now(),
            asset_type=AssetType.FOREX
        )
    
    def _save_to_history(self, user_session: str, result: CalculationResult):
        """Sauvegarde le résultat dans l'historique"""
        if user_session not in self.calculation_history:
            self.calculation_history[user_session] = []
        
        self.calculation_history[user_session].append(result)
        
        # Limiter l'historique à 100 calculs par utilisateur
        if len(self.calculation_history[user_session]) > 100:
            self.calculation_history[user_session] = self.calculation_history[user_session][-100:]
    
    def get_calculation_history(self, user_session: str, days: int = 30) -> List[CalculationResult]:
        """Récupère l'historique des calculs"""
        if user_session not in self.calculation_history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [
            calc for calc in self.calculation_history[user_session]
            if calc.calculation_time > cutoff
        ]
    
    def get_user_stats(self, user_session: str) -> Dict:
        """Statistiques d'utilisation utilisateur"""
        history = self.get_calculation_history(user_session)
        
        if not history:
            return {"message": "Aucun calcul dans l'historique"}
        
        # Analyse des actifs les plus calculés
        asset_counts = {}
        risk_levels = {"low": 0, "medium": 0, "high": 0, "extreme": 0}
        total_risk = 0
        
        for calc in history:
            # Comptage des actifs
            asset_counts[calc.calculation_id.split('_')[0]] = asset_counts.get(calc.calculation_id.split('_')[0], 0) + 1
            
            # Comptage des niveaux de risque
            risk_levels[calc.risk_level] += 1
            
            # Risque moyen
            total_risk += calc.risk_amount
        
        most_used_asset = max(asset_counts.items(), key=lambda x: x[1]) if asset_counts else None
        avg_risk = total_risk / len(history)
        
        return {
            'total_calculations': len(history),
            'most_used_asset': most_used_asset[0] if most_used_asset else None,
            'average_risk_amount': round(avg_risk, 2),
            'risk_distribution': risk_levels,
            'conservative_trader': risk_levels['low'] > risk_levels['high'] + risk_levels['extreme']
        }
    
    def get_supported_assets(self) -> List[Dict]:
        """Liste des actifs supportés avec leurs spécifications"""
        assets = []
        
        for symbol, spec in self.asset_specs.items():
            assets.append({
                'symbol': symbol,
                'name': self._get_asset_name(symbol),
                'type': spec.asset_type.value,
                'pip_size': spec.pip_size,
                'min_lot': spec.min_lot_size,
                'max_lot': spec.max_lot_size,
                'margin_req': spec.margin_requirement,
                'trading_hours': spec.trading_hours
            })
        
        return sorted(assets, key=lambda x: (x['type'], x['symbol']))
    
    def _get_asset_name(self, symbol: str) -> str:
        """Retourne le nom complet de l'actif"""
        names = {
            'EURUSD': 'Euro/Dollar US',
            'GBPUSD': 'Livre Sterling/Dollar US',
            'USDJPY': 'Dollar US/Yen Japonais',
            'XAUUSD': 'Or/Dollar US',
            'XAGUSD': 'Argent/Dollar US',
            'BTCUSD': 'Bitcoin/Dollar US',
            'ETHUSD': 'Ethereum/Dollar US',
            'SPX500': 'S&P 500 Index',
            'USOIL': 'Pétrole Brut US'
        }
        return names.get(symbol, symbol)

# Instance globale du calculateur avancé
advanced_calculator = AdvancedPositionCalculator()