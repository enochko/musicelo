# User Research Findings: MusicElo v3.0

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System
**Date:** February 2026
**Research Method:** Stakeholder Interview (Primary User)
**Stage:** Discovery and Problem Definition
**Version:** 1.0

---

## Research Overview

### Research Goals

- Understand current music listening and ranking behaviour
- Identify pain points with existing streaming platforms
- Define success criteria for a ranking system
- Assess data availability and technical constraints
- Validate problem severity and solution direction
- Learn from MusicElo v2 failures to inform v3 design

### Methodology

Semi-structured interview with the primary user, focusing on current state, frustrations, and desired future state. The research explored technical constraints, data sources, and v2 learnings.

---

## Primary User Profile

### Demographics and Context

- **Role:** IT/accounting professional, data science graduate student
- **Music preferences:** K-pop enthusiast, particularly TWICE
- **Library size:** 1,000+ songs total, including 300+ TWICE tracks (250+ core discography + MISAMO + solo releases)
- **Primary platform:** YouTube Music (YouTube Premium subscriber)
- **Secondary platform:** Spotify (currently Free; willing to upgrade to Premium for metadata and library benefits)
- **Technical proficiency:** High — comfortable with APIs, algorithms, data analysis; some Python and HTML knowledge; limited other programming languages

### Listening Behaviour Patterns

Current decision-making is dominated by recency bias, with favourites shifting based on mood and context. The user relies on "Liked Songs" and curated playlists, and is aware that all favourites "feel good in different ways" making definitive ranking difficult. Music is heavily influenced by visual media — audio and visual go together.

> "It really depends on what I listened to most recently, what I'm currently into. But that changes over time."

### Platform and Device Context

- **Desktop (macOS/web):** Used most days; also used for music listening
- **Mobile (iOS):** Primary listening platform for on-the-go use (driving, walking, chores)
- **Listening frequency:** Not daily — usually when driving, sometimes during walks or chores, occasionally at desktop

**Current Playlist Ecosystem:**

TWICE-specific playlists include "TWICE Favourites" (songs that became favourites through various discovery paths) and "TWICE To Listen" (elevated from full discography for repeated listening and potential promotion). Genre and season-based playlists cover categories such as Soundtrack, Cinematic Score, K-pop, Japanese, Christmas, Disney, and mood-based collections (Happy, Love, Emotional, Dance, Pump Up, Easy Listening, Nostalgia) — though these mood collections remain underdeveloped.

---

## User Pain Points

### 1. Inability to Definitively Rank Favourites

**Severity:** High  
**Frequency:** Every time the user is asked about favourite songs

> "TWICE has such a large music library that it is incredibly difficult for me to figure out what's my favourite song."

Each song appeals in different ways, making it difficult to rank within songs that are all genuinely enjoyed. This causes frustration when articulating preferences, inability to create "best of" playlists with confidence, and reliance on recency rather than true preference assessment.

### 2. Opaque Streaming Platform Recommendations

**Severity:** Medium-High  
**Frequency:** Regular (during driving, walks, chores, and desktop listening)

> "Spotify and YouTube Music recommend me music, and it's generally pretty good. But I have no idea how they pick the songs they recommend."

The issue is not distrust of recommendations, but lack of understanding of the reasoning and context behind them. This represents a missed learning opportunity to understand personal preferences systematically.

### 3. Playlist Creation Lacks Emotional Continuity

**Severity:** Medium  
**Frequency:** When manually creating playlists

> "I'd like that the next song or whatever song that follows kind of carries on the emotional journey."

Manual playlist curation is time-intensive (~10–20 mins/month) and results in playlists that become "a bit of a mess" due to lack of systematic approach. The user wants similar songs to flow together naturally and for playlists to guide mood transitions.

### 4. MusicElo v2 UX Failures

**Severity:** Critical (for v3 design)  
**Impact:** Caused project abandonment

**What went wrong:**

