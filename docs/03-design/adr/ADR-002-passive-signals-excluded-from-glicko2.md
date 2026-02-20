# ADR-002: Passive Listening Signals Excluded from Glicko-2 Calculations

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** PRD v0.2 BR-008, CLAUDE.md §Business Rules BR-008  

---

## Context and Problem Statement

MusicElo captures passive listening signals — song completions, skips, replays, play
percentage — from the streaming app via `MPNowPlayingInfoCenter`. These signals carry
preference information: completing a song suggests positive sentiment, skipping suggests
negative. The question is whether to use these signals to directly update Glicko-2 ratings.

## Decision Drivers

- Passive signals are ambiguous: a skip may indicate dislike, or that the user is in a
  hurry, driving in traffic, or heard the song recently; a completion may indicate active
  enjoyment or passive background listening with no engagement
- Glicko-2 is designed for head-to-head comparisons with explicit outcomes; feeding it
  single-signal observations without an opponent violates the model's assumptions
- Ranking integrity is the core value proposition of MusicElo — if users cannot trust that
  ratings reflect deliberate preferences, the system loses its reason to exist
- The 90/10 passive/active design means passive signals are the majority data source;
  polluting Glicko-2 with them would make ratings drift based on listening patterns
  rather than preference strength

## Considered Options

| Option | Description |
|--------|-------------|
| A — Full exclusion | Passive signals stored in `play_events` only; never modify `glicko_ratings` |
| B — Weighted injection | Passive signals treated as fractional comparison outcomes (e.g. skip = 0.1 loss vs. average) |
| C — Separate passive rating | Maintain a second rating system for passive signals; blend with Glicko-2 for final rank |
| D — Context modifiers | Passive signals adjust a per-song context weight but not the Glicko-2 score itself |

## Decision Outcome

**Chosen option: A — Full exclusion**

Passive signals are stored in `play_events` for future analysis (playlist generation,
context-aware recommendations) but never modify `glicko_ratings`. Only explicit pairwise
comparisons via the active comparison UI update Glicko-2 scores.

## Consequences

**Positive:**
- Ranking integrity is unambiguous — ratings reflect only deliberate preference choices
- Simplifies the comparison recording service: one clear path to score updates
- `play_events` data remains available for ML-based playlist generation without
  contaminating the ranking system
- Easy to explain to a portfolio reviewer: "ratings = comparisons only"

**Negative:**
- Songs with few comparisons will have high rating deviation (uncertainty) for longer;
  passive signals could theoretically accelerate convergence
- A user who never actively compares two songs will never have them ranked relative to
  each other, even if they have strong skip/complete patterns between them

**Implementation note:**
This rule is encoded in CLAUDE.md as a DO NOT VIOLATE constraint. Any code path in
`comparisons/service.py` that processes play events must explicitly not call
`glicko2.update_ratings()`. Test T-025 enforces this.
