# MusicElo v3.0 — Implementation Plan

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Document:** Implementation Plan  
**Stage:** Design Foundation  
**Version:** 0.1 (pre-spike draft — subject to revision after S-01 through S-10)  
**Author:** Enoch Ko  
**Date:** February 2026

---

## Purpose

This document translates PRD requirements into a sequenced, branch-level execution
plan. Each unit is independently completable, demonstrable, and mergeable. Units are
ordered to build on confirmed foundations — no unit assumes unvalidated API
capabilities (see spike dependency notes).

**This is a living document.** Revise after spike tests complete (S-01 through S-10),
and after each phase as estimates are calibrated against actual cycle time.

---

## Guiding Principles

- **One branch per unit.** Each unit produces working, tested code that can be
  reviewed and merged independently.
- **Tests first for Tier 1 code.** Glicko-2 engine and comparison logic have tests
  written before implementation. See `test-plan.md`.
- **Spike results govern.** No API integration unit starts until the relevant spike
  test is complete and documented in `docs/02-requirements/spikes/`.
- **Passive before active.** Infrastructure (DB, backend scaffold, Glicko-2 core)
  before features. Core ranking before enrichment. Mobile MVP before polish.
- **Portfolio visibility.** Each phase produces a demonstrable, explainable artifact.
  Commit history should tell a coherent story.

---

## Constraints

| Constraint | Value |
|---|---|
| Development time | ~2–3 hours/week |
| Primary developer | Solo, with AI assistance |
| Swift experience | New — keep iOS app minimal |
| JS experience | None — desktop web framework TBD (OQ-1) |
| Budget | <$30 AUD/month |

At 2–3 hours/week, a "session" is one development sitting (~2 hours). Estimates below
are in sessions, not calendar weeks — calendar time will be longer due to scheduling.

---

## Phase Overview

| Phase | Focus | Key Deliverable |
|---|---|---|
| **0 — Foundation** | Repo, DB scaffold, backend skeleton | Running FastAPI app connected to Supabase |
| **1 — Glicko-2 Core** | Pure math engine + DB integration | Testable, provably correct ranking engine |
| **2 — Song Library** | Import, dedup, relationships | Songs importable from CSV/manual entry |
| **3 — Comparisons** | Record, undo, audit trail | Functional comparison recording via API |
| **4 — Enrichment** | Metadata pipeline (post-spike) | Songs enriched from Deezer + MusicBrainz |
| **5 — Now-Playing (iOS)** | MPNowPlayingInfoCenter + comparison widget | iOS app surfaces comparison during listening |
| **6 — Platform Import** | Spotify + Apple Music + YouTube Music | Real library importable |
| **7 — Rankings Display** | Desktop web rankings view | Ranked song list visible in browser |
| **8 — Playlist Export** | Export to streaming platforms | Top-N playlist pushable to Spotify/Apple Music |
| **9 — Polish and Release** | Offline queue, snapshots, manual test checklist | MVP release criteria met |

---

## Phase 0 — Foundation

**Goal:** Running infrastructure. No features yet. Everything subsequent builds on this.

### Unit 0.1 — Repository and Environment Setup
**Branch:** `setup/repo-init`  
**PRD reference:** §6 Constraints, §10 Dependencies  
**Estimated effort:** 1 session

- Initialise Git repo with branch strategy (`main`, `v3-development`, feature branches)
- Add `CLAUDE.md` to repo root
- Add `.env.example` with all required environment variables (no secrets)
- Add `.gitignore` (Python, Swift, secrets)
- Add `docs/` folder structure: `01-discovery/`, `02-requirements/`, `02-requirements/spikes/`, `03-design/`
- Commit all existing docs (PRD, schema SQL, ERD, API research, test plan,
  backend architecture, this document)
- **Definition of done:** Clean repo; all docs committed; CLAUDE.md in place

### Unit 0.2 — Database Schema Deployment
**Branch:** `setup/database-schema`  
**PRD reference:** §5 Data Model, companion `musicelo_schema.sql`  
**Estimated effort:** 1 session  
**Depends on:** Unit 0.1

