# Product Requirements Document: MusicElo v3.0

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Date:** February 2026  
**Author:** Enoch Ko  
**Stage:** Requirements Definition  
**Version:** 0.2

---

## 1. Executive Summary

### Product Vision

MusicElo v3.0 is a personal music ranking system that uses the Glicko-2 algorithm to build transparent, preference-based song rankings through natural listening. Unlike opaque streaming platform algorithms, MusicElo provides explainable rankings based on accumulated pairwise comparisons made during everyday music consumption — while driving, walking, doing chores, or at a desktop.

### Goals and Objectives

1. Enable transparent ranking of 300+ TWICE ecosystem songs (expandable to 10,000+) through natural listening behaviour
2. Integrate ranking into everyday music consumption with a 90% passive data collection / 10% active comparison input balance
3. Generate playlists filtered by ranking, language, category, and context — seeded with platform metadata from day one
4. Capture rich play history and context data for future ML-powered playlist generation
5. Demonstrate end-to-end product development for portfolio (PM, engineering, data science, AI-assisted development)

### Target User

Single primary user — IT/accounting professional and data science graduate student, K-pop enthusiast with a 300+ song TWICE library, listening primarily while driving (CarPlay), walking, and at desktop.

### Key Architectural Decision

MusicElo operates as a **companion app** that monitors playback in native streaming apps (Spotify, YouTube Music, Apple Music) and captures ranking comparisons. It does not play music itself. Music plays in the native app; MusicElo reads what's playing and presents a comparison interface.

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Ranking agreement | Top 50 songs >80% intuitively correct after 3 months | Self-assessment |
| Input balance | ≥80% of Glicko-2 inputs from passive listening sessions (not dedicated comparison) | Comparison source tracking |
| Forgotten favourites | ≥5 songs rediscovered through ranking | Self-reported |
| System adoption | Voluntarily used for ≥50% of listening sessions | Usage tracking |
| Ranking convergence | RD <150 for top 50 songs within 3 months | Glicko-2 RD tracking |

---

## 2. Solution Architecture

### Hybrid Remote Control (Approach D)

```
┌──────────────────────────────────────────────────────────┐
│  Native Streaming Apps (handle all audio playback)       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Spotify  │  │ YouTube Music│  │ Apple Music  │       │
│  │  (API)   │  │  (NowPlaying)│  │  (MusicKit)  │       │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘       │
│       │               │                 │               │
└───────┼───────────────┼─────────────────┼───────────────┘
        │               │                 │
        ▼               ▼                 ▼
┌──────────────────────────────────────────────────────────┐
│  MusicElo Backend (Python/FastAPI + PostgreSQL)          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Glicko-2 │ │ Song     │ │ Playlist │ │ Context/   │  │
│  │ Engine   │ │ Library  │ │ Generator│ │ History    │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Metadata Enrichment Pipeline                     │    │
│  │ Deezer · MusicBrainz · Last.fm · ReccoBeats ·   │    │
│  │ AcousticBrainz · Musixmatch                      │    │
│  └──────────────────────────────────────────────────┘    │
│                        │                                 │
│              ┌─────────┴─────────┐                       │
│              │    REST API       │                       │
│              └─────────┬─────────┘                       │
└────────────────────────┼─────────────────────────────────┘
                ┌────────┴────────┐
                ▼                 ▼
┌──────────────────────┐ ┌────────────────────────────────┐
│  iOS Companion App   │ │  Desktop Web App               │
│  (Swift)             │ │  (Browser-based)               │
│  • Comparison widget │ │  • Rankings & history tables   │
│  • MPNowPlaying      │ │  • Multi-song comparison       │
│  • CarPlay detection │ │  • Playlist management         │
│  • Location zones    │ │  • Library & relationship mgmt │
│  • Offline vote queue│ │  • Settings & configuration    │
│  • Focus/DND status  │ │  • Spotify Connect monitoring  │
└──────────────────────┘ │  • Apple Music monitoring      │
                         └────────────────────────────────┘
```

### Component Responsibilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python (FastAPI) | Glicko-2 engine, REST API, data storage, playlist generation logic, metadata enrichment pipeline |
| **Database** | PostgreSQL (Supabase) | Song library, comparisons, rankings, play history, context data, cross-platform ID mapping, raw API cache |
| **iOS App** | Swift (native) | Comparison widget, now-playing detection, context capture, offline queue |
| **Desktop Web** | Web app (framework TBD) | Rankings dashboard, multi-song comparison, library management, settings |
| **Primary metadata** | Deezer API, MusicBrainz API, Apple Music (MusicKit) | ISRC resolution, canonical identifiers, structured metadata |
| **Audio features** | ReccoBeats, Deezer, AcousticBrainz (legacy) | BPM, key, valence, danceability, energy |
| **Genre/mood tags** | Last.fm, MusicBrainz, Apple Music, Musixmatch | Community tags, editorial genres, mood classification |
| **Playback monitoring** | Spotify Connect API, MusicKit, MPNowPlayingInfoCenter | Now-playing detection across platforms |

### Metadata Enrichment Strategy

Based on the Song Metadata API Research (see companion document), metadata is sourced in priority tiers:

**Tier 1 — Primary import sources (song library):**
- **Apple Music** (MusicKit) — Must Have. ISRC, structured metadata, genre, user library/playlists. Elevated from Could Have due to Spotify API restrictions.
- **Spotify** — Must Have. Playlist read/write, playback monitoring (Connect API), track metadata. ISRC available but only in Extended Quota mode.
- **YouTube Music** — Must Have. User's primary playback platform. Playlists/library via unofficial `ytmusicapi`. No ISRC.

