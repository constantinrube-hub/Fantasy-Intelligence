# Controlled Implementation — Tranche 1 Characterization

**Status:** TESTS ONLY  
**Production semantics changed:** NO  
**Cleanup performed:** NO  
**Statistical thresholds changed:** NO  
**Tranche 0 frozen head:** `b9221db1134b9257153ca0ec97a91aeafe8c8415`

## Purpose

Tranche 1 creates the behavioral safety net required by C10-014 before any correctness or consolidation change.

It deliberately contains both:

1. **positive guards** for behavior that already works and must survive, and
2. **known-gap reproduction assertions** for audited defects that existing green validation did not catch.

A green baseline run therefore means the repository is characterized correctly, **not** that the known defects have disappeared.

## New characterization suites

### Six-format runtime
Executes browser owners for all six formats and reproduces the hybrid disagreement across:

- Runtime Foundation
- LeagueContext
- DraftBase
- calibration
- Core LineupOptimizer
- Monte Carlo worker
- V9 diagnostic hybrid branch

### All 22 real league profiles
Runs every enabled profile through browser format/capability ownership and confirms that the current mismatch is isolated to the real `CHOPPED_BESTBALL` league.

### Core ↔ A3 ↔ D economics
Verifies starter-demand parity on a fixed FLEX/Superflex fixture and records the separate D replacement-frontier convention.

### DataClient scope/race
Reproduces URL-only in-flight coalescing across two different AbortController scopes while also proving the delayed A→B snapshot/live-overlay abort guard works.

### Direct-fetch allowlist
Rejects any new raw-fetch app module outside the audited allowlist and marks ResearchReportService's current primary raw fetch as the known exception.

### Unified research stage identity
Uses the committed pilot stage manifest to prove the stage names exist but lack typed producer/schema/validator identity and do not invoke the dedicated builders by filename.

### Responsive primary decision visibility
Parses the actual Start/Sit/Waiver/DST/Kicker schemas and the CSS breakpoints to reproduce the ordinal-column hiding defect.

## Baseline versus target mode

All tests support:

```bash
--mode baseline
```

for Tranche 1.

Selected suites also support:

```bash
--mode target
```

which expresses the post-fix contract. Target mode is **not enabled in this tranche**.

## Pass condition

- only Tranche-1 files changed after `b9221db1134b9257153ca0ec97a91aeafe8c8415`;
- all characterization tests pass in baseline mode;
- known gaps are reproduced exactly;
- positive guards remain green;
- canonical release build remains `DEPLOYABLE_SOURCE`;
- tracked `dist/` remains unchanged after deterministic build.