- Set up Supabase project (free tier)
- Configure Alembic with async SQLAlchemy connection
- Deploy `musicelo_schema.sql` via Alembic initial migration (not raw SQL — wrap
  existing DDL in an Alembic migration file)
- Verify all 22 tables created with correct indexes and constraints
- Confirm storage baseline is within Supabase free tier (target <5MB empty)
- **Definition of done:** `alembic upgrade head` succeeds against Supabase; all
  tables visible in Supabase dashboard

### Unit 0.3 — Backend Scaffold
**Branch:** `setup/backend-scaffold`  
**PRD reference:** §2 Solution Architecture  
**Estimated effort:** 1 session  
**Depends on:** Unit 0.2

- Create `backend/` structure per `backend-architecture.md`
- `core/config.py` — Pydantic `BaseSettings` loading from `.env`
- `core/database.py` — Async SQLAlchemy engine + session factory
- `core/exceptions.py` — Stub custom exception classes
- `main.py` — FastAPI app with health check endpoint (`GET /health → 200 OK`)
- Stub `__init__.py` and empty module files for all slices (songs, comparisons,
  rankings, playlists, enrichment)
- Configure pytest with test DB connection (separate Supabase project or local
  PostgreSQL)
- **Definition of done:** `GET /health` returns 200; `pytest` runs with 0 tests,
  0 errors

---

## Phase 1 — Glicko-2 Core

**Goal:** Provably correct Glicko-2 engine. The most critical code in the system.
Written test-first.

### Unit 1.1 — Pure Glicko-2 Math Engine
**Branch:** `feat/glicko2-engine`  
**PRD reference:** FR-200, FR-201, BR-001 through BR-006  
**Estimated effort:** 2 sessions  
**Depends on:** Unit 0.3  
**Tests:** T-001 through T-013 (write before implementing)

- Implement `core/glicko2.py`:
  - `initialise_rating() → GlickoRating`
  - `map_outcome(level: ComparisonLevel) → float` — maps 5-level input to
    0.0/0.25/0.5/0.75/1.0
  - `update_ratings(song_a, song_b, outcome, params) → tuple[GlickoRating, GlickoRating]`
  - `replay_comparisons(history: list[ComparisonRecord]) → dict[int, GlickoRating]`
- No database imports. No FastAPI imports.
- All tests T-001 through T-013 passing
- Hand-verify at least one update result against the official Glicko-2 worked example
  from Glickman's paper
- **Definition of done:** All Tier 1 Glicko-2 math tests pass; module has zero
  non-stdlib imports

### Unit 1.2 — Glicko-2 DB Integration
**Branch:** `feat/glicko2-db`  
**PRD reference:** FR-200, FR-206, BR-001, BR-005  
**Estimated effort:** 1 session  
**Depends on:** Unit 1.1  
**Tests:** T-047 (new song initialises with defaults)

- SQLAlchemy ORM model for `glicko_ratings` in `comparisons/models.py`
- `comparisons/repository.py`:
  - `get_rating(song_id) → GlickoRating | None`
  - `upsert_rating(song_id, rating: GlickoRating) → None`
  - `initialise_rating(song_id) → GlickoRating` — inserts BR-001 defaults
- `glicko_parameters` ORM model + repository (read current params; write new param
  set with `active_until` on change)
- Integration test: insert song, call `initialise_rating`, read back — assert
  1500/350/0.06
- **Definition of done:** T-047 passing; `glicko_ratings` row readable/writable
  via repository

---

## Phase 2 — Song Library (Manual Import)

**Goal:** Songs can be added to the library manually or via CSV before platform
integrations are built. Enables Glicko-2 testing with real song data.

### Unit 2.1 — Song, Album, Artist ORM Models
**Branch:** `feat/song-models`  
**PRD reference:** FR-105, FR-106, §5 Data Model  
**Estimated effort:** 1 session  
**Depends on:** Unit 0.3

- SQLAlchemy ORM models in `songs/models.py`:
  - `Song`, `Album`, `Artist`
  - `SongArtist` (M:N with roles), `AlbumArtist` (M:N)
  - `ArtistGroup` (M:N, member ↔ group)
  - `SongRelationship` (M:N with type)
  - `PlatformSongId`, `PlatformArtistId`, `PlatformAlbumId`
