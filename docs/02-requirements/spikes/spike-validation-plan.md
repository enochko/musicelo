# MusicElo V3.0 — Spike Validation Test Plan

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Date:** February 2026  
**Author:** Enoch Ko  
**Stage:** Pre-Design Validation  
**Version:** 0.1

---

## 1. Purpose and Rationale

### Why This Spike Exists

The MusicElo v3.0 PRD and API Research Report make architectural decisions based on documented API capabilities. However, several of those capabilities were identified through documentation review by an LLM (Claude), not through hands-on testing. This creates a specific category of risk: **documentation-reality mismatch**.

Known failure modes include:

- **Hallucinated API behaviour.** LLMs can confidently describe endpoints, fields, or capabilities that don't exist, or that exist differently from how they're described. The API Research Report was generated from web documentation — not from running code against live APIs.
- **Documentation staleness.** API docs may describe capabilities that have since been deprecated, rate-limited, or restricted. The Spotify Feb 2026 changes are proof that services change without always updating all documentation pages simultaneously.
- **K-pop coverage gaps.** Even if an API works perfectly for Western music, coverage for K-pop artists (particularly sub-unit/solo credits, ISRCs for Japanese releases, and lesser-known B-sides) may be incomplete. The API research identified this as a risk for MusicBrainz but didn't empirically test it.
- **Undocumented behaviour.** The Deezer ISRC lookup (`/track/isrc:{ISRC}`) is described as "undocumented but widely used." This means no official guarantee it works, no official error codes, and no official rate limits.
- **iOS platform API assumptions.** `MPNowPlayingInfoCenter` is assumed to reliably report now-playing metadata from all streaming apps. This is a core architectural dependency that has not been prototyped.

### What This Sprint Delivers

1. **Validated or invalidated assumptions** for every critical-path API dependency
2. **Documented evidence** (response payloads, field presence/absence, coverage statistics) that the PRD can reference
3. **Go/no-go recommendations** for each API source, feeding into PRD v1.1 if adjustments are needed
4. **Portfolio evidence** that hypotheses were validated before committing design and development time
5. **Reusable test scripts** in a public GitHub repository demonstrating technical diligence

### Trust Calibration Philosophy

The question isn't "should I trust the LLM or not?" — it's "what is the cost of being wrong?" For each dependency, this plan applies a simple framework:

| If wrong, what happens? | Validation approach |
|--------------------------|---------------------|
| Architecture changes required | **Must validate** — run test script, inspect response |
| Swap to a different source, no architecture change | **Should validate** — quick test if time permits |
| Nice-to-have feature lost | **Skip** — validate during implementation |

---

## 2. Scope

### In Scope (Must Validate)

These are "load-bearing" assumptions — if wrong, the PRD architecture or priority decisions change.

| ID | Spike | PRD Dependency | Est. Time |
|----|-------|----------------|-----------|
| S-01 | Spotify Web API — Accessible Content Audit | FR-100, FR-301, FR-500, Assumption 5 | 1.5 hours |
| S-02 | Deezer ISRC Fetch (search → track → ISRC) | FR-103, FR-106, BR-010, ISRC strategy | 1 hour |
| S-03 | Deezer ISRC Reverse Lookup (`/track/isrc:{ISRC}`) | FR-103, Matching strategy | 30 min |
| S-04 | MusicBrainz TWICE Coverage Audit | FR-107, Artist credit matching | 1.5 hours |
| S-05 | ReccoBeats TWICE Coverage | FR-103, Audio features strategy | 30 min |
| S-06 | Apple Music MusicKit — Auth + Catalogue Fetch | FR-102, Assumption 3, Must Have elevation | 2 hours |
| S-07 | iOS MPNowPlayingInfoCenter — Prototype | FR-300, Assumption 4, Core architecture | 2–3 hours |

**Total estimated time: 9–10 hours (3–4 sessions at 2–3 hours each)**

### In Scope (Should Validate If Time Permits)

Lower risk but worth confirming. Architecture survives if these fail.

| ID | Spike | PRD Dependency | Est. Time |
|----|-------|----------------|-----------|
| S-08 | Last.fm Tag Fetch for TWICE | FR-103, Tier 4 enrichment | 30 min |
| S-09 | Spotify Connect "Currently Playing" Polling | FR-301, Desktop monitoring | 30 min |
| S-10 | ytmusicapi Playlist/Library Fetch | FR-101, YouTube Music import | 30 min |

