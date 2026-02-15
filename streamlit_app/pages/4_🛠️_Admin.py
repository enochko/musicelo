"""
Admin Tools - Data Quality Management

Features:
- Find and merge duplicates
- Update classifications
- Data quality dashboard
- Admin action log
"""

import streamlit as st
from pathlib import Path
import sys
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.operations import DatabaseOperations
from core.utils.security import escape_html, safe_youtube_embed
from core.database.admin_operations import AdminOperations
from core.database.models import Song

st.set_page_config(
    page_title="Admin Tools - MusicElo",
    page_icon="🛠️",
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

# Initialize
@st.cache_resource
def get_operations():
    db = DatabaseOperations()
    admin = AdminOperations(db)
    return db, admin

db, admin = get_operations()

# Page header
st.title("🛠️ Admin Tools")
st.markdown("**Data quality management and song organization**")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🔍 Find & Merge Duplicates", 
    "✏️ Edit Classifications",
    "📜 Action Log"
])

# ==================== TAB 1: DASHBOARD ====================

with tab1:
    st.header("Data Quality Dashboard")
    
    # Get report
    with st.spinner("Analyzing data quality..."):
        report = admin.get_data_quality_report()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "High Uncertainty",
            report['high_uncertainty'],
            help="Songs with RD > 250 and < 5 games"
        )
    
    with col2:
        st.metric(
            "Potential Duplicates",
            report['potential_duplicates'],
            help="Songs with similar titles/artists"
        )
    
    with col3:
        st.metric(
            "Orphan Variants",
            report['orphan_variants'],
            help="Variants without linked originals"
        )
    
    with col4:
        st.metric(
            "No Album Link",
            report['no_album'],
            help="Songs not linked to any album"
        )
    
    # Show duplicate pairs
    if report['duplicate_pairs']:
        st.markdown("---")
        st.subheader("🔍 Potential Duplicates (Top 20)")
        
        for song_a, song_b, similarity in report['duplicate_pairs']:
            with st.expander(f"**{song_a.canonical_name}** vs **{song_b.canonical_name}** ({similarity*100:.0f}% match)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Song A:**")
                    st.write(f"- ID: {song_a.song_id}")
                    st.write(f"- Title: {song_a.canonical_name}")
                    st.write(f"- Artist: {song_a.artist_name}")
                    st.write(f"- Rating: {song_a.rating:.0f} (±{song_a.rating_deviation:.0f})")
                    st.write(f"- Games: {song_a.games_played}")
                    st.write(f"- Video ID: {song_a.youtube_video_id}")
                
                with col2:
                    st.markdown("**Song B:**")
                    st.write(f"- ID: {song_b.song_id}")
                    st.write(f"- Title: {song_b.canonical_name}")
                    st.write(f"- Artist: {song_b.artist_name}")
                    st.write(f"- Rating: {song_b.rating:.0f} (±{song_b.rating_deviation:.0f})")
                    st.write(f"- Games: {song_b.games_played}")
                    st.write(f"- Video ID: {song_b.youtube_video_id}")
                
                # Quick merge button
                merge_key = f"merge_{song_a.song_id}_{song_b.song_id}"
                if st.button(f"Merge these songs →", key=merge_key):
                    st.session_state[f'merge_pair_{merge_key}'] = (song_a.song_id, song_b.song_id)
                    st.switch_page("pages/4_🛠️_Admin.py")  # Reload to merge tab

# ==================== TAB 2: FIND & MERGE ====================

