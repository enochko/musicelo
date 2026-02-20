# MusicElo V3.0 — Spike Validation Sprint: GitHub Documentation Guide

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System  
**Date:** February 2026  
**Author:** Enoch Ko  
**Version:** 0.1

---

## 1. Why Document Spikes in GitHub?

### Portfolio Value

Spike validation scripts in a public repository demonstrate three things that hiring managers and portfolio reviewers look for:

1. **Risk-aware planning.** You identified assumptions that could invalidate your architecture *before* committing to building it. This is the difference between "I built something and it mostly works" and "I systematically validated my technical approach before designing the system."

2. **Hypothesis-driven development.** Each spike has a clear question, expected result, pass/fail criteria, and documented impact on the project if the result is unexpected. This is the scientific method applied to software engineering.

3. **Honest documentation of AI-assisted work.** The spike plan explicitly states that API capabilities were researched by an LLM and required human validation. This shows you understand the limitations of AI-assisted development and take responsibility for verifying its outputs — a nuance that is increasingly valued.

### When Reviewers See This

A portfolio reviewer opening `02-requirements/spikes/` sees:

- A structured test plan that precedes design (process maturity)
- Python scripts that actually call real APIs (hands-on technical skill)
- Results documented with PRD impact analysis (product thinking)
- A clear connection between validation findings and design decisions (end-to-end traceability)

This is substantially more impressive than either "I built a thing" or "I wrote a 50-page document."

---

## 2. What to Commit

### Commit Everything Except Secrets

| Include | Exclude |
|---------|---------|
| `spike-validation-plan.md` (this test plan) | `.env` files with real API keys |
| All `s0X_*.py` scripts | OAuth tokens or refresh tokens |
| `s07_mpnowplaying_prototype/` Xcode project | Apple private keys |
| `spike-validation-results.md` (post-sprint summary) | Raw API responses containing personal library data |
| `.env.example` (template with placeholder values) | |
| `requirements.txt` (Python dependencies) | |
| A `README.md` for the spikes folder | |

### Handling Sensitive Output

Some spike scripts will print raw API responses that may contain your personal data (Spotify library, Apple Music playlists, YouTube Music history). Two approaches:

**Option A — Redact before committing output logs:**
- Keep output in the script's header comment block
- Replace personal data with `[REDACTED]` or generic descriptions
- e.g., "Returns 847 library songs" rather than printing titles

**Option B — Don't commit output logs:**
- Document results in `spike-validation-results.md` in summary form
- Keep raw output locally for your reference
- Scripts demonstrate the *method*; results document captures the *findings*

**Recommendation:** Option B. The scripts show process; the results document shows findings. No need to expose personal library data.

---

## 3. Repository Structure

### Recommended Placement

```
musicelo-v3/
├── README.md
│
├── 01-discovery/
│   └── ...existing files...
│
├── 02-requirements/
│   ├── musicelo-v3-prd-v1_0.md
│   │
│   └── spikes/
│       ├── README.md                          ← Overview + how to run
│       ├── spike-validation-plan.md           ← Full test plan (this companion's parent doc)
│       ├── spike-validation-results.md        ← Post-sprint findings summary
│       ├── requirements.txt                   ← Python deps
│       ├── .env.example                       ← API key template
│       │
│       ├── s01_spotify_content_audit.py
│       ├── s02_deezer_isrc_fetch.py
│       ├── s03_deezer_isrc_lookup.py
│       ├── s04_musicbrainz_twice_audit.py
│       ├── s05_reccobeats_twice.py
│       ├── s06_apple_musickit_auth.py
│       ├── s08_lastfm_tags.py
│       ├── s09_spotify_connect_polling.py
│       ├── s10_ytmusicapi_fetch.py
│       │
│       └── s07_mpnowplaying_prototype/
│           ├── README.md                      ← How to build/run
│           ├── NowPlayingSpike/
│           │   ├── NowPlayingSpikeApp.swift
│           │   ├── ContentView.swift
│           │   └── Info.plist
│           └── NowPlayingSpike.xcodeproj/
│
├── 03-design/
│   └── ...existing files...
│
└── 04-implementation/
    └── (future)
```