**Tier 2 — Canonical identification and enrichment:**
- **Deezer** — Must Have. Free ISRC + BPM without authentication. Primary ISRC source to bypass Spotify restrictions.
- **MusicBrainz** — Must Have. Canonical recording/work IDs, artist credit resolution, group membership relationships, URL cross-references.

**Tier 3 — Audio features (post-Spotify restrictions):**
- **ReccoBeats** — Should Have. Free drop-in replacement for Spotify Audio Features. Uses Spotify track IDs.
- **AcousticBrainz** (legacy) — Could Have. Pre-computed features for ~7M recordings. CC0 licence. No new data since 2022.
- **Essentia/librosa** (local) — Deferred. Requires audio files; future consideration for tracks without API coverage.

**Tier 4 — Genre, mood, and community tags:**
- **Last.fm** — Should Have. Best source for community genre/mood tags with weighted counts.
- **Musixmatch** — Could Have. Structured genres, lyrics metadata. Free tier: 2,000 calls/day.

### Hosting and Infrastructure

| Service | Provider | Tier | Cost |
|---------|----------|------|------|
| Database | Supabase | Free (500MB) | $0/month |
| Backend API | Railway or Render | Free/Hobby | $0–5/month |
| iOS App | Apple Developer Program | Required | ~$149 AUD/year |
| Spotify | Premium (Student) | Required for Player API | ~$7.99 AUD/month |
| Apple Music | Individual (Student) | For MusicKit metadata + playback monitoring | ~$6.99 AUD/month |

**Why Supabase for database:** Built on PostgreSQL; generous free tier (500MB, sufficient for years of personal use — see Database Schema Design document §5 for detailed storage estimates); auto-backups included; REST API built in; dashboard for manual data inspection. The database schema (22 tables across 6 domains) fits comfortably within the free tier even at 10,000 tracks (~162 MB estimated).

---

## 3. Functional Requirements

### Epic 1: Song Library Management

**FR-100: Import songs from Spotify** — Must Have  
Import song metadata from Spotify playlists, user library, and Liked Songs.

- Given a Spotify playlist URL, user library, or Liked Songs, when import is triggered, then all songs are added to the MusicElo library with available metadata populated
- Given a song already exists (matched by ISRC or heuristic title/artist/duration match), when importing, then metadata is merged but existing Glicko-2 scores are preserved
- Given Spotify Dev Mode restrictions (Feb 2026), then ISRC is obtained via Deezer lookup rather than Spotify directly; audio features are obtained via ReccoBeats using Spotify track IDs

**FR-101: Import songs from YouTube Music** — Must Have  
Import song metadata and playlist structure from YouTube Music via unofficial `ytmusicapi`.