### Out of Scope (With Reasons)

| API/Feature | Reason for Exclusion |
|-------------|----------------------|
| **AcousticBrainz** | Could Have priority. Legacy dataset. Not on critical path. If MusicBrainz MBIDs are available (validated in S-04), AcousticBrainz lookup is trivial. |
| **Musixmatch** | Could Have priority. Lyrics/genre not core to ranking. Well-documented commercial API. |
| **Essentia / librosa** | Deferred to post-MVP. Requires audio files. These are established open-source libraries with extensive documentation and community validation. |
| **Supabase / PostgreSQL** | Well-established platform. Schema DDL is standard PostgreSQL. No novel dependencies. Risk is near-zero. |
| **FastAPI backend** | Standard Python web framework. No API-specific risk. |
| **Glicko-2 algorithm** | Mathematical algorithm with multiple reference implementations. Implementation correctness is a unit testing concern, not a spike. |
| **Desktop web framework** | OQ-1 in PRD. A separate decision that doesn't affect API validation. |
| **YouTube Music desktop detection** | OQ-2 in PRD. Worth investigating but not a spike — it's a research task. The system works without YTM desktop detection. |
| **CarPlay detection** | Standard iOS `UIScene` API. Well-documented by Apple. Low risk. |
| **Focus/DND status** | Standard iOS API (`UNNotificationSettings`). Well-documented. Low risk. |
| **Location zones / GPS** | Standard `CoreLocation`. Well-documented. Privacy architecture is a design decision, not a validation question. |
| **Apple Watch workout status** | OQ-4 in PRD. Explicitly "if technically feasible." Not on critical path. |

---

## 3. Spike Specifications

### S-01: Spotify Web API — Accessible Content Audit

**Risk being mitigated:** The API Research Report describes Spotify's Feb 2026 restrictions based on documentation review. The PRD's architecture (Assumption 5, FR-100, FR-301, FR-500) assumes specific endpoints remain accessible in Dev Mode. If the report hallucinated or misinterpreted the restriction scope, core functionality could be affected.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1a | `GET /v1/me/player/currently-playing` | Returns current track with `item.name`, `item.artists`, `item.album`, `item.id`, `progress_ms`, `is_playing` | Core of desktop now-playing detection (FR-301) |
| 1b | Same response — check for `item.external_ids.isrc` | **Should be ABSENT** in Dev Mode per Feb 2026 changes | Confirms ISRC restriction; validates Deezer fallback decision |
| 1c | `GET /v1/me/player/currently-playing` — check for `item.popularity` | **Should be ABSENT** in Dev Mode per Feb 2026 changes | Confirms popularity restriction |
| 2a | `GET /v1/tracks/{id}` with a known TWICE track | Returns track metadata (name, artists, album, duration_ms, track_number, disc_number, explicit) | Basic track fetch for library import |
| 2b | Same response — check for `external_ids` | **Should be ABSENT** in Dev Mode | Confirms ISRC restriction on track endpoint too |
| 3 | `GET /v1/me/playlists` | Returns user's playlists with `items[].id`, `items[].name`, `items[].tracks.total` | Playlist import (FR-100) |
| 4 | `GET /v1/playlists/{id}/tracks` for a user-owned playlist | Returns track items with `track.id`, `track.name`, `track.artists` | Playlist track enumeration |
| 5 | `GET /v1/playlists/{id}/tracks` for a **non-owned** playlist | **Should return error or empty** per Feb 2026 Dev Mode restriction | Confirms restriction; affects import UX |
| 6 | `GET /v1/me/tracks` (Liked Songs) | Returns saved tracks | Liked Songs import path |
| 7 | `GET /v1/search?q=TWICE+What+is+Love&type=track&limit=10` | Returns results (limited to 10/page in Dev Mode) | Confirms search still works but with limit |
| 8 | `GET /v1/tracks?ids={id1},{id2},{id3}` (batch endpoint) | **Should return error** in Dev Mode per Feb 2026 changes | Confirms batch endpoint removed; affects import performance |
| 9 | `GET /v1/audio-features/{id}` | **Should return 403 or similar** for new apps | Confirms audio features restricted; validates ReccoBeats decision |
| 10 | `PUT /v1/users/{user_id}/playlists` or `POST /v1/playlists/{id}/tracks` | Successfully creates/updates playlist | Playlist export (FR-500) |
| 11 | `GET /v1/me/player` (player state) | Returns device info, shuffle/repeat state | Context capture |

