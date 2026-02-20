# ADR-003: Immediate Glicko-2 Updates (No Rating Period Batching)

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** PRD v0.2 BR-005, CLAUDE.md §Business Rules BR-005  

---

## Context and Problem Statement

The Glicko-2 algorithm was designed by Mark Glickman to be applied in discrete rating
periods: comparisons are accumulated over a period (e.g. one month), then all ratings
are updated simultaneously at the end of the period. This batching approach is how Glicko-2
is used in chess and other competitive systems.

MusicElo must decide whether to follow this design (batched updates) or update ratings
immediately after each comparison.

## Decision Drivers

- MusicElo is a single-user personal system, not a multi-player competitive environment;
  the fairness rationale for batching (all players updated simultaneously) does not apply
- The user expects to see updated rankings immediately after making a comparison —
  a delayed update creates a confusing experience where comparisons appear to have no effect
- Batching introduces complexity: the system must track "pending" comparisons separately
  from "applied" comparisons, and manage period boundaries
- Rating deviation (RD) in Glicko-2 increases between rating periods to reflect uncertainty
  from inactivity — in a single-user system with continuous use, this mechanism is less
  meaningful
- The undo/replay mechanism (ADR-004) requires a clear, ordered history of applied
  comparisons; batching would complicate this

## Considered Options

| Option | Description |
|--------|-------------|
| A — Immediate update | Each comparison immediately updates both songs' `glicko_ratings` |
| B — Daily batching | Comparisons accumulate during the day; ratings updated at midnight |
| C — Standard rating period | Follow Glicko-2 design: accumulate for ~1 month, update at period end |
| D — Configurable period | Allow the user to choose their rating period length |

## Decision Outcome

**Chosen option: A — Immediate update**

Each comparison triggers an immediate call to `glicko2.update_ratings()` and the result
is written to `glicko_ratings` before the API response is returned. Rankings reflect the
latest state at all times.

## Consequences

**Positive:**
- Immediate feedback loop — user sees ranking change after every comparison
- Simpler data model — no "pending" state, no period boundary logic
- Undo/replay operates on a clean linear history of applied comparisons
- RD still decreases naturally as comparisons accumulate, providing increasing confidence

**Negative:**
- Deviates from Glicko-2's designed usage; some statistical properties of the algorithm
  (specifically around RD inflation between periods) are not used
- In theory, a burst of comparisons in one session could cause larger swings than a
  batched model would produce — though in practice this is desirable behaviour for a
  personal system

**Implementation note:**
Encoded in CLAUDE.md as a DO NOT VIOLATE constraint: "Glicko-2 updates are immediate —
no batching or deferred calculation." `comparisons/service.py` must call
`glicko2.update_ratings()` synchronously within the same transaction as the
`comparisons` row insert.