with tab2:
    st.header("Find & Merge Duplicates")
    
    # Search interface
    st.subheader("🔍 Search Songs")
    
    search_query = st.text_input(
        "Search by title",
        placeholder="e.g., Strategy, 1 to 10, BDZ"
    )
    
    if search_query:
        results = admin.get_songs_by_title_pattern(search_query)
        
        if results:
            st.success(f"Found {len(results)} songs matching '{search_query}'")
            
            # Show results
            for song in results:
                with st.expander(f"**{escape_html(song.canonical_name)}** - Rating: {song.rating:.0f}, Games: {song.games_played}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**ID:** {song.song_id}")
                        st.write(f"**Artist:** {escape_html(song.artist_name)}")
                        st.write(f"**Language:** {song.language}")
                        st.write(f"**Category:** {song.category}")
                        st.write(f"**Variant:** {song.variant_type or 'Original'}")
                        st.write(f"**Rating:** {song.rating:.0f} ±{song.rating_deviation:.0f}")
                        st.write(f"**Stats:** {song.games_played} games ({song.wins}W-{song.losses}L-{song.draws}D)")
                        
                        if song.youtube_music_url:
                            st.markdown(f"[▶️ Play on YouTube Music]({song.youtube_music_url})")
                    
                    with col2:
                        # Selection checkbox
                        selected = st.checkbox(
                            "Select for merge",
                            key=f"select_{song.song_id}"
                        )
                        
                        if selected:
                            if 'merge_selection' not in st.session_state:
                                st.session_state.merge_selection = []
                            if song.song_id not in st.session_state.merge_selection:
                                st.session_state.merge_selection.append(song.song_id)
            
            # Merge interface
            if 'merge_selection' in st.session_state and len(st.session_state.merge_selection) >= 2:
                st.markdown("---")
                st.subheader("🔄 Merge Selected Songs")
                
                selected_ids = st.session_state.merge_selection
                st.info(f"Selected {len(selected_ids)} songs for merging")
                
                # Choose which to keep
                keep_song_id = st.selectbox(
                    "Keep which song?",
                    options=selected_ids,
                    format_func=lambda sid: next((s.canonical_name for s in results if s.song_id == sid), f"Song {sid}")
                )
                
                merge_song_id = st.selectbox(
                    "Merge which song into it?",
                    options=[sid for sid in selected_ids if sid != keep_song_id],
                    format_func=lambda sid: next((s.canonical_name for s in results if s.song_id == sid), f"Song {sid}")
                )
                
                # Preview merge
                if st.button("📊 Preview Merge"):
                    preview = admin.preview_merge(keep_song_id, merge_song_id)
                    
                    if preview:
                        st.success("Merge Preview:")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**Keep Song (Before)**")
                            st.write(f"Name: {preview['song1']['name']}")
                            st.write(f"Rating: {preview['song1']['rating']:.0f}")
                            st.write(f"RD: ±{preview['song1']['rd']:.0f}")
                            st.write(f"Games: {preview['song1']['games']}")
                        
                        with col2:
                            st.markdown("**Merge Song**")
                            st.write(f"Name: {preview['song2']['name']}")
                            st.write(f"Rating: {preview['song2']['rating']:.0f}")
                            st.write(f"RD: ±{preview['song2']['rd']:.0f}")
                            st.write(f"Games: {preview['song2']['games']}")
                        
                        with col3:
                            st.markdown("**Result (After)**")
                            st.write(f"Rating: {preview['merged']['rating']:.0f}")
                            st.write(f"RD: ±{preview['merged']['rd']:.0f}")
                            st.write(f"Games: {preview['merged']['games']}")
                            st.write(f"W-L-D: {preview['merged']['wins']}-{preview['merged']['losses']}-{preview['merged']['draws']}")
                        
                        st.warning(f"⚠️ This will affect {preview['comparisons_affected']} comparisons")
                        
                        # Store preview in session
                        st.session_state.merge_preview = preview
                
                # Execute merge
                if 'merge_preview' in st.session_state:
                    merge_reason = st.text_input(
                        "Reason for merge",
                        value="duplicate",
                        help="Why are you merging these songs?"
                    )
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if st.button("✅ Execute Merge", type="primary"):
                            with st.spinner("Merging songs..."):
                                success = admin.merge_songs(keep_song_id, merge_song_id, merge_reason)
                            
                            if success:
                                st.success("✅ Songs merged successfully!")
                                st.balloons()
                                
                                # Clear selection
                                del st.session_state.merge_selection
                                del st.session_state.merge_preview
                                st.rerun()
                            else:
                                st.error("❌ Merge failed. Check logs.")
                    
                    with col2:
                        if st.button("❌ Cancel"):
                            del st.session_state.merge_selection
                            del st.session_state.merge_preview
                            st.rerun()
        
        else:
            st.warning(f"No songs found matching '{search_query}'")

# ==================== TAB 3: EDIT CLASSIFICATIONS ====================

