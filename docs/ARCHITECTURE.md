# 🏛️ MusicElo Architecture

Technical architecture and design decisions for MusicElo.

---

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                    (Streamlit App)                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   │
│  │ Review   │ Duel     │ Playlist │ Rankings │ Analytics│   │
│  │ Data     │ Mode     │ Mode     │          │          │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│                     (Core Services)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  glicko2_service   │  spotify_service                │   │
│  │  recommendation    │  playlist_service               │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│                  (Database Operations)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  models.py (SQLAlchemy)  │  operations.py           │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                            │
│                    (SQLite Database)                         │
│  ┌──────┬───────────┬──────────┬────────────────────┐      │
│  │Songs │Comparisons│ Playlists│ Parameters         │      │
│  └──────┴───────────┴──────────┴────────────────────┘      │
└─────────────────────────────────────────────────────────────┘

External APIs:
- Spotify Web API (metadata enrichment)
- YouTube Music (playback URLs)
```

---

## 🎯 Design Principles

### 1. Framework Agnosticism

**Problem**: Streamlit is great for MVPs, but we might want React/FastAPI later.

**Solution**: Core business logic has ZERO UI dependencies.

```python
# ✅ GOOD: core/services/glicko2_service.py
class Glicko2Calculator:
    def update_rating(self, rating, rd, volatility, opponents):
        # Pure Python logic
        # No imports from streamlit, flask, etc.
        return new_rating, new_rd, new_volatility

# ❌ BAD: core/services/glicko2_service.py
import streamlit as st  # UI dependency in core!

class Glicko2Calculator:
    def update_rating(self, rating, rd, volatility, opponents):
        st.write("Calculating...")  # Breaks framework agnosticism
```

**Benefits**:
- Swap Streamlit for React without rewriting logic
- Test business logic without UI
- Reuse code in CLI tools, APIs, etc.

### 2. Single Responsibility

Each module has ONE job:

```
core/
├── database/
│   ├── models.py           # ONLY: Database schema
│   └── operations.py       # ONLY: CRUD operations
├── services/
│   ├── glicko2_service.py  # ONLY: Rating calculations
│   ├── spotify_service.py  # ONLY: Spotify API calls
│   └── recommendation.py   # ONLY: Playlist generation
```

### 3. Dependency Injection

**Problem**: Hard to test code that creates its own dependencies.

**Solution**: Pass dependencies as arguments.

```python
# ✅ GOOD: Testable
class SongComparison:
    def __init__(self, glicko_calculator, database):
        self.glicko = glicko_calculator
        self.db = database
    
    def record_comparison(self, song_a, song_b, outcome):
        new_ratings = self.glicko.update_rating(...)
        self.db.save_comparison(...)

# Testing is easy:
mock_glicko = MockGlicko()
mock_db = MockDatabase()
comparison = SongComparison(mock_glicko, mock_db)

# ❌ BAD: Untestable
class SongComparison:
    def __init__(self):
        self.glicko = Glicko2Calculator()  # Hard-coded!
        self.db = connect_to_database()    # Hard-coded!
```

### 4. Configuration as Code

**All configuration in one place**: `config.py`

```python
# config.py loads from environment
class Config:
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/musicelo.db')
    
# Use everywhere:
from config import Config

spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=Config.SPOTIFY_CLIENT_ID,
        client_secret=Config.SPOTIFY_CLIENT_SECRET
    )
)
```

---

## 📊 Database Schema

### Entity Relationship Diagram

```
┌─────────────────────┐
│      songs          │
├─────────────────────┤
│ song_id (PK)        │
│ canonical_name      │
│ album               │
│ release_date        │
│ spotify_id          │
│ youtube_music_url   │
│                     │
│ -- Glicko-2 --      │
│ rating              │
│ rating_deviation    │
│ volatility          │
│                     │
│ -- Spotify Audio -- │
│ valence             │
│ energy              │
│ danceability        │
│ tempo               │
│ key, mode           │
│                     │
│ -- Stats --         │
│ games_played        │
│ wins, losses, draws │
│ last_compared       │
└──────────┬──────────┘
           │
           │ Many-to-Many
           │
           ▼
