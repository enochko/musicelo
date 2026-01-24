"""
MusicElo - TWICE Song Ranking System

Main Streamlit application entry point
Uses Glicko-2 rating system for pairwise comparisons
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations

# Page configuration
st.set_page_config(
    page_title="MusicElo - TWICE Song Ranker",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🎵 MusicElo</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Rank your favorite TWICE songs using Glicko-2</p>', unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    """Get database connection (cached)"""
    return DatabaseOperations()

db = get_database()

# Get statistics
stats = db.get_statistics()

# Welcome section
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats['total_songs']}</div>
        <div class="stat-label">Total Songs</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats['total_comparisons']}</div>
        <div class="stat-label">Comparisons</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats['avg_rating']:.0f}</div>
        <div class="stat-label">Avg Rating</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats['max_rating']:.0f}</div>
        <div class="stat-label">Top Rating</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Features overview
st.header("🚀 Get Started")

col1, col2 = st.columns(2)

with col1:
    st.subheader("⚔️ Duel Mode")
    st.write("""
    **Compare songs head-to-head**
    
    - Listen to two songs
    - Choose your preference
    - Ratings update automatically using Glicko-2
    - Build your personal ranking!
    """)
    st.page_link("pages/1_⚔️_Duel_Mode.py", label="Start Ranking →", icon="⚔️")

with col2:
    st.subheader("📊 Rankings")
    st.write("""
    **View your song rankings**
    
    - See all songs sorted by rating
    - Filter by language, category, album
    - Track confidence levels
    - Export your rankings
    """)
    st.page_link("pages/3_📊_Rankings.py", label="View Rankings →", icon="📊")

st.markdown("---")

# How it works
with st.expander("ℹ️ How does MusicElo work?"):
    st.markdown("""
    ### Glicko-2 Rating System
    
    MusicElo uses the **Glicko-2 algorithm** - the same system used by chess ratings and competitive games.
    
    **Key Concepts:**
    
    1. **Rating (μ)**: Your song's current score (starts at 1500)
    2. **Rating Deviation (RD)**: How confident we are in the rating (lower = more confident)
    3. **Volatility (σ)**: How consistent the song's performance is
    
    **How ratings change:**
    
    - Beating a highly-rated song → Big rating increase
    - Losing to a low-rated song → Big rating decrease
    - Expected results → Small changes
    - More comparisons → More confidence (lower RD)
    
    **Your personalized start:**
    
    - ❤️ Liked songs started at **1600**
    - 👀 Familiar songs started at **1550**
    - 📚 To-listen songs started at **1525**
    - 🆕 Unknown songs started at **1500**
    
    This gives you a head start and reduces comparisons needed!
    """)

# Language breakdown
with st.expander("🌍 Song Collection"):
    st.markdown("### Language Distribution")
    
    lang_cols = st.columns(len(stats['language_breakdown']))
    for idx, (lang, count) in enumerate(stats['language_breakdown'].items()):
        with lang_cols[idx]:
            st.metric(lang.capitalize(), count)
    
    st.markdown(f"""
    ### Collection Sources
    
    Songs collected from 3 comprehensive YouTube Music playlists:
    - TWICE Complete Discography
    - All Songs Collection
    - Comprehensive Playlist
    
    **Includes:**
    - Group songs (title tracks & B-sides)
    - Japanese releases
    - English singles
    - Solo tracks (Nayeon, Jihyo, etc.)
    - Subunit songs (MISAMO)
    - Collaborations
    - Remixes & variants
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Made with ❤️ for TWICE fans</p>
    <p style="font-size: 0.9rem;">Powered by Glicko-2 • Data from YouTube Music</p>
</div>
""", unsafe_allow_html=True)
