"""
Duel Mode - Song Comparison Interface

Head-to-head song comparisons with Glicko-2 rating updates
"""

import streamlit as st
from pathlib import Path
import sys
import random

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations
from core.database.models import Song, Comparison
from core.services.glicko2_service import Glicko2Calculator, Opponent
from core.utils.security import escape_html, safe_youtube_embed

st.set_page_config(
    page_title="Duel Mode - MusicElo",
    page_icon="⚔️",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .song-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        min-height: 80px;
    }
    .song-title {
        font-size: 1.6rem;
        font-weight: bold;
        margin-bottom: 0.2rem;
    }
    .song-artist {
        font-size: 1rem;
        opacity: 0.9;
    }
    .vs-divider {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        color: #667eea;
        padding: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_resource
def get_database():
    return DatabaseOperations()

@st.cache_resource
def get_calculator():
    return Glicko2Calculator()

db = get_database()
calc = get_calculator()

# Page header
st.title("⚔️ Duel Mode")

# Session state
if 'comparison_count' not in st.session_state:
    st.session_state.comparison_count = 0
if 'current_pair' not in st.session_state:
    st.session_state.current_pair = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'last_comparison' not in st.session_state:
    st.session_state.last_comparison = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("Song Selection")
    language_filter = st.selectbox(
        "Language",
        ["All", "Korean", "Japanese", "English"],
        key="language_filter"
    )
    category_filter = st.selectbox(
        "Category",
        ["All", "TWICE", "Solo", "Subunit", "Collaboration"],
        key="category_filter"
    )
    variants_enabled = st.checkbox(
        "Include Variants",
        value=False,
        help="Include remixes, alternate versions, etc."
    )
    
    st.subheader("Player Settings")
    player_height = st.slider(
        "Player Height (px)",
        min_value=250,
        max_value=600,
        value=400,
        step=50
    )
    
    st.markdown("---")
    st.subheader("📊 Your Progress")
    session = db.Session()
    try:
        total_songs = session.query(Song).count()
        total_comparisons = session.query(Comparison).filter_by(is_undone=False).count()
    finally:
        session.close()
    st.metric("Total Songs", total_songs)
    st.metric("Total Comparisons", total_comparisons)
    st.metric("This Session", st.session_state.comparison_count)

# Filters
lang_filter = None if language_filter == "All" else language_filter.lower()
cat_filter = None if category_filter == "All" else category_filter

# Get song pair
if st.session_state.current_pair is None:
    songs = db.search_songs(
        language=lang_filter,
        category=cat_filter,
        is_original=None if variants_enabled else True
    )
    
    if len(songs) < 2:
        st.error("Not enough songs matching your filters. Try different settings.")
        st.stop()
    
    song_a, song_b = random.sample(songs, 2)
    st.session_state.current_pair = (song_a.song_id, song_b.song_id)

# Get songs
song_a = db.get_song(st.session_state.current_pair[0])
song_b = db.get_song(st.session_state.current_pair[1])

if not song_a or not song_b:
    st.error("Error loading songs. Please try again.")
    st.session_state.current_pair = None
    st.stop()

# Display songs (ALWAYS VISIBLE - songs stay on screen)
col1, col_vs, col2 = st.columns([5, 1, 5])

with col1:
    st.markdown(f"""
    <div class="song-card">
        <div class="song-title">{escape_html(song_a.canonical_name)}</div>
        <div class="song-artist">{escape_html(song_a.artist_name)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if song_a.youtube_video_id:
        iframe = safe_youtube_embed(song_a.youtube_video_id, height=player_height)
        if iframe:
            st.markdown(iframe, unsafe_allow_html=True)
        else:
            st.error("Invalid video ID")
    
    with st.expander("ℹ️ Song Details"):
        st.write(f"**Language:** {song_a.language}")
        st.write(f"**Category:** {song_a.category}")
        st.write(f"**Rating:** {song_a.rating:.0f} ±{song_a.rating_deviation:.0f}")
        st.write(f"**Games:** {song_a.games_played}")
        if song_a.games_played > 0:
            win_rate = (song_a.wins / song_a.games_played * 100)
            st.write(f"**Win Rate:** {win_rate:.1f}%")

with col_vs:
    st.markdown('<div class="vs-divider">VS</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="song-card">
        <div class="song-title">{escape_html(song_b.canonical_name)}</div>
        <div class="song-artist">{escape_html(song_b.artist_name)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if song_b.youtube_video_id:
        iframe = safe_youtube_embed(song_b.youtube_video_id, height=player_height)
        if iframe:
            st.markdown(iframe, unsafe_allow_html=True)
        else:
            st.error("Invalid video ID")
    
    with st.expander("ℹ️ Song Details"):
        st.write(f"**Language:** {song_b.language}")
        st.write(f"**Category:** {song_b.category}")
        st.write(f"**Rating:** {song_b.rating:.0f} ±{song_b.rating_deviation:.0f}")
        st.write(f"**Games:** {song_b.games_played}")
        if song_b.games_played > 0:
            win_rate = (song_b.wins / song_b.games_played * 100)
            st.write(f"**Win Rate:** {win_rate:.1f}%")

# Voting/Result buttons (where voting buttons are)
st.markdown("---")

if st.session_state.show_result and st.session_state.last_comparison:
    # Show result in place of voting buttons
    comp = st.session_state.last_comparison
    
    st.success("✅ Comparison recorded!")
    
    # Rating changes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{escape_html(comp['song_a_name'])}**")
        delta_a = comp['song_a_new_rating'] - comp['song_a_old_rating']
        st.metric("Rating", f"{comp['song_a_new_rating']:.0f}", f"{delta_a:+.0f}")
    
    with col2:
        st.markdown(f"**{escape_html(comp['song_b_name'])}**")
        delta_b = comp['song_b_new_rating'] - comp['song_b_old_rating']
        st.metric("Rating", f"{comp['song_b_new_rating']:.0f}", f"{delta_b:+.0f}")
    
    st.markdown("---")
    
    # Action buttons (in place of voting buttons)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↩️ Undo", type="secondary", use_container_width=True):
            if comp['comparison_id']:
                session = db.Session()
                try:
                    comparison = session.query(Comparison).filter_by(
                        comparison_id=comp['comparison_id']
                    ).first()
                    
                    if comparison:
                        comparison.is_undone = True
                        
                        song_a_db = session.query(Song).filter_by(song_id=comparison.song_a_id).first()
                        song_b_db = session.query(Song).filter_by(song_id=comparison.song_b_id).first()
                        
                        if song_a_db and song_b_db:
                            # Revert ratings
                            song_a_db.rating = comp['song_a_old_rating']
                            song_a_db.rating_deviation = comp['song_a_old_rd']
                            song_a_db.volatility = comp['song_a_old_vol']
                            
                            song_b_db.rating = comp['song_b_old_rating']
                            song_b_db.rating_deviation = comp['song_b_old_rd']
                            song_b_db.volatility = comp['song_b_old_vol']
                            
                            # Revert stats
                            outcome = comparison.outcome
                            if outcome == 1.0:
                                song_a_db.wins -= 1
                                song_b_db.losses -= 1
                            elif outcome == 0.0:
                                song_a_db.losses -= 1
                                song_b_db.wins -= 1
                            else:
                                song_a_db.draws -= 1
                                song_b_db.draws -= 1
                            
                            song_a_db.games_played -= 1
                            song_b_db.games_played -= 1
                        
                        session.commit()
                finally:
                    session.close()
                
                st.session_state.show_result = False
                st.session_state.last_comparison = None
                st.session_state.comparison_count -= 1
                st.rerun()
    
    with col2:
        if st.button("➡️ Next Comparison", type="primary", use_container_width=True):
            st.session_state.show_result = False
            st.session_state.current_pair = None
            st.rerun()
    
    with col3:
        if st.button("📊 View Rankings", use_container_width=True):
            st.switch_page("pages/3_📊_Rankings.py")

else:
    # Voting buttons
    st.markdown("### 🎵 Which song do you prefer?")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    def record_vote(outcome_a: float, outcome_b: float, label: str):
        """Record comparison and update ratings"""
        # Store old values
        old_rating_a = song_a.rating
        old_rd_a = song_a.rating_deviation
        old_vol_a = song_a.volatility
        
        old_rating_b = song_b.rating
        old_rd_b = song_b.rating_deviation
        old_vol_b = song_b.volatility
        
        # Update ratings
        result_a = calc.update_rating(
            song_a.rating, song_a.rating_deviation, song_a.volatility,
            opponents=[Opponent(
                rating=song_b.rating,
                rating_deviation=song_b.rating_deviation,
                outcome=outcome_a
            )]
        )
        
        result_b = calc.update_rating(
            song_b.rating, song_b.rating_deviation, song_b.volatility,
            opponents=[Opponent(
                rating=song_a.rating,
                rating_deviation=song_a.rating_deviation,
                outcome=outcome_b
            )]
        )
        
        # Update database
        db.update_song_rating(song_a.song_id, result_a.rating, result_a.rating_deviation, result_a.volatility)
        db.update_song_rating(song_b.song_id, result_b.rating, result_b.rating_deviation, result_b.volatility)
        db.update_song_stats(song_a.song_id, outcome_a)
        db.update_song_stats(song_b.song_id, outcome_b)
        
        # Record comparison
        comparison = db.record_comparison(
            song_a.song_id,
            song_b.song_id,
            outcome_a,
            label,
            (old_rating_a, old_rd_a, old_vol_a),
            (result_a.rating, result_a.rating_deviation, result_a.volatility),
            (old_rating_b, old_rd_b, old_vol_b),
            (result_b.rating, result_b.rating_deviation, result_b.volatility),
            comparison_mode='duel'
        )
        
        # Store for display
        st.session_state.last_comparison = {
            'comparison_id': comparison.comparison_id,
            'song_a_name': song_a.canonical_name,
            'song_b_name': song_b.canonical_name,
            'song_a_old_rating': old_rating_a,
            'song_a_old_rd': old_rd_a,
            'song_a_old_vol': old_vol_a,
            'song_a_new_rating': result_a.rating,
            'song_b_old_rating': old_rating_b,
            'song_b_old_rd': old_rd_b,
            'song_b_old_vol': old_vol_b,
            'song_b_new_rating': result_b.rating,
        }
        
        st.session_state.show_result = True
        st.session_state.comparison_count += 1
    
    with col1:
        if st.button(
            f"🔥 {song_a.canonical_name} (Strong)",
            use_container_width=True,
            help=f"{song_a.canonical_name} is WAY better"
        ):
            record_vote(1.0, 0.0, "landslide_a")
            st.rerun()
    
    with col2:
        if st.button(
            f"👍 {song_a.canonical_name} (Slight)",
            use_container_width=True,
            help=f"{song_a.canonical_name} is better"
        ):
            record_vote(0.75, 0.25, "slight_a")
            st.rerun()
    
    with col3:
        if st.button(
            "🤝 Draw / Equal",
            use_container_width=True,
            help="Both songs are equally good"
        ):
            record_vote(0.5, 0.5, "draw")
            st.rerun()
    
    with col4:
        if st.button(
            f"👍 {song_b.canonical_name} (Slight)",
            use_container_width=True,
            help=f"{song_b.canonical_name} is better"
        ):
            record_vote(0.25, 0.75, "slight_b")
            st.rerun()
    
    with col5:
        if st.button(
            f"🔥 {song_b.canonical_name} (Strong)",
            use_container_width=True,
            help=f"{song_b.canonical_name} is WAY better"
        ):
            record_vote(0.0, 1.0, "landslide_b")
            st.rerun()
    
    # Skip (only when not showing result)
    st.markdown("---")
    if st.button("⏭️ Skip This Pair", help="Get a new pair of songs"):
        st.session_state.current_pair = None
        st.rerun()

# Help
with st.expander("ℹ️ How to use Duel Mode"):
    st.markdown("""
    ### Making Comparisons
    
    1. **Listen** to both songs
    2. **Choose** which you prefer using the buttons
    3. **View results** to see rating changes
    4. **Continue** or **Undo** if you made a mistake
    
    ### Voting Options
    
    - **🔥 Strong**: One song is MUCH better (1.0 vs 0.0)
    - **👍 Slight**: One song is better (0.75 vs 0.25)
    - **🤝 Equal**: Both songs are equally good (0.5 vs 0.5)
    
    ### Tips
    
    - More comparisons = more accurate rankings
    - Focus on songs with high uncertainty (high RD)
    - Use filters to focus on specific categories
    - You can undo your last comparison
    
    ### Glicko-2 Rating System
    
    - **Rating**: Base score (higher = better)
    - **RD** (Rating Deviation): Uncertainty (lower = more confident)
    - **Games**: Number of comparisons
    """)
