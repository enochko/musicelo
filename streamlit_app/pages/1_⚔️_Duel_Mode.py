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

st.set_page_config(
    page_title="Duel Mode - MusicElo",
    page_icon="⚔️",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .song-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .song-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .song-artist {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    .song-rating {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .song-rd {
        font-size: 1rem;
        opacity: 0.8;
    }
    .vs-divider {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        color: #667eea;
        padding: 2rem 0;
    }
    .outcome-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database and calculator
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
st.markdown("**Compare two songs and choose your preference**")

# Initialize session state
if 'comparison_count' not in st.session_state:
    st.session_state.comparison_count = 0

if 'current_pair' not in st.session_state:
    st.session_state.current_pair = None

if 'show_result' not in st.session_state:
    st.session_state.show_result = False

if 'last_comparison' not in st.session_state:
    st.session_state.last_comparison = None  # Store last comparison for undo

# Sidebar - Filters and Stats
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Filter options
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
    
    include_variants = st.checkbox("Include variants (remixes, etc.)", value=False)
    
    min_games = st.slider("Minimum comparisons", 0, 20, 0)
    
    st.markdown("---")
    
    # Session stats
    st.subheader("📊 Session Stats")
    st.metric("Comparisons Made", st.session_state.comparison_count)
    
    total_comparisons = db.get_comparison_count()
    st.metric("Total Comparisons", total_comparisons)
    
    st.markdown("---")
    
    # Quick actions
    if st.button("🔄 New Pair", width="stretch"):
        st.session_state.current_pair = None
        st.session_state.show_result = False
        st.rerun()

# Get songs based on filters
def get_filtered_songs():
    """Get songs based on current filters"""
    language = None if language_filter == "All" else language_filter.lower()
    category = None if category_filter == "All" else category_filter
    
    songs = db.search_songs(
        language=language,
        category=category,
        is_original=None if include_variants else True,
        min_games=min_games
    )
    
    return songs

# Select a random pair
def select_random_pair():
    """Select two random songs for comparison"""
    songs = get_filtered_songs()
    
    if len(songs) < 2:
        return None, None
    
    # Use smart pairing: similar ratings
    songs.sort(key=lambda s: s.rating)
    
    # Pick a random song
    idx = random.randint(0, len(songs) - 1)
    song_a = songs[idx]
    
    # Pick opponent within ±200 rating range
    candidates = [
        s for s in songs 
        if s.song_id != song_a.song_id 
        and abs(s.rating - song_a.rating) < 200
    ]
    
    if not candidates:
        candidates = [s for s in songs if s.song_id != song_a.song_id]
    
    song_b = random.choice(candidates) if candidates else songs[(idx + 1) % len(songs)]
    
    return song_a, song_b

# Load current pair
if st.session_state.current_pair is None:
    song_a, song_b = select_random_pair()
    if song_a and song_b:
        st.session_state.current_pair = (song_a.song_id, song_b.song_id)
    else:
        st.error("Not enough songs match your filters. Try relaxing the filters.")
        st.stop()

# Get current songs
song_a = db.get_song(st.session_state.current_pair[0])
song_b = db.get_song(st.session_state.current_pair[1])

# Calculate expected outcome
expected_a = calc.win_probability(song_a.rating, song_a.rating_deviation, 
                                   song_b.rating, song_b.rating_deviation)

# Define undo function before it's used
def undo_last_comparison():
    """Undo the last comparison"""
    if not st.session_state.last_comparison:
        st.warning("No comparison to undo")
        return
    
    last = st.session_state.last_comparison
    
    # Mark comparison as undone in database
    from sqlalchemy import update
    session = db.Session()
    try:
        # Import Comparison model
        from core.database.models import Comparison
        
        # Mark as undone
        session.query(Comparison).filter_by(
            comparison_id=last['comparison_id']
        ).update({'is_undone': True})
        
        # Restore previous ratings
        song_a = session.query(Song).filter_by(song_id=last['song_a_id']).first()
        song_b = session.query(Song).filter_by(song_id=last['song_b_id']).first()
        
        if song_a:
            song_a.rating = last['song_a_before'][0]
            song_a.rating_deviation = last['song_a_before'][1]
            song_a.volatility = last['song_a_before'][2]
            song_a.confidence_interval_lower = song_a.rating - 2 * song_a.rating_deviation
            song_a.confidence_interval_upper = song_a.rating + 2 * song_a.rating_deviation
            
            # Decrement stats
            song_a.games_played = max(0, song_a.games_played - 1)
            if last['outcome_value'] == 1.0:
                song_a.wins = max(0, song_a.wins - 1)
            elif last['outcome_value'] == 0.0:
                song_a.losses = max(0, song_a.losses - 1)
            else:
                song_a.draws = max(0, song_a.draws - 1)
        
        if song_b:
            song_b.rating = last['song_b_before'][0]
            song_b.rating_deviation = last['song_b_before'][1]
            song_b.volatility = last['song_b_before'][2]
            song_b.confidence_interval_lower = song_b.rating - 2 * song_b.rating_deviation
            song_b.confidence_interval_upper = song_b.rating + 2 * song_b.rating_deviation
            
            # Decrement stats
            song_b.games_played = max(0, song_b.games_played - 1)
            song_b_outcome = 1.0 - last['outcome_value']
            if song_b_outcome == 1.0:
                song_b.wins = max(0, song_b.wins - 1)
            elif song_b_outcome == 0.0:
                song_b.losses = max(0, song_b.losses - 1)
            else:
                song_b.draws = max(0, song_b.draws - 1)
        
        session.commit()
    finally:
        session.close()
    
    # Clear last comparison
    st.session_state.last_comparison = None
    st.session_state.comparison_count = max(0, st.session_state.comparison_count - 1)
    st.session_state.show_result = False
    
    st.success("↩️ Comparison undone! Ratings restored.")

# Display songs
col1, col_vs, col2 = st.columns([5, 1, 5])

with col1:
    st.markdown(f"""
    <div class="song-card">
        <div>
            <div class="song-title">{song_a.canonical_name}</div>
            <div class="song-artist">{song_a.artist_name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Embedded YouTube player
    if song_a.youtube_video_id:
        st.markdown(f"""
        <iframe width="100%" height="450" 
                src="https://www.youtube.com/embed/{song_a.youtube_video_id}?autoplay=0" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
        """, unsafe_allow_html=True)
    
    # Details in expander (hidden by default)
    with st.expander("📊 View Stats"):
        st.markdown(f"""
        **Current Rating**: {song_a.rating:.0f} ±{song_a.rating_deviation:.0f}
        
        **Details:**
        - Language: {song_a.language.capitalize()}
        - Category: {song_a.category}
        - Games: {song_a.games_played} ({song_a.wins}W-{song_a.losses}L-{song_a.draws}D)
        """)


with col_vs:
    st.markdown('<div class="vs-divider">VS</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="song-card">
        <div>
            <div class="song-title">{song_b.canonical_name}</div>
            <div class="song-artist">{song_b.artist_name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Embedded YouTube player
    if song_b.youtube_video_id:
        st.markdown(f"""
        <iframe width="100%" height="450" 
                src="https://www.youtube.com/embed/{song_b.youtube_video_id}?autoplay=0" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
        """, unsafe_allow_html=True)
    
    # Details in expander (hidden by default)
    with st.expander("📊 View Stats"):
        st.markdown(f"""
        **Current Rating**: {song_b.rating:.0f} ±{song_b.rating_deviation:.0f}
        
        **Details:**
        - Language: {song_b.language.capitalize()}
        - Category: {song_b.category}
        - Games: {song_b.games_played} ({song_b.wins}W-{song_b.losses}L-{song_b.draws}D)
        """)


# Outcome selection
st.markdown("---")
st.subheader("🎯 Which song do you prefer?")

col1, col2, col3, col4, col5 = st.columns(5)

def record_outcome(outcome_value, outcome_label):
    """Record comparison outcome and update ratings"""
    # Get current ratings
    song_a_before = (song_a.rating, song_a.rating_deviation, song_a.volatility)
    song_b_before = (song_b.rating, song_b.rating_deviation, song_b.volatility)
    
    # Update ratings using Opponent objects
    result_a = calc.update_rating(
        song_a.rating, song_a.rating_deviation, song_a.volatility,
        opponents=[Opponent(
            rating=song_b.rating,
            rating_deviation=song_b.rating_deviation,
            outcome=outcome_value
        )]
    )
    
    result_b = calc.update_rating(
        song_b.rating, song_b.rating_deviation, song_b.volatility,
        opponents=[Opponent(
            rating=song_a.rating,
            rating_deviation=song_a.rating_deviation,
            outcome=1.0 - outcome_value
        )]
    )
    
    # Extract new ratings
    new_a_rating = result_a.rating
    new_a_rd = result_a.rating_deviation
    new_a_vol = result_a.volatility
    
    new_b_rating = result_b.rating
    new_b_rd = result_b.rating_deviation
    new_b_vol = result_b.volatility
    
    song_a_after = (new_a_rating, new_a_rd, new_a_vol)
    song_b_after = (new_b_rating, new_b_rd, new_b_vol)
    
    # Update database
    db.update_song_rating(song_a.song_id, new_a_rating, new_a_rd, new_a_vol)
    db.update_song_rating(song_b.song_id, new_b_rating, new_b_rd, new_b_vol)
    
    db.update_song_stats(song_a.song_id, outcome_value)
    db.update_song_stats(song_b.song_id, 1.0 - outcome_value)
    
    # Record comparison
    comparison = db.record_comparison(
        song_a.song_id, song_b.song_id,
        outcome_value, outcome_label,
        song_a_before, song_a_after,
        song_b_before, song_b_after,
        comparison_mode='duel'
    )
    
    # Store for undo
    st.session_state.last_comparison = {
        'comparison_id': comparison.comparison_id,
        'song_a_id': song_a.song_id,
        'song_b_id': song_b.song_id,
        'song_a_before': song_a_before,
        'song_b_before': song_b_before,
        'outcome_label': outcome_label,
        'outcome_value': outcome_value,
    }
    
    # Update session state
    st.session_state.comparison_count += 1
    st.session_state.show_result = True
    st.session_state.result_data = {
        'song_a_delta': new_a_rating - song_a.rating,
        'song_b_delta': new_b_rating - song_b.rating,
        'outcome_label': outcome_label,
    }

with col1:
    if st.button(f"🏆 {song_a.canonical_name} (Strong)", width="stretch"):
        record_outcome(1.0, "decisive_win")
        st.rerun()

with col2:
    if st.button(f"✓ {song_a.canonical_name} (Slight)", width="stretch"):
        record_outcome(0.75, "slight_win")
        st.rerun()

with col3:
    if st.button("🤝 Draw / Equal", width="stretch"):
        record_outcome(0.5, "draw")
        st.rerun()

with col4:
    if st.button(f"✓ {song_b.canonical_name} (Slight)", width="stretch"):
        record_outcome(0.25, "slight_loss")
        st.rerun()

with col5:
    if st.button(f"🏆 {song_b.canonical_name} (Strong)", width="stretch"):
        record_outcome(0.0, "decisive_loss")
        st.rerun()

# Show result
if st.session_state.show_result:
    st.success(f"✅ Comparison recorded! Outcome: {st.session_state.result_data['outcome_label']}")
    
    col1, col2 = st.columns(2)
    with col1:
        delta = st.session_state.result_data['song_a_delta']
        st.metric(
            f"{song_a.canonical_name}",
            f"{song_a.rating:.0f}",
            f"{delta:+.0f}"
        )
    with col2:
        delta = st.session_state.result_data['song_b_delta']
        st.metric(
            f"{song_b.canonical_name}",
            f"{song_b.rating:.0f}",
            f"{delta:+.0f}"
        )
    
    # Action buttons
    col_next, col_undo = st.columns([3, 1])
    
    with col_next:
        if st.button("➡️ Next Comparison", type="primary", width="stretch"):
            st.session_state.current_pair = None
            st.session_state.show_result = False
            st.rerun()
    
    with col_undo:
        if st.button("↩️ Undo", width="stretch"):
            undo_last_comparison()
            st.rerun()

# Help section
with st.expander("ℹ️ How to use Duel Mode"):
    st.markdown("""
    ### Making Comparisons
    
    1. **Listen** to both songs (click YouTube Music links)
    2. **Choose** your preference:
       - 🏆 **Strong preference**: You clearly prefer one song
       - ✓ **Slight preference**: You prefer one, but it's close
       - 🤝 **Draw**: You like them equally
    
    3. **Ratings update** automatically using Glicko-2
    
    ### Tips
    
    - **Be honest!** There are no wrong answers
    - **Consistent choices** lead to better ratings
    - **More comparisons** = more accurate rankings
    - Use **filters** to focus on specific categories
    
    ### Rating Changes
    
    - Upsets (underdog wins) cause bigger changes
    - Expected outcomes cause smaller changes
    - Rating Deviation decreases with more comparisons
    """)