- Given a YouTube Music playlist (including user's "Liked" playlist), when import is triggered, then songs are matched to existing library entries (by heuristic title/artist match, supplemented by album from unofficial API) or created as new entries
- Given a song exists in both Spotify and YouTube Music, when imported from both, then they are linked as the same canonical song via ISRC or heuristic matching
- Given YouTube Music does not expose ISRC, then cross-platform matching relies on title + artist + duration matching with Deezer/MusicBrainz ISRC lookup as verification

**FR-102: Import songs from Apple Music** — Must Have  
Import song metadata from Apple Music catalogue and user library via MusicKit API.

- Given an Apple Music user library, playlists, or favourites list, when import is triggered, then songs are added with full metadata including ISRC (from catalogue songs)
- Given Apple Music provides ISRC on catalogue songs (not library-songs), then the `catalog` relationship is followed to obtain ISRC for library items
- Given Apple Music provides `genreNames[]`, then these are stored as seed genre data

**FR-103: Enrich metadata from supplemental sources** — Must Have  
Enrich library entries with canonical identifiers and supplemental metadata from multiple API sources.

- Given a song with ISRC, when enrichment is triggered, then the following lookups are performed:
  - **MusicBrainz:** Recording ID, work ID, artist credits (with `inc=artist-credits+isrcs`), genre tags (`inc=genres`)
  - **Deezer:** BPM, gain/loudness, contributors, ISRC verification (via `/track/isrc:{ISRC}`)
  - **ReccoBeats:** Full audio feature set (valence, danceability, energy, acousticness, etc.) using Spotify track ID
  - **Last.fm:** Community genre/mood tags with weighted counts (via `track.getTopTags`)
  - **AcousticBrainz:** Pre-computed audio features if MusicBrainz Recording MBID is available
  - **Musixmatch:** Structured genre data, lyrics availability indicator (Could Have)
- Given raw API responses are received, then they are cached verbatim in the source cache tables with timestamps
- Given enrichment data is received, then it is merged into both the structured `audio_features` table and the `song_tags` table with source attribution

**FR-104: Manual song entry** — Could Have  
Add songs not available on any streaming platform.

- Given a user enters title, artist, album, and language manually, then a new library entry is created with default Glicko-2 scores
- Manual entry should be minimal — the vast majority of songs should come from platform imports (FR-100 through FR-102)

**FR-105: Song relationship management** — Must Have  
Define and manage relationships between songs.

Relationship types:

| Type | Behaviour | Example |
|------|-----------|---------|
| Canonical alias | Shared Glicko-2 score; ranked as one song | "What is Love" on *Twicetagram* and *#TWICE* |
| Translation | Separate scores; linked as translation pair | "What is Love" (Korean) ↔ "What is Love" (Japanese) |
| Remix | Separate scores; linked to original | "Alcohol-Free" ↔ "Alcohol-Free (Instrumental)" |
| Live recording | Separate scores; linked to studio version | Concert recording ↔ album track |
| Acoustic/Unplugged | Separate scores; linked to original | Same as remix treatment |
| Solo/sub-unit version | Separate scores; linked to group version | Dahyun's "Glow" ↔ TWICE "Glow" |
| Medley/mashup | Separate score; flagged as medley in metadata | Medley track containing multiple songs |

Acceptance criteria:

- Given two songs are the same recording on different albums, when linked as canonical aliases, then they share a single Glicko-2 score
- Given any other relationship type, when linked, then both retain separate Glicko-2 scores and the relationship is queryable for playlist filtering
- Given a song has a solo performer within a group listing (e.g., "Meeeeee" (Nayeon solo) by TWICE), when tagged, then both the official artist (TWICE) and the actual performer (Nayeon) are recorded via the `song_artists` M:N relationship with appropriate credit roles

**FR-106: Song metadata fields** — Must Have  
Each song stores metadata across two layers: the application layer (core song table with quick-access fields) and the metadata infrastructure layer (structured audio features, multi-source tags, and cross-platform IDs). See the Database Schema Design document for full table definitions.

Core song fields:

| Field | Source(s) | Notes |
|-------|-----------|-------|
| Title | All platforms | Official title as listed |
| Artist (structured) | All platforms, MusicBrainz | Via `song_artists` M:N with roles (primary, featured, performer, etc.) |
| Album (structured) | All platforms | Via `albums` table with FK |
| Language | Manual/inferred | Korean, Japanese, English, other |
| ISRC | Deezer (primary), Apple Music, MusicBrainz, Spotify (Extended Quota) | Canonical identifier; cached aggressively |
| MusicBrainz IDs | MusicBrainz | Recording MBID, work MBID |
| Duration | All platforms | Milliseconds |
| Track type | Manual | Title track, B-side, OST, special |
| Release date | All platforms, MusicBrainz (`first-release-date`) | Earliest release preferred |
| Performer tags | Manual/MusicBrainz artist credits | Lightweight array for quick display |
| Visual notes | Manual | TTT references, concert moments, YouTube links with timestamps |
| Custom tags | Manual/ML | Emotional/context tags |

Enrichment fields (separate tables with source tracking):

| Field | Source(s) | Table |
|-------|-----------|-------|
| BPM/tempo | Deezer, ReccoBeats, AcousticBrainz, Essentia | `audio_features` |
| Key/scale | ReccoBeats, AcousticBrainz, Essentia | `audio_features` |
| Valence, danceability, energy, etc. | ReccoBeats, AcousticBrainz | `audio_features` |
| Genre tags | Last.fm, MusicBrainz, Apple Music, Musixmatch | `song_tags` |
| Mood tags | Last.fm, AcousticBrainz, Musixmatch | `song_tags` |
| Cross-platform IDs | All platforms | `platform_song_ids` |
| Raw API responses | All platforms | `source_cache_tracks` |

**FR-107: Artist credit matching** — Must Have  
Handle artist credit mismatches between streaming platforms and MusicBrainz.

- Given MusicBrainz credits a solo track to an individual member (e.g., Nayeon) while streaming platforms credit the group (TWICE), when matching, then MusicBrainz "member of group" artist relationships are used to resolve the match
- Given artist IDs from each platform are stored in `platform_artist_ids`, when matching, then ID-based matching is preferred over name matching
- Given an artist group (e.g., TWICE), then all member relationships are pre-fetched and cached in the `artist_groups` table

### Epic 2: Glicko-2 Ranking System

**FR-200: Glicko-2 rating calculation** — Must Have  
Implement Glicko-2 with configurable parameters, processing comparisons immediately (no rating period batching).

Default parameters (configurable):

| Parameter | Default | Notes |
|-----------|---------|-------|
| Initial rating (μ) | 1500 | Standard starting point |
| Initial rating deviation (RD) | 350 | High uncertainty for new songs |
| Initial volatility (σ) | 0.06 | Standard Glicko-2 default |
| System constant (τ) | 0.5 | Controls volatility change rate |

- Given a comparison between Song A and Song B with a 5-level outcome, when processed, then both songs' ratings, RDs, and volatilities are updated per Glicko-2 formula
- Given parameters are changed in settings, when future comparisons are processed, then the new parameters apply (no retroactive recalculation)
- Given any parameter change, then the previous parameter set is closed (with `active_until` timestamp) and a new parameter record is created in the `glicko_parameters` table, preserving full history for analysis

**FR-201: 5-level comparison input** — Must Have  
Support nuanced preference expression.

| Input | Label | Glicko-2 Score |
|-------|-------|----------------|
| [STRONG] Strong [Previous Song] | Strong prefer previous | Previous = 1.0, Current = 0.0 |
| [SLIGHT] Slight [Previous Song] | Weak prefer previous | Previous = 0.75, Current = 0.25 |
| [EQUAL] Equal | Draw | Both = 0.5 |
| [SLIGHT] Slight [Current Song] | Weak prefer current | Previous = 0.25, Current = 0.75 |
| [STRONG] Strong [Current Song] | Strong prefer current | Previous = 0.0, Current = 1.0 |

- Given a comparison is submitted, when processed, then the Glicko-2 scores for both songs are updated immediately
- Given the outcome mapping values (0.0, 0.25, 0.5, 0.75, 1.0) may need tuning, then they are configurable and stored with history in the `glicko_parameters` table

**FR-202: Comparison across all song types** — Must Have  
All songs in the library are comparable in a single global Glicko-2 pool, including translations, remixes, live versions, and solo versions.

- Given a Korean original and its Japanese translation appear as a comparison pair, when voted on, then both songs' ratings are updated normally
- Given any two songs in the library, when presented for comparison, then the comparison is valid regardless of relationship type

**FR-203: Comparison undo/re-vote** — Must Have  
Support correcting accidental votes (critical for driving safety).

- Given a vote has been cast, when undo is triggered within a 10-second undo window, then the comparison is reversed and Glicko-2 scores are recalculated — this window applies even if the song has advanced to the next song, including late vote and pause-to-vote scenarios (FR-302)
- Given a re-vote is cast, then the original vote is replaced (not stacked) — the original comparison is soft-deleted (`is_undone = true`) and a new comparison is recorded
- Given a comparison is undone, then Glicko-2 scores are recalculated by replaying non-undone comparison history for the affected songs

**FR-204: Skip/dismiss comparison** — Must Have  
User must never feel compelled to vote.

- Given the comparison widget is visible, when skip/dismiss is pressed (or no interaction occurs), then no Glicko-2 data is recorded for that pair
- Given the skip button, it is always visible alongside comparison controls

**FR-205: Comparison audit trail** — Must Have  
Full history of all comparisons for transparency.

- Given any comparison, when recorded, then the following are stored: both songs, outcome, Glicko-2 scores before and after (including volatility), timestamp, source (mobile/desktop, passive/focused), context data (device, CarPlay, focus mode, location zone), and response time in milliseconds
- Given a song's ranking is queried, when audit trail is requested, then all comparisons involving that song are retrievable with their impact on the score

**FR-206: Ranking snapshots** — Must Have  
Capture ranking state for historical tracking.

- Given the end of a calendar week or month, when snapshot is triggered, then the complete ranking (all songs with ratings, RDs, volatilities, comparison counts) is stored
- Weekly snapshots are taken during the first 3 months (high volatility period), transitioning to monthly-only once rankings stabilise (configurable threshold)
- Given historical data exists, when MVP history view is requested, then a "current vs. last snapshot" comparison table is displayed
- Given all comparison history is stored, when needed, then any historical ranking can be reconstructed from the raw data

### Epic 3: Comparison UX During Playback

**FR-300: Now-playing detection (iOS)** — Must Have  
Detect what song is currently playing from any streaming app.

- Given Spotify, YouTube Music, or Apple Music is playing, when a song starts, then MusicElo reads the current track via `MPNowPlayingInfoCenter`
- Given track metadata is detected, when matched to the library, then the comparison UI is prepared for the current and previous songs

**FR-301: Now-playing detection (Desktop)** — Must Have  
Detect what song is currently playing via platform APIs.

- Given Spotify is the active player on any device, when the desktop web app polls the Player API, then the current track is identified
- Given Apple Music is the active player, when the desktop web app queries via MusicKit, then the current track is identified (feature parity with Spotify)
- Given YouTube Music is playing on the same machine, when feasible, then now-playing is detected (best effort; may require browser extension or OS-level detection)

**FR-302: Mobile comparison — three-phase timing** — Must Have  
Prevent mis-votes during mobile listening (driving, walking).

| Phase | Timing | UI Element |
|-------|--------|------------|
| **Late vote on previous pair** | First 5–10 seconds of new song | Large button (replaces normal vote area): "[↩️ BACK] Vote on previous pair". Tapping pauses current song, shows previous pair comparison, then replays current from start. |
| **Compare current vs. previous** | 10 seconds – last 10 seconds | Standard 5-level comparison widget with emoji buttons ([🔥 STRONG]/[👍 SLIGHT]/[🤝 EQUAL]). |
| **Pause to vote** | Last 10 seconds of song | Large button (replaces normal vote area): "[⏸️ PAUSE] Wait to vote". Tapping prevents auto-advance; song advances after vote or skip. |

- Given no interaction occurs during any phase, then the song plays to completion, advances normally, and no Glicko-2 data is recorded
- Given the skip/dismiss button, it is always visible in all three phases
- Given the "late vote on previous" button is in a panic-tap scenario, then it occupies the full comparison widget area (large, easy target)
- Given the "Wait to vote" button is tapped, then the playlist does not advance until vote or skip is pressed
- Given a vote is cast in any phase, then a 10-second undo window begins regardless of phase

**FR-303: Desktop comparison — multi-song** — Should Have  
Compare current song against multiple recent songs simultaneously.

- Given the last 3–5 songs played are tracked, when the desktop comparison UI is shown, then each recent song has its own 5-level comparison row against the current song
- Given a vote is cast for one row, then that comparison is processed independently (each row = one Glicko-2 comparison)
- Given not all rows need to be voted on, then unvoted rows produce no data

**FR-304: Focused pairwise comparison mode** — Could Have  
Optional mode for dedicated ranking sessions (not during listening).

- Given the user wants to do focused comparisons, when entering this mode, then the system presents optimally-selected pairs (maximising information gain based on current RD and comparison history)
- Given comparison fatigue, when ~10 focused comparisons are completed, then the system suggests stopping (soft limit, overridable)

### Epic 4: Passive Data Collection

**FR-400: Play history capture** — Must Have  
Record all playback events with context metadata.

| Data Point | Captured | Storage |
|------------|----------|---------|
| Song played | Always | Cloud |
| Datetime | Always | Cloud |
| Play duration / percentage | Always | Cloud |
| Device type (iPhone/Mac) | Always | Cloud |
| CarPlay active flag | Always | Cloud |
| Focus/DND status | Always | Cloud |
| Playback platform | Always | Cloud (spotify/youtube_music/apple_music) |
| Location zone name | When available | Cloud (zone name only; e.g., "Home", "Office", "Uni") |
| Apple Watch workout status | When available | Cloud (if technically feasible) |

- Given the location zone feature, then GPS coordinates are converted to user-defined zone names on the iOS device; only the zone name is stored in the cloud; zone boundary definitions never leave the device
- Given no context signal is detected, then the play event is still recorded with null context fields

**FR-401: Passive signals as context/ML data only** — Must Have  
Passive signals never directly affect Glicko-2 scores.

- Given a song is played to completion without user interaction, then no Glicko-2 score change occurs
- Given a song is skipped, replayed, liked, or removed from a playlist, then the event is recorded as context/ML data but Glicko-2 scores are not affected
- Given passive data exists, then it is available for future ML-based playlist generation and mood tagging

**FR-402: Location zone configuration (iOS)** — Should Have  
User-defined location zones for context inference.

- Given the user defines a zone (name + approximate radius around a GPS point), then all subsequent plays within that zone are tagged with the zone name
- Given zones are defined on-device, then zone boundary definitions are stored only on the iOS device (never in cloud)
- Given complex zone shapes (e.g., bus routes), then these are deferred to a later version — v3.0 supports only point-and-radius zones

### Epic 5: Playlist Generation and Export

**FR-500: Ranked playlist export** — Must Have  
Export top N songs by Glicko-2 rating to Spotify, YouTube Music, or Apple Music.

- Given a requested playlist size (e.g., top 50), when export is triggered, then a playlist is created/updated on the target platform with songs ordered by Glicko-2 rating

**FR-501: Category-filtered playlist export** — Must Have  
Export ranked songs filtered by category.

- Given filter criteria (language, track type, relationship type, performer, genre/mood tags, audio feature ranges, etc.), when export is triggered, then only matching songs are included, ordered by Glicko-2 rating
- Given example filters: "Korean title tracks only", "Japanese versions only", "Nayeon solos" (via `song_artists` query), "All versions of Feel Special (original + remixes + live)" (via `song_relationships`), "BPM > 120 AND energy > 0.7" (via `audio_features` table)

**FR-502: Auto-playlists by Glicko-2 threshold** — Must Have  
System-maintained playlists based on ranking thresholds.

- Given a threshold rule (e.g., top 50 by rating = "Favourites"), when rankings change, then the auto-playlist membership is updated automatically
- Given a song crosses a threshold, then it is promoted or relegated between auto-playlists

**FR-503: System-suggested playlist changes** — Should Have  
System flags candidates for manual review.

- Given a song in "General" has risen above the "Favourites" threshold, when the user opens playlist management, then the system suggests promotion with supporting data (recent comparisons, rank trajectory)
- Given the user confirms or rejects the suggestion, then the playlist is updated accordingly

**FR-504: Seed context data from enrichment pipeline** — Must Have  
Initialise context/ML data from available platform audio features at import time.

- Given the metadata enrichment pipeline (FR-103) provides audio features and tags from multiple sources, when a song is imported, then these features are stored as seed context data
- Given seed data exists, then it is immediately available for category-filtered playlists and future emotional journey generation

### Epic 6: Rankings and History Display

**FR-600: Ranked song list** — Must Have  
Display all songs ordered by Glicko-2 rating with confidence indicators.

- Given the rankings view, when displayed, then each song shows: rank, title, artist, rating, RD (as confidence level: Very Confident / Confident / Moderately Confident / Uncertain), language, and track type
- Given filters are available, when applied, then the list re-sorts within the filtered subset

**FR-601: Song detail view** — Must Have  
Detailed view of a single song's ranking data.

- Given a song is selected, when detail view opens, then it shows: full metadata, current Glicko-2 scores, comparison history (all pairwise comparisons involving this song), related songs (translations, remixes, etc.), visual notes, and rank trajectory vs. previous snapshot

**FR-602: Current vs. last snapshot comparison** — Must Have (MVP history visualisation)  
Simple historical comparison table.

- Given ranking snapshots exist, when history view is opened, then a table shows each song's current rank vs. last snapshot's rank, with rank change indicators (↑↓—)

**FR-603: Animated ranking history** — Deferred (post-MVP)  
Animated line graphs showing songs rising and falling over time. Data captured from day one via snapshots; visualisation built later.

---

## 4. Non-Functional Requirements

### Performance

| Requirement | Target | Verification |
|-------------|--------|-------------|
| NFR-001: Page/view load time | <2 seconds | Manual testing |
| NFR-002: Comparison input response | <200ms from tap to visual confirmation | Manual testing |
| NFR-003: Glicko-2 calculation | <100ms per comparison | Automated test |
| NFR-004: Now-playing detection latency | <3 seconds from song change to comparison UI ready | Manual testing |

### Scalability

| Requirement | Target | Notes |
|-------------|--------|-------|
| NFR-010: Library size | Up to 10,000 songs | TWICE ecosystem + extended library |
| NFR-011: Comparison history | Unlimited (years of data) | PostgreSQL handles this |
| NFR-012: Play history | Unlimited | Partitioned by month if needed |
| NFR-013: Database storage | <500 MB (Supabase free tier) | ~162 MB estimated at 10,000 tracks with full cache |

### Reliability

| Requirement | Target | Verification |
|-------------|--------|-------------|
| NFR-020: No lost comparisons | Zero data loss for completed votes | Offline queue + sync verification |
| NFR-021: Crash recovery | Pending votes survive app crash | Local persistence before sync |
| NFR-022: Offline operation | Comparison input works offline; syncs when connected | Test in airplane mode |

### Security and Privacy

| Requirement | Target | Notes |
|-------------|--------|-------|
| NFR-030: Cloud data | No precise GPS coordinates in cloud | Location zones on-device only |
| NFR-031: Authentication | API key / token-based for backend access | Standard OAuth for streaming APIs |
| NFR-032: Data export | Full data export in JSON/CSV on demand | Audit trail and academic use |
| NFR-033: Backup | Supabase auto-backup + manual export capability | Protect years of ranking data |
| NFR-034: API cache | Raw API responses cached locally | Protects against service disappearance (e.g., AcousticBrainz precedent) |

### Usability

| Requirement | Target | Notes |
|-------------|--------|-------|
| NFR-040: One-handed mobile operation | All comparison inputs reachable with one thumb | Driving/walking safety |
| NFR-041: Large tap targets | Comparison buttons ≥44pt minimum (Apple HIG) | Driving safety |
| NFR-042: Readable text | Minimum 16pt body text; adequate contrast ratios | Desktop and mobile |
| NFR-043: No colour-only indicators | All status conveyed via text/icon + colour | Accessibility |

### Sync

| Requirement | Target | Notes |
|-------------|--------|-------|
| NFR-050: Mobile ↔ Backend sync | Votes synced within 30 seconds when online | REST API polling or push |
| NFR-051: Desktop ↔ Backend | Real-time via web app connected to backend | WebSocket or polling |
| NFR-052: Offline queue | Votes queued locally; synced in order when connection restored | FIFO with timestamps |

---

## 5. Data Model

The data model spans two layers: the **application layer** (what the user interacts with — songs, ratings, comparisons, play events, playlists) and the **metadata infrastructure layer** (what supports cross-platform data collection, caching, and rebuild capability).

For complete table definitions, SQL DDL, ERD diagram, storage estimates, and design rationale, see the companion documents: **MusicElo Database Schema Design** (v1.0), **musicelo_schema.sql**, and **musicelo_erd.mermaid**.

### Schema Overview (22 tables)

| Layer | Tables | Purpose |
|-------|--------|---------|
| Core library | 7 | `songs`, `albums`, `artists`, `album_artists`, `song_artists`, `artist_groups`, `song_relationships` |
| Glicko-2 / app | 6 | `glicko_ratings`, `comparisons`, `play_events`, `ranking_snapshots`, `playlist_rules`, `glicko_parameters` |
| Platform cross-refs | 3 | `platform_song_ids`, `platform_artist_ids`, `platform_album_ids` |
| Raw cache | 3 | `source_cache_tracks`, `source_cache_albums`, `source_cache_artists` |
| Metadata | 2 | `audio_features`, `song_tags` |
| System | 1 | `merge_log` |

### Key Design Decisions (PRD ↔ Schema)

1. **PRD's flat "Song" → normalised songs + albums + artists.** The PRD's `artist_official` string becomes a proper `artists` table with M:N `song_artists` join. The PRD's `performer_tags` array is retained for quick display alongside the full M:N table for deep queries.

2. **Dual audio features storage.** `songs.audio_features` (JSONB) provides quick-access blob per PRD FR-106. The `audio_features` table provides queryable columns with per-field source tracking (e.g., BPM from Deezer vs. ReccoBeats).

3. **Cross-platform ID mapping.** `platform_song_ids` / `platform_artist_ids` / `platform_album_ids` tables store every platform's native ID for each entity with match method and confidence.

4. **Raw API response caching.** `source_cache_tracks/albums/artists` store verbatim JSON responses timestamped, providing insurance against service disappearance and enabling re-merge if deduplication methodology changes.

### Key Relationships

- Song → GlickoRating: one-to-one (canonical songs only; aliases point to canonical)
- Song → Song (canonical_id): many-to-one (aliases → canonical)
- Song ↔ Song (SongRelationship): many-to-many with type
- Song ↔ Artist (song_artists): many-to-many with roles
- Song → Album: many-to-one
- Artist → Artist (artist_groups): many-to-many (member ↔ group)
- Song → Comparison: one-to-many (as song_a or song_b)
- Song → PlayEvent: one-to-many
- Song → platform_song_ids: one-to-many (cross-platform IDs)
- Song → audio_features: one-to-one (structured)
- Song → song_tags: one-to-many (multi-source)

### Business Rules

- **BR-001:** New songs initialise with rating 1500, RD 350, volatility 0.06
- **BR-002:** Canonical alias songs share a single `glicko_ratings` record; the alias' `canonical_id` points to the rated song
- **BR-003:** All other relationship types maintain separate `glicko_ratings` records
- **BR-004:** Comparisons always reference the canonical song ID (not alias) for Glicko-2 calculation
- **BR-005:** Glicko-2 updates are immediate (no rating period batching)
- **BR-006:** Undone comparisons are soft-deleted (`is_undone = true`); Glicko-2 scores are recalculated by replaying non-undone comparison history for affected songs
- **BR-007:** No interaction during playback = no Glicko-2 data recorded
- **BR-008:** Passive signals (play events) never trigger Glicko-2 score changes
- **BR-009:** Ranking snapshots are taken weekly during the first 3 months (high volatility), then monthly thereafter
- **BR-010:** ISRCs are cached aggressively — once obtained, they are permanent identifiers
- **BR-011:** Artist IDs from every platform are stored (not just names) for reliable cross-platform matching
- **BR-012:** Raw API responses are cached with timestamps to protect against service changes or disappearance

---

## 6. Assumptions and Constraints

### Assumptions

1. User has Spotify Premium for Player API access (Student pricing: ~$7.99 AUD/month)
2. User has Apple Developer Program membership for iOS app distribution (~$149 AUD/year)
3. User has Apple Music subscription for MusicKit metadata access (Student pricing: ~$6.99 AUD/month)
4. iOS `MPNowPlayingInfoCenter` reliably reports current track from all streaming apps
5. Spotify Connect API remains available under February 2026 restrictions (confirmed in discovery)
6. MusicBrainz has adequate TWICE discography coverage
7. Single-user system — no authentication complexity beyond API tokens
8. Deezer API remains free for unauthenticated catalogue lookups
9. ReccoBeats API remains available as a free audio features source

### Constraints

1. **Budget:** <$30 AUD/month total recurring costs
2. **Development time:** 2–3 hours/week alongside full-time work, part-time Masters, and other commitments
3. **Technical skill:** Primary developer (with AI assistance) has Python and basic HTML experience; Swift is new; no JavaScript experience
4. **Spotify API:** Development Mode limited to 1 Client ID, 5 authorised users, requires Premium. ISRC removed from Dev Mode (Feb 2026). Audio Features endpoint restricted for new apps.
5. **iOS background execution:** iOS limits background processing; now-playing detection and vote queueing must work within iOS background execution rules
6. **MusicBrainz rate limit:** 1 request/second with mandatory descriptive User-Agent
7. **ReccoBeats rate limit:** ~0.5s between calls; batch size ~5 IDs

---

## 7. Out of Scope (v3.0)

| Item | Reason | Future? |
|------|--------|---------|
| Social features / multi-user ranking | Cost-prohibitive; Spotify limits to 5 users | v4.0+ |
| Real-time collaborative filtering | Requires multi-user | v4.0+ |
| Cross-artist ranking (beyond TWICE ecosystem) | Testing scope; design supports it | v4.0 |
| TTT episode ranking | Different content type | v4.0 |
| Music discovery outside personal library | Different problem domain | Maybe |
| Advanced emotional journey playlists | Requires sufficient ML data; infrastructure in place | v3.1+ |
| Animated ranking history visualisation | Data captured from day one; UI deferred | v3.1 |
| Android/Windows native apps | iOS/macOS/web first | v4.0+ |
| Multi-user database design | Single user; schema extensible if straightforward | v4.0+ |
| Local audio analysis (Essentia/librosa) | Requires audio files; API sources sufficient for MVP | v3.1+ |
| Lyrics integration | Musixmatch free tier limited; not core to ranking | v3.1+ |
| Bus route / complex zone shapes | GPS corridor processing complex; point-and-radius zones only for v3.0 | v3.1+ |

---

## 8. Release Criteria

### MVP (v3.0) Ready When:

- [ ] Song library imported from at least two platforms (Spotify + Apple Music or YouTube Music) with ISRC-based deduplication
- [ ] Song relationships (canonical aliases, translations, remixes) manageable
- [ ] Metadata enriched from Deezer (ISRC + BPM) and MusicBrainz (canonical IDs)
- [ ] Glicko-2 comparisons processed correctly with 5-level input
- [ ] iOS companion app detects now-playing and presents comparison widget
- [ ] Desktop web app shows ranked song list and multi-song comparison
- [ ] Comparisons sync between mobile and desktop via backend
- [ ] Offline vote queue works on iOS
- [ ] Play history captured with context metadata (device, CarPlay, Focus/DND, playback platform)
- [ ] Ranking snapshots captured (weekly during early phase, monthly thereafter)
- [ ] Ranked playlist export to at least one platform functional
- [ ] Undo/re-vote functional with 10-second window
- [ ] All comparison data has full audit trail (including volatility before/after)
- [ ] Skip/dismiss always available; no interaction = no data
- [ ] Cross-platform song IDs stored in `platform_song_ids` for all imported songs
- [ ] Raw API responses cached in `source_cache_tracks`

### Quality Gates:

- [ ] No lost comparisons after 1 week of daily use testing
- [ ] Comparison input works one-handed on iPhone (driving simulation test)
- [ ] Page load <2 seconds on desktop; comparison response <200ms on mobile
- [ ] Data export functional (JSON/CSV)

---

## 9. Open Questions and Technical Risks

### Open Questions (To Resolve in Design Phase)

| # | Question | Impact |
|---|----------|--------|
| OQ-1 | Desktop web framework choice (React vs. simpler alternative given no JS experience) | Frontend development approach |
| OQ-2 | YouTube Music now-playing detection on desktop (no official API; may need browser extension) | Desktop YTM integration |
| OQ-3 | iOS background execution limits for now-playing polling frequency | Comparison availability reliability |
| OQ-4 | Apple Watch workout status API feasibility from companion iOS app | Exercise context detection |
| OQ-5 | Optimal Glicko-2 parameter tuning approach after initial use | Rating behaviour calibration |
| OQ-6 | Song matching algorithm for cross-platform deduplication (ISRC + fuzzy matching fallback) — tolerance thresholds for title/artist/duration heuristic matching | Data import accuracy |
| OQ-7 | Deezer ISRC lookup endpoint reliability — undocumented, returns only 1 result per ISRC | ISRC resolution completeness |
| OQ-8 | ReccoBeats data provenance — feature extraction methodology not fully documented | Audio feature accuracy |
| OQ-9 | MusicBrainz TWICE discography coverage completeness, particularly for recent releases and solo/sub-unit tracks | Metadata enrichment coverage |

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Spotify API further restricted | Medium | High | Apple Music + Deezer + MusicBrainz as metadata backbone; `MPNowPlayingInfoCenter` platform-agnostic for now-playing |
| iOS background execution blocks now-playing polling | Low-Medium | High | Live Activities or notification-based approach; test early in development |
| YouTube Music has no desktop API | High | Medium | Accept Spotify/Apple Music for desktop monitoring; YTM works on mobile via `MPNowPlayingInfoCenter` |
| Supabase free tier limits reached | Very Low | Low | ~162 MB at 10K tracks; upgrade to $25/month Pro if needed |
| Swift learning curve delays iOS app | Medium | Medium | AI-assisted development; keep iOS app minimal (comparison widget + sync only) |
| ReccoBeats service discontinuation | Low-Medium | Medium | AcousticBrainz legacy data as fallback; Essentia local analysis as ultimate fallback |
| Deezer API rate limiting or restriction | Low | Medium | Cache aggressively; Deezer data is mostly one-time lookups |
| MusicBrainz incomplete K-pop coverage | Low-Medium | Low | Artist credit matching handles group/solo mismatch; manual override available |
| Unofficial ytmusicapi breaks | Medium | Medium | YouTube Music data is supplementary; Spotify + Apple Music provide core metadata |

---

## 10. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Spotify Web API (Player, Playlists, Tracks) | External API | Available; Feb 2026 restrictions confirmed survivable |
| Spotify Premium subscription (Student) | Financial | Accepted (~$7.99 AUD/month) |
| Apple Developer Program | Financial | Accepted (~$149 AUD/year) |
| Apple Music subscription (Student) | Financial | Accepted (~$6.99 AUD/month) |
| Apple Music API (MusicKit) | External API | Available; requires Apple Developer Program |
| MusicBrainz API | External API | Free; 1 req/sec rate limit |
| Deezer API | External API | Free; no auth for catalogue lookups |
| ReccoBeats API | External API | Free; no auth for track lookups |
| Last.fm API | External API | Free API key; ~5 req/sec |
| Musixmatch API | External API | Free tier; 2,000 calls/day |
| AcousticBrainz | External API (legacy) | Available but no new data |
| Unofficial ytmusicapi | External library | Reverse-engineered; may break |
| Supabase | Infrastructure | Free tier; no commitment |
| Railway or Render | Infrastructure | Free tier; no commitment |
| iOS `MPNowPlayingInfoCenter` | Platform API | Built into iOS; no external dependency |

---

## 11. Companion Documents

The following documents provide detailed context and should be consulted alongside this PRD:

| Document | Description | Status |
|----------|-------------|--------|
| **01-discovery/problem-statement.md** | Core problem definition, background, success criteria | ✅ Approved |
| **01-discovery/user-research-findings.md** | User profile, pain points, behavioural patterns | ✅ Approved |
| **01-discovery/business-case.md** | Strategic alignment, ROI analysis, risks | ✅ Approved |
| **01-discovery/stakeholder-analysis.md** | Stakeholder mapping, engagement strategy | ✅ Approved |
| **Song_Metadata_API_Research_Report.md** | 10-source API research, ISRC strategy, audio features landscape | ✅ Complete |
| **metadata_fields_all_services.json** | Machine-readable API field catalogue | ✅ Complete |
| **MusicElo_Database_Schema_Design.md** | 22-table schema design, storage estimates, design rationale | ✅ Complete |
| **musicelo_schema.sql** | PostgreSQL DDL (tables, indexes, views, triggers) | ✅ Complete |
| **musicelo_erd.mermaid** | Entity relationship diagram (Mermaid format) | ✅ Complete |

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-15 | 0.1 | Initial PRD draft from requirements intake v0.2 | Enoch Ko |
| 2026-02-16 | 0.2 | Major iteration: incorporated API research findings (expanded data sources, Deezer as primary ISRC source, ReccoBeats for audio features, Last.fm for tags); elevated Apple Music to Must Have; integrated database schema design (22-table two-layer architecture); added metadata enrichment strategy; added artist credit matching requirement (FR-107); expanded FR-103 to cover all enrichment sources; added weekly snapshots option; added 10-second undo window clarification; added student pricing; added companion documents section; resolved all v0.1 annotations | Enoch Ko |

---

## Document Status

**Status:** Draft — Ready for Product Owner Review  
**Next Step:** Review and feedback, then finalise for GitHub publication
