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

**Requirements Specification Phase** (Coming soon)

Detailed functional and non-functional requirements derived from the discovery phase.

**Planned contents:** Functional requirements specification, user stories and acceptance criteria, API requirements, performance and scalability requirements, security and privacy requirements.

**Status:** 🔜 Not started

### 03-design/

**Design and Architecture Phase** (Coming soon)

Technical architecture, system design, and UX/UI specifications.

**Planned contents:** System architecture diagram, database schema and data models, API integration design, cross-platform architecture, UX wireframes and user flows, component structure.

**Status:** 🔜 Not started

### 04-implementation/

**Implementation Documentation** (Coming soon)

Development notes, decisions, and implementation guidance.

**Planned contents:** Implementation decisions and rationale, code structure and organisation, API integration notes, testing strategy, deployment procedures.

**Status:** 🔜 Not started

## Documentation Principles

### Why This Structure?

This documentation follows professional product development practices to:

1. **Demonstrate product thinking** — Structured discovery → requirements → design → implementation
2. **Maintain decision history** — Clear rationale for all major decisions
3. **Enable portfolio sharing** — Professional-quality artefacts suitable for job applications
4. **Support future development** — Clear context for resuming work after breaks

### Version Control

Documents are versioned within Git commits. Major updates increment the document version (currently v1.0). Revision history is tracked within each document.

### Australian English

All documentation uses Australian English spelling conventions (colour, visualise, organise, etc.).

## Key Decisions Summary

Quick reference for major architectural decisions made during the discovery phase:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Platform priority** | Spotify (metadata) + YouTube Music (playback) | Spotify has better library organisation and ISRC; YouTube Music is primary personal platform. Core Spotify endpoints confirmed available under Feb 2026 restrictions |
| **Cross-platform** | Desktop + mobile (feature parity) | Desktop for viewing/management, mobile for on-the-go listening/ranking |
| **Passive/active ratio** | 90% passive / 10% active | Avoid v2 UX failure where focused comparison felt like "work" |
| **Deduplication** | Canonical (earliest release) + aliases | Same song across multiple albums shares one rank/score |
| **Context handling** | Tagging (ML or manual) | Not separate Glicko-2 pools; tags used for context playlists |
| **Historical tracking** | Monthly snapshots | Weekly ideal but unrealistic; all history recorded for reconstruction |
| **Visual metadata** | Yes (if efficient) | Notes + YouTube links with timestamps for TTT/concert associations |
| **Intra-playlist pools** | Optional (if efficient) | Enables promotion/relegation workflow (Favourites ↔ General) |
| **Multi-user groundwork** | If straightforward, otherwise defer | Design flexibility without premature optimisation |

## Navigation Tips

### For Portfolio Reviewers

Start with:

1. [Problem Statement](./01-discovery/problem-statement.md) — Understand the core challenge
2. [Business Case](./01-discovery/business-case.md) — See strategic rationale and portfolio context
3. [User Research](./01-discovery/user-research-findings.md) — Dive into user-centred design approach

### For Technical Implementation

Start with:

1. [User Research Findings](./01-discovery/user-research-findings.md) — Platform requirements, UX patterns
2. [Problem Statement](./01-discovery/problem-statement.md) — Technical architecture decisions
3. 03-design/ (when available) — System architecture and data models

### For Understanding v2 → v3 Evolution

See:

- [Problem Statement — Background section](./01-discovery/problem-statement.md#background) — Origin story
- [User Research — v2 UX Failures](./01-discovery/user-research-findings.md#4-musicelo-v2-ux-failures) — What went wrong and lessons learned

## Changelog

### v1.0 (2026-02-14)

- Initial discovery phase documentation
- Problem statement, user research, business case, stakeholder analysis
- All key architectural decisions finalised

---

**Next Phase:** Requirements Specification (02-requirements/)

For project overview, see [root README.md](../README.md)
