# Tranche 2C — Production Authority / Release Identity

Change package: **C10-003**  
Baseline: `a0e9617598777a9aab60389ea0d44211c51cd038`  
Prepared: `2026-09-02T10:18:48+00:00`

## Purpose

Reconcile production decision authority, candidate-promotion semantics, release identity and living documentation without changing football-model behavior.

## Canonical authority after 2C

- Production decision owner: `FIEDecisionService@9.3.2`.
- Canonical route: V9 diagnostic decision geometry plus DraftBase canonical overlay.
- Candidate decision coefficients: `production.promoted=false` and remain fail-closed.
- Governed current features: independent league-scoped lineage + M6 runtime gate.
- `FIE_DRAFT_V71`: compatibility fallback only if canonical V9 rows are unavailable.

## Release identity

- Release: `9.3.4c-production-authority`
- Runtime: `9.3.4C-modular-runtime`
- Decision model/geometry: `9.1-diagnostic-architecture`
- Research generation: `M1-M9 league-scoped + current-split-v1 + unified-research-v1`
- Stage: `controlled-implementation`

This corrects stale release prose that still described the active runtime as V9.3.2-only / M1–M6 and stale documentation that described V8.9 as the normal unpromoted production fallback.

## Explicit non-changes

- No projection changes.
- No ranking changes.
- No DraftBase weight changes.
- No V9 candidate coefficient changes.
- No ADP boundary changes.
- No replacement/scarcity changes.
- No current-feature governance threshold changes.
- No candidate promotion.
- No cleanup/deletion.

## Validation

Permanent checks cover:

1. release ↔ model-config identity parity;
2. `FIEDecisionService` as production owner;
3. candidate promotion remains false;
4. current-feature governance remains independent and league-scoped;
5. V7.1 is fallback-only;
6. active release identity references V9.3.4C and M1–M9;
7. generated release/model descriptors match their sources;
8. existing 2A six-format and 2B responsive contracts remain green;
9. full canonical release build remains `DEPLOYABLE_SOURCE`.

The first target run is allowed to regenerate only `config/build-manifest.json` and `dist/config/build-manifest.json`. Those two exact files are then synchronized in a final commit.
