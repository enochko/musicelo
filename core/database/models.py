"""
MusicElo Database Models

SQLAlchemy ORM models for the MusicElo database
Designed for YouTube Music as primary source, Spotify enrichment later

Schema supports:
- One song appearing on multiple albums
- Variants (Japanese versions, remixes, etc.) linked to originals
- Album sequential play with track numbers
- Future Spotify metadata enrichment
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, Date, Text, ForeignKey, Table, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Song(Base):
    """
    Songs table - stores individual songs and variants
    
    De-duplication strategy:
    - Same recording on multiple albums → ONE song, multiple album_tracks entries
    - Different recordings (variants) → Separate songs, linked via original_song_id
    
    Examples:
    - "Jelly Jelly" on Lane 1 and Lane 2 → 1 song, 2 album_tracks
    - "Like OOH-AHH" Korean vs Japanese → 2 songs, linked as variant
    """
    __tablename__ = 'songs'
    
    # Primary Key
    song_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Song Identity
    canonical_name = Column(String(200), nullable=False, index=True)
    """Base song name without variant suffixes (e.g., "Like OOH-AHH")"""
    
    # YouTube Music (Primary Source)
    youtube_music_url = Column(String(500))
    """Primary playback URL: https://music.youtube.com/watch?v=..."""
    
    youtube_video_id = Column(String(50), unique=True, index=True)
    """YouTube video ID (unique identifier)"""
    
    youtube_url = Column(String(500))
    """Standard YouTube URL: https://www.youtube.com/watch?v=..."""
    
    thumbnail_url = Column(String(500))
    """Album art / thumbnail URL"""
    
    # Variant Tracking
    is_original = Column(Boolean, default=True, nullable=False, index=True)
    """True if this is the original version, False if variant"""
    
    original_song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=True)
    """Points to original song if this is a variant"""
    
    variant_type = Column(String(50), nullable=True, index=True)
    """Type of variant: japanese_version, english_version, remix, live, instrumental, etc."""
    
    # Language
    language = Column(String(20), nullable=False, default='korean', index=True)
    """Song language: korean, japanese, english, instrumental"""
    
    # Basic Metadata
    duration_ms = Column(Integer)
    """Duration in milliseconds"""
    
    duration_seconds = Column(Integer)
    """Duration in seconds (from YouTube)"""
    
    release_date = Column(Date, nullable=True, index=True)
    """Official release date"""
    
    # Song Classification
    song_type = Column(String(50), index=True)
    """Type: title_track, b_side, ost, collaboration, solo, subunit"""
    
    category = Column(String(50), nullable=False, default='TWICE', index=True)
    """Category: TWICE, Solo, Subunit, Collaboration"""
    
    # Artist Information
    artist_name = Column(String(200), nullable=False, default='TWICE')
    """Primary artist(s)"""
    
    featured_artists = Column(String(200), nullable=True)
    """Featured/collaboration artists (comma-separated)"""
    
    # External IDs (for future enrichment)
    spotify_id = Column(String(50), nullable=True, unique=True, index=True)
    """Spotify track ID (when API becomes available)"""
    
    musicbrainz_id = Column(String(50), nullable=True)
    """MusicBrainz recording ID"""
    
    # Spotify Audio Features (NULL until enriched)
    valence = Column(Float, nullable=True)
    """Happiness/positivity (0.0 to 1.0)"""
    
    energy = Column(Float, nullable=True)
    """Energy level (0.0 to 1.0)"""
    
    danceability = Column(Float, nullable=True)
    """Danceability (0.0 to 1.0)"""
    
    acousticness = Column(Float, nullable=True)
    """Acoustic vs electronic (0.0 to 1.0)"""
    
    instrumentalness = Column(Float, nullable=True)
    """Instrumental vs vocal (0.0 to 1.0)"""
    
    speechiness = Column(Float, nullable=True)
    """Spoken word presence (0.0 to 1.0)"""
    
    liveness = Column(Float, nullable=True)
    """Live performance probability (0.0 to 1.0)"""
    
    tempo = Column(Float, nullable=True)
    """Beats per minute"""
    
    loudness = Column(Float, nullable=True)
    """Overall loudness in dB"""
    
    key = Column(Integer, nullable=True)
    """Musical key (0-11, C=0, C#=1, etc.)"""
    
    mode = Column(Integer, nullable=True)
    """Major (1) or Minor (0)"""
    
    time_signature = Column(Integer, nullable=True)
    """Time signature (e.g., 4 for 4/4)"""
    
    popularity = Column(Integer, nullable=True)
    """Spotify popularity score (0-100)"""
    
    # Glicko-2 Rating System
    rating = Column(Float, nullable=False, default=1500.0, index=True)
    """Current Glicko-2 rating"""
    
    rating_deviation = Column(Float, nullable=False, default=350.0)
    """Rating uncertainty (RD) - higher = less certain"""
    
    volatility = Column(Float, nullable=False, default=0.06)
    """Rating volatility (sigma) - consistency measure"""
    
    confidence_interval_lower = Column(Float, nullable=True)
    """Lower bound of 95% confidence interval (rating - 2*RD)"""
    
    confidence_interval_upper = Column(Float, nullable=True)
    """Upper bound of 95% confidence interval (rating + 2*RD)"""
    
    # Statistics
    games_played = Column(Integer, nullable=False, default=0)
    """Total number of comparisons"""
    
    wins = Column(Integer, nullable=False, default=0)
    """Number of wins"""
    
    losses = Column(Integer, nullable=False, default=0)
    """Number of losses"""
    
    draws = Column(Integer, nullable=False, default=0)
    """Number of draws"""
    
    last_compared = Column(DateTime, nullable=True)
    """Timestamp of last comparison"""
    
    # User Flags
    is_liked = Column(Boolean, default=False, index=True)
    """User has marked this as a favorite"""
    
    is_familiar = Column(Boolean, default=False)
    """User is familiar with this song"""
    
    notes = Column(Text, nullable=True)
    """User notes about the song"""
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    original = relationship('Song', remote_side=[song_id], backref='variants')
    """If this is a variant, link to the original song"""
    
    album_appearances = relationship('AlbumTrack', back_populates='song', cascade='all, delete-orphan')
    """All albums this song appears on"""
    
    comparisons_as_a = relationship('Comparison', foreign_keys='Comparison.song_a_id', back_populates='song_a')
    comparisons_as_b = relationship('Comparison', foreign_keys='Comparison.song_b_id', back_populates='song_b')
    
    def __repr__(self):
        return f"<Song(id={self.song_id}, name='{self.canonical_name}', language={self.language})>"


