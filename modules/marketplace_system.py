"""
Système Marketplace/Partenariats - MindTraderPro
Gestion des liens affiliés, offres partenaires, suivi des conversions
"""
import json
import os
from datetime import datetime
from uuid import uuid4

class MarketplaceSystem:
    def __init__(self):
        self.partners_file = 'data/partners.json'
        self.offers_file = 'data/partner_offers.json'
        self.clicks_file = 'data/affiliate_clicks.json'
        
    def add_partner(self, name, description, logo_url, website, contact_email, commission_rate, category):
        """Ajoute un nouveau partenaire"""
        try:
            partner_id = str(uuid4())
            
            partner = {
                'id': partner_id,
                'name': name,
                'description': description,
                'logo_url': logo_url,
                'website': website,
                'contact_email': contact_email,
                'commission_rate': commission_rate,
                'category': category,
                'status': 'active',
                'added_at': datetime.now().isoformat(),
                'total_clicks': 0,
                'total_conversions': 0,
                'total_earnings': 0.0
            }
            
            partners = self._load_partners()
            partners.append(partner)
            self._save_partners(partners)
            
            return {
                'success': True,
                'partner_id': partner_id,
                'message': 'Partenaire ajouté avec succès'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur ajout partenaire: {str(e)}'}
    
    def add_offer(self, partner_id, title, description, offer_type, value, affiliate_link, target_audience, expires_at=None):
        """Ajoute une nouvelle offre partenaire"""
        try:
            offer_id = str(uuid4())
            
            offer = {
                'id': offer_id,
                'partner_id': partner_id,
                'title': title,
                'description': description,
                'offer_type': offer_type,  # discount, bonus, trial, etc.
                'value': value,  # pourcentage remise, montant bonus, etc.
                'affiliate_link': affiliate_link,
                'target_audience': target_audience,  # beginner, intermediate, advanced, all
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at,
                'status': 'active',
                'clicks': 0,
                'conversions': 0,
                'featured': False
            }
            
            offers = self._load_offers()
            offers.append(offer)
            self._save_offers(offers)
            
            return {
                'success': True,
                'offer_id': offer_id,
                'message': 'Offre ajoutée avec succès'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur ajout offre: {str(e)}'}
    
    def get_active_offers(self, user_level='all', limit=20):
        """Récupère les offres actives"""
        try:
            offers = self._load_offers()
            partners = self._load_partners()
            
            # Filtrer les offres actives et non expirées
            now = datetime.now()
            active_offers = []
            
            for offer in offers:
                if offer['status'] != 'active':
                    continue
                
                # Vérifier expiration
                if offer.get('expires_at'):
                    expires = datetime.fromisoformat(offer['expires_at'])
                    if now > expires:
                        continue
                
                # Vérifier audience cible
                if user_level != 'all' and offer['target_audience'] not in ['all', user_level]:
                    continue
                
                # Enrichir avec les données du partenaire
                partner = next((p for p in partners if p['id'] == offer['partner_id']), None)
                if partner:
                    offer['partner_name'] = partner['name']
                    offer['partner_logo'] = partner['logo_url']
                    offer['partner_category'] = partner['category']
                
                active_offers.append(offer)
            
            # Trier par featured puis par date
            active_offers.sort(key=lambda x: (not x.get('featured', False), x['created_at']), reverse=True)
            
            return {
                'success': True,
                'offers': active_offers[:limit],
                'total_count': len(active_offers)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur récupération offres: {str(e)}'}
    
    def track_click(self, offer_id, user_session, user_agent=None, referrer=None):
        """Enregistre un clic sur une offre"""
        try:
            click_id = str(uuid4())
            
            click_data = {
                'id': click_id,
                'offer_id': offer_id,
                'user_session': user_session,
                'clicked_at': datetime.now().isoformat(),
                'user_agent': user_agent,
                'referrer': referrer,
                'converted': False,
                'conversion_date': None,
                'conversion_value': 0.0
            }
            
            # Sauvegarder le clic
            clicks = self._load_clicks()
            clicks.append(click_data)
            self._save_clicks(clicks)
            
            # Mettre à jour les compteurs
            self._update_offer_stats(offer_id, 'click')
            
            return {
                'success': True,
                'click_id': click_id,
                'tracking_confirmed': True
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur tracking clic: {str(e)}'}
    
    def track_conversion(self, offer_id, user_session, conversion_value=0.0):
        """Enregistre une conversion"""
        try:
            clicks = self._load_clicks()
            
            # Trouver le clic correspondant
            click = next(
                (c for c in clicks if c['offer_id'] == offer_id and c['user_session'] == user_session and not c['converted']),
                None
            )
            
            if click:
                # Marquer comme converti
                click['converted'] = True
                click['conversion_date'] = datetime.now().isoformat()
                click['conversion_value'] = conversion_value
                
                self._save_clicks(clicks)
                
                # Mettre à jour les stats
                self._update_offer_stats(offer_id, 'conversion', conversion_value)
                
                return {
                    'success': True,
                    'message': 'Conversion enregistrée',
                    'conversion_value': conversion_value
                }
            else:
                return {'success': False, 'error': 'Clic correspondant non trouvé'}
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur tracking conversion: {str(e)}'}
    
    def get_partner_dashboard(self, partner_id=None):
        """Dashboard des statistiques partenaires"""
        try:
            partners = self._load_partners()
            offers = self._load_offers()
            clicks = self._load_clicks()
            
            if partner_id:
                # Stats pour un partenaire spécifique
                partner = next((p for p in partners if p['id'] == partner_id), None)
                if not partner:
                    return {'success': False, 'error': 'Partenaire non trouvé'}
                
                partner_offers = [o for o in offers if o['partner_id'] == partner_id]
                offer_ids = [o['id'] for o in partner_offers]
                partner_clicks = [c for c in clicks if c['offer_id'] in offer_ids]
                
                stats = {
                    'partner': partner,
                    'total_offers': len(partner_offers),
                    'active_offers': len([o for o in partner_offers if o['status'] == 'active']),
                    'total_clicks': len(partner_clicks),
                    'total_conversions': len([c for c in partner_clicks if c['converted']]),
                    'conversion_rate': 0,
                    'total_earnings': sum(c.get('conversion_value', 0) for c in partner_clicks if c['converted']),
                    'recent_clicks': sorted(partner_clicks, key=lambda x: x['clicked_at'], reverse=True)[:10]
                }
                
                if stats['total_clicks'] > 0:
                    stats['conversion_rate'] = (stats['total_conversions'] / stats['total_clicks']) * 100
                
                return {'success': True, 'stats': stats}
            
            else:
                # Stats globales
                total_clicks = len(clicks)
                total_conversions = len([c for c in clicks if c['converted']])
                
                stats = {
                    'overview': {
                        'total_partners': len([p for p in partners if p['status'] == 'active']),
                        'total_offers': len([o for o in offers if o['status'] == 'active']),
                        'total_clicks': total_clicks,
                        'total_conversions': total_conversions,
                        'global_conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
                        'total_earnings': sum(c.get('conversion_value', 0) for c in clicks if c['converted'])
                    },
                    'top_performers': self._get_top_performing_offers(offers, clicks),
                    'recent_activity': sorted(clicks, key=lambda x: x['clicked_at'], reverse=True)[:20]
                }
                
                return {'success': True, 'stats': stats}
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur dashboard: {str(e)}'}
    
    def update_offer_featured(self, offer_id, featured=True):
        """Met à jour le statut featured d'une offre"""
        try:
            offers = self._load_offers()
            
            offer = next((o for o in offers if o['id'] == offer_id), None)
            if not offer:
                return {'success': False, 'error': 'Offre non trouvée'}
            
            offer['featured'] = featured
            offer['updated_at'] = datetime.now().isoformat()
            
            self._save_offers(offers)
            
            return {
                'success': True,
                'message': f'Offre {"mise en avant" if featured else "retirée de la mise en avant"}'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur mise à jour: {str(e)}'}
    
    def get_affiliate_link(self, offer_id, user_session):
        """Génère un lien affilié trackable"""
        try:
            offers = self._load_offers()
            offer = next((o for o in offers if o['id'] == offer_id), None)
            
            if not offer:
                return {'success': False, 'error': 'Offre non trouvée'}
            
            # Générer un lien trackable
            base_url = offer['affiliate_link']
            tracking_params = f"?ref=mindtraderpro&offer={offer_id}&user={user_session[:8]}"
            
            trackable_link = base_url + tracking_params
            
            return {
                'success': True,
                'trackable_link': trackable_link,
                'offer_title': offer['title']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erreur génération lien: {str(e)}'}
    
    def _update_offer_stats(self, offer_id, stat_type, value=0):
        """Met à jour les statistiques d'une offre"""
        try:
            offers = self._load_offers()
            partners = self._load_partners()
            
            offer = next((o for o in offers if o['id'] == offer_id), None)
            if offer:
                if stat_type == 'click':
                    offer['clicks'] = offer.get('clicks', 0) + 1
                elif stat_type == 'conversion':
                    offer['conversions'] = offer.get('conversions', 0) + 1
                
                self._save_offers(offers)
                
                # Mettre à jour aussi les stats du partenaire
                partner = next((p for p in partners if p['id'] == offer['partner_id']), None)
                if partner:
                    if stat_type == 'click':
                        partner['total_clicks'] = partner.get('total_clicks', 0) + 1
                    elif stat_type == 'conversion':
                        partner['total_conversions'] = partner.get('total_conversions', 0) + 1
                        partner['total_earnings'] = partner.get('total_earnings', 0) + value
                    
                    self._save_partners(partners)
            
        except Exception as e:
            print(f"Erreur mise à jour stats: {e}")
    
    def _get_top_performing_offers(self, offers, clicks):
        """Récupère les offres les plus performantes"""
        offer_stats = {}
        
        for click in clicks:
            offer_id = click['offer_id']
            if offer_id not in offer_stats:
                offer_stats[offer_id] = {'clicks': 0, 'conversions': 0}
            
            offer_stats[offer_id]['clicks'] += 1
            if click.get('converted'):
                offer_stats[offer_id]['conversions'] += 1
        
        # Calculer le taux de conversion et trier
        top_offers = []
        for offer in offers:
            if offer['id'] in offer_stats:
                stats = offer_stats[offer['id']]
                conversion_rate = (stats['conversions'] / stats['clicks'] * 100) if stats['clicks'] > 0 else 0
                
                top_offers.append({
                    'offer': offer,
                    'stats': stats,
                    'conversion_rate': conversion_rate
                })
        
        top_offers.sort(key=lambda x: x['conversion_rate'], reverse=True)
        return top_offers[:5]
    
    def _load_partners(self):
        """Charge les partenaires"""
        try:
            if os.path.exists(self.partners_file):
                with open(self.partners_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_partners(self, partners):
        """Sauvegarde les partenaires"""
        try:
            os.makedirs(os.path.dirname(self.partners_file), exist_ok=True)
            with open(self.partners_file, 'w', encoding='utf-8') as f:
                json.dump(partners, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde partenaires: {e}")
    
    def _load_offers(self):
        """Charge les offres"""
        try:
            if os.path.exists(self.offers_file):
                with open(self.offers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_offers(self, offers):
        """Sauvegarde les offres"""
        try:
            os.makedirs(os.path.dirname(self.offers_file), exist_ok=True)
            with open(self.offers_file, 'w', encoding='utf-8') as f:
                json.dump(offers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde offres: {e}")
    
    def _load_clicks(self):
        """Charge les clics"""
        try:
            if os.path.exists(self.clicks_file):
                with open(self.clicks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def _save_clicks(self, clicks):
        """Sauvegarde les clics"""
        try:
            os.makedirs(os.path.dirname(self.clicks_file), exist_ok=True)
            with open(self.clicks_file, 'w', encoding='utf-8') as f:
                json.dump(clicks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde clics: {e}")

# Instance globale
marketplace = MarketplaceSystem()