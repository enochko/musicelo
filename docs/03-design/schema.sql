-- ============================================================================
-- MusicElo v3.0 — Database Schema (PostgreSQL / Supabase)
-- Version: 0.2
-- Date: February 2026
-- Aligned with: prd-v0.2
--
-- 22 tables across 6 domains:
--   1. Core Library          (artists, albums, songs, join tables)
--   2. Glicko-2 / App        (ratings, comparisons, play events, snapshots)
--   3. Platform Cross-Refs    (links to Spotify/Apple/MB/Deezer/YT IDs)
--   4. Raw Source Cache        (verbatim API JSON responses)
--   5. Audio & Tags            (structured features + multi-source tags)
--   6. System                  (merge audit log)
-- ============================================================================


-- ============================================================================
-- 1. CORE LIBRARY
-- ============================================================================

-- 1a. Artists ----------------------------------------------------------------

CREATE TABLE artists (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    name_normalized   TEXT,
    sort_name         TEXT,
    artist_type       TEXT CHECK (artist_type IN ('person','group','orchestra','other')),
    country           TEXT,                -- ISO 3166-1 alpha-2
    disambiguation    TEXT,
    image_url         TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_artists_name_norm ON artists(name_normalized);

-- 1b. Artist group membership ------------------------------------------------

CREATE TABLE artist_groups (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_artist_id  UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    group_artist_id   UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    active_from       DATE,
    active_until      DATE,               -- NULL = still active
    role              TEXT DEFAULT 'member'
                      CHECK (role IN ('member','former_member','guest','collaborator')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (group_artist_id, member_artist_id)
);

CREATE INDEX idx_artist_groups_member ON artist_groups(member_artist_id);

-- 1c. Albums -----------------------------------------------------------------

CREATE TABLE albums (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT NOT NULL,
    title_normalized  TEXT,
    album_type        TEXT CHECK (album_type IN ('album','single','ep','compilation','live','remix','other')),
    release_date      TEXT,               -- YYYY-MM-DD / YYYY-MM / YYYY
    release_date_precision TEXT CHECK (release_date_precision IN ('day','month','year')),
    total_tracks      INTEGER,
    total_discs       INTEGER DEFAULT 1,
    upc               TEXT,
    label             TEXT,
    image_url         TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_albums_title_norm ON albums(title_normalized);
CREATE INDEX idx_albums_upc ON albums(upc) WHERE upc IS NOT NULL;

-- 1d. Album ↔ Artist (M:N) ---------------------------------------------------

CREATE TABLE album_artists (
    album_id          UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    artist_id         UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    credit_order      INTEGER NOT NULL DEFAULT 0,
    credited_as       TEXT,
    PRIMARY KEY (album_id, artist_id, credit_order)
);

-- 1e. Songs — the central entity ---------------------------------------------
--     Combines PRD "Song" entity with normalized relationships.
--     canonical_id implements PRD BR-002 (alias → canonical).

CREATE TABLE songs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_id      UUID REFERENCES songs(id) ON DELETE SET NULL,
                      -- NULL = this IS the canonical song
                      -- Non-NULL = alias pointing to canonical (PRD BR-002)
    title             TEXT NOT NULL,
    title_normalized  TEXT,
    album_id          UUID REFERENCES albums(id) ON DELETE SET NULL,
    track_number      INTEGER,
    disc_number       INTEGER DEFAULT 1,
    duration_ms       INTEGER,
    isrc              TEXT,               -- indexed, not unique (see design doc §1.3)
    language          TEXT CHECK (language IN ('korean','japanese','english','other')),
    track_type        TEXT CHECK (track_type IN ('title_track','b_side','ost','special')),
    explicit          BOOLEAN DEFAULT FALSE,
    is_medley         BOOLEAN DEFAULT FALSE,
    release_date      TEXT,               -- track-level override
    performer_tags    TEXT[],             -- PRD FR-106: actual performers e.g. {'Nayeon','Momo'}
    visual_notes      TEXT,               -- PRD FR-106: TTT refs, concert moments, YT links
    custom_tags       TEXT[],             -- PRD FR-106: emotional/context tags
    audio_features    JSONB,              -- PRD FR-106: seed data from Spotify/Apple Music
    preview_url       TEXT,
    image_url         TEXT,
    merge_confidence  REAL,
    merge_method      TEXT CHECK (merge_method IN ('isrc','heuristic','manual','single_source')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_songs_isrc ON songs(isrc) WHERE isrc IS NOT NULL;
CREATE INDEX idx_songs_title_norm ON songs(title_normalized);
CREATE INDEX idx_songs_canonical ON songs(canonical_id) WHERE canonical_id IS NOT NULL;
CREATE INDEX idx_songs_album ON songs(album_id, disc_number, track_number);
CREATE INDEX idx_songs_language ON songs(language);
CREATE INDEX idx_songs_track_type ON songs(track_type);
CREATE INDEX idx_songs_performer_tags ON songs USING GIN(performer_tags);
CREATE INDEX idx_songs_custom_tags ON songs USING GIN(custom_tags);
CREATE INDEX idx_songs_audio_features ON songs USING GIN(audio_features);

-- 1f. Song ↔ Artist (M:N with roles) -----------------------------------------

CREATE TABLE song_artists (
    song_id           UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    artist_id         UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    credit_order      INTEGER NOT NULL DEFAULT 0,
    credit_role       TEXT NOT NULL DEFAULT 'primary'
                      CHECK (credit_role IN (
                          'primary','featured','remix','producer',
                          'composer','writer','arranger','performer'
                      )),
    credited_as       TEXT,
    PRIMARY KEY (song_id, artist_id, credit_role)
);

CREATE INDEX idx_song_artists_artist ON song_artists(artist_id);

-- 1g. Song relationships (PRD FR-105) ----------------------------------------

CREATE TABLE song_relationships (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_a_id         UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    song_b_id         UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL
                      CHECK (relationship_type IN (
                          'translation','remix','live_recording',
                          'acoustic','solo_version','medley_component'
                      )),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (song_a_id, song_b_id, relationship_type)
);

CREATE INDEX idx_song_rels_b ON song_relationships(song_b_id);


-- ============================================================================
-- 2. GLICKO-2 RATING SYSTEM & APP TABLES
-- ============================================================================

-- 2a. Glicko-2 ratings (one per canonical song — PRD BR-002) -----------------

CREATE TABLE glicko_ratings (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_id           UUID NOT NULL UNIQUE REFERENCES songs(id) ON DELETE CASCADE,
                      -- Enforce: only canonical songs (canonical_id IS NULL) get ratings.
                      -- Application-level check; can add CHECK or trigger if desired.
    rating            DOUBLE PRECISION NOT NULL DEFAULT 1500.0,
    rating_deviation  DOUBLE PRECISION NOT NULL DEFAULT 350.0,
    volatility        DOUBLE PRECISION NOT NULL DEFAULT 0.06,
    comparison_count  INTEGER NOT NULL DEFAULT 0,
    last_compared_at  TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_glicko_ratings_leaderboard ON glicko_ratings(rating DESC);

-- 2b. Comparisons (full audit trail — PRD FR-205, BR-006) --------------------

CREATE TABLE comparisons (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_a_id         UUID NOT NULL REFERENCES songs(id),
    song_b_id         UUID NOT NULL REFERENCES songs(id),
    outcome           DOUBLE PRECISION NOT NULL,
                      -- 0.0 = B wins strong, 0.25 = B wins slight
                      -- 0.5 = draw, 0.75 = A wins slight, 1.0 = A wins strong
                      -- From Song A's perspective (PRD FR-201)

    -- Rating snapshots before
    song_a_rating_before      DOUBLE PRECISION,
    song_a_rd_before          DOUBLE PRECISION,
    song_a_volatility_before  DOUBLE PRECISION,
    song_b_rating_before      DOUBLE PRECISION,
    song_b_rd_before          DOUBLE PRECISION,
    song_b_volatility_before  DOUBLE PRECISION,

    -- Rating snapshots after
    song_a_rating_after       DOUBLE PRECISION,
    song_a_rd_after           DOUBLE PRECISION,
    song_a_volatility_after   DOUBLE PRECISION,
    song_b_rating_after       DOUBLE PRECISION,
    song_b_rd_after           DOUBLE PRECISION,
    song_b_volatility_after   DOUBLE PRECISION,

    source            TEXT NOT NULL
                      CHECK (source IN (
                          'mobile_passive','mobile_focused',
                          'desktop_passive','desktop_focused'
                      )),
    context           JSONB,              -- {"device","carplay","focus_mode","location_zone"}
    response_time_ms  INTEGER,
    is_undone         BOOLEAN NOT NULL DEFAULT FALSE,   -- PRD BR-006 soft delete
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comparisons_song_a ON comparisons(song_a_id, created_at);
CREATE INDEX idx_comparisons_song_b ON comparisons(song_b_id, created_at);
CREATE INDEX idx_comparisons_created ON comparisons(created_at);
CREATE INDEX idx_comparisons_active ON comparisons(created_at)
    WHERE is_undone = FALSE;             -- partial index for active-only queries

-- 2c. Play events (passive listening — PRD FR-400, BR-008) -------------------

CREATE TABLE play_events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_id           UUID NOT NULL REFERENCES songs(id),
    started_at        TIMESTAMPTZ NOT NULL,
    duration_played_seconds INTEGER,
    play_percentage   REAL,               -- 0.0–1.0
    completed         BOOLEAN,
    skipped           BOOLEAN,
    replayed          BOOLEAN,
    device_type       TEXT CHECK (device_type IN ('iphone','mac','carplay')),
    carplay_active    BOOLEAN,
    focus_mode        TEXT,               -- 'Driving', 'Do Not Disturb', etc.
    location_zone     TEXT,               -- 'Home', 'Office', 'Uni', 'Commute'
    workout_active    BOOLEAN,
    playback_platform TEXT CHECK (playback_platform IN ('spotify','youtube_music','apple_music'))
);

CREATE INDEX idx_play_events_song ON play_events(song_id, started_at);
CREATE INDEX idx_play_events_time ON play_events(started_at);

-- 2d. Ranking snapshots (monthly — PRD FR-206, BR-009) -----------------------

CREATE TABLE ranking_snapshots (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date     DATE NOT NULL UNIQUE,
    snapshot_data     JSONB NOT NULL,
                      -- [{song_id, title, rating, rd, volatility, rank, comparison_count}, ...]
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2e. Playlist rules (PRD PlaylistRule) --------------------------------------

CREATE TABLE playlist_rules (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    rule_type         TEXT CHECK (rule_type IN ('threshold_rank','threshold_rating','filter')),
    rule_definition   JSONB,              -- {"top_n":50} or {"language":"korean","track_type":"title_track","top_n":20}
    platform_playlist_ids JSONB,          -- {"spotify":"...","ytm":"...","apple_music":"..."}
    auto_sync         BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2f. Glicko parameter history (PRD FR-200) ----------------------------------

CREATE TABLE glicko_parameters (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initial_rating    DOUBLE PRECISION NOT NULL DEFAULT 1500.0,
    initial_rd        DOUBLE PRECISION NOT NULL DEFAULT 350.0,
    initial_volatility DOUBLE PRECISION NOT NULL DEFAULT 0.06,
    system_constant_tau DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    outcome_strong    DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    outcome_slight    DOUBLE PRECISION NOT NULL DEFAULT 0.75,
    outcome_equal     DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    active_from       TIMESTAMPTZ NOT NULL DEFAULT now(),
    active_until      TIMESTAMPTZ,        -- NULL = currently active
    notes             TEXT
);

-- Seed default parameters
INSERT INTO glicko_parameters (
    initial_rating, initial_rd, initial_volatility, system_constant_tau,
    outcome_strong, outcome_slight, outcome_equal, active_from, notes
) VALUES (
    1500.0, 350.0, 0.06, 0.5,
    1.0, 0.75, 0.5, now(),
    'Default Glicko-2 parameters per PRD FR-200'
);


-- ============================================================================
-- 3. PLATFORM CROSS-REFERENCES
-- ============================================================================

CREATE TABLE platform_song_ids (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_id           UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    platform_uri      TEXT,
    match_method      TEXT CHECK (match_method IN ('isrc','heuristic','manual','api_relationship')),
    match_confidence  REAL,
    last_verified     TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, platform_id)
);

CREATE INDEX idx_platform_songs_song ON platform_song_ids(song_id);

CREATE TABLE platform_artist_ids (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artist_id         UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    platform_url      TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, platform_id)
);

CREATE INDEX idx_platform_artists_artist ON platform_artist_ids(artist_id);

CREATE TABLE platform_album_ids (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    album_id          UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    platform_url      TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, platform_id)
);

CREATE INDEX idx_platform_albums_album ON platform_album_ids(album_id);


-- ============================================================================
-- 4. RAW SOURCE CACHE
-- ============================================================================

CREATE TABLE source_cache_tracks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    response_json     JSONB NOT NULL,     -- TOAST auto-compresses
    fetched_at        TIMESTAMPTZ NOT NULL,
    api_endpoint      TEXT,
    http_status       INTEGER,
    is_stale          BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_src_cache_tracks_lookup ON source_cache_tracks(platform, platform_id);
CREATE INDEX idx_src_cache_tracks_fetched ON source_cache_tracks(fetched_at);

CREATE TABLE source_cache_albums (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    response_json     JSONB NOT NULL,
    fetched_at        TIMESTAMPTZ NOT NULL,
    api_endpoint      TEXT,
    http_status       INTEGER,
    is_stale          BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_src_cache_albums_lookup ON source_cache_albums(platform, platform_id);

CREATE TABLE source_cache_artists (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform          TEXT NOT NULL,
    platform_id       TEXT NOT NULL,
    response_json     JSONB NOT NULL,
    fetched_at        TIMESTAMPTZ NOT NULL,
    api_endpoint      TEXT,
    http_status       INTEGER,
    is_stale          BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_src_cache_artists_lookup ON source_cache_artists(platform, platform_id);


-- ============================================================================
-- 5. AUDIO FEATURES & TAGS
-- ============================================================================

-- 5a. Structured audio features (queryable supplement to songs.audio_features)

CREATE TABLE audio_features (
    song_id           UUID PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,
    bpm               REAL,
    bpm_source        TEXT,
    key_pitch         INTEGER CHECK (key_pitch BETWEEN 0 AND 11),
    mode              INTEGER CHECK (mode IN (0, 1)),
    key_source        TEXT,
    time_signature    INTEGER,
    loudness_db       REAL,
    energy            REAL CHECK (energy BETWEEN 0.0 AND 1.0),
    valence           REAL CHECK (valence BETWEEN 0.0 AND 1.0),
    danceability      REAL CHECK (danceability BETWEEN 0.0 AND 1.0),
    acousticness      REAL CHECK (acousticness BETWEEN 0.0 AND 1.0),
    instrumentalness  REAL CHECK (instrumentalness BETWEEN 0.0 AND 1.0),
    speechiness       REAL CHECK (speechiness BETWEEN 0.0 AND 1.0),
    liveness          REAL CHECK (liveness BETWEEN 0.0 AND 1.0),
    primary_source    TEXT,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5b. Multi-source tags (genre, mood, style) ---------------------------------

CREATE TABLE song_tags (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_id           UUID NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    tag_name          TEXT NOT NULL,
    tag_category      TEXT CHECK (tag_category IN ('genre','mood','style','era','theme','other')),
    weight            REAL,
    source            TEXT NOT NULL,
    source_weight     INTEGER,
    UNIQUE (song_id, tag_name, source)
);

CREATE INDEX idx_song_tags_song ON song_tags(song_id);
CREATE INDEX idx_song_tags_name ON song_tags(tag_name);


-- ============================================================================
-- 6. SYSTEM
-- ============================================================================

CREATE TABLE merge_log (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type       TEXT NOT NULL CHECK (entity_type IN ('song','artist','album')),
    entity_id         UUID NOT NULL,
    action            TEXT NOT NULL CHECK (action IN ('created','merged','split','updated','field_override','deleted')),
    source_platform   TEXT,
    source_platform_id TEXT,
    details           JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_merge_log_entity ON merge_log(entity_type, entity_id);
CREATE INDEX idx_merge_log_time ON merge_log(created_at);


-- ============================================================================
-- VIEWS
-- ============================================================================

-- Full song detail with primary artist and album (most common query pattern)
CREATE VIEW v_song_detail AS
SELECT
    s.id              AS song_id,
    s.title,
    s.track_number,
    s.disc_number,
    s.duration_ms,
    s.isrc,
    s.language,
    s.track_type,
    s.explicit,
    s.is_medley,
    s.performer_tags,
    s.custom_tags,
    s.canonical_id,
    a.id              AS album_id,
    a.title           AS album_title,
    a.album_type,
    a.image_url       AS album_image_url,
    COALESCE(s.release_date, a.release_date) AS release_date,
    ar.id             AS primary_artist_id,
    ar.name           AS primary_artist_name,
    ar.artist_type,
    COALESCE(s.image_url, a.image_url) AS image_url
FROM songs s
LEFT JOIN albums a ON s.album_id = a.id
LEFT JOIN song_artists sa ON sa.song_id = s.id
    AND sa.credit_role = 'primary' AND sa.credit_order = 0
LEFT JOIN artists ar ON sa.artist_id = ar.id;

-- Leaderboard: canonical songs ranked by Glicko-2 rating
CREATE VIEW v_leaderboard AS
SELECT
    s.id              AS song_id,
    s.title,
    s.language,
    s.track_type,
    ar.name           AS artist_name,
    a.title           AS album_title,
    gr.rating,
    gr.rating_deviation,
    gr.volatility,
    gr.comparison_count,
    RANK() OVER (ORDER BY gr.rating DESC) AS rank
FROM glicko_ratings gr
JOIN songs s ON gr.song_id = s.id
LEFT JOIN song_artists sa ON sa.song_id = s.id
    AND sa.credit_role = 'primary' AND sa.credit_order = 0
LEFT JOIN artists ar ON sa.artist_id = ar.id
LEFT JOIN albums a ON s.album_id = a.id
WHERE s.canonical_id IS NULL;            -- only canonical songs

-- Song with all platform IDs pivoted
CREATE VIEW v_song_platforms AS
SELECT
    s.id              AS song_id,
    s.title,
    s.isrc,
    MAX(CASE WHEN p.platform = 'spotify' THEN p.platform_id END)       AS spotify_id,
    MAX(CASE WHEN p.platform = 'apple_music' THEN p.platform_id END)   AS apple_music_id,
    MAX(CASE WHEN p.platform = 'musicbrainz' THEN p.platform_id END)   AS musicbrainz_id,
    MAX(CASE WHEN p.platform = 'deezer' THEN p.platform_id END)        AS deezer_id,
    MAX(CASE WHEN p.platform = 'youtube' THEN p.platform_id END)       AS youtube_id,
    MAX(CASE WHEN p.platform = 'musixmatch' THEN p.platform_id END)    AS musixmatch_id
FROM songs s
LEFT JOIN platform_song_ids p ON p.song_id = s.id
GROUP BY s.id, s.title, s.isrc;

-- Song with structured audio features and top tags
CREATE VIEW v_song_features AS
SELECT
    s.id              AS song_id,
    s.title,
    af.bpm,
    af.key_pitch,
    af.mode,
    af.energy,
    af.valence,
    af.danceability,
    af.acousticness,
    af.instrumentalness,
    af.loudness_db,
    STRING_AGG(st.tag_name, ', ' ORDER BY st.weight DESC) AS top_tags
FROM songs s
LEFT JOIN audio_features af ON af.song_id = s.id
LEFT JOIN song_tags st ON st.song_id = s.id AND st.weight >= 0.3
GROUP BY s.id, s.title,
         af.bpm, af.key_pitch, af.mode, af.energy, af.valence,
         af.danceability, af.acousticness, af.instrumentalness, af.loudness_db;

-- Current vs. previous month ranking comparison (PRD FR-602)
-- Usage: SELECT * FROM v_rank_change WHERE prev_snapshot = '<last_month_date>';
CREATE VIEW v_rank_change AS
SELECT
    lb.song_id,
    lb.title,
    lb.artist_name,
    lb.rank AS current_rank,
    lb.rating AS current_rating,
    (snap.elem->>'rank')::INTEGER AS previous_rank,
    lb.rank - (snap.elem->>'rank')::INTEGER AS rank_change
FROM v_leaderboard lb
LEFT JOIN LATERAL (
    SELECT elem
    FROM ranking_snapshots rs,
         jsonb_array_elements(rs.snapshot_data) AS elem
    WHERE rs.snapshot_date = (
        SELECT MAX(snapshot_date) FROM ranking_snapshots
    )
    AND (elem->>'song_id')::UUID = lb.song_id
    LIMIT 1
) snap ON TRUE;


-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_artists_updated_at
    BEFORE UPDATE ON artists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_albums_updated_at
    BEFORE UPDATE ON albums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_songs_updated_at
    BEFORE UPDATE ON songs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_glicko_ratings_updated_at
    BEFORE UPDATE ON glicko_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_playlist_rules_updated_at
    BEFORE UPDATE ON playlist_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- SCHEMA SUMMARY
-- ============================================================================
-- Tables:  22
-- Views:    4 (v_song_detail, v_leaderboard, v_song_platforms, v_song_features)
--           + 1 analytical (v_rank_change)
-- Indexes: 28
-- Triggers: 5 (auto updated_at)
-- Functions: 1 (update_updated_at)
-- ============================================================================