┌──────────────────────┐       ┌──────────────────┐
│    comparisons       │       │   playlists      │
├──────────────────────┤       ├──────────────────┤
│ comparison_id (PK)   │       │ playlist_id (PK) │
│ timestamp            │       │ name             │
│ song_a_id (FK)       │       │ generation_type  │
│ song_b_id (FK)       │       │ parameters       │
│ winner_id (FK)       │       │ created_at       │
│ outcome (0.0-1.0)    │       │ overall_rating   │
│ outcome_type         │       └─────────┬────────┘
│                      │                 │
│ -- Before/After --   │                 │ Many-to-Many
│ song_a_rating_before │                 │
│ song_a_rating_after  │                 ▼
│ song_a_rd_before     │       ┌──────────────────┐
│ song_a_rd_after      │       │ playlist_songs   │
│ song_a_vol_before    │       ├──────────────────┤
│ song_a_vol_after     │       │ playlist_id (FK) │
│                      │       │ song_id (FK)     │
│ song_b_...           │       │ position         │
│                      │       │ was_played       │
│ -- Metadata --       │       │ song_rating      │
│ comparison_mode      │       │ skip_time        │
│ was_sequential       │       └──────────────────┘
│ expected_outcome     │
│ rating_impact        │
└──────────────────────┘

┌──────────────────────┐
│     parameters       │
├──────────────────────┤
│ param_name (PK)      │
│ param_value          │
│ description          │
└──────────────────────┘
```

### Key Design Decisions

**1. Store Before/After States**
- Full audit trail of rating changes
- Can undo comparisons accurately
- Analyze rating evolution over time

**2. Outcome as Float (0.0 to 1.0)**
- Flexible: Supports wins, losses, draws, partial outcomes
- Glicko-2 compatible: Direct input to algorithm
- Future-proof: Can add "slight win" (0.75) later

**3. Denormalized Audio Features**
- Spotify data copied into songs table
- Faster queries (no joins needed)
- Trade-off: Duplication vs. speed
- Decision: Speed wins for personal-scale data

**4. JSON for Playlist Parameters**
- Flexible schema for different generation types
- Example: `{"mood": "happy", "min_valence": 0.7, "max_results": 20}`
- SQLite supports JSON queries: `json_extract(parameters, '$.mood')`

---

## 🔄 Data Flow

### Comparison Flow (Duel Mode)

```
User clicks "A is Better"
        │
        ▼
streamlit_app/pages/1_Duel_Mode.py
├─ Get current songs from session_state
├─ Call: record_comparison(song_a, song_b, outcome=1.0)
        │
        ▼
core/services/comparison_service.py
├─ Load song ratings from database
├─ Call: glicko2_service.update_rating()
        │
        ▼
core/services/glicko2_service.py
├─ Calculate new ratings (pure math)
├─ Return: (new_rating_a, new_rd_a, new_vol_a), (new_rating_b, ...)
        │
        ▼
core/database/operations.py
├─ Begin transaction
├─ Update song ratings
├─ Insert comparison record
├─ Commit transaction
        │
        ▼
streamlit_app/pages/1_Duel_Mode.py
├─ Show rating changes
├─ Load next pair
├─ st.rerun()
```

### Playlist Generation Flow

```
User: "Generate chill vibes playlist"
        │
        ▼
streamlit_app/pages/3_Playlists.py
├─ Parse input: mood="chill"
├─ Call: recommendation_service.generate_playlist()
        │
        ▼
core/services/recommendation_service.py
├─ Load all songs from database
├─ Filter by mood (valence, energy)
├─ Weight by Glicko rating
├─ Calculate mood distance
├─ Apply diversity sampling
├─ Return: list of song_ids
        │
        ▼