- Pydantic schemas in `songs/schemas.py` for create/read
- Basic repository functions: `get_song`, `create_song`, `get_by_isrc`
- **Definition of done:** ORM models map correctly to deployed schema; no migration
  needed (schema already deployed in 0.2)

### Unit 2.2 — Manual Song Entry and CSV Import
**Branch:** `feat/song-import-manual`  
**PRD reference:** FR-104, FR-100 (dedup logic)  
**Estimated effort:** 1–2 sessions  
**Depends on:** Unit 2.1, Unit 1.2

- `songs/service.py`:
  - `create_song(data: SongCreate) → Song` — creates song, initialises
    `glicko_ratings`
  - `import_from_csv(path: str) → ImportResult` — reads CSV of title/artist/album/
    language/ISRC; calls `create_song` per row; deduplicates by ISRC
  - Dedup rule: if ISRC match exists, merge metadata and preserve `glicko_ratings`
- FastAPI route: `POST /songs` (single), `POST /songs/import/csv` (bulk)
- Tests: T-047 (new song gets defaults), T-048 (re-import preserves scores),
  T-124 (duplicate ISRC does not create second row)
- CSV format for TWICE library bootstrap (separate from code — see `docs/data/`)
- **Definition of done:** Can import 300+ TWICE songs from CSV; duplicates handled;
  all initialised with correct Glicko-2 defaults

### Unit 2.3 — Song Relationship Management
**Branch:** `feat/song-relationships`  
**PRD reference:** FR-105, BR-002, BR-003  
**Estimated effort:** 1–2 sessions  
**Depends on:** Unit 2.2  
**Tests:** T-040 through T-046

- `songs/service.py`:
  - `link_canonical_alias(song_id, canonical_id)` — sets `canonical_id` FK; removes
    alias's `glicko_ratings` row if it exists (canonical owns the rating)
  - `link_relationship(song_a_id, song_b_id, type: RelationshipType)` — creates
    `song_relationships` row; both songs retain separate `glicko_ratings`
- FastAPI routes: `POST /songs/{id}/alias`, `POST /songs/{id}/relationship`
- All T-040 through T-046 passing
- **Definition of done:** Canonical aliases share one `glicko_ratings`; all other
  types maintain separate records; all relationship tests passing

---

## Phase 3 — Comparisons

**Goal:** Functional comparison recording, undo, and audit trail. The core user-facing
feature of the backend.

### Unit 3.1 — Record Comparison
**Branch:** `feat/comparison-record`  
**PRD reference:** FR-200, FR-201, FR-204, FR-205, BR-004 through BR-008  
**Estimated effort:** 2 sessions  
**Depends on:** Unit 1.2, Unit 2.3  
**Tests:** T-020 through T-027

- `comparisons/service.py`:
  - `record_comparison(song_a_id, song_b_id, outcome, context) → Comparison`
    - Resolves alias → canonical for both songs (BR-004)
    - Fetches current `glicko_ratings` for both
    - Calls `core/glicko2.update_ratings()`
    - Writes `comparisons` row with pre/post scores, context, timestamp,
      response_time_ms (FR-205)
    - Writes updated `glicko_ratings` for both songs
  - `skip_comparison(song_a_id, song_b_id) → None` — no DB writes (FR-204)
  - `record_play_event(song_id, context) → PlayEvent` — writes to `play_events`
    only, never touches `glicko_ratings` (FR-400, BR-008)
- FastAPI routes: `POST /comparisons`, `POST /comparisons/skip`,
  `POST /play-events`
- All T-020 through T-027 passing
- **Definition of done:** Comparison recorded with full audit trail; play events
  recorded without Glicko-2 side effects; all tests passing

### Unit 3.2 — Undo and Replay
**Branch:** `feat/comparison-undo`  
**PRD reference:** FR-203, BR-006  
**Estimated effort:** 2 sessions  
**Depends on:** Unit 3.1  
**Tests:** T-030 through T-039

