# Proposed Unified Per-League FIE Research Pipeline

After V9.7.5 is proven on the pilot league, consolidate the currently separate
research workflows into one orchestrator.

## Recommended modes

### SINGLE_LEAGUE
Inputs:
- league_id
- league_format=AUTO preferred
- season
- adp_key=AUTO
- optional force_rebuild flags

Runs every required stage for one league and produces one final readiness report.

### ALL_REGISTERED
Later addition. Reads the league registry and starts a matrix job per registered
league, with a conservative max-parallel limit. Each league remains isolated:
its profile/scoring signature, artifacts, gates and pass/fail status are separate.

## Stage sequence
1. Refresh/validate league profile and scoring signature.
2. Ensure shared historical nflverse backbone.
3. Build/reuse M1-M9 league research.
4. Build feature-evidence / production-shadow / controlled-runtime research as applicable.
5. Build V9.7 strategy/preseason evidence.
6. Exact M9 comparator audit (V9.7.4).
7. QB ensemble audit (V9.7.5).
8. Market/availability evidence and league-specific value board.
9. Final per-league readiness manifest.

## Efficiency
Do not repeat downloads/model backbones unnecessarily:
- raw nflverse history can be cached globally by data/version hash;
- league-level artifacts are keyed by league ID + scoring signature + format;
- if two leagues have identical scoring signatures, historical scoring research can
  eventually be deduplicated, while replacement/VORP/roster decisions remain league-specific.

## Governance
A large workflow must not mean one giant all-or-nothing model.
Each stage writes a status and immutable provenance. Downstream stages consume only
valid prerequisites and fail closed where evidence is insufficient.

Recommended final artifact:
`performance/<season>/research_pipeline/readiness.json`

It should show each gate by position and stage, plus:
- READY_FOR_PROMOTION_REVIEW
- DIAGNOSTIC_ONLY
- BLOCKED_DATA
- BLOCKED_SCORING
- BLOCKED_STATISTICS

This allows all leagues to be tested with one workflow while preserving individual
statistical decisions.
