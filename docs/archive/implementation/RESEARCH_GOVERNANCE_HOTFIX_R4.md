# FIE Research Governance Hotfix R4

## Purpose
This patch closes the final three research-governance issues identified after the post-workflow Redraft/Chopped audit.

## Fixes

### 1. Correlation alignment
All shared `safe_corr` helpers now pair observations by row order rather than pandas index labels. This prevents ndarray predictions from being incorrectly aligned with Series retaining original dataframe indexes.

### 2. Server-side format gates
`build_current_snapshot.py` now applies `decision_format_position_gates` for weekly and waiver decisions whenever a League-ID profile is supplied. The server artifact therefore uses the same format restrictions as the browser. Legacy/global snapshots retain the generic gate as a backwards-compatible fallback.

### 3. Waiver decision validation
M5 contract revision 4 requires two independent conditions before a position is placed in the live waiver gate:

- point-forecast validation: chronological next-3-game MAE improvement over recent points;
- decision-ranking validation: chronological improvement in within-week rank correlation, with non-inferior top-quartile precision and top-pick regret.

Ranking metrics are calculated inside each weekly waiver decision set, then aggregated to the holdout season. Promotion still requires at least four chronological holdout seasons.

## Deployment effect
Existing revision-3 artifacts remain readable and fail-closed. To obtain revision-4 waiver gates, each league must rerun the M1-M6 research workflow once after deploying this patch, followed by the current-season refresh.
