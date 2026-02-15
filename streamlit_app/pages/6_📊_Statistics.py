"""
Statistics Dashboard - Analytics and Insights

Features:
- Rating distribution
- Comparison activity
- Top/bottom songs
- Category breakdowns
- Progress tracking
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations
from sqlalchemy import func, and_

st.set_page_config(
    page_title="Statistics - MusicElo",
    page_icon="📊",
    layout="wide",
)

# Hide Streamlit header
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_resource
def get_db():
    return DatabaseOperations()

db = get_db()

# Page header
st.title("📊 Statistics Dashboard")
st.markdown("**Your ranking progress and insights**")

# Get data
from core.database.models import Song, Comparison

session = db.Session()

try:
    # Overall stats
    total_songs = session.query(Song).count()
    total_comparisons = session.query(Comparison).filter_by(is_undone=False).count()
    
    # Songs by category
    songs_by_category = session.query(
        Song.category,
        func.count(Song.song_id)
    ).group_by(Song.category).all()
    
    # Songs by language
    songs_by_language = session.query(
        Song.language,
        func.count(Song.song_id)
    ).group_by(Song.language).all()
    
    # Rating statistics
    avg_rating = session.query(func.avg(Song.rating)).scalar() or 1500
    min_rating = session.query(func.min(Song.rating)).scalar() or 1500
    max_rating = session.query(func.max(Song.rating)).scalar() or 1500
    
    # Uncertainty stats
    avg_rd = session.query(func.avg(Song.rating_deviation)).scalar() or 350
    high_uncertainty = session.query(Song).filter(Song.rating_deviation > 250).count()
    low_uncertainty = session.query(Song).filter(Song.rating_deviation < 100).count()
    
    # Activity stats
    songs_never_played = session.query(Song).filter(Song.games_played == 0).count()
    songs_well_ranked = session.query(Song).filter(Song.games_played >= 10).count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_comparisons = session.query(Comparison).filter(
        Comparison.timestamp >= week_ago,
        Comparison.is_undone == False
    ).count()
    
    # Top 10 songs
    top_songs = session.query(Song).filter(
        Song.games_played >= 5
    ).order_by(Song.rating.desc()).limit(10).all()
    
    # Most active (games played)
    most_active = session.query(Song).order_by(
        Song.games_played.desc()
    ).limit(10).all()
    
    # Biggest movers (highest volatility)
    biggest_movers = session.query(Song).filter(
        Song.games_played >= 3
    ).order_by(Song.volatility.desc()).limit(10).all()
    
finally:
    session.close()

# ==================== OVERVIEW METRICS ====================

st.header("📈 Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Songs",
        f"{total_songs:,}",
        help="Songs in your collection"
    )

with col2:
    st.metric(
        "Comparisons",
        f"{total_comparisons:,}",
        delta=f"+{recent_comparisons} this week",
        help="Total head-to-head comparisons"
    )

with col3:
    st.metric(
        "Avg Rating",
        f"{avg_rating:.0f}",
        help="Mean Glicko-2 rating"
    )

with col4:
    st.metric(
        "Rating Spread",
        f"{max_rating - min_rating:.0f}",
        help="Difference between top and bottom"
    )

# ==================== COLLECTION BREAKDOWN ====================

st.markdown("---")
st.header("🎵 Collection Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.subheader("By Category")
    
    if songs_by_category:
        cat_df = pd.DataFrame(songs_by_category, columns=['Category', 'Count'])
        st.bar_chart(cat_df.set_index('Category'))
        
        for category, count in songs_by_category:
            pct = (count / total_songs * 100)
            st.write(f"**{category}**: {count} songs ({pct:.1f}%)")

with col2:
    st.subheader("By Language")
    
    if songs_by_language:
        lang_df = pd.DataFrame(songs_by_language, columns=['Language', 'Count'])
        st.bar_chart(lang_df.set_index('Language'))
        
        for language, count in songs_by_language:
            pct = (count / total_songs * 100)
            st.write(f"**{language.capitalize()}**: {count} songs ({pct:.1f}%)")

# ==================== RANKING PROGRESS ====================

st.markdown("---")
st.header("📊 Ranking Progress")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Never Played",
        f"{songs_never_played}",
        delta=f"-{songs_never_played} to go",
        delta_color="inverse",
        help="Songs with 0 comparisons"
    )

with col2:
    st.metric(
        "Well Ranked",
        f"{songs_well_ranked}",
        delta=f"{songs_well_ranked/total_songs*100:.1f}%",
        help="Songs with 10+ comparisons"
    )

with col3:
    st.metric(
        "High Confidence",
        f"{low_uncertainty}",
        delta=f"{low_uncertainty/total_songs*100:.1f}%",
        help="Songs with RD < 100"
    )

# Progress bar
progress_pct = (total_songs - songs_never_played) / total_songs
st.progress(progress_pct, text=f"Overall Progress: {progress_pct*100:.1f}%")

# ==================== UNCERTAINTY ANALYSIS ====================

st.markdown("---")
st.header("🎯 Confidence Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Avg Uncertainty",
        f"±{avg_rd:.0f}",
        help="Average rating deviation (lower = better)"
    )

with col2:
    st.metric(
        "High Uncertainty",
        f"{high_uncertainty}",
        help="Songs with RD > 250 (need more comparisons)"
    )

with col3:
    st.metric(
        "Low Uncertainty",
        f"{low_uncertainty}",
        help="Songs with RD < 100 (well-established)"
    )

# Recommendation
if high_uncertainty > 100:
    st.warning(f"💡 **Tip:** You have {high_uncertainty} songs with high uncertainty. Use Playlist's **Discover mode** to rank them efficiently!")
elif songs_never_played > 50:
    st.info(f"💡 **Tip:** You have {songs_never_played} unplayed songs. Start with random comparisons in Duel Mode!")
else:
    st.success("✅ **Great job!** Your rankings are well-established. Keep it up!")

# ==================== TOP SONGS ====================

st.markdown("---")
st.header("⭐ Top Rated Songs")

if top_songs:
    st.markdown("Songs with at least 5 comparisons, ranked by rating:")
    
    for i, song in enumerate(top_songs, 1):
        with st.expander(f"#{i} - **{song.canonical_name}** ({song.rating:.0f})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Artist:** {song.artist_name}")
                st.write(f"**Language:** {song.language}")
                st.write(f"**Category:** {song.category}")
            
            with col2:
                st.write(f"**Rating:** {song.rating:.0f} ±{song.rating_deviation:.0f}")
                st.write(f"**Confidence:** {'High' if song.rating_deviation < 100 else 'Medium' if song.rating_deviation < 200 else 'Low'}")
            
            with col3:
                st.write(f"**Games:** {song.games_played}")
                win_rate = (song.wins / song.games_played * 100) if song.games_played > 0 else 0
                st.write(f"**Win Rate:** {win_rate:.1f}%")
                st.write(f"**Record:** {song.wins}W-{song.losses}L-{song.draws}D")
            
            if song.youtube_music_url:
                st.markdown(f"[▶️ Play on YouTube Music]({song.youtube_music_url})")
else:
    st.info("No songs with enough comparisons yet. Keep ranking!")

# ==================== MOST ACTIVE ====================

st.markdown("---")
st.header("🔥 Most Active Songs")

if most_active:
    st.markdown("Songs with the most comparisons:")
    
    for i, song in enumerate(most_active, 1):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{i}. {song.canonical_name}**")
            st.caption(f"{song.artist_name} • {song.language}")
        
        with col2:
            st.write(f"**{song.games_played}** games")
        
        with col3:
            win_rate = (song.wins / song.games_played * 100) if song.games_played > 0 else 0
            st.write(f"{win_rate:.0f}% wins")

# ==================== BIGGEST MOVERS ====================

st.markdown("---")
st.header("📈 Biggest Movers")

if biggest_movers:
    st.markdown("Songs with highest volatility (ratings changing the most):")
    
    for i, song in enumerate(biggest_movers, 1):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{i}. {song.canonical_name}**")
            st.caption(f"{song.artist_name}")
        
        with col2:
            st.write(f"Rating: **{song.rating:.0f}**")
        
        with col3:
            st.write(f"σ: **{song.volatility:.3f}**")

st.caption("σ (sigma) = volatility. Higher values mean ratings are still changing significantly.")

# ==================== ACTIVITY TIMELINE ====================

st.markdown("---")
st.header("📅 Recent Activity")

# Get comparisons from last 30 days
session = db.Session()
try:
    days_ago_30 = datetime.utcnow() - timedelta(days=30)
    
    daily_activity = session.query(
        func.date(Comparison.timestamp).label('date'),
        func.count(Comparison.comparison_id).label('count')
    ).filter(
        Comparison.timestamp >= days_ago_30,
        Comparison.is_undone == False
    ).group_by(
        func.date(Comparison.timestamp)
    ).order_by('date').all()
    
    if daily_activity:
        df = pd.DataFrame(daily_activity, columns=['Date', 'Comparisons'])
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        st.line_chart(df)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Last 7 Days", f"{recent_comparisons} comparisons")
        
        with col2:
            total_30_days = sum(c for _, c in daily_activity)
            st.metric("Last 30 Days", f"{total_30_days} comparisons")
        
        with col3:
            avg_per_day = total_30_days / 30
            st.metric("Avg Per Day", f"{avg_per_day:.1f} comparisons")
    else:
        st.info("No activity in the last 30 days. Start ranking!")
        
finally:
    session.close()

# ==================== EXPORT DATA ====================

st.markdown("---")
st.header("💾 Export Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Export Rankings to CSV"):
        session = db.Session()
        try:
            all_songs = session.query(Song).order_by(Song.rating.desc()).all()
            
            data = []
            for song in all_songs:
                data.append({
                    'Rank': len(data) + 1,
                    'Song': song.canonical_name,
                    'Artist': song.artist_name,
                    'Rating': song.rating,
                    'RD': song.rating_deviation,
                    'Games': song.games_played,
                    'Wins': song.wins,
                    'Losses': song.losses,
                    'Draws': song.draws,
                    'Win %': (song.wins / song.games_played * 100) if song.games_played > 0 else 0,
                    'Language': song.language,
                    'Category': song.category,
                })
            
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"musicelo_rankings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            st.success("✅ CSV ready for download!")
        finally:
            session.close()

with col2:
    if st.button("📈 Export Comparison History"):
        session = db.Session()
        try:
            all_comparisons = session.query(Comparison).order_by(
                Comparison.timestamp.desc()
            ).all()
            
            data = []
            for comp in all_comparisons:
                song_a = session.query(Song).filter_by(song_id=comp.song_a_id).first()
                song_b = session.query(Song).filter_by(song_id=comp.song_b_id).first()
                
                data.append({
                    'Timestamp': comp.comparison_timestamp,
                    'Song A': song_a.canonical_name if song_a else 'Unknown',
                    'Song B': song_b.canonical_name if song_b else 'Unknown',
                    'Outcome': comp.outcome_label,
                    'Score': comp.outcome_value,
                })
            
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"musicelo_comparisons_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            st.success("✅ CSV ready for download!")
        finally:
            session.close()

# Help section
with st.expander("ℹ️ Understanding the Statistics"):
    st.markdown("""
    ### Metrics Explained
    
    **Rating**
    - Base rating: 1500
    - Higher = better
    - Range: Typically 1200-1800
    
    **Rating Deviation (RD)**
    - Uncertainty in rating
    - Lower = more confident
    - < 100: High confidence
    - 100-200: Medium confidence
    - > 200: Low confidence (needs more games)
    
    **Volatility (σ)**
    - How much rating changes
    - High: Rating still settling
    - Low: Rating stable
    
    **Win Rate**
    - Percentage of comparisons won
    - 50% = average
    - > 50% = above average
    
    **Games Played**
    - Number of comparisons
    - 10+ recommended for accuracy
    - 20+ for high confidence
    
    ### Tips
    
    - Focus on songs with **high RD** (> 250) to improve accuracy
    - Use **Discover playlists** for efficient ranking
    - Aim for **10+ games** per song
    - Check **biggest movers** for surprises
    """)