with tab3:
    st.header("Edit Song Classifications")
    
    # Search for song to edit
    edit_search = st.text_input(
        "Search song to edit",
        placeholder="Enter song title",
        key="edit_search"
    )
    
    if edit_search:
        edit_results = admin.get_songs_by_title_pattern(edit_search)
        
        if edit_results:
            selected_song_id = st.selectbox(
                "Select song to edit",
                options=[s.song_id for s in edit_results],
                format_func=lambda sid: next(s.canonical_name for s in edit_results if s.song_id == sid)
            )
            
            selected_song = next(s for s in edit_results if s.song_id == selected_song_id)
            
            st.markdown("---")
            st.subheader(f"Editing: **{selected_song.canonical_name}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Values:**")
                st.write(f"- Original: {selected_song.is_original}")
                st.write(f"- Variant Type: {selected_song.variant_type or 'None'}")
                st.write(f"- Language: {selected_song.language}")
                st.write(f"- Linked to: {selected_song.original_song_id or 'None'}")
            
            with col2:
                st.markdown("**Update:**")
                
                new_is_original = st.checkbox(
                    "Is Original",
                    value=selected_song.is_original
                )
                
                new_variant_type = st.selectbox(
                    "Variant Type",
                    options=[None, 'remix', 'remix_house', 'remix_moombahton', 
                            'japanese_version', 'english_version', 'korean_version',
                            'instrumental', 'acoustic', 'sped_up', 'slowed',
                            'music_video', 'alias'],
                    index=0 if not selected_song.variant_type else None
                )
                
                new_language = st.selectbox(
                    "Language",
                    options=['korean', 'japanese', 'english', 'instrumental'],
                    index=['korean', 'japanese', 'english', 'instrumental'].index(selected_song.language)
                )
                
                # Link to original
                link_search = st.text_input(
                    "Link to original (search)",
                    placeholder="Search for original song",
                    key="link_search"
                )
                
                new_original_id = None
                if link_search:
                    link_results = admin.get_songs_by_title_pattern(link_search)
                    if link_results:
                        new_original_id = st.selectbox(
                            "Select original",
                            options=[s.song_id for s in link_results],
                            format_func=lambda sid: next(s.canonical_name for s in link_results if s.song_id == sid)
                        )
                
                # Update buttons
                col_update, col_lang = st.columns(2)
                
                with col_update:
                    if st.button("💾 Update Classification", type="primary"):
                        success = admin.update_variant_classification(
                            selected_song_id,
                            new_is_original,
                            new_variant_type,
                            new_original_id
                        )
                        
                        if success:
                            st.success("✅ Classification updated!")
                            st.rerun()
                        else:
                            st.error("❌ Update failed")
                
                with col_lang:
                    if st.button("🌍 Update Language"):
                        success = admin.update_song_language(selected_song_id, new_language)
                        
                        if success:
                            st.success("✅ Language updated!")
                            st.rerun()
                        else:
                            st.error("❌ Update failed")

# ==================== TAB 4: ACTION LOG ====================

with tab4:
    st.header("Admin Action Log")
    
    # Get recent actions
    actions = admin.get_recent_actions(limit=50)
    
    if actions:
        st.info(f"Showing last {len(actions)} actions")
        
        for action in actions:
            with st.expander(f"**{action.action_type}** - {action.action_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"):
                st.markdown(f"**Description:** {action.description}")
                st.write(f"**Affected Songs:** {action.affected_song_ids}")
                
                # Show action data if available
                if action.action_data:
                    try:
                        data = json.loads(action.action_data) if isinstance(action.action_data, str) else action.action_data
                        st.json(data)
                    except:
                        st.text(action.action_data)
    else:
        st.info("No admin actions recorded yet")

# Help section
with st.expander("ℹ️ How to use Admin Tools"):
    st.markdown("""
    ### Dashboard
    - View overall data quality metrics
    - See potential duplicates automatically detected
    - Quick links to merge common duplicates
    
    ### Find & Merge Duplicates
    1. **Search** for songs by title (e.g., "Strategy", "1 to 10")
    2. **Select** 2+ songs to merge using checkboxes
    3. **Choose** which song to keep
    4. **Preview** the merge to see combined stats
    5. **Execute** the merge (affects ratings and comparisons)
    
    **What merging does:**
    - Combines comparison history
    - Calculates weighted average rating
    - Updates all comparisons to reference kept song
    - Marks merged song as alias (preserves data)
    
    ### Edit Classifications
    - Change variant type (remix, language version, etc.)
    - Link variants to originals
    - Update language classification
    - Fix misclassified songs
    
    ### Action Log
    - View all admin actions
    - Audit trail for changes
    - See before/after states
    
    ### Tips
    - Always **preview** before merging
    - Use **descriptive reasons** when merging
    - Check the **action log** if something looks wrong
    - Album links are preserved (both songs can appear on albums)
    """)