### Why Under `02-requirements/` Not `03-design/`

Spikes are pre-design validation — they test whether the requirements' assumptions hold before committing to a design. They are the bridge between "what we think is true" (requirements) and "how we'll build it" (design). Placing them under `02-requirements/` makes this sequence explicit.

If a spike reveals that an API doesn't work as expected, the impact flows *backward* into the PRD (as a v1.1 update), not forward into design. This confirms their position in the requirements phase.

---

## 4. README Template for Spikes Folder

Use this as `02-requirements/spikes/README.md`:

```markdown
# MusicElo v3.0 — API Spike Validation

Pre-design validation of critical API dependencies. These scripts verify that
the architectural assumptions in the [PRD v1.0](../musicelo-v3-prd-v1_0.md)
hold against real API responses.

## Why?

The PRD's metadata enrichment strategy relies on 6+ external APIs. API
capabilities were initially researched through documentation review (with AI
assistance). These spikes validate critical-path assumptions before committing
to design — particularly for APIs where:

- Documentation may be stale (Spotify post-Feb 2026 restrictions)
- Endpoints are undocumented (Deezer ISRC lookup)
- Coverage for K-pop is unverified (MusicBrainz, ReccoBeats)
- Setup complexity is unknown (Apple MusicKit)
- Platform behaviour is assumed (iOS MPNowPlayingInfoCenter)

## Spikes

| ID | Script | Status | Result |
|----|--------|--------|--------|
| S-01 | `s01_spotify_content_audit.py` | ⬜ | — |
| S-02 | `s02_deezer_isrc_fetch.py` | ⬜ | — |
| S-03 | `s03_deezer_isrc_lookup.py` | ⬜ | — |
| S-04 | `s04_musicbrainz_twice_audit.py` | ⬜ | — |
| S-05 | `s05_reccobeats_twice.py` | ⬜ | — |
| S-06 | `s06_apple_musickit_auth.py` | ⬜ | — |
| S-07 | `s07_mpnowplaying_prototype/` | ⬜ | — |
| S-08 | `s08_lastfm_tags.py` | ⬜ | — |
| S-09 | `s09_spotify_connect_polling.py` | ⬜ | — |
| S-10 | `s10_ytmusicapi_fetch.py` | ⬜ | — |

Status: ⬜ Not started · 🔄 In progress · ✅ Pass · ⚠️ Partial · ❌ Fail

## How to Run

### Prerequisites

- Python 3.10+
- Xcode 15+ (for S-07 only)
- Copy `.env.example` to `.env` and fill in your API keys

### Setup

```bash
cd 02-requirements/spikes
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Running a Spike

```bash
python s02_deezer_isrc_fetch.py
```

Each script prints results to stdout and includes a summary comment block
at the top of the file (updated after execution).

## Results

See [spike-validation-results.md](./spike-validation-results.md) for the
consolidated findings and PRD impact analysis.

## Full Test Plan

See [spike-validation-plan.md](./spike-validation-plan.md) for detailed
test specifications, pass/fail criteria, and decision framework.
```

---

## 5. `.env.example` Template

```env
# MusicElo v3.0 — Spike Validation API Keys
# Copy this file to .env and fill in your values.
# NEVER commit .env to version control.

# Spotify (S-01, S-09)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
# After OAuth flow, paste your access token here:
SPOTIFY_ACCESS_TOKEN=

# Apple Music (S-06)
APPLE_TEAM_ID=your_team_id
APPLE_KEY_ID=your_key_id
APPLE_PRIVATE_KEY_PATH=./AuthKey_XXXXXXXXXX.p8
# After MusicKit auth, paste user token here:
APPLE_MUSIC_USER_TOKEN=

# Last.fm (S-08)
LASTFM_API_KEY=your_api_key

# YouTube Music (S-10)
# ytmusicapi uses browser cookie auth — run `ytmusicapi oauth` to set up
YTMUSIC_AUTH_FILE=./oauth.json

