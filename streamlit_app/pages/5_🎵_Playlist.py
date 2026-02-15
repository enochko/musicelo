"""
Playlist Player - Sequential Ranking Mode

Features:
- Generate playlists based on filters/modes
- Import YouTube Music playlists (skips songs not in database)
- Play songs sequentially with embedded player
- Compare each song to previous (ladder ranking)
- Rate overall playlist
"""

import streamlit as st
from pathlib import Path
import sys
import random
import re
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations
from core.database.models import Song, Comparison
from core.services.glicko2_service import Glicko2Calculator, Opponent
from core.utils.security import escape_html, safe_youtube_embed

st.set_page_config(
    page_title="Playlist Player - MusicElo",
    page_icon="🎵",
    layout="wide",
)

# CSS
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .compact-song-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.8rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 0.8rem;
    }
    .compact-song-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin: 0;
    }
    .compact-song-meta {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_resource
def get_services():
    db = DatabaseOperations()
    calc = Glicko2Calculator()
    return db, calc

db, calc = get_services()

# Helper functions for YTM
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
if 'playlist' not in st.session_state:
    st.session_state.playlist = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'playlist_comparisons' not in st.session_state:
    st.session_state.playlist_comparisons = []
if 'playlist_complete' not in st.session_state:
    st.session_state.playlist_complete = False
if 'vote_recorded' not in st.session_state:
    st.session_state.vote_recorded = False

# Header
st.title("🎵 Playlist Player")
st.markdown("**Generate playlists and rank songs sequentially**")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "🎛️ Generate Playlist",
    "▶️ Play & Rank",
    "📊 Results"
])

# ==================== TAB 1: GENERATE ====================

