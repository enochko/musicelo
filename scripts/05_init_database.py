"""
Initialize MusicElo database from collected data

Loads:
- Songs from ytm_enriched.csv
- Albums from albums.csv
- User preferences (liked, familiar, to-listen)
- Applies Glicko-2 initial ratings

Creates complete database ready for ranking
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.models import create_database, get_session, initialize_parameters
from core.database.models import Song, Album, AlbumTrack, YTMPlaylist
from config import Config


class DatabaseInitializer:
    """Initialize database from CSV data"""
    
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
        
        # Load each preference file
        for pref_type, filepath in [
            ('liked', self.liked_file),
            ('familiar', self.familiar_file),
            ('to_listen', self.to_listen_file),
        ]:
            if filepath.exists():
                df = pd.read_csv(filepath)
                video_ids = set(df['video_id'].dropna())
                preferences[pref_type] = video_ids
                print(f"   ✅ {pref_type}: {len(video_ids)} songs")
        
        return preferences
    
    def determine_initial_elo(self, video_id: str, preferences: dict) -> tuple:
        """
        Determine initial Elo rating and source
        
        Args:
            video_id: YouTube video ID
            preferences: Dict of preference sets
        
        Returns:
            (elo_rating, elo_source)
        """
        if video_id in preferences['liked']:
            return self.elo_boosts['liked'], 'user_liked'
        elif video_id in preferences['familiar']:
            return self.elo_boosts['familiar'], 'user_familiar'
        elif video_id in preferences['to_listen']:
            return self.elo_boosts['to_listen'], 'to_listen'
        else:
            return self.elo_boosts['unknown'], 'unknown'
    
    def insert_songs(self, session, songs_df: pd.DataFrame, preferences: dict):
        """
        Insert songs into database
        
        Args:
            session: SQLAlchemy session
            songs_df: DataFrame with song data
            preferences: User preferences dict
        """
        print("\n📀 Inserting songs...")
        
        songs_created = 0
        elo_distribution = {}
        
        for _, row in songs_df.iterrows():
            # Determine initial Elo
            video_id = row.get('video_id')
            initial_elo, elo_source = self.determine_initial_elo(video_id, preferences)
            
            # Track distribution
            elo_distribution[elo_source] = elo_distribution.get(elo_source, 0) + 1
            
            # Create song
            song = Song(
                canonical_name=row.get('canonical_name', row['title']),
                youtube_music_url=row.get('youtube_music_url'),
                youtube_video_id=video_id,
                youtube_url=row.get('youtube_url'),
                thumbnail_url=row.get('thumbnail_url'),
                
                # Variant info (will link song IDs in second pass)
                is_original=row.get('is_original', True),
                variant_type=row.get('variant_type'),
                
                # Language
                language=row.get('language', 'korean'),
                
                # Duration
                duration_ms=row.get('duration_ms'),
                duration_seconds=row.get('duration_seconds'),
                
                # Artist
                artist_name=row.get('artists', 'TWICE'),
                
                # Category (detect from artist name)
                category=self._detect_category(row.get('artists', 'TWICE')),
                
                # Glicko-2 (initial values)
                rating=float(initial_elo),
                rating_deviation=350.0,  # High uncertainty for new songs
                volatility=0.06,
                
                # User flags
                is_liked=video_id in preferences['liked'],
                is_familiar=video_id in preferences['familiar'],
            )
            
            session.add(song)
            songs_created += 1
        
        session.commit()
        
        # Second pass: Link variants to originals
        print(f"\n🔗 Linking variants to originals...")
        variants_linked = 0
        
        for _, row in songs_df.iterrows():
            if not row.get('is_original', True) and pd.notna(row.get('original_video_id')):
                # This is a variant, find the original
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
            print(f"   ✅ Linked {variants_linked} variants to originals")
        
        print(f"   ✅ Created {songs_created} songs")
        print(f"\n   📊 Initial Elo distribution:")
        for source, count in sorted(elo_distribution.items()):
            elo = self.elo_boosts.get(source, 1500)
            print(f"      {source}: {count} songs @ {elo} Elo")
    
    def _detect_category(self, artist_name: str) -> str:
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
    
    def insert_albums(self, session, albums_df: pd.DataFrame, songs_df: pd.DataFrame):
        """
        Insert albums and link to songs
        
        Args:
            session: SQLAlchemy session
            albums_df: DataFrame with album data
            songs_df: DataFrame with song data (to link tracks)
        """
        print("\n💿 Inserting albums...")
        
        albums_created = 0
        tracks_linked = 0
        
        for _, album_row in albums_df.iterrows():
            # Create album
            album = Album(
                album_name=album_row['album_name'],
                album_type=album_row.get('album_type', 'ep'),
                language=album_row.get('language', 'korean'),
            )
            session.add(album)
            session.flush()  # Get album_id
            
            albums_created += 1
            
            # Find songs from this album
            album_songs = songs_df[songs_df['album'] == album_row['album_name']]
            
            # Link songs to album
            for idx, song_row in enumerate(album_songs.iterrows(), 1):
                _, song_data = song_row
                
                # Find song in database by video_id
                song = session.query(Song).filter_by(
                    youtube_video_id=song_data.get('video_id')
                ).first()
                
                if song:
                    # Create album track link
                    album_track = AlbumTrack(
                        album_id=album.album_id,
                        song_id=song.song_id,
                        track_number=idx,  # Sequential for now
                        disc_number=1,
                    )
                    session.add(album_track)
                    tracks_linked += 1
        
        session.commit()
        
        print(f"   ✅ Created {albums_created} albums")
        print(f"   ✅ Linked {tracks_linked} album tracks")
    
    def insert_source_playlists(self, session):
        """Record which YTM playlists were used as sources"""
        print("\n📋 Recording source playlists...")
        
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
        print(f"   ✅ Recorded {len(playlists)} source playlists")
    
    def run(self):
        """Initialize complete database"""
        print("=" * 60)
        print("Database Initialization")
        print("=" * 60)
        
        # Check required files exist
        print("\n📂 Checking data files...")
        required_files = [self.songs_file, self.albums_file]
        for filepath in required_files:
            if not filepath.exists():
                print(f"   ❌ Missing: {filepath}")
                print(f"\n   Run data collection scripts first:")
                print(f"     python scripts/01_fetch_ytm_playlists.py")
                print(f"     python scripts/02_deduplicate_and_classify.py")
                print(f"     python scripts/03_extract_album_info.py")
                return
            print(f"   ✅ Found: {filepath}")
        
        # Load user preferences (optional)
        print("\n📊 Loading user preferences...")
        preferences = self.load_user_preferences()
        
        # Load data
        print("\n📥 Loading CSV data...")
        songs_df = pd.read_csv(self.songs_file)
        albums_df = pd.read_csv(self.albums_file)
        print(f"   ✅ Songs: {len(songs_df)}")
        print(f"   ✅ Albums: {len(albums_df)}")
        
        # Create database
        print(f"\n🗄️  Creating database: {Config.DATABASE_URL}")
        engine = create_database(Config.DATABASE_URL)
        session = get_session(engine)
        
        try:
            # Initialize parameters
            print("\n⚙️  Initializing Glicko-2 parameters...")
            initialize_parameters(session)
            
            # Insert data
            self.insert_songs(session, songs_df, preferences)
            self.insert_albums(session, albums_df, songs_df)
            self.insert_source_playlists(session)
            
            # Summary
            print("\n" + "=" * 60)
            print("✅ Database Initialization Complete!")
            print("=" * 60)
            
            # Stats
            total_songs = session.query(Song).count()
            total_albums = session.query(Album).count()
            total_tracks = session.query(AlbumTrack).count()
            
            print(f"\n📊 Database contents:")
            print(f"   Songs: {total_songs}")
            print(f"   Albums: {total_albums}")
            print(f"   Album tracks: {total_tracks}")
            
            # Rating distribution
            print(f"\n🎵 Song breakdown:")
            originals = session.query(Song).filter_by(is_original=True).count()
            variants = session.query(Song).filter_by(is_original=False).count()
            print(f"   Original songs: {originals}")
            print(f"   Variants: {variants}")
            
            print(f"\n🌍 Language distribution:")
            for lang in ['korean', 'japanese', 'english', 'instrumental']:
                count = session.query(Song).filter_by(language=lang).count()
                if count > 0:
                    print(f"   {lang.capitalize()}: {count}")
            
            print(f"\n⭐ Your personalized ratings:")
            liked = session.query(Song).filter_by(is_liked=True).count()
            familiar = session.query(Song).filter_by(is_familiar=True).count()
            print(f"   Liked songs (1600 Elo): {liked}")
            print(f"   Familiar songs (1550 Elo): {familiar}")
            
            print("\n" + "=" * 60)
            print("🚀 Next steps:")
            print("=" * 60)
            print("\n1. Start the app:")
            print("     streamlit run streamlit_app/app.py")
            print("\n2. Begin ranking in Duel Mode")
            print("3. Watch your ratings evolve!")
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error during initialization: {e}")
            session.rollback()
            raise
        
        finally:
            session.close()
        
        return True


def main():
    """Main entry point"""
    initializer = DatabaseInitializer()
    initializer.run()


if __name__ == '__main__':
    main()
