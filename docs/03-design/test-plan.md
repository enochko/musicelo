# MusicElo v3.0 — Test Plan

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Document:** Test Plan  
**Stage:** Design Foundation  
**Version:** 0.1 (draft — pre-implementation)  
**Author:** Enoch Ko  
**Date:** February 2026

---

## Purpose and Scope

This document defines what to test, at what rigour, and in what order. It is a companion
to the PRD (requirements) and architecture doc (structure). Tests are the primary mechanism
for keeping AI-generated code honest — AI agents will find ways to make tests pass
incorrectly, so human review of test logic is as important as human review of
implementation code.

**In scope:** Backend Python (Glicko-2 engine, comparison logic, enrichment pipeline,
playlist generation, API routes). iOS and desktop web are manual-only for v3.0.

**Not in scope:** Full UI/UX testing, load testing, cross-device compatibility testing.

---

## Tiered Approach

Code is not equally critical. Test rigour matches risk and expected lifespan.

| Tier | Code Type | Approach | When Written |
|---|---|---|---|
| 1 — Durable | Glicko-2 engine, comparison recording, undo/replay, canonical alias logic | Full unit + integration tests, written before implementation (TDD) | Before feature branch |
| 2 — Integration | API enrichment pipeline, cross-platform matching, offline queue sync | Integration tests against test DB, written alongside implementation | During feature branch |
| 3 — Smoke | Import scripts, playlist export, snapshot capture | Lightweight end-to-end checks | After implementation |
| Manual only | CarPlay one-handed interaction, now-playing latency, mobile comparison timing | Documented manual test checklist | Pre-release |

---

## Tier 1 — Durable Code (Write Before Implementing)

These must pass before any comparison-related code is merged. Write the test first,
then implement until it passes.

### 1.1 Glicko-2 Pure Math Engine (`core/glicko2.py`)

All tests in `tests/unit/test_glicko2_math.py`. No database, no FastAPI — pure function
calls only.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-001 | Correct μ update — strong win | Call update with outcome=1.0, known μ/RD/σ inputs, verify μ increases by expected amount per Glicko-2 formula | Output μ matches hand-calculated reference value (±0.01 tolerance) |
| T-002 | Correct μ update — strong loss | As above with outcome=0.0 | Output μ decreases by expected amount |
| T-003 | Correct μ update — draw | outcome=0.5, equal-rated opponents | Both μ values unchanged (draw between equal players) |
| T-004 | Correct μ update — slight win (0.75) | outcome=0.75 | μ increases, less than T-001 |
| T-005 | Correct μ update — slight loss (0.25) | outcome=0.25 | μ decreases, less than T-002 |
| T-006 | RD decreases after comparison | New song (RD=350) vs established song | Winner and loser RD both decrease from pre-comparison values |
| T-007 | Volatility (σ) update within bounds | Any comparison with default τ=0.5 | σ remains positive and does not diverge |
| T-008 | High-RD song has larger score swing | Compare: new song (RD=350) vs established song. Repeat with established vs established | New song's μ changes more per comparison than established song |
| T-009 | Default initialisation values | Call initialise_song() | Returns rating=1500, RD=350, volatility=0.06 |
| T-010 | Outcome mapping values are correct | Call map_outcome('strong_win'), map_outcome('slight_win'), etc. | Returns 1.0, 0.75, 0.5, 0.25, 0.0 respectively |
| T-011 | System constant τ is configurable | Pass τ=0.3 to update function | Volatility change differs from default τ=0.5 result |
| T-012 | Function is pure — no side effects | Call update twice with same inputs | Returns identical output both times |
| T-013 | Both songs updated in single call | Single comparison call | Returns updated ratings for both song_a and song_b |

### 1.2 Comparison Recording (`comparisons/`)