- **v1 blocked by Spotify API closure:** Original concept could not proceed when Spotify closed new developer app registration in December 2025, forcing a pivot to YouTube Music for v2.
- **v2 pairwise comparison felt like "work":** Head-to-head song duels aren't how music is naturally consumed.
- Required focused sitting sessions — couldn't integrate with normal listening during driving, chores, or walking.
- Interest waned after novelty period — tedious to maintain engagement beyond initial setup.
- Discography extraction issues — YouTube Music deduplication problems with the same song appearing across multiple albums.
- Lacked canonical identification — didn't utilise ISRC or MusicBrainz IDs for song identity.

> "I want the ranking to work while I listen to music naturally — which means easily vote on current song ranking compared to previous song as I listen to it at the computer, while driving, walking, doing chores on the phone, etc. Having to sit down on focused pairwise comparison is tedious after the initial interest."

**v2 UX patterns to avoid:** One-on-one comparison with manual advancement; requiring clicks to advance playlist playback.

**v2 UX patterns to preserve:** 5-level comparison system (strong/weak previous, draw/equal, weak/strong current); easy playlist import; easy new song addition during playlist import.

---

## User Needs and Desired Outcomes

### Functional Needs

**1. Transparent Ranking System**

Rankings should be explainable via an audit trail of comparisons and listening history. The user wants to see a ranked list and think "yeah, that actually makes sense to me" — not a black-box algorithm.

**2. Similar Song Discovery**

Group and categorise songs by emotional or sonic similarity. Enable discovery of forgotten favourites and support ranking across different content types (could extend to TTT episodes using the same algorithm).

**3. Emotional Journey Playlists**

Automated playlist generation with mood progression — guiding from one emotional state to another (e.g., sad → happy, excited → calm) with smooth transitions between songs.

**4. Passive + Active Input Mechanisms (90/10 Balance)**

Primary input (90%) should be passive learning from playlists and listening patterns. Secondary input (10%) involves easy indication of whether the current song is better or worse than the previous one. Continuous listening flow must be preserved — the user must be able to continue listening while doing other activities.

**5. Visual Memory Integration**

Songs are strongly associated with visual memories (TTT episodes, concerts, music videos). Examples include songs tied to specific Mina, Sana, or member moments in concerts and variety shows. Implementation involves capturing notes and YouTube links with timestamps for future specialised playlist generation.

**6. Playlist Promotion/Relegation**

Use intra-playlist scoring to identify top songs in the "To Listen/General" playlist for promotion to "Favourites," and bottom songs in "Favourites" for relegation to "General."

### Non-Functional Needs

**Usability:** Low friction input methods (passive > active); works alongside existing streaming platforms; doesn't require constant attention; must support both desktop and mobile with full feature parity.

**Trust and Transparency:** Clear logic for why rankings exist; ability to validate rankings against intuition; explainable recommendations with an audit trail.

**Flexibility:** Support multiple artists; adapt to changing preferences over time with historical snapshots; allow pairwise comparison inputs and emotion/feeling tags; context tagging for workout/study/commute playlists.

**Privacy:** No concerns storing data locally or in cloud, provided cloud data is not associated with sensitive personally identifiable information. Data capture is acceptable and necessary for auditable rankings.

---

## Behavioural Patterns and Decision Triggers

### Song Skipping

When driving with others, the user skips songs that are too loud, heavy, or jarring. When listening alone within personal playlists, skipping is rare — occasional skips only to jump to a specific song that came to mind.

### Replay Behaviour

Triggered by emotional resonance at that moment. Usually not more than a couple of continuous replays, but may revisit multiple times throughout a day or week.

### Playlist Addition

Triggered when a song is interesting enough to warrant repeated listening, or when a song is intertwined with a movie, TV show, or video creating a memorable context.

### Comparison Fatigue

Focused pairwise comparison sessions have a tolerance of roughly 10 songs before fatigue sets in. Casual background listening with ranking comparisons can be sustained for up to around 30 songs, though attention wanes and only a few standout songs are actively ranked. This confirms passive ranking must be the primary mechanism (90%), with active comparison as an optional enhancement (10%).

---

## Emotional Taxonomy and Song Categorisation

### Current Emotion Categories

Happy, Love, Emotional, Dance, Pump Up, Easy Listening, Nostalgia — historically used but tiny collections (underdeveloped, low time investment). The user is receptive to better emotional categorisation if psychologically studied methods exist for reliable emotion mapping. Implementation would use context tagging via ML analysis or manual selection, not separate Glicko-2 rating pools.

