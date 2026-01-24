"""
MusicElo Database Operations

CRUD operations for songs, albums, comparisons, and playlists
Provides clean interface to database without exposing SQLAlchemy details
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import desc, asc, func, and_, or_
from sqlalchemy.orm import Session

from core.database.models import (
    Song, Album, AlbumTrack, Comparison, Playlist, PlaylistSong, 
    Parameter, YTMPlaylist, create_database, get_session
)
from config import Config


class DatabaseOperations:
    """
    Database operations wrapper
    
    Provides high-level methods for:
    - Songs: Create, read, update, delete, search
    - Comparisons: Record, undo, history
    - Rankings: Get rankings with filters
    - Playlists: Generate, save, retrieve
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection
        
        Args:
            database_url: SQLAlchemy database URL (defaults to Config)
        """
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_database(self.database_url)
        self.Session = lambda: get_session(self.engine)
    
    # =========================================================================
    # SONG OPERATIONS
    # =========================================================================
    
    def add_song(self, song_data: Dict) -> Song:
        """
        Add a new song to the database
        
        Args:
            song_data: Dictionary with song fields
        
        Returns:
            Created Song object
        """
        session = self.Session()
        try:
            song = Song(**song_data)
            session.add(song)
            session.commit()
            session.refresh(song)
            return song
        finally:
            session.close()
    
    def get_song(self, song_id: int) -> Optional[Song]:
        """Get song by ID"""
        session = self.Session()
        try:
            return session.query(Song).filter_by(song_id=song_id).first()
        finally:
            session.close()
    
    def get_song_by_video_id(self, video_id: str) -> Optional[Song]:
        """Get song by YouTube video ID"""
        session = self.Session()
        try:
            return session.query(Song).filter_by(youtube_video_id=video_id).first()
        finally:
            session.close()
    
    def get_all_songs(self, include_variants: bool = True) -> List[Song]:
        """
        Get all songs
        
        Args:
            include_variants: If False, only return original songs
        
        Returns:
            List of Song objects
        """
        session = self.Session()
        try:
            query = session.query(Song)
            if not include_variants:
                query = query.filter_by(is_original=True)
            return query.all()
        finally:
            session.close()
    
    def update_song_rating(
        self, 
        song_id: int, 
        rating: float, 
        rd: float, 
        volatility: float
    ) -> None:
        """
        Update song's Glicko-2 rating
        
        Args:
            song_id: Song ID
            rating: New rating
            rd: New rating deviation
            volatility: New volatility
        """
        session = self.Session()
        try:
            song = session.query(Song).filter_by(song_id=song_id).first()
            if song:
                song.rating = rating
                song.rating_deviation = rd
                song.volatility = volatility
                song.last_compared = datetime.utcnow()
                
                # Update confidence interval
                song.confidence_interval_lower = rating - 2 * rd
                song.confidence_interval_upper = rating + 2 * rd
                
                session.commit()
        finally:
            session.close()
    
    def update_song_stats(
        self, 
        song_id: int, 
        outcome: float  # 1.0 = win, 0.5 = draw, 0.0 = loss
    ) -> None:
        """
        Update song's win/loss/draw statistics
        
        Args:
            song_id: Song ID
            outcome: Comparison outcome
        """
        session = self.Session()
        try:
            song = session.query(Song).filter_by(song_id=song_id).first()
            if song:
                song.games_played += 1
                
                if outcome == 1.0:
                    song.wins += 1
                elif outcome == 0.0:
                    song.losses += 1
                else:
                    song.draws += 1
                
                session.commit()
        finally:
            session.close()
    
    def search_songs(
        self, 
        query: str = None,
        language: str = None,
        category: str = None,
        is_original: bool = None,
        min_rating: float = None,
        max_rating: float = None
    ) -> List[Song]:
        """
        Search songs with filters
        
        Args:
            query: Search in song name
            language: Filter by language
            category: Filter by category
            is_original: Filter originals vs variants
            min_rating: Minimum rating
            max_rating: Maximum rating
        
        Returns:
            List of matching songs
        """
        session = self.Session()
        try:
            q = session.query(Song)
            
            if query:
                q = q.filter(Song.canonical_name.ilike(f'%{query}%'))
            
            if language:
                q = q.filter_by(language=language)
            
            if category:
                q = q.filter_by(category=category)
            
            if is_original is not None:
                q = q.filter_by(is_original=is_original)
            
            if min_rating is not None:
                q = q.filter(Song.rating >= min_rating)
            
            if max_rating is not None:
                q = q.filter(Song.rating <= max_rating)
            
            return q.all()
        finally:
            session.close()
    
    # =========================================================================
    # COMPARISON OPERATIONS
    # =========================================================================
    
    def record_comparison(
        self,
        song_a_id: int,
        song_b_id: int,
        outcome: float,
        outcome_type: str,
        song_a_before: Tuple[float, float, float],
        song_a_after: Tuple[float, float, float],
        song_b_before: Tuple[float, float, float],
        song_b_after: Tuple[float, float, float],
        comparison_mode: str = 'duel',
        was_sequential: bool = False
    ) -> Comparison:
        """
        Record a comparison between two songs
        
        Args:
            song_a_id: First song ID
            song_b_id: Second song ID
            outcome: Outcome from A's perspective (1.0/0.5/0.0)
            outcome_type: decisive_win, slight_win, draw, etc.
            song_a_before: (rating, rd, volatility) before
            song_a_after: (rating, rd, volatility) after
            song_b_before: (rating, rd, volatility) before
            song_b_after: (rating, rd, volatility) after
            comparison_mode: duel, playlist, etc.
            was_sequential: True if songs played back-to-back
        
        Returns:
            Created Comparison object
        """
        session = self.Session()
        try:
            # Determine winner
            if outcome == 1.0:
                winner_id = song_a_id
            elif outcome == 0.0:
                winner_id = song_b_id
            else:
                winner_id = None  # Draw
            
            # Calculate expected outcome (for upset detection)
            from core.services.glicko2_service import Glicko2Calculator
            calc = Glicko2Calculator()
            expected = calc.win_probability(
                song_a_before[0], song_a_before[1],
                song_b_before[0], song_b_before[1]
            )
            
            # Detect upset
            was_upset = (expected < 0.4 and outcome == 1.0) or (expected > 0.6 and outcome == 0.0)
            
            comparison = Comparison(
                song_a_id=song_a_id,
                song_b_id=song_b_id,
                winner_id=winner_id,
                outcome=outcome,
                outcome_type=outcome_type,
                
                song_a_rating_before=song_a_before[0],
                song_a_rd_before=song_a_before[1],
                song_a_vol_before=song_a_before[2],
                
                song_a_rating_after=song_a_after[0],
                song_a_rd_after=song_a_after[1],
                song_a_vol_after=song_a_after[2],
                
                song_b_rating_before=song_b_before[0],
                song_b_rd_before=song_b_before[1],
                song_b_vol_before=song_b_before[2],
                
                song_b_rating_after=song_b_after[0],
                song_b_rd_after=song_b_after[1],
                song_b_vol_after=song_b_after[2],
                
                comparison_mode=comparison_mode,
                was_sequential=was_sequential,
                expected_outcome=expected,
                rating_impact=abs(song_a_after[0] - song_a_before[0]),
                was_upset=was_upset
            )
            
            session.add(comparison)
            session.commit()
            session.refresh(comparison)
            
            return comparison
        finally:
            session.close()
    
    def get_recent_comparisons(self, limit: int = 10) -> List[Comparison]:
        """Get most recent comparisons"""
        session = self.Session()
        try:
            return session.query(Comparison)\
                .filter_by(is_undone=False)\
                .order_by(desc(Comparison.timestamp))\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def get_comparison_count(self) -> int:
        """Get total number of comparisons"""
        session = self.Session()
        try:
            return session.query(Comparison).filter_by(is_undone=False).count()
        finally:
            session.close()
    
    # =========================================================================
    # RANKING OPERATIONS
    # =========================================================================
    
    def get_rankings(
        self,
        sort_by: str = 'rating',
        ascending: bool = False,
        language: str = None,
        category: str = None,
        include_variants: bool = True,
        min_games: int = 0
    ) -> List[Song]:
        """
        Get song rankings with filters
        
        Args:
            sort_by: Field to sort by (rating, games_played, wins, canonical_name)
            ascending: Sort order
            language: Filter by language
            category: Filter by category
            include_variants: Include variant songs
            min_games: Minimum games played
        
        Returns:
            List of songs sorted by criteria
        """
        session = self.Session()
        try:
            query = session.query(Song)
            
            # Filters
            if not include_variants:
                query = query.filter_by(is_original=True)
            
            if language:
                query = query.filter_by(language=language)
            
            if category:
                query = query.filter_by(category=category)
            
            if min_games > 0:
                query = query.filter(Song.games_played >= min_games)
            
            # Sorting
            sort_field = getattr(Song, sort_by, Song.rating)
            if ascending:
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))
            
            return query.all()
        finally:
            session.close()
    
    def get_top_songs(self, limit: int = 10, min_games: int = 5) -> List[Song]:
        """Get top-rated songs"""
        return self.get_rankings(
            sort_by='rating',
            ascending=False,
            min_games=min_games
        )[:limit]
    
    # =========================================================================
    # ALBUM OPERATIONS
    # =========================================================================
    
    def add_album(self, album_data: Dict) -> Album:
        """Add a new album"""
        session = self.Session()
        try:
            album = Album(**album_data)
            session.add(album)
            session.commit()
            session.refresh(album)
            return album
        finally:
            session.close()
    
    def add_album_track(
        self, 
        album_id: int, 
        song_id: int, 
        track_number: int,
        disc_number: int = 1
    ) -> AlbumTrack:
        """Add a song to an album"""
        session = self.Session()
        try:
            track = AlbumTrack(
                album_id=album_id,
                song_id=song_id,
                track_number=track_number,
                disc_number=disc_number
            )
            session.add(track)
            session.commit()
            return track
        finally:
            session.close()
    
    def get_album_by_name(self, album_name: str) -> Optional[Album]:
        """Get album by name"""
        session = self.Session()
        try:
            return session.query(Album).filter_by(album_name=album_name).first()
        finally:
            session.close()
    
    def get_album_tracks(self, album_id: int) -> List[Tuple[Song, int]]:
        """
        Get all songs in an album with track numbers
        
        Returns:
            List of (Song, track_number) tuples, sorted by track number
        """
        session = self.Session()
        try:
            results = session.query(Song, AlbumTrack.track_number)\
                .join(AlbumTrack)\
                .filter(AlbumTrack.album_id == album_id)\
                .order_by(AlbumTrack.disc_number, AlbumTrack.track_number)\
                .all()
            return results
        finally:
            session.close()
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_statistics(self) -> Dict:
        """
        Get overall statistics
        
        Returns:
            Dictionary with statistics
        """
        session = self.Session()
        try:
            total_songs = session.query(Song).count()
            total_originals = session.query(Song).filter_by(is_original=True).count()
            total_variants = total_songs - total_originals
            total_comparisons = session.query(Comparison).filter_by(is_undone=False).count()
            
            # Rating distribution
            avg_rating = session.query(func.avg(Song.rating)).scalar() or 0
            max_rating = session.query(func.max(Song.rating)).scalar() or 0
            min_rating = session.query(func.min(Song.rating)).scalar() or 0
            
            # Language breakdown
            language_counts = session.query(
                Song.language, 
                func.count(Song.song_id)
            ).group_by(Song.language).all()
            
            return {
                'total_songs': total_songs,
                'total_originals': total_originals,
                'total_variants': total_variants,
                'total_comparisons': total_comparisons,
                'avg_rating': round(avg_rating, 1),
                'max_rating': round(max_rating, 1),
                'min_rating': round(min_rating, 1),
                'language_breakdown': dict(language_counts)
            }
        finally:
            session.close()
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def bulk_insert_songs(self, songs_data: List[Dict]) -> int:
        """
        Bulk insert songs for efficiency
        
        Args:
            songs_data: List of song dictionaries
        
        Returns:
            Number of songs inserted
        """
        session = self.Session()
        try:
            songs = [Song(**data) for data in songs_data]
            session.bulk_save_objects(songs)
            session.commit()
            return len(songs)
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'engine'):
            self.engine.dispose()


# Convenience function for scripts
def get_db() -> DatabaseOperations:
    """Get database operations instance"""
    return DatabaseOperations()


if __name__ == '__main__':
    # Example usage
    db = get_db()
    
    print("=" * 60)
    print("Database Operations Test")
    print("=" * 60)
    
    # Get statistics
    stats = db.get_statistics()
    print("\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Get top songs
    top_songs = db.get_top_songs(limit=5, min_games=0)
    print(f"\nTop {len(top_songs)} Songs:")
    for i, song in enumerate(top_songs, 1):
        print(f"  {i}. {song.canonical_name} - {song.rating:.0f} (±{song.rating_deviation:.0f})")
    
    db.close()
    print("\n" + "=" * 60)