- `comparisons/service.py`:
  - `undo_comparison(comparison_id, requested_at) → None`
    - Validates within 10-second window (FR-203)
    - Sets `is_undone=True` on `comparisons` row
    - Fetches all non-undone comparisons for both affected songs in chronological order
    - Calls `core/glicko2.replay_comparisons()` for each song
    - Writes replayed ratings to `glicko_ratings`
  - `re_vote(original_comparison_id, new_outcome, context) → Comparison`
    - Calls `undo_comparison` on original
    - Calls `record_comparison` with new outcome
- FastAPI routes: `POST /comparisons/{id}/undo`, `POST /comparisons/{id}/revote`
- All T-030 through T-039 passing
- **Definition of done:** Undo soft-deletes and replays correctly; replay is
  deterministic; 10-second window enforced; all tests passing

---

## Phase 4 — Metadata Enrichment

**⚠️ Spike dependency.** Do not start unit 4.x until the relevant spike test is
complete and documented.

| Unit | Spike Required |
|---|---|
| 4.1 Deezer | S-03 (Deezer ISRC endpoint reliability) |
| 4.2 MusicBrainz | S-04 (MusicBrainz TWICE coverage) |
| 4.3 ReccoBeats | S-05 (ReccoBeats feature availability) |
| 4.4 Last.fm | S-06 (Last.fm tag quality for K-pop) |

### Unit 4.0 — Enrichment Infrastructure
**Branch:** `feat/enrichment-infra`  
**PRD reference:** FR-103, BR-012  
**Estimated effort:** 1 session  
**Depends on:** Unit 2.2

- SQLAlchemy models in `enrichment/models.py`:
  `AudioFeatures`, `SongTag`, `SourceCacheTracks`, `SourceCacheAlbums`,
  `SourceCacheArtists`, `MergeLog`
- `enrichment/cache.py` — `cache_raw_response(source, entity_id, raw_json)`
- `enrichment/merge.py` — `merge_audio_features(song_id, source, data)`,
  `merge_tags(song_id, source, tags)`
- FastAPI route stubs only (no source integrations yet)
- **Definition of done:** Cache and merge modules functional; source cache tables
  writable from Python

### Unit 4.1 — Deezer Enrichment
**Branch:** `feat/enrichment-deezer`  
**PRD reference:** FR-103 (Deezer tier)  
**Estimated effort:** 1 session  
**Spike required:** S-03  
**Tests:** T-100 through T-103

- `enrichment/sources/deezer.py`:
  - `lookup_by_isrc(isrc: str) → DeezerTrack | None`
  - Rate limiting, error handling, cache write (BR-012)
- `enrichment/pipeline.py` — initial orchestration for Deezer only
- FastAPI route: `POST /enrich/{song_id}` triggers Deezer lookup
- T-100 through T-103 passing
- **Definition of done:** Deezer BPM + ISRC written to `audio_features`; raw
  response cached; partial failure handled gracefully

### Unit 4.2 — MusicBrainz Enrichment
**Branch:** `feat/enrichment-musicbrainz`  
**PRD reference:** FR-103 (MusicBrainz tier), FR-107  
**Estimated effort:** 2 sessions  
**Spike required:** S-04  
**Tests:** T-104 through T-107, T-123

- `enrichment/sources/musicbrainz.py`:
  - `lookup_by_isrc(isrc: str) → MBRecording | None`
  - `lookup_artist_credits(mbid: str) → list[ArtistCredit]`
  - Rate limiter enforced (1 req/sec with mandatory User-Agent) — T-104, T-105
  - Group/solo artist credit mismatch resolution — T-123
- `songs/service.py`: update to write MusicBrainz artist credits to `song_artists`
- Extend `enrichment/pipeline.py` to include MusicBrainz step
- T-104 through T-107, T-123 passing
- **Definition of done:** Recording MBID, artist credits (including group/member
  disambiguation) written; rate limit respected; raw response cached

### Unit 4.3 — ReccoBeats Enrichment
**Branch:** `feat/enrichment-reccobeats`  
**PRD reference:** FR-103 (ReccoBeats tier)  
**Estimated effort:** 1 session  
**Spike required:** S-05  
**Tests:** T-108, T-109

- `enrichment/sources/reccobeats.py`:
  - `get_audio_features(spotify_ids: list[str]) → list[AudioFeatureResult]`
  - Batch enforcement (max 5 IDs) — T-108
  - Rate limit delay — T-109
