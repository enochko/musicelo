# Song Metadata Fields Across Music Service APIs

## Research Report — February 2026 (v0.1)

---

## 1. Executive Summary

This report catalogues the song/track-level metadata fields available via APIs and tools from **ten** music data sources: **Spotify**, **YouTube Music**, **Apple Music**, **MusicBrainz**, **Deezer**, **Last.fm**, **AcousticBrainz** (legacy), **Musixmatch**, **ReccoBeats**, and local audio analysis libraries (**Essentia** / **librosa**). It identifies cross-platform identifiers, documents access restrictions, addresses the artist credit mismatch problem (particularly for K-pop group/solo releases), and surveys alternatives for audio features (genre, key, tempo, valence, mood) now that Spotify has restricted access.

**Key findings:**

- **ISRC** remains the primary cross-platform identifier (available from Spotify Extended Quota, Apple Music, MusicBrainz, and — crucially — **Deezer**, which is free and unauthenticated for basic lookups).
- **Deezer** is a major discovery: its free API provides ISRC, BPM, gain, contributors, and an undocumented ISRC lookup endpoint (`/track/isrc:{ISRC}`). It fills gaps left by Spotify's restrictions.
- **Artist credit mismatches** between MusicBrainz and streaming platforms (e.g., TWICE's *TEN* album crediting individual soloists vs. the group) require multi-level matching using **artist IDs**, **release-level artist credits**, and MusicBrainz's **"member of group" relationships**.
- **Audio features** (key, tempo, valence, danceability, etc.) are obtainable outside Spotify via Deezer (BPM), AcousticBrainz (legacy dataset, ~7M recordings), ReccoBeats (free API, Spotify-compatible features), Essentia (open-source local analysis), and librosa (Python library).
- **Genre/mood tags** are best sourced from Last.fm (community tags), MusicBrainz (genres), Apple Music (genreNames), and Musixmatch (genre + mood metadata).

---

## 2. Service-by-Service API Overview

### 2.1 Spotify Web API

**API Type:** Official REST API (OAuth 2.0)
**Base URL:** `https://api.spotify.com/v1`
**Endpoint:** `GET /tracks/{id}`

Spotify's Web API is the most widely used commercial music metadata API. It returns a structured JSON Track Object with nested Album and Artist sub-objects.

**Critical Warning — February 2026 Breaking Changes:**
Spotify announced sweeping changes to its Web API in February 2026 that severely impact **Development Mode** apps. The following fields have been **removed** from Dev Mode responses:

- `external_ids` (which contained **ISRC**, EAN, and UPC)
- `available_markets`
- `linked_from`
- `popularity`

For album objects, `external_ids`, `label`, and `popularity` were also removed.

**Extended Quota Mode** apps are unaffected. This means that obtaining ISRC from Spotify now requires applying for and being granted Extended Quota Mode access—a significantly higher bar.

Additional restrictions for Dev Mode include: search results limited to 10 per page, batch endpoints (`GET /tracks` for multiple IDs) removed, and playlist contents only returned for playlists the user owns or collaborates on.

**Other access notes:**
- Audio Features and Audio Analysis endpoints were restricted to pre-existing apps in late 2024; new apps cannot access them.
- 30-second preview URLs were removed for new apps.
- Spotify Premium account required to create apps.
- Content may not be used to train ML/AI models.
- Metadata must be accompanied by a link back to Spotify and the Spotify logo.

### 2.2 YouTube Music / YouTube Data API v3

**API Type:** Official YouTube Data API v3 (REST, API key or OAuth 2.0) + Unofficial `ytmusicapi` (Python, cookie-based auth)
**Base URL (official):** `https://www.googleapis.com/youtube/v3`
**Unofficial library:** `ytmusicapi` (Python, reverse-engineered)

YouTube Music does **not** have a dedicated official API. Developers must choose between:

1. **YouTube Data API v3** — returns video-level metadata (title, description, channel, duration, view count) but has no music-specific fields, no ISRC, no album, no structured artist field.

2. **`ytmusicapi`** (unofficial) — provides music-specific fields like artist, album, duration, and explicit flag. Does **not** expose ISRC.

**Access restrictions (official API):** Daily quota of 10,000 units. No ISRC, no structured artist/album fields.
**Access restrictions (ytmusicapi):** Unofficial; may break at any time. Requires browser cookie authentication. No ISRC field.

### 2.3 Apple Music API

**API Type:** Official REST API (JWT authentication via Apple Developer Program)
**Base URL:** `https://api.music.apple.com/v1`
**Endpoint:** `GET /v1/catalog/{storefront}/songs/{id}`

Apple Music's API provides rich metadata including ISRC as a standard field and a dedicated ISRC lookup endpoint: `GET /v1/catalog/{storefront}/songs?filter[isrc]={isrc}`.

**Important caveat:** ISRC is only on **catalog songs**, not `library-songs`. Must follow the `catalog` relationship to get ISRC for library songs.

**Access requirements:** Apple Developer Program membership (annual fee), JWT token authentication.

### 2.4 MusicBrainz API

**API Type:** Open REST API (no API key required; User-Agent header mandatory)
**Base URL:** `https://musicbrainz.org/ws/2`
**Key resource:** `recording` (equivalent to a "track/song")

MusicBrainz is an open-source, community-maintained music encyclopedia. ISRC is available via `inc=isrcs`. Direct ISRC lookups: `GET /ws/2/isrc/{isrc}`. Stores URL relationships to Spotify, Apple Music, YouTube, and other platforms.

**Access notes:** 1 request/sec rate limit. Descriptive User-Agent mandatory. Community-curated data: excellent for Western music, may be incomplete for K-pop.

### 2.5 Deezer API *(NEW)*

**API Type:** REST API (no auth required for basic catalog lookups; OAuth 2.0 for user data)
**Base URL:** `https://api.deezer.com`
**Endpoint:** `GET /track/{id}`

Deezer is a critical addition to the data source portfolio. Its "Simple API" provides free, unauthenticated access to track metadata including **ISRC and BPM** — two fields that have become restricted on Spotify. It also supports an undocumented but widely-used ISRC lookup endpoint.

**Key fields on Deezer Track object:**
- `id`, `title`, `title_short`, `title_version`
- `isrc` — **Available freely, no authentication required**
- `duration` (seconds)
- `track_position`, `disk_number`
- `bpm` (float) — **BPM/tempo available without audio analysis**
- `gain` (float) — track gain/loudness value
- `rank` (integer, 0–1M range, popularity proxy)
- `release_date`
- `explicit_lyrics`, `explicit_content_lyrics`, `explicit_content_cover`
- `preview` (30-second MP3 preview URL)
- `contributors[]` (array of contributing artists with id, name, role)
- `artist` (object with id, name)
- `album` (object with id, title, cover URLs)
- `available_countries[]`

**Undocumented ISRC lookup:** `GET /track/isrc:{ISRC}` returns a track matching the given ISRC. Note: only returns one track even if multiple share an ISRC.

**Access notes:**
- No authentication required for catalog lookups (search, track, album, artist).
- No published rate limits for unauthenticated access, but throttling is enforced.
- OAuth 2.0 required for user-specific data (playlists, favorites).
- BPM is only returned on individual track lookups, not when listing album tracks.

### 2.6 Last.fm API *(NEW)*

**API Type:** REST API (API key required, free registration)
**Base URL:** `https://ws.audioscrobbler.com/2.0/`

Last.fm is the premier source for **community-sourced genre/style tags** and **listening statistics**. Its tagging system is freeform and crowdsourced, providing richer genre classification than most structured APIs.

**Key endpoints and data:**
- `track.getTopTags` — Community tags for a track (e.g., "k-pop", "dance pop", "electronic"), with weighted counts (0–100)
- `artist.getTopTags` — Community tags for an artist
- `track.getInfo` — Track metadata including playcount, listeners, duration, MBID (MusicBrainz ID), tags, wiki
- `track.getSimilar` — Similar tracks based on Audioscrobbler algorithm (requires both track and artist name)
- `artist.getSimilar` — Similar artists

**Key fields per track:** track name, artist name, MBID, playcount, listeners, duration, top tags (with counts), wiki/summary, album info, user playcount (if authenticated).

**Access notes:**
- Free API key via registration. No OAuth required for public data.
- Rate limit: ~5 requests/second (not formally documented, but enforced).
- Tags are community-generated and unstructured—some noise (e.g., "seen live", "favorites").
- MusicBrainz IDs (MBIDs) are often included, enabling cross-referencing.
- Commercial/research use requires contacting Last.fm.

### 2.7 AcousticBrainz *(LEGACY — Data Archive)*

**API Type:** REST API (still accessible at acousticbrainz.org) + downloadable data dumps
**Status:** Stopped collecting data in 2022. Website and API still available but no new submissions.

AcousticBrainz crowdsourced audio analysis data (computed via Essentia) for ~7 million unique MusicBrainz recordings. Data is indexed by MusicBrainz Recording MBID.

**Key fields (low-level):** BPM, key, scale, average loudness, spectral features, rhythm descriptors, tonal descriptors.
**Key fields (high-level):** mood (acoustic, aggressive, electronic, happy, party, relaxed, sad), genre (Rosamerica, Electronic, TZNETZE), danceability, voice/instrumental classification, gender classification, timbre, tonal/atonal.

**Access notes:**
- All data licensed CC0 (public domain).
- Data dumps available: ~29.5M submissions across ~7M unique MBIDs.
- Requires knowing the MusicBrainz Recording MBID to look up data.
- Data quality varies by submission (different audio codecs/bitrates).
- Best used as a pre-computed lookup table, not for new analysis.

### 2.8 Musixmatch API *(NEW)*

**API Type:** REST API (API key required)
**Base URL:** `https://api.musixmatch.com/ws/1.1/`

Musixmatch operates the world's largest licensed lyrics database (14M+ lyrics, 50+ languages). Beyond lyrics, it provides track metadata, genre tags, and mood annotations.

**Key endpoints:**
- `track.search` — Search by track name, artist name, lyrics text, or ISRC
- `track.get` — Track metadata including genre, ISRC, album info
- `track.lyrics.get` — Full lyrics text
- `matcher.lyrics.get` — Match and retrieve lyrics by track + artist name
- `track.snippet.get` — Short lyric snippet

**Key fields:** track_name, artist_name, album_name, track_isrc, first_release_date, track_rating (0–100), has_lyrics, has_subtitles, num_favourite, primary_genres (genre_list with id, name), lyrics_body, lyrics_language.

**Access notes:**
- Free tier for non-commercial use (limited to 2,000 API calls/day, 30% of lyrics body).
- Commercial use requires paid plan or partnership.
- ISRC available in track metadata.
- Genre data is structured (not freeform like Last.fm tags).

### 2.9 ReccoBeats API *(NEW)*

**API Type:** REST API (free, no auth for basic features)
**Base URL:** `https://reccobeats.com/`
**Key endpoint:** `GET /v1/track/audio-features?ids={spotify_ids}`

ReccoBeats emerged as a direct replacement for Spotify's deprecated Audio Features API. It provides the same set of audio features (acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, valence) using Spotify track IDs.

**Key fields returned:**
- `acousticness` (0.0–1.0)
- `danceability` (0.0–1.0)
- `energy` (0.0–1.0)
- `instrumentalness` (0.0–1.0)
- `liveness` (0.0–1.0)
- `loudness` (dB, typically -60 to 0)
- `speechiness` (0.0–1.0)
- `tempo` (BPM)
- `valence` (0.0–1.0, musical positiveness)
- `key` (0–11, pitch class)
- `mode` (0 = minor, 1 = major)
- `time_signature` (e.g., 3, 4, 5)
- `duration_ms`

**Also offers:** Audio Feature Extraction API (upload audio file, get features back).

**Access notes:**
- Free to use, no API key required for track lookups.
- Accepts Spotify track IDs (comma-separated for batch).
- Rate limited (recommended ~0.5s between calls; batch size ~5 IDs).
- Database of millions of tracks, regularly updated.
- Quality/provenance of data not fully documented.

### 2.10 Local Audio Analysis Libraries *(NEW)*

For complete control over audio feature extraction, two open-source Python libraries are the industry standard:

#### Essentia (Music Technology Group, UPF Barcelona)
**License:** AGPL v3 (proprietary license available)
**Languages:** C++ core, Python and JavaScript bindings

Essentia is the most comprehensive MIR (Music Information Retrieval) library. It was the engine behind AcousticBrainz.

**Extractable features:**
- **Rhythm:** BPM (multiple algorithms: RhythmExtractor2013, PercivalBpmEstimator, TempoCNN), beat positions, onset detection, rhythm patterns
- **Tonal:** Key and scale (KeyExtractor using HPCP), chords, chord progression, tuning frequency
- **Spectral:** MFCCs, spectral centroid, rolloff, flux, contrast, bandwidth
- **High-level (via TensorFlow models):** Mood (happy, sad, aggressive, relaxed, party, acoustic, electronic), genre classification, danceability, voice/instrumental, music auto-tagging
- **Loudness:** EBU R128 loudness, dynamic range
- **Duration, silence detection, audio problems**

**Requires:** Access to audio files (MP3, WAV, FLAC, etc.). Cannot work from metadata alone.

#### librosa (LabROSA, Columbia University)
**License:** ISC (permissive)
**Language:** Python only

librosa is simpler and more accessible than Essentia, widely used in research.

**Extractable features:**
- **Tempo/rhythm:** BPM estimation (`librosa.feature.tempo`), beat tracking, onset detection, tempogram
- **Tonal:** Chroma features (STFT, CQT, CENS), tonnetz
- **Spectral:** MFCCs, spectral centroid, bandwidth, contrast, rolloff, zero crossing rate
- **Mel spectrogram**, Short-time Fourier Transform
- **Does NOT directly output:** Key/scale (must derive from chroma), mood/valence, genre, danceability

**Key difference:** librosa provides building blocks (chroma, MFCCs, spectrograms) but not high-level descriptors like mood or genre. Essentia provides both low-level and high-level features including pre-trained ML models.

---

## 3. Artist Credit Mismatch Problem

### 3.1 The TWICE *TEN* Example

A critical matching issue arises with K-pop group releases that contain solo tracks. On streaming platforms (Spotify, Apple Music, YouTube Music, Deezer), all tracks on TWICE's *TEN* album are credited to **TWICE** as the artist. However, MusicBrainz follows its style guidelines of crediting tracks to the **specific performing artist(s)** as printed on the release. This means solo tracks may be credited to individual members (e.g., Nayeon, Jihyo) rather than the group.

This creates a mismatch where:
- **Spotify:** Artist = "TWICE" (Spotify Artist ID: `7n2Ycct7Beij7Dj7meI4X0`)
- **MusicBrainz:** Track-level artist credit = "Nayeon" or "Jihyo" (individual MBIDs), while the **release-level** artist credit remains "TWICE"

### 3.2 MusicBrainz Artist Credit Structure

MusicBrainz's artist credit system is multi-layered:

- **Release-group artist credit** — The "album artist" (typically the group name: TWICE)
- **Release artist credit** — Same as release-group in most cases
- **Track/Recording artist credit** — The specific credited artist(s), which may differ per track
- **Artist-credit[] array** — Contains one or more artist objects, each with:
  - `artist.id` (MBID)
  - `artist.name` (canonical name)
  - `name` (credited-as name, may differ from canonical)
  - `joinphrase` (e.g., " feat. ", " & ")
- **"Member of group" relationship** — Links individual artists to their group(s)

### 3.3 Recommended Matching Strategy with Artist IDs

To handle this mismatch:

1. **Always store and match on artist IDs, not just artist names.** Spotify Artist IDs, Apple Music Artist IDs, and MusicBrainz Artist MBIDs are all stable and unambiguous.

2. **Use release-level artist credit from MusicBrainz** as the "album artist" for matching against streaming platforms, since streaming platforms typically credit the group for all tracks.

3. **Leverage "member of group" relationships** in MusicBrainz. When a track-level artist credit on MusicBrainz is an individual (e.g., Nayeon), check if that artist has a "member of group" relationship to the expected group (TWICE). If so, treat it as a match.

4. **Fetch with `inc=artist-credits`** when looking up MusicBrainz releases to get full artist credit details at both release and track level.

5. **Build an artist alias/group membership cache:** For each group in your library, pre-fetch all member relationships. When matching, check: does the MusicBrainz track artist belong to the same group as the streaming platform's album artist?

**API calls for this:**
- Lookup artist by MBID with `inc=artist-rels`: returns "member of band" relationships
- Browse recordings by artist: `GET /ws/2/recording?artist={mbid}&inc=artist-credits+isrcs`
- Release lookup with `inc=artist-credits+recordings`: shows both release-level and track-level credits

---

## 4. ISRC and Cross-Platform Identifiers

### 4.1 ISRC Availability (Updated)

| Service | ISRC Available? | How to Access | Restrictions |
|---------|----------------|---------------|-------------|
| **Spotify** | Yes (was standard) | `external_ids.isrc` on Track Object | **Removed from Dev Mode in Feb 2026.** Extended Quota only. |
| **Apple Music** | Yes | `attributes.isrc` on catalog Songs; ISRC lookup endpoint | Only on catalog songs, not `library-songs`. |
| **MusicBrainz** | Yes | `inc=isrcs` on recording lookups; `/ws/2/isrc/{isrc}` | Community-curated; coverage varies. |
| **Deezer** | **Yes** | `isrc` field on Track object; `/track/isrc:{ISRC}` lookup | Free, no auth. Undocumented ISRC endpoint returns only 1 result. |
| **Musixmatch** | Yes | `track_isrc` in track metadata | Available in track.get and track.search responses. |
| **YouTube Music** | No | Not exposed via any public/unofficial API | Internal CMS uses ISRC for rights management. |
| **Last.fm** | No | N/A | Provides MusicBrainz IDs instead. |

### 4.2 Other Cross-Platform Identifiers

| Identifier | What It Identifies | Where Available |
|-----------|-------------------|----------------|
| **UPC/EAN** | Album/release (product) | Spotify (Extended Quota), Apple Music (EPF), MusicBrainz (barcode), Deezer (album.upc) |
| **ISWC** | Composition/musical work | MusicBrainz (Work entities) |
| **MBID** | Any MusicBrainz entity | MusicBrainz; referenced by Last.fm and AcousticBrainz |
| **Spotify ID/URI** | Track/album/artist on Spotify | Spotify; MusicBrainz stores as URL relationships |
| **Apple Music ID** | Song/album/artist on Apple Music | Apple Music |
| **Deezer ID** | Track/album/artist on Deezer | Deezer; MusicBrainz stores as URL relationships |
| **YouTube Video ID** | Video/song on YouTube | YouTube; MusicBrainz stores as URL relationships |

### 4.3 Practical Matching Strategy (Updated)

1. **ISRC first** — Obtain from Deezer (free, no auth), Apple Music, or MusicBrainz. Search other platforms by ISRC.
2. **Heuristic matching** — title + artist + album + duration (±2–5s tolerance). Normalize strings.
3. **MusicBrainz as a bridge** — URL relationships link to Spotify, YouTube, Apple Music, Deezer, and more.
4. **Artist ID resolution** — When artist names don't match (group vs. solo), use MusicBrainz artist relationships to resolve group membership.
5. **Deezer as ISRC bridge** — Use Deezer's free ISRC field to obtain ISRCs without Spotify Extended Quota.

---

## 5. Audio Features, Genre, and Mood: Alternatives to Spotify

With Spotify's Audio Features and Audio Analysis endpoints restricted (new apps post-Nov 2024 cannot access them), here is the landscape for obtaining these enrichment fields:

### 5.1 Feature Availability Matrix

| Feature | Deezer | AcousticBrainz | ReccoBeats | Essentia | librosa | Last.fm | Musixmatch | Apple Music |
|---------|--------|---------------|------------|----------|---------|---------|------------|-------------|
| **BPM/Tempo** | `bpm` field | Yes | `tempo` | Yes (multiple algos) | Yes | No | No | No |
| **Key** | No | Yes | `key` + `mode` | Yes (KeyExtractor) | Derivable from chroma | No | No | No |
| **Time Signature** | No | No | `time_signature` | Derivable | Derivable | No | No | No |
| **Valence** | No | No | `valence` | Mood models (proxy) | No | No | No | No |
| **Danceability** | No | `danceable` | `danceability` | Yes (algo) | No | No | No | No |
| **Energy** | No | No | `energy` | Derivable (loudness/dynamics) | Derivable | No | No | No |
| **Acousticness** | No | `mood_acoustic` | `acousticness` | Yes (model) | No | No | No | No |
| **Instrumentalness** | No | `voice_instrumental` | `instrumentalness` | Yes (model) | No | No | No | No |
| **Loudness** | `gain` | `average_loudness` | `loudness` | Yes (EBU R128) | Yes (RMS) | No | No | No |
| **Genre** | Album genre | `genre_rosamerica` etc. | No | Yes (models) | No | **Community tags** | `primary_genres` | `genreNames[]` |
| **Mood** | No | Multiple mood classifiers | No | Yes (models) | No | **Community tags** | Yes (mood tags) | No |
| **Speechiness** | No | No | `speechiness` | Derivable | No | No | No | No |
| **Liveness** | No | No | `liveness` | Derivable | No | No | No | No |

### 5.2 Recommended Strategy for Audio Features

**Tier 1 — Pre-computed API lookups (no audio file needed):**
- **Deezer:** Free BPM and gain for any track by ID or ISRC. Start here.
- **ReccoBeats:** Full Spotify-style feature set by Spotify track ID. Free, easy drop-in replacement.
- **AcousticBrainz:** If you have MusicBrainz Recording MBIDs, look up pre-computed features for ~7M tracks. CC0 license. Legacy data (no new submissions since 2022).

**Tier 2 — Community tags (genre/mood):**
- **Last.fm:** Best source for genre/mood tags. `track.getTopTags` returns weighted tags.
- **MusicBrainz:** `inc=genres` returns structured genres (more controlled than Last.fm but less granular).
- **Apple Music:** `genreNames[]` provides Apple's editorial genre classification.
- **Musixmatch:** `primary_genres` provides structured genre data; mood available on some tracks.

**Tier 3 — Local audio analysis (requires audio files):**
- **Essentia:** Most comprehensive. Run locally on audio files for key, BPM, mood, genre, danceability, etc. Pre-trained TensorFlow models for high-level features.
- **librosa:** Simpler, good for BPM and tonal features. No built-in high-level classifiers.

---

## 6. Common Fields Across Services (Summary Table)

| Metadata Concept | Spotify | YouTube API | ytmusicapi | Apple Music | MusicBrainz | Deezer | Last.fm |
|-----------------|---------|-------------|------------|-------------|-------------|--------|---------|
| **Platform ID** | `id` | `id` (VideoID) | `videoId` | `id` | `id` (MBID) | `id` | N/A |
| **Title** | `name` | `snippet.title` | `title` | `attributes.name` | `title` | `title` | `name` |
| **Artist Name(s)** | `artists[].name` | `channelTitle`¹ | `artists[].name` | `attributes.artistName` | `artist-credit[].artist.name` | `artist.name` | `artist` |
| **Artist ID** | `artists[].id` | `channelId` | `artists[].id` | via rels | `artist-credit[].artist.id` | `artist.id` | MBID |
| **Album Name** | `album.name` | N/A | `album.name` | `attributes.albumName` | via release | `album.title` | `album` |
| **Duration** | `duration_ms` (ms) | ISO 8601 | `duration_seconds` | `durationInMillis` | `length` (ms) | `duration` (sec) | `duration` (ms) |
| **Track Number** | `track_number` | N/A | `trackNumber`² | `attributes.trackNumber` | track position | `track_position` | N/A |
| **Disc Number** | `disc_number` | N/A | N/A | `attributes.discNumber` | medium position | `disk_number` | N/A |
| **ISRC** | `external_ids.isrc`³ | N/A | N/A | `attributes.isrc`⁴ | `inc=isrcs` | `isrc` | N/A |
| **Explicit** | `explicit` | N/A | `isExplicit` | `contentRating` | N/A | `explicit_lyrics` | N/A |
| **Release Date** | `album.release_date` | `publishedAt`⁵ | `year` | `attributes.releaseDate` | `first-release-date` | `release_date` | N/A |
| **Genre(s)** | via artist | `topicCategories`⁶ | N/A | `genreNames[]` | `genres[]` | album genre | **tags** |
| **BPM/Tempo** | ~~Audio Features~~³ | N/A | N/A | N/A | N/A | `bpm` | N/A |
| **Popularity** | `popularity`³ | `viewCount` | `views` | N/A | N/A | `rank` | `playcount` |
| **Preview** | `preview_url`⁷ | N/A | N/A | `previews[].url` | N/A | `preview` | N/A |
| **Contributors** | N/A | N/A | N/A | `composerName` | via Work rels | `contributors[]` | N/A |
| **Lyrics** | N/A | N/A | N/A | `hasLyrics` | N/A | N/A | N/A⁸ |
| **Artwork** | `album.images[]` | `thumbnails` | `thumbnails[]` | `artwork` | Cover Art Archive | `album.cover*` | `image[]` |

**Footnotes:**
1. YouTube `channelTitle` is the uploader, not necessarily the performing artist.
2. Only available from `get_album()` in ytmusicapi.
3. **Removed from Spotify Dev Mode in Feb 2026.** Extended Quota only.
4. Only on catalog songs; not `library-songs`.
5. YouTube `publishedAt` is upload date, not music release date.
6. Wikipedia URLs, not structured genre labels.
7. Preview URLs removed for new Spotify apps (late 2024).
8. Last.fm does not provide lyrics; use Musixmatch instead.

---

## 7. Access Restrictions and Developer Warnings Summary

| Issue | Service | Impact |
|-------|---------|--------|
| **ISRC removed from Dev Mode** | Spotify | Feb 2026; must use Extended Quota Mode. **Use Deezer as alternative ISRC source.** |
| **Audio Features/Analysis restricted** | Spotify | New apps (post-Nov 2024) cannot access. **Use ReccoBeats, Deezer BPM, or Essentia.** |
| **Batch endpoints removed** | Spotify | Must fetch tracks individually in Dev Mode. |
| **Search limit reduced** | Spotify | Capped at 10/page in Dev Mode. |
| **Premium required** | Spotify | App owner needs active Premium subscription. |
| **No ML/AI training** | Spotify | Content may not be used for ML/AI model training. |
| **No official YouTube Music API** | YouTube | Must use video-centric API or unofficial ytmusicapi. |
| **Quota system** | YouTube | 10,000 units/day default. |
| **ISRC only on catalog songs** | Apple Music | Must follow `catalog` relationship for library-songs. |
| **Apple Developer Program cost** | Apple Music | Annual fee required. |
| **Rate limit: 1 req/sec** | MusicBrainz | Strict; descriptive User-Agent mandatory. |
| **Community-curated data** | MusicBrainz | Coverage varies; K-pop may have artist credit inconsistencies. |
| **BPM only on individual lookups** | Deezer | Not returned when listing album tracks (need per-track fetch). |
| **ISRC lookup returns single result** | Deezer | Undocumented endpoint; may miss duplicates. |
| **Legacy data only** | AcousticBrainz | No new data since 2022. ~7M recordings covered. |
| **Non-commercial free tier** | Musixmatch | Free tier limited to 2,000 calls/day, 30% lyrics. Commercial requires paid plan. |
| **Unofficial ytmusicapi** | YouTube | Reverse-engineered; can break without notice. |
| **Data provenance unclear** | ReccoBeats | Feature extraction methodology not fully documented. |

---

## 8. Recommendations for MusicElo / Cross-Platform Projects

1. **Use Deezer as your primary ISRC source** — free, no auth, immediate access. For any track, fetch from Deezer to get ISRC + BPM + gain without needing Spotify Extended Quota.

2. **Use MusicBrainz as your metadata backbone** — free, open, ISRC, URL relationships, detailed artist credits. Leverage "member of group" relationships to resolve the TWICE/solo mismatch pattern.

3. **For audio features, layer sources:**
   - Deezer BPM (free, no auth) for tempo
   - ReccoBeats (free, Spotify IDs) for full feature set (valence, danceability, energy, etc.)
   - AcousticBrainz (CC0 legacy data) for key, mood, genre if MBIDs are available
   - Essentia (local analysis) as the ultimate fallback for any track where you have audio files

4. **For genre/mood tags, combine:**
   - Last.fm community tags (best granularity, e.g., "K-pop", "dance pop")
   - Apple Music genreNames (editorial, structured)
   - MusicBrainz genres (controlled vocabulary)
   - Musixmatch primary_genres (structured, with IDs)

5. **Cache ISRCs aggressively** — once obtained, they're permanent identifiers.

6. **Store artist IDs from every platform** — don't rely on name matching alone. Build a cross-reference table: Spotify ID ↔ MBID ↔ Deezer ID ↔ Apple Music ID.

7. **For lyrics data** — Musixmatch is the leading source (14M+ lyrics). Free tier available for non-commercial use.

8. **Monitor Spotify API** — The Feb 2026 changes were significant. No replacement for Audio Features has materialized despite hints from Spotify support in Dec 2024.

---

## 9. References

- Spotify Web API Reference: https://developer.spotify.com/documentation/web-api/reference
- Spotify Feb 2026 Changes: https://developer.spotify.com/documentation/web-api/references/changes/february-2026
- YouTube Data API v3: https://developers.google.com/youtube/v3/docs
- ytmusicapi: https://ytmusicapi.readthedocs.io/
- Apple Music API: https://developer.apple.com/documentation/applemusicapi/
- MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API
- MusicBrainz Artist Credits: https://wiki.musicbrainz.org/Style/Artist_Credits
- Deezer API: https://developers.deezer.com/api
- Deezer Python Client: https://deezer-python.readthedocs.io/
- Last.fm API: https://www.last.fm/api
- AcousticBrainz: https://acousticbrainz.org/
- AcousticBrainz Downloads: https://acousticbrainz.org/download
- Musixmatch API: https://developer.musixmatch.com/
- ReccoBeats: https://reccobeats.com/
- ReccoBeats Audio Features: https://reccobeats.com/docs/apis/get-track-audio-features
- Essentia: https://essentia.upf.edu/
- librosa: https://librosa.org/
- Soundcharts Audio Features API: https://soundcharts.com/en/audio-features-api
- ISRC (ISO 3901): https://musicbrainz.org/doc/ISRC
- Music APIs Collection: https://gist.github.com/0xdevalias/eba698730024674ecae7f43f4c650096
