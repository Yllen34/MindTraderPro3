"""
Simulateur Prop Firm - MindTraderPro
Simulation FTMO, 5%ers avec règles automatiques et blocages
"""
import json
import os
from datetime import datetime, timedelta
from uuid import uuid4

class PropFirmSimulator:
    def __init__(self):
        self.challenges_file = 'data/prop_challenges.json'
        self.user_accounts_file = 'data/prop_accounts.json'
        
        # Définition des règles des prop firms
        self.firm_rules = {
            'ftmo': {
                'name': 'FTMO Challenge',
                'sizes': {
                    10000: {'target': 1000, 'max_dd': 1000, 'daily_dd': 500},
                    25000: {'target': 2500, 'max_dd': 2500, 'daily_dd': 1250},
                    50000: {'target': 5000, 'max_dd': 2500, 'daily_dd': 2500},
                    100000: {'target': 10000, 'max_dd': 5000, 'daily_dd': 5000},
                    200000: {'target': 20000, 'max_dd': 10000, 'daily_dd': 10000}
                },
                'min_trading_days': 5,
                'max_trading_days': 30,
                'weekend_holding': False,
                'news_trading': False,
                'lot_restrictions': {
                    'XAUUSD': 2.0,
                    'EURUSD': 20.0,
                    'GBPUSD': 20.0
                }
            },
            'the5ers': {
                'name': 'The 5%ers Challenge',
                'sizes': {
                    4000: {'target': 200, 'max_dd': 200, 'daily_dd': 100},
                    6000: {'target': 300, 'max_dd': 300, 'daily_dd': 150},
                    20000: {'target': 1000, 'max_dd': 1000, 'daily_dd': 500},
                    100000: {'target': 5000, 'max_dd': 5000, 'daily_dd': 2500}
                },
                'min_trading_days': 6,
                'max_trading_days': 60,
                'weekend_holding': True,
                'news_trading': True,
                'lot_restrictions': {
                    'XAUUSD': 1.5,
                    'EURUSD': 15.0
                }
            },
            'apex': {
                'name': 'Apex Trader Challenge',
                'sizes': {
                    25000: {'target': 1500, 'max_dd': 1500, 'daily_dd': 750},
                    50000: {'target': 3000, 'max_dd': 3000, 'daily_dd': 1500},
                    100000: {'target': 6000, 'max_dd': 6000, 'daily_dd': 3000},
                    250000: {'target': 15000, 'max_dd': 15000, 'daily_dd': 7500}
                },
                'min_trading_days': 5,
                'max_trading_days': 30,
                'weekend_holding': False,
                'news_trading': False,
                'lot_restrictions': {
                    'XAUUSD': 3.0,
                    'EURUSD': 30.0
                }
            }
        }
    
    def create_challenge(self, user_session, firm_name, account_size, user_plan='free'):
        """Crée un nouveau challenge prop firm"""
        try:
            # Vérification des limitations freemium
            if user_plan == 'free':
                existing_challenges = self.get_user_challenges(user_session)
                if existing_challenges['success'] and len(existing_challenges['challenges']) >= 1:
                    return {
                        'success': False,
                        'error': 'Limite gratuite atteinte. Passez Premium pour des challenges illimités.',
                        'upgrade_required': True
                    }
            
            if firm_name not in self.firm_rules:
                return {'success': False, 'error': 'Prop firm non supportée'}
            
            firm = self.firm_rules[firm_name]
            if account_size not in firm['sizes']:
                return {'success': False, 'error': 'Taille de compte non disponible'}
            
            rules = firm['sizes'][account_size]
            challenge_id = str(uuid4())
            
            challenge = {
                'id': challenge_id,
                'user_session': user_session,
                'firm_name': firm_name,
                'firm_display_name': firm['name'],
                'account_size': account_size,
                'target_profit': rules['target'],
                'max_drawdown': rules['max_dd'],
                'daily_drawdown': rules['daily_dd'],
                'min_trading_days': firm['min_trading_days'],
                'max_trading_days': firm['max_trading_days'],
                'lot_restrictions': firm['lot_restrictions'],
                'rules': {
                    'weekend_holding': firm['weekend_holding'],
                    'news_trading': firm['news_trading']
                },
                'created_at': datetime.now().isoformat(),
                'status': 'active',  # active, passed, failed, expired
                'current_balance': account_size,
                'peak_balance': account_size,
                'current_drawdown': 0,
                'max_daily_loss': 0,
                'trading_days': 0,
                'trades': [],
                'violations': [],
                'daily_stats': {}
            }
            
            # Sauvegarder
            challenges = self._load_challenges()
            challenges.append(challenge)
            self._save_challenges(challenges)
            
            return {
                'success': True,
                'challenge_id': challenge_id,
                'message': f'Challenge {firm["name"]} créé avec succès',
                'challenge': challenge
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur création challenge: {str(e)}'}
    
    def add_trade_to_challenge(self, challenge_id, trade_data):
        """Ajoute un trade au challenge et vérifie les règles"""
        try:
            challenges = self._load_challenges()
            challenge = next((c for c in challenges if c['id'] == challenge_id), None)
            
            if not challenge:
                return {'success': False, 'error': 'Challenge non trouvé'}
            
            if challenge['status'] != 'active':
                return {'success': False, 'error': 'Challenge non actif'}
            
            # Validation du trade
            validation_result = self._validate_trade(challenge, trade_data)
            if not validation_result['valid']:
                # Enregistrer la violation
                violation = {
                    'type': validation_result['violation_type'],
                    'description': validation_result['message'],
                    'trade_data': trade_data,
                    'timestamp': datetime.now().isoformat()
                }
                challenge['violations'].append(violation)
                
                # Vérifier si échec immédiat
                if validation_result['immediate_failure']:
                    challenge['status'] = 'failed'
                    challenge['failure_reason'] = validation_result['message']
                    self._save_challenges(challenges)
                    
                    return {
                        'success': False,
                        'challenge_failed': True,
                        'reason': validation_result['message'],
                        'violation': violation
                    }
            
            # Ajouter le trade
            trade_entry = {
                'id': str(uuid4()),
                'pair_symbol': trade_data['pair_symbol'],
                'trade_type': trade_data['trade_type'],
                'lot_size': trade_data['lot_size'],
                'entry_price': trade_data['entry_price'],
                'exit_price': trade_data.get('exit_price'),
                'profit_loss': trade_data['profit_loss'],
                'timestamp': trade_data.get('timestamp', datetime.now().isoformat()),
                'status': trade_data.get('status', 'closed')
            }
            
            challenge['trades'].append(trade_entry)
            
            # Mettre à jour les statistiques
            self._update_challenge_stats(challenge, trade_entry)
            
            # Vérifier les règles après le trade
            rule_check = self._check_challenge_rules(challenge)
            
            self._save_challenges(challenges)
            
            return {
                'success': True,
                'trade_added': True,
                'current_stats': {
                    'balance': challenge['current_balance'],
                    'drawdown': challenge['current_drawdown'],
                    'profit': challenge['current_balance'] - challenge['account_size'],
                    'target_progress': ((challenge['current_balance'] - challenge['account_size']) / challenge['target_profit']) * 100
                },
                'rule_violations': challenge['violations'],
                'challenge_status': challenge['status'],
                'rule_check': rule_check
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur ajout trade: {str(e)}'}
    
    def get_challenge_status(self, challenge_id):
        """Récupère le statut détaillé d'un challenge"""
        try:
            challenges = self._load_challenges()
            challenge = next((c for c in challenges if c['id'] == challenge_id), None)
            
            if not challenge:
                return {'success': False, 'error': 'Challenge non trouvé'}
            
            # Calculer les métriques
            total_trades = len(challenge['trades'])
            winning_trades = len([t for t in challenge['trades'] if t['profit_loss'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_profit = challenge['current_balance'] - challenge['account_size']
            target_progress = (total_profit / challenge['target_profit'] * 100) if challenge['target_profit'] > 0 else 0
            
            days_remaining = max(0, challenge['max_trading_days'] - challenge['trading_days'])
            min_days_remaining = max(0, challenge['min_trading_days'] - challenge['trading_days'])
            
            status_detail = {
                'challenge': challenge,
                'metrics': {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'target_progress': target_progress,
                    'current_drawdown_pct': (challenge['current_drawdown'] / challenge['account_size']) * 100,
                    'days_remaining': days_remaining,
                    'min_days_remaining': min_days_remaining
                },
                'requirements': {
                    'profit_target': challenge['target_profit'],
                    'max_drawdown': challenge['max_drawdown'],
                    'daily_drawdown': challenge['daily_drawdown'],
                    'min_trading_days': challenge['min_trading_days']
                },
                'violations': challenge['violations'],
                'recent_trades': challenge['trades'][-5:] if challenge['trades'] else []
            }
            
            return {
                'success': True,
                'status': status_detail
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération statut: {str(e)}'}
    
    def get_user_challenges(self, user_session):
        """Récupère tous les challenges d'un utilisateur"""
        try:
            challenges = self._load_challenges()
            user_challenges = [c for c in challenges if c['user_session'] == user_session]
            
            # Trier par date de création
            user_challenges.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'challenges': user_challenges,
                'total_count': len(user_challenges),
                'active_count': len([c for c in user_challenges if c['status'] == 'active']),
                'passed_count': len([c for c in user_challenges if c['status'] == 'passed']),
                'failed_count': len([c for c in user_challenges if c['status'] == 'failed'])
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération challenges: {str(e)}'}
    
    def _validate_trade(self, challenge, trade_data):
        """Valide un trade selon les règles du prop firm"""
        firm_rules = self.firm_rules[challenge['firm_name']]
        
        # Vérifier les restrictions de lot
        pair = trade_data['pair_symbol']
        lot_size = trade_data['lot_size']
        
        if pair in firm_rules['lot_restrictions']:
            max_lot = firm_rules['lot_restrictions'][pair]
            if lot_size > max_lot:
                return {
                    'valid': False,
                    'violation_type': 'lot_size_exceeded',
                    'message': f'Taille de lot dépassée pour {pair}: {lot_size} > {max_lot}',
                    'immediate_failure': True
                }
        
        # Vérifier le trading de weekend (si interdit)
        if not firm_rules['weekend_holding']:
            trade_time = datetime.fromisoformat(trade_data.get('timestamp', datetime.now().isoformat()))
            if trade_time.weekday() >= 5:  # Samedi = 5, Dimanche = 6
                return {
                    'valid': False,
                    'violation_type': 'weekend_trading',
                    'message': 'Trading le weekend interdit',
                    'immediate_failure': False
                }
        
        return {'valid': True}
    
    def _update_challenge_stats(self, challenge, trade_entry):
        """Met à jour les statistiques du challenge"""
        # Mettre à jour le solde
        challenge['current_balance'] += trade_entry['profit_loss']
        
        # Mettre à jour le pic de balance
        if challenge['current_balance'] > challenge['peak_balance']:
            challenge['peak_balance'] = challenge['current_balance']
        
        # Calculer le drawdown actuel
        challenge['current_drawdown'] = challenge['peak_balance'] - challenge['current_balance']
        
        # Statistiques quotidiennes
        trade_date = datetime.fromisoformat(trade_entry['timestamp']).date().isoformat()
        if trade_date not in challenge['daily_stats']:
            challenge['daily_stats'][trade_date] = {
                'trades': 0,
                'profit_loss': 0,
                'max_loss_today': 0
            }
        
        daily_stats = challenge['daily_stats'][trade_date]
        daily_stats['trades'] += 1
        daily_stats['profit_loss'] += trade_entry['profit_loss']
        
        if trade_entry['profit_loss'] < 0:
            daily_stats['max_loss_today'] += abs(trade_entry['profit_loss'])
        
        # Compter les jours de trading
        challenge['trading_days'] = len(challenge['daily_stats'])
    
    def _check_challenge_rules(self, challenge):
        """Vérifie toutes les règles du challenge"""
        violations = []
        
        # Vérifier le drawdown maximum
        if challenge['current_drawdown'] >= challenge['max_drawdown']:
            challenge['status'] = 'failed'
            challenge['failure_reason'] = f'Drawdown maximum dépassé: {challenge["current_drawdown"]}$'
            violations.append('max_drawdown_exceeded')
        
        # Vérifier le drawdown quotidien
        today = datetime.now().date().isoformat()
        if today in challenge['daily_stats']:
            daily_loss = challenge['daily_stats'][today]['max_loss_today']
            if daily_loss >= challenge['daily_drawdown']:
                challenge['status'] = 'failed'
                challenge['failure_reason'] = f'Perte quotidienne maximum dépassée: {daily_loss}$'
                violations.append('daily_drawdown_exceeded')
        
        # Vérifier si l'objectif est atteint
        profit = challenge['current_balance'] - challenge['account_size']
        if (profit >= challenge['target_profit'] and 
            challenge['trading_days'] >= challenge['min_trading_days']):
            challenge['status'] = 'passed'
            challenge['passed_at'] = datetime.now().isoformat()
        
        # Vérifier l'expiration
        if challenge['trading_days'] >= challenge['max_trading_days'] and challenge['status'] == 'active':
            if profit < challenge['target_profit']:
                challenge['status'] = 'failed'
                challenge['failure_reason'] = 'Objectif non atteint dans les délais'
                violations.append('time_expired')
        
        return {
            'violations': violations,
            'status': challenge['status']
        }
    
    def _load_challenges(self):
        """Charge les challenges"""
        try:
            if os.path.exists(self.challenges_file):
                with open(self.challenges_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_challenges(self, challenges):
        """Sauvegarde les challenges"""
        try:
            os.makedirs(os.path.dirname(self.challenges_file), exist_ok=True)
            with open(self.challenges_file, 'w', encoding='utf-8') as f:
                json.dump(challenges, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde challenges: {e}")

# Instance globale
prop_simulator = PropFirmSimulator()