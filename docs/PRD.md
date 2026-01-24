# MusicElo Product Requirements Document (PRD)

**Version:** 2.0 (YouTube Music Implementation)  
**Last Updated:** January 24, 2026  
**Status:** MVP Complete - Ready for Use  
**Owner:** Enoch Ko

---

## Executive Summary

**MusicElo** is a personalized music ranking system for TWICE's discography using the Glicko-2 rating algorithm. Users compare songs head-to-head to build individualized rankings based on their preferences, with ratings that evolve based on comparison outcomes.

### Key Changes from v1.0
- **Primary Data Source**: YouTube Music (Spotify API unavailable)
- **Data Collection**: 3 community playlists → 559 unique songs
- **Personalization**: Initial Elo boosts from user's liked/familiar songs
- **Database**: Enhanced schema supporting variants, albums, and future Spotify enrichment

---

## 1. Product Vision

### 1.1 Problem Statement

TWICE fans face several challenges when managing their music preferences:

1. **Overwhelming Discography**: 550+ songs across Korean, Japanese, English releases, solos, subunits, and collaborations
2. **Binary Ratings Insufficient**: Simple "like/dislike" doesn't capture nuanced preferences
3. **Context Blindness**: Playlist algorithms don't consider mood, transitions, or personal ranking stability
4. **No Personalization**: Streaming services rank by popularity, not individual taste

### 1.2 Solution

A **Glicko-2 powered ranking system** where users:
- Compare songs pairwise (A vs B)
- Build personalized rankings through cumulative comparisons
- Receive confidence-weighted ratings (more comparisons = more certainty)
- Get playlist recommendations based on ratings and mood

### 1.3 Success Metrics

**Engagement**
- Users complete 50+ comparisons in first session
- Return rate: 60%+ within 7 days
- Average session length: 15+ minutes

**Data Quality**
- 80%+ of songs reach RD < 100 (confident ratings)
- Rating stability: <5% change after 30 comparisons
- Consistent choices: <10% contradictory outcomes

**User Satisfaction**
- 90%+ agree rankings reflect their preferences
- 75%+ use generated playlists regularly

---

## 2. User Personas

### Primary: TWICE Enthusiast (Enoch)
- **Background**: Long-time ONCE, data science student, organized personality
- **Behavior**: Creates detailed playlists, tracks listening history, values data-driven insights
- **Goals**: Perfect ranking system, discover underrated tracks, optimize playlist flow
- **Pain Points**: Too many songs to manually rank, streaming service rankings don't match taste

### Secondary: Casual TWICE Fan
- **Background**: Enjoys TWICE but hasn't explored full discography
- **Behavior**: Sticks to title tracks and popular songs
- **Goals**: Discover B-sides, understand personal preferences
- **Pain Points**: Overwhelmed by catalog size, unsure where to start

---

## 3. Core Features

### 3.1 Duel Mode (Head-to-Head Comparison)

**Description**: Users compare two songs and indicate preference strength

**User Flow**:
1. System presents two songs (matched by similar ratings)
2. User listens to both (YouTube Music links provided)
3. User selects outcome:
   - 🏆 Strong preference (1.0 or 0.0)
   - ✓ Slight preference (0.75 or 0.25)
   - 🤝 Draw / Equal (0.5)
4. Ratings update immediately using Glicko-2
5. Next pair loads automatically

**Smart Pairing Logic**:
- Prioritize songs with high RD (uncertain ratings)
- Match songs within ±200 rating points (competitive matches)
- Avoid recent comparisons (cooldown period)
- Balance exploration (new songs) vs exploitation (refine top rankings)

**Filters**:
- Language: Korean, Japanese, English, Instrumental
- Category: TWICE, Solo, Subunit, Collaboration
- Include/exclude variants (remixes, live versions, etc.)
- Minimum comparison threshold

### 3.2 Rankings View

**Description**: Comprehensive view of all ranked songs with filtering and export

**Features**:
- **Table View**: Sortable data table with all songs
- **Card View**: Visual cards showing top 50 songs
- **Sorting Options**:
  - Rating (high to low / low to high)
  - Most compared (games played)
  - Alphabetical
  - Rating confidence (lowest RD first)
- **Filtering**: Same as Duel Mode
- **Export**: Download rankings as CSV