# Deezer (S-02, S-03) — no auth needed
# ReccoBeats (S-05) — no auth needed
# MusicBrainz (S-04) — no auth needed (User-Agent required in script)
```

---

## 6. `requirements.txt`

```
requests>=2.31.0
python-dotenv>=1.0.0
PyJWT>=2.8.0        # For Apple MusicKit JWT generation
cryptography>=41.0   # For Apple MusicKit key handling
ytmusicapi>=1.5.0    # For S-10
tabulate>=0.9.0      # For formatted console output
```

---

## 7. Commit Strategy

### Recommended Commit Sequence

**Commit 1 — Plan and scaffolding (before running any spikes):**
```
feat(spikes): add spike validation plan and scaffolding

- spike-validation-plan.md: full test plan with 10 spikes
- README.md: spikes folder overview
- .env.example: API key template
- requirements.txt: Python dependencies
```

This commit shows the *plan* existed before execution. Portfolio reviewers can see the planning artefact independent of results.

**Commits 2–N — One per spike completed:**
```
feat(spikes): S-02 Deezer ISRC fetch — PASS (9/10 tracks)

- s02_deezer_isrc_fetch.py: test script with result summary
- Updated spikes/README.md status table
```

Individual commits per spike create a clear trail of incremental validation.

**Final commit — Results summary:**
```
docs(spikes): spike validation results and PRD impact analysis

- spike-validation-results.md: consolidated findings
- Updated spike-validation-plan.md if any amendments
- Updated PRD reference (if v1.1 changes needed)
```

### `.gitignore` Additions

Add to the repository's `.gitignore`:

```gitignore
# Spike validation secrets
02-requirements/spikes/.env
02-requirements/spikes/oauth.json
02-requirements/spikes/*.p8
02-requirements/spikes/venv/

# Xcode build artifacts
02-requirements/spikes/s07_mpnowplaying_prototype/build/
02-requirements/spikes/s07_mpnowplaying_prototype/*.xcworkspace
02-requirements/spikes/s07_mpnowplaying_prototype/DerivedData/
```

---

## 8. Spike Results Template

After completing all spikes, use this template for `spike-validation-results.md`:

```markdown
# MusicElo v3.0 — Spike Validation Results

**Sprint dates:** 2026-0X-XX to 2026-0X-XX  
**Total time invested:** XX hours across X sessions  

## Summary

| ID | Spike | Result | PRD Impact |
|----|-------|--------|------------|
| S-01 | Spotify Content Audit | ✅/⚠️/❌ | None / [description] |
| S-02 | Deezer ISRC Fetch | ✅/⚠️/❌ | None / [description] |
| ... | ... | ... | ... |

## Detailed Findings

### S-01: Spotify Web API Content Audit
**Result:** [PASS / PARTIAL / FAIL]  
**Key findings:**
- [Finding 1]
- [Finding 2]

**PRD impact:** [None / Description of changes needed]

### S-02: Deezer ISRC Fetch
...

## PRD v1.1 Changes Required

[List any PRD changes triggered by spike findings, or state "No changes required."]

## Updated Risk Assessment

[Any changes to the Technical Risks table in PRD §9]
```

---

## 9. What This Communicates to Portfolio Reviewers

When a technical interviewer or hiring manager browses the repository, the spikes folder tells a story:

1. **`spike-validation-plan.md`** — "I identified which assumptions were load-bearing and needed validation before design. I explicitly called out that AI-assisted research needed human verification."

2. **`s0X_*.py` scripts** — "I can write code that calls real APIs, handle auth flows, and interpret responses. These aren't theoretical — they ran against production APIs."

3. **`spike-validation-results.md`** — "I documented what I found, assessed the impact on my plans, and made data-driven decisions about whether to proceed, pivot, or de-scope."

4. **The commit history** — "Plan was committed before results. Each spike was completed and documented independently. Findings fed back into requirements."

This is the kind of structured, risk-aware, evidence-based approach that distinguishes senior practitioners from juniors. It's not about the code — it's about the methodology.

---

## 10. Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-16 | 0.1 | Initial GitHub documentation guide | Enoch Ko |