- Requires Spotify track ID in `platform_song_ids` — enrich only songs with
  Spotify IDs
- **Definition of done:** Valence, danceability, energy, etc. written to
  `audio_features` with source='reccobeats'; batch and rate limits enforced

### Unit 4.4 — Last.fm Tags
**Branch:** `feat/enrichment-lastfm`  
**PRD reference:** FR-103 (Last.fm tier)  
**Estimated effort:** 1 session  
**Spike required:** S-06  
**Tests:** T-110

- `enrichment/sources/lastfm.py`:
  - `get_top_tags(artist, track) → list[Tag]`
- Tags written to `song_tags` with source='lastfm' and count values
- **Definition of done:** Community genre/mood tags in `song_tags`; T-110 passing

### Unit 4.5 — Enrichment Pipeline Integration
**Branch:** `feat/enrichment-pipeline`  
**PRD reference:** FR-103, FR-103 partial failure  
**Estimated effort:** 1 session  
**Depends on:** Units 4.0–4.4  
**Tests:** T-111, T-112

- `enrichment/pipeline.py` — full orchestration across all sources
- Partial failure isolation: one source error does not block others (T-112)
- `POST /enrich/batch` endpoint for bulk enrichment of imported songs
- **Definition of done:** T-111 and T-112 passing; enrichment pipeline runs
  end-to-end for a sample of TWICE songs

---

## Phase 5 — iOS Companion App

**⚠️ Spike dependency.** Do not start until S-07 (MPNowPlayingInfoCenter reliability)
is complete.

**Note:** Swift is new. Keep iOS scope minimal. One screen: comparison widget.
AI-assisted implementation. Expect longer cycle time per session.

### Unit 5.1 — iOS Project Setup
**Branch:** `feat/ios-scaffold`  
**Estimated effort:** 1–2 sessions  
**Spike required:** S-07

- Xcode project setup, Apple Developer Program configuration
- Target: iPhone only, iOS 16+
- Single-screen app with placeholder comparison widget
- Backend API client (URLSession, async/await)
- **Definition of done:** App builds and runs on device; can make HTTP request
  to backend health check

### Unit 5.2 — Now-Playing Detection
**Branch:** `feat/ios-nowplaying`  
**PRD reference:** FR-300  
**Estimated effort:** 2 sessions  
**Spike required:** S-07  
**Depends on:** Unit 5.1

- `MPNowPlayingInfoCenter` integration — read current track title, artist,
  duration
- Poll every 2 seconds for track changes (configurable)
- On track change: send track info to backend `GET /songs/match` to resolve
  library entry
- Handle: song not in library (no UI shown), song in library (proceed to
  comparison UI)
- **Definition of done:** Changing track in Spotify/Apple Music/YouTube Music
  is detected in MusicElo within 3 seconds (M-005 through M-007)

### Unit 5.3 — Comparison Widget (iOS)
**Branch:** `feat/ios-comparison-widget`  
**PRD reference:** FR-302, FR-201, FR-203, FR-204  
**Estimated effort:** 3–4 sessions  
**Depends on:** Unit 5.2, Unit 3.1

- Three-phase timing UI (FR-302):
  - Phase 1 (0–10s): "Late vote" full-width button
  - Phase 2 (10s–last 10s): 5-level comparison widget (5 buttons)
  - Phase 3 (last 10s): "Pause to vote" full-width button
- Skip/dismiss always visible (FR-204)
- Tap → `POST /comparisons` to backend
- 10-second undo button after vote (FR-203)
- CarPlay detection flag sent with comparison payload
- All buttons ≥44pt (NFR-041), one-handed reachable (NFR-040)
- Manual tests: M-001 through M-004, M-009
- **Definition of done:** Full comparison flow works end-to-end; undo functional;
  M-001 through M-004 pass

### Unit 5.4 — Offline Vote Queue (iOS)
**Branch:** `feat/ios-offline-queue`  
**PRD reference:** FR-203, NFR-020, NFR-021, NFR-022  
**Estimated effort:** 2 sessions  
**Depends on:** Unit 5.3, Unit 3.2  
**Tests:** T-130 through T-133