Tests in `tests/unit/test_comparison_logic.py` and `tests/integration/test_comparison_db.py`.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-020 | Comparison stored with full audit fields | Submit comparison via service layer | Row in `comparisons` contains: both song IDs, outcome, μ/RD/σ before and after for both songs, timestamp, source, context fields |
| T-021 | Glicko-2 scores updated after comparison | Submit comparison | `glicko_ratings` rows for both songs reflect updated μ, RD, σ |
| T-022 | Response time recorded | Submit comparison with response_time_ms field | Field stored in `comparisons` row |
| T-023 | Source field stored correctly | Submit comparison from 'mobile_passive' source | `source` field in `comparisons` = 'mobile_passive' |
| T-024 | Skip/dismiss records no comparison data | Call skip on a song pair | No row inserted in `comparisons`, no change to `glicko_ratings` |
| T-025 | Play event records no Glicko-2 change | Record a play event | `glicko_ratings` unchanged; row in `play_events` created |
| T-026 | Play event with null context fields accepted | Record play event with no location, no CarPlay flag | Row created with null context fields, no error |
| T-027 | Comparison source context captured | Submit comparison with CarPlay=true, location_zone='Car' | Both fields stored in `comparisons` row |

### 1.3 Undo and Replay Logic (`comparisons/`)

Tests in `tests/unit/test_undo_logic.py` and `tests/integration/test_undo_db.py`.
These are the highest-risk tests — replay logic is complex and easy to get subtly wrong.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-030 | Undo soft-deletes comparison | Submit comparison, then undo | `comparisons` row has `is_undone=true`; row is NOT deleted |
| T-031 | Undo triggers replay | Undo a comparison between Song A and Song B | `glicko_ratings` for both songs are recalculated |
| T-032 | Replay produces same result as original | Song A vs B: record 3 comparisons, replay from scratch | Replayed scores match forward-calculated scores exactly |
| T-033 | Undone comparison excluded from replay | Record comparisons 1, 2, 3. Undo comparison 2. Replay. | Final scores match forward calculation of comparisons 1 and 3 only |
| T-034 | Undo of first comparison restores defaults | New song has one comparison, then undo | Song's μ, RD, σ return to 1500, 350, 0.06 |
| T-035 | Multiple undos in sequence | Record 5 comparisons, undo 3 and 4 | Scores reflect only comparisons 1, 2, 5 |
| T-036 | Re-vote replaces original (not stacked) | Submit comparison, re-vote with different outcome | Only the re-vote comparison is `is_undone=false`; original is `is_undone=true` |
| T-037 | Re-vote produces different final score | Same pair, strong win vs strong loss | Different μ outcomes confirm re-vote is applied correctly |
| T-038 | Undo within 10-second window allowed | Undo at t+9s | Undo succeeds |
| T-039 | Undo rejected outside 10-second window | Undo at t+11s | Returns error; `is_undone` unchanged |

### 1.4 Canonical Alias and Relationship Logic (`songs/`)

Tests in `tests/unit/test_song_relationships.py` and `tests/integration/test_alias_db.py`.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-040 | Alias song shares glicko_ratings with canonical | Create canonical + alias pair | Alias `canonical_id` points to canonical song; only one `glicko_ratings` row exists |
| T-041 | Comparison on alias uses canonical ID | Submit comparison using alias song ID | `comparisons` row records canonical song ID; `glicko_ratings` for canonical updated |
| T-042 | Comparison on alias updates canonical score | Submit comparison using alias ID | Canonical song's μ changes; no second `glicko_ratings` row created |
| T-043 | Translation pair has separate glicko_ratings | Create Korean original + Japanese translation pair | Two separate `glicko_ratings` rows exist |
| T-044 | Remix has separate glicko_ratings | Create original + instrumental remix | Two separate `glicko_ratings` rows exist |
| T-045 | Live recording has separate glicko_ratings | Create studio + live recording pair | Two separate `glicko_ratings` rows exist |
| T-046 | Solo version has separate glicko_ratings | Create group version + solo member version | Two separate `glicko_ratings` rows exist |
| T-047 | New song initialises with defaults | Import new song | `glicko_ratings` row created with rating=1500, RD=350, volatility=0.06 |
| T-048 | Re-import preserves existing glicko_ratings | Import song, compare it, re-import same song by ISRC | `glicko_ratings` unchanged after second import |

