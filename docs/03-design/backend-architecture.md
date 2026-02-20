# MusicElo v3.0 — Backend Architecture

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Document:** Backend Architecture  
**Stage:** Design Foundation  
**Version:** 0.1 (draft)  
**Author:** Enoch Ko  
**Date:** February 2026

---

## Purpose

This document defines the backend folder structure, module responsibilities, and
architectural conventions. It governs how implementation code is organised and serves
as a reference for AI-assisted development sessions alongside `CLAUDE.md`.

This document covers the Python/FastAPI backend only. iOS (Swift) and desktop web
are addressed in separate design documents.

---

## Guiding Principles

**1. Vertical slices with shared core.**
Code is organised by feature domain (songs, comparisons, rankings) rather than by
layer (models, services, routes). This bounds the context an AI agent needs for any
given task and minimises unintended cross-feature side effects.

**2. Pure core, thin layers.**
`core/glicko2.py` is a pure function library — no database, no FastAPI. It is the
only module with zero external dependencies. All other modules may depend on core;
core depends on nothing.

**3. Explicit over implicit.**
Explicit types (Pydantic models for all I/O), explicit error handling, explicit
interfaces between layers. No magic or dynamic attribute access.

**4. Async throughout.**
All database calls and external HTTP requests use `async`/`await`. No synchronous
blocking calls in request handlers.

**5. Tiered code rigour.**
The Glicko-2 engine and comparison recording are durable code — full test coverage,
written before implementation. Import scripts and enrichment utilities are disposable
code — lighter-touch testing, correctness verified empirically.

---

## Folder Structure

```
backend/
├── main.py                      # FastAPI app entry point; router registration
├── core/
│   ├── __init__.py
│   ├── config.py                # Settings (env vars, Supabase URL, API keys)
│   ├── database.py              # Async SQLAlchemy engine, session factory, Base
│   ├── exceptions.py            # Custom exception classes (NotFound, DuplicateISRC, etc.)
│   └── glicko2.py               # Pure Glicko-2 math — no DB, no FastAPI imports
│
├── songs/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy ORM models: Song, Album, Artist,
│   │                            #   SongArtist, ArtistGroup, SongRelationship,
│   │                            #   PlatformSongId, PlatformArtistId, PlatformAlbumId
│   ├── schemas.py               # Pydantic request/response models
│   ├── repository.py            # DB queries only — no business logic
│   ├── service.py               # Business logic: import, dedup, relationship mgmt
│   └── routes.py                # FastAPI endpoints
│
├── comparisons/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy: Comparison, PlayEvent, GlickoRating,
│   │                            #   GlickoParameters
│   ├── schemas.py               # Pydantic: ComparisonCreate, ComparisonResult,
│   │                            #   PlayEventCreate, UndoRequest
│   ├── repository.py            # DB queries: fetch comparison history, ratings
│   ├── service.py               # Business logic: record comparison, undo, replay,
│   │                            #   offline queue sync
│   └── routes.py                # FastAPI endpoints: POST /comparisons,
│                                #   POST /comparisons/{id}/undo, POST /play-events
│
├── rankings/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy: RankingSnapshot
│   ├── schemas.py               # Pydantic: RankingEntry, SnapshotSummary, RankDelta
│   ├── repository.py            # DB queries: ranked list, snapshot retrieval, delta calc
│   ├── service.py               # Business logic: snapshot trigger, threshold evaluation
│   └── routes.py                # FastAPI endpoints: GET /rankings, GET /rankings/history
│
├── playlists/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy: PlaylistRule
│   ├── schemas.py               # Pydantic: PlaylistFilter, PlaylistExportRequest
│   ├── repository.py            # DB queries: filter songs by rule, fetch rule state
│   ├── service.py               # Business logic: generate playlist, export to platform,
│   │                            #   auto-playlist membership updates
│   └── routes.py                # FastAPI endpoints: POST /playlists/export,
│                                #   GET /playlists/rules, PUT /playlists/rules/{id}
│
├── enrichment/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy: AudioFeatures, SongTag,
│   │                            #   SourceCacheTracks, SourceCacheAlbums,
│   │                            #   SourceCacheArtists, MergeLog
│   ├── schemas.py               # Pydantic: EnrichmentResult, AudioFeaturesUpdate
│   ├── cache.py                 # Raw API response caching to source_cache_* tables
│   ├── merge.py                 # Merge enrichment data into audio_features + song_tags
│   │                            #   with per-field source attribution
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── deezer.py            # Deezer API client (ISRC lookup, BPM, contributors)
│   │   ├── musicbrainz.py       # MusicBrainz API client (Recording MBID, artist
│   │   │                        #   credits, genres, rate limiter enforced here)
│   │   ├── reccobeats.py        # ReccoBeats API client (audio features via Spotify ID)
│   │   ├── lastfm.py            # Last.fm API client (community tags)
│   │   ├── acousticbrainz.py    # AcousticBrainz legacy client (pre-computed features)
│   │   └── musixmatch.py        # Musixmatch API client (genres, lyrics availability)
│   ├── pipeline.py              # Orchestrates enrichment: calls sources, handles
│   │                            #   partial failures, writes cache, calls merge
│   └── routes.py                # FastAPI endpoints: POST /enrich/{song_id},
│                                #   POST /enrich/batch
│
migrations/                      # Alembic migration files — generated by Alembic only
tests/
├── unit/                        # Pure logic, no DB
│   ├── test_glicko2_math.py
│   ├── test_comparison_logic.py
│   ├── test_undo_logic.py
│   └── test_song_relationships.py
├── integration/                 # Against test DB; external APIs mocked
│   ├── test_comparison_db.py
│   ├── test_undo_db.py
│   ├── test_alias_db.py
│   ├── test_enrichment_deezer.py
│   ├── test_enrichment_musicbrainz.py
│   ├── test_enrichment_reccobeats.py
│   ├── test_song_matching.py
│   ├── test_offline_queue.py
│   └── test_snapshots.py
└── smoke/                       # Lightweight end-to-end
    ├── test_import_spotify.py
    ├── test_import_apple_music.py
    ├── test_playlist_export.py
    └── test_snapshot_trigger.py
```