- Local persistence of pending comparisons (UserDefaults or Core Data — TBD A-03)
- Queue drains when network available; FIFO order preserved
- Survives app crash
- M-008 manual test passing
- **Definition of done:** T-130 through T-133 passing; M-008 passing

---

## Phase 6 — Platform Import

**⚠️ Spike dependency.** Do not start until relevant spike complete.

| Unit | Spike Required |
|---|---|
| 6.1 Spotify | S-01 (Spotify Dev Mode), S-02 (Spotify Connect) |
| 6.2 Apple Music | S-08 (MusicKit metadata, ISRC on library songs) |
| 6.3 YouTube Music | S-09 (ytmusicapi reliability) |

### Unit 6.1 — Spotify Import
**Branch:** `feat/import-spotify`  
**PRD reference:** FR-100  
**Estimated effort:** 2 sessions  
**Spike required:** S-01, S-02  
**Tests:** T-120, T-122, T-124, T-125, T-200

- `songs/service.py` — `import_from_spotify_playlist(playlist_url)`
- Spotify API client (OAuth, playlist tracks, track metadata)
- Dedup by ISRC (via Deezer lookup if Spotify Dev Mode lacks ISRC — FR-100)
- Store Spotify track ID in `platform_song_ids`
- `POST /import/spotify` endpoint
- Smoke test T-200 passing
- **Definition of done:** TWICE playlist importable; all songs in `songs` table
  with Spotify ID in `platform_song_ids`; no duplicates

### Unit 6.2 — Apple Music Import
**Branch:** `feat/import-apple-music`  
**PRD reference:** FR-102  
**Estimated effort:** 2 sessions  
**Spike required:** S-08  
**Tests:** T-120, T-201

- `songs/service.py` — `import_from_apple_music_library()`
- MusicKit API client (user library, catalogue relationship for ISRC)
- Dedup with existing Spotify entries by ISRC
- Store Apple Music catalogue ID in `platform_song_ids`
- Smoke test T-201 passing
- **Definition of done:** Apple Music library importable; ISRC populated for
  catalogue songs; cross-platform dedup works (T-120)

### Unit 6.3 — YouTube Music Import
**Branch:** `feat/import-ytmusic`  
**PRD reference:** FR-101  
**Estimated effort:** 1–2 sessions  
**Spike required:** S-09  
**Tests:** T-121, T-202

- `songs/service.py` — `import_from_youtube_music_playlist(playlist_id)`
- `ytmusicapi` integration
- Heuristic matching (title + artist + duration) → Deezer ISRC lookup for
  verification (FR-101)
- Store YouTube Music video ID in `platform_song_ids`
- Smoke test T-202 passing (best effort — YTM matching is inherently fuzzy)
- **Definition of done:** YTM liked songs importable; matched to existing library
  entries where possible; unmatched entries created as new songs

---

## Phase 7 — Desktop Rankings Display

**⚠️ Spike dependency:** S-10 (Desktop web framework viability given no JS
experience). OQ-1 must be resolved first.

### Unit 7.1 — Rankings API Endpoints
**Branch:** `feat/rankings-api`  
**PRD reference:** FR-600, FR-601, FR-602  
**Estimated effort:** 1 session  
**Depends on:** Unit 3.1

- `rankings/repository.py` — `get_ranked_list(filters)`, `get_song_detail(song_id)`,
  `get_ranking_delta(snapshot_id)`
- `rankings/service.py` — filter/sort logic
- FastAPI routes:
  - `GET /rankings` — paginated ranked song list with filters
  - `GET /rankings/songs/{id}` — song detail with comparison history
  - `GET /rankings/history` — current vs. last snapshot delta

### Unit 7.2 — Desktop Web App (Rankings View)
**Branch:** `feat/web-rankings`  
**PRD reference:** FR-600, FR-602  
**Estimated effort:** 3–4 sessions (framework-dependent)  
**Spike required:** S-10  
**Depends on:** Unit 7.1

- Framework decision per OQ-1 (React or simpler alternative)
- Rankings table: rank, title, artist, rating, RD confidence label, language,
  track type
- Filter controls: language, track type, relationship type
- Current vs. last snapshot delta view (rank change indicators)

