# MusicElo v3.0

Personal Music Ranking and Discovery System using the Glicko-2 algorithm for transparent, preference-based song ranking.

## Overview

MusicElo applies proven rating systems from competitive domains (chess, sports) to personal music preference quantification. Unlike opaque streaming platform algorithms, MusicElo provides transparent rankings based on accumulated pairwise comparisons and listening patterns.

**Key Innovation:** 90/10 passive/active learning — rank songs naturally while listening, not through tedious focused comparison sessions.

## Project Status

**Current Version:** v3.0 (in development)  
**Branch:** `v3-development`  
**Stage:** Design Foundation ✓ → Spike Validation (in progress)

### Version History

- **v1.0** — Original Spotify-based concept (not completed — blocked by Spotify API closure of new app registration in December 2025)
- **v2.0** ([main branch](../../tree/main)) — Pivoted to YouTube Music; Glicko-2 implementation with localhost UI (completed)
  - ✅ Proved Glicko-2 ranking works
  - ❌ UX failure: pairwise comparison felt like "work"
- **v3.0** (this branch) — Cross-platform companion app with 90/10 passive/active design (in development)

## Documentation

Comprehensive product development documentation available in [`docs/`](./docs):

- **[01-discovery/](./docs/01-discovery)** — Problem definition, user research, business case, stakeholder analysis ✅
- **[02-requirements/](./docs/02-requirements)** — PRD v0.2, API research, spike validation plan ✅
- **[03-design/](./docs/03-design)** — Database schema, backend architecture, test plan, implementation plan ✅
- **04-implementation/** — Implementation notes and decisions (coming soon)

See [docs/README.md](./docs/README.md) for detailed navigation and file descriptions.

## Problem Statement

**Core Challenge:** Users with extensive music libraries — particularly within single artists like TWICE's 300+ song discography — struggle to definitively answer "What is my favourite song?" when each song appeals in different ways.

**MusicElo's Solution:**

- Transparent Glicko-2 ranking based on accumulated comparisons
- 90/10 passive/active input balance (natural listening + easy preference indication)
- Historical tracking showing preference evolution over time
- Emotional journey playlist generation
- Visual memory metadata (TTT episodes, concerts, music videos)

## Technical Architecture (Planned)

**Approach:** Companion app — monitors native streaming apps (Spotify, YouTube Music, Apple Music) rather than playing music itself. Solves iOS background playback limitations.

**Platforms:**

- Deezer: Primary ISRC source (free, no auth required)
- Apple Music: Primary library import + metadata (ISRC, structured genres)
- Spotify: Secondary metadata source (Dev Mode restrictions apply as of Feb 2026)
- MusicBrainz: Canonical identifiers, artist relationships, K-pop credit resolution
- YouTube Music: Playback platform (YouTube Premium)

**Stack:**

- Backend: Python / FastAPI / PostgreSQL (Supabase)
- Mobile: Swift iOS companion app
- Desktop: Web app (framework TBD pending spike S-10)

**Algorithm:**

- Glicko-2 for global ranking (immediate updates, no rating period batching)
- Passive signals (skips, completions, replays) captured separately — never modify Glicko-2 scores
- Canonical alias system: same song across albums shares one Glicko-2 record
- Weekly snapshots (first 3 months), monthly thereafter

## Development Roadmap

### Current: Spike Validation

10 spike tests (S-01 to S-10) validating critical API and platform assumptions before implementation. See [spike-validation-plan.md](./docs/02-requirements/spikes/spike-validation-plan.md).

### Phase 0–3: Foundation + Core (Next)

- Repo setup, Alembic schema migration, FastAPI scaffold
- Glicko-2 engine (pure functions, TDD)
- Song library with CSV import and deduplication
- Comparison recording with undo/replay

### Phase 4–6: Integrations (Spike-gated)

- Metadata enrichment pipeline (Deezer, MusicBrainz, ReccoBeats, Last.fm)
- iOS companion app with MPNowPlayingInfoCenter
- Platform library import (Spotify, Apple Music, YouTube Music)

### Phase 7–9: Rankings + Polish

- Desktop rankings web app
- Playlist export to platforms
- Ranking snapshots, data export, release readiness

See [implementation-plan.md](./docs/03-design/implementation-plan.md) for full phase breakdown.

## Portfolio Context

This project serves as a comprehensive demonstration of:

- **Product Management:** End-to-end discovery, requirements, stakeholder analysis
- **Software Engineering:** Cross-platform architecture, API integration, database design
- **Data Science:** Statistical algorithm application (Glicko-2), preference modelling
- **AI-Assisted Development:** Effective collaboration with AI for development

Target audience: Potential employers for Data Science / Product Manager roles post-Masters (2028).

## Getting Started (v2.0)

See [main branch](../../tree/main) for v2.0 implementation instructions.

v3.0 development instructions coming soon.

## Licence

This project is licensed under the [MIT Licence](./LICENCE).

## Author

Enoch Ko — Master of Data Science (2025–2028), University of Melbourne

---

**Note:** This is a personal project developed as part of professional portfolio development. Not affiliated with TWICE, Spotify, YouTube Music, or any streaming platforms.
