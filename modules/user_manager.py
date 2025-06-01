"""
Gestionnaire d'utilisateurs - Trading Calculator Pro
Gestion des sessions et données utilisateur en JSON
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

class UserManager:
    """Gestionnaire d'utilisateurs avec stockage JSON"""
    
    def __init__(self, data_folder: str):
        """Initialise le gestionnaire d'utilisateurs"""
        self.data_folder = data_folder
        self.users_file = os.path.join(data_folder, 'users.json')
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """Crée les fichiers de données s'ils n'existent pas"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def ensure_user_exists(self, user_id: str):
        """S'assure qu'un utilisateur existe dans les données"""
        users = self.load_users()
        
        if user_id not in users:
            users[user_id] = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'settings': {
                    'theme': 'dark',
                    'language': 'fr',
                    'notifications': True
                },
                'trades': [],
                'analytics': {
                    'total_calculations': 0,
                    'total_trades': 0,
                    'win_rate': 0.0
                }
            }
            self.save_users(users)
        else:
            # Mettre à jour la dernière activité
            users[user_id]['last_active'] = datetime.now().isoformat()
            self.save_users(users)
    
    def load_users(self) -> Dict[str, Any]:
        """Charge les données utilisateurs depuis JSON"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, users: Dict[str, Any]):
        """Sauvegarde les données utilisateurs en JSON"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Récupère les données d'un utilisateur"""
        users = self.load_users()
        return users.get(user_id, {})
    
    def update_user(self, user_id: str, data: Dict[str, Any]):
        """Met à jour les données d'un utilisateur"""
        users = self.load_users()
        if user_id in users:
            users[user_id].update(data)
            self.save_users(users)