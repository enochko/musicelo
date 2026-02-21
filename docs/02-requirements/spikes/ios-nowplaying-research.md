# MusicElo V3.0 — iOS Now-Playing API Research

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Date:** February 2026  
**Author:** Claude (AI-assisted research)  
**Stage:** Pre-Design Validation  
**Version:** 0.1

---

## 1. Purpose

This document records findings from iOS API documentation research conducted prior to executing spike S-07. It answers three questions raised during requirements review:

1. What data does `MPNowPlayingInfoCenter` expose to companion apps?
2. Does it identify the source music player/service provider?
3. If not, how should MusicElo disambiguate songs across platforms?

Findings informed the addition of tests #12–16 to the S-07 spike plan (see `spike-validation-plan.md` v0.2).

---

## 2. MPNowPlayingInfoCenter: Available Fields

`MPNowPlayingInfoCenter.default().nowPlayingInfo` is a `[String: Any]` dictionary. Each streaming app chooses which keys to populate. Based on Apple's documentation and developer community reports, the commonly populated keys are:

| Key | Type | Expected Reliability |
|-----|------|---------------------|
| `MPMediaItemPropertyTitle` | String | High — all apps set this |
| `MPMediaItemPropertyArtist` | String | High |
| `MPMediaItemPropertyAlbumTitle` | String | High |
| `MPMediaItemPropertyArtwork` | MPMediaItemArtwork | High |
| `MPMediaItemPropertyPlaybackDuration` | Double (seconds) | High |
| `MPNowPlayingInfoPropertyElapsedPlaybackTime` | Double (seconds) | High |
| `MPNowPlayingInfoPropertyPlaybackRate` | Float | High |
| `MPMediaItemPropertyAlbumArtist` | String | Medium |

Other keys that apps *can* set but may not: `MPMediaItemPropertyGenre`, `MPMediaItemPropertyComposer`, `MPMediaItemPropertyDiscNumber`, `MPMediaItemPropertyAlbumTrackNumber`, `MPNowPlayingInfoPropertyIsLiveStream`.

**Key finding: No source app identifier.** The dictionary contains no bundle ID, app name, or any system-injected metadata about which app wrote the now-playing data.

**Key finding: No platform-specific track IDs.** No Spotify track ID, Apple Music catalogue ID, or YouTube video ID is expected in the dictionary. S-07 test #9 (existing) and test #12 (new) will confirm empirically.

---

## 3. Platform-Specific Identification Paths

Research identified richer identification paths available per platform beyond `MPNowPlayingInfoCenter`:

### Spotify — Web API Polling

`GET /me/player/currently-playing` returns the full track object:

- `item.id` — Spotify track ID (direct lookup in `platform_song_ids`)
- `item.external_ids.isrc` — ISRC (canonical matching)
- `item.name`, `item.artists[].name`, `item.album.name` — metadata
- `item.duration_ms` — duration
- `is_playing` — playback state

Post-February 2026 status: endpoint retained in Dev Mode. ISRC confirmed available in the February 2026 changelog. Single-user scope means the 25-user Dev Mode limit is irrelevant.

### Apple Music — SystemMusicPlayer

`MPMusicPlayerController.systemMusicPlayer.nowPlayingItem` returns an `MPMediaItem` with `playbackStoreID` — the Apple Music catalogue ID (numeric string like `1440818831`). This only works when Apple Music is the active player; returns nil or stale data for Spotify/YTM.

### YouTube Music — No API Path

No equivalent API for currently-playing detection. Song identification relies entirely on title + artist string matching from `MPNowPlayingInfoCenter`. This is the weakest identification path and the primary consumer of fuzzy matching logic.

---

## 4. Proposed Hybrid Source Detection Strategy

To be validated in S-07 tests #13–15:

1. Poll Spotify Web API — if `is_playing == true` and title matches `MPNowPlayingInfoCenter` title → source = Spotify.
2. Check `systemMusicPlayer.playbackState` — if playing and `nowPlayingItem.title` matches → source = Apple Music.
3. If neither matches but `MPNowPlayingInfoCenter` has data → infer YouTube Music (or unknown).

Fallback: user-selected platform per session if heuristic proves unreliable.

---

## 5. Title Inconsistency Across Platforms

K-pop titles commonly vary across platforms:

| Variance Type | Example |
|---------------|---------|
| Language version suffix | YTM: "The Feels (Korean Ver.)" vs Spotify: "The Feels" |
| Remix/version tags | "FANCY (Remix)" vs "FANCY - Remix" |
| Parentheses vs dash | "What is Love? (Japanese Ver.)" vs "What is Love? - Japanese Ver." |
| Artist name ordering | "TWICE & Stray Kids" vs "Stray Kids, TWICE" |
| Whitespace variance | Trailing/double spaces (rare but observed) |

**Recommended matching approach:**

1. **Exact match** on title + artist + duration (±3 sec) against known platform IDs.
2. **Normalised fuzzy match**: lowercase, strip parenthetical suffixes, normalise whitespace, strip trailing punctuation.
3. **ISRC match** (when Spotify or Apple Music provides the ID, use it to look up ISRC → canonical match).
4. Below confidence threshold → queue for manual resolution.

Storing `original_title` per platform in `platform_song_ids` is recommended to preserve raw data for matching. The existing schema supports this without migration — the current `platform_id` and `platform_uri` columns capture the platform's native identifier, and title matching uses the `songs.title` field.

---

## 6. Impact Assessment

| Document | Impact | Action |
|----------|--------|--------|
| `spike-validation-plan.md` | S-07 tests expanded (#12–16), pass criteria and decision framework updated | **Done** — v0.2 |
| PRD | None — already correctly lists MPNowPlayingInfoCenter and Spotify Connect as separate monitoring paths | No changes needed |
| API research report | None — already documents Spotify currently-playing endpoint fields | No changes needed |
| Database schema | None — `playback_platform` on `play_events` and `platform_song_ids` already accommodate this | No changes needed |
| ADR-001 | None — companion app architecture unchanged; hybrid detection is an implementation detail | No changes needed |

---

## 7. Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-21 | 0.1 | Initial research note based on iOS API documentation review | Claude |
