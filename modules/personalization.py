"""
Personnalisation Avancée - Thèmes, interfaces et widgets personnalisables
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ThemeType(Enum):
    DARK_PROFESSIONAL = "dark_professional"
    LIGHT_CLEAN = "light_clean"
    TRADING_GREEN = "trading_green"
    CRYPTO_NEON = "crypto_neon"
    MINIMAL_WHITE = "minimal_white"
    HIGH_CONTRAST = "high_contrast"

class WidgetType(Enum):
    QUICK_CALCULATOR = "quick_calculator"
    PRICE_TICKER = "price_ticker"
    MENTAL_SCORE = "mental_score"
    RECENT_TRADES = "recent_trades"
    MARKET_NEWS = "market_news"
    ALERTS_SUMMARY = "alerts_summary"
    DAILY_GOALS = "daily_goals"
    PERFORMANCE_CHART = "performance_chart"

class LayoutType(Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    EXTENDED = "extended"
    MOBILE_OPTIMIZED = "mobile_optimized"

@dataclass
class UserTheme:
    """Thème utilisateur personnalisé"""
    theme_id: str
    user_session: str
    theme_type: ThemeType
    
    # Couleurs personnalisées
    primary_color: str
    secondary_color: str
    success_color: str
    warning_color: str
    danger_color: str
    background_color: str
    text_color: str
    
    # Options d'affichage
    font_size: str  # small, medium, large
    border_radius: str  # sharp, rounded, very_rounded
    shadow_intensity: str  # none, light, medium, strong
    animation_speed: str  # none, slow, normal, fast
    
    # Préférences spécifiques au trading
    profit_color: str
    loss_color: str
    chart_style: str  # candlestick, line, area
    
    created_at: datetime
    last_modified: datetime

@dataclass
class DashboardWidget:
    """Widget du tableau de bord"""
    widget_id: str
    user_session: str
    widget_type: WidgetType
    
    # Position et taille
    position_x: int
    position_y: int
    width: int
    height: int
    
    # Configuration
    title: str
    is_visible: bool
    refresh_interval: int  # secondes
    settings: Dict[str, Any]
    
    created_at: datetime

@dataclass
class UserInterface:
    """Interface utilisateur personnalisée"""
    user_session: str
    layout_type: LayoutType
    
    # Navigation
    sidebar_collapsed: bool
    navigation_style: str  # top, side, floating
    show_breadcrumbs: bool
    
    # Tableau de bord
    dashboard_widgets: List[str]  # IDs des widgets
    quick_access_buttons: List[str]
    
    # Préférences d'affichage
    show_tips: bool
    show_animations: bool
    compact_mode: bool
    
    # Notifications
    notification_position: str  # top-right, top-left, bottom-right, bottom-left
    notification_duration: int  # secondes
    
    last_updated: datetime

class PersonalizationManager:
    """Gestionnaire de personnalisation"""
    
    def __init__(self):
        self.user_themes = {}  # user_session -> UserTheme
        self.dashboard_widgets = {}  # user_session -> List[DashboardWidget]
        self.user_interfaces = {}  # user_session -> UserInterface
        self.available_themes = self._init_default_themes()
        self.available_widgets = self._init_default_widgets()
        
    def _init_default_themes(self) -> Dict[str, Dict]:
        """Initialise les thèmes par défaut"""
        return {
            "dark_professional": {
                "name": "🌙 Sombre Professionnel",
                "description": "Thème sombre élégant pour le trading professionnel",
                "primary_color": "#0d6efd",
                "secondary_color": "#6c757d",
                "success_color": "#198754",
                "warning_color": "#ffc107",
                "danger_color": "#dc3545",
                "background_color": "#1a1a1a",
                "text_color": "#ffffff",
                "profit_color": "#00d4aa",
                "loss_color": "#ff6b6b",
                "preview_image": "/static/themes/dark_professional.png"
            },
            "light_clean": {
                "name": "☀️ Clair et Propre",
                "description": "Interface claire et minimaliste",
                "primary_color": "#0056b3",
                "secondary_color": "#6c757d",
                "success_color": "#28a745",
                "warning_color": "#ffc107",
                "danger_color": "#dc3545",
                "background_color": "#ffffff",
                "text_color": "#212529",
                "profit_color": "#28a745",
                "loss_color": "#dc3545",
                "preview_image": "/static/themes/light_clean.png"
            },
            "trading_green": {
                "name": "💚 Vert Trading",
                "description": "Thème inspiré des terminaux de trading classiques",
                "primary_color": "#00ff88",
                "secondary_color": "#00cc6a",
                "success_color": "#00ff88",
                "warning_color": "#ffaa00",
                "danger_color": "#ff4444",
                "background_color": "#0a0a0a",
                "text_color": "#00ff88",
                "profit_color": "#00ff88",
                "loss_color": "#ff4444",
                "preview_image": "/static/themes/trading_green.png"
            },
            "crypto_neon": {
                "name": "⚡ Crypto Néon",
                "description": "Style futuriste pour les crypto-traders",
                "primary_color": "#ff0080",
                "secondary_color": "#8000ff",
                "success_color": "#00ff80",
                "warning_color": "#ffff00",
                "danger_color": "#ff0040",
                "background_color": "#0a0010",
                "text_color": "#ffffff",
                "profit_color": "#00ff80",
                "loss_color": "#ff0040",
                "preview_image": "/static/themes/crypto_neon.png"
            },
            "minimal_white": {
                "name": "⚪ Minimaliste Blanc",
                "description": "Design épuré et minimaliste",
                "primary_color": "#007bff",
                "secondary_color": "#f8f9fa",
                "success_color": "#28a745",
                "warning_color": "#ffc107",
                "danger_color": "#dc3545",
                "background_color": "#ffffff",
                "text_color": "#333333",
                "profit_color": "#007bff",
                "loss_color": "#6c757d",
                "preview_image": "/static/themes/minimal_white.png"
            }
        }
    
    def _init_default_widgets(self) -> Dict[str, Dict]:
        """Initialise les widgets disponibles"""
        return {
            "quick_calculator": {
                "name": "🧮 Calculateur Rapide",
                "description": "Calcul rapide de position sans quitter le tableau de bord",
                "default_size": {"width": 300, "height": 250},
                "settings": ["pair_symbol", "risk_percent", "auto_refresh"]
            },
            "price_ticker": {
                "name": "📊 Ticker de Prix",
                "description": "Affichage en temps réel des prix de vos paires préférées",
                "default_size": {"width": 280, "height": 150},
                "settings": ["watched_pairs", "update_frequency", "show_change"]
            },
            "mental_score": {
                "name": "🧠 Score Mental",
                "description": "Votre score mental actuel et recommandations",
                "default_size": {"width": 250, "height": 180},
                "settings": ["show_recommendations", "auto_update"]
            },
            "recent_trades": {
                "name": "📈 Trades Récents",
                "description": "Aperçu de vos derniers trades du journal",
                "default_size": {"width": 350, "height": 200},
                "settings": ["trade_count", "show_pnl", "show_notes"]
            },
            "alerts_summary": {
                "name": "🔔 Résumé Alertes",
                "description": "Alertes actives et déclenchées récemment",
                "default_size": {"width": 300, "height": 160},
                "settings": ["show_triggered", "alert_types"]
            },
            "daily_goals": {
                "name": "🎯 Objectifs Quotidiens",
                "description": "Vos objectifs du jour et progression",
                "default_size": {"width": 280, "height": 200},
                "settings": ["goal_types", "show_progress"]
            },
            "performance_chart": {
                "name": "📊 Graphique Performance",
                "description": "Mini-graphique de votre performance",
                "default_size": {"width": 400, "height": 250},
                "settings": ["chart_period", "chart_type", "show_drawdown"]
            },
            "market_news": {
                "name": "📰 Actualités Marché",
                "description": "Dernières nouvelles financières",
                "default_size": {"width": 350, "height": 300},
                "settings": ["news_sources", "keywords", "update_frequency"]
            }
        }
    
    def apply_theme(self, user_session: str, theme_type: str, custom_settings: Dict = None) -> Dict:
        """Applique un thème à l'interface utilisateur"""
        
        if theme_type not in self.available_themes:
            return {
                'success': False,
                'error': 'Thème non disponible'
            }
        
        theme_config = self.available_themes[theme_type].copy()
        
        # Appliquer les personnalisations
        if custom_settings:
            theme_config.update(custom_settings)
        
        user_theme = UserTheme(
            theme_id=f"theme_{user_session}_{int(datetime.now().timestamp())}",
            user_session=user_session,
            theme_type=ThemeType(theme_type),
            primary_color=theme_config.get('primary_color', '#0d6efd'),
            secondary_color=theme_config.get('secondary_color', '#6c757d'),
            success_color=theme_config.get('success_color', '#198754'),
            warning_color=theme_config.get('warning_color', '#ffc107'),
            danger_color=theme_config.get('danger_color', '#dc3545'),
            background_color=theme_config.get('background_color', '#ffffff'),
            text_color=theme_config.get('text_color', '#212529'),
            font_size=custom_settings.get('font_size', 'medium') if custom_settings else 'medium',
            border_radius=custom_settings.get('border_radius', 'rounded') if custom_settings else 'rounded',
            shadow_intensity=custom_settings.get('shadow_intensity', 'medium') if custom_settings else 'medium',
            animation_speed=custom_settings.get('animation_speed', 'normal') if custom_settings else 'normal',
            profit_color=theme_config.get('profit_color', '#198754'),
            loss_color=theme_config.get('loss_color', '#dc3545'),
            chart_style=custom_settings.get('chart_style', 'candlestick') if custom_settings else 'candlestick',
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        
        self.user_themes[user_session] = user_theme
        
        return {
            'success': True,
            'theme': self._theme_to_dict(user_theme),
            'css_variables': self._generate_css_variables(user_theme)
        }
    
    def add_dashboard_widget(self, user_session: str, widget_data: Dict) -> Dict:
        """Ajoute un widget au tableau de bord"""
        
        widget_type = widget_data.get('widget_type')
        if widget_type not in self.available_widgets:
            return {
                'success': False,
                'error': 'Type de widget non disponible'
            }
        
        widget_config = self.available_widgets[widget_type]
        default_size = widget_config['default_size']
        
        widget = DashboardWidget(
            widget_id=f"widget_{user_session}_{int(datetime.now().timestamp())}",
            user_session=user_session,
            widget_type=WidgetType(widget_type),
            position_x=widget_data.get('position_x', 0),
            position_y=widget_data.get('position_y', 0),
            width=widget_data.get('width', default_size['width']),
            height=widget_data.get('height', default_size['height']),
            title=widget_data.get('title', widget_config['name']),
            is_visible=True,
            refresh_interval=widget_data.get('refresh_interval', 30),
            settings=widget_data.get('settings', {}),
            created_at=datetime.now()
        )
        
        if user_session not in self.dashboard_widgets:
            self.dashboard_widgets[user_session] = []
        
        self.dashboard_widgets[user_session].append(widget)
        
        return {
            'success': True,
            'widget': self._widget_to_dict(widget)
        }
    
    def customize_interface(self, user_session: str, interface_settings: Dict) -> Dict:
        """Personnalise l'interface utilisateur"""
        
        interface = UserInterface(
            user_session=user_session,
            layout_type=LayoutType(interface_settings.get('layout_type', 'standard')),
            sidebar_collapsed=interface_settings.get('sidebar_collapsed', False),
            navigation_style=interface_settings.get('navigation_style', 'side'),
            show_breadcrumbs=interface_settings.get('show_breadcrumbs', True),
            dashboard_widgets=interface_settings.get('dashboard_widgets', []),
            quick_access_buttons=interface_settings.get('quick_access_buttons', [
                'calculator', 'journal', 'alerts'
            ]),
            show_tips=interface_settings.get('show_tips', True),
            show_animations=interface_settings.get('show_animations', True),
            compact_mode=interface_settings.get('compact_mode', False),
            notification_position=interface_settings.get('notification_position', 'top-right'),
            notification_duration=interface_settings.get('notification_duration', 4),
            last_updated=datetime.now()
        )
        
        self.user_interfaces[user_session] = interface
        
        return {
            'success': True,
            'interface': self._interface_to_dict(interface)
        }
    
    def get_user_personalization(self, user_session: str) -> Dict:
        """Récupère toute la personnalisation d'un utilisateur"""
        
        theme = self.user_themes.get(user_session)
        widgets = self.dashboard_widgets.get(user_session, [])
        interface = self.user_interfaces.get(user_session)
        
        return {
            'theme': self._theme_to_dict(theme) if theme else None,
            'widgets': [self._widget_to_dict(w) for w in widgets],
            'interface': self._interface_to_dict(interface) if interface else None,
            'css_variables': self._generate_css_variables(theme) if theme else {}
        }
    
    def _theme_to_dict(self, theme: UserTheme) -> Dict:
        """Convertit un thème en dictionnaire"""
        return {
            'theme_id': theme.theme_id,
            'theme_type': theme.theme_type.value,
            'colors': {
                'primary': theme.primary_color,
                'secondary': theme.secondary_color,
                'success': theme.success_color,
                'warning': theme.warning_color,
                'danger': theme.danger_color,
                'background': theme.background_color,
                'text': theme.text_color,
                'profit': theme.profit_color,
                'loss': theme.loss_color
            },
            'display': {
                'font_size': theme.font_size,
                'border_radius': theme.border_radius,
                'shadow_intensity': theme.shadow_intensity,
                'animation_speed': theme.animation_speed,
                'chart_style': theme.chart_style
            },
            'created_at': theme.created_at.isoformat(),
            'last_modified': theme.last_modified.isoformat()
        }
    
    def _widget_to_dict(self, widget: DashboardWidget) -> Dict:
        """Convertit un widget en dictionnaire"""
        return {
            'widget_id': widget.widget_id,
            'widget_type': widget.widget_type.value,
            'position': {
                'x': widget.position_x,
                'y': widget.position_y,
                'width': widget.width,
                'height': widget.height
            },
            'title': widget.title,
            'is_visible': widget.is_visible,
            'refresh_interval': widget.refresh_interval,
            'settings': widget.settings,
            'created_at': widget.created_at.isoformat()
        }
    
    def _interface_to_dict(self, interface: UserInterface) -> Dict:
        """Convertit une interface en dictionnaire"""
        return {
            'layout_type': interface.layout_type.value,
            'navigation': {
                'sidebar_collapsed': interface.sidebar_collapsed,
                'navigation_style': interface.navigation_style,
                'show_breadcrumbs': interface.show_breadcrumbs
            },
            'dashboard': {
                'widgets': interface.dashboard_widgets,
                'quick_access_buttons': interface.quick_access_buttons
            },
            'display': {
                'show_tips': interface.show_tips,
                'show_animations': interface.show_animations,
                'compact_mode': interface.compact_mode
            },
            'notifications': {
                'position': interface.notification_position,
                'duration': interface.notification_duration
            },
            'last_updated': interface.last_updated.isoformat()
        }
    
    def _generate_css_variables(self, theme: UserTheme) -> Dict[str, str]:
        """Génère les variables CSS pour le thème"""
        
        return {
            '--bs-primary': theme.primary_color,
            '--bs-secondary': theme.secondary_color,
            '--bs-success': theme.success_color,
            '--bs-warning': theme.warning_color,
            '--bs-danger': theme.danger_color,
            '--bs-background': theme.background_color,
            '--bs-text': theme.text_color,
            '--trading-profit': theme.profit_color,
            '--trading-loss': theme.loss_color,
            '--font-size-base': {
                'small': '0.875rem',
                'medium': '1rem',
                'large': '1.125rem'
            }.get(theme.font_size, '1rem'),
            '--border-radius': {
                'sharp': '0',
                'rounded': '0.375rem',
                'very_rounded': '1rem'
            }.get(theme.border_radius, '0.375rem'),
            '--box-shadow': {
                'none': 'none',
                'light': '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                'medium': '0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                'strong': '0 1rem 3rem rgba(0, 0, 0, 0.175)'
            }.get(theme.shadow_intensity, '0 0.5rem 1rem rgba(0, 0, 0, 0.15)'),
            '--animation-duration': {
                'none': '0s',
                'slow': '0.5s',
                'normal': '0.3s',
                'fast': '0.15s'
            }.get(theme.animation_speed, '0.3s')
        }
    
    def get_available_themes(self) -> List[Dict]:
        """Récupère la liste des thèmes disponibles"""
        return [
            {
                'id': theme_id,
                'name': theme_data['name'],
                'description': theme_data['description'],
                'preview': theme_data.get('preview_image', ''),
                'colors': {
                    'primary': theme_data['primary_color'],
                    'background': theme_data['background_color'],
                    'text': theme_data['text_color']
                }
            }
            for theme_id, theme_data in self.available_themes.items()
        ]
    
    def get_available_widgets(self) -> List[Dict]:
        """Récupère la liste des widgets disponibles"""
        return [
            {
                'id': widget_id,
                'name': widget_data['name'],
                'description': widget_data['description'],
                'default_size': widget_data['default_size'],
                'settings': widget_data['settings']
            }
            for widget_id, widget_data in self.available_widgets.items()
        ]
    
    def remove_widget(self, user_session: str, widget_id: str) -> bool:
        """Supprime un widget du tableau de bord"""
        
        if user_session not in self.dashboard_widgets:
            return False
        
        widgets = self.dashboard_widgets[user_session]
        self.dashboard_widgets[user_session] = [
            w for w in widgets if w.widget_id != widget_id
        ]
        
        return True
    
    def update_widget_position(self, user_session: str, widget_id: str, position: Dict) -> bool:
        """Met à jour la position d'un widget"""
        
        widgets = self.dashboard_widgets.get(user_session, [])
        
        for widget in widgets:
            if widget.widget_id == widget_id:
                widget.position_x = position.get('x', widget.position_x)
                widget.position_y = position.get('y', widget.position_y)
                widget.width = position.get('width', widget.width)
                widget.height = position.get('height', widget.height)
                return True
        
        return False
    
    def create_custom_theme(self, user_session: str, theme_name: str, colors: Dict, display_options: Dict) -> Dict:
        """Crée un thème personnalisé"""
        
        custom_theme = UserTheme(
            theme_id=f"custom_{user_session}_{int(datetime.now().timestamp())}",
            user_session=user_session,
            theme_type=ThemeType.DARK_PROFESSIONAL,  # Base
            primary_color=colors.get('primary', '#0d6efd'),
            secondary_color=colors.get('secondary', '#6c757d'),
            success_color=colors.get('success', '#198754'),
            warning_color=colors.get('warning', '#ffc107'),
            danger_color=colors.get('danger', '#dc3545'),
            background_color=colors.get('background', '#ffffff'),
            text_color=colors.get('text', '#212529'),
            font_size=display_options.get('font_size', 'medium'),
            border_radius=display_options.get('border_radius', 'rounded'),
            shadow_intensity=display_options.get('shadow_intensity', 'medium'),
            animation_speed=display_options.get('animation_speed', 'normal'),
            profit_color=colors.get('profit', '#198754'),
            loss_color=colors.get('loss', '#dc3545'),
            chart_style=display_options.get('chart_style', 'candlestick'),
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        
        self.user_themes[user_session] = custom_theme
        
        return {
            'success': True,
            'theme': self._theme_to_dict(custom_theme),
            'css_variables': self._generate_css_variables(custom_theme)
        }

# Instance globale du gestionnaire de personnalisation
personalization_manager = PersonalizationManager()