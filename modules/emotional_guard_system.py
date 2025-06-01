"""
Système de Protection Émotionnelle - MindTraderPro
Mode Safe, Auto-lock, détection revenge trading, blocages intelligents
"""
import json
import os
from datetime import datetime, timedelta
from uuid import uuid4

class EmotionalGuardSystem:
    def __init__(self):
        self.user_states_file = 'data/emotional_states.json'
        self.lockout_sessions_file = 'data/lockout_sessions.json'
        self.safe_mode_configs_file = 'data/safe_mode_configs.json'
        
        # Configuration des triggers émotionnels
        self.emotional_triggers = {
            'consecutive_losses': {
                'threshold': 3,
                'action': 'auto_lock',
                'duration_minutes': 30,
                'message': '3 pertes consécutives détectées. Prenez une pause pour éviter le revenge trading.'
            },
            'rapid_trading': {
                'threshold': 5,  # 5 trades en moins de 30 minutes
                'timeframe_minutes': 30,
                'action': 'warning',
                'message': 'Vous tradez très rapidement. Prenez le temps d\'analyser.'
            },
            'lot_escalation': {
                'threshold': 2.0,  # Doublement de la taille
                'action': 'confirm_required',
                'message': 'Augmentation importante de la taille de position détectée.'
            },
            'high_risk_after_loss': {
                'threshold': 1.5,  # 50% plus de risque après perte
                'action': 'warning',
                'message': 'Vous augmentez le risque après une perte. Restez discipliné.'
            }
        }
    
    def activate_safe_mode(self, user_session, duration_hours=24, restrictions=None):
        """Active le mode sécurisé avec restrictions personnalisées"""
        try:
            safe_mode_id = str(uuid4())
            
            default_restrictions = {
                'max_lot_size': 0.1,
                'max_trades_per_day': 3,
                'max_risk_percent': 0.5,
                'blocked_pairs': [],
                'require_confirmation': True,
                'auto_tp_required': True
            }
            
            if restrictions:
                default_restrictions.update(restrictions)
            
            safe_mode_config = {
                'id': safe_mode_id,
                'user_session': user_session,
                'activated_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=duration_hours)).isoformat(),
                'restrictions': default_restrictions,
                'reason': 'Manual activation',
                'status': 'active',
                'trades_today': 0,
                'max_lot_used_today': 0,
                'violations': []
            }
            
            # Sauvegarder
            configs = self._load_safe_mode_configs()
            
            # Désactiver les anciens modes pour cet utilisateur
            for config in configs:
                if config['user_session'] == user_session and config['status'] == 'active':
                    config['status'] = 'replaced'
            
            configs.append(safe_mode_config)
            self._save_safe_mode_configs(configs)
            
            # Enregistrer l'état émotionnel
            self._record_emotional_state(user_session, 'safe_mode_activated', {
                'duration_hours': duration_hours,
                'restrictions': default_restrictions
            })
            
            return {
                'success': True,
                'safe_mode_id': safe_mode_id,
                'message': f'Mode sécurisé activé pour {duration_hours}h',
                'restrictions': default_restrictions,
                'expires_at': safe_mode_config['expires_at']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur activation mode sécurisé: {str(e)}'}
    
    def check_trade_permission(self, user_session, trade_data):
        """Vérifie si un trade est autorisé selon l'état émotionnel"""
        try:
            # Vérifier le mode sécurisé
            safe_mode = self.get_active_safe_mode(user_session)
            if safe_mode['active']:
                permission_check = self._check_safe_mode_permission(safe_mode['config'], trade_data)
                if not permission_check['allowed']:
                    return permission_check
            
            # Vérifier les blocages émotionnels
            lockout_check = self.check_emotional_lockout(user_session)
            if lockout_check['locked']:
                return {
                    'allowed': False,
                    'reason': 'emotional_lockout',
                    'message': lockout_check['message'],
                    'unlock_time': lockout_check['unlock_time']
                }
            
            # Analyser les patterns de trading récents
            pattern_analysis = self._analyze_trading_patterns(user_session, trade_data)
            if pattern_analysis['risk_detected']:
                return {
                    'allowed': True,
                    'warning': True,
                    'risk_type': pattern_analysis['risk_type'],
                    'message': pattern_analysis['message'],
                    'confirmation_required': pattern_analysis.get('confirmation_required', False)
                }
            
            return {
                'allowed': True,
                'message': 'Trade autorisé'
            }
            
        except Exception as e:
            return {'allowed': False, 'error': f'Erreur vérification: {str(e)}'}
    
    def trigger_auto_lock(self, user_session, trigger_type, trigger_data):
        """Déclenche un blocage automatique"""
        try:
            trigger_config = self.emotional_triggers.get(trigger_type)
            if not trigger_config:
                return {'success': False, 'error': 'Type de trigger inconnu'}
            
            lockout_id = str(uuid4())
            duration_minutes = trigger_config.get('duration_minutes', 30)
            
            lockout_session = {
                'id': lockout_id,
                'user_session': user_session,
                'trigger_type': trigger_type,
                'trigger_data': trigger_data,
                'triggered_at': datetime.now().isoformat(),
                'unlock_time': (datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
                'status': 'active',
                'message': trigger_config['message'],
                'manual_unlock': False
            }
            
            # Sauvegarder
            lockouts = self._load_lockout_sessions()
            lockouts.append(lockout_session)
            self._save_lockout_sessions(lockouts)
            
            # Enregistrer l'état émotionnel
            self._record_emotional_state(user_session, 'auto_locked', {
                'trigger_type': trigger_type,
                'duration_minutes': duration_minutes
            })
            
            return {
                'success': True,
                'lockout_id': lockout_id,
                'message': trigger_config['message'],
                'unlock_time': lockout_session['unlock_time'],
                'duration_minutes': duration_minutes
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur auto-lock: {str(e)}'}
    
    def check_emotional_lockout(self, user_session):
        """Vérifie si l'utilisateur est bloqué émotionnellement"""
        try:
            lockouts = self._load_lockout_sessions()
            current_time = datetime.now()
            
            # Chercher un blocage actif
            active_lockout = None
            for lockout in lockouts:
                if (lockout['user_session'] == user_session and 
                    lockout['status'] == 'active'):
                    unlock_time = datetime.fromisoformat(lockout['unlock_time'])
                    if current_time < unlock_time:
                        active_lockout = lockout
                        break
                    else:
                        # Expirer le blocage
                        lockout['status'] = 'expired'
            
            if active_lockout:
                self._save_lockout_sessions(lockouts)
                return {
                    'locked': True,
                    'lockout': active_lockout,
                    'message': active_lockout['message'],
                    'unlock_time': active_lockout['unlock_time'],
                    'remaining_minutes': (datetime.fromisoformat(active_lockout['unlock_time']) - current_time).total_seconds() / 60
                }
            
            return {'locked': False}
            
        except Exception as e:
            return {'locked': False, 'error': f'Erreur vérification blocage: {str(e)}'}
    
    def get_active_safe_mode(self, user_session):
        """Récupère le mode sécurisé actif pour un utilisateur"""
        try:
            configs = self._load_safe_mode_configs()
            current_time = datetime.now()
            
            for config in configs:
                if (config['user_session'] == user_session and 
                    config['status'] == 'active'):
                    expires_at = datetime.fromisoformat(config['expires_at'])
                    if current_time < expires_at:
                        return {
                            'active': True,
                            'config': config,
                            'remaining_hours': (expires_at - current_time).total_seconds() / 3600
                        }
                    else:
                        # Expirer le mode
                        config['status'] = 'expired'
                        self._save_safe_mode_configs(configs)
            
            return {'active': False}
            
        except Exception as e:
            return {'active': False, 'error': f'Erreur mode sécurisé: {str(e)}'}
    
    def record_emotional_trade(self, user_session, trade_data, emotion_before, emotion_after, confidence_level):
        """Enregistre un trade avec son contexte émotionnel"""
        try:
            emotional_entry = {
                'user_session': user_session,
                'trade_data': trade_data,
                'emotion_before': emotion_before,  # calm, excited, anxious, angry, confident
                'emotion_after': emotion_after,
                'confidence_level': confidence_level,  # 1-10
                'timestamp': datetime.now().isoformat(),
                'triggers_detected': []
            }
            
            # Analyser les triggers potentiels
            self._analyze_emotional_triggers(user_session, emotional_entry)
            
            # Enregistrer l'état
            self._record_emotional_state(user_session, 'trade_executed', emotional_entry)
            
            return {
                'success': True,
                'emotional_analysis': emotional_entry,
                'recommendations': self._generate_emotional_recommendations(emotional_entry)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur enregistrement émotionnel: {str(e)}'}
    
    def get_emotional_dashboard(self, user_session, days_back=30):
        """Génère un dashboard des états émotionnels"""
        try:
            states = self._load_emotional_states()
            user_states = [
                s for s in states 
                if s['user_session'] == user_session and
                datetime.fromisoformat(s['timestamp']) > datetime.now() - timedelta(days=days_back)
            ]
            
            # Analyse des patterns
            emotional_patterns = self._analyze_emotional_patterns(user_states)
            
            # États récents
            recent_states = sorted(user_states, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            # Recommandations
            recommendations = self._generate_dashboard_recommendations(emotional_patterns)
            
            return {
                'success': True,
                'dashboard': {
                    'total_entries': len(user_states),
                    'emotional_patterns': emotional_patterns,
                    'recent_states': recent_states,
                    'recommendations': recommendations,
                    'safe_mode_status': self.get_active_safe_mode(user_session),
                    'lockout_status': self.check_emotional_lockout(user_session)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur dashboard émotionnel: {str(e)}'}
    
    def _check_safe_mode_permission(self, safe_config, trade_data):
        """Vérifie les permissions selon le mode sécurisé"""
        restrictions = safe_config['restrictions']
        
        # Vérifier la taille de lot
        if trade_data.get('lot_size', 0) > restrictions['max_lot_size']:
            return {
                'allowed': False,
                'reason': 'lot_size_restricted',
                'message': f'Taille de lot limitée à {restrictions["max_lot_size"]} en mode sécurisé'
            }
        
        # Vérifier le nombre de trades quotidiens
        if safe_config['trades_today'] >= restrictions['max_trades_per_day']:
            return {
                'allowed': False,
                'reason': 'daily_trades_limit',
                'message': f'Limite quotidienne de {restrictions["max_trades_per_day"]} trades atteinte'
            }
        
        # Vérifier le risque
        if trade_data.get('risk_percent', 0) > restrictions['max_risk_percent']:
            return {
                'allowed': False,
                'reason': 'risk_limited',
                'message': f'Risque limité à {restrictions["max_risk_percent"]}% en mode sécurisé'
            }
        
        # Vérifier les paires bloquées
        if trade_data.get('pair_symbol') in restrictions.get('blocked_pairs', []):
            return {
                'allowed': False,
                'reason': 'pair_blocked',
                'message': f'Paire {trade_data["pair_symbol"]} bloquée en mode sécurisé'
            }
        
        return {'allowed': True}
    
    def _analyze_trading_patterns(self, user_session, current_trade):
        """Analyse les patterns de trading pour détecter les risques"""
        # Récupérer les trades récents
        recent_trades = self._get_recent_trades(user_session, hours=2)
        
        # Vérifier les pertes consécutives
        consecutive_losses = 0
        for trade in recent_trades:
            if trade.get('profit_loss', 0) < 0:
                consecutive_losses += 1
            else:
                break
        
        if consecutive_losses >= 2:
            return {
                'risk_detected': True,
                'risk_type': 'consecutive_losses',
                'message': f'{consecutive_losses} pertes consécutives. Attention au revenge trading.',
                'confirmation_required': True
            }
        
        # Vérifier le trading rapide
        if len(recent_trades) >= 4:
            return {
                'risk_detected': True,
                'risk_type': 'rapid_trading',
                'message': 'Trading très fréquent détecté. Prenez le temps d\'analyser.',
                'confirmation_required': False
            }
        
        return {'risk_detected': False}
    
    def _analyze_emotional_triggers(self, user_session, emotional_entry):
        """Analyse les triggers émotionnels"""
        triggers = []
        
        # Émotion négative avec faible confiance
        if (emotional_entry['emotion_before'] in ['angry', 'anxious'] and 
            emotional_entry['confidence_level'] < 5):
            triggers.append('negative_emotion_low_confidence')
        
        # Trading après forte émotion
        if emotional_entry['emotion_before'] == 'angry':
            triggers.append('anger_trading')
        
        emotional_entry['triggers_detected'] = triggers
        return triggers
    
    def _generate_emotional_recommendations(self, emotional_entry):
        """Génère des recommandations basées sur l'état émotionnel"""
        recommendations = []
        
        if 'anger_trading' in emotional_entry['triggers_detected']:
            recommendations.append("Évitez de trader en colère. Prenez une pause de 15 minutes.")
        
        if emotional_entry['confidence_level'] < 4:
            recommendations.append("Niveau de confiance faible. Réduisez la taille de position.")
        
        if emotional_entry['emotion_after'] == 'anxious':
            recommendations.append("L'anxiété après trade indique un risque trop élevé.")
        
        return recommendations
    
    def _get_recent_trades(self, user_session, hours=24):
        """Récupère les trades récents d'un utilisateur"""
        try:
            trades_file = f'data/trades_{user_session}.json'
            if os.path.exists(trades_file):
                with open(trades_file, 'r', encoding='utf-8') as f:
                    all_trades = json.load(f)
                
                cutoff_time = datetime.now() - timedelta(hours=hours)
                recent_trades = [
                    trade for trade in all_trades 
                    if datetime.fromisoformat(trade.get('timestamp', '2024-01-01T00:00:00')) > cutoff_time
                ]
                return sorted(recent_trades, key=lambda x: x.get('timestamp', ''), reverse=True)
            return []
        except:
            return []
    
    def _record_emotional_state(self, user_session, state_type, data):
        """Enregistre un état émotionnel"""
        try:
            states = self._load_emotional_states()
            
            state_entry = {
                'user_session': user_session,
                'state_type': state_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            states.append(state_entry)
            states = states[-1000:]  # Garder seulement les 1000 derniers
            
            self._save_emotional_states(states)
        except Exception as e:
            print(f"Erreur enregistrement état émotionnel: {e}")
    
    def _load_emotional_states(self):
        """Charge les états émotionnels"""
        try:
            if os.path.exists(self.user_states_file):
                with open(self.user_states_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_emotional_states(self, states):
        """Sauvegarde les états émotionnels"""
        try:
            os.makedirs(os.path.dirname(self.user_states_file), exist_ok=True)
            with open(self.user_states_file, 'w', encoding='utf-8') as f:
                json.dump(states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde états émotionnels: {e}")
    
    def _load_lockout_sessions(self):
        """Charge les sessions de blocage"""
        try:
            if os.path.exists(self.lockout_sessions_file):
                with open(self.lockout_sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_lockout_sessions(self, sessions):
        """Sauvegarde les sessions de blocage"""
        try:
            os.makedirs(os.path.dirname(self.lockout_sessions_file), exist_ok=True)
            with open(self.lockout_sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde sessions blocage: {e}")
    
    def _load_safe_mode_configs(self):
        """Charge les configurations mode sécurisé"""
        try:
            if os.path.exists(self.safe_mode_configs_file):
                with open(self.safe_mode_configs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_safe_mode_configs(self, configs):
        """Sauvegarde les configurations mode sécurisé"""
        try:
            os.makedirs(os.path.dirname(self.safe_mode_configs_file), exist_ok=True)
            with open(self.safe_mode_configs_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde configs mode sécurisé: {e}")

# Instance globale
emotional_guard = EmotionalGuardSystem()