"""
Import Songs - Add songs from YouTube Music playlists

Features:
- Import songs from YouTube Music playlists
- Match against database (including aliases)
- Preview unmatched songs
- Add new songs to database
"""

import streamlit as st
from pathlib import Path
import sys
import re
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations
from core.database.models import Song
from core.utils.security import escape_html, safe_youtube_embed

st.set_page_config(
    page_title="Import Songs - MusicElo",
    page_icon="📥",
    layout="wide",
)

# CSS
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_resource
def get_database():
    return DatabaseOperations()

db = get_database()

# Helper functions
def extract_playlist_id(url: str) -> str:
    """Extract playlist ID from YouTube Music URL"""
    match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid playlist URL - must contain 'list=' parameter")

def match_ytm_tracks_to_db(ytm_tracks, db_operations):
    """
    Match YouTube Music tracks to database songs
    Checks both canonical songs AND aliases
    """
    matched = []
    unmatched = []
    
    session = db_operations.Session()
    try:
        for track in ytm_tracks:
            video_id = track.get('videoId')
            
            if video_id:
                # Check canonical songs first
                db_song = session.query(Song).filter_by(
                    youtube_video_id=video_id,
                    is_original=True
                ).first()
                
                # If not found, check aliases
                if not db_song:
                    alias_song = session.query(Song).filter_by(
                        youtube_video_id=video_id,
                        is_original=False
                    ).first()
                    
                    if alias_song and alias_song.original_song_id:
                        # Get the canonical song
                        db_song = session.query(Song).filter_by(
                            song_id=alias_song.original_song_id
                        ).first()
                
                if db_song:
                    matched.append((track, db_song))
                else:
                    unmatched.append(track)
            else:
                unmatched.append(track)
    finally:
        session.close()
    
    return matched, unmatched

# Session state
if 'ytm_preview' not in st.session_state:
    st.session_state.ytm_preview = None
if 'ytm_matched' not in st.session_state:
    st.session_state.ytm_matched = []
if 'ytm_unmatched' not in st.session_state:
    st.session_state.ytm_unmatched = []
if 'import_complete' not in st.session_state:
    st.session_state.import_complete = False
if 'added_songs' not in st.session_state:
    st.session_state.added_songs = []

# Header
st.title("📥 Import Songs")
st.markdown("**Add new songs to your database from YouTube Music playlists**")

# Tabs
tab1, tab2 = st.tabs([
    "📋 Import from Playlist",
    "📊 Import History"
])

# ==================== TAB 1: IMPORT ====================

with tab1:
    if st.session_state.import_complete:
        # Show completion summary
        st.success("✅ Import complete!")
        
        added = st.session_state.added_songs
        st.metric("Songs Added", len(added))
        
        if added:
            with st.expander(f"📋 View {len(added)} added songs"):
                for song in added:
                    st.write(f"• {song['name']} - {song['artist']}")
        
        if st.button("➕ Import Another Playlist", type="primary"):
            st.session_state.ytm_preview = None
            st.session_state.ytm_matched = []
            st.session_state.ytm_unmatched = []
            st.session_state.import_complete = False
            st.session_state.added_songs = []
            st.rerun()
    
    elif st.session_state.ytm_unmatched:
        # Show add songs interface
        st.header("➕ Add Songs to Database")
        
        unmatched = st.session_state.ytm_unmatched
        preview = st.session_state.ytm_preview
        
        st.info(f"📋 Adding songs from: **{preview['title']}**")
        st.write(f"**{len(unmatched)}** song{'s' if len(unmatched) != 1 else ''} not in your database")
        
        st.markdown("---")
        
        # Add songs one by one
        added_count = 0
        added_songs_list = []
        
        for i, track in enumerate(unmatched, 1):
            with st.expander(f"🆕 {i}. {track['title']}", expanded=(i == 1)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Auto-filled from YTM
                    name = st.text_input(
                        "Song Name", 
                        value=track['title'], 
                        key=f"name_{i}"
                    )
                    artist = st.text_input(
                        "Artist", 
                        value=track['artists'][0]['name'] if track.get('artists') else "Unknown",
                        key=f"artist_{i}"
                    )
                
                with col2:
                    # User must select
                    lang = st.selectbox(
                        "Language",
                        ["korean", "japanese", "english", "instrumental"],
                        key=f"lang_{i}"
                    )
                    cat = st.selectbox(
                        "Category",
                        ["TWICE", "Solo", "Subunit", "Collaboration"],
                        key=f"cat_{i}"
                    )
                
                # Preview player
                if track.get('videoId'):
                    iframe = safe_youtube_embed(track['videoId'], height=200)
                    if iframe:
                        st.markdown(iframe, unsafe_allow_html=True)
                
                # Add button
                button_key = f"add_{i}"
                added_key = f"added_{i}"
                
                # Check if already added this session
                if st.session_state.get(added_key, False):
                    st.success(f"✅ Added: {st.session_state.get(f'added_name_{i}', name)}")
                else:
                    if st.button(f"✅ Add This Song", key=button_key, type="primary"):
                        # Add to database
                        new_song = Song(
                            canonical_name=name,
                            artist_name=artist,
                            youtube_video_id=track.get('videoId'),
                            language=lang,
                            category=cat,
                            is_original=True
                        )
                        
                        session = db.Session()
                        try:
                            session.add(new_song)
                            session.commit()
                            session.refresh(new_song)
                            
                            # Mark as added
                            st.session_state[added_key] = True
                            st.session_state[f'added_name_{i}'] = name
                            
                            added_songs_list.append({
                                'name': name,
                                'artist': artist,
                                'song_id': new_song.song_id
                            })
                            
                            added_count += 1
                            
                            st.success(f"✅ Added: {name}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error adding song: {e}")
                        finally:
                            session.close()
        
        st.markdown("---")
        
        # Done button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Finish Import", type="primary", use_container_width=True):
                # Collect all added songs
                all_added = []
                for i in range(1, len(unmatched) + 1):
                    if st.session_state.get(f"added_{i}", False):
                        all_added.append({
                            'name': st.session_state.get(f'added_name_{i}', ''),
                            'artist': '',
                        })
                
                st.session_state.added_songs = all_added
                st.session_state.import_complete = True
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel Import", type="secondary", use_container_width=True):
                st.session_state.ytm_preview = None
                st.session_state.ytm_matched = []
                st.session_state.ytm_unmatched = []
                st.rerun()
    
    else:
        # Show import form
        st.header("Import from YouTube Music Playlist")
        
        st.markdown("""
        ### How it works:
        
        1. **Paste** a YouTube Music playlist URL
        2. **Match** songs against your database (including aliases)
        3. **Add** any new songs not in your database
        4. **Done!** Songs are ready to use in playlists and rankings
        """)
        
        st.markdown("---")
        
        # Playlist URL input
        playlist_url = st.text_input(
            "YouTube Music Playlist URL",
            placeholder="https://music.youtube.com/playlist?list=...",
            help="Paste a public or unlisted playlist URL"
        )
        
        if playlist_url and st.button("📥 Import Playlist", type="primary"):
            with st.spinner("Fetching playlist from YouTube Music..."):
                try:
                    # Import ytmusicapi
                    from ytmusicapi import YTMusic
                    
                    # Try authenticated, fall back to unauthenticated
                    try:
                        ytmusic = YTMusic('browser.json')
                    except FileNotFoundError:
                        st.info("💡 Using unauthenticated mode (public playlists only)")
                        ytmusic = YTMusic()
                    
                    # Extract playlist ID
                    playlist_id = extract_playlist_id(playlist_url)
                    
                    # Get playlist
                    playlist_data = ytmusic.get_playlist(playlist_id, limit=100)
                    
                    # Match to database
                    matched, unmatched = match_ytm_tracks_to_db(playlist_data['tracks'], db)
                    
                    # Store in session state
                    st.session_state.ytm_preview = {
                        'title': playlist_data['title'],
                        'total': len(playlist_data['tracks'])
                    }
                    st.session_state.ytm_matched = matched
                    st.session_state.ytm_unmatched = unmatched
                    
                    # Show results
                    st.success(f"✅ Fetched: **{playlist_data['title']}**")
                    st.info(f"📊 **{len(matched)}/{len(playlist_data['tracks'])}** songs already in your database")
                    
                    if unmatched:
                        st.warning(f"⚠️ **{len(unmatched)}** song{'s' if len(unmatched) != 1 else ''} not in database")
                        
                        with st.expander(f"📋 Preview {len(unmatched)} new song{'s' if len(unmatched) != 1 else ''}"):
                            for track in unmatched:
                                artist = track['artists'][0]['name'] if track.get('artists') else "Unknown"
                                st.write(f"• {track['title']} - {artist}")
                        
                        st.success("👇 Click below to add these songs!")
                        
                        if st.button("➕ Add New Songs", type="primary", key="start_add"):
                            st.rerun()
                    else:
                        st.success("🎉 All songs already in your database!")
                        st.info("You can use this playlist in the Playlist Player now")
                
                except ImportError:
                    st.error("❌ ytmusicapi not installed. Run: `pip install ytmusicapi`")
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Error fetching playlist: {e}")
                    st.info("Make sure the playlist is public or unlisted")
        
        elif not playlist_url:
            st.info("👆 Enter a YouTube Music playlist URL to begin")

# ==================== TAB 2: HISTORY ====================

with tab2:
    st.header("Import History")
    
    st.info("🚧 **Coming soon!** This will show your import history and statistics.")
    
    # Placeholder for future implementation
    st.markdown("""
    ### Planned features:
    
    - View all imported playlists
    - Track which songs came from which playlist
    - Re-import playlists to find new songs
    - Import statistics and analytics
    """)

# Help
with st.expander("ℹ️ How to use Import Songs"):
    st.markdown("""
    ### Importing Songs
    
    1. **Find a YouTube Music playlist** you want to import
    2. **Copy the playlist URL** (must be public or unlisted)
    3. **Paste the URL** in the import form
    4. **Review** which songs are new
    5. **Add songs** one by one with metadata
    
    ### Song Matching
    
    The system automatically matches songs by YouTube video ID and checks:
    - **Canonical songs** (original songs in your database)
    - **Aliases** (merged duplicates that point to canonical songs)
    
    If a song matches an alias, the canonical song will be used in playlists.
    
    ### Adding New Songs
    
    For each new song:
    - **Song name and artist** are auto-filled from YouTube Music
    - **Language and category** must be selected manually
    - **Preview player** lets you verify it's the right song
    
    ### Tips
    
    - Import playlists from trusted sources first
    - Double-check language/category selections
    - Use the Admin panel to merge duplicates if needed
    - Imported songs are immediately available in Playlist Player
    """)