---

## Module Responsibilities

### `core/glicko2.py`

Pure functions only. No imports from any other MusicElo module.

```python
# Signature examples — implementation TBD
def initialise_rating() -> GlickoRating: ...
def map_outcome(level: ComparisonLevel) -> float: ...
def update_ratings(
    song_a: GlickoRating,
    song_b: GlickoRating,
    outcome: float,
    params: GlickoParameters
) -> tuple[GlickoRating, GlickoRating]: ...
def replay_comparisons(
    history: list[ComparisonRecord]
) -> dict[int, GlickoRating]: ...
```

`replay_comparisons` is used by the undo service to recalculate scores from history.
It must be deterministic — same input always produces same output.

### `songs/service.py`

Owns: song import, cross-platform deduplication, relationship management, artist
credit matching.

Key rules enforced here:
- Dedup by ISRC first; fall back to title+artist+duration heuristic
- On duplicate: merge metadata, preserve existing `glicko_ratings`
- On new canonical alias: create song row with `canonical_id` set; do NOT create
  `glicko_ratings` row
- On any other relationship type: create song row with `canonical_id=None`;
  create `glicko_ratings` row with defaults

### `comparisons/service.py`

Owns: comparison recording, undo, replay, play event recording, offline queue sync.

Key rules enforced here:
- Before recording a comparison, resolve alias → canonical song ID
- After recording, call `core/glicko2.py::update_ratings()` and persist result
- Undo: set `is_undone=True`, then call `replay_comparisons()` for affected songs,
  persist replayed ratings
- Play events: write to `play_events` table only — never touch `glicko_ratings`

### `enrichment/pipeline.py`

Orchestrates per-source enrichment. Partial failures are isolated — one source
failing does not block others.

Execution order (to maximise ISRC availability for downstream sources):
1. Deezer (ISRC confirmation + BPM)
2. MusicBrainz (Recording MBID, artist credits, genre tags)
3. ReccoBeats (audio features using Spotify ID from `platform_song_ids`)
4. Last.fm (community tags)
5. AcousticBrainz (legacy features using MBID)
6. Musixmatch (structured genres — Could Have)

Each source client: caches raw response verbatim → returns structured result →
pipeline calls `merge.py` to write to `audio_features` and `song_tags`.