### Example Song Clusters

- **Emotional/Connection:** One in a Million, Stuck, Cactus — songs where TWICE connected with Once; songs where members cried on stage.
- **Upbeat/Party:** Rollin' — upbeat, dance-y, party vibe.
- **Nostalgic/Seasonal:** The Best Thing I Ever Did — simultaneously nostalgic and Christmas-themed.
- **Motivating/Intense:** Shot Clock — hard driving, motivating, concert opener energy.
- **Easy Listening/City Pop:** Say Something — easy-listening, jazzy feel, Japanese sound with Korean lyrics.

---

## Current Workarounds and Limitations

### What the User Does Today

Ranking relies on recency bias as the first protocol, referencing "Liked Songs" and curated playlists with mental shortcuts based on recent emotional connections and visual memory associations. Playlist creation is manual, based on mood, with no systematic similarity assessment (~10–20 mins/month with inconsistent results).

### Why Current Approaches Fail

**Recency Bias:** Overweights recent listens at the expense of genuine long-term favourites. Lacks a comparative framework across all songs, and preference stability varies across time horizons.

**Streaming Platform Limitations:** YouTube Music has limited metadata and deduplication issues; Spotify has better metadata and ISRC for canonical identification but uncertain historical data retention. Both platforms have unknown play count/skip data availability, no export of ranking logic, and algorithms that optimise for engagement rather than user understanding.

**Manual Methods:** Don't scale to 300+ song catalogues. Subjective, inconsistent, with no quantitative comparison framework and no systematic visual memory capture.

---

## Data Availability Assessment

### Confirmed Available

- User-created playlists (structure and contents) from Spotify and YouTube Music
- Playlists the user listens to (listening context)
- Songs added to library / liked songs
- Favourites playlist and Liked Songs as signal data

### Uncertain Availability

- YouTube Music History export method (exists but unclear if exportable)
- Play count, skip rates, and listening timestamps per track (both platforms)
- Spotify historical data retention (may require Premium)

### Available Metadata Sources

- **Spotify:** ISRC (International Standard Recording Code) for canonical song identification; better organised library
- **MusicBrainz API:** Universal unique IDs, supplemental metadata
- Additional identifiers: ISWC, IPI, IPN, ISNI

### Required New Data

- Pairwise comparisons (user input during listening)
- "Previous song comparison" rankings during playback
- Song similarity metadata (to be generated via ML or manual tagging)
- Emotional categorisation and context tags
- Visual memory associations (notes and YouTube links with timestamps)
- Historical ranking snapshots (monthly cadence)

---

## Platform and Technical Constraints

### Development Environment

- **Primary workstation:** macOS/web (desktop work + some listening)
- **Mobile:** iOS (primary on-the-go listening)
- **Programming knowledge:** Some Python and HTML; limited other languages
- **Constraint:** Time limitations require significant AI assistance for coding and troubleshooting

### Integration Requirements

Must function with both Spotify and YouTube Music as playback platforms. Spotify serves as the primary metadata and library source; YouTube Music serves as the primary personal playback platform. Can be a separate app or extension; must have a dedicated UI for displaying ranking results on desktop.

---

## Success Validation Criteria

### Minimum Success Threshold

- Ranked list makes intuitive sense — "I look at the ranked list and go, yeah, that actually makes sense to me"
- Can confidently answer "what's my favourite song?"
- Passive ranking during natural listening works (not tedious like v2)
- 90% passive / 10% active input balance achieved

### Optimal Success State

- System discovers forgotten favourites
- Playlist generation has smooth emotional transitions
- Rankings adapt to changing preferences over time
- Transparent enough to understand and trust (audit trail functional)
- Historical tracking shows preference evolution (monthly snapshots)
- Reasonable ranking emerges after a few months of natural listening and ranking

### Measurable Indicators

- User can recall and agree with top 20 ranked songs
- Generated playlists feel emotionally coherent
- Comparative inputs (A vs B) align with computed rankings >80% of the time
- User voluntarily uses system instead of existing playlists and platform shuffle

