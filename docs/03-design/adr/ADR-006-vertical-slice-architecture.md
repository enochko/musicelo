# ADR-006: Vertical Slice Architecture (Not Layered)

**Date:** 2026-02  
**Status:** Accepted  
**Deciders:** Enoch Ko  
**Aligned with:** backend-architecture.md §2, CLAUDE.md §Repository Structure  

---

## Context and Problem Statement

The MusicElo Python backend needs a folder structure for organising code. The two
conventional approaches are layered architecture (group by technical role: models/,
services/, routes/) and vertical slice architecture (group by feature: songs/,
comparisons/, rankings/).

This project uses AI-assisted development heavily. The chosen structure will determine
how much context an AI agent needs to load when working on a feature, and how easy it
is to bound the scope of a single task.

## Decision Drivers

- AI agents working on a feature need to read models, service logic, and route handlers
  simultaneously; layered architecture scatters these across three directories
- Vertical slices mean all code for a feature lives in one directory — an AI agent
  working on comparisons reads only `comparisons/` plus `core/`
- Each slice is independently testable: `tests/unit/test_comparison_*.py` maps directly
  to `comparisons/`
- The project has a small, well-defined feature set (songs, comparisons, rankings,
  playlists, enrichment) — there is no risk of slice proliferation
- Shared infrastructure (Glicko-2 math, DB session, config, exceptions) lives in `core/`
  which all slices may depend on; `core/` depends on nothing

## Considered Options

| Option | Description |
|--------|-------------|
| A — Layered (horizontal) | `models/`, `services/`, `routes/`, `repositories/` at root |
| B — Vertical slices | `songs/`, `comparisons/`, `rankings/`, `playlists/`, `enrichment/`, `core/` |
| C — Hybrid | Layered at top level; feature sub-packages within services/ |

## Decision Outcome

**Chosen option: B — Vertical slices**

```
backend/
  core/           # glicko2.py, db.py, config.py, exceptions.py
  songs/          # models.py, repository.py, service.py, routes.py
  comparisons/    # models.py, repository.py, service.py, routes.py
  rankings/       # models.py, repository.py, service.py, routes.py
  playlists/      # models.py, repository.py, service.py, routes.py
  enrichment/     # pipeline.py, sources/
```

Dependency rule: routes never call repositories directly; services never construct HTTP
responses; repositories contain only DB queries; all slices may depend on core, but
core depends on nothing.

## Consequences

**Positive:**
- AI agent context is bounded per feature — working on comparisons does not require
  loading models from an unrelated songs/ layer
- New features added as new slices without touching existing code
- Test file naming maps directly to source directories
- Onboarding (human or AI) is faster: "everything about comparisons is in comparisons/"

**Negative:**
- Slight duplication of file names within each slice (every slice has models.py,
  service.py, etc.) — mitigated by the fact that each file's content is entirely distinct
- Less familiar to developers expecting the conventional Django/Flask layered structure;
  a portfolio reviewer from a Django background may find it unconventional
- Cross-slice queries (e.g. a rankings query that joins songs and comparisons) require
  deliberate design to avoid circular imports between slices

**Implementation note:**
Circular imports between slices are prevented by the dependency rule: slices communicate
via service interfaces, not direct model imports. If rankings/ needs song data, it calls
`songs/service.py`, not `songs/models.py` directly.
