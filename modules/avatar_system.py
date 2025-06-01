"""
Système d'Avatars Personnalisés - MindTraderPro
Choix d'avatars et contours (gratuits/premium/lifetime)
"""
import json
import os
from datetime import datetime

class AvatarSystem:
    def __init__(self):
        self.avatars_config_file = 'data/avatars_config.json'
        self.user_avatars_file = 'data/user_avatars.json'
        
        # Configuration des avatars disponibles
        self.avatar_library = {
            'free': {
                'basic_trader': {
                    'name': 'Trader Classique',
                    'svg_path': '/static/avatars/basic_trader.svg',
                    'category': 'professional',
                    'description': 'Avatar professionnel standard'
                },
                'casual_trader': {
                    'name': 'Trader Décontracté',
                    'svg_path': '/static/avatars/casual_trader.svg',
                    'category': 'casual',
                    'description': 'Style décontracté et moderne'
                },
                'female_trader': {
                    'name': 'Trader Femme',
                    'svg_path': '/static/avatars/female_trader.svg',
                    'category': 'professional',
                    'description': 'Avatar professionnel féminin'
                },
                'young_trader': {
                    'name': 'Jeune Trader',
                    'svg_path': '/static/avatars/young_trader.svg',
                    'category': 'modern',
                    'description': 'Style jeune et dynamique'
                }
            },
            'premium': {
                'luxury_trader': {
                    'name': 'Trader de Luxe',
                    'svg_path': '/static/avatars/luxury_trader.svg',
                    'category': 'luxury',
                    'description': 'Avatar premium avec costume de luxe'
                },
                'crypto_trader': {
                    'name': 'Crypto Trader',
                    'svg_path': '/static/avatars/crypto_trader.svg',
                    'category': 'modern',
                    'description': 'Style futuriste crypto'
                },
                'executive_trader': {
                    'name': 'Trader Exécutif',
                    'svg_path': '/static/avatars/executive_trader.svg',
                    'category': 'executive',
                    'description': 'Look de directeur financier'
                },
                'international_trader': {
                    'name': 'Trader International',
                    'svg_path': '/static/avatars/international_trader.svg',
                    'category': 'international',
                    'description': 'Style cosmopolite'
                }
            },
            'lifetime': {
                'golden_trader': {
                    'name': 'Trader d\'Or',
                    'svg_path': '/static/avatars/golden_trader.svg',
                    'category': 'exclusive',
                    'description': 'Avatar exclusif doré'
                },
                'diamond_trader': {
                    'name': 'Trader Diamant',
                    'svg_path': '/static/avatars/diamond_trader.svg',
                    'category': 'exclusive',
                    'description': 'Avatar ultra-premium diamant'
                },
                'master_trader': {
                    'name': 'Maître Trader',
                    'svg_path': '/static/avatars/master_trader.svg',
                    'category': 'master',
                    'description': 'Avatar de maître légendaire'
                }
            }
        }
        
        # Contours/bordures disponibles
        self.border_library = {
            'free': {
                'simple': {
                    'name': 'Bordure Simple',
                    'css_class': 'avatar-border-simple',
                    'color': '#6c757d'
                },
                'classic': {
                    'name': 'Bordure Classique',
                    'css_class': 'avatar-border-classic',
                    'color': '#007bff'
                }
            },
            'premium': {
                'gradient': {
                    'name': 'Bordure Dégradé',
                    'css_class': 'avatar-border-gradient',
                    'gradient': 'linear-gradient(45deg, #667eea, #764ba2)'
                },
                'neon': {
                    'name': 'Bordure Néon',
                    'css_class': 'avatar-border-neon',
                    'color': '#00ffff',
                    'glow': True
                },
                'gold': {
                    'name': 'Bordure Or',
                    'css_class': 'avatar-border-gold',
                    'color': '#ffd700',
                    'metallic': True
                }
            },
            'lifetime': {
                'diamond': {
                    'name': 'Bordure Diamant',
                    'css_class': 'avatar-border-diamond',
                    'gradient': 'linear-gradient(45deg, #ffffff, #e3f2fd, #ffffff)',
                    'sparkle': True
                },
                'royal': {
                    'name': 'Bordure Royale',
                    'css_class': 'avatar-border-royal',
                    'gradient': 'linear-gradient(45deg, #4a00e0, #8e2de2)',
                    'crown': True
                },
                'master': {
                    'name': 'Bordure Maître',
                    'css_class': 'avatar-border-master',
                    'gradient': 'linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4ecdc4)',
                    'animated': True
                }
            }
        }
    
    def get_available_avatars(self, user_plan='free'):
        """Récupère les avatars disponibles selon le plan utilisateur"""
        try:
            available_avatars = {}
            
            # Toujours inclure les avatars gratuits
            available_avatars.update(self.avatar_library['free'])
            
            # Ajouter selon le plan
            if user_plan in ['premium', 'lifetime']:
                available_avatars.update(self.avatar_library['premium'])
            
            if user_plan == 'lifetime':
                available_avatars.update(self.avatar_library['lifetime'])
            
            return {
                'success': True,
                'avatars': available_avatars,
                'total_available': len(available_avatars),
                'user_plan': user_plan
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération avatars: {str(e)}'}
    
    def get_available_borders(self, user_plan='free'):
        """Récupère les bordures disponibles selon le plan utilisateur"""
        try:
            available_borders = {}
            
            # Toujours inclure les bordures gratuites
            available_borders.update(self.border_library['free'])
            
            # Ajouter selon le plan
            if user_plan in ['premium', 'lifetime']:
                available_borders.update(self.border_library['premium'])
            
            if user_plan == 'lifetime':
                available_borders.update(self.border_library['lifetime'])
            
            return {
                'success': True,
                'borders': available_borders,
                'total_available': len(available_borders),
                'user_plan': user_plan
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération bordures: {str(e)}'}
    
    def set_user_avatar(self, user_session, avatar_id, border_id=None, user_plan='free'):
        """Configure l'avatar d'un utilisateur"""
        try:
            # Vérifier si l'avatar est disponible pour ce plan
            available_avatars = self.get_available_avatars(user_plan)
            if not available_avatars['success'] or avatar_id not in available_avatars['avatars']:
                return {'success': False, 'error': 'Avatar non disponible pour votre plan'}
            
            # Vérifier la bordure si spécifiée
            if border_id:
                available_borders = self.get_available_borders(user_plan)
                if not available_borders['success'] or border_id not in available_borders['borders']:
                    return {'success': False, 'error': 'Bordure non disponible pour votre plan'}
            
            # Charger les configurations utilisateur
            user_avatars = self._load_user_avatars()
            
            # Mettre à jour ou créer la configuration
            user_config = {
                'user_session': user_session,
                'avatar_id': avatar_id,
                'border_id': border_id,
                'updated_at': datetime.now().isoformat(),
                'user_plan': user_plan
            }
            
            # Supprimer l'ancienne config si elle existe
            user_avatars = [ua for ua in user_avatars if ua['user_session'] != user_session]
            user_avatars.append(user_config)
            
            self._save_user_avatars(user_avatars)
            
            return {
                'success': True,
                'message': 'Avatar mis à jour avec succès',
                'avatar_config': user_config
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur configuration avatar: {str(e)}'}
    
    def get_user_avatar(self, user_session):
        """Récupère la configuration avatar d'un utilisateur"""
        try:
            user_avatars = self._load_user_avatars()
            
            user_config = next(
                (ua for ua in user_avatars if ua['user_session'] == user_session),
                None
            )
            
            if not user_config:
                # Configuration par défaut
                user_config = {
                    'user_session': user_session,
                    'avatar_id': 'basic_trader',
                    'border_id': 'simple',
                    'user_plan': 'free'
                }
            
            # Enrichir avec les détails de l'avatar et de la bordure
            avatar_details = self._get_avatar_details(user_config['avatar_id'])
            border_details = self._get_border_details(user_config['border_id']) if user_config.get('border_id') else None
            
            return {
                'success': True,
                'config': user_config,
                'avatar_details': avatar_details,
                'border_details': border_details
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération avatar: {str(e)}'}
    
    def generate_avatar_html(self, user_session, size='medium'):
        """Génère le HTML pour afficher l'avatar d'un utilisateur"""
        try:
            avatar_data = self.get_user_avatar(user_session)
            if not avatar_data['success']:
                return {'success': False, 'error': avatar_data['error']}
            
            config = avatar_data['config']
            avatar_details = avatar_data['avatar_details']
            border_details = avatar_data['border_details']
            
            # Tailles disponibles
            size_classes = {
                'small': 'avatar-small',  # 32px
                'medium': 'avatar-medium',  # 48px
                'large': 'avatar-large',  # 64px
                'xl': 'avatar-xl'  # 96px
            }
            
            size_class = size_classes.get(size, 'avatar-medium')
            
            # Construction du HTML
            border_class = border_details['css_class'] if border_details else ''
            
            html = f"""
            <div class="user-avatar {size_class} {border_class}" 
                 data-user="{user_session}" 
                 data-plan="{config['user_plan']}"
                 title="{avatar_details['name']}">
                <img src="{avatar_details['svg_path']}" 
                     alt="{avatar_details['name']}" 
                     class="avatar-image">
                {self._generate_border_effects(border_details) if border_details else ''}
            </div>
            """
            
            return {
                'success': True,
                'html': html,
                'css_classes': f"{size_class} {border_class}".strip()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération HTML: {str(e)}'}
    
    def get_avatar_showcase(self):
        """Récupère tous les avatars pour la vitrine"""
        try:
            showcase = {
                'free': {
                    'title': 'Avatars Gratuits',
                    'avatars': self.avatar_library['free'],
                    'borders': self.border_library['free']
                },
                'premium': {
                    'title': 'Avatars Premium',
                    'avatars': self.avatar_library['premium'],
                    'borders': self.border_library['premium'],
                    'price': '€9.99/mois'
                },
                'lifetime': {
                    'title': 'Avatars Exclusifs',
                    'avatars': self.avatar_library['lifetime'],
                    'borders': self.border_library['lifetime'],
                    'price': '€149 - Accès à vie'
                }
            }
            
            return {
                'success': True,
                'showcase': showcase,
                'total_avatars': sum(len(tier['avatars']) for tier in showcase.values()),
                'total_borders': sum(len(tier['borders']) for tier in showcase.values())
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur vitrine: {str(e)}'}
    
    def generate_avatar_css(self):
        """Génère le CSS pour tous les avatars et bordures"""
        css = """
        /* Tailles d'avatars */
        .avatar-small { width: 32px; height: 32px; }
        .avatar-medium { width: 48px; height: 48px; }
        .avatar-large { width: 64px; height: 64px; }
        .avatar-xl { width: 96px; height: 96px; }
        
        /* Base avatar */
        .user-avatar {
            position: relative;
            border-radius: 50%;
            overflow: hidden;
            display: inline-block;
            transition: all 0.3s ease;
        }
        
        .avatar-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* Bordures gratuites */
        .avatar-border-simple {
            border: 2px solid #6c757d;
        }
        
        .avatar-border-classic {
            border: 3px solid #007bff;
            box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
        }
        
        /* Bordures premium */
        .avatar-border-gradient {
            border: 3px solid transparent;
            background: linear-gradient(45deg, #667eea, #764ba2);
            background-clip: padding-box;
        }
        
        .avatar-border-neon {
            border: 2px solid #00ffff;
            box-shadow: 0 0 20px #00ffff, inset 0 0 20px rgba(0, 255, 255, 0.1);
            animation: neon-pulse 2s infinite alternate;
        }
        
        .avatar-border-gold {
            border: 3px solid #ffd700;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
            background: radial-gradient(circle at 30% 30%, rgba(255, 215, 0, 0.2), transparent);
        }
        
        /* Bordures lifetime */
        .avatar-border-diamond {
            border: 3px solid transparent;
            background: linear-gradient(45deg, #ffffff, #e3f2fd, #ffffff);
            background-clip: padding-box;
            animation: diamond-sparkle 3s infinite;
        }
        
        .avatar-border-royal {
            border: 4px solid transparent;
            background: linear-gradient(45deg, #4a00e0, #8e2de2);
            background-clip: padding-box;
            position: relative;
        }
        
        .avatar-border-royal::before {
            content: '👑';
            position: absolute;
            top: -10px;
            right: -5px;
            font-size: 16px;
        }
        
        .avatar-border-master {
            border: 4px solid transparent;
            background: linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4ecdc4);
            background-clip: padding-box;
            animation: master-rainbow 4s infinite linear;
        }
        
        /* Animations */
        @keyframes neon-pulse {
            from { box-shadow: 0 0 20px #00ffff, inset 0 0 20px rgba(0, 255, 255, 0.1); }
            to { box-shadow: 0 0 30px #00ffff, inset 0 0 30px rgba(0, 255, 255, 0.2); }
        }
        
        @keyframes diamond-sparkle {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); filter: brightness(1.2); }
        }
        
        @keyframes master-rainbow {
            0% { filter: hue-rotate(0deg); }
            100% { filter: hue-rotate(360deg); }
        }
        
        /* Hover effects */
        .user-avatar:hover {
            transform: scale(1.1);
            z-index: 10;
        }
        """
        
        return css
    
    def _get_avatar_details(self, avatar_id):
        """Récupère les détails d'un avatar"""
        for tier in self.avatar_library.values():
            if avatar_id in tier:
                return tier[avatar_id]
        
        # Fallback
        return self.avatar_library['free']['basic_trader']
    
    def _get_border_details(self, border_id):
        """Récupère les détails d'une bordure"""
        for tier in self.border_library.values():
            if border_id in tier:
                return tier[border_id]
        
        return None
    
    def _generate_border_effects(self, border_details):
        """Génère les effets spéciaux pour les bordures"""
        if not border_details:
            return ""
        
        effects = ""
        
        if border_details.get('sparkle'):
            effects += '<div class="sparkle-effect"></div>'
        
        if border_details.get('glow'):
            effects += '<div class="glow-effect"></div>'
        
        return effects
    
    def _load_user_avatars(self):
        """Charge les configurations d'avatars utilisateur"""
        try:
            if os.path.exists(self.user_avatars_file):
                with open(self.user_avatars_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_user_avatars(self, user_avatars):
        """Sauvegarde les configurations d'avatars"""
        try:
            os.makedirs(os.path.dirname(self.user_avatars_file), exist_ok=True)
            with open(self.user_avatars_file, 'w', encoding='utf-8') as f:
                json.dump(user_avatars, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde avatars: {e}")

# Instance globale
avatar_system = AvatarSystem()