---

## Tier 2 — Integration Tests (Write Alongside Implementation)

### 2.1 External API Clients (`enrichment/`)

Tests in `tests/integration/test_enrichment_*.py`. These run against real endpoints in
development, mocked in CI.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-100 | Deezer ISRC lookup returns track data | GET `/track/isrc:{valid_ISRC}` | Returns BPM, contributor data, ISRC confirmation |
| T-101 | Deezer ISRC lookup — no result | GET `/track/isrc:{invalid_ISRC}` | Returns graceful empty result; no exception; no DB write for missing field |
| T-102 | Deezer response cached verbatim | Successful Deezer lookup | Raw JSON stored in `source_cache_tracks` with timestamp |
| T-103 | Deezer failed response still cached | Failed/empty Deezer lookup | Failure response or null still written to cache with timestamp |
| T-104 | MusicBrainz rate limiter enforces 1 req/sec | Submit 5 sequential requests | Elapsed time ≥ 4 seconds; no 429 response received |
| T-105 | MusicBrainz User-Agent header present | Any MusicBrainz request | Request headers contain descriptive User-Agent string |
| T-106 | MusicBrainz artist credit resolution | Lookup MBID for a known TWICE track | Returns artist-credits including group and member credits |
| T-107 | MusicBrainz response cached verbatim | Successful lookup | Raw JSON stored in `source_cache_tracks` |
| T-108 | ReccoBeats batch size respected | Submit 6 Spotify IDs | Sent in two batches (5 + 1), not as single 6-item request |
| T-109 | ReccoBeats rate limit delay enforced | Submit 2 requests | Elapsed time ≥ 0.5 seconds |
| T-110 | Last.fm tag lookup returns weighted tags | GET `track.getTopTags` for known track | Returns list of tags with count values |
| T-111 | All enrichment data merged into audio_features | Complete enrichment run for one track | `audio_features` row populated with source attribution for each field |
| T-112 | Enrichment partial failure does not block other sources | Deezer returns error; other sources proceed | MusicBrainz, ReccoBeats, Last.fm data still written; only Deezer fields null |

### 2.2 Cross-Platform Song Matching (`songs/`)

Tests in `tests/integration/test_song_matching.py`.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-120 | ISRC match deduplicates across platforms | Import song from Spotify; import same song from Apple Music (same ISRC) | Single `songs` row; both platform IDs in `platform_song_ids` |
| T-121 | Heuristic match deduplicates when ISRC absent | Import song from YouTube Music (no ISRC); Deezer lookup confirms ISRC; matches Spotify entry | Single `songs` row after ISRC resolution |
| T-122 | Artist ID stored for each platform | Import artist from Spotify and Apple Music | `platform_artist_ids` has rows for both platforms |
| T-123 | MusicBrainz group/solo artist credit mismatch resolved | Lookup track credited to TWICE on Spotify, credited to Nayeon on MusicBrainz | `song_artists` contains both TWICE (primary) and Nayeon (performer) with correct roles |
| T-124 | Duplicate import does not create second song row | Import same ISRC twice | One `songs` row; metadata updated; `glicko_ratings` preserved |
| T-125 | Platform IDs stored on import | Import from Spotify | `platform_song_ids` row created with platform='spotify', native_id=Spotify track ID |

### 2.3 Offline Vote Queue (`comparisons/`)

Tests in `tests/integration/test_offline_queue.py`.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-130 | Vote queued when offline | Submit comparison while backend unreachable | Vote stored locally; not lost |
| T-131 | Queued votes sync in FIFO order when reconnected | Queue 3 votes offline; reconnect | Votes processed in submission order; timestamps preserved |
| T-132 | No duplicate processing of queued votes | Sync once, attempt second sync | Second sync produces no duplicate `comparisons` rows |
| T-133 | Queued votes survive app crash | Queue vote; simulate crash; relaunch | Vote still in queue; syncs on reconnect |

