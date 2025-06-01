"""
Journal Manager - Module de gestion du journal de trading
Toutes les fonctions de traitement des trades et statistiques
"""

import os
import sqlite3
import uuid
from datetime import datetime

# Configuration de la base de données
DATABASE = 'mindtraderpro_users.db'

# ============================================================================
# FONCTIONS DE GESTION DES TRADES
# ============================================================================

def add_trade_to_journal(user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit, 
                        lot_size, trading_style, emotions, notes, audio_note_path=None):
    """
    Ajoute un nouveau trade au journal de trading
    
    Args:
        user_id (int): ID de l'utilisateur
        asset (str): Actif tradé (ex: EURUSD, XAUUSD)
        trade_type (str): Type de trade ('buy' ou 'sell')
        trade_date (str): Date et heure du trade
        entry_price (float): Prix d'entrée
        stop_loss (float): Stop loss
        take_profit (float): Take profit
        lot_size (float): Taille de la position
        trading_style (str): Style de trading (scalping, day_trading, swing, position)
        emotions (str): État émotionnel (confident, nervous, greedy, fearful, calm, frustrated, excited)
        notes (str): Notes textuelles
        audio_note_path (str): Chemin vers la note audio (optionnel)
    
    Returns:
        dict: Résultat de l'ajout avec succès/erreur
    """
    try:
        # Validation stricte des paramètres obligatoires
        if not all([asset, trade_type, trade_date, entry_price, lot_size]):
            return {'success': False, 'error': 'Tous les champs obligatoires doivent être renseignés'}
        
        # Validation des types de données
        if trade_type not in ['buy', 'sell']:
            return {'success': False, 'error': 'Type de trade invalide'}
        
        if trading_style and trading_style not in ['scalping', 'day_trading', 'swing', 'position']:
            return {'success': False, 'error': 'Style de trading invalide'}
        
        if emotions and emotions not in ['confident', 'nervous', 'greedy', 'fearful', 'calm', 'frustrated', 'excited']:
            return {'success': False, 'error': 'État émotionnel invalide'}
        
        # Validation des valeurs numériques
        if entry_price <= 0 or lot_size <= 0:
            return {'success': False, 'error': 'Prix et lot size doivent être positifs'}
        
        # Limitation de la taille des notes pour éviter les injections
        if notes and len(notes) > 1000:
            return {'success': False, 'error': 'Notes limitées à 1000 caractères'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trading_journal (
                user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
                lot_size, trading_style, emotions, notes, audio_note_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        ''', (user_id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
              lot_size, trading_style, emotions, notes, audio_note_path))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'trade_id': trade_id, 'message': 'Trade ajouté avec succès'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de l\'ajout du trade: {str(e)}'}

def update_trade_result(trade_id, user_id, exit_price, result_pnl, result_pips):
    """
    Met à jour les résultats d'un trade (quand il est clôturé)
    
    Args:
        trade_id (int): ID du trade
        user_id (int): ID de l'utilisateur (pour vérification de sécurité)
        exit_price (float): Prix de sortie
        result_pnl (float): Résultat en devise
        result_pips (float): Résultat en pips
    
    Returns:
        dict: Résultat de la mise à jour
    """
    try:
        # Validation des données
        if not all([trade_id, user_id, exit_price]):
            return {'success': False, 'error': 'Paramètres requis manquants'}
        
        if exit_price <= 0:
            return {'success': False, 'error': 'Prix de sortie invalide'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trading_journal 
            SET exit_price = ?, result_pnl = ?, result_pips = ?, status = 'closed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (exit_price, result_pnl, result_pips, trade_id, user_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Trade mis à jour avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Trade non trouvé ou accès non autorisé'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}

def update_trade_details(trade_id, user_id, asset, trade_type, trade_date, entry_price, 
                        stop_loss, take_profit, lot_size, trading_style, emotions, notes):
    """
    Modifie les détails d'un trade existant
    
    Args:
        trade_id (int): ID du trade à modifier
        user_id (int): ID de l'utilisateur (sécurité)
        ... autres paramètres du trade
    
    Returns:
        dict: Résultat de la modification
    """
    try:
        # Validation stricte des paramètres
        if not all([trade_id, user_id, asset, trade_type, trade_date, entry_price, lot_size]):
            return {'success': False, 'error': 'Tous les champs obligatoires doivent être renseignés'}
        
        # Validations de sécurité
        if trade_type not in ['buy', 'sell']:
            return {'success': False, 'error': 'Type de trade invalide'}
        
        if trading_style and trading_style not in ['scalping', 'day_trading', 'swing', 'position']:
            return {'success': False, 'error': 'Style de trading invalide'}
        
        if emotions and emotions not in ['confident', 'nervous', 'greedy', 'fearful', 'calm', 'frustrated', 'excited']:
            return {'success': False, 'error': 'État émotionnel invalide'}
        
        if entry_price <= 0 or lot_size <= 0:
            return {'success': False, 'error': 'Prix et lot size doivent être positifs'}
        
        if notes and len(notes) > 1000:
            return {'success': False, 'error': 'Notes limitées à 1000 caractères'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trading_journal 
            SET asset = ?, trade_type = ?, trade_date = ?, entry_price = ?, stop_loss = ?, 
                take_profit = ?, lot_size = ?, trading_style = ?, emotions = ?, notes = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (asset, trade_type, trade_date, entry_price, stop_loss, take_profit, 
              lot_size, trading_style, emotions, notes, trade_id, user_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Trade modifié avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Trade non trouvé ou accès non autorisé'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la modification: {str(e)}'}

def delete_trade(trade_id, user_id):
    """
    Supprime un trade de façon sécurisée
    
    Args:
        trade_id (int): ID du trade à supprimer
        user_id (int): ID de l'utilisateur (vérification de propriété)
    
    Returns:
        dict: Résultat de la suppression
    """
    try:
        if not trade_id or not user_id:
            return {'success': False, 'error': 'Paramètres requis manquants'}
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération du chemin audio avant suppression pour nettoyage
        cursor.execute('''
            SELECT audio_note_path FROM trading_journal 
            WHERE id = ? AND user_id = ?
        ''', (trade_id, user_id))
        
        result = cursor.fetchone()
        audio_path = result[0] if result else None
        
        # Suppression du trade
        cursor.execute('''
            DELETE FROM trading_journal 
            WHERE id = ? AND user_id = ?
        ''', (trade_id, user_id))
        
        if cursor.rowcount > 0:
            # Suppression du fichier audio associé si existant
            if audio_path:
                try:
                    audio_file_path = f'static/audio/{audio_path}'
                    if os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
                except Exception as e:
                    print(f"Erreur suppression fichier audio: {e}")
            
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Trade supprimé avec succès'}
        else:
            conn.close()
            return {'success': False, 'error': 'Trade non trouvé ou accès non autorisé'}
    except Exception as e:
        return {'success': False, 'error': f'Erreur lors de la suppression: {str(e)}'}

def get_user_trades(user_id, limit=50, offset=0, filters=None):
    """
    Récupère la liste des trades d'un utilisateur avec filtres optionnels
    
    Args:
        user_id (int): ID de l'utilisateur
        limit (int): Nombre maximum de trades à récupérer
        offset (int): Décalage pour la pagination
        filters (dict): Filtres à appliquer (asset, trade_type, date_from, date_to, result_type)
    
    Returns:
        list: Liste des trades de l'utilisateur
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Construction de la requête avec filtres
        query = '''
            SELECT id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
                   exit_price, lot_size, result_pnl, result_pips, trading_style, emotions,
                   notes, audio_note_path, status, created_at
            FROM trading_journal 
            WHERE user_id = ?
        '''
        params = [user_id]
        
        # Application des filtres si fournis
        if filters:
            if filters.get('asset'):
                query += ' AND asset = ?'
                params.append(filters['asset'])
            
            if filters.get('trade_type'):
                query += ' AND trade_type = ?'
                params.append(filters['trade_type'])
            
            if filters.get('date_from'):
                query += ' AND date(trade_date) >= ?'
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                query += ' AND date(trade_date) <= ?'
                params.append(filters['date_to'])
            
            if filters.get('result_type') == 'win':
                query += ' AND result_pnl > 0'
            elif filters.get('result_type') == 'loss':
                query += ' AND result_pnl < 0'
            
            if filters.get('status'):
                query += ' AND status = ?'
                params.append(filters['status'])
        
        query += ' ORDER BY trade_date DESC, created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        trades = cursor.fetchall()
        conn.close()
        
        # Conversion en dictionnaire pour faciliter l'utilisation
        trades_list = []
        for trade in trades:
            trades_list.append({
                'id': trade[0],
                'asset': trade[1],
                'trade_type': trade[2],
                'trade_date': trade[3],
                'entry_price': trade[4],
                'stop_loss': trade[5],
                'take_profit': trade[6],
                'exit_price': trade[7],
                'lot_size': trade[8],
                'result_pnl': trade[9],
                'result_pips': trade[10],
                'trading_style': trade[11],
                'emotions': trade[12],
                'notes': trade[13],
                'audio_note_path': trade[14],
                'status': trade[15],
                'created_at': trade[16]
            })
        
        return trades_list
    except Exception as e:
        print(f"Erreur lors de la récupération des trades: {e}")
        return []

def get_single_trade(trade_id, user_id):
    """
    Récupère un trade spécifique pour un utilisateur (sécurité)
    
    Args:
        trade_id (int): ID du trade
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Détails du trade ou None si non trouvé
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, asset, trade_type, trade_date, entry_price, stop_loss, take_profit,
                   exit_price, lot_size, result_pnl, result_pips, trading_style, emotions,
                   notes, audio_note_path, status, created_at
            FROM trading_journal 
            WHERE id = ? AND user_id = ?
        ''', (trade_id, user_id))
        
        trade = cursor.fetchone()
        conn.close()
        
        if trade:
            return {
                'id': trade[0],
                'asset': trade[1],
                'trade_type': trade[2],
                'trade_date': trade[3],
                'entry_price': trade[4],
                'stop_loss': trade[5],
                'take_profit': trade[6],
                'exit_price': trade[7],
                'lot_size': trade[8],
                'result_pnl': trade[9],
                'result_pips': trade[10],
                'trading_style': trade[11],
                'emotions': trade[12],
                'notes': trade[13],
                'audio_note_path': trade[14],
                'status': trade[15],
                'created_at': trade[16]
            }
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du trade: {e}")
        return None

def get_trading_statistics(user_id):
    """
    Calcule les statistiques de trading pour un utilisateur
    
    Args:
        user_id (int): ID de l'utilisateur
    
    Returns:
        dict: Statistiques de trading (winrate, R moyen, drawdown, etc.)
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Récupération de tous les trades fermés
        cursor.execute('''
            SELECT result_pnl, result_pips, asset, trading_style
            FROM trading_journal 
            WHERE user_id = ? AND status = 'closed' AND result_pnl IS NOT NULL
            ORDER BY trade_date ASC
        ''', (user_id,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'winrate': 0,
                'total_pnl': 0,
                'average_win': 0,
                'average_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'assets_traded': [],
                'styles_distribution': {}
            }
        
        # Calculs statistiques détaillés
        total_trades = len(trades)
        pnl_values = [trade[0] for trade in trades]
        
        winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
        losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
        
        winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(pnl_values)
        
        wins = [pnl for pnl in pnl_values if pnl > 0]
        losses = [pnl for pnl in pnl_values if pnl < 0]
        
        average_win = (sum(wins) / len(wins)) if wins else 0
        average_loss = (sum(losses) / len(losses)) if losses else 0
        
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Calcul du drawdown maximum
        running_total = 0
        peak = 0
        max_drawdown = 0
        
        for pnl in pnl_values:
            running_total += pnl
            if running_total > peak:
                peak = running_total
            drawdown = peak - running_total
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Meilleur et pire trade
        best_trade = max(pnl_values) if pnl_values else 0
        worst_trade = min(pnl_values) if pnl_values else 0
        
        # Actifs tradés et styles
        assets_traded = list(set([trade[2] for trade in trades]))
        styles = [trade[3] for trade in trades if trade[3]]
        styles_distribution = {}
        for style in set(styles):
            styles_distribution[style] = styles.count(style)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'winrate': round(winrate, 2),
            'total_pnl': round(total_pnl, 2),
            'average_win': round(average_win, 2),
            'average_loss': round(average_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'assets_traded': assets_traded,
            'styles_distribution': styles_distribution
        }
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {}

def save_audio_note(audio_file, user_id):
    """
    Sauvegarde sécurisée d'une note audio
    
    Args:
        audio_file: Fichier audio uploadé
        user_id (int): ID de l'utilisateur
    
    Returns:
        str: Nom du fichier sauvegardé ou None si erreur
    """
    try:
        if not audio_file or not audio_file.filename:
            return None
        
        # Validation de l'extension
        allowed_extensions = ['mp3', 'wav', 'm4a', 'ogg']
        file_extension = audio_file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            return None
        
        # Limitation de la taille (10MB max)
        if hasattr(audio_file, 'content_length') and audio_file.content_length > 10 * 1024 * 1024:
            return None
        
        # Création du dossier audio s'il n'existe pas
        os.makedirs('static/audio', exist_ok=True)
        
        # Génération d'un nom de fichier unique et sécurisé
        unique_filename = f"trade_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Sauvegarde du fichier
        audio_file.save(f'static/audio/{unique_filename}')
        
        return unique_filename
    except Exception as e:
        print(f"Erreur sauvegarde audio: {e}")
        return None

def get_available_assets():
    """
    Retourne la liste des actifs disponibles pour le trading
    
    Returns:
        list: Liste des actifs avec leurs noms complets
    """
    return [
        {'symbol': 'EURUSD', 'name': 'EUR/USD'},
        {'symbol': 'GBPUSD', 'name': 'GBP/USD'},
        {'symbol': 'USDJPY', 'name': 'USD/JPY'},
        {'symbol': 'USDCHF', 'name': 'USD/CHF'},
        {'symbol': 'AUDUSD', 'name': 'AUD/USD'},
        {'symbol': 'USDCAD', 'name': 'USD/CAD'},
        {'symbol': 'NZDUSD', 'name': 'NZD/USD'},
        {'symbol': 'EURJPY', 'name': 'EUR/JPY'},
        {'symbol': 'GBPJPY', 'name': 'GBP/JPY'},
        {'symbol': 'XAUUSD', 'name': 'XAU/USD (Or)'},
        {'symbol': 'XAGUSD', 'name': 'XAG/USD (Argent)'},
        {'symbol': 'BTCUSD', 'name': 'BTC/USD'},
        {'symbol': 'ETHUSD', 'name': 'ETH/USD'},
    ]