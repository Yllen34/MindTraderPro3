"""
Système de Vote de Fonctionnalités - MindTraderPro
Interface pour proposer, voter et gérer les demandes de fonctionnalités
"""
import json
import os
from datetime import datetime
from uuid import uuid4

class FeatureVotingSystem:
    def __init__(self):
        self.features_file = 'data/feature_requests.json'
        self.votes_file = 'data/feature_votes.json'
        self.status_options = ['pending', 'under_review', 'approved', 'in_development', 'completed', 'rejected']
        
    def submit_feature_request(self, user_session, title, description, category=None):
        """Soumet une nouvelle demande de fonctionnalité"""
        try:
            feature_id = str(uuid4())
            
            feature_request = {
                'id': feature_id,
                'title': title.strip(),
                'description': description.strip(),
                'category': category or 'general',
                'submitted_by': user_session,
                'submitted_at': datetime.now().isoformat(),
                'status': 'pending',
                'votes': 0,
                'admin_notes': '',
                'priority': 'medium',
                'estimated_effort': 'unknown',
                'tags': []
            }
            
            # Validation des données
            if len(feature_request['title']) < 5:
                return {'success': False, 'error': 'Le titre doit contenir au moins 5 caractères'}
            
            if len(feature_request['description']) < 20:
                return {'success': False, 'error': 'La description doit contenir au moins 20 caractères'}
            
            # Sauvegarde
            features = self._load_features()
            features.append(feature_request)
            self._save_features(features)
            
            return {
                'success': True,
                'feature_id': feature_id,
                'message': 'Demande de fonctionnalité soumise avec succès'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la soumission: {str(e)}'}
    
    def vote_for_feature(self, user_session, feature_id, vote_type='up'):
        """Vote pour une fonctionnalité (up/down)"""
        try:
            features = self._load_features()
            votes = self._load_votes()
            
            # Vérifier si la fonctionnalité existe
            feature = next((f for f in features if f['id'] == feature_id), None)
            if not feature:
                return {'success': False, 'error': 'Fonctionnalité non trouvée'}
            
            # Vérifier si l'utilisateur a déjà voté
            existing_vote = next(
                (v for v in votes if v['user_session'] == user_session and v['feature_id'] == feature_id), 
                None
            )
            
            if existing_vote:
                # Modifier le vote existant
                if existing_vote['vote_type'] == vote_type:
                    return {'success': False, 'error': 'Vous avez déjà voté de cette façon'}
                
                old_vote = existing_vote['vote_type']
                existing_vote['vote_type'] = vote_type
                existing_vote['voted_at'] = datetime.now().isoformat()
                
                # Ajuster le compteur
                if old_vote == 'up' and vote_type == 'down':
                    feature['votes'] -= 2
                elif old_vote == 'down' and vote_type == 'up':
                    feature['votes'] += 2
                
            else:
                # Nouveau vote
                new_vote = {
                    'id': str(uuid4()),
                    'user_session': user_session,
                    'feature_id': feature_id,
                    'vote_type': vote_type,
                    'voted_at': datetime.now().isoformat()
                }
                votes.append(new_vote)
                
                # Ajuster le compteur
                if vote_type == 'up':
                    feature['votes'] += 1
                else:
                    feature['votes'] -= 1
            
            # Sauvegardes
            self._save_features(features)
            self._save_votes(votes)
            
            return {
                'success': True,
                'new_vote_count': feature['votes'],
                'message': f'Vote {"positif" if vote_type == "up" else "négatif"} enregistré'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors du vote: {str(e)}'}
    
    def get_features_list(self, status_filter=None, sort_by='votes', limit=50):
        """Récupère la liste des fonctionnalités avec filtres"""
        try:
            features = self._load_features()
            
            # Filtrer par statut
            if status_filter and status_filter in self.status_options:
                features = [f for f in features if f['status'] == status_filter]
            
            # Trier
            if sort_by == 'votes':
                features.sort(key=lambda x: x['votes'], reverse=True)
            elif sort_by == 'date':
                features.sort(key=lambda x: x['submitted_at'], reverse=True)
            elif sort_by == 'status':
                features.sort(key=lambda x: x['status'])
            
            # Limiter
            features = features[:limit]
            
            # Enrichir avec les informations de vote utilisateur si possible
            return {
                'success': True,
                'features': features,
                'total_count': len(features),
                'available_statuses': self.status_options
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la récupération: {str(e)}'}
    
    def get_feature_details(self, feature_id, user_session=None):
        """Récupère les détails d'une fonctionnalité"""
        try:
            features = self._load_features()
            feature = next((f for f in features if f['id'] == feature_id), None)
            
            if not feature:
                return {'success': False, 'error': 'Fonctionnalité non trouvée'}
            
            # Ajouter les informations de vote de l'utilisateur
            user_vote = None
            if user_session:
                votes = self._load_votes()
                user_vote_obj = next(
                    (v for v in votes if v['user_session'] == user_session and v['feature_id'] == feature_id),
                    None
                )
                if user_vote_obj:
                    user_vote = user_vote_obj['vote_type']
            
            # Statistiques des votes
            votes = self._load_votes()
            feature_votes = [v for v in votes if v['feature_id'] == feature_id]
            vote_stats = {
                'total_votes': len(feature_votes),
                'upvotes': len([v for v in feature_votes if v['vote_type'] == 'up']),
                'downvotes': len([v for v in feature_votes if v['vote_type'] == 'down']),
                'score': feature['votes']
            }
            
            return {
                'success': True,
                'feature': feature,
                'user_vote': user_vote,
                'vote_stats': vote_stats
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la récupération: {str(e)}'}
    
    def update_feature_status(self, feature_id, new_status, admin_notes=None, priority=None):
        """Met à jour le statut d'une fonctionnalité (admin uniquement)"""
        try:
            if new_status not in self.status_options:
                return {'success': False, 'error': 'Statut invalide'}
            
            features = self._load_features()
            feature = next((f for f in features if f['id'] == feature_id), None)
            
            if not feature:
                return {'success': False, 'error': 'Fonctionnalité non trouvée'}
            
            old_status = feature['status']
            feature['status'] = new_status
            feature['last_updated'] = datetime.now().isoformat()
            
            if admin_notes:
                feature['admin_notes'] = admin_notes
            
            if priority and priority in ['low', 'medium', 'high', 'critical']:
                feature['priority'] = priority
            
            # Historique des changements
            if 'status_history' not in feature:
                feature['status_history'] = []
            
            feature['status_history'].append({
                'from_status': old_status,
                'to_status': new_status,
                'changed_at': datetime.now().isoformat(),
                'notes': admin_notes or ''
            })
            
            self._save_features(features)
            
            return {
                'success': True,
                'message': f'Statut mis à jour de "{old_status}" vers "{new_status}"'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}
    
    def get_user_submissions(self, user_session):
        """Récupère les soumissions d'un utilisateur"""
        try:
            features = self._load_features()
            user_features = [f for f in features if f['submitted_by'] == user_session]
            
            # Trier par date de soumission
            user_features.sort(key=lambda x: x['submitted_at'], reverse=True)
            
            return {
                'success': True,
                'features': user_features,
                'total_submitted': len(user_features)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la récupération: {str(e)}'}
    
    def get_user_votes(self, user_session):
        """Récupère les votes d'un utilisateur"""
        try:
            votes = self._load_votes()
            features = self._load_features()
            
            user_votes = [v for v in votes if v['user_session'] == user_session]
            
            # Enrichir avec les détails des fonctionnalités
            enriched_votes = []
            for vote in user_votes:
                feature = next((f for f in features if f['id'] == vote['feature_id']), None)
                if feature:
                    enriched_votes.append({
                        'vote': vote,
                        'feature': {
                            'id': feature['id'],
                            'title': feature['title'],
                            'status': feature['status'],
                            'total_votes': feature['votes']
                        }
                    })
            
            # Trier par date de vote
            enriched_votes.sort(key=lambda x: x['vote']['voted_at'], reverse=True)
            
            return {
                'success': True,
                'votes': enriched_votes,
                'total_votes': len(user_votes)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur lors de la récupération: {str(e)}'}
    
    def get_admin_dashboard(self):
        """Récupère les données pour le dashboard admin"""
        try:
            features = self._load_features()
            votes = self._load_votes()
            
            # Statistiques générales
            stats = {
                'total_features': len(features),
                'pending_features': len([f for f in features if f['status'] == 'pending']),
                'approved_features': len([f for f in features if f['status'] == 'approved']),
                'completed_features': len([f for f in features if f['status'] == 'completed']),
                'total_votes': len(votes),
                'unique_voters': len(set(v['user_session'] for v in votes))
            }
            
            # Fonctionnalités par statut
            by_status = {}
            for status in self.status_options:
                by_status[status] = [f for f in features if f['status'] == status]
            
            # Top fonctionnalités par votes
            top_features = sorted(features, key=lambda x: x['votes'], reverse=True)[:10]
            
            # Activité récente
            recent_features = sorted(features, key=lambda x: x['submitted_at'], reverse=True)[:5]
            recent_votes = sorted(votes, key=lambda x: x['voted_at'], reverse=True)[:10]
            
            return {
                'success': True,
                'stats': stats,
                'features_by_status': by_status,
                'top_features': top_features,
                'recent_activity': {
                    'features': recent_features,
                    'votes': recent_votes
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur dashboard admin: {str(e)}'}
    
    def _load_features(self):
        """Charge les fonctionnalités depuis le fichier"""
        try:
            if os.path.exists(self.features_file):
                with open(self.features_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_features(self, features):
        """Sauvegarde les fonctionnalités"""
        try:
            os.makedirs(os.path.dirname(self.features_file), exist_ok=True)
            with open(self.features_file, 'w', encoding='utf-8') as f:
                json.dump(features, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde fonctionnalités: {e}")
    
    def _load_votes(self):
        """Charge les votes depuis le fichier"""
        try:
            if os.path.exists(self.votes_file):
                with open(self.votes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_votes(self, votes):
        """Sauvegarde les votes"""
        try:
            os.makedirs(os.path.dirname(self.votes_file), exist_ok=True)
            with open(self.votes_file, 'w', encoding='utf-8') as f:
                json.dump(votes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde votes: {e}")

# Instance globale
feature_voting = FeatureVotingSystem()