### 2.4 Ranking Snapshots (`rankings/`)

Tests in `tests/integration/test_snapshots.py`.

| # | Test | Description | Pass Condition |
|---|---|---|---|
| T-140 | Snapshot captures all songs with full Glicko-2 state | Trigger snapshot with 10 songs in library | `ranking_snapshots` row contains all 10 songs with μ, RD, σ, comparison count |
| T-141 | Snapshot is point-in-time (not affected by later comparisons) | Take snapshot; submit comparison; query snapshot | Snapshot values unchanged |
| T-142 | Current vs snapshot delta queryable | Take snapshot; change rankings; query delta | Returns rank position change for each song |

---

## Tier 3 — Smoke Tests (Write After Implementation)

| # | Test | Description |
|---|---|---|
| T-200 | Spotify import end-to-end | Import a playlist; confirm songs, platform IDs, and metadata rows created |
| T-201 | Apple Music import end-to-end | Import library; confirm ISRC populated for catalogue songs |
| T-202 | YouTube Music import end-to-end | Import liked songs; confirm heuristic matching attempted |
| T-203 | Ranked playlist export | Generate top-50 playlist; confirm correct songs in rating order |
| T-204 | Category-filtered export | Filter Korean title tracks; confirm only matching songs included |
| T-205 | Glicko-2 parameter change history | Update τ; confirm old parameter set closed, new set created |
| T-206 | Weekly snapshot trigger | Simulate week boundary; confirm snapshot created |
| T-207 | Playlist rule auto-update | Song crosses threshold; confirm playlist membership updated |

---

## Manual Test Checklist (Pre-Release)

These cannot be automated and must be checked manually before v3.0 release.

| # | Test | Success Criterion |
|---|---|---|
| M-001 | CarPlay one-handed operation | All comparison buttons reachable with right thumb, phone mounted |
| M-002 | Late vote button (first 5–10 seconds) | Button visible and full-width; tapping pauses current song correctly |
| M-003 | Pause-to-vote button (last 10 seconds) | Button visible; playlist does not advance after tap until vote/skip |
| M-004 | 10-second undo window on mobile | Undo available and functional immediately after vote |
| M-005 | Now-playing detection — Spotify | Song change in Spotify reflects in MusicElo within 3 seconds |
| M-006 | Now-playing detection — YouTube Music | As above |
| M-007 | Now-playing detection — Apple Music | As above |
| M-008 | Offline vote queue | Vote while in Airplane Mode; reconnect; confirm sync |
| M-009 | Comparison timing phases transition correctly | Three phases visible at correct timestamps; no phase displayed outside its window |
| M-010 | Desktop multi-song comparison | Last 3–5 songs each show comparison row; unvoted rows produce no data |
| M-011 | Data export (JSON/CSV) | Full export completes; contains all songs, comparisons, play events |
| M-012 | Page load time | Rankings page loads in <2 seconds on desktop |
| M-013 | Comparison response time | Tap to visual confirmation <200ms on iPhone |

---

## Test Environment

| Environment | Purpose | DB |
|---|---|---|
| Local (pytest) | Unit tests, integration tests during development | Local PostgreSQL or SQLite in-memory |
| CI (GitHub Actions) | All Tier 1 and Tier 2 tests on every push | Ephemeral PostgreSQL |
| Staging (Supabase) | Smoke tests, pre-release validation | Supabase staging project |
| Production (Supabase) | No automated tests run here | Live data |

External API calls are **mocked in CI** using `pytest-httpx` or equivalent. Real API
calls run locally only, against actual endpoints, using spike test credentials.

---

## Revision History

| Date | Version | Changes | Author |
|---|---|---|---|
| 2026-02 | 0.1 | Initial draft, pre-implementation | Enoch Ko |