class Album(Base):
    """
    Albums table - TWICE albums, EPs, singles
    
    Examples:
    - TWICEcoaster: Lane 1 (EP, Korean)
    - #TWICE (Studio, Japanese)
    - The Feels (Single, English)
    """
    __tablename__ = 'albums'
    
    album_id = Column(Integer, primary_key=True, autoincrement=True)
    
    album_name = Column(String(200), nullable=False, unique=True, index=True)
    """Official album name"""
    
    album_type = Column(String(50), nullable=False, index=True)
    """Type: studio, ep, single, compilation, repackage, japanese"""
    
    release_date = Column(Date, nullable=True, index=True)
    """Official release date"""
    
    language = Column(String(20), nullable=False, default='korean')
    """Primary language: korean, japanese, english"""
    
    cover_url = Column(String(500), nullable=True)
    """Album cover art URL"""
    
    # External IDs
    spotify_album_id = Column(String(50), nullable=True, unique=True)
    """Spotify album ID (for future enrichment)"""
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tracks = relationship('AlbumTrack', back_populates='album', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Album(id={self.album_id}, name='{self.album_name}', type={self.album_type})>"


class AlbumTrack(Base):
    """
    Album-Song many-to-many relationship with track numbers
    
    Enables:
    - One song on multiple albums (e.g., "Jelly Jelly")
    - Album sequential play
    - Track number tracking
    
    Example:
    - Album: "TWICEcoaster: Lane 1", Song: "Jelly Jelly", Track: 5
    - Album: "TWICEcoaster: Lane 2", Song: "Jelly Jelly", Track: 5
    """
    __tablename__ = 'album_tracks'
    
    # Composite primary key
    album_id = Column(Integer, ForeignKey('albums.album_id'), primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), primary_key=True)
    track_number = Column(Integer, nullable=False, primary_key=True)
    """Track number within the album"""
    
    disc_number = Column(Integer, nullable=False, default=1)
    """Disc number for multi-disc albums"""
    
    # Relationships
    album = relationship('Album', back_populates='tracks')
    song = relationship('Song', back_populates='album_appearances')
    
    def __repr__(self):
        return f"<AlbumTrack(album_id={self.album_id}, song_id={self.song_id}, track={self.track_number})>"


class Comparison(Base):
    """
    Comparisons table - records all pairwise song comparisons
    
    Stores:
    - Before/after Glicko-2 ratings (full audit trail)
    - Outcome (win/draw/loss as float 0.0 to 1.0)
    - Comparison context (mode, sequential play, etc.)
    """
    __tablename__ = 'comparisons'
    
    comparison_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Songs being compared
    song_a_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False, index=True)
    song_b_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False, index=True)
    winner_id = Column(Integer, ForeignKey('songs.song_id'), nullable=True)
    """NULL for draws"""
    
    # Outcome (from Song A's perspective)
    outcome = Column(Float, nullable=False)
    """1.0 = A wins, 0.5 = draw, 0.0 = B wins, 0.75 = A slight win, etc."""
    
    outcome_type = Column(String(50), nullable=False)
    """decisive_win, slight_win, draw, slight_loss, decisive_loss"""
    
    # Comparison Context
    comparison_mode = Column(String(50), nullable=False, default='duel')
    """Mode: duel, playlist, smart, random"""
    
    was_sequential = Column(Boolean, default=False)
    """True if songs played back-to-back (playlist mode)"""
    
    # Before State (Song A)
    song_a_rating_before = Column(Float, nullable=False)
    song_a_rd_before = Column(Float, nullable=False)
    song_a_vol_before = Column(Float, nullable=False)
    
    # After State (Song A)
    song_a_rating_after = Column(Float, nullable=False)
    song_a_rd_after = Column(Float, nullable=False)
    song_a_vol_after = Column(Float, nullable=False)
    
    # Before State (Song B)
    song_b_rating_before = Column(Float, nullable=False)
    song_b_rd_before = Column(Float, nullable=False)
    song_b_vol_before = Column(Float, nullable=False)
    
    # After State (Song B)
    song_b_rating_after = Column(Float, nullable=False)
    song_b_rd_after = Column(Float, nullable=False)
    song_b_vol_after = Column(Float, nullable=False)
    
    # Metadata
    expected_outcome = Column(Float, nullable=True)
    """Expected probability of A winning (0.0 to 1.0)"""
    
    rating_impact = Column(Float, nullable=True)
    """Absolute rating change for Song A"""
    
    was_upset = Column(Boolean, default=False)
    """True if underdog won (expected < 0.4 but outcome = 1.0)"""
    
    user_notes = Column(Text, nullable=True)
    """Optional user notes about this comparison"""
    
    is_undone = Column(Boolean, default=False)
    """True if this comparison was undone"""
    
    # Relationships
    song_a = relationship('Song', foreign_keys=[song_a_id], back_populates='comparisons_as_a')
    song_b = relationship('Song', foreign_keys=[song_b_id], back_populates='comparisons_as_b')
    
    def __repr__(self):
        return f"<Comparison(id={self.comparison_id}, A={self.song_a_id} vs B={self.song_b_id}, outcome={self.outcome})>"