**Prerequisites:**
- Spotify Premium account (student plan)
- Registered Spotify app in Dev Mode
- OAuth 2.0 token with scopes: `user-read-currently-playing`, `user-read-playback-state`, `user-library-read`, `playlist-read-private`, `playlist-modify-public`, `playlist-modify-private`

**Script approach:**
- Python script using `requests` library (not `spotipy`, to see raw responses)
- Authenticate via Authorization Code Flow (manual browser redirect for token)
- Print each response with status code, headers, and body
- Highlight presence/absence of restricted fields

**Pass criteria:** All expected-available endpoints return 200 with expected fields. All expected-restricted fields are confirmed absent. Any surprises documented.

**Fail action:** If critical endpoints (currently-playing, playlists, liked songs) don't work, escalate immediately — this would invalidate the Spotify integration entirely and require architectural reassessment.

---

### S-02: Deezer ISRC Fetch (Search → Track → ISRC)

**Risk being mitigated:** Deezer is positioned as the primary ISRC source (replacing restricted Spotify ISRC). The API Research Report describes this as "free, no auth, immediate access" — but this was not tested against actual K-pop tracks.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | `GET /search?q=TWICE What is Love` | Returns track results with `data[].id`, `data[].title`, `data[].artist.name` | Basic K-pop search works |
| 2 | `GET /track/{deezer_id}` for the result above | Returns full track with `isrc`, `bpm`, `gain`, `duration`, `contributors[]` | ISRC + BPM available on individual track |
| 3 | Verify the ISRC format (e.g., `KRXXXXXXXX`) | Valid ISRC string | ISRC actually populated, not null/empty |
| 4 | Repeat for 10 diverse TWICE tracks: title track, B-side, Japanese version, solo, sub-unit (MISAMO), older era, recent release | ISRC present for all or most | Coverage across the TWICE catalogue |
| 5 | `GET /search?q=TWICE Feel Special` — check BPM on individual track lookup | Non-zero `bpm` value | BPM field populated for K-pop |
| 6 | `GET /album/{album_id}/tracks` for a TWICE album | Returns tracks **without** `bpm` field | Confirms BPM only on individual lookups (documented limitation) |
| 7 | Test rate limiting: make 20 requests in quick succession | Some succeed, observe throttling behaviour | Understand practical rate limits |
| 8 | Search for an obscure TWICE track (e.g., "Jaljayo Good Night" from *twicetagram*) | Returns result with ISRC | Coverage for non-title tracks |

**Test tracks (minimum 10, spanning the catalogue):**

| Track | Album | Era | Type | Notes |
|-------|-------|-----|------|-------|
| What is Love | What Is Love? | 2018 | Title track | High-popularity, definitely on Deezer |
| Feel Special | Feel Special | 2019 | Title track | Standard test |
| SCIENTIST | Formula of Love | 2021 | Title track | More recent |
| SET ME FREE | READY TO BE | 2023 | Title track | Recent era |
| Strategy | STRATEGY | 2025 | Title track | Most recent |
| Jaljayo Good Night | twicetagram | 2017 | B-side | Obscure, tests deep catalogue |
| Alcohol-Free | Taste of Love | 2021 | Title track | Well-known |
| ONE SPARK | With YOU-th | 2024 | Title track | Recent |
| Hare Hare | ??? | 2023 | Japanese single | Tests J-releases on Deezer |
| Marshmallow | — | 2023 | MISAMO sub-unit | Tests sub-unit coverage |

**Prerequisites:** None (unauthenticated API).

**Script approach:**
- Python script using `requests`
- No auth required
- Print ISRC, BPM, duration, artist name for each track
- Summary table at the end: track name → ISRC present (Y/N), BPM present (Y/N)

**Pass criteria:** ISRC present for ≥8/10 test tracks. BPM present for ≥6/10. Rate limiting manageable (≥1 req/sec sustained).

**Fail action:** If ISRC coverage is <50% for TWICE, Deezer cannot be the "primary ISRC source." Fallback: Apple Music becomes primary ISRC source, or apply for Spotify Extended Quota.

---

### S-03: Deezer ISRC Reverse Lookup

