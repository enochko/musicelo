"""
Admin Database Operations

Functions for:
- Finding duplicates
- Merging songs
- Updating classifications
- Logging admin actions
"""

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import logging

from core.database.models import Song, Comparison, AlbumTrack, AdminAction

logger = logging.getLogger(__name__)


class AdminOperations:
    """Database operations for admin tasks"""
    
    def __init__(self, db_operations):
        """Initialize with existing DatabaseOperations instance"""
        self.db = db_operations
        self.Session = db_operations.Session
    
    # ==================== DUPLICATE DETECTION ====================
    
    def find_potential_duplicates(self, threshold: float = 0.9) -> List[Tuple[Song, Song, float]]:
        """
        Find songs that might be duplicates
        
        Uses:
        - Exact title match
        - Similar titles (Levenshtein distance)
        - Same artist
        
        Returns: List of (song1, song2, similarity_score)
        """
        session = self.Session()
        try:
            duplicates = []
            
            # Get all songs
            songs = session.query(Song).all()
            
            # Compare each pair
            for i, song_a in enumerate(songs):
                for song_b in songs[i+1:]:
                    # Same artist check
                    if song_a.artist_name != song_b.artist_name:
                        continue
                    
                    # Title similarity
                    title_a = song_a.canonical_name.lower().strip()
                    title_b = song_b.canonical_name.lower().strip()
                    
                    # Exact match
                    if title_a == title_b:
                        duplicates.append((song_a, song_b, 1.0))
                        continue
                    
                    # Very similar (simple check - can enhance later)
                    # Remove common differences
                    clean_a = title_a.replace(' ', '').replace('-', '')
                    clean_b = title_b.replace(' ', '').replace('-', '')
                    
                    if clean_a == clean_b:
                        duplicates.append((song_a, song_b, 0.95))
            
            return duplicates
            
        finally:
            session.close()
    
    def get_songs_by_title_pattern(self, pattern: str) -> List[Song]:
        """Search songs by title (case-insensitive, partial match)"""
        session = self.Session()
        try:
            songs = session.query(Song).filter(
                Song.canonical_name.ilike(f'%{pattern}%')
            ).order_by(Song.canonical_name).all()
            
            # Detach from session
            session.expunge_all()
            return songs
            
        finally:
            session.close()
    
    # ==================== MERGE OPERATIONS ====================
    
    def preview_merge(self, song_id_1: int, song_id_2: int) -> Dict:
        """
        Preview what would happen if two songs are merged
        
        Returns dict with:
        - new_rating
        - new_rd
        - new_volatility
        - combined_games
        - combined_wins/losses/draws
        - comparisons_affected
        """
        session = self.Session()
        try:
            song1 = session.query(Song).filter_by(song_id=song_id_1).first()
            song2 = session.query(Song).filter_by(song_id=song_id_2).first()
            
            if not song1 or not song2:
                return None
            
            # Weighted average by games_played
            total_games = song1.games_played + song2.games_played
            
            if total_games == 0:
                new_rating = (song1.rating + song2.rating) / 2
                new_rd = max(song1.rating_deviation, song2.rating_deviation)
                new_vol = max(song1.volatility, song2.volatility)
            else:
                new_rating = (
                    song1.rating * song1.games_played + 
                    song2.rating * song2.games_played
                ) / total_games
                
                # Use lower RD (higher confidence)
                new_rd = min(song1.rating_deviation, song2.rating_deviation)
                
                # Average volatility
                new_vol = (song1.volatility + song2.volatility) / 2
            
            # Count affected comparisons
            comp_count = session.query(Comparison).filter(
                or_(
                    Comparison.song_a_id == song_id_2,
                    Comparison.song_b_id == song_id_2
                )
            ).count()
            
            return {
                'song1': {
                    'id': song1.song_id,
                    'name': song1.canonical_name,
                    'rating': song1.rating,
                    'rd': song1.rating_deviation,
                    'games': song1.games_played,
                },
                'song2': {
                    'id': song2.song_id,
                    'name': song2.canonical_name,
                    'rating': song2.rating,
                    'rd': song2.rating_deviation,
                    'games': song2.games_played,
                },
                'merged': {
                    'rating': new_rating,
                    'rd': new_rd,
                    'volatility': new_vol,
                    'games': total_games,
                    'wins': song1.wins + song2.wins,
                    'losses': song1.losses + song2.losses,
                    'draws': song1.draws + song2.draws,
                },
                'comparisons_affected': comp_count,
            }
            
        finally:
            session.close()
    
    def merge_songs(self, keep_song_id: int, merge_song_id: int, reason: str = "duplicate") -> bool:
        """
        Merge two songs (keep one, alias the other)
        
        Process:
        1. Update all comparisons referencing merge_song
        2. Combine statistics into keep_song
        3. Mark merge_song as alias of keep_song
        4. Log action
        
        Returns: True if successful
        """
        session = self.Session()
        try:
            keep_song = session.query(Song).filter_by(song_id=keep_song_id).first()
            merge_song = session.query(Song).filter_by(song_id=merge_song_id).first()
            
            if not keep_song or not merge_song:
                logger.error(f"Songs not found: {keep_song_id}, {merge_song_id}")
                return False
            
            # Calculate merged ratings (weighted average)
            preview = self.preview_merge(keep_song_id, merge_song_id)
            
            # Update keep_song with merged values
            keep_song.rating = preview['merged']['rating']
            keep_song.rating_deviation = preview['merged']['rd']
            keep_song.volatility = preview['merged']['volatility']
            keep_song.games_played = preview['merged']['games']
            keep_song.wins = preview['merged']['wins']
            keep_song.losses = preview['merged']['losses']
            keep_song.draws = preview['merged']['draws']
            
            # Update confidence intervals
            keep_song.confidence_interval_lower = keep_song.rating - 2 * keep_song.rating_deviation
            keep_song.confidence_interval_upper = keep_song.rating + 2 * keep_song.rating_deviation
            
            # Update all comparisons referencing merge_song to point to keep_song
            session.query(Comparison).filter_by(song_a_id=merge_song_id).update({
                'song_a_id': keep_song_id
            })
            
            session.query(Comparison).filter_by(song_b_id=merge_song_id).update({
                'song_b_id': keep_song_id
            })
            
            # Mark merge_song as alias (soft delete)
            merge_song.is_original = False
            merge_song.original_song_id = keep_song_id
            merge_song.variant_type = 'alias'
            
            # Note: AlbumTrack links remain - both songs can appear on albums
            
            # Log admin action
            import json
            action = AdminAction(
                action_type='merge_songs',
                description=f"Merged '{merge_song.canonical_name}' ({merge_song_id}) into '{keep_song.canonical_name}' ({keep_song_id}). Reason: {reason}",
                affected_song_ids=f"{keep_song_id},{merge_song_id}",
                action_data=json.dumps({
                    'keep_song_id': keep_song_id,
                    'merge_song_id': merge_song_id,
                    'reason': reason,
                    'before_keep': preview['song1'],
                    'before_merge': preview['song2'],
                    'after': preview['merged'],
                })
            )
            session.add(action)
            
            session.commit()
            
            logger.info(f"✅ Merged songs: {merge_song_id} → {keep_song_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Merge failed: {e}")
            return False
            
        finally:
            session.close()
    
    # ==================== CLASSIFICATION UPDATES ====================
    
    def update_variant_classification(
        self, 
        song_id: int, 
        is_original: bool, 
        variant_type: Optional[str] = None,
        original_song_id: Optional[int] = None
    ) -> bool:
        """Update song's variant classification"""
        session = self.Session()
        try:
            song = session.query(Song).filter_by(song_id=song_id).first()
            
            if not song:
                return False
            
            old_values = {
                'is_original': song.is_original,
                'variant_type': song.variant_type,
                'original_song_id': song.original_song_id,
            }
            
            song.is_original = is_original
            song.variant_type = variant_type
            song.original_song_id = original_song_id
            
            # Log action
            import json
            action = AdminAction(
                action_type='update_classification',
                description=f"Updated classification for '{song.canonical_name}' ({song_id})",
                affected_song_ids=str(song_id),
                action_data=json.dumps({
                    'song_id': song_id,
                    'before': old_values,
                    'after': {
                        'is_original': is_original,
                        'variant_type': variant_type,
                        'original_song_id': original_song_id,
                    }
                })
            )
            session.add(action)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Classification update failed: {e}")
            return False
            
        finally:
            session.close()
    
    def update_song_language(self, song_id: int, language: str) -> bool:
        """Update song language"""
        session = self.Session()
        try:
            song = session.query(Song).filter_by(song_id=song_id).first()
            
            if not song:
                return False
            
            old_lang = song.language
            song.language = language
            
            import json
            action = AdminAction(
                action_type='update_language',
                description=f"Changed language for '{song.canonical_name}' from {old_lang} to {language}",
                affected_song_ids=str(song_id),
                action_data=json.dumps({'song_id': song_id, 'from': old_lang, 'to': language})
            )
            session.add(action)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Language update failed: {e}")
            return False
            
        finally:
            session.close()
    
    # ==================== DATA QUALITY ====================
    
    def get_data_quality_report(self) -> Dict:
        """Generate data quality report"""
        session = self.Session()
        try:
            # Songs needing attention
            high_rd_songs = session.query(Song).filter(
                Song.rating_deviation > 250,
                Song.games_played < 5
            ).count()
            
            # Potential duplicates
            duplicates = self.find_potential_duplicates()
            
            # Variants without originals
            orphan_variants = session.query(Song).filter(
                Song.is_original == False,
                Song.original_song_id == None
            ).count()
            
            # Songs with no album
            no_album = session.query(Song).outerjoin(AlbumTrack).filter(
                AlbumTrack.song_id == None
            ).count()
            
            return {
                'high_uncertainty': high_rd_songs,
                'potential_duplicates': len(duplicates),
                'orphan_variants': orphan_variants,
                'no_album': no_album,
                'duplicate_pairs': duplicates[:20],  # Top 20
            }
            
        finally:
            session.close()
    
    # ==================== ADMIN ACTION LOG ====================
    
    def get_recent_actions(self, limit: int = 50) -> List[AdminAction]:
        """Get recent admin actions"""
        session = self.Session()
        try:
            actions = session.query(AdminAction).order_by(
                AdminAction.action_timestamp.desc()
            ).limit(limit).all()
            
            session.expunge_all()
            return actions
            
        finally:
            session.close()
