"""
Rankings - View Song Rankings

Display and filter song rankings with export functionality
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations

st.set_page_config(
    page_title="Rankings - MusicElo",
    page_icon="📊",
    layout="wide",
)

# Hide Streamlit header
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseOperations()

db = get_database()

# Page header
st.title("📊 Song Rankings")
st.markdown("**View and filter your personalized TWICE song rankings**")

# Sidebar - Filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Rating (High to Low)", "Rating (Low to High)", 
         "Most Compared", "Alphabetical", "Rating Confidence"],
        key="sort_by"
    )
    
    # Language filter - default all
    language_filter = st.multiselect(
        "Language",
        ["korean", "japanese", "english", "instrumental"],
        default=["korean", "japanese", "english", "instrumental"]
    )
    
    # Category filter - default all
    category_filter = st.multiselect(
        "Category",
        ["TWICE", "Solo", "Subunit", "Collaboration"],
        default=["TWICE", "Solo", "Subunit", "Collaboration"]
    )
    
    # Include variants - default off
    include_variants = st.checkbox("Include variants (remixes, etc.)", value=False)
    
    # Minimum comparisons
    min_games = st.slider("Minimum comparisons", 0, 50, 5)
    
    # Rating range - get actual min/max from database
    st.subheader("Rating Range")
    all_songs = db.get_all_songs()
    if all_songs:
        actual_min = int(min(s.rating for s in all_songs))
        actual_max = int(max(s.rating for s in all_songs))
        
        min_rating = st.number_input("Min Rating", 
                                     value=actual_min, 
                                     min_value=0, 
                                     max_value=3000, 
                                     step=50)
        max_rating = st.number_input("Max Rating", 
                                     value=actual_max, 
                                     min_value=0, 
                                     max_value=3000, 
                                     step=50)
    else:
        min_rating = 0
        max_rating = 3000
    
    st.markdown("---")
    
    # Export
    st.subheader("📤 Export")
    if st.button("Download as CSV", width="stretch"):
        st.session_state.download_trigger = True

# Determine sort parameters
sort_field = "rating"
ascending = False

if "Low to High" in sort_by:
    ascending = True
elif "Most Compared" in sort_by:
    sort_field = "games_played"
elif "Alphabetical" in sort_by:
    sort_field = "canonical_name"
    ascending = True
elif "Confidence" in sort_by:
    sort_field = "rating_deviation"
    ascending = True  # Lower RD = higher confidence

# Get rankings
songs = db.get_rankings(
    sort_by=sort_field,
    ascending=ascending,
    include_variants=include_variants,
    min_games=min_games
)

# Apply additional filters
if language_filter:
    songs = [s for s in songs if s.language in language_filter]

if category_filter:
    songs = [s for s in songs if s.category in category_filter]

if min_rating or max_rating < 3000:
    songs = [s for s in songs if min_rating <= s.rating <= max_rating]

# Display stats
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Songs Shown", len(songs))

with col2:
    if songs:
        avg_rating = sum(s.rating for s in songs) / len(songs)
        st.metric("Avg Rating", f"{avg_rating:.0f}")

with col3:
    if songs:
        avg_games = sum(s.games_played for s in songs) / len(songs)
        st.metric("Avg Comparisons", f"{avg_games:.1f}")

with col4:
    if songs:
        avg_rd = sum(s.rating_deviation for s in songs) / len(songs)
        st.metric("Avg Confidence", f"±{avg_rd:.0f}")

st.markdown("---")

# Display rankings
if not songs:
    st.warning("No songs match your filters. Try relaxing the criteria.")
else:
    # View mode
    view_mode = st.radio(
        "View mode",
        ["Table", "Cards"],
        horizontal=True
    )
    
    if view_mode == "Table":
        # Table view with separate link column
        df_data = []
        for rank, song in enumerate(songs, 1):
            df_data.append({
                'Rank': rank,
                'Song': song.canonical_name,
                'Artist': song.artist_name,
                'Rating': f"{song.rating:.0f}",
                'Confidence': f"±{song.rating_deviation:.0f}",
                'Language': song.language.capitalize(),
                'Category': song.category,
                'Games': song.games_played,
                'W-L-D': f"{song.wins}-{song.losses}-{song.draws}",
                'Win %': f"{(song.wins / song.games_played * 100):.1f}%" if song.games_played > 0 else "N/A",
                'YouTube': song.youtube_music_url if song.youtube_music_url else "",
            })
        
        df = pd.DataFrame(df_data)
        
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Song": st.column_config.TextColumn("Song", width="large"),
                "Artist": st.column_config.TextColumn("Artist", width="medium"),
                "Rating": st.column_config.TextColumn("Rating", width="small"),
                "Confidence": st.column_config.TextColumn("±RD", width="small"),
                "Language": st.column_config.TextColumn("Language", width="small"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Games": st.column_config.NumberColumn("Games", width="small"),
                "W-L-D": st.column_config.TextColumn("W-L-D", width="small"),
                "Win %": st.column_config.TextColumn("Win %", width="small"),
                "YouTube": st.column_config.LinkColumn("YouTube", width="small", display_text="▶️"),
            }
        )
        
        # Export functionality
        if st.session_state.get('download_trigger', False):
            # Remove YouTube column for CSV export
            df_export = df.drop(columns=['YouTube'])
            
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="💾 Save CSV",
                data=csv,
                file_name="musicelo_rankings.csv",
                mime="text/csv",
            )
            st.session_state.download_trigger = False
    
    else:
        # Card view - more compact
        st.markdown("### Top Rankings")
        
        # Show top 50 in card view
        display_songs = songs[:50]
        
        for rank, song in enumerate(display_songs, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 6, 2, 2])
                
                with col1:
                    # Rank with medal for top 3
                    if rank == 1:
                        st.markdown("# 🥇")
                    elif rank == 2:
                        st.markdown("# 🥈")
                    elif rank == 3:
                        st.markdown("# 🥉")
                    else:
                        st.markdown(f"## #{rank}")
                
                with col2:
                    # Song title with YouTube link
                    if song.youtube_music_url:
                        st.markdown(f"### [{song.canonical_name}]({song.youtube_music_url})")
                    else:
                        st.markdown(f"### {song.canonical_name}")
                    
                    # Artist on its own line
                    st.markdown(f"*{song.artist_name}*")
                    
                    # Metadata in caption row (aligned with ±RD and Win%)
                    metadata_parts = [f"🌍 {song.language.capitalize()}", f"📁 {song.category}"]
                    if song.variant_type:
                        metadata_parts.append(f"🔄 {song.variant_type}")
                    st.caption(" • ".join(metadata_parts))
                
                with col3:
                    # Rating column
                    st.metric("Rating", f"{song.rating:.0f}")
                    st.caption(f"📊 ±{song.rating_deviation:.0f}")
                
                with col4:
                    # Games column (aligned with rating)
                    st.metric("Games", song.games_played)
                    if song.games_played > 0:
                        win_rate = song.wins / song.games_played * 100
                        st.caption(f"🏆 Win: {win_rate:.0f}%")
                    else:
                        st.caption("🏆 No games")  # Consistent formatting
                
                st.markdown("---")
        
        if len(songs) > 50:
            st.info(f"Showing top 50 of {len(songs)} songs. Use table view to see all.")

# Statistics section
with st.expander("📈 Detailed Statistics"):
    if songs:
        st.subheader("Rating Distribution")
        
        # Create rating bins
        ratings = [s.rating for s in songs]
        rating_bins = pd.cut(ratings, bins=10)
        rating_counts = rating_bins.value_counts().sort_index()
        
        # Display as bar chart data
        chart_data = pd.DataFrame({
            'Rating Range': [str(interval) for interval in rating_counts.index],
            'Count': rating_counts.values
        })
        
        st.bar_chart(chart_data.set_index('Rating Range'))
        
        # Top performers
        st.subheader("🏆 Top 10 Songs")
        top_10 = songs[:10]
        for i, song in enumerate(top_10, 1):
            st.markdown(f"{i}. **{song.canonical_name}** - {song.rating:.0f} (±{song.rating_deviation:.0f})")
        
        # Most active
        st.subheader("🎯 Most Compared Songs")
        most_active = sorted(songs, key=lambda s: s.games_played, reverse=True)[:10]
        for i, song in enumerate(most_active, 1):
            st.markdown(f"{i}. **{song.canonical_name}** - {song.games_played} games")
        
        # Highest confidence (lowest RD)
        st.subheader("✅ Highest Confidence Ratings")
        highest_conf = sorted(songs, key=lambda s: s.rating_deviation)[:10]
        for i, song in enumerate(highest_conf, 1):
            st.markdown(f"{i}. **{song.canonical_name}** - ±{song.rating_deviation:.0f}")

# Help section
with st.expander("ℹ️ Understanding the Rankings"):
    st.markdown("""
    ### Rating Components
    
    **Rating (μ)**
    - Your song's current score
    - Higher = better in your preference
    - Default start: 1500 (or boosted if liked/familiar)
    
    **Rating Deviation (RD) / Confidence**
    - How certain we are about the rating
    - Lower = more confident
    - Decreases with more comparisons
    - ±350 = completely uncertain
    - ±50 = very confident
    
    **Games / Comparisons**
    - Number of times this song was compared
    - More games = more accurate rating
    - At least 10-15 games recommended for stability
    
    ### Interpreting Ratings
    
    - **1700+**: Your absolute favorites
    - **1600-1700**: Really love these
    - **1500-1600**: Like them, solid songs
    - **1400-1500**: Okay, but not favorites
    - **<1400**: Not your preference
    
    ### Tips
    
    - Compare songs until RD is below ±100
    - Songs with high RD need more comparisons
    - Click song titles to open in YouTube Music
    """)