### Unit 7.3 — Desktop Multi-Song Comparison
**Branch:** `feat/web-comparison`  
**PRD reference:** FR-303, FR-301  
**Estimated effort:** 2–3 sessions  
**Depends on:** Unit 7.2

- Now-playing detection via Spotify Connect API polling (FR-301)
- Comparison widget showing last 3–5 songs, each with own 5-level row
- Each row submits independently to `POST /comparisons`
- Manual test: M-010

---

## Phase 8 — Playlist Export

### Unit 8.1 — Ranked Playlist Export
**Branch:** `feat/playlist-export`  
**PRD reference:** FR-500, FR-501, FR-502  
**Estimated effort:** 2 sessions  
**Depends on:** Unit 3.1, Unit 6.x (platform tokens available)  
**Tests:** T-203, T-204

- `playlists/service.py` — `generate_playlist(filter: PlaylistFilter, size: int)`,
  `export_to_spotify(playlist)`, `export_to_apple_music(playlist)`
- Filter support: language, track type, relationship type, performer, audio feature
  ranges
- `PlaylistRule` model — `POST /playlists/rules` to define auto-playlists
- T-203, T-204 smoke tests passing
- Manual test: M-011

### Unit 8.2 — Auto-Playlist Membership Updates
**Branch:** `feat/playlist-auto`  
**PRD reference:** FR-502, FR-503  
**Estimated effort:** 1 session  
**Depends on:** Unit 8.1, Unit 3.1

- Background job: after each comparison, evaluate `PlaylistRule` thresholds;
  update membership if songs cross threshold
- `GET /playlists/suggestions` — songs approaching threshold, flagged for review
  (FR-503)
- T-207 smoke test passing

---

## Phase 9 — Polish and Release

### Unit 9.1 — Ranking Snapshots
**Branch:** `feat/ranking-snapshots`  
**PRD reference:** FR-206, BR-009  
**Estimated effort:** 1 session  
**Tests:** T-140 through T-142

- `rankings/service.py` — `take_snapshot()` — captures full ranking state
- Triggered manually (API call) or via scheduled job
- Weekly/monthly schedule logic (BR-009)
- T-140 through T-142 passing

### Unit 9.2 — Data Export
**Branch:** `feat/data-export`  
**PRD reference:** NFR-032  
**Estimated effort:** 1 session

- `GET /export/songs` — all songs, ratings, comparisons, play events as JSON/CSV
- Manual test M-011

### Unit 9.3 — Release Readiness
**Branch:** `release/v3.0-rc`  
**PRD reference:** §8 Release Criteria  
**Estimated effort:** 1–2 sessions

- Run all Tier 1 and Tier 2 tests against Supabase staging
- Run full manual test checklist (M-001 through M-013)
- Verify no lost comparisons after 1 week of daily use testing
- Verify Supabase storage within free tier limits
- All release criteria in PRD §8 checked

---

## Spike Tests (Pre-Implementation)

These must complete before dependent units begin. Results documented in
`docs/02-requirements/spikes/S-{id}-{name}.md`.

| Spike | Question | Dependent Units |
|---|---|---|
| S-01 | Spotify Dev Mode: playlist read, ISRC availability in Feb 2026 | 6.1 |
| S-02 | Spotify Connect API: current track readable from desktop web | 7.3 |
| S-03 | Deezer ISRC endpoint: reliability, response format, K-pop coverage | 4.1 |
| S-04 | MusicBrainz TWICE discography coverage, artist credit format | 4.2 |
| S-05 | ReccoBeats: feature availability, batch format, rate limit | 4.3 |
| S-06 | Last.fm tag quality for TWICE tracks | 4.4 |
| S-07 | MPNowPlayingInfoCenter: reliability across Spotify/YTM/Apple Music | 5.2 |
| S-08 | MusicKit: ISRC availability on library (vs catalogue) songs | 6.2 |
| S-09 | ytmusicapi: stability, playlist read, matching accuracy | 6.3 |
| S-10 | Desktop web framework: viability given no JS experience | 7.2 |

---

## Revision History

| Date | Version | Changes | Author |
|---|---|---|---|
| 2026-02 | 0.1 | Initial draft, pre-spike validation | Enoch Ko |