core/database/operations.py
├─ Create playlist record
├─ Insert playlist_songs entries
├─ Return: playlist_id
        │
        ▼
streamlit_app/pages/3_Playlists.py
├─ Display songs with YouTube players
├─ Enable quick ranking (vs previous song)
```

---

## 🧩 Module Responsibilities

### Core Layer (No UI Dependencies)

#### `core/database/models.py`
```python
# SQLAlchemy ORM models
# Defines: Song, Comparison, Playlist, PlaylistSong, Parameter
# NO business logic, ONLY schema definition
```

#### `core/database/operations.py`
```python
# CRUD operations
# Functions: get_song(), save_comparison(), get_rankings()
# Uses: SQLAlchemy sessions
# Returns: Plain dicts or model objects
```

#### `core/services/glicko2_service.py`
```python
# Pure Glicko-2 algorithm
# Input: ratings, RDs, volatilities, outcomes
# Output: updated ratings, RDs, volatilities
# ZERO database or UI dependencies
# 100% testable with unit tests
```

#### `core/services/spotify_service.py`
```python
# Spotify API wrapper
# Functions: search_artist(), get_audio_features()
# Handles: Authentication, rate limiting, errors
# Returns: Clean dicts with relevant data
```

#### `core/services/recommendation_service.py`
```python
# Playlist generation algorithms
# Functions: generate_by_mood(), generate_transition()
# Uses: Song ratings + audio features
# Returns: List of song_ids with scores
```

### UI Layer (Streamlit)

#### `streamlit_app/app.py`
```python
# Main entry point
# Configures: Page layout, theme, navigation
# Initializes: Database connection, session state
# Shows: Welcome page, navigation sidebar
```

#### `streamlit_app/pages/1_Duel_Mode.py`
```python
# Comparison interface
# Responsibilities:
# - Display two songs side-by-side
# - Handle user input (A/B/Draw buttons)
# - Show rating changes
# - Load next pair
# ONLY calls core services, NO business logic
```

#### `streamlit_app/pages/3_Rankings.py`
```python
# Rankings display
# Responsibilities:
# - Fetch rankings from database
# - Display table with sorting/filtering
# - Show confidence intervals
# - Export to CSV
```

### Scripts (One-time Setup)

#### `scripts/01_fetch_spotify_discography.py`
```python
# Standalone script
# Purpose: Initial data collection
# Output: data/spotify_discography_raw.csv
# Can be re-run to refresh metadata
```

#### `scripts/05_init_database.py`
```python
# Database initialization
# Purpose: Create tables, insert initial data
# Idempotent: Safe to re-run (drops existing tables)
# Uses: core/database/models.py
```

---

## 🔒 Security Architecture

### Secrets Management

```
┌─────────────────────────────────────────┐
│         Environment Variables            │
│              (.env file)                 │
│  ┌───────────────────────────────────┐  │
│  │ SPOTIFY_CLIENT_ID=abc123          │  │
│  │ SPOTIFY_CLIENT_SECRET=def456      │  │
│  │ DATABASE_URL=sqlite:///data/...   │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ Loaded by
               ▼
┌─────────────────────────────────────────┐
│           config.py                      │
│      (Single source of truth)            │
│  ┌───────────────────────────────────┐  │
│  │ class Config:                     │  │
│  │   SPOTIFY_CLIENT_ID = os.getenv() │  │
│  │   @classmethod validate()         │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ Used by
               ▼
┌─────────────────────────────────────────┐
│        All application code              │
│  from config import Config               │
│  spotify = Spotify(Config.CLIENT_ID)    │
└─────────────────────────────────────────┘

       .gitignore ensures:
       ✅ .env NOT committed
       ✅ config.py committed (loads from env)
       ✅ .env.example committed (template only)
