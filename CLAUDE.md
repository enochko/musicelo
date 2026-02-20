# CLAUDE.md — MusicElo v3.0

**Repo:** musicelo-v3  
**Last updated:** February 2026  
**Maintained by:** Enoch Ko

---

## Project Purpose

Personal music ranking system using the Glicko-2 algorithm. Single user. MusicElo is a
**companion app** that monitors native streaming apps (Spotify, YouTube Music, Apple Music)
and captures pairwise song comparisons. It does NOT play music. Music plays in the native
app; MusicElo reads what is playing and presents a comparison interface.

Portfolio piece demonstrating end-to-end product development (PM, engineering, data
science, AI-assisted development).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL (Supabase free tier, 500MB limit) |
| iOS | Swift (native, minimal — comparison widget + now-playing sync only) |
| Desktop | Web app (framework TBD — see OQ-1 in PRD §9) |
| Key libs | glicko2 (Python), httpx (async API calls), pydantic v2, pytest |

---

## Repository Structure

```
/
├── CLAUDE.md                    ← This file
├── backend/
│   ├── core/                    ← Shared: DB session, pure Glicko-2 math, config, exceptions
│   ├── songs/                   ← models, repository, service, routes
│   ├── comparisons/             ← models, repository, service, routes
│   ├── rankings/                ← models, repository, service, routes
│   ├── playlists/               ← models, repository, service, routes
│   └── enrichment/              ← Metadata pipeline per source (Deezer, MusicBrainz, etc.)
├── ios/                         ← Swift companion app
├── web/                         ← Desktop web app
├── migrations/                  ← Alembic migration files only — never edit manually
├── tests/
│   ├── unit/                    ← Pure logic, no DB (Glicko-2 math, business rules)
│   ├── integration/             ← Against test DB (repositories, API clients)
│   └── smoke/                   ← Lightweight end-to-end checks
└── docs/
    ├── 01-discovery/
    ├── 02-requirements/         ← PRD lives here
    |   └── spikes/              ← Spike plans and S-01 through S-10 results
    └── 03-design/               ← Architecture, test plan, wireframes
```

---

## Critical Architectural Rules — DO NOT VIOLATE

### Glicko-2 Engine

- **Passive signals (play events, skips, completions) NEVER modify `glicko_ratings`.**
  Only explicit user comparison inputs trigger score updates. This is BR-008 and is
  architecturally fundamental — violating it silently corrupts the entire ranking system.
- Glicko-2 updates are **immediate** — no rating period batching. Process each comparison
  as it arrives.
- The pure math engine lives in `backend/core/glicko2.py` with **no database dependencies**.
  It accepts ratings in, returns updated ratings out. All other modules depend on it;
  it depends on nothing.
- Always reference `canonical_id` when writing to `glicko_ratings`. Never write to
  `glicko_ratings` using an alias song's ID.

### Comparison Undo and Replay

- Undo = **soft-delete** (`is_undone = true`) on the `comparisons` table. Never hard-delete
  a comparison record.
- After undo, **replay** all non-undone comparisons for affected songs in chronological
  order to recalculate current scores. Do not apply a delta or reverse calculation.
- Replay must produce identical output to the original forward calculation.

### Song Relationships and Canonical Aliases

- **Canonical aliases** (same recording, different albums): share ONE `glicko_ratings`
  record. The alias song row has `canonical_id` pointing to the rated song.
- **All other relationship types** (translation, remix, live, acoustic, solo/sub-unit):
  maintain **separate** `glicko_ratings` records.
- Comparisons always use the canonical song's ID, never an alias ID.

### Data Integrity

- ISRC is the primary cross-platform identifier. **Cache aggressively. Never overwrite
  with null.** Once obtained, treat as permanent (BR-010).
- Raw API responses are always cached verbatim in `source_cache_tracks`,
  `source_cache_albums`, `source_cache_artists` with timestamps, regardless of parse
  success. This protects against service disappearance (BR-012).
