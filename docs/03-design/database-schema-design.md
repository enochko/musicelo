# MusicElo v3.0 — Database Schema Design

**Version:** 0.2
**Date:** February 2026
**Database:** PostgreSQL (Supabase free tier)
**Aligned with:** prd-v0.2

---

## 1. Design Principles

### 1.1 Why Cache Everything Locally?

Services disappear (AcousticBrainz stopped 2022), APIs get restricted (Spotify Feb 2026), rate limits make re-fetching painful (MusicBrainz 1 req/sec). The database stores:

- **MusicElo's canonical library** — the merged, deduplicated "source of truth" for the app
- **Raw API response cache** — the original JSON from each service, timestamped, so we never need to re-fetch and can re-merge if our deduplication methodology changes
- **Cross-platform links** — mapping between MusicElo's internal IDs and every platform's native IDs
- **Glicko-2 rating data** — ratings, match history, play events, snapshots
- **Audio features & tags** — from all sources, normalized into a common schema

### 1.2 Will This Blow the Supabase Free Tier (500 MB)?

**No.** For a realistic personal library:

| Library Size | Core App Data | + Raw API Cache | Verdict |
|-------------|--------------|----------------|---------|
| 300 tracks (MVP TWICE) | ~2 MB | ~8 MB | Trivial |
| 800 tracks (full TWICE ecosystem) | ~5 MB | ~25 MB | Trivial |
| 5,000 tracks (expanded K-pop) | ~30 MB | ~150 MB | Comfortable |
| 10,000 tracks (PRD NFR-010 target) | ~60 MB | ~300 MB | Within 500 MB |

The raw JSON cache is the largest component. Two strategies if space gets tight:
1. **Compress before storing** — typical 3:1 ratio on JSON. PostgreSQL TOAST already compresses large TEXT/JSONB values automatically.
2. **Age out stale cache** — keep latest fetch per platform per track; archive or drop older fetches.

Even at 10,000 tracks with full raw cache, we'd use ~300 MB of the 500 MB Supabase free tier. Years of comparison history and play events would add modest growth — roughly 100 bytes per comparison, 200 bytes per play event. At 20 comparisons/day for 3 years that's only ~2 MB of comparison data.

### 1.3 Primary Keys: ISRC Is Not Enough

Each service has its own canonical ID, and **ISRC alone cannot serve as a universal PK** because:

- Not all tracks have ISRCs (indie/unsigned releases, YouTube-only tracks)
- Multiple ISRCs can exist for the same logical song (remaster, radio edit, deluxe version)
- YouTube Music doesn't expose ISRC at all
- ISRC identifies a *recording*, not a *track-on-an-album* (same ISRC on a single and an album)

**Solution:** MusicElo uses **UUID primary keys** for all entities (PostgreSQL native `gen_random_uuid()`). ISRCs and platform IDs are stored as indexed attributes for cross-referencing but never as primary keys.

| Service | ID Type | Example | Uniqueness |
|---------|---------|---------|-----------|
| MusicElo | UUID v4 | `a1b2c3d4-...` | Generated internally |
| Spotify | 22-char alphanumeric | `11dFghVXANMlKmJXsNCbNl` | Unique within Spotify |
| Apple Music | Numeric string | `1440818831` | Unique within storefront |
| MusicBrainz | UUID | `026fa041-3917-...` | Globally unique |
| Deezer | Integer | `67238732` | Unique within Deezer |
| YouTube Music | 11-char video ID | `dQw4w9WgXcQ` | Unique within YouTube |
| Last.fm | No numeric ID | N/A (name+artist match) | Match by name |
| Musixmatch | Integer | `15445219` | Unique within Musixmatch |
| ISRC | 12-char code | `USAT21206919` | Unique per *recording* (not per track-on-album) |

---

## 2. Schema Overview

