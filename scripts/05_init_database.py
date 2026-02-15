"""
Improved Database Initialization

Key improvements:
1. Uses display_title for user-facing names
2. Properly handles same song on multiple albums (one Song, many AlbumTrack)
3. Better variant linking
4. Album display in schema
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.models import create_database, get_session, initialize_parameters
from core.database.models import Song, Album, AlbumTrack, YTMPlaylist
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImprovedDatabaseInitializer:
    """Initialize database with improved data handling"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        
        # File paths
        self.songs_file = self.data_dir / 'ytm_enriched.csv'
        self.albums_file = self.data_dir / 'albums.csv'
        self.liked_file = self.data_dir / 'user_liked_songs.csv'
        self.familiar_file = self.data_dir / 'user_familiar_songs.csv'
        self.to_listen_file = self.data_dir / 'user_to_listen_songs.csv'
        
        # Elo boost levels
        self.elo_boosts = {
            'liked': 1600,
            'familiar': 1550,
            'to_listen': 1525,
            'unknown': 1500,
        }
    
    def load_user_preferences(self):
        """Load user's liked/familiar/to-listen songs"""
        preferences = {
            'liked': set(),
            'familiar': set(),
            'to_listen': set(),
        }
        
        for pref_type, filepath in [
            ('liked', self.liked_file),
            ('familiar', self.familiar_file),
            ('to_listen', self.to_listen_file),
        ]:
            if filepath.exists():
                df = pd.read_csv(filepath)
                video_ids = set(df['video_id'].dropna())
                preferences[pref_type] = video_ids
                logger.info(f"   {pref_type}: {len(video_ids)} songs")
        
        return preferences
    
    def determine_initial_elo(self, video_id: str, preferences: dict) -> tuple:
        """Determine initial Elo rating and source"""
        if video_id in preferences['liked']:
            return self.elo_boosts['liked'], 'user_liked'
        elif video_id in preferences['familiar']:
            return self.elo_boosts['familiar'], 'user_familiar'
        elif video_id in preferences['to_listen']:
            return self.elo_boosts['to_listen'], 'to_listen'
        else:
            return self.elo_boosts['unknown'], 'unknown'
    
    def detect_category(self, artist_name: str) -> str:
        """Detect song category from artist name"""
        artist_lower = artist_name.lower()
        
        # Solo artists
        solo_artists = ['nayeon', 'jihyo', 'sana', 'momo', 'dahyun', 
                       'chaeyoung', 'tzuyu', 'mina', 'jeongyeon']
        if any(solo in artist_lower for solo in solo_artists):
            return 'Solo'
        
        # Subunits
        if 'misamo' in artist_lower:
            return 'Subunit'
        
        # Collaborations
        if ',' in artist_name or '&' in artist_name or 'feat' in artist_lower:
            return 'Collaboration'
        
        # Default: TWICE
        return 'TWICE'
    
    def insert_songs(self, session, songs_df: pd.DataFrame, preferences: dict):
        """
        Insert songs into database
        
        Key: Uses display_title for user-facing name
        """
        logger.info("\n📀 Inserting songs...")
        
        songs_created = 0
        elo_distribution = {}
        
        for _, row in songs_df.iterrows():
            video_id = row.get('video_id')
            initial_elo, elo_source = self.determine_initial_elo(video_id, preferences)
            
            # Track distribution
            elo_distribution[elo_source] = elo_distribution.get(elo_source, 0) + 1
            
            # Use display_title if available, otherwise canonical_name
            display_name = row.get('display_title', row.get('canonical_name', row['title']))
            
            # Create song
            song = Song(
                canonical_name=display_name,  # Use full title with parentheses
                youtube_music_url=row.get('youtube_music_url'),
                youtube_video_id=video_id,
                youtube_url=row.get('youtube_url'),
                thumbnail_url=row.get('thumbnail_url'),
                
                # Variant info (will be linked in second pass)
                is_original=row.get('is_original', True),
                variant_type=row.get('variant_type'),
                
                # Language
                language=row.get('language', 'korean'),
                
                # Duration
                duration_ms=row.get('duration_ms'),
                duration_seconds=row.get('duration_seconds'),
                
                # Artist
                artist_name=row.get('artists', 'TWICE'),
                
                # Category
                category=self.detect_category(row.get('artists', 'TWICE')),
                
                # Glicko-2 (initial values)
                rating=float(initial_elo),
                rating_deviation=350.0,
                volatility=0.06,
                
                # User flags
                is_liked=video_id in preferences['liked'],
                is_familiar=video_id in preferences['familiar'],
            )
            
            session.add(song)
            songs_created += 1
        
        session.commit()
        
        logger.info(f"   ✅ Created {songs_created} songs")
        logger.info(f"\n   📊 Initial Elo distribution:")
        for source, count in sorted(elo_distribution.items()):
            elo = self.elo_boosts.get(source, 1500)
            logger.info(f"      {source}: {count} songs @ {elo} Elo")
        
        # Second pass: Link variants to originals
        logger.info(f"\n🔗 Linking variants to originals...")
        variants_linked = 0
        
        for _, row in songs_df.iterrows():
            if not row.get('is_original', True) and pd.notna(row.get('original_video_id')):
                variant_video_id = row.get('video_id')
                original_video_id = row.get('original_video_id')
                
                # Find both songs in database
                variant_song = session.query(Song).filter_by(youtube_video_id=variant_video_id).first()
                original_song = session.query(Song).filter_by(youtube_video_id=original_video_id).first()
                
                if variant_song and original_song:
                    variant_song.original_song_id = original_song.song_id
                    variants_linked += 1
        
        session.commit()
        
        if variants_linked > 0:
            logger.info(f"   ✅ Linked {variants_linked} variants to originals")
    
    def insert_albums(self, session, albums_df: pd.DataFrame, songs_df: pd.DataFrame):
        """
        Insert albums and link to songs
        
        Key: One song can appear on multiple albums
        """
        logger.info("\n💿 Inserting albums...")
        
        albums_created = 0
        tracks_linked = 0
        
        # Create a lookup: album_name -> set of video_ids
        album_tracks = {}
        for _, row in songs_df.iterrows():
            album = row.get('album', '')
            video_id = row.get('video_id')
            if album and video_id:
                if album not in album_tracks:
                    album_tracks[album] = []
                album_tracks[album].append(video_id)
        
        for _, album_row in albums_df.iterrows():
            album_name = album_row['album_name']
            
            # Create album
            album = Album(
                album_name=album_name,
                album_type=album_row.get('album_type', 'ep'),
                language=album_row.get('language', 'korean'),
            )
            session.add(album)
            session.flush()
            
            albums_created += 1
            
            # Link songs to this album
            if album_name in album_tracks:
                for track_num, video_id in enumerate(album_tracks[album_name], 1):
                    # Find song in database
                    song = session.query(Song).filter_by(youtube_video_id=video_id).first()
                    
                    if song:
                        # Create album track link
                        album_track = AlbumTrack(
                            album_id=album.album_id,
                            song_id=song.song_id,
                            track_number=track_num,
                            disc_number=1,
                        )
                        session.add(album_track)
                        tracks_linked += 1
        
        session.commit()
        
        logger.info(f"   ✅ Created {albums_created} albums")
        logger.info(f"   ✅ Linked {tracks_linked} album tracks")
    
    def insert_source_playlists(self, session):
        """Record which YTM playlists were used as sources"""
        logger.info("\n📋 Recording source playlists...")
        
        playlists = [
            {
                'playlist_id': 'PLGpL_nBYyJ5aYgEp0T54lkxSg6GRuQHQZ',
                'playlist_name': 'TWICE Complete Discography #1',
                'playlist_url': 'https://music.youtube.com/playlist?list=PLGpL_nBYyJ5aYgEp0T54lkxSg6GRuQHQZ',
            },
            {
                'playlist_id': 'PL5jXuaOqUMtVGZstkNWayKhybNyVrW9lA',
                'playlist_name': 'TWICE All Songs #2',
                'playlist_url': 'https://music.youtube.com/playlist?list=PL5jXuaOqUMtVGZstkNWayKhybNyVrW9lA',
            },
            {
                'playlist_id': 'PLHPHZDuwUETkXn8t5HvghLY1QXZLlEB21',
                'playlist_name': 'TWICE Comprehensive #3',
                'playlist_url': 'https://music.youtube.com/playlist?list=PLHPHZDuwUETkXn8t5HvghLY1QXZLlEB21',
            },
        ]
        
        for pl in playlists:
            ytm_playlist = YTMPlaylist(**pl, last_updated=datetime.utcnow())
            session.add(ytm_playlist)
        
        session.commit()
        logger.info(f"   ✅ Recorded {len(playlists)} source playlists")
    
    def run(self):
        """Initialize complete database"""
        logger.info("=" * 60)
        logger.info("Database Initialization (Improved)")
        logger.info("=" * 60)
        
        # Check required files exist
        logger.info("\n📂 Checking data files...")
        required_files = [self.songs_file, self.albums_file]
        for filepath in required_files:
            if not filepath.exists():
                logger.error(f"   ❌ Missing: {filepath}")
                logger.error(f"\n   Run data collection scripts first:")
                logger.error(f"     python scripts/01_fetch_ytm_playlists.py")
                logger.error(f"     python scripts/02_deduplicate_IMPROVED.py")
                logger.error(f"     python scripts/03_extract_album_info.py")
                return
            logger.info(f"   ✅ Found: {filepath}")
        
        # Load user preferences (optional)
        logger.info("\n📊 Loading user preferences...")
        preferences = self.load_user_preferences()
        
        # Load data
        logger.info("\n📥 Loading CSV data...")
        songs_df = pd.read_csv(self.songs_file)
        albums_df = pd.read_csv(self.albums_file)
        logger.info(f"   ✅ Songs: {len(songs_df)}")
        logger.info(f"   ✅ Albums: {len(albums_df)}")
        
        # Create database
        logger.info(f"\n🗄️  Creating database: {Config.DATABASE_URL}")
        engine = create_database(Config.DATABASE_URL)
        session = get_session(engine)
        
        try:
            # Initialize parameters
            logger.info("\n⚙️  Initializing Glicko-2 parameters...")
            initialize_parameters(session)
            
            # Insert data
            self.insert_songs(session, songs_df, preferences)
            self.insert_albums(session, albums_df, songs_df)
            self.insert_source_playlists(session)
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("✅ Database Initialization Complete!")
            logger.info("=" * 60)
            
            # Stats
            total_songs = session.query(Song).count()
            total_albums = session.query(Album).count()
            total_tracks = session.query(AlbumTrack).count()
            
            logger.info(f"\n📊 Database contents:")
            logger.info(f"   Songs: {total_songs}")
            logger.info(f"   Albums: {total_albums}")
            logger.info(f"   Album tracks: {total_tracks}")
            
            # Rating distribution
            logger.info(f"\n🎵 Song breakdown:")
            originals = session.query(Song).filter_by(is_original=True).count()
            variants = session.query(Song).filter_by(is_original=False).count()
            logger.info(f"   Original songs: {originals}")
            logger.info(f"   Variants: {variants}")
            
            logger.info(f"\n🌍 Language distribution:")
            for lang in ['korean', 'japanese', 'english', 'instrumental']:
                count = session.query(Song).filter_by(language=lang).count()
                if count > 0:
                    logger.info(f"   {lang.capitalize()}: {count}")
            
            logger.info(f"\n⭐ Your personalized ratings:")
            liked = session.query(Song).filter_by(is_liked=True).count()
            familiar = session.query(Song).filter_by(is_familiar=True).count()
            logger.info(f"   Liked songs (1600 Elo): {liked}")
            logger.info(f"   Familiar songs (1550 Elo): {familiar}")
            
            logger.info("\n" + "=" * 60)
            logger.info("🚀 Next steps:")
            logger.info("=" * 60)
            logger.info("\n1. Start the app:")
            logger.info("     streamlit run streamlit_app/Home.py")
            logger.info("\n2. Begin ranking in Duel Mode")
            logger.info("3. Watch your ratings evolve!")
            logger.info("\n" + "=" * 60)
            
        except Exception as e:
            logger.error(f"\n❌ Error during initialization: {e}")
            session.rollback()
            raise
        
        finally:
            session.close()
        
        return True


def main():
    """Main entry point"""
    initializer = ImprovedDatabaseInitializer()
    initializer.run()


if __name__ == '__main__':
    main()
