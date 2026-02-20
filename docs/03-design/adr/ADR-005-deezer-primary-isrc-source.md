# ADR-005: Deezer as Primary ISRC Source

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** PRD v0.2 §4.2, api-research-report.md §2.5, prd-review-notes.md §4  

---

## Context and Problem Statement

ISRC (International Standard Recording Code) is the primary cross-platform identifier
for song deduplication in MusicElo. The same recording may exist on Spotify, Apple Music,
YouTube Music, and Deezer under different platform IDs; ISRC is the stable identifier
that links them.

MusicElo needs a reliable, accessible source for ISRC data. As of February 2026, the
API landscape for ISRC access has changed significantly.

## Decision Drivers

- Spotify removed `external_ids` (which contained ISRC) from Development Mode API
  responses in February 2026; ISRC is now only available to apps with Extended Quota
  Mode approval — a significantly higher bar requiring Spotify review
- MusicElo is currently a Development Mode app and obtaining Extended Quota Mode is
  not guaranteed
- Apple Music provides ISRC on catalogue songs but requires an Apple Developer Program
  membership (annual fee) and JWT authentication setup
- MusicBrainz provides ISRC via `inc=isrcs` but coverage varies for K-pop; community
  curation means recent releases may be missing or incomplete
- Deezer provides ISRC freely on its Track object (`isrc` field) with no authentication
  required for catalogue lookups, and supports a direct ISRC lookup endpoint
  (`GET /track/isrc:{ISRC}`)
- Deezer also provides BPM as a bonus field on the same Track object — no additional
  request needed

## Considered Options

| Option | Description |
|--------|-------------|
| A — Spotify Extended Quota | Apply for Extended Quota Mode; use Spotify as ISRC source |
| B — Apple Music | Use Apple Music API as primary ISRC source |
| C — MusicBrainz | Use MusicBrainz `inc=isrcs` as primary ISRC source |
| D — Deezer | Use Deezer free API as primary ISRC source |
| E — Multi-source with priority | Try Deezer first, fall back to Apple Music, then MusicBrainz |

## Decision Outcome

**Chosen option: E — Multi-source with priority, with Deezer first**

Deezer is the primary ISRC source due to zero barriers to access. Apple Music is the
secondary source (reliable, structured, but requires Developer Program). MusicBrainz
is the tertiary source (free, but K-pop coverage gaps are a known risk validated in
spike S-04).

Applying for Spotify Extended Quota Mode (Option A) is recommended as a parallel track
but not depended upon.

## Consequences

**Positive:**
- Immediate ISRC access with no authentication setup, no API key management, no approval process
- BPM obtained as a free by-product of the ISRC lookup
- Fallback chain provides resilience if any single source is unavailable
- Deezer's ISRC lookup endpoint enables bidirectional lookup

**Negative:**
- Deezer's ISRC lookup endpoint is undocumented — works in practice but could be removed without notice; must be validated in spike S-03
- Deezer returns only one track per ISRC lookup, even if multiple recordings share the ISRC
- Deezer has no published rate limits for unauthenticated access; throttling behaviour must be validated empirically
- BPM only returned on individual track lookups, not when listing album tracks — requires per-track fetches

**Risks mitigated:**
- Spike S-03 validates Deezer ISRC availability specifically for TWICE tracks before the enrichment pipeline is built