### `enrichment/cache.py`

Single responsibility: write raw API JSON to `source_cache_tracks/albums/artists`
with `source`, `fetched_at`, and `raw_response` fields. Called by each source
client before returning. Failure to cache must NOT block the enrichment result
being returned — log the cache failure and proceed.

---

## Layer Interactions

```
routes.py
    └── calls service.py (business logic)
            ├── calls repository.py (DB queries)
            ├── calls core/glicko2.py (pure math)
            └── calls enrichment/pipeline.py (enrichment orchestration)
                    └── calls enrichment/sources/*.py (API clients)
                            └── calls enrichment/cache.py (raw response storage)
```

Routes never call repositories directly. Services never construct HTTP responses.
Repositories contain only DB queries — no business logic.

---

## Dependency Rules

| Module | May import from | Must NOT import from |
|---|---|---|
| `core/` | Standard library only | Any other MusicElo module |
| `*/repository.py` | `core/database.py`, `*/models.py` | `*/service.py`, `*/routes.py` |
| `*/service.py` | `core/`, `*/repository.py`, `enrichment/` | `*/routes.py` |
| `*/routes.py` | `*/service.py`, `*/schemas.py` | `*/repository.py`, `core/glicko2.py` |
| `enrichment/sources/` | `core/config.py`, `enrichment/cache.py` | Any feature slice |

---

## Schema Migrations

All schema changes go through Alembic.

```bash
# Generate migration after ORM model change
alembic revision --autogenerate -m "description_of_change"

# Review generated file before applying
# Apply to local DB
alembic upgrade head
```

**Breaking migrations** — changes that require data transformation or drop columns —
must be flagged explicitly in the PR/commit message as `BREAKING MIGRATION` and
reviewed before applying to Supabase staging.

Never use `alembic --autogenerate` output without reviewing the generated file.
Auto-generated migrations sometimes drop columns it shouldn't.

---

## Environment Configuration

All configuration via environment variables, loaded through `core/config.py`
(Pydantic `BaseSettings`).

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `SPOTIFY_CLIENT_ID` | Spotify API |
| `SPOTIFY_CLIENT_SECRET` | Spotify API |
| `APPLE_MUSIC_KEY` | MusicKit |
| `LASTFM_API_KEY` | Last.fm |
| `MUSIXMATCH_API_KEY` | Musixmatch |
| `MUSICBRAINZ_USER_AGENT` | Required header (format: `AppName/Version contact@email`) |
| `ENVIRONMENT` | `local` / `staging` / `production` |

No API keys are hardcoded or committed. `.env` is gitignored.

---

## Decisions and Rationale

| Decision | Alternatives Considered | Rationale |
|---|---|---|
| Vertical slice over layer-based | models/, services/, routes/ at root | Bounds AI agent context per task; feature-complete slices easier to reason about and test in isolation |
| Pure `core/glicko2.py` | Embed math in `comparisons/service.py` | Enables unit testing without DB; makes determinism provable; reusable for replay logic |
| Replay-based undo over delta reversal | Apply inverse Glicko-2 delta | Glicko-2 is non-linear; delta reversal is imprecise. Replay is exact and auditable |
| Enrichment as separate slice | Embed in `songs/` | Enrichment pipeline grows in complexity (6 sources, rate limiting, caching); isolation prevents contaminating song import logic |
| Per-source files in `enrichment/sources/` | Single monolithic enrichment client | Each source has different auth, rate limits, and failure modes; isolation makes partial failure handling clean |

---

## Open Questions (Architecture-Specific)

These are in addition to the PRD §9 open questions.

| # | Question | Impact |
|---|---|---|
| A-01 | Desktop web framework (React vs. simpler alternative) — no JS experience | Affects `web/` structure; backend API design is not affected |
| A-02 | WebSocket vs polling for desktop now-playing sync | Affects `rankings/routes.py` and frontend design |
| A-03 | iOS offline queue storage mechanism (Core Data vs SQLite vs UserDefaults) | iOS only; does not affect backend API contract |

---

## Revision History

| Date | Version | Changes | Author |
|---|---|---|---|
| 2026-02 | 0.1 | Initial draft | Enoch Ko |