**Display Information**:
- Rank position (with medals for top 3)
- Song title and artist
- Rating with confidence interval (1500 ±350)
- Games played (W-L-D record)
- Language and category tags
- YouTube Music playback link

**Statistics**:
- Rating distribution histogram
- Top 10 songs by rating
- Most compared songs
- Highest confidence ratings

### 3.3 Data Collection Pipeline

**Source**: 3 YouTube Music Community Playlists
- TWICE Complete Discography #1: 367 tracks
- TWICE All Songs #2: 355 tracks  
- TWICE Comprehensive #3: 388 tracks
- **Total**: 1,110 raw tracks → 559 unique songs

**Process**:
1. **Fetch** (`01_fetch_ytm_playlists.py`): Download all tracks with metadata
2. **De-duplicate** (`02_deduplicate_and_classify.py`): 
   - Remove exact duplicates (same video_id)
   - Classify variants (Japanese versions, remixes, etc.)
   - Extract canonical names
   - Detect languages
3. **Extract Albums** (`03_extract_album_info.py`):
   - Parse album types (studio, EP, single, Japanese, repackage)
   - Detect album languages
   - Create album-song relationships
4. **Import User Preferences** (`04_import_user_playlists.py`):
   - Authenticate with YouTube Music
   - Read user's playlists and liked music
   - Match to database songs
   - Bootstrap Elo ratings
5. **Initialize Database** (`05_init_database.py`):
   - Load all data into SQLite
   - Apply Elo boosts
   - Link variants to originals
   - Create album track relationships

---

## 4. Technical Architecture

### 4.1 Technology Stack

**Backend**:
- Python 3.11
- SQLAlchemy 2.0 (ORM)
- SQLite (database)
- ytmusicapi (YouTube Music data collection)

**Frontend**:
- Streamlit 1.30+ (web framework)
- Pandas (data manipulation)
- Python-dotenv (environment management)