```

---

## 📈 Scalability Considerations

### Current Scale
- **Users**: 1 (personal project)
- **Songs**: ~250 (TWICE discography)
- **Comparisons**: ~1,000 over time
- **Database**: SQLite (< 10 MB)

### Future Scale (if needed)

**10,000 songs**:
- ✅ SQLite still fine
- Add indexes on rating, album, category
- Keep current architecture

**Multiple users**:
- Add `user_id` to all tables
- Row-level security
- Consider PostgreSQL
- Add authentication layer

**100,000+ songs** (unlikely):
- PostgreSQL required
- Separate services (microservices)
- Caching layer (Redis)
- API instead of direct DB access

**Current decision**: YAGNI (You Ain't Gonna Need It)
- SQLite is perfect for personal use
- Architecture allows future migration
- Don't over-engineer for unlikely scenarios

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_glicko2.py
def test_rating_increases_on_win():
    calc = Glicko2Calculator()
    rating, rd, vol = calc.update_rating(
        1500, 350, 0.06,
        [(1500, 350, 1.0)]  # Win vs equal opponent
    )
    assert rating > 1500  # Rating should increase
```

### Integration Tests
```python
# tests/test_comparison_flow.py
def test_full_comparison_flow():
    # Setup test database
    # Create two songs
    # Record comparison
    # Verify ratings updated
    # Verify comparison saved
```

### Manual Testing
- Use Review Data page to check imports
- Try all UI flows before git push
- Test with sample data first

---

## 🚀 Performance Optimizations

### Database Queries

**Avoid N+1 queries**:
```python
# ❌ BAD: N+1 queries
for song in songs:
    album = db.query(Album).filter_by(id=song.album_id).first()

# ✅ GOOD: Join once
songs = db.query(Song).join(Album).all()
```

**Use indexes**:
```sql
CREATE INDEX idx_song_rating ON songs(rating DESC);
CREATE INDEX idx_comparison_timestamp ON comparisons(timestamp DESC);
```

### Streamlit Caching

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_all_songs():
    return db.query(Song).all()

@st.cache_resource
def get_spotify_client():
    return SpotifyClient(Config.CLIENT_ID, Config.CLIENT_SECRET)
```

---

## 🔄 Migration Path

**Current**: Streamlit + SQLite
**Future options**:

### Option A: Keep Streamlit, Upgrade Database
```
Streamlit UI
     ↓
Core Services (unchanged)
     ↓
PostgreSQL (instead of SQLite)
```
**When**: 10,000+ songs or multi-user

### Option B: React Frontend, FastAPI Backend
```
React UI ←→ FastAPI ←→ Core Services ←→ PostgreSQL
```
**When**: Want professional web app

### Option C: Mobile App
```
React Native ←→ FastAPI ←→ Core Services ←→ PostgreSQL
```
**When**: Want mobile experience

**All options reuse `core/` modules!**

---

## 📝 Code Style

### Python
- PEP 8 compliant
- Type hints for public functions
- Docstrings for classes and complex functions
- Max line length: 100 characters

### File Organization
- One class per file (services)
- Related functions grouped (operations)
- Tests mirror source structure

### Naming Conventions
```python
# Classes: PascalCase
class Glicko2Calculator:

# Functions: snake_case
def update_rating():

# Constants: UPPER_SNAKE_CASE
DEFAULT_RATING = 1500

# Private: _leading_underscore
def _internal_helper():
```

---

## 🎯 Future Enhancements

### Phase 2
- [ ] Smart pairing algorithms
- [ ] Undo stack (10 comparisons)
- [ ] Keyboard shortcuts
- [ ] Batch comparison mode

### Phase 3
- [ ] ML preference prediction
- [ ] Song clustering
- [ ] Advanced visualizations
- [ ] Mood-based auto-playlists

### Phase 4
- [ ] Multi-artist support
- [ ] Collaborative ranking
- [ ] Export to Spotify
- [ ] Mobile-responsive UI

---

**Architecture is designed for evolution while maintaining simplicity today.**

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment architecture.