**Risk being mitigated:** The undocumented `/track/isrc:{ISRC}` endpoint is referenced in the matching strategy. If it doesn't work, cross-platform matching by ISRC needs a different implementation.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | Take an ISRC obtained in S-02, call `GET /track/isrc:{ISRC}` | Returns the matching Deezer track | Confirms endpoint exists and works |
| 2 | Try with ISRCs from 5 different TWICE tracks | Returns matches for all/most | Coverage |
| 3 | Try with an ISRC from Apple Music or MusicBrainz (not Deezer-sourced) | Returns a match | Cross-source ISRC lookup works |
| 4 | Try with an obviously invalid ISRC | Returns error (not crash) | Error handling is reasonable |
| 5 | Try with an ISRC that has multiple versions (e.g., remastered) | Returns one result (documented limitation) | Understand single-result behaviour |

**Prerequisites:** At least one valid ISRC from S-02 or from Apple Music/MusicBrainz.

**Script approach:** Extension of S-02 script. Feed ISRCs back in and check responses.

**Pass criteria:** Endpoint returns valid responses for ≥4/5 known ISRCs. Errors handled gracefully for invalid input.

**Fail action:** If endpoint is broken or severely rate-limited, remove it from the matching strategy. The forward direction (Deezer search → get ISRC) is more important and is what S-02 validates.

---

### S-04: MusicBrainz TWICE Coverage Audit