**Rating Algorithm**:
- Glicko-2 (Mark Glickman's algorithm)
- Custom implementation in `core/services/glicko2_service.py`

### 4.2 Database Schema

**Tables**:

**songs** (559 records)
- Primary Key: `song_id`
- Identity: `canonical_name`, `youtube_video_id`, `youtube_music_url`
- Variants: `is_original`, `original_song_id`, `variant_type`
- Metadata: `language`, `duration_ms`, `artist_name`, `category`
- Glicko-2: `rating`, `rating_deviation`, `volatility`
- Statistics: `games_played`, `wins`, `losses`, `draws`
- User flags: `is_liked`, `is_familiar`
- Future: `spotify_id`, `valence`, `energy`, `danceability` (NULL until Spotify available)

**albums** (92 records)
- Primary Key: `album_id`
- Fields: `album_name`, `album_type`, `release_date`, `language`

**album_tracks** (many-to-many, 441 links)
- Composite PK: `(album_id, song_id, track_number)`
- Enables: Same song on multiple albums, album sequential play

**comparisons** (audit trail)
- Records: Both songs' before/after ratings, outcome, expected probability
- Metadata: `comparison_mode`, `was_upset`, `rating_impact`

**ytm_playlists** (source tracking)
- Records which YouTube Music playlists were used

### 4.3 Glicko-2 Implementation

**Parameters**:
- τ (tau): 0.5 (volatility constraint)
- Default rating: 1500
- Default RD: 350 (completely uncertain)
- Default volatility: 0.06

**Initial Elo Boosts** (from user preferences):
- ❤️ Liked songs: 1600
- 👀 Familiar songs: 1550
- 📚 To-listen songs: 1525
- 🆕 Unknown songs: 1500

**Rating Updates**:
```python
# For each comparison
new_rating = calc.update_rating(
    current_rating, current_rd, current_volatility,
    opponents=[(opponent_rating, opponent_rd, outcome)]
)
```

**Outcome Values**:
- Decisive win: 1.0
- Slight win: 0.75
- Draw: 0.5
- Slight loss: 0.25
- Decisive loss: 0.0

**Confidence Intervals**:
- 95% CI = rating ± (2 × RD)
- Example: 1650 ± 100 → True skill likely between 1550-1750

### 4.4 Project Structure

```
musicelo/
├── core/
│   ├── database/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── operations.py       # CRUD operations
│   └── services/
│       └── glicko2_service.py  # Glicko-2 algorithm
│
├── scripts/
│   ├── 01_fetch_ytm_playlists.py      # Data collection
│   ├── 02_deduplicate_and_classify.py # De-duplication
│   ├── 03_extract_album_info.py       # Album extraction
│   ├── 04_import_user_playlists.py    # User preferences
│   └── 05_init_database.py            # Database initialization
│
├── streamlit_app/
│   ├── app.py                  # Home page
│   └── pages/
│       ├── 1_⚔️_Duel_Mode.py   # Comparison interface
│       └── 3_📊_Rankings.py    # Rankings view
│
├── data/                       # Local data (gitignored)
│   ├── musicelo.db            # SQLite database
│   ├── ytm_raw_tracks.csv     # Raw YouTube Music data
│   ├── ytm_deduplicated.csv   # De-duplicated songs
│   ├── ytm_enriched.csv       # Final song data
│   ├── albums.csv             # Album metadata
│   └── user_*.csv             # User preference CSVs
│
├── docs/
│   ├── SETUP.md               # Installation guide
│   ├── ARCHITECTURE.md        # System design
│   └── PRD.md                 # This document
│
├── .env                        # Environment variables (gitignored)
├── .gitignore                 # Git exclusions
├── config.py                  # Configuration loader
├── requirements.txt           # Python dependencies
└── README.md                  # Project overview
```

---

## 5. Data Model

### 5.1 Song Categorization

**Languages**:
- Korean: 436 songs (78%)
- Japanese: 91 songs (16%)
- English: 22 songs (4%)
- Instrumental: 10 songs (2%)

**Categories**:
- TWICE (group): ~450 songs
- Solo (Nayeon, Jihyo, etc.): ~50 songs
- Subunit (MISAMO): ~20 songs
- Collaboration: ~39 songs

**Album Types**:
- EP: 72 albums
- Studio: 7 albums
- Japanese: 12 albums
- Single: ~1 album
- Repackage: 1 album

### 5.2 Variant Handling

**Strategy**: One recording = one song, different recordings = separate songs

**Examples**:

**Same Song, Multiple Albums**:
```
Song: "Jelly Jelly" (song_id: 42)
Albums:
  - TWICEcoaster: Lane 1 (track 5)
  - TWICEcoaster: Lane 2 (track 5)
Result: ONE song, TWO album_tracks entries
```

**Different Versions (Variants)**:
```
Original: "Like OOH-AHH" Korean (song_id: 1, is_original: True)
Variant: "Like OOH-AHH" Japanese (song_id: 2, is_original: False, original_song_id: 1)
Result: TWO songs, linked via original_song_id
```

**Variant Types**:
- japanese_version: 29 songs
- remix: 29 songs
- instrumental: 10 songs
- english_version: 8 songs
- sped_up, slowed, acoustic, live, radio_edit

### 5.3 User Preference Matching

**From User's YouTube Music**:
- ❤️ Liked Music: 413 songs total
- 📂 TWICE Favourites: 66 songs
- 📚 TWICE To-Listen: 107 songs

**Matched to Database**:
- 54 liked songs → 1600 Elo
- 14 familiar songs → 1550 Elo
- 102 to-listen songs → 1525 Elo
- 391 unknown songs → 1500 Elo

**Matching Strategy**:
- Primary: Match by `youtube_video_id`
- Includes: All TWICE-related content (group, solos, subunits, collabs)
- Excludes: Non-TWICE songs in Liked Music

---

## 6. User Workflows

### 6.1 First-Time Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/username/musicelo.git
   cd musicelo
   ```

2. **Setup Environment**
   ```bash
   conda create -n musicelo python=3.11
   conda activate musicelo
   pip install -r requirements.txt
   ```

3. **Configure Settings**
   ```bash
   cp .env.example .env
   # Edit .env if needed (database path, etc.)
   ```

4. **Collect Data** (optional - database included)
   ```bash
   python scripts/01_fetch_ytm_playlists.py
   python scripts/02_deduplicate_and_classify.py
   python scripts/03_extract_album_info.py
   ```

5. **Bootstrap from Your Playlists** (optional)
   ```bash
   ytmusicapi oauth  # Authenticate
   python scripts/04_import_user_playlists.py
   ```

6. **Initialize Database**
   ```bash
   python scripts/05_init_database.py
   ```

7. **Launch App**
   ```bash
   streamlit run streamlit_app/app.py
   ```

### 6.2 Daily Usage

1. **Open App**: `streamlit run streamlit_app/app.py`
2. **Navigate to Duel Mode**
3. **Make Comparisons** (goal: 10-20 per session)
4. **Check Rankings** periodically to see evolution
5. **Export Rankings** when satisfied

### 6.3 Typical Session Flow

**Session 1** (Initial ranking - 30 min):
- 30-50 comparisons
- Focus on high-RD songs (uncertain ratings)
- Broad exploration across categories

**Sessions 2-5** (Refinement - 15 min each):
- 20-30 comparisons per session
- Target songs with RD > 150
- Start seeing stable top 20

**Sessions 6+** (Maintenance - 10 min):
- 10-15 comparisons
- Fine-tune close matchups
- Stable rankings achieved (RD < 100)

---

## 7. Future Enhancements

### 7.1 Phase 2: Playlist Generation

**Mood-Based Playlists**:
- Input: Mood (happy, sad, energetic, chill)
- Output: Playlist using Spotify audio features (valence, energy, etc.)
- When: After Spotify API becomes available

**Transition Optimization**:
- Minimize key/tempo jumps between songs
- Create smooth listening flow
- ML-based track sequencing

**Dynamic Playlists**:
- Top 20 songs (auto-updating)
- Random sample (weighted by rating)
- Discover mode (high-RD songs)

### 7.2 Phase 3: Advanced Features

**Album Sequential Play**:
- Play entire album in track order
- Rate album cohesion
- Album-level rankings

**Comparison Modes**:
- Tournament mode (bracket-style)
- Playlist mode (sequential comparisons)
- Battle royale (multi-song comparison)

**Social Features**:
- Share rankings with friends
- Compare rankings (correlation analysis)
- Collaborative playlists

**Analytics**:
- Rating evolution over time
- Upset tracking (unexpected outcomes)
- Bias detection (language preference, recency bias)

### 7.3 Phase 4: Cross-Artist Support

**Multi-Artist Rankings**:
- Expand beyond TWICE
- Cross-artist comparisons
- Genre-based rankings

**Import from Streaming Services**:
- Spotify listening history
- Apple Music library
- YouTube Music history

---

## 8. Success Criteria

### 8.1 MVP Success (Current)

✅ **Data Collection**:
- [ ] 500+ songs collected → ✅ **559 songs**
- [ ] Korean, Japanese, English coverage → ✅ **436/91/22**
- [ ] Variant detection and linking → ✅ **77 variants linked**

✅ **Core Functionality**:
- [ ] Glicko-2 implementation working → ✅ **Complete**
- [ ] Pairwise comparison UI → ✅ **Duel Mode**
- [ ] Rankings display → ✅ **Rankings Page**
- [ ] Rating updates in real-time → ✅ **Immediate updates**

✅ **Personalization**:
- [ ] User playlist import → ✅ **54 liked, 14 familiar, 102 to-listen**
- [ ] Initial Elo boosts → ✅ **1600/1550/1525/1500**

✅ **Data Quality**:
- [ ] Database schema supports all use cases → ✅ **Complete**
- [ ] Future-proof for Spotify enrichment → ✅ **Fields ready**

### 8.2 Post-MVP Goals

**Week 1**:
- 100+ comparisons completed
- Top 20 songs stable (RD < 100)
- Rankings feel accurate

**Month 1**:
- All songs have 5+ comparisons
- 80% of songs RD < 150
- Playlist generation ready (if Spotify available)

**Month 3**:
- Confident rankings (RD < 100 for top 100)
- Sharing feature used
- Analytics dashboard complete

---

## 9. Technical Decisions & Rationale

### 9.1 Why YouTube Music Instead of Spotify?

**Decision**: Use YouTube Music as primary data source

**Context**:
- Spotify API requires app creation
- App creation has been disabled 20+ days with no ETA
- Need to proceed with project

**Solution**:
- YouTube Music has comprehensive TWICE playlists
- ytmusicapi requires no app registration
- Database designed for future Spotify enrichment

**Trade-offs**:
- ✅ Can proceed immediately
- ✅ No API rate limits
- ✅ Complete discography available
- ❌ No audio features (valence, energy) yet
- ❌ Must wait for Spotify for playlist generation

### 9.2 Why Glicko-2 Over Elo?

**Elo Issues**:
- No uncertainty measure
- Treats all comparisons equally
- No volatility tracking

**Glicko-2 Advantages**:
- Rating Deviation (confidence measure)
- Volatility (performance consistency)
- Better handling of infrequent comparisons
- More accurate for sparse data

### 9.3 Why SQLite?

**Decision**: Use SQLite instead of PostgreSQL/MySQL

**Rationale**:
- Single-user application
- Local-first (no server setup)
- Simple deployment (just a file)
- Sufficient for 1000s of songs
- Easy backup (copy .db file)

**When to migrate**: If adding multi-user features

### 9.4 Why Streamlit?

**Decision**: Use Streamlit instead of React/Flask

**Rationale**:
- Rapid prototyping (MVP in days not weeks)
- Python-native (no context switching)
- Built-in components (charts, tables, forms)
- Easy deployment
- Focus on functionality over polish

**Trade-offs**:
- ✅ Fast development
- ✅ Python ecosystem integration
- ❌ Less UI customization
- ❌ Not suitable for mobile

---

## 10. Security & Privacy

### 10.1 Data Protection

**Local-First**:
- All data stored locally
- No cloud sync (user controls backups)
- Database file: `data/musicelo.db`

**Gitignore Protection**:
```
# Sensitive files
.env
data/
*.db
*_auth.json
oauth.json
```

### 10.2 Authentication

**YouTube Music**:
- Uses browser cookies or OAuth
- Stored in `data/ytm_headers_auth.json` or `oauth.json`
- **Never committed to Git** (in .gitignore)
- User must generate their own

**Future Spotify**:
- Will use OAuth 2.0
- Access token stored in .env
- Refresh token encrypted

### 10.3 User Data

**What's Stored**:
- Song comparisons and outcomes
- Glicko-2 ratings
- User flags (liked, familiar)

**What's NOT Stored**:
- Personal information
- Authentication credentials (gitignored)
- Listening history beyond what user imports

**Data Portability**:
- Export rankings as CSV
- Database is SQLite (standard format)
- Can be backed up/shared manually

---

## 11. Appendices

### 11.1 Glossary

**Glicko-2 Terms**:
- **Rating (μ)**: Current skill estimate (default: 1500)
- **Rating Deviation (RD / φ)**: Uncertainty in rating (default: 350)
- **Volatility (σ)**: Consistency of performance (default: 0.06)
- **Tau (τ)**: System constant constraining volatility changes (0.5)

**Domain Terms**:
- **Canonical Name**: Base song title without variant suffixes
- **Variant**: Different recording of same song (Japanese ver, remix, etc.)
- **Original**: Primary version of a song (Korean typically)
- **Duel**: Head-to-head comparison between two songs

### 11.2 References

**Glicko-2 Algorithm**:
- Mark Glickman (2012): "Example of the Glicko-2 System"
- http://www.glicko.net/glicko/glicko2.pdf

**Similar Projects**:
- Elo World: Photography ranking (inspiration)
- TrueSkill: Microsoft's ranking system
- Lichess: Chess rating implementation

**Data Sources**:
- YouTube Music community playlists
- User's personal playlists (optional)

### 11.3 Changelog

**v2.0 (January 24, 2026)**:
- Switched from Spotify to YouTube Music
- Enhanced database schema (variants, albums)
- User preference bootstrapping
- Complete data pipeline (5 scripts)
- Streamlit UI (3 pages)
- MVP complete and functional

**v1.0 (January 24, 2026)**:
- Initial design (Spotify-first)
- Glicko-2 implementation
- Project structure and documentation
- NOT IMPLEMENTED (Spotify API unavailable)

---

## 12. Contact & Support

**Project Owner**: Enoch Ko  
**Repository**: https://github.com/username/musicelo  
**Issues**: GitHub Issues  
**License**: MIT

---

**End of PRD v2.0**
