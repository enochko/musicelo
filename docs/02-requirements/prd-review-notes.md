# MusicElo v3.0 PRD v0.2 — Review Notes

## Conflicts and Decisions Between Documents

### 1. Apple Music Priority: Could Have → Must Have

**PRD v0.1 (original):** FR-102 listed Apple Music as "Could Have"  
**Your annotation:** "Change to Should Have or Must Have"  
**API Research finding:** Spotify API restrictions (Feb 2026) removed ISRC from Dev Mode, removed audio features for new apps. Apple Music provides ISRC on catalogue songs, structured genres, and full library access.  
**Decision in v0.2:** Elevated to **Must Have**. Apple Music becomes a primary metadata and library import source alongside Spotify, not just a "nice to have". Spotify's restrictions make a multi-source strategy essential.

### 2. PRD Data Model vs. Database Schema Design

**PRD v0.1:** Defined a flat `Song` entity with `artist_official` as a string, `audio_features` as a single JSONB field.  
**Schema Design:** Normalised into 22 tables with separate `artists`, `albums`, `song_artists` M:N, structured `audio_features` table, `platform_song_ids` cross-references, `source_cache_*` tables.  
**Conflict:** The PRD's data model section was significantly simpler than what the schema design delivered.  
**Resolution in v0.2:** PRD §5 now references the schema design as the authoritative source for table definitions. The PRD retains a summary of the schema (22-table overview, key relationships, business rules) but defers detailed table definitions to the companion document. The flat `Song` entity description was replaced with a note explaining the normalisation decision.

### 3. Metadata Sources: PRD vs. API Research

**PRD v0.1:** Listed Spotify, YouTube Music, Apple Music, and MusicBrainz as sources. Audio features sourced from "Spotify/Apple Music/MusicBrainz?".  
**API Research:** Identified 10 sources including Deezer (free ISRC + BPM), ReccoBeats (Spotify Audio Features replacement), Last.fm (community tags), AcousticBrainz (legacy features), Musixmatch (genres + lyrics), Essentia/librosa (local).  
**Resolution in v0.2:** 
- Added "Metadata Enrichment Strategy" section to §2 with tiered priority
- Expanded FR-103 from "Import supplemental metadata from MusicBrainz" to "Enrich metadata from supplemental sources" covering all API sources
- Added FR-107 (Artist credit matching) based on the TWICE solo track mismatch problem identified in the API research
- Updated FR-106 to show source availability per field

### 4. ISRC Strategy: Spotify vs. Deezer

**PRD v0.1:** Assumed Spotify as primary ISRC source. Your annotation noted ISRC matching "no longer possible due to Spotify API restrictions".  
**API Research:** Deezer provides ISRC freely without authentication. MusicBrainz and Apple Music also provide ISRC.  
**Resolution in v0.2:** Deezer is now the primary ISRC source. Spotify ISRC is noted as "available but only in Extended Quota mode". The matching strategy is: ISRC first (from Deezer/Apple Music/MusicBrainz), then heuristic title+artist+duration fallback.

### 5. Snapshot Frequency: Monthly vs. Weekly

**PRD v0.1:** Monthly snapshots only (FR-206).  
**Your annotation:** "Should be weekly AND monthly — for the start when there are lots of volatility/movements, weekly changes will be very meaningful."  
**Schema Design:** `ranking_snapshots.snapshot_date` has a UNIQUE constraint — supports any frequency.  
**Resolution in v0.2:** Weekly snapshots during the first 3 months (high volatility period), transitioning to monthly once rankings stabilise. Business rule BR-009 updated accordingly. The schema's DATE UNIQUE constraint works for both frequencies (just different dates).

### 6. Undo Window: PRD v0.1 Ambiguity

**PRD v0.1:** "Undo is triggered within the same song's playback window."  
**Your annotation:** "Undo should always be allowed within a 10-second undo window — even if the song has advanced."  
**Resolution in v0.2:** FR-203 now explicitly specifies a 10-second undo window that applies regardless of song advancement, including late vote and pause-to-vote scenarios.

### 7. Duration Units: Seconds vs. Milliseconds

**PRD v0.1 data model:** `duration_seconds` (Integer)  
**Schema Design:** `duration_ms` (Integer) — milliseconds for consistency with Spotify and Apple Music APIs  
**Resolution in v0.2:** PRD defers to schema design. FR-106 notes "Duration: All platforms, Milliseconds".

### 8. Comparison Volatility Before/After

**PRD v0.1 data model:** Comparison entity stored rating and RD before/after but not volatility.  
**Schema Design:** Stores full rating, RD, AND volatility before/after (12 snapshot columns total).  
**Resolution in v0.2:** PRD FR-205 now specifies "Glicko-2 scores before and after (including volatility)". Business rules unchanged as the schema design already implements this correctly.

### 9. `response_time_ms` on Comparisons

**PRD v0.1:** Not specified.  
**Schema Design:** Added `response_time_ms` column for decision latency tracking.  
**Resolution in v0.2:** No conflict — this is an addition from the schema design. The PRD doesn't need to enumerate every column; the schema is authoritative.

### 10. `playback_platform` on Play Events

**PRD v0.1:** `PlayEvent` had no `playback_platform` field.  
**Schema Design:** Added `playback_platform` column ('spotify', 'youtube_music', 'apple_music').  
**Resolution in v0.2:** FR-400 data table now includes "Playback platform" as a captured data point.

---

## No Conflicts (Alignment Confirmed)

These items were consistent across all documents and required no resolution:

- Glicko-2 parameters and defaults (1500/350/0.06/0.5)
- 5-level comparison system (0.0/0.25/0.5/0.75/1.0)
- Canonical alias behaviour (shared Glicko-2 score via self-FK)
- Soft-delete for undo (`is_undone` flag, replay to recalculate)
- Three-phase mobile comparison timing
- Location zone privacy (GPS on-device only, zone names in cloud)
- Single-user scope with extensibility designed in
- Supabase free tier suitability (confirmed by schema storage estimates)

---

## Recommendations

1. **Consider applying for Spotify Extended Quota Mode** — if granted, this restores ISRC + batch endpoints. Worth attempting even if Deezer fills the gap, as it simplifies the import pipeline.

2. **MusicBrainz TWICE coverage validation** — before Phase 3 (design), verify MusicBrainz coverage of the full TWICE discography including recent releases, MISAMO, and solo tracks. This directly impacts the artist credit matching strategy.

3. **ReccoBeats reliability assessment** — the API's data provenance is undocumented. Consider running a small validation against known Spotify audio features (from existing public datasets or manual spot-checks) before relying on it heavily.