**Risk being mitigated:** The entire artist credit matching strategy (FR-107) and canonical ID system depends on MusicBrainz having adequate TWICE data. The API Research Report flagged this as a risk but didn't verify empirically.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | `GET /ws/2/artist?query=TWICE&fmt=json` | Returns TWICE (the K-pop group) with MBID | Can find the group |
| 2 | `GET /ws/2/artist/{twice_mbid}?inc=artist-rels&fmt=json` | Returns "member of band" relationships listing all 9 members | Artist credit matching depends on this |
| 3 | Check member count: Nayeon, Jeongyeon, Momo, Sana, Jihyo, Mina, Dahyun, Chaeyoung, Tzuyu | All 9 present with individual MBIDs | Complete group membership |
| 4 | `GET /ws/2/release-group?artist={twice_mbid}&type=album&fmt=json` | Returns TWICE Korean + Japanese albums | Discography coverage |
| 5 | Count albums: compare against known TWICE discography (~13 Korean + ~5 Japanese albums + compilations + MISAMO) | ≥80% coverage | Overall catalogue completeness |
| 6 | Pick a Korean album (e.g., *Formula of Love*): `GET /ws/2/release?release-group={rg_mbid}&inc=recordings+artist-credits&fmt=json` | Returns tracks with artist credits | Track-level coverage |
| 7 | Check a solo track on *TEN* album (e.g., Nayeon's track): is artist credit Nayeon or TWICE? | Likely credited to individual member per MusicBrainz style | Validates the artist credit mismatch problem |
| 8 | `GET /ws/2/recording?artist={nayeon_mbid}&inc=isrcs+artist-credits&fmt=json` | Returns Nayeon's solo recordings with ISRCs | Solo track ISRC availability |
| 9 | Search for MISAMO: `GET /ws/2/artist?query=MISAMO&fmt=json` | Returns MISAMO as a separate artist entity | Sub-unit handling |
| 10 | Check MISAMO → TWICE relationship | "subgroup"/"member of" relationship exists | Sub-unit to group mapping |
| 11 | Search for a very recent release (2025 *STRATEGY* album) | Present in MusicBrainz | Timeliness of data |
| 12 | `GET /ws/2/recording/{mbid}?inc=url-rels&fmt=json` for a TWICE recording | Returns URL relationships to Spotify, Apple Music, etc. | Cross-platform ID resolution via MusicBrainz |

**Prerequisites:** None (open API, User-Agent header required).

**Script approach:**
- Python script, 1 request/second rate limit enforced
- Start from TWICE artist MBID, traverse down to releases and recordings
- Build a coverage report: albums found vs. expected, member count, ISRC presence
- Log raw responses for reference

**Pass criteria:**
- All 9 members present with "member of band" relationships
- ≥80% of known TWICE albums present
- Track-level data exists for tested albums
- Solo tracks credited to individuals (confirming the mismatch pattern exists and is navigable)

**Fail action:** If coverage is <50%, MusicBrainz cannot be the canonical ID backbone. Consider contributing missing data to MusicBrainz (community-editable) or relying more heavily on Deezer + Apple Music IDs for cross-referencing.

---

### S-05: ReccoBeats TWICE Coverage

**Risk being mitigated:** ReccoBeats is the primary replacement for Spotify Audio Features. Its data provenance is undocumented (PRD OQ-8). If it has no data for K-pop, audio features need a different source or deferral.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | Look up audio features for "What is Love" using Spotify track ID | Returns `tempo`, `valence`, `danceability`, `energy`, `key`, `mode`, `loudness`, etc. | Basic availability |
| 2 | Repeat for 10 TWICE tracks (same diverse set as S-02) | Returns features for all/most | K-pop coverage breadth |
| 3 | Compare returned BPM with Deezer BPM (from S-02) for the same tracks | Values within ±5 BPM | Cross-source consistency (basic sanity check) |
| 4 | Check for null/zero fields in responses | Most fields populated | Data completeness |
| 5 | Test rate limiting: 10 requests with ~0.5s delay | All succeed | Practical throughput |
| 6 | Try batch endpoint with 5 Spotify IDs | Returns features for all 5 | Batch capability |

**Prerequisites:** Spotify track IDs for test tracks (obtainable from Spotify URLs or S-01).

**Script approach:**
- Python script, no auth
- Use Spotify track IDs
- Print feature set per track
- Summary: fields present/absent per track, BPM comparison with Deezer

**Pass criteria:** Audio features returned for ≥7/10 tracks. Core fields (tempo, valence, danceability, energy) populated.

**Fail action:** If coverage <50%, deprioritise ReccoBeats to Could Have. Audio features become a v3.1 concern. BPM still available from Deezer. The ranking system does not depend on audio features.

---

### S-06: Apple Music MusicKit — Auth + Catalogue Fetch

**Risk being mitigated:** Apple Music was elevated from Could Have to Must Have in PRD v1.0. This is the highest-impact priority change in the PRD. If MusicKit authentication is prohibitively complex or the developer experience is poor, this decision should be reconsidered before design begins.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | Generate a MusicKit developer token (JWT) | Valid JWT token | Auth pipeline works |
| 2 | `GET /v1/catalog/au/search?term=TWICE+What+is+Love&types=songs` | Returns search results with song objects | Basic catalogue access |
| 3 | Inspect a song result: check for `attributes.isrc` | ISRC present (e.g., `KRXXXXXXXX`) | ISRC availability on catalogue songs |
| 4 | Inspect: `attributes.genreNames[]` | Genre array populated (e.g., `["K-Pop", "Pop"]`) | Genre data quality |
| 5 | Inspect: `attributes.durationInMillis`, `attributes.trackNumber`, `attributes.discNumber` | Present and correct | Core metadata fields |
| 6 | ISRC filter lookup: `GET /v1/catalog/au/songs?filter[isrc]={isrc}` | Returns matching song(s) | ISRC-based cross-platform matching |
| 7 | Fetch user library (requires user token): `GET /v1/me/library/songs` | Returns library songs | Library import path (FR-102) |
| 8 | Check library song for ISRC: follow `catalog` relationship | ISRC accessible via catalogue relationship | Confirms ISRC not on library-songs directly |
| 9 | Fetch user playlists: `GET /v1/me/library/playlists` | Returns playlist list | Playlist import |

**Prerequisites:**
- Apple Developer Program membership (already budgeted: ~$149 AUD/year)
- Apple Music subscription (already budgeted: ~$6.99 AUD/month)
- Developer token generation (requires private key from Apple Developer portal)
- User token for library access (MusicKit JS or native auth flow)

**Important note:** This spike has the highest setup cost. The JWT token generation requires:
1. Creating a MusicKit identifier in Apple Developer portal
2. Generating a private key
3. Writing JWT creation code (Python `PyJWT` library)

If this setup alone takes >1 hour, document the experience — that's valuable data about the developer experience for planning purposes.

**Script approach:**
- Python script using `requests` + `PyJWT`
- Developer token: generated locally from Apple private key
- User token: may need to use MusicKit JS in a browser for the OAuth flow, then copy the token to the Python script
- Print responses with field inspection

**Pass criteria:**
- Developer token generation works
- Catalogue search returns TWICE songs with ISRC and genre
- ISRC filter lookup works
- Library access achievable (even if the auth flow is clunky)

**Fail action:** If developer token generation fails or is blocked, reconsider Apple Music as Must Have. If catalogue works but library access is impractical without a native app, note that library import requires the iOS app (not a standalone backend script) — this is an architectural finding, not a failure.

---

### S-07: iOS MPNowPlayingInfoCenter — Prototype

**Risk being mitigated:** `MPNowPlayingInfoCenter` is the foundational assumption of the entire companion app architecture. The PRD states (Assumption 4): "iOS MPNowPlayingInfoCenter reliably reports current track from all streaming apps." This has never been tested. If it doesn't work — or doesn't provide enough metadata to identify songs — the architecture needs fundamental rethinking.

**What to test:**

| # | Test | Expected Result | Why It Matters |
|---|------|-----------------|----------------|
| 1 | Build minimal iOS app (or Playground) that reads `MPNowPlayingInfoCenter.default().nowPlayingInfo` | Returns a dictionary with metadata | Basic API access |
| 2 | Play a song in **Spotify**, read now-playing info | Dictionary contains `MPMediaItemPropertyTitle`, `MPMediaItemPropertyArtist`, `MPMediaItemPropertyAlbumTitle`, `MPMediaItemPropertyPlaybackDuration` | Spotify populates the system now-playing |
| 3 | Play a song in **Apple Music**, read now-playing info | Same fields present | Apple Music populates it |
| 4 | Play a song in **YouTube Music**, read now-playing info | Same fields present | YTM populates it (this is the most uncertain) |
| 5 | Check for additional useful fields: `MPNowPlayingInfoPropertyElapsedPlaybackTime`, `MPMediaItemPropertyPlaybackDuration`, `MPNowPlayingInfoPropertyPlaybackRate` | Present and updating | Playback progress tracking |
| 6 | Song transition: play song A, then song B — does the dictionary update? | New song metadata appears | Transition detection works |
| 7 | Timing: how quickly after song change does the dictionary update? | <3 seconds (per NFR-004) | Latency acceptable |
| 8 | Background execution: move app to background, play a song — can we still read now-playing? | Yes, via background task or timer | Critical for real-world use |
| 9 | Check for unique identifiers: is there a Spotify track ID, Apple Music ID, or any platform-specific ID in the dictionary? | **Probably not** — but must verify | If present, simplifies song matching significantly |
| 10 | CarPlay: connect to CarPlay (or simulator), play music — does now-playing still work? | Yes | CarPlay use case (primary driving scenario) |
| 11 | Test with Korean song titles: do Unicode characters come through correctly? | Yes, full Hangul preserved | K-pop metadata integrity |

**Prerequisites:**
- Xcode installed on Mac
- iPhone for real-device testing (simulator may not have real now-playing data)
- Spotify, Apple Music, and YouTube Music apps installed on the iPhone
- Apple Developer account for deploying to device

**Prototype approach:**
- Minimal SwiftUI app with a single view
- Timer-based polling (every 1 second) of `MPNowPlayingInfoCenter`
- Display all dictionary keys and values on screen
- Log to console for analysis
- No backend, no Supabase, no API calls — purely testing what iOS provides

**Why this can't be a Python script:** `MPNowPlayingInfoCenter` is an iOS/macOS framework API. It must be tested in a native app context. This is the one spike that requires Swift/Xcode.

**Pass criteria:**
- Now-playing metadata accessible from all three streaming apps (Spotify, Apple Music, YouTube Music)
- Song title, artist, album, and duration present
- Updates within 3 seconds of song change
- Works in background (even with limitations)
- Korean characters displayed correctly

**Fail action:** If `MPNowPlayingInfoCenter` doesn't work for YouTube Music, the PRD's claim that YTM works on mobile "via MPNowPlayingInfoCenter" is wrong. Mitigation: YTM mobile now-playing detection may require a different approach or may not be possible. If it doesn't work for *any* app, the companion app architecture itself needs rethinking (this would be a critical finding).

**Partial failure scenarios:**
- If background execution is severely limited: now-playing detection may only work when the MusicElo app is in foreground. This changes the UX significantly — document and escalate.
- If no platform-specific IDs are in the dictionary: song matching must rely on title + artist string matching against the library. This is expected but confirm.

---

### S-08: Last.fm Tag Fetch for TWICE (Should Validate)

**Risk:** Low. Last.fm is a well-established API. But K-pop tag quality/availability is unknown.

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `track.getTopTags` for "TWICE - What is Love" | Returns tags with counts (e.g., "k-pop", "dance pop") |
| 2 | Repeat for 5 TWICE tracks | Tags present for most |
| 3 | `artist.getTopTags` for "TWICE" | Returns artist-level genre tags |

**Prerequisites:** Free Last.fm API key.

**Pass criteria:** Tags returned for ≥3/5 tracks. Tag quality reasonable (not garbage/spam).

---

### S-09: Spotify Connect "Currently Playing" Polling (Should Validate)

**Risk:** Medium-low. Already partially covered by S-01 test 1a, but this tests real-time behaviour.

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Poll `GET /v1/me/player/currently-playing` every 2 seconds while music plays | Returns consistent, updating responses |
| 2 | Change song — how quickly does the endpoint reflect the new track? | <5 seconds |
| 3 | Pause playback — does `is_playing` update? | Yes |
| 4 | Play on phone, poll from desktop script — does it see the phone's playback? | Yes (Connect API is cross-device) |

**Prerequisites:** Same as S-01. Music actively playing on any Spotify device.

**Pass criteria:** Endpoint updates within 5 seconds of song change. Cross-device visibility confirmed.

---

### S-10: Ytmusicapi Playlist/Library Fetch (Should Validate)

**Risk:** Medium. Unofficial library. May break. But community-maintained and actively used.

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `ytmusic.get_library_songs()` | Returns list of library songs with title, artist, album |
| 2 | `ytmusic.get_playlist(playlist_id)` for a known playlist | Returns playlist tracks |
| 3 | Check for `videoId`, `title`, `artists[].name`, `album.name`, `duration_seconds` | Fields present |
| 4 | Test with a playlist containing TWICE songs | Korean metadata correct |

**Prerequisites:** YouTube Music account. Browser cookie authentication setup for `ytmusicapi`.

**Pass criteria:** Library and playlist fetch work. Core metadata fields present. Korean characters correct.

---

## 4. Test Data Strategy

All spikes should use a consistent set of TWICE songs to enable cross-source comparison. The canonical test set:

| # | Track | Album | Year | Type | Spotify ID | Notes |
|---|-------|-------|------|------|-----------|-------|
| T-01 | What is Love | What Is Love? | 2018 | Korean title track | `0Cy2oKxAHqaClJE6PxfFnl` | High popularity baseline |
| T-02 | Feel Special | Feel Special | 2019 | Korean title track | `4bMVRHSBfHOKYsfXMZJx6w` | Standard test |
| T-03 | SCIENTIST | Formula of Love: O+T=<3 | 2021 | Korean title track | TBD | Mid-era |
| T-04 | SET ME FREE | READY TO BE | 2023 | Korean title track | TBD | Recent |
| T-05 | Strategy | STRATEGY | 2025 | Korean title track | TBD | Most recent |
| T-06 | Jaljayo Good Night | twicetagram | 2017 | Korean B-side | TBD | Obscure deep cut |
| T-07 | Hare Hare | — | 2023 | Japanese single | TBD | Japanese release |
| T-08 | Marshmallow | — | 2023 | MISAMO sub-unit | TBD | Sub-unit track |
| T-09 | POP! | IM NAYEON | 2022 | Solo (Nayeon) | TBD | Solo member release |
| T-10 | Alcohol-Free | Taste of Love | 2021 | Korean title track | TBD | Well-known, good BPM test |

**"TBD" Spotify IDs:** Look up before running spikes. These are needed for S-01 and S-05.

---

## 5. Deliverables and Documentation

### Per-Spike Deliverables

Each spike produces:

1. **Python script** (or Swift project for S-07) — the test code
2. **Raw output log** — console output showing actual API responses (redacted of tokens)
3. **Result summary** — at the top of the script file as a comment block:
   ```
   # SPIKE S-02: Deezer ISRC Fetch
   # Date: 2026-0X-XX
   # Result: PASS / PARTIAL PASS / FAIL
   # Summary: ISRC found for 9/10 tracks. BPM found for 7/10. Rate limiting ~2 req/sec.
   # PRD Impact: None — Deezer confirmed as primary ISRC source.
   # Detailed findings: [see output log below]
   ```

### Sprint Summary Document

After all spikes complete, produce a `spike-validation-results.md` summarising:

- Overall pass/fail status per spike
- Findings that change PRD assumptions
- Recommended PRD v1.1 changes (if any)
- Updated risk assessments for Technical Risks table (§9)

### GitHub Structure

```
musicelo-v3/
├── ...existing folders...
│
├── 02-requirements/
│   ├── musicelo-v3-prd-v1_0.md
│   └── spikes/                              ← New
│       ├── README.md                        ← This plan + summary
│       ├── spike-validation-plan.md         ← This document
│       ├── spike-validation-results.md      ← Post-sprint summary
│       ├── s01_spotify_content_audit.py
│       ├── s02_deezer_isrc_fetch.py
│       ├── s03_deezer_isrc_lookup.py
│       ├── s04_musicbrainz_twice_audit.py
│       ├── s05_reccobeats_twice.py
│       ├── s06_apple_musickit_auth.py
│       ├── s07_mpnowplaying_prototype/      ← Xcode project folder
│       │   └── (minimal Swift project)
│       ├── s08_lastfm_tags.py               ← If completed
│       ├── s09_spotify_connect_polling.py    ← If completed
│       ├── s10_ytmusicapi_fetch.py           ← If completed
│       └── .env.example                     ← Template for API keys (no real keys)
```

---

## 6. Execution Schedule

### Recommended Session Plan

| Session | Spikes | Focus | Est. Time |
|---------|--------|-------|-----------|
| **Session 1** | S-02, S-03, S-05, S-08 | No-auth APIs (Deezer, ReccoBeats, Last.fm) | 2.5–3 hours |
| **Session 2** | S-01, S-09, S-10 | Auth-required APIs (Spotify, ytmusicapi) | 2–2.5 hours |
| **Session 3** | S-04 | MusicBrainz deep audit (rate-limited, slow) | 1.5–2 hours |
| **Session 4** | S-06 | Apple Music MusicKit setup + test | 2 hours |
| **Session 5** | S-07 | iOS MPNowPlayingInfoCenter prototype | 2–3 hours |
| **Session 6** | — | Write spike-validation-results.md, update PRD if needed | 1 hour |

**Total: ~12–14 hours across 6 sessions**

Session 1 is deliberately front-loaded with no-auth APIs — fastest to execute, provides immediate confidence/concern signals that inform later sessions. If Deezer ISRC fails in Session 1, Session 4 (Apple Music) becomes more urgent.

### Dependencies Between Spikes

```
S-02 (Deezer ISRC) ──→ S-03 (Deezer ISRC Lookup) — needs ISRCs from S-02
S-01 (Spotify audit) ──→ S-05 (ReccoBeats) — needs Spotify track IDs
S-04 (MusicBrainz) ──→ (informs S-06 priority) — if MB coverage poor, Apple Music more critical
```

---

## 7. Decision Framework

After all spikes complete, use this framework to determine PRD impact:

| Scenario | Action |
|----------|--------|
| All spikes pass | Proceed to design with PRD v1.0 as-is |
| Deezer ISRC fails for K-pop | Elevate Apple Music ISRC to primary; consider Spotify Extended Quota application; update PRD §2 enrichment strategy |
| MusicBrainz TWICE coverage <50% | Downgrade FR-107 (artist credit matching) to Should Have; rely on platform artist IDs + manual override |
| ReccoBeats has no K-pop data | Move audio features to v3.1; remove from MVP enrichment scope |
| Apple Music auth prohibitively complex | Reconsider Must Have → Should Have; document developer experience findings |
| MPNowPlayingInfoCenter doesn't work for YTM | Remove YTM mobile now-playing claim from PRD; YTM becomes import-only source |
| MPNowPlayingInfoCenter doesn't work at all | **Critical.** Companion app architecture needs redesign. Consider notification-based approach or foreground-only operation. |
| Spotify endpoints more restricted than documented | Reduce Spotify dependency; accelerate Apple Music integration |
| Multiple spikes fail | PRD v1.1 with revised architecture; possible scope reduction for MVP |

---

## 8. Revision History

| Date       | Version | Changes                       | Author   |
| ---------- | ------- | ----------------------------- | -------- |
| 2026-02-16 | 0.1     | Initial spike validation plan | Enoch Ko |
