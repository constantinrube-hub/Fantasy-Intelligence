# FIE Unified Per-League Research Pipeline — Live Repository Audit

Audit date: 2026-08-31

Audited repository: `constantinrube-hub/Fantasy-Intelligence`

Audited `main` SHA: `36f687712b3c2aebc07b1f7bfef456a087cfdfe3`

## Executive conclusion

The implementation plan remains architecturally correct, but the repository has advanced since the plan was written. The unified layer must therefore be **more orchestration-heavy and less algorithmic** than the original draft suggested.

The implementation in this patch does not rewrite the existing football/market/value engines. It wraps them, binds them to one league profile at a time, adds fail-closed readiness/governance, then exposes one canonical report/app contract.

## Necessary adaptations to the original plan

### 1. V9.7.1–V9.7.3 are already consolidated into the current strategy stack

Current live files:

- `research/fie_strategy_stack.py`
- `research/build_fie_strategy_stack.py`

The live strategy builder identifies itself as the V10.4 generation and already performs:

- V9.7.1 component-first preseason validation;
- V9.7.2 research-only current-season shadow construction;
- V9.7.3 historical head-to-head/calibration validation;
- league profile based ADP-key resolution;
- market movement and historical market-curve diagnostics;
- league-specific replacement/VORP;
- Value Finder/action semantics;
- current identity/relevance hardening.

**Adaptation:** the unified orchestrator calls `build_fie_strategy_stack.py` once and records V9.7.1/V9.7.2/V9.7.3 as separate stage evidence. It does not rerun or copy those algorithms.

### 2. V9.7.4 and V9.7.5 remain separate exact-governance research stages

Current live files:

- `research/preseason_projection_v4.py`
- `research/preseason_projection_v5.py`
- `research/validate_v974_preseason.py`
- `research/validate_v975_preseason.py`

The current V9.7.4 comparator reconstructs exact M9 scoring and delegates unchanged prior gates. V9.7.5 remains QB-only and includes standalone non-inferiority plus unchanged chronological/statistical gates.

**Adaptation:** these are run after the current strategy stack. Their results are read by the resolver; no threshold is restated or weakened in the new pipeline.

### 3. Promotion review is now explicitly distinct from production activation

The latest pilot V9.7.5 evidence and workflow explicitly keep:

- `production_activation_allowed = false`;
- canonical M9/M1/runtime unchanged;
- ADP/market inputs out of the football model;
- no automatic activation.

**Adaptation:** `PROMOTION_REVIEW_READY` is a research readiness state only. The final board still uses the production M9 source unless a separate, explicit future governance artifact approves a preseason model by league/profile/scoring fingerprint.

### 4. Canonical league value is already implemented and must not be re-created

Current `fie_strategy_stack.build_league_value_board()` already derives:

- actual league fixed starters;
- FLEX/SUPER_FLEX marginal allocation;
- league-specific replacement;
- VORP;
- relevant-universe positional FIE rank;
- market positional rank/rank edge;
- draft/watchlist horizons from teams × roster slots;
- deterministic VALUE/STRONG_VALUE/OVERPRICED/STRONG_FADE semantics.

**Adaptation:** the new final board feeds the **canonical M9 season board** into this exact existing function. The V9.7.2 strategy shadow is joined only as challenger evidence. This prevents the report from becoming a second rank calculation and prevents research shadow output from silently becoming production.

### 5. D/ST and K are first-class dedicated engines, but their current app scope differs from offense

The current repository has dedicated D/ST and kicker contracts/engines and current snapshot summaries. The pilot current snapshot reports active D/ST and K entities even while current-season nflverse player-week data is unavailable.

**Adaptation:** D/ST and K are selected from their existing specialist engines. The report labels their current output scope `WEEKLY_CURRENT`; it does not invent season-long VORP/ADP semantics when the existing specialist contract does not provide them.

### 6. V9.6/current storage is now split/deduplicated

Current:

- `research/current_snapshot_storage.py`
- split manifests reference shared player bases and scoring overlays.

The pilot current snapshot is valid for 2026 Week 1, but V9.6 is currently blocked because regular-season nflverse player/team/snaps files are not yet available. This is a correct preseason fail-closed state.

**Adaptation:** the unified pipeline hydrates the existing current snapshot through the storage helper and treats V9.6 as context. A blocked V9.6 current-season runtime does **not** block historical preseason research.

### 7. Fast league switching is already hash-bound and namespaced

Current:

- `research/build_league_app_snapshots.py`
- per-league `app/core.json` + `app/manifest.json`;
- `data/research/app/league-index.json`.

Current `core.research` exposes profile/current/governance only.

**Adaptation:** a small postprocessor extends the existing core with readiness/rankings/report-summary paths and recomputes core/manifest/index hashes. No parallel app shell is created.

### 8. Value Finder already owns a strict “canonical rank vs discovery layer” separation

Current `app/value-finder.js` explicitly states that canonical FIE ranks come from the existing Draft Base Value service and Value Finder must not redefine them.

**Adaptation:** the new Value Finder bridge only filters already-rendered canonical rows using report membership. It adds Top-100 Outliers, Sleepers >100, Strong Value and Strong Fade quick filters without recomputing rank, VORP, ADP rank or optimizer score.

### 9. App source is a large integrated shell

The current `index.html` and Value Finder source are large, mature integrated surfaces.

**Adaptation:** the patch avoids replacing `index.html` or the full Value Finder. `tools/sync_league_app_snapshots.py` injects the small research service/UI/bridge into the validated dist tree, following the same additive pattern already used for calibration protection.

### 10. All-league Git publication must be more atomic than current one-league research workflows

Existing specialized research workflows can commit their own league result. That is unsafe for a 19-ish league matrix.

**Adaptation:** the reusable matrix job has `contents: read`, uploads league-namespaced artifacts and never pushes. The final aggregator downloads all artifacts, verifies registry reconciliation, builds portfolio/app output once, then performs one commit/rebase/push.

## Live pilot assumption

The current pilot remains league `1391803939736801280`, matching the latest V9.7.5 audit commit and existing pilot research artifacts.

The reusable workflow automatically captures a pre-run pilot equivalence baseline and compares M1–M9 hashes, V9.7.1/2/4/5 evidence, ADP-key resolution and replacement points after the unified run when `force_rebuild=false`.

## Governance conclusion

No new file in this implementation changes:

- M1–M9 model formulas;
- V9.7 statistical thresholds;
- V9.7 chronological folds;
- positive-fold/CI requirements;
- exact-scoring requirements;
- standalone ensemble safety boundary;
- ADP exclusion from the football model;
- production promotion policy.

The new code is orchestration, selection/readiness, deterministic report grouping and app context only.
