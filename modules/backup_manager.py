"""
Gestionnaire de sauvegarde chiffrée pour MindTraderPro
Sauvegarde automatique et sécurisée des données utilisateur
"""

import os
import json
import gzip
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestionnaire de sauvegarde sécurisé"""
    
    def __init__(self):
        self.backup_dir = 'data/backups'
        self.max_backups = 30  # Garde 30 sauvegardes maximum
        self.backup_interval = 3600  # Sauvegarde toutes les heures
        self.encryption_key = self._get_encryption_key()
        
        # Création du dossier de sauvegarde
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, user_session: str, data_type: str, data: Dict) -> Dict:
        """Crée une sauvegarde chiffrée des données"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{user_session}_{data_type}_{timestamp}.bak"
            filepath = os.path.join(self.backup_dir, filename)
            
            # Prépare les données pour la sauvegarde
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'user_session': user_session,
                'data_type': data_type,
                'version': '1.0',
                'data': data,
                'checksum': self._calculate_checksum(data)
            }
            
            # Chiffre et compresse les données
            encrypted_data = self._encrypt_data(json.dumps(backup_data))
            compressed_data = gzip.compress(encrypted_data.encode())
            
            # Sauvegarde dans le fichier
            with open(filepath, 'wb') as f:
                f.write(compressed_data)
            
            # Nettoie les anciennes sauvegardes
            self._cleanup_old_backups(user_session, data_type)
            
            logger.info(f"Sauvegarde créée: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'size': os.path.getsize(filepath)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def restore_backup(self, filename: str) -> Dict:
        """Restaure une sauvegarde"""
        try:
            filepath = os.path.join(self.backup_dir, filename)
            
            if not os.path.exists(filepath):
                return {'success': False, 'error': 'Fichier de sauvegarde non trouvé'}
            
            # Lit et décompresse le fichier
            with open(filepath, 'rb') as f:
                compressed_data = f.read()
            
            decompressed_data = gzip.decompress(compressed_data).decode()
            decrypted_data = self._decrypt_data(decompressed_data)
            backup_data = json.loads(decrypted_data)
            
            # Vérifie l'intégrité des données
            if not self._verify_checksum(backup_data['data'], backup_data['checksum']):
                return {'success': False, 'error': 'Intégrité des données compromise'}
            
            logger.info(f"Sauvegarde restaurée: {filename}")
            
            return {
                'success': True,
                'data': backup_data['data'],
                'timestamp': backup_data['timestamp'],
                'data_type': backup_data['data_type']
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_backups(self, user_session: str = None, data_type: str = None) -> List[Dict]:
        """Liste les sauvegardes disponibles"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.bak'):
                    parts = filename.replace('.bak', '').split('_')
                    if len(parts) >= 4:
                        backup_user = parts[1]
                        backup_type = parts[2]
                        backup_time = parts[3] + '_' + parts[4] if len(parts) > 4 else parts[3]
                        
                        # Filtre selon les critères
                        if user_session and backup_user != user_session:
                            continue
                        if data_type and backup_type != data_type:
                            continue
                        
                        filepath = os.path.join(self.backup_dir, filename)
                        stat = os.stat(filepath)
                        
                        backups.append({
                            'filename': filename,
                            'user_session': backup_user,
                            'data_type': backup_type,
                            'timestamp': backup_time,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                        })
            
            # Trie par date de création (plus récent en premier)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des sauvegardes: {str(e)}")
            return []
    
    def auto_backup_user_data(self, user_session: str) -> Dict:
        """Sauvegarde automatique de toutes les données utilisateur"""
        try:
            results = {}
            
            # Sauvegarde des différents types de données
            data_types = [
                ('trades', f'data/trades_{user_session}.json'),
                ('settings', f'data/settings_{user_session}.json'),
                ('alerts', f'data/alerts_{user_session}.json'),
                ('journal', f'data/journal_{user_session}.json')
            ]
            
            for data_type, filepath in data_types:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    result = self.create_backup(user_session, data_type, data)
                    results[data_type] = result
            
            return {
                'success': True,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde automatique: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_encryption_key(self) -> str:
        """Génère ou récupère la clé de chiffrement"""
        key_file = 'data/.backup_key'
        
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        else:
            # Génère une nouvelle clé
            key = base64.b64encode(os.urandom(32)).decode()
            with open(key_file, 'w') as f:
                f.write(key)
            
            # Sécurise le fichier de clé
            os.chmod(key_file, 0o600)
            return key
    
    def _encrypt_data(self, data: str) -> str:
        """Chiffrement simple des données (à améliorer avec une vraie crypto)"""
        # Implémentation basique - en production, utilisez une vraie bibliothèque crypto
        key_bytes = self.encryption_key.encode()
        data_bytes = data.encode()
        
        encrypted = []
        for i, byte in enumerate(data_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            encrypted.append(byte ^ key_byte)
        
        return base64.b64encode(bytes(encrypted)).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffrement des données"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            key_bytes = self.encryption_key.encode()
            
            decrypted = []
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted.append(byte ^ key_byte)
            
            return bytes(decrypted).decode()
        except Exception:
            raise ValueError("Erreur de déchiffrement")
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Calcule le checksum des données"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _verify_checksum(self, data: Dict, expected_checksum: str) -> bool:
        """Vérifie l'intégrité des données"""
        calculated_checksum = self._calculate_checksum(data)
        return calculated_checksum == expected_checksum
    
    def _cleanup_old_backups(self, user_session: str, data_type: str):
        """Nettoie les anciennes sauvegardes"""
        try:
            backups = self.list_backups(user_session, data_type)
            
            if len(backups) > self.max_backups:
                # Supprime les plus anciennes
                for backup in backups[self.max_backups:]:
                    filepath = os.path.join(self.backup_dir, backup['filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.info(f"Ancienne sauvegarde supprimée: {backup['filename']}")
        
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {str(e)}")

# Instance globale
backup_manager = BackupManager()