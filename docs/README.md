# MusicElo v3.0 Documentation

Comprehensive product development documentation following structured software engineering and product management practices.

## Documentation Structure

### 01-discovery/

**Discovery and Problem Definition Phase**

Foundation documents that define the problem space, user needs, and strategic rationale.

- **[problem-statement.md](./01-discovery/problem-statement.md)** — Core problem definition, background, success criteria, technical decisions
- **[user-research-findings.md](./01-discovery/user-research-findings.md)** — User profile, pain points, behavioural patterns, design implications
- **[business-case.md](./01-discovery/business-case.md)** — Strategic alignment, ROI analysis, risks, investment requirements
- **[stakeholder-analysis.md](./01-discovery/stakeholder-analysis.md)** — Stakeholder mapping, engagement strategy, success metrics

**Status:** ✅ Complete and approved

### 02-requirements/

**Requirements Specification Phase**

Functional and non-functional requirements, API research, and spike validation planning.

- **[prd.md](./02-requirements/prd.md)** — Product Requirements Document v0.2. Functional requirements, business rules, data model summary, non-functional requirements
- **[prd-review-notes.md](./02-requirements/prd-review-notes.md)** — Decision log documenting 10 conflicts resolved between PRD v0.1, API research, and schema design during v0.2 revision
- **[api-research-report.md](./02-requirements/api-research-report.md)** — Comprehensive survey of 10 music metadata APIs (Spotify, YouTube Music, Apple Music, MusicBrainz, Deezer, Last.fm, AcousticBrainz, Musixmatch, ReccoBeats, Essentia/librosa). Covers access restrictions, ISRC availability, artist credit mismatches, and audio feature alternatives post-Spotify restrictions
- **[api-fields-catalogue.json](./02-requirements/api-fields-catalogue.json)** — Machine-readable companion to the API research report. Field listings per service, audio feature availability matrix, ISRC availability, and artist credit matching strategy
- **[spikes/spike-validation-plan.md](./02-requirements/spikes/spike-validation-plan.md)** — 10 spike tests (S-01 to S-10) validating critical API and platform assumptions before implementation. Covers Spotify Dev Mode restrictions, Deezer ISRC, MusicBrainz K-pop coverage, iOS MPNowPlayingInfoCenter, and more
- **[spikes/spike-github-guide.md](./02-requirements/spikes/spike-github-guide.md)** — Git workflow guide for spike branches: naming conventions, branch lifecycle, result documentation, and PR process

**Status:** ✅ Requirements complete — spike validation in progress

### 03-design/

**Design and Architecture Phase**

Technical architecture, system design, and database specifications.

- **[database-schema-design.md](./03-design/database-schema-design.md)** — Narrative design document for the 22-table PostgreSQL schema. Covers design decisions, normalisation rationale, Glicko-2 integration, metadata caching strategy, and storage estimates
- **[schema.sql](./03-design/schema.sql)** — Full PostgreSQL DDL. All 22 tables, indexes, constraints, foreign keys, and seed data for `glicko_parameters`
- **[erd.mermaid](./03-design/erd.mermaid)** — Entity relationship diagram in Mermaid syntax. Renders in GitHub and VS Code with the Mermaid Preview extension
- **[backend-architecture.md](./03-design/backend-architecture.md)** — Python backend folder structure (vertical slice architecture), module responsibilities, layer interaction rules, and architectural decision rationale
- **[test-plan.md](./03-design/test-plan.md)** — Tiered testing strategy. Tier 1 (durable: Glicko-2, comparisons, undo/replay, canonical aliases), Tier 2 (integration: enrichment, platform matching), Tier 3 (smoke: imports, exports). Prioritised test list with test IDs
- **[implementation-plan.md](./03-design/implementation-plan.md)** — Phased implementation plan (Phases 0–9) broken into small vertical-slice units. Spike-gated phases for API integrations and iOS companion app

**Status:** ✅ Design foundation complete — pending spike validation results before Phase 4+

### 04-implementation/

**Implementation Documentation** (Coming soon)

Development notes, decisions, and implementation guidance.