---

## User Mental Models

### How the User Thinks About Music Preferences

**Emotional Resonance + Visual Memory Over Technical Quality:** Not focused on production quality or composition complexity. Focused on "how does this make me feel" and "what do I associate this with." Context-dependent with mood-based preference shifts. Songs are tied to specific visual moments (TTT episodes, concerts, music videos).

**Relative vs Absolute Ranking:** The user doesn't think in absolute scores (7/10, 8/10) but in comparisons ("Song A > Song B"). All favourites feel "good in different ways," making absolute values difficult to assign. The Glicko-2 approach aligns with this natural comparison mindset, and the 5-level system captures nuance when songs are close.

**Playlist as Journey:** Listening sessions are thought of as narrative arcs. The user values transitions and flow between songs and wants intentional mood guidance rather than shuffle.

**Playlist Hierarchy:** "Favourites" at the top tier, "To Listen/General" as a middle tier for evaluation. Intra-playlist ranking helps identify promotion and relegation candidates.

**Preference Evolution Awareness:** The user is aware that preferences change over time across multiple horizons (immediate, short-term, medium-term, long-term) and is interested in tracking this evolution through historical snapshots — whether as Billboard chart-style monthly rankings or as animated line graphs showing individual songs rising and falling over time.

---

## Insights and Design Implications

### Key Insights

1. **Transparency is as important as accuracy** — the user needs to understand *why* rankings exist to trust them.
2. **Passive learning must be primary (90%)** — active comparison should be an optional enhancement (10%), not the main mechanism.
3. **Natural listening integration is critical** — the system must work during driving, chores, and walking, not as a separate focused task.
4. **Emotional journey matters more than individual song quality** — playlist context matters as much as individual rankings.
5. **Forgotten song discovery is high-value** — surfacing past favourites is a key success metric.
6. **Visual memories matter** — songs strongly associated with visual contexts are a valuable metadata dimension.
7. **Preference evolution tracking is desired** — Billboard-style monthly historical snapshots to visualise change over time.
8. **Playlist promotion/relegation workflow** — intra-playlist scores help manage transitions between playlist tiers.
9. **Cross-platform parity is required** — both desktop and mobile need full playback and ranking capabilities.
10. **Both Spotify and YouTube Music are critical** — Spotify for metadata, YouTube Music for personal use, both for playback.

### Design Implications

**Ranking Algorithm:** Glicko-2 provides a comparative framework aligned with the user's mental model. An explainability layer (audit trail) is needed to show why Song X > Song Y. Rankings must update based on temporal preference shifts and support monthly historical snapshots.

**Input Mechanisms:** Primary (90%) passive learning from playlist structure and listening patterns. Secondary (10%) "previous song comparison" during natural playback with the 5-level system — casual background listening with ranking comparisons tolerable for up to around 30 songs. Tertiary: optional focused pairwise sessions with a tolerance of roughly 10 songs before fatigue sets in. Pure listening without active input must not negatively affect rankings.

**Playlist Generation:** Must consider emotional transitions, not just rankings. Needs similarity/mood clustering for journey creation. Sub-lists by category (title tracks, B-sides, language, remixes). Intra-playlist ranking for promotion/relegation workflow.

**Platform Integration:** Spotify as primary metadata source (ISRC, better organisation) with playback support. YouTube Music as primary personal platform, aligned with canonical library for playback. MusicBrainz for supplemental metadata and universal unique IDs.

**User Interface:** Desktop shows rankings with justifications (audit trail) and supports listening/ranking. Mobile provides low-friction "previous song comparison" input during playback. Both platforms enable exploration of similar songs and visualisation of emotional journeys.

**Data Model:** Canonical song identification via ISRC/MusicBrainz to handle deduplication. Earliest release as canonical; later releases aliased. Preserve full catalogue metadata for album-based playlist generation.

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-14 | 1.0 | Initial discovery phase documentation | Enoch Ko |

---

## Document Status

**Status:** Approved — Ready for Requirements Definition Phase  
**Next Phase:** Solution Exploration and Requirements Specification  
**Outstanding Items:** None — all research questions answered