- **Schema migrations require an Alembic file.** Never ALTER TABLE manually, via raw SQL
  outside migrations, or via ORM tricks. Flag any proposed schema change explicitly.
- `platform_song_ids` stores every platform's native ID. Prefer ID-based matching over
  name matching for cross-platform deduplication (BR-011).
- Duplicate imports (same ISRC) must merge metadata and **preserve** existing
  `glicko_ratings`. Never overwrite scores on re-import.

### Privacy

- GPS coordinates never leave the iOS device. Only zone names (e.g., "Home", "Office")
  are transmitted to the backend. No precise location data in any cloud table, ever.

---

## Business Rules Quick Reference

These are encoded in the PRD (§5) and must be respected in all generated code.

| Rule | Summary |
|---|---|
| BR-001 | New songs init: rating=1500, RD=350, volatility=0.06 |
| BR-002 | Alias songs share `glicko_ratings` via `canonical_id` |
| BR-003 | All other relationship types have separate `glicko_ratings` |
| BR-004 | Comparisons reference canonical song ID only |
| BR-005 | Glicko-2 updates are immediate (no batching) |
| BR-006 | Undo = soft-delete (`is_undone=true`) + full score replay |
| BR-007 | No user interaction during playback = no Glicko-2 data recorded |
| BR-008 | Passive signals (play events) never trigger Glicko-2 changes |
| BR-009 | Snapshots weekly (first 3 months), monthly thereafter |
| BR-010 | ISRCs are permanent once obtained — never overwrite with null |
| BR-011 | Store platform artist IDs, not just names |
| BR-012 | Cache raw API responses verbatim with timestamps |

---

## API Rate Limits — Always Respect

| Source | Limit | Notes |
|---|---|---|
| MusicBrainz | 1 req/sec | Mandatory descriptive `User-Agent` header required |
| ReccoBeats | ~0.5s between calls | Batch max ~5 Spotify IDs |
| Musixmatch | 2,000 calls/day | Free tier hard limit |
| Last.fm | ~5 req/sec | Free API key |
| Deezer | Unspecified | Cache aggressively; mostly one-time lookups |

---

## Current Development State

- **Stage:** Spike validation in progress (S-01 through S-10)
- **No implementation code exists yet**
- Requirements definition complete — see `docs/02-requirements/musicelo-v3-prd-v1_0.md`
- Design phase (architecture, wireframes, test plan) in progress

**Before writing any API integration code**, check `docs/02-requirements/spikes/` for validated results.
Do not trust streaming API documentation without spike confirmation — see PRD §6
(Assumptions) and §9 (Open Questions and Technical Risks).

---

## DO

- Write tests for Glicko-2 engine and comparison recording **before** implementing the feature
- Use `async`/`await` throughout FastAPI routes and database calls
- Check `docs/02-requirements/spikes/` before implementing any external API integration
- Check PRD §9 (Open Questions) before making assumptions about API behaviour
- Flag any proposed schema change explicitly — label it "BREAKING MIGRATION" if it
  affects existing data or column names
- Keep `core/glicko2.py` free of database and FastAPI imports at all times

## DON'T

- Don't add audio playback — MusicElo is a companion app only
- Don't modify `glicko_ratings` from any trigger, background job, or passive signal
- Don't hard-delete from `comparisons`, `play_events`, or `glicko_ratings`
- Don't denormalize songs/artists/albums — the M:N relationship via `song_artists` is
  intentional and must be preserved
- Don't store GPS coordinates anywhere in the backend or any API payload
- Don't skip Alembic for schema changes, even trivial ones
- Don't trust external API documentation without checking spike test results first
- Don't apply Glicko-2 delta calculations for undo — always replay from history

---

## Updating This File

Update CLAUDE.md when:
- Spike tests confirm or change API assumptions (add confirmed endpoint details)
- New external dependencies are added
- Architectural decisions change
- New DO/DON'T rules emerge from implementation experience

Do not let this file exceed ~300 lines.
