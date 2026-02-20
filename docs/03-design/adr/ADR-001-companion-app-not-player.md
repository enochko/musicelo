# ADR-001: Companion App Architecture (Not a Music Player)

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** PRD v0.2 §3.1, CLAUDE.md §Critical Architectural Rules  

---

## Context and Problem Statement

MusicElo needs to capture now-playing data (song identity, play duration, skip events) from
the user's streaming apps to drive passive signal collection and trigger comparison prompts.
There are two broad approaches: build a music player that controls playback directly, or
build a companion app that monitors existing streaming apps.

The user's primary listening happens across Spotify, YouTube Music, and Apple Music on iOS,
with CarPlay as a key usage context. iOS imposes strict constraints on background audio
and inter-app communication.

## Decision Drivers

- iOS does not permit third-party apps to control or intercept audio from other apps in
  the background without the user explicitly routing audio through the third-party app
- The user already has established listening habits and playlists across multiple streaming
  platforms — requiring a platform switch creates adoption friction
- YouTube Premium subscription makes YouTube Music the primary playback platform; building
  a player that replicates this is redundant
- CarPlay integration requires apps to use specific Apple frameworks (CarPlay Audio or
  CarPlay Navigation); a full music player requires entitlements from Apple that are
  difficult to obtain for independent developers
- Development scope: building a full streaming player with offline caching, gapless
  playback, and CarPlay UI is a multi-year project in itself

## Considered Options

| Option | Description |
|--------|-------------|
| A — Full streaming player | Build MusicElo as a standalone music player that streams directly |
| B — Spotify-only remote control | Use Spotify Connect API to control Spotify playback |
| C — Screen scraping / accessibility API | Read now-playing data via iOS Accessibility APIs |
| D — Companion app via MPNowPlayingInfoCenter | Monitor system-wide now-playing info passively; no playback control |

## Decision Outcome

**Chosen option: D — Companion app via MPNowPlayingInfoCenter**

iOS exposes `MPNowPlayingInfoCenter` system-wide, which any app can read. This gives
MusicElo access to the currently playing track (title, artist, album, duration, elapsed
time) regardless of which streaming app is playing it, without requiring audio routing
changes or special entitlements.

## Consequences

**Positive:**
- Works across all streaming apps (Spotify, YouTube Music, Apple Music) with a single
  implementation
- No friction for the user — they continue using their preferred streaming app
- No Apple entitlement applications required
- Dramatically reduced scope: MusicElo only needs to read metadata and present UI, not
  manage audio

**Negative:**
- Dependent on streaming apps populating `MPNowPlayingInfoCenter` correctly — must be
  validated via spike S-07
- Cannot control playback (pause, skip) from MusicElo — comparison prompts are passive
  overlays only
- Now-playing data may have latency; apps are not required to update immediately on track
  change
- If a streaming app stops updating `MPNowPlayingInfoCenter` (e.g. after an OS update),
  MusicElo loses visibility silently

**Risks mitigated:**
- Spike S-07 validates `MPNowPlayingInfoCenter` reliability across Spotify, YouTube Music,
  and Apple Music before iOS development begins
