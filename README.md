# MusicElo v3.0

Personal Music Ranking and Discovery System using the Glicko-2 algorithm for transparent, preference-based song ranking.

## Overview

MusicElo applies proven rating systems from competitive domains (chess, sports) to personal music preference quantification. Unlike opaque streaming platform algorithms, MusicElo provides transparent rankings based on accumulated pairwise comparisons and listening patterns.

**Key Innovation:** 90/10 passive/active learning — rank songs naturally while listening, not through tedious focused comparison sessions.

## Project Status

**Current Version:** v3.0 (in development)  
**Branch:** `v3-development`  
**Stage:** Discovery and Problem Definition ✓

### Version History

- **v1.0** — Original Spotify-based concept (not completed — blocked by Spotify API closure of new app registration in December 2025)
- **v2.0** ([main branch](../../tree/main)) — Pivoted to YouTube Music; Glicko-2 implementation with localhost UI (completed)
  - ✅ Proved Glicko-2 ranking works
  - ❌ UX failure: pairwise comparison felt like "work"
- **v3.0** (this branch) — Cross-platform with 90/10 passive/active design (in development)
  - Returns to Spotify for metadata (API access reopened, albeit with [stricter Development Mode limits](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security))
  - Retains YouTube Music for playback
  - Cross-platform: Desktop + mobile
  - 90% passive listening / 10% active comparison

## Documentation

Comprehensive product development documentation available in [`docs/`](./docs):

- **[01-discovery/](./docs/01-discovery)** — Problem definition, user research, business case, stakeholder analysis
- **02-requirements/** — Requirements specification (coming soon)
- **03-design/** — Technical architecture, UX design, data models (coming soon)
- **04-implementation/** — Implementation notes and decisions (coming soon)

See [docs/README.md](./docs/README.md) for detailed navigation.

## Problem Statement

**Core Challenge:** Users with extensive music libraries — particularly within single artists like TWICE's 300+ song discography — struggle to definitively answer "What is my favourite song?" when each song appeals in different ways.

**MusicElo's Solution:**

- Transparent Glicko-2 ranking based on accumulated comparisons
- 90/10 passive/active input balance (natural listening + easy preference indication)
- Historical tracking showing preference evolution over time
- Emotional journey playlist generation
- Visual memory metadata (TTT episodes, concerts, music videos)

## Technical Architecture (Planned)

**Platforms:**

- Spotify: Primary metadata source (ISRC, better library organisation)
- YouTube Music: Primary playback platform (YouTube Premium subscription)
- MusicBrainz: Supplemental canonical identifiers

**Cross-Platform:**

- Desktop (macOS/web): Viewing rankings + listening/ranking
- Mobile (iOS): Primary listening/ranking platform

**Algorithm:**

- Glicko-2 for global ranking
- Optional intra-playlist pools for promotion/relegation workflow
- Monthly historical snapshots for evolution tracking

## Development Roadmap

### Phase 1: Foundation (Weeks 1–6)

- [ ] API integration (Spotify, YouTube Music, MusicBrainz)
- [ ] Glicko-2 implementation with 5-level comparison system
- [ ] Cross-platform prototype (desktop + mobile)
- [ ] Canonical song identification and deduplication

### Phase 2: MVP (Months 2–4)

- [ ] 90/10 passive/active input interface
- [ ] Playlist generation with Spotify/YouTube Music export
- [ ] Monthly historical snapshot system
- [ ] Cross-platform feature parity

### Phase 3: Polish (Months 5–6)

- [ ] Documentation and code cleanup
- [ ] Portfolio case study
- [ ] GitHub publication
- [ ] Professional sharing (LinkedIn)

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
