# Problem Statement: MusicElo v3.0

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System
**Date:** February 2026
**Author:** Enoch Ko
**Stage:** Discovery and Problem Definition
**Version:** 1.0

---

## Executive Summary

MusicElo v3.0 aims to solve the fundamental challenge of transparently ranking and discovering music within a large personal library. Traditional streaming platforms provide opaque recommendation algorithms that don't reflect individual listening preferences or enable users to understand why certain songs are recommended. MusicElo applies a proven competitive rating system (Glicko-2) to personal music preference quantification, enabling transparent, evidence-based rankings that adapt over time.

---

## Background

The MusicElo concept originated from observing ranking tournaments in the TWICE community on Reddit. User u/kdhisthebest conducted Quick Sort tournaments for [Time to Twice (TTT) episodes](https://old.reddit.com/r/twice/comments/13243ch/best_time_to_twice_ttt_season_tournament_final/) and subsequently for [all TWICE songs](https://old.reddit.com/r/twice/comments/16y3axa/best_twice_song_tournament_final_results/). The results were surprising and often controversial.

### Why Quick Sort Tournaments Have Limitations

The Quick Sort approach, while computationally efficient (O(n log n) comparisons), has fundamental problems for subjective preference ranking:

1. **Transitivity assumption fails:** Just because A > B and B > C doesn't necessarily mean A > C when preferences are subjective and context-dependent.
2. **Winner-takes-all voting:** Individual preferences get overwhelmed in group surveys, losing nuance.
3. **Minimal comparison data:** Quick Sort makes as few comparisons as possible, leaving most song relationships undefined.

### Inspiration from Glicko-2

After seeing [MKBHD's blind smartphone camera test](https://www.youtube.com/watch?v=VRoTOE3FqT0) using Elo ratings for pairwise photo comparisons, the concept emerged: use Glicko-2 (an improved Elo variant) to rate and rank songs through accumulated pairwise comparisons. This provides transparent rankings with confidence intervals, adaptability to changing preferences, and preservation of individual expression in what would otherwise be winner-takes-all group contexts.

---

## The Problem

### Core Issues

Users with extensive music libraries — particularly within single artists like TWICE's 250–300+ song discography including MISAMO and solo releases — face significant difficulty in:

1. **Definitively answering "What is my favourite song?"** when each song appeals in different ways.
2. **Understanding why streaming services recommend certain songs** — the algorithms are black boxes.
3. **Ranking songs that are all subjectively "good"** but require nuanced comparison.
4. **Creating playlists with emotional continuity** rather than just collections of favourites.
5. **Expressing individual preferences** in collective ranking contexts without being overwhelmed by winner-takes-all group dynamics.

### Current Pain Points

**Recency Bias Dominates Decision-Making**

Current listening relies heavily on what was most recently played. Mental shortcuts favour songs that are "top of mind" rather than genuinely preferred. Liked songs and favourites playlists don't capture relative preferences, and temporal shifts make it impossible to track preference evolution over time.

**Opaque Recommendation Systems**

Spotify and YouTube Music provide recommendations with no transparency into why a song was recommended or what context drove the suggestion. The recommendations may be good, but the reasoning remains invisible with no ability to understand or influence the ranking logic.

**Lack of Comparative Framework**

There is no systematic way to compare songs within large catalogues. Emotional resonance and replay value are subjective and unmeasured. Grouping similar songs or finding emotional journeys is manual and unreliable, and social groups (such as the r/TWICE subreddit) lack tools to rank collectively while respecting individual preferences.

**Previous Solution Attempts (v1 & v2) Failed**

- **v1:** Original concept using Spotify API — development was blocked when Spotify [closed new app registration](https://community.spotify.com/t5/Spotify-for-Developers/Unable-to-create-app/td-p/7283365) in December 2025, preventing API access. The project pivoted to YouTube Music for v2.
- **v2:** Built from PRD using YouTube Music but had critical UX issues:
  - Head-to-head pairwise comparison felt like "work" rather than natural listening.
  - Required focused sitting sessions rather than integrating with normal music consumption.
  - Interest waned after initial novelty — tedious to maintain engagement.
  - TWICE discography extraction from YouTube Music had deduplication issues (same song across multiple albums).
  - Lacked canonical song identification (ISRC and MusicBrainz IDs could solve this).

**Key Insight from v2:** The ranking system must work *while listening to music naturally* — during driving, walking, and chores — not as a separate focused task.

---

## Problem Context

### Library Scale

- **Primary focus:** TWICE discography (~250–300+ songs including MISAMO and solo releases)
- **Extended library:** Low thousands of songs across multiple artists
- **Challenge magnitude:** Ranking within enjoyed songs, not filtering bad from good

### User Constraints

- Limited time for active ranking inputs (especially as focused task)
- Needs passive learning from natural listening behaviour
- Requires transparency in how rankings are determined
- Must integrate with existing Spotify and YouTube Music platforms

### Temporal Dynamics

Preference change patterns identified:

- **Immediate shifts:** Preferences can change right after hearing a song in a TTT episode or YouTube compilation.
- **Short-term obsessions:** Some songs dominate for days or a week before dropping off.
- **Medium-term evolution:** Most preferences change on a month-to-quarter scale.
- **Long-term stability:** Some preferences remain stable, but specific favourites rotate.

A Billboard chart-like monthly ranking with historical tracking could visualise preference evolution over time. All ranking history should be recorded to enable reconstruction of any historical ranking.

### Failure Modes

Rankings would feel fundamentally wrong if clearly weaker songs ranked above known favourites, or if known favourites ranked anomalously low. The system must produce rankings that pass an intuitive "sniff test" against the user's existing sense of preference.

---

## What Success Looks Like

The problem will be considered solved when:

1. **Intuitive Rankings:** The ranked song list "just looks right" and makes immediate sense.
2. **Discovery of Forgotten Favourites:** The system surfaces songs that were genuinely loved but mentally deprioritised.
3. **Emotional Journey Playlists:** Generated playlists have smooth transitions and can guide mood (e.g., sad → happy, excited → calm).
4. **Transparent Logic:** Clear understanding of why songs are ranked as they are, via an audit trail of comparisons and listening history.
5. **Similar Song Grouping:** Ability to find and categorise songs by emotional or sonic similarity.
6. **Reasonable Ranking Emergence:** After listening and ranking naturally over a few months, meaningful results appear.

---

## Scope

### In Scope (v3.0)

**Core Ranking System**

- Glicko-2 algorithm implementation for transparent rating and ranking
- Support for TWICE complete discography (250–300+ songs)
- Multi-artist ranking within the TWICE ecosystem: TWICE, MISAMO, and solo releases are treated as separate artists but ranked together in a single global pool, reflecting how the music library is naturally consumed
- Song deduplication across albums while preserving catalogue metadata
- Canonical song identification using ISRC and/or MusicBrainz IDs (earliest release as canonical; later releases aliased)
- Scope limited to TWICE and related artists for easier testing and validation

**Passive + Active Input (90/10 Balance)**

- Natural listening integration — rank while playing music on-the-go and at desktop
- "Previous song comparison" UI during playback with 5-level system (strong/weak previous, draw, weak/strong current)
- Pure listening without ranking should not affect rankings negatively
- Easy tap/click to indicate preference without impacting listening experience
- Manual pairwise comparison as secondary/optional input

**Playlist Generation**

- Export rankings as playlists to Spotify and YouTube Music
- Basic playlist generation with ranking-based song ordering
- Sub-lists by category (title tracks vs. B-sides, original vs. translated, original vs. remix)
- Optional intra-playlist Glicko-2 scoring for promotion/relegation between playlist tiers

**Context and Metadata**

- Overall preference ranking (primary) — global Glicko-2 pool
- Context-dependent playlists (workout, study, etc.) handled via tagging (ML-based or manual), not separate rating pools
- Visual memory metadata: notes and/or YouTube links with timestamps for contextual associations (TTT episodes, concert moments, music videos)

**Platform Integration**

- **Primary metadata source:** Spotify (better organised library, ISRC for canonical identification)
- **Playback platforms:** Both Spotify and YouTube Music
- **Supplemental metadata:** MusicBrainz API for canonical identifiers

**Cross-Platform Support**

- Desktop (macOS/web): Full viewing, listening, and ranking capabilities
- Mobile (iOS): Full listening and ranking capabilities (primary on-the-go platform)
- Full feature parity for playback and ranking across both platforms

### Out of Scope (Deferred to v4.0+)

- Social features or multi-user ranking
- Real-time collaborative filtering
- Advanced emotional journey playlist generation (basic version in scope)
- Cross-artist ranking beyond the TWICE ecosystem (e.g., comparing TWICE songs against other artists)
- TTT episode ranking (same algorithm could apply, but different content type)
- Apple Music integration
- Music discovery outside personal library

**Data model consideration:** Design for future multi-user expansion where straightforward; otherwise defer to avoid premature optimisation.

---

## Problem Validation

**Evidence this is a real problem:**

- Existing MusicElo v1/v2 iterations indicate sustained interest despite v2's UX failures
- Personal frustration with inability to definitively rank favourites
- r/TWICE tournament results that feel "wrong" suggest broader community interest in better ranking methods
- v2 proved Glicko-2 scoring works — v3 must solve the UX and passive ranking challenge

**Why now:**

- Spotify has reopened developer access (v1 was blocked by API closure), albeit with [more restrictive Development Mode limits](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security) as of February 2026
- Accumulated 2+ years of YouTube Music listening history
- Spotify available for better metadata and library organisation
- Glicko-2 algorithm provides proven comparative ranking framework
- Spotify and YouTube Music APIs enable playback and data integration
- MusicBrainz API provides canonical music metadata
- Portfolio development goal creates structured development opportunity
- Master of Data Science programme provides academic context

---

## Success Criteria

### Minimum Viable Problem Solution

- System can rank TWICE discography in a way that feels intuitively correct
- User can answer "what's my favourite song?" with confidence
- Rankings are transparent and explainable via audit trail
- Passive ranking during natural listening is functional (not tedious like v2)

### Ideal State

- Automated playlist generation with emotional continuity
- 90% passive / 10% active input balance
- Historical ranking tracking showing preference evolution (monthly snapshots)
- Context-dependent playlist support via tagging
- Intra-playlist Glicko-2 scoring for playlist promotion/relegation
- Visual memory metadata captured and utilisable for specialised playlists

---

## Comparison Framework

### Context Sensitivity

**Primary use case:** Ranking "favourite overall" regardless of context (global Glicko-2 pool).

**Secondary use cases:** Context-dependent rankings (workout vs. study vs. commute), handled via a tagging system (ML-based or manual tags), not separate Glicko-2 pools.

### Comparison Boundaries

All songs are ranked together in a unified global system. Sub-lists are generated from the full ranking: title tracks vs. B-sides, original language vs. translated versions, original recordings vs. remixes, Korean vs. Japanese releases. Optional intra-playlist rankings support promotion/relegation between playlist tiers.

### Similar Song Examples

**Emotional/Connected cluster:** One in a Million, Stuck, Cactus — emotional, connection-focused songs where TWICE members cried on stage.

**Contrasting examples:** Rollin' (upbeat, party vibe), The Best Thing I Ever Did (nostalgic, Christmas-themed), Shot Clock (hard driving, concert opener energy), Say Something (easy-listening, jazzy, city pop feel).

---

## Technical Architecture Decisions

Key architectural decisions made during discovery:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Song deduplication** | Canonical (earliest release) + aliases | All aliases share the canonical song's rank/score; playlist generation uses alias but applies canonical ranking |
| **Platform priority** | Spotify (metadata) + YouTube Music (playback) | Spotify has better library organisation and ISRC; YouTube Music is primary personal platform. Note: Spotify's [February 2026 API restrictions](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security) constrain Development Mode but core endpoints (playlists, tracks, playback) remain available |
| **Cross-platform** | Desktop + mobile with feature parity | Desktop for viewing/management + listening; mobile for primary on-the-go listening/ranking |
| **Ranking architecture** | Global Glicko-2 pool (primary) | Single rating per song; optional intra-playlist pools only if efficient to implement |
| **Context handling** | Tagging (ML or manual) | Not separate rating pools; tags used for context-specific playlist generation |
| **Input balance** | 90% passive / 10% active | v2 failure lesson — pure listening must not negatively affect rankings |
| **Historical tracking** | Monthly snapshots | Weekly ideal but unrealistic long-term; all history recorded for reconstruction |
| **Visual metadata** | Notes + YouTube links with timestamps | For TTT/concert associations; implement if overhead is manageable |

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-14 | 1.0 | Initial discovery phase documentation | Enoch Ko |

---

## Document Status

**Status:** Approved — Ready for Requirements Definition Phase  
**Next Phase:** Solution Exploration and Requirements Specification  
**Outstanding Items:** None — all discovery questions answered