class Playlist(Base):
    """
    Generated playlists (mood-based, transition, etc.)
    """
    __tablename__ = 'playlists'
    
    playlist_id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String(200), nullable=False)
    """User-friendly playlist name"""
    
    generation_type = Column(String(50), nullable=False)
    """Type: mood, transition, top_rated, random, album_play"""
    
    parameters = Column(Text, nullable=True)
    """JSON string of generation parameters (e.g., {"mood": "happy", "min_valence": 0.7})"""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    overall_rating = Column(Float, nullable=True)
    """User's rating of the playlist (1-5 stars)"""
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    songs = relationship('PlaylistSong', back_populates='playlist', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Playlist(id={self.playlist_id}, name='{self.name}', type={self.generation_type})>"


class PlaylistSong(Base):
    """
    Playlist-Song relationship with playback tracking
    """
    __tablename__ = 'playlist_songs'
    
    playlist_id = Column(Integer, ForeignKey('playlists.playlist_id'), primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), primary_key=True)
    position = Column(Integer, nullable=False)
    """Position in playlist (1-indexed)"""
    
    was_played = Column(Boolean, default=False)
    """True if user played this song"""
    
    song_rating = Column(Float, nullable=True)
    """User's rating of this specific song in playlist context"""
    
    skip_time = Column(Integer, nullable=True)
    """Seconds into song when skipped (NULL if not skipped)"""
    
    # Relationships
    playlist = relationship('Playlist', back_populates='songs')
    song = relationship('Song')
    
    def __repr__(self):
        return f"<PlaylistSong(playlist={self.playlist_id}, song={self.song_id}, pos={self.position})>"


class Parameter(Base):
    """
    System parameters (Glicko-2 constants, etc.)
    """
    __tablename__ = 'parameters'
    
    param_name = Column(String(100), primary_key=True)
    param_value = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Parameter(name='{self.param_name}', value={self.param_value})>"


class YTMPlaylist(Base):
    """
    YouTube Music playlists used as data sources
    Tracks which community playlists were imported
    """
    __tablename__ = 'ytm_playlists'
    
    playlist_id = Column(String(100), primary_key=True)
    """YouTube Music playlist ID"""
    
    playlist_name = Column(String(200), nullable=False)
    playlist_url = Column(String(500), nullable=False)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    """When this playlist was last fetched"""
    
    track_count = Column(Integer, default=0)
    """Number of tracks in playlist"""
    
    def __repr__(self):
        return f"<YTMPlaylist(id='{self.playlist_id}', name='{self.playlist_name}')>"


# Database initialization functions

def create_database(database_url: str):
    """
    Create all tables in the database
    
    Args:
        database_url: SQLAlchemy database URL (e.g., 'sqlite:///data/musicelo.db')
    
    Returns:
        SQLAlchemy engine
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """
    Create a new database session
    
    Args:
        engine: SQLAlchemy engine
    
    Returns:
        SQLAlchemy session
    """
    Session = sessionmaker(bind=engine)
    return Session()


def initialize_parameters(session):
    """
    Initialize default Glicko-2 parameters
    
    Args:
        session: SQLAlchemy session
    """
    default_params = [
        Parameter(param_name='tau', param_value=0.5, 
                 description='System constant (constrains volatility changes)'),
        Parameter(param_name='epsilon', param_value=0.000001, 
                 description='Convergence tolerance'),
        Parameter(param_name='default_rd', param_value=350.0, 
                 description='Starting rating deviation'),
        Parameter(param_name='default_rating', param_value=1500.0, 
                 description='Starting rating'),
        Parameter(param_name='default_volatility', param_value=0.06, 
                 description='Starting volatility'),
        Parameter(param_name='rd_increase_per_day', param_value=0.5, 
                 description='RD increase when inactive'),
    ]
    
    for param in default_params:
        existing = session.query(Parameter).filter_by(param_name=param.param_name).first()
        if not existing:
            session.add(param)
    
    session.commit()


if __name__ == '__main__':
    # Example usage
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from config import Config
    
    print("=" * 60)
    print("MusicElo Database Models")
    print("=" * 60)
    
    # Create database
    print(f"\nCreating database: {Config.DATABASE_URL}")
    engine = create_database(Config.DATABASE_URL)
    
    print("✅ Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
    
    # Initialize parameters
    session = get_session(engine)
    initialize_parameters(session)
    print("\n✅ Default parameters initialized")
    
    session.close()
    print("\n" + "=" * 60)