**Planned contents:** Implementation decisions and rationale, code structure and organisation, API integration notes, testing strategy, deployment procedures.

**Status:** 🔜 Not started — begins after spike validation

## Documentation Principles

### Why This Structure?

This documentation follows professional product development practices to:

1. **Demonstrate product thinking** — Structured discovery → requirements → design → implementation
2. **Maintain decision history** — Clear rationale for all major decisions
3. **Enable portfolio sharing** — Professional-quality artefacts suitable for job applications
4. **Support future development** — Clear context for resuming work after breaks

### Version Control

Documents are versioned within Git commits. Major updates increment the document version. Revision history is tracked within each document.

### Australian English

All documentation uses Australian English spelling conventions (colour, visualise, organise, etc.).

## Key Decisions Summary

Quick reference for major architectural decisions. See [prd-review-notes.md](./02-requirements/prd-review-notes.md) for full decision rationale.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Platform approach** | Companion app (monitor native players) | iOS background playback limitations make a standalone player unworkable |
| **Primary ISRC source** | Deezer (free, no auth) | Spotify removed ISRC from Dev Mode in Feb 2026; Deezer fills the gap freely |
| **Apple Music priority** | Must Have (elevated from Could Have) | Provides ISRC, structured genres, full library access; essential given Spotify restrictions |
| **Passive/active ratio** | 90% passive / 10% active | Avoids v2 UX failure where focused comparison felt like "work" |
| **Passive signals → Glicko-2** | Never (passive signals excluded) | Preserves ranking integrity; passive data used for context only |
| **Deduplication** | Canonical (earliest release) + aliases sharing one Glicko-2 record | Same song across multiple albums shares one rank; translations/remixes ranked separately |
| **Undo mechanism** | Soft-delete + full replay | Glicko-2 is path-dependent; delta reversal imprecise; replay is exact and auditable |
| **Ranking snapshots** | Weekly (first 3 months) then monthly | High early volatility makes weekly snapshots meaningful during initial ranking period |
| **Location privacy** | GPS → zone conversion on-device | Raw coordinates never leave iOS |
| **Backend architecture** | Vertical slices | Bounds AI agent context per feature; easier to test in isolation |

## Navigation Tips

### For Portfolio Reviewers

Start with:

1. [Problem Statement](./01-discovery/problem-statement.md) — Understand the core challenge
2. [Business Case](./01-discovery/business-case.md) — See strategic rationale and portfolio context
3. [PRD](./02-requirements/prd.md) — Full requirements and business rules
4. [Backend Architecture](./03-design/backend-architecture.md) — Technical design decisions

### For Technical Implementation

Start with:

1. [CLAUDE.md](../CLAUDE.md) — AI agent context file; critical rules and architecture summary
2. [Schema SQL](./03-design/schema.sql) — Database DDL
3. [Backend Architecture](./03-design/backend-architecture.md) — Folder structure and module responsibilities
4. [Implementation Plan](./03-design/implementation-plan.md) — Phased build sequence

### For Understanding v2 → v3 Evolution

See:

- [Problem Statement — Background section](./01-discovery/problem-statement.md#background) — Origin story
- [User Research — v2 UX Failures](./01-discovery/user-research-findings.md#4-musicelo-v2-ux-failures) — What went wrong and lessons learned

## Changelog

### v0.3 (2026-02-21)

- Added 02-requirements/ phase: PRD v0.2, PRD review notes, API research report, fields catalogue, spike validation plan, GitHub guide
- Added 03-design/ phase: database schema design, SQL DDL, ERD, backend architecture, test plan, implementation plan
- Added CLAUDE.md to repo root (AI agent context file)
- Updated Key Decisions table to reflect post-API-research decisions (Deezer as ISRC source, Apple Music elevated, passive signals excluded from Glicko-2)

### v0.2 (2026-02-14)

- Initial discovery phase documentation
- Problem statement, user research, business case, stakeholder analysis
- All key architectural decisions finalised

---

**Next Phase:** Spike Validation (S-01 to S-10), then Phase 0 implementation

For project overview, see [root README.md](../README.md)
