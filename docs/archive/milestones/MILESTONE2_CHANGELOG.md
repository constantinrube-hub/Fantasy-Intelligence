# V8.4-M2 Changelog, Steps 10–15

## Baseline preservation

- V8.2.2 remains the frozen live decision model.
- All V8.3-M1 historical research functionality is retained.
- Key live scoring functions were byte-for-byte compared against the M1 build and remain unchanged.

## Step 10, position production decomposition

- Added separate out-of-sample forecasts for team opportunity and player participation/share.
- Added position-specific recombination:
  - QB: team pass volume × QB attempt share; team rush volume × QB rush share.
  - RB: team rush volume × carry share; team pass volume × target share.
  - WR/TE: team pass volume × target share.
  - EDGE/IDL/LB/S/CB: opponent opportunity volume × defensive participation, retained as clearly labelled public-core proxies where richer participation is not yet available.
- Added component and recombined-count validation across all expanding folds.

## Step 11, opportunity xFP

- Added realized-opportunity xFP and pregame opportunity xFP.
- Explicit leakage guardrail forbids realized efficiency/outcome fields from xFP predictors.
- Added MAE/RMSE/rank-correlation comparison against recent fantasy-point baseline.

## Step 12, regression engine

- Added `xfp_residual = actual FP - realized-opportunity xFP`.
- Tests whether over/under-performance predicts subsequent three-game mean reversion.
- Labels results as validated regression candidates only when the historical relationship supports it; no live activation occurs.

## Step 13, opportunity-change detection

- Added robust position-specific role-change score.
- Compares recent 3-game opportunity with the prior 5-game baseline.
- Validates flagged role breakouts against subsequent 3-game fantasy scoring.

## Step 14, teammate competition

Added pregame indices:

- Receiving Competition Index.
- Receiving competitor count.
- Receiving concentration HHI.
- Backfield Competition Index.
- Backfield competitor count.
- Tackle Competition Index.
- Pass Rush Support Index.

Each is evaluated by comparing otherwise-identical models with and without competition features.

## Step 15, vacated opportunity

- Added retrospective absence-event detection.
- Measures vacated target/carry/defensive-role share.
- Measures teammate capture rate and top redistribution beneficiaries.
- Hard-coded `activation_eligible: false` until a trustworthy pregame availability layer is added.

## Research workflow

- Combined manual workflow now rebuilds M1 first, then M2 from the same scoring profile and historical backbone.
- Added M2 fixture tests and bundle validator.
- Added M2 derived-table output for later milestones.

## UI

- Added `Lab → M2 Research`.
- Displays Steps 10–15 independently from M1.
- Pending placeholder bundle is safe and does not break the rest of the app.