The schema has **two layers**: the **application layer** (what the PRD's data model describes — songs, ratings, comparisons, play events, playlists) and the **metadata infrastructure layer** (what supports cross-platform data collection, caching, and rebuild capability).

```
┌──────────────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER (PRD Data Model)                                      │
│                                                                          │
│  songs ─────────┬── glicko_ratings    (1:1 with canonical songs)         │
│    │ canonical_  ├── comparisons       (pairwise match history)          │
│    │ id self-FK  ├── play_events       (passive listening log)           │
│    │             ├── song_relationships (translation/remix/live/etc.)    │
│    │             └── ranking_snapshots  (monthly JSONB snapshots)        │
│    │                                                                     │
│    ├── albums                                                            │
│    ├── artists ── artist_groups (group membership)                       │
│    ├── song_artists (M:N with roles)                                     │
│    └── playlist_rules (auto-playlist definitions)                        │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  METADATA INFRASTRUCTURE LAYER (API cache & cross-platform linking)       │
│                                                                          │
│  platform_song_ids  ◀──▶ songs      (Spotify/Apple/Deezer/YT/MB IDs)    │
│  platform_artist_ids ◀──▶ artists                                        │
│  platform_album_ids  ◀──▶ albums                                         │
│                                                                          │
│  source_cache_tracks   (raw JSON per service per track)                  │
│  source_cache_albums   (raw JSON per service per album)                  │
│  source_cache_artists  (raw JSON per service per artist)                 │
│                                                                          │
│  audio_features        (unified BPM/key/energy/valence from all sources) │
│  song_tags             (genre/mood/style from Last.fm/MB/Apple/etc.)     │
│                                                                          │
│  merge_log             (audit trail for data lineage)                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Table Definitions

### 3.1 Application Layer — Core Library

#### `artists`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | `DEFAULT gen_random_uuid()` |
| `name` | TEXT NOT NULL | Canonical display name (e.g., "TWICE") |
| `name_normalized` | TEXT | Lowercase, stripped diacritics, for matching |
| `sort_name` | TEXT | For alphabetical ordering |
| `artist_type` | TEXT | 'person', 'group', 'orchestra', 'other' |
| `country` | TEXT | ISO 3166-1 alpha-2 (e.g., 'KR') |
| `disambiguation` | TEXT | Distinguisher for same-name artists |
| `image_url` | TEXT | Best available artist image |
| `created_at` | TIMESTAMPTZ | `DEFAULT now()` |
| `updated_at` | TIMESTAMPTZ | `DEFAULT now()` |

#### `artist_groups`
Maps group membership. Solves: MusicBrainz credits "Nayeon" on solo tracks, Spotify credits "TWICE".

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `member_artist_id` | UUID FK → artists | The individual (e.g., Nayeon) |
| `group_artist_id` | UUID FK → artists | The group (e.g., TWICE) |
| `active_from` | DATE | |
| `active_until` | DATE | NULL = still active |
| `role` | TEXT | 'member', 'former_member', 'guest' |

Unique: `(group_artist_id, member_artist_id)`

#### `albums`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `title` | TEXT NOT NULL | |
| `title_normalized` | TEXT | |
| `album_type` | TEXT | 'album', 'single', 'ep', 'compilation' |
| `release_date` | TEXT | YYYY-MM-DD (or YYYY-MM, YYYY) |
| `release_date_precision` | TEXT | 'day', 'month', 'year' |
| `total_tracks` | INTEGER | |
| `total_discs` | INTEGER | |
| `upc` | TEXT | UPC/EAN barcode |
| `label` | TEXT | Record label |
| `image_url` | TEXT | Cover art URL |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

#### `album_artists`
M:N album ↔ artist credits.

| Column | Type | Notes |
|--------|------|-------|
| `album_id` | UUID FK → albums | |
| `artist_id` | UUID FK → artists | |
| `credit_order` | INTEGER | 0 = primary |
| `credited_as` | TEXT | Name as credited if different from canonical |

PK: `(album_id, artist_id, credit_order)`

#### `songs`
The central entity. Merges the PRD's flat "Song" model with normalized album/artist relationships.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `canonical_id` | UUID FK → songs | Self-FK. NULL = this IS the canonical. Non-NULL = alias pointing to canonical (PRD BR-002) |
| `title` | TEXT NOT NULL | Official title as listed |
| `title_normalized` | TEXT | Lowercase, stripped diacritics |
| `album_id` | UUID FK → albums | |
| `track_number` | INTEGER | |
| `disc_number` | INTEGER DEFAULT 1 | |
| `duration_ms` | INTEGER | Duration in milliseconds |
| `isrc` | TEXT | Indexed but not unique (see §1.3) |
| `language` | TEXT | 'korean', 'japanese', 'english', 'other' |
| `track_type` | TEXT | 'title_track', 'b_side', 'ost', 'special' |
| `explicit` | BOOLEAN DEFAULT FALSE | |
| `is_medley` | BOOLEAN DEFAULT FALSE | PRD FR-105 |
| `release_date` | TEXT | Track-level date if different from album |
| `performer_tags` | TEXT[] | Actual performers e.g. `{'Nayeon','Momo'}` (PRD FR-106) |
| `visual_notes` | TEXT | TTT references, concert moments, YouTube links (PRD FR-106) |
| `custom_tags` | TEXT[] | Emotional/context tags (PRD FR-106) |
| `audio_features` | JSONB | Seed data from Spotify/Apple Music (PRD FR-106) |
| `preview_url` | TEXT | Best available preview URL |
| `image_url` | TEXT | Track art (falls back to album art) |
| `merge_confidence` | REAL | 0.0–1.0 |
| `merge_method` | TEXT | 'isrc', 'heuristic', 'manual', 'single_source' |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Design note — `canonical_id` (PRD BR-002):** When Song A is a canonical alias of Song B (same recording on different albums), A.canonical_id points to B.id. Song B has canonical_id = NULL (it IS the canonical). GlickoRating only exists for canonical songs. Comparisons always reference the canonical ID (PRD BR-004).

**Design note — `audio_features` JSONB vs normalized table:** The PRD stores audio features as a JSONB blob on Song. We additionally maintain a structured `audio_features` table in the metadata layer (§3.3) for queryable analysis. The JSONB column is the "quick access" copy; the normalized table is the "full detail" copy with source tracking.

**Design note — `performer_tags` TEXT[] vs `song_artists` M:N:** Both exist. `performer_tags` is the PRD's lightweight array for quick display ("Nayeon solo"). `song_artists` is the full M:N relationship table with roles and credit order, supporting queries like "all songs where Nayeon has a vocal credit".

#### `song_artists`
M:N track ↔ artist credits with roles.

| Column | Type | Notes |
|--------|------|-------|
| `song_id` | UUID FK → songs | |
| `artist_id` | UUID FK → artists | |
| `credit_order` | INTEGER DEFAULT 0 | |
| `credit_role` | TEXT | 'primary', 'featured', 'remix', 'producer', 'composer', 'writer', 'arranger', 'performer' |
| `credited_as` | TEXT | Name as credited on this track |

PK: `(song_id, artist_id, credit_role)`

#### `song_relationships`
Typed relationships between songs (PRD FR-105).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_a_id` | UUID FK → songs | |
| `song_b_id` | UUID FK → songs | |
| `relationship_type` | TEXT NOT NULL | 'translation', 'remix', 'live_recording', 'acoustic', 'solo_version', 'medley_component' |
| `created_at` | TIMESTAMPTZ | |

Unique: `(song_a_id, song_b_id, relationship_type)`

### 3.2 Application Layer — Glicko-2 Rating System

#### `glicko_ratings`
One row per canonical song. Aliases don't have ratings (PRD BR-002).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_id` | UUID FK → songs UNIQUE | Must be a canonical song (canonical_id IS NULL) |
| `rating` | DOUBLE PRECISION DEFAULT 1500.0 | Glicko-2 μ |
| `rating_deviation` | DOUBLE PRECISION DEFAULT 350.0 | Glicko-2 φ |
| `volatility` | DOUBLE PRECISION DEFAULT 0.06 | Glicko-2 σ |
| `comparison_count` | INTEGER DEFAULT 0 | |
| `last_compared_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

#### `comparisons`
Every pairwise vote. Full audit trail (PRD FR-205). Supports undo via soft delete (PRD BR-006).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_a_id` | UUID FK → songs | Always references canonical ID (PRD BR-004) |
| `song_b_id` | UUID FK → songs | Always references canonical ID |
| `outcome` | DOUBLE PRECISION NOT NULL | 0.0, 0.25, 0.5, 0.75, 1.0 — from Song A's perspective (PRD FR-201) |
| `song_a_rating_before` | DOUBLE PRECISION | |
| `song_a_rd_before` | DOUBLE PRECISION | |
| `song_a_volatility_before` | DOUBLE PRECISION | |
| `song_b_rating_before` | DOUBLE PRECISION | |
| `song_b_rd_before` | DOUBLE PRECISION | |
| `song_b_volatility_before` | DOUBLE PRECISION | |
| `song_a_rating_after` | DOUBLE PRECISION | |
| `song_a_rd_after` | DOUBLE PRECISION | |
| `song_a_volatility_after` | DOUBLE PRECISION | |
| `song_b_rating_after` | DOUBLE PRECISION | |
| `song_b_rd_after` | DOUBLE PRECISION | |
| `song_b_volatility_after` | DOUBLE PRECISION | |
| `source` | TEXT NOT NULL | 'mobile_passive', 'mobile_focused', 'desktop_passive', 'desktop_focused' |
| `context` | JSONB | `{"device":"iphone","carplay":true,"focus_mode":"Driving","location_zone":"Commute"}` |
| `response_time_ms` | INTEGER | Decision latency |
| `is_undone` | BOOLEAN DEFAULT FALSE | Soft delete for undo (PRD BR-006) |
| `created_at` | TIMESTAMPTZ NOT NULL | |

#### `play_events`
Passive listening log (PRD FR-400). Never triggers Glicko-2 changes (PRD BR-008).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_id` | UUID FK → songs | |
| `started_at` | TIMESTAMPTZ NOT NULL | |
| `duration_played_seconds` | INTEGER | |
| `play_percentage` | REAL | 0.0–1.0 |
| `completed` | BOOLEAN | Played to end |
| `skipped` | BOOLEAN | |
| `replayed` | BOOLEAN | Immediately replayed |
| `device_type` | TEXT | 'iphone', 'mac', 'carplay' |
| `carplay_active` | BOOLEAN | |
| `focus_mode` | TEXT | 'Driving', 'Do Not Disturb', etc. |
| `location_zone` | TEXT | 'Home', 'Office', 'Uni', 'Commute' |
| `workout_active` | BOOLEAN | Apple Watch signal |
| `playback_platform` | TEXT | 'spotify', 'youtube_music', 'apple_music' |

#### `ranking_snapshots`
Monthly snapshots (PRD FR-206, BR-009).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `snapshot_date` | DATE NOT NULL UNIQUE | End-of-month date |
| `snapshot_data` | JSONB NOT NULL | `[{"song_id":"...","rating":1650.2,"rd":85.3,"volatility":0.055,"rank":1}, ...]` |
| `created_at` | TIMESTAMPTZ | |

#### `playlist_rules`
Auto-playlist definitions (PRD PlaylistRule).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | TEXT NOT NULL | e.g., "Favourites", "Top Korean Title Tracks" |
| `rule_type` | TEXT | 'threshold_rank', 'threshold_rating', 'filter' |
| `rule_definition` | JSONB | `{"top_n":50}` or `{"language":"korean","track_type":"title_track","top_n":20}` |
| `platform_playlist_ids` | JSONB | `{"spotify":"...","ytm":"...","apple_music":"..."}` |
| `auto_sync` | BOOLEAN DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

#### `glicko_parameters`
Parameter history (PRD FR-200: "parameter history should be kept with datetime stamp").

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `initial_rating` | DOUBLE PRECISION DEFAULT 1500.0 | |
| `initial_rd` | DOUBLE PRECISION DEFAULT 350.0 | |
| `initial_volatility` | DOUBLE PRECISION DEFAULT 0.06 | |
| `system_constant_tau` | DOUBLE PRECISION DEFAULT 0.5 | |
| `outcome_strong` | DOUBLE PRECISION DEFAULT 1.0 | Configurable outcome mapping (PRD FR-201) |
| `outcome_slight` | DOUBLE PRECISION DEFAULT 0.75 | |
| `outcome_equal` | DOUBLE PRECISION DEFAULT 0.5 | |
| `active_from` | TIMESTAMPTZ NOT NULL | When these params took effect |
| `active_until` | TIMESTAMPTZ | NULL = current |
| `notes` | TEXT | Why parameters were changed |

### 3.3 Metadata Infrastructure Layer

#### `platform_song_ids`
Links canonical songs to every platform's native IDs.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_id` | UUID FK → songs | |
| `platform` | TEXT NOT NULL | 'spotify', 'apple_music', 'musicbrainz', 'deezer', 'youtube', 'musixmatch', 'lastfm', 'reccobeats', 'acousticbrainz' |
| `platform_id` | TEXT NOT NULL | Platform's native ID |
| `platform_uri` | TEXT | Full URI/URL |
| `match_method` | TEXT | 'isrc', 'heuristic', 'manual', 'api_relationship' |
| `match_confidence` | REAL | 0.0–1.0 |
| `last_verified` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

Unique: `(platform, platform_id)`

#### `platform_artist_ids`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `artist_id` | UUID FK → artists | |
| `platform` | TEXT NOT NULL | |
| `platform_id` | TEXT NOT NULL | |
| `platform_url` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

Unique: `(platform, platform_id)`

#### `platform_album_ids`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `album_id` | UUID FK → albums | |
| `platform` | TEXT NOT NULL | |
| `platform_id` | TEXT NOT NULL | |
| `platform_url` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

Unique: `(platform, platform_id)`

#### `audio_features`
Structured audio features. Supplements `songs.audio_features` JSONB with queryable columns and source tracking.

| Column | Type | Notes |
|--------|------|-------|
| `song_id` | UUID PK FK → songs | |
| `bpm` | REAL | |
| `bpm_source` | TEXT | 'deezer', 'reccobeats', 'acousticbrainz', 'essentia' |
| `key_pitch` | INTEGER | Pitch class 0–11 (0=C … 11=B) |
| `mode` | INTEGER | 0=minor, 1=major |
| `key_source` | TEXT | |
| `time_signature` | INTEGER | |
| `loudness_db` | REAL | |
| `energy` | REAL | 0.0–1.0 |
| `valence` | REAL | 0.0–1.0 |
| `danceability` | REAL | 0.0–1.0 |
| `acousticness` | REAL | 0.0–1.0 |
| `instrumentalness` | REAL | 0.0–1.0 |
| `speechiness` | REAL | 0.0–1.0 |
| `liveness` | REAL | 0.0–1.0 |
| `primary_source` | TEXT | |
| `updated_at` | TIMESTAMPTZ | |

#### `song_tags`
Multi-source tags with weights.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `song_id` | UUID FK → songs | |
| `tag_name` | TEXT NOT NULL | Normalized: 'k-pop', 'dance-pop', 'energetic' |
| `tag_category` | TEXT | 'genre', 'mood', 'style', 'era', 'theme', 'other' |
| `weight` | REAL | 0.0–1.0 normalized relevance |
| `source` | TEXT NOT NULL | 'lastfm', 'musicbrainz', 'apple_music', 'musixmatch', 'acousticbrainz', 'essentia', 'user' |
| `source_weight` | INTEGER | Raw weight from source (Last.fm 0–100) |

Unique: `(song_id, tag_name, source)`

#### `source_cache_tracks` / `source_cache_albums` / `source_cache_artists`
Verbatim API responses. Insurance against service disappearance. Each table has identical structure:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `platform` | TEXT NOT NULL | |
| `platform_id` | TEXT NOT NULL | |
| `response_json` | JSONB NOT NULL | Full API response (TOAST-compressed automatically) |
| `fetched_at` | TIMESTAMPTZ NOT NULL | |
| `api_endpoint` | TEXT | Which endpoint was called |
| `http_status` | INTEGER | |
| `is_stale` | BOOLEAN DEFAULT FALSE | |

Index: `(platform, platform_id)`, `fetched_at`

#### `merge_log`
Audit trail for how canonical records were created/merged.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `entity_type` | TEXT | 'song', 'artist', 'album' |
| `entity_id` | UUID | |
| `action` | TEXT | 'created', 'merged', 'split', 'updated', 'field_override' |
| `source_platform` | TEXT | |
| `source_platform_id` | TEXT | |
| `details` | JSONB | What changed |
| `created_at` | TIMESTAMPTZ | |

---

## 4. Key Design Decisions

### 4.1 PRD "Song" → Normalized songs + albums + artists

The PRD defines a flat Song entity with `artist_official` as a string. We normalize into separate `artists`, `albums`, and join tables because: (a) the same artist appears on hundreds of tracks, (b) the same album contains multiple tracks, (c) cross-platform artist matching requires a stable artist identity, and (d) the PRD's `performer_tags` array coexists with the full `song_artists` M:N table for different use cases (quick display vs. deep queries).

### 4.2 `canonical_id` Self-FK (PRD BR-002)

When "What is Love" appears on both *Twicetagram* and *#TWICE*, the copy on *#TWICE* has `canonical_id` pointing to the *Twicetagram* version. Only the canonical (canonical_id IS NULL) gets a `glicko_ratings` row. All comparisons resolve to the canonical ID before processing (PRD BR-004).

### 4.3 Dual Audio Features Storage

`songs.audio_features` (JSONB) provides the PRD's specified quick-access blob. The `audio_features` table (structured columns) enables queries like "all songs with BPM > 120 AND energy > 0.7" efficiently, with per-field source tracking.

### 4.4 Why Snapshot Before/After on Comparisons?

Storing full rating state before and after each comparison (including volatility, which was absent in the initial draft) means: (a) complete replay capability for undo (PRD BR-006), (b) rating trajectory visualization per song, (c) debugging anomalous rating changes, (d) no need to recalculate from scratch.

### 4.5 `is_undone` Soft Delete (PRD BR-006)

Undone comparisons are never physically deleted. `is_undone = TRUE` excludes them from active queries. Glicko-2 scores are recalculated by replaying all non-undone comparison history for affected songs.

### 4.6 No Multi-Context Rating (Deferred)

The PRD specifies a single global Glicko-2 pool. If context-aware ranking (e.g., "workout ranking" vs "chill ranking") is needed in v4.0+, adding a `context_id` FK to `glicko_ratings` and `comparisons` is straightforward.

### 4.7 No `users` Table (PRD §7: Single User)

The PRD explicitly scopes v3.0 as single-user. Adding a `user_id` FK to ratings/comparisons/play_events later is a simple migration.

---

## 5. Storage Estimates for Supabase

| Component | 300 tracks | 800 tracks | 10,000 tracks |
|-----------|-----------|-----------|-------------|
| Songs + albums + artists | 0.3 MB | 0.8 MB | 10 MB |
| Platform cross-references | 0.05 MB | 0.1 MB | 1.5 MB |
| Song tags (avg 10/song) | 0.1 MB | 0.3 MB | 4 MB |
| Audio features | 0.03 MB | 0.1 MB | 1 MB |
| Glicko-2 ratings | 0.01 MB | 0.03 MB | 0.4 MB |
| Comparison history (1 year) | 0.5 MB | 0.5 MB | 0.5 MB |
| Play events (1 year) | 1 MB | 1 MB | 1 MB |
| Ranking snapshots (12 months) | 0.1 MB | 0.3 MB | 4 MB |
| Raw source cache (all services) | 4 MB | 11 MB | 140 MB |
| **Total** | **~6 MB** | **~14 MB** | **~162 MB** |
| **Supabase free tier remaining** | **494 MB** | **486 MB** | **338 MB** |

---

## 6. Table Count Summary

| Layer | Tables | Purpose |
|-------|--------|---------|
| Core library | 7 | songs, albums, artists, album_artists, song_artists, artist_groups, song_relationships |
| Glicko-2 / app | 6 | glicko_ratings, comparisons, play_events, ranking_snapshots, playlist_rules, glicko_parameters |
| Platform cross-refs | 3 | platform_song_ids, platform_artist_ids, platform_album_ids |
| Raw cache | 3 | source_cache_tracks, source_cache_albums, source_cache_artists |
| Metadata | 2 | audio_features, song_tags |
| System | 1 | merge_log |
| **Total** | **22** | |
