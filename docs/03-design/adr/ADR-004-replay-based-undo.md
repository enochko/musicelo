# ADR-004: Replay-Based Undo (Not Delta Reversal)

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** PRD v0.2 BR-006, CLAUDE.md §Business Rules BR-006  

---

## Context and Problem Statement

MusicElo supports undoing a comparison within a 10-second window (FR-203). After a
comparison is undone, both songs' Glicko-2 ratings must be restored to their pre-comparison
state. There are two approaches to achieving this: store the delta and reverse it, or
replay all remaining comparisons from scratch.

## Decision Drivers

- Glicko-2 is a non-linear algorithm — the rating change from a comparison depends on
  the current rating, rating deviation, and volatility of both songs at the time of the
  comparison; it is not a simple additive delta
- If comparison C2 is undone, comparison C3 was calculated using ratings that incorporated
  C2's outcome; those ratings no longer exist after the undo; C3's stored "before" values
  are now wrong
- The `comparisons` table stores full before/after snapshots (μ, RD, σ for both songs);
  this audit trail is the input to replay
- Delta reversal is only exactly correct when undoing the most recent comparison for
  both songs simultaneously; any other case produces approximate results
- Ranking integrity (see ADR-002) demands that ratings are always exactly correct, not
  approximately correct

## Considered Options

| Option | Description |
|--------|-------------|
| A — Delta reversal | Store rating change at comparison time; subtract it on undo |
| B — Snapshot restore | Store full before-state at comparison time; restore it on undo |
| C — Full replay | Soft-delete undone comparison; replay all remaining comparisons from defaults |
| D — Partial replay | Replay only comparisons involving the two affected songs |

## Decision Outcome

**Chosen option: C — Full replay**

When a comparison is undone, it is soft-deleted (`is_undone = true`). All non-undone
comparisons are then replayed in chronological order from default initial ratings
(1500/350/0.06) to produce correct current ratings for all affected songs.

Option D (partial replay) was considered as an optimisation but rejected: determining
the correct "affected song" boundary is complex when songs share comparison history
with third songs that are themselves involved in other comparisons. Full replay is
unambiguously correct and the comparison volume in a personal system (hundreds, not
millions) makes it computationally acceptable.

## Consequences

**Positive:**
- Mathematically exact — replayed ratings are identical to ratings that would have
  resulted from never having made the undone comparison
- Auditable — the full comparison history in `comparisons` is the single source of truth;
  current ratings can always be reconstructed from it
- Simplifies the data model — no need to store deltas or manage snapshot restoration logic
- Test T-032 can verify correctness by comparing replay output to forward calculation

**Negative:**
- Replay time scales with total comparison count — for a library with thousands of
  comparisons, a single undo triggers a full recalculation; acceptable at current scale,
  may need optimisation later
- More complex to implement correctly than delta reversal — the replay function must
  handle edge cases (undo of first comparison, multiple undos, re-vote)

**Implementation note:**
`core/glicko2.py` must expose a pure `replay_comparisons(history: list[Comparison])`
function. `comparisons/service.py` calls this after setting `is_undone = true`. The
replay function takes only non-undone comparisons ordered by `compared_at` ascending.
Tests T-030 to T-039 cover the full undo/replay behaviour.
