"""
Système de Gamification - MindTraderPro
XP, niveaux, badges, récompenses, défis hebdomadaires
"""
import json
import os
from datetime import datetime, timedelta
from math import floor

class GamificationSystem:
    def __init__(self):
        self.badges_definitions = {
            'first_trade': {
                'name': 'Premier Trade',
                'description': 'Enregistrez votre premier trade',
                'icon': '🎯',
                'xp_reward': 50,
                'type': 'milestone'
            },
            'profitable_week': {
                'name': 'Semaine Profitable',
                'description': 'Réalisez une semaine profitable',
                'icon': '💚',
                'xp_reward': 100,
                'type': 'performance'
            },
            'consistency_master': {
                'name': 'Maître de la Consistance',
                'description': '5 jours de trading consécutifs',
                'icon': '🏆',
                'xp_reward': 150,
                'type': 'consistency'
            },
            'risk_manager': {
                'name': 'Gestionnaire de Risque',
                'description': 'Respectez votre limite de risque pendant 10 trades',
                'icon': '🛡️',
                'xp_reward': 120,
                'type': 'discipline'
            },
            'big_win': {
                'name': 'Gros Gain',
                'description': 'Réalisez un gain de plus de 500$',
                'icon': '💎',
                'xp_reward': 200,
                'type': 'achievement'
            },
            'comeback_king': {
                'name': 'Roi du Comeback',
                'description': 'Récupérez après 3 trades perdants',
                'icon': '👑',
                'xp_reward': 180,
                'type': 'resilience'
            },
            'journal_keeper': {
                'name': 'Gardien du Journal',
                'description': 'Enregistrez 50 trades dans votre journal',
                'icon': '📚',
                'xp_reward': 100,
                'type': 'documentation'
            },
            'early_bird': {
                'name': 'Lève-Tôt',
                'description': 'Tradez avant 9h pendant 5 jours',
                'icon': '🌅',
                'xp_reward': 80,
                'type': 'habit'
            },
            'calculator_expert': {
                'name': 'Expert Calculateur',
                'description': 'Utilisez le calculateur 100 fois',
                'icon': '🧮',
                'xp_reward': 90,
                'type': 'tool_usage'
            },
            'ai_student': {
                'name': 'Élève IA',
                'description': 'Demandez 10 analyses à l\'assistant IA',
                'icon': '🤖',
                'xp_reward': 110,
                'type': 'learning'
            }
        }
        
        self.level_thresholds = [
            0, 100, 250, 500, 1000, 1800, 2800, 4200, 6000, 8500, 
            11500, 15000, 19000, 24000, 30000, 37000, 45000, 54000, 
            65000, 78000, 93000, 110000, 130000, 153000, 180000
        ]
        
        self.weekly_challenges = {
            'profit_target': {
                'name': 'Objectif Profit',
                'description': 'Réalisez 200$ de profit cette semaine',
                'reward_xp': 200,
                'icon': '💰'
            },
            'consistency_challenge': {
                'name': 'Défi Consistance',
                'description': 'Tradez 5 jours cette semaine',
                'reward_xp': 150,
                'icon': '📅'
            },
            'risk_discipline': {
                'name': 'Discipline du Risque',
                'description': 'Ne dépassez jamais 2% de risque',
                'reward_xp': 180,
                'icon': '⚖️'
            },
            'journal_master': {
                'name': 'Maître du Journal',
                'description': 'Documentez tous vos trades',
                'reward_xp': 120,
                'icon': '✍️'
            },
            'learning_week': {
                'name': 'Semaine d\'Apprentissage',
                'description': 'Utilisez l\'IA 3 fois pour des analyses',
                'reward_xp': 140,
                'icon': '🎓'
            }
        }
    
    def get_user_profile(self, user_session):
        """Récupère le profil gamification de l'utilisateur"""
        try:
            profile_file = f'data/gamification_{user_session}.json'
            if os.path.exists(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = self._create_new_profile(user_session)
            
            # Mise à jour du niveau
            profile = self._update_level(profile)
            return profile
            
        except Exception as e:
            return self._create_new_profile(user_session)
    
    def award_xp(self, user_session, amount, reason="Action"):
        """Attribue de l'XP à un utilisateur"""
        try:
            profile = self.get_user_profile(user_session)
            old_level = profile['level']
            
            profile['xp'] += amount
            profile['total_xp'] += amount
            
            # Vérification de montée de niveau
            new_profile = self._update_level(profile)
            level_up = new_profile['level'] > old_level
            
            # Enregistrement de l'activité XP
            xp_activity = {
                'amount': amount,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'total_xp': new_profile['total_xp']
            }
            
            new_profile['xp_history'].append(xp_activity)
            new_profile['xp_history'] = new_profile['xp_history'][-50:]  # Garder 50 dernières
            
            self._save_profile(user_session, new_profile)
            
            return {
                'success': True,
                'xp_awarded': amount,
                'total_xp': new_profile['total_xp'],
                'level': new_profile['level'],
                'level_up': level_up,
                'progress_to_next': new_profile['progress_to_next_level']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_badge_earned(self, user_session, action_type, action_data=None):
        """Vérifie si un badge a été gagné"""
        try:
            profile = self.get_user_profile(user_session)
            earned_badges = []
            
            # Vérifications selon le type d'action
            if action_type == 'trade_completed':
                earned_badges.extend(self._check_trade_badges(profile, action_data))
            elif action_type == 'calculator_used':
                earned_badges.extend(self._check_calculator_badges(profile))
            elif action_type == 'ai_analysis':
                earned_badges.extend(self._check_ai_badges(profile))
            elif action_type == 'journal_entry':
                earned_badges.extend(self._check_journal_badges(profile))
            
            # Attribution des nouveaux badges
            for badge_id in earned_badges:
                if badge_id not in profile['badges']:
                    badge_info = self.badges_definitions[badge_id]
                    profile['badges'].append({
                        'id': badge_id,
                        'name': badge_info['name'],
                        'earned_at': datetime.now().isoformat(),
                        'xp_reward': badge_info['xp_reward']
                    })
                    
                    # Attribution XP du badge
                    self.award_xp(user_session, badge_info['xp_reward'], f"Badge: {badge_info['name']}")
            
            self._save_profile(user_session, profile)
            
            return {
                'success': True,
                'new_badges': earned_badges,
                'total_badges': len(profile['badges'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_weekly_challenges(self, user_session):
        """Récupère les défis de la semaine"""
        try:
            profile = self.get_user_profile(user_session)
            current_week = self._get_current_week()
            
            # Vérifier si c'est une nouvelle semaine
            if profile.get('current_week') != current_week:
                profile['current_week'] = current_week
                profile['weekly_progress'] = {}
                self._save_profile(user_session, profile)
            
            # Calculer les progrès
            challenges_with_progress = {}
            for challenge_id, challenge in self.weekly_challenges.items():
                progress = self._calculate_challenge_progress(user_session, challenge_id, profile)
                challenges_with_progress[challenge_id] = {
                    **challenge,
                    'progress': progress,
                    'completed': progress >= 100
                }
            
            return {
                'success': True,
                'challenges': challenges_with_progress,
                'week': current_week
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_challenge(self, user_session, challenge_id):
        """Marque un défi comme complété"""
        try:
            profile = self.get_user_profile(user_session)
            
            if challenge_id in self.weekly_challenges:
                challenge = self.weekly_challenges[challenge_id]
                
                # Vérifier si déjà complété cette semaine
                current_week = self._get_current_week()
                completed_key = f"{current_week}_{challenge_id}"
                
                if completed_key not in profile.get('completed_challenges', []):
                    # Marquer comme complété
                    if 'completed_challenges' not in profile:
                        profile['completed_challenges'] = []
                    profile['completed_challenges'].append(completed_key)
                    
                    # Attribution XP
                    self.award_xp(user_session, challenge['reward_xp'], f"Défi: {challenge['name']}")
                    
                    self._save_profile(user_session, profile)
                    
                    return {
                        'success': True,
                        'challenge_completed': challenge['name'],
                        'xp_awarded': challenge['reward_xp']
                    }
            
            return {'success': False, 'message': 'Défi déjà complété ou inexistant'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_leaderboard(self, limit=10):
        """Récupère le classement des utilisateurs"""
        try:
            leaderboard = []
            
            # Parcourir tous les profils de gamification
            data_dir = 'data'
            if os.path.exists(data_dir):
                for filename in os.listdir(data_dir):
                    if filename.startswith('gamification_') and filename.endswith('.json'):
                        try:
                            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                                profile = json.load(f)
                                leaderboard.append({
                                    'user_session': profile['user_session'],
                                    'level': profile['level'],
                                    'total_xp': profile['total_xp'],
                                    'badges_count': len(profile['badges']),
                                    'username': profile.get('display_name', f"Trader_{profile['user_session'][-4:]}")
                                })
                        except:
                            continue
            
            # Trier par XP total
            leaderboard.sort(key=lambda x: x['total_xp'], reverse=True)
            
            return {
                'success': True,
                'leaderboard': leaderboard[:limit],
                'total_players': len(leaderboard)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_new_profile(self, user_session):
        """Crée un nouveau profil gamification"""
        profile = {
            'user_session': user_session,
            'xp': 0,
            'total_xp': 0,
            'level': 1,
            'badges': [],
            'xp_history': [],
            'created_at': datetime.now().isoformat(),
            'current_week': self._get_current_week(),
            'weekly_progress': {},
            'completed_challenges': [],
            'stats': {
                'calculator_uses': 0,
                'trades_logged': 0,
                'ai_analyses': 0,
                'days_active': 0
            }
        }
        self._save_profile(user_session, profile)
        return profile
    
    def _update_level(self, profile):
        """Met à jour le niveau basé sur l'XP"""
        current_xp = profile['total_xp']
        level = 1
        
        for threshold in self.level_thresholds:
            if current_xp >= threshold:
                level += 1
            else:
                break
        
        profile['level'] = min(level - 1, len(self.level_thresholds))
        
        # Calcul du progrès vers le niveau suivant
        if profile['level'] < len(self.level_thresholds):
            current_threshold = self.level_thresholds[profile['level'] - 1] if profile['level'] > 1 else 0
            next_threshold = self.level_thresholds[profile['level']]
            progress = ((current_xp - current_threshold) / (next_threshold - current_threshold)) * 100
            profile['progress_to_next_level'] = min(100, max(0, progress))
            profile['xp_to_next_level'] = next_threshold - current_xp
        else:
            profile['progress_to_next_level'] = 100
            profile['xp_to_next_level'] = 0
        
        return profile
    
    def _check_trade_badges(self, profile, trade_data):
        """Vérifie les badges liés aux trades"""
        earned = []
        
        # Premier trade
        if profile['stats']['trades_logged'] == 0:
            earned.append('first_trade')
        
        # Gros gain
        if trade_data and trade_data.get('profit_loss', 0) > 500:
            earned.append('big_win')
        
        return earned
    
    def _check_calculator_badges(self, profile):
        """Vérifie les badges liés au calculateur"""
        earned = []
        
        if profile['stats']['calculator_uses'] >= 100:
            earned.append('calculator_expert')
        
        return earned
    
    def _check_ai_badges(self, profile):
        """Vérifie les badges liés à l'IA"""
        earned = []
        
        if profile['stats']['ai_analyses'] >= 10:
            earned.append('ai_student')
        
        return earned
    
    def _check_journal_badges(self, profile):
        """Vérifie les badges liés au journal"""
        earned = []
        
        if profile['stats']['trades_logged'] >= 50:
            earned.append('journal_keeper')
        
        return earned
    
    def _get_current_week(self):
        """Retourne l'identifiant de la semaine actuelle"""
        now = datetime.now()
        return f"{now.year}-W{now.isocalendar()[1]}"
    
    def _calculate_challenge_progress(self, user_session, challenge_id, profile):
        """Calcule le progrès d'un défi"""
        current_week = self._get_current_week()
        
        if challenge_id == 'consistency_challenge':
            # Compter les jours de trading cette semaine
            return min(100, profile['stats'].get('days_active_this_week', 0) * 20)
        elif challenge_id == 'journal_master':
            # Tous les trades documentés
            return min(100, profile['stats'].get('trades_documented_this_week', 0) * 10)
        elif challenge_id == 'learning_week':
            # Analyses IA cette semaine
            return min(100, profile['stats'].get('ai_uses_this_week', 0) * 33.33)
        
        return 0
    
    def _save_profile(self, user_session, profile):
        """Sauvegarde le profil gamification"""
        try:
            profile_file = f'data/gamification_{user_session}.json'
            os.makedirs(os.path.dirname(profile_file), exist_ok=True)
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde profil gamification: {e}")

# Instance globale
gamification = GamificationSystem()