with tab1:
    st.header("Generate Playlist")
    
    st.subheader("🎯 Playlist Mode")
    mode = st.radio(
        "Choose mode",
        options=[
            "🔍 Discover (Songs needing ratings)",
            "⭐ Favorites (Highly rated songs)",
            "🎲 Random Mix",
            "🎯 Focused (Custom filters)",
            "🎼 YouTube Music Playlist"
        ],
        help="Different modes prioritize different songs"
    )
    
    st.subheader("⚙️ Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        playlist_length = st.select_slider(
            "Playlist Length",
            options=[5, 10, 15, 20, 30, 50],
            value=10
        )
    
    with col2:
        player_height = st.slider(
            "Player Height (px)",
            min_value=250,
            max_value=600,
            value=400,
            step=50
        )
    
    with col3:
        autoplay = st.checkbox(
            "🔁 Autoplay",
            value=True,
            help="Automatically play songs when loaded"
        )
    
    # Mode-specific settings
    if mode == "🎯 Focused (Custom filters)":
        st.subheader("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            language_filter = st.multiselect(
                "Language",
                options=["korean", "japanese", "english", "instrumental"],
                default=["korean", "japanese", "english"]
            )
        
        with col2:
            category_filter = st.multiselect(
                "Category",
                options=["TWICE", "Solo", "Subunit", "Collaboration"],
                default=["TWICE", "Solo", "Subunit", "Collaboration"]
            )
        
        with col3:
            include_variants = st.checkbox("Include variants", value=False)
        
        min_rating = st.slider(
            "Minimum Rating",
            min_value=1000,
            max_value=2000,
            value=1400,
            step=50
        )
    
    elif mode == "🎼 YouTube Music Playlist":
        st.subheader("🎼 YouTube Music Playlist")
        
        # Playlist URL input
        playlist_url = st.text_input(
            "YouTube Music Playlist URL",
            placeholder="https://music.youtube.com/playlist?list=...",
            help="Paste a public or unlisted playlist URL"
        )
        
        # Order option
        playlist_order = st.radio(
            "Playlist Order",
            options=["As-is (original order)", "Randomised"],
            help="Play in original order or shuffle"
        )
        
        st.info("💡 **Note:** Songs not in your database will be automatically skipped. To add new songs from playlists, use the **Import Songs** page.")
    
    st.markdown("---")
    
    # Generate button
    if mode == "🎼 YouTube Music Playlist":
        # YTM playlist flow
        if playlist_url and st.button("🎵 Read YouTube Music Playlist", type="primary"):
            with st.spinner("Reading playlist from YouTube Music..."):
                try:
                    # Import ytmusicapi
                    from ytmusicapi import YTMusic
                    
                    # Try authenticated, fall back to unauthenticated
                    try:
                        ytmusic = YTMusic('browser.json')
                    except FileNotFoundError:
                        ytmusic = YTMusic()
                    
                    # Extract playlist ID
                    playlist_id = extract_playlist_id(playlist_url)
                    
                    # Get playlist
                    playlist_data = ytmusic.get_playlist(playlist_id, limit=100)
                    
                    # Match to database
                    matched, unmatched = match_ytm_tracks_to_db(playlist_data['tracks'], db)
                    
                    if matched:
                        # Extract song IDs
                        song_ids = [db_song.song_id for _, db_song in matched]
                        
                        # Randomise if requested
                        if playlist_order.startswith("Randomised"):
                            random.shuffle(song_ids)
                        
                        # Create playlist
                        st.session_state.playlist = {
                            'songs': song_ids,
                            'mode': mode,
                            'length': len(song_ids),
                            'created_at': datetime.now(),
                            'player_height': player_height,
                            'autoplay': autoplay,
                            'ytm_source': playlist_data['title'],
                            'ytm_total': len(playlist_data['tracks']),
                            'ytm_skipped': len(unmatched),
                        }
                        
                        st.session_state.current_index = 0
                        st.session_state.playlist_comparisons = []
                        st.session_state.playlist_complete = False
                        st.session_state.vote_recorded = False
                        
                        # Show results
                        st.success(f"✅ Loaded: **{playlist_data['title']}**")
                        st.info(f"📊 **{len(matched)}/{len(playlist_data['tracks'])}** songs found in your database")
                        
                        if unmatched:
                            st.warning(f"⚠️ **{len(unmatched)}** song{'s' if len(unmatched) != 1 else ''} not in database (will be skipped)")
                            
                            with st.expander(f"📋 View {len(unmatched)} skipped song{'s' if len(unmatched) != 1 else ''}"):
                                for track in unmatched:
                                    artist = track['artists'][0]['name'] if track.get('artists') else "Unknown"
                                    st.write(f"• {track['title']} - {artist}")
                            
                            st.info("💡 **To add these songs:** Use the **Import Songs** page to add missing songs to your database")
                        
                        st.success("👉 Switch to **Play & Rank** tab to start!")
                    
                    else:
                        st.error(f"❌ No songs from this playlist found in your database")
                        st.info("💡 Use the **Import Songs** page to add songs from this playlist first")
                
                except ImportError:
                    st.error("❌ ytmusicapi not installed. Run: `pip install ytmusicapi`")
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Error reading playlist: {e}")
                    st.info("Make sure the playlist is public or unlisted")
        
        elif not playlist_url:
            st.info("👆 Enter a YouTube Music playlist URL to continue")
    
    else:
        # Regular playlist generation
        if st.button("🎵 Generate Playlist", type="primary"):
            with st.spinner("Generating playlist..."):
                # Get songs based on mode
                if mode == "🔍 Discover (Songs needing ratings)":
                    songs = db.search_songs(language=None, category=None, is_original=True, min_games=0)
                    songs = sorted(songs, key=lambda s: (-s.rating_deviation, s.games_played))
                    playlist_songs = songs[:playlist_length]
                
                elif mode == "⭐ Favorites (Highly rated songs)":
                    songs = db.search_songs(language=None, category=None, is_original=True, min_games=5)
                    songs = sorted(songs, key=lambda s: (-s.rating, s.rating_deviation))
                    playlist_songs = songs[:playlist_length]
                
                elif mode == "🎲 Random Mix":
                    songs = db.search_songs(language=None, category=None, is_original=True, min_games=0)
                    weights = [max(s.rating - 1000, 100) for s in songs]
                    playlist_songs = random.choices(songs, weights=weights, k=min(playlist_length, len(songs)))
                
                else:  # Focused
                    lang = language_filter if language_filter else None
                    cat = category_filter if category_filter else None
                    
                    songs = db.search_songs(
                        language=None if not lang else (lang[0] if len(lang) == 1 else None),
                        category=None if not cat else (cat[0] if len(cat) == 1 else None),
                        is_original=None if include_variants else True,
                        min_games=0
                    )
                    
                    if lang and len(lang) > 1:
                        songs = [s for s in songs if s.language in lang]
                    if cat and len(cat) > 1:
                        songs = [s for s in songs if s.category in cat]
                    songs = [s for s in songs if s.rating >= min_rating]
                    playlist_songs = random.sample(songs, min(playlist_length, len(songs)))
                
                if playlist_songs:
                    st.session_state.playlist = {
                        'songs': [s.song_id for s in playlist_songs],
                        'mode': mode,
                        'length': len(playlist_songs),
                        'created_at': datetime.now(),
                        'player_height': player_height,
                        'autoplay': autoplay,
                    }
                    st.session_state.current_index = 0
                    st.session_state.playlist_comparisons = []
                    st.session_state.playlist_complete = False
                    st.session_state.vote_recorded = False
                    
                    st.success(f"✅ Generated playlist with {len(playlist_songs)} songs!")
                    st.info("👉 Switch to 'Play & Rank' tab to start")
                else:
                    st.error("No songs match your criteria. Try different filters.")

# ==================== TAB 2: PLAY & RANK ====================

with tab2:
    if not st.session_state.playlist:
        st.info("👈 Generate a playlist first in the 'Generate Playlist' tab")
    elif st.session_state.playlist_complete:
        st.success("🎉 Playlist complete! Check the 'Results' tab")
    else:
        playlist = st.session_state.playlist
        current_idx = st.session_state.current_index
        song_ids = playlist['songs']
        
        # Sidebar - Playlist panel
        with st.sidebar:
            st.subheader("📋 Playlist")
            st.caption(f"{current_idx + 1} / {len(song_ids)} songs")
            
            # Show source if YTM
            if playlist.get('ytm_source'):
                st.caption(f"📼 {playlist['ytm_source']}")
                if playlist.get('ytm_skipped', 0) > 0:
                    st.caption(f"⚠️ {playlist['ytm_skipped']} songs skipped")
            
            for i, song_id in enumerate(song_ids):
                song = db.get_song(song_id)
                if i < current_idx:
                    status = "✓"
                elif i == current_idx:
                    status = "►"
                else:
                    status = "  "
                st.caption(f"{status} {i + 1}. {song.canonical_name[:30]}")
        
        # Progress
        st.progress((current_idx + 1) / len(song_ids), text=f"Song {current_idx + 1} of {len(song_ids)}")
        
        # Current song - COMPACT HEADER
        current_song = db.get_song(song_ids[current_idx])
        
        st.markdown(f"""
        <div class="compact-song-header">
            <div class="compact-song-title">{escape_html(current_song.canonical_name)}</div>
            <div class="compact-song-meta">
                {escape_html(current_song.artist_name)} • 
                {current_song.language.capitalize()} • 
                {current_song.category}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Player
        if current_song.youtube_video_id:
            iframe = safe_youtube_embed(
                current_song.youtube_video_id,
                height=playlist['player_height'],
                autoplay=playlist.get('autoplay', False)
            )
            if iframe:
                st.markdown(iframe, unsafe_allow_html=True)
            else:
                st.error("Invalid video ID")
        
        # Comparison
        if current_idx > 0:
            st.markdown("---")
            
            if not st.session_state.vote_recorded:
                # Voting interface
                prev_song = db.get_song(song_ids[current_idx - 1])
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                def record_comparison(outcome_value, outcome_label):
                    """Record comparison and update ratings"""
                    # Store old values
                    old_rating_prev = prev_song.rating
                    old_rd_prev = prev_song.rating_deviation
                    old_vol_prev = prev_song.volatility
                    
                    old_rating_curr = current_song.rating
                    old_rd_curr = current_song.rating_deviation
                    old_vol_curr = current_song.volatility
                    
                    # Update ratings
                    result_prev = calc.update_rating(
                        prev_song.rating, prev_song.rating_deviation, prev_song.volatility,
                        opponents=[Opponent(
                            rating=current_song.rating,
                            rating_deviation=current_song.rating_deviation,
                            outcome=outcome_value
                        )]
                    )
                    
                    result_curr = calc.update_rating(
                        current_song.rating, current_song.rating_deviation, current_song.volatility,
                        opponents=[Opponent(
                            rating=prev_song.rating,
                            rating_deviation=prev_song.rating_deviation,
                            outcome=1.0 - outcome_value
                        )]
                    )
                    
                    # Update database
                    db.update_song_rating(prev_song.song_id, result_prev.rating, result_prev.rating_deviation, result_prev.volatility)
                    db.update_song_rating(current_song.song_id, result_curr.rating, result_curr.rating_deviation, result_curr.volatility)
                    db.update_song_stats(prev_song.song_id, outcome_value)
                    db.update_song_stats(current_song.song_id, 1.0 - outcome_value)
                    
                    # Record comparison
                    comparison = db.record_comparison(
                        prev_song.song_id,
                        current_song.song_id,
                        outcome_value,
                        outcome_label,
                        (old_rating_prev, old_rd_prev, old_vol_prev),
                        (result_prev.rating, result_prev.rating_deviation, result_prev.volatility),
                        (old_rating_curr, old_rd_curr, old_vol_curr),
                        (result_curr.rating, result_curr.rating_deviation, result_curr.volatility),
                        comparison_mode='playlist'
                    )
                    
                    # Store in session
                    st.session_state.playlist_comparisons.append({
                        'comparison_id': comparison.comparison_id,
                        'prev_song': prev_song.canonical_name,
                        'curr_song': current_song.canonical_name,
                        'outcome': outcome_label,
                        'prev_delta': result_prev.rating - old_rating_prev,
                        'curr_delta': result_curr.rating - old_rating_curr,
                        'prev_new_rating': result_prev.rating,
                        'curr_new_rating': result_curr.rating,
                        'prev_old_rating': old_rating_prev,
                        'prev_old_rd': old_rd_prev,
                        'prev_old_vol': old_vol_prev,
                        'curr_old_rating': old_rating_curr,
                        'curr_old_rd': old_rd_curr,
                        'curr_old_vol': old_vol_curr,
                        'prev_song_id': prev_song.song_id,
                        'curr_song_id': current_song.song_id,
                    })
                    
                    st.session_state.vote_recorded = True
                
                with col1:
                    if st.button(
                        f"🔥 {prev_song.canonical_name} (Strong)",
                        use_container_width=True,
                        help=f"{prev_song.canonical_name} is WAY better"
                    ):
                        record_comparison(1.0, "landslide_prev")
                        st.rerun()
                
                with col2:
                    if st.button(
                        f"👍 {prev_song.canonical_name} (Slight)",
                        use_container_width=True,
                        help=f"{prev_song.canonical_name} is better"
                    ):
                        record_comparison(0.75, "slight_prev")
                        st.rerun()
                
                with col3:
                    if st.button(
                        "🤝 Draw / Equal",
                        use_container_width=True,
                        help="Both songs are equally good"
                    ):
                        record_comparison(0.5, "equal")
                        st.rerun()
                
                with col4:
                    if st.button(
                        f"👍 {current_song.canonical_name} (Slight)",
                        use_container_width=True,
                        help=f"{current_song.canonical_name} is better"
                    ):
                        record_comparison(0.25, "slight_curr")
                        st.rerun()
                
                with col5:
                    if st.button(
                        f"🔥 {current_song.canonical_name} (Strong)",
                        use_container_width=True,
                        help=f"{current_song.canonical_name} is WAY better"
                    ):
                        record_comparison(0.0, "landslide_curr")
                        st.rerun()
            
            else:
                # SHOW RATING CHANGES
                last_comp = st.session_state.playlist_comparisons[-1]
                
                st.success("✅ Vote recorded!")
                
                # Rating changes
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**{escape_html(last_comp['prev_song'])}**")
                    st.metric(
                        "Rating",
                        f"{last_comp['prev_new_rating']:.0f}",
                        f"{last_comp['prev_delta']:+.0f}"
                    )
                
                with col2:
                    st.markdown(f"**{escape_html(last_comp['curr_song'])}**")
                    st.metric(
                        "Rating",
                        f"{last_comp['curr_new_rating']:.0f}",
                        f"{last_comp['curr_delta']:+.0f}"
                    )
                
                st.markdown("---")
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("↩️ Undo Vote", type="secondary", use_container_width=True):
                        # MANUAL UNDO
                        if st.session_state.playlist_comparisons:
                            last_comp = st.session_state.playlist_comparisons[-1]
                            
                            session = db.Session()
                            try:
                                comparison = session.query(Comparison).filter_by(
                                    comparison_id=last_comp['comparison_id']
                                ).first()
                                
                                if comparison:
                                    comparison.is_undone = True
                                    
                                    prev_song_db = session.query(Song).filter_by(
                                        song_id=last_comp['prev_song_id']
                                    ).first()
                                    curr_song_db = session.query(Song).filter_by(
                                        song_id=last_comp['curr_song_id']
                                    ).first()
                                    
                                    if prev_song_db and curr_song_db:
                                        # Revert ratings
                                        prev_song_db.rating = last_comp['prev_old_rating']
                                        prev_song_db.rating_deviation = last_comp['prev_old_rd']
                                        prev_song_db.volatility = last_comp['prev_old_vol']
                                        
                                        curr_song_db.rating = last_comp['curr_old_rating']
                                        curr_song_db.rating_deviation = last_comp['curr_old_rd']
                                        curr_song_db.volatility = last_comp['curr_old_vol']
                                        
                                        # Revert stats
                                        outcome = comparison.outcome
                                        if outcome == 1.0:
                                            prev_song_db.wins -= 1
                                            curr_song_db.losses -= 1
                                        elif outcome == 0.0:
                                            prev_song_db.losses -= 1
                                            curr_song_db.wins -= 1
                                        else:
                                            prev_song_db.draws -= 1
                                            curr_song_db.draws -= 1
                                        
                                        prev_song_db.games_played -= 1
                                        curr_song_db.games_played -= 1
                                    
                                    session.commit()
                            finally:
                                session.close()
                            
                            st.session_state.playlist_comparisons.pop()
                            st.session_state.vote_recorded = False
                            st.rerun()
                
                with col2:
                    if st.button("➡️ Next Song", type="primary", use_container_width=True):
                        st.session_state.current_index += 1
                        st.session_state.vote_recorded = False
                        
                        if st.session_state.current_index >= len(song_ids):
                            st.session_state.playlist_complete = True
                        
                        st.rerun()
        
        else:
            # First song
            st.info("🎧 This is the first song. Listen and enjoy!")
            
            st.markdown("---")
            if st.button("➡️ Next Song", type="primary"):
                st.session_state.current_index += 1
                st.rerun()
        
        # Skip button - ONLY SHOW IF NOT VOTED
        if not st.session_state.vote_recorded:
            st.markdown("---")
            if st.button("⏭️ Skip Song", help="Skip to next song without voting"):
                st.session_state.current_index += 1
                st.session_state.vote_recorded = False
                
                if st.session_state.current_index >= len(song_ids):
                    st.session_state.playlist_complete = True
                
                st.rerun()

# ==================== TAB 3: RESULTS ====================

with tab3:
    if not st.session_state.playlist:
        st.info("👈 Generate a playlist first")
    elif not st.session_state.playlist_complete:
        st.info("Complete the playlist to see results")
    else:
        st.header("Playlist Results")
        
        playlist = st.session_state.playlist
        comparisons = st.session_state.playlist_comparisons
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Songs Played", playlist['length'])
        with col2:
            st.metric("Comparisons Made", len(comparisons))
        with col3:
            st.metric("Mode", playlist['mode'])
        
        # Show YTM source if imported
        if playlist.get('ytm_source'):
            st.info(f"📼 Source: **{playlist['ytm_source']}**")
            if playlist.get('ytm_total'):
                st.caption(f"Played {playlist['length']} of {playlist['ytm_total']} total songs")
        
        st.markdown("---")
        st.subheader("⭐ Rate This Playlist")
        
        playlist_rating = st.radio(
            "How would you rate this playlist overall?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: "⭐" * x,
            horizontal=True
        )
        
        feedback = st.text_area(
            "Optional feedback",
            placeholder="What did you like or dislike about this playlist?"
        )
        
        if st.button("💾 Save Rating"):
            st.success("✅ Playlist rating saved!")
            st.balloons()
        
        # Comparison history
        if comparisons:
            st.markdown("---")
            st.subheader("📊 Comparison History")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📖 Expand All"):
                    for i in range(len(comparisons)):
                        st.session_state[f'expand_comp_{i}'] = True
                    st.rerun()
            with col2:
                if st.button("📕 Collapse All"):
                    for i in range(len(comparisons)):
                        st.session_state[f'expand_comp_{i}'] = False
                    st.rerun()
            
            for i, comp in enumerate(comparisons, 1):
                expanded = st.session_state.get(f'expand_comp_{i}', False)
                
                with st.expander(f"Comparison {i}: {comp['prev_song']} vs {comp['curr_song']}", expanded=expanded):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**{comp['prev_song']}**")
                        st.write(f"Rating change: {comp['prev_delta']:+.0f}")
                    
                    with col2:
                        st.write(f"**{comp['curr_song']}**")
                        st.write(f"Rating change: {comp['curr_delta']:+.0f}")
                    
                    st.write(f"**Outcome:** {comp['outcome']}")
        
        st.markdown("---")
        if st.button("🎵 Generate New Playlist"):
            st.session_state.playlist = None
            st.session_state.current_index = 0
            st.session_state.playlist_comparisons = []
            st.session_state.playlist_complete = False
            st.session_state.vote_recorded = False
            st.rerun()

# Help
with st.expander("ℹ️ How to use Playlist Player"):
    st.markdown("""
    ### Playlist Modes
    
    **🔍 Discover** - Songs with high uncertainty (high RD)
    **⭐ Favorites** - Highest-rated songs (requires 5+ comparisons)
    **🎲 Random Mix** - Weighted random (higher rated = higher chance)
    **🎯 Focused** - Custom filters (language, category, rating)
    **🎼 YouTube Music** - Import public/unlisted YTM playlists (skips songs not in DB)
    
    ### YouTube Music Playlists
    
    - Paste any public or unlisted playlist URL
    - Songs not in your database are automatically skipped
    - To add new songs, use the **Import Songs** page
    
    ### Voting Options
    
    - **🔥 Strong**: One song is MUCH better (1.0 vs 0.0)
    - **👍 Slight**: One song is better (0.75 vs 0.25)
    - **🤝 Equal**: Both equally good (0.5 vs 0.5)
    
    ### Tips
    
    - Use **Discover mode** to focus on songs needing ratings
    - **Undo** is available after each vote
    - You can **skip** songs that don't match your mood
    - Sequential ranking is faster but less accurate than Duel Mode
    """)
