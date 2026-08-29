# FIE Feature Evidence Research (Phases 1–7)

This layer answers a narrower question than M7/M8/M9: **why did each candidate metric pass, fail, or remain uncertain?** It is research-only and cannot activate runtime adjustments.

## Outputs

For each league/season the workflow writes `performance/<season>/evidence/` containing:

- `feature_evidence.json` — complete auditable bundle.
- `feature_evidence_matrix.csv` — one row per position/feature with coverage, redundancy, weekly/next-season gates, FDR diagnostics, validated horizons, and classification.
- `feature_fold_evidence.csv` — fold-level weekly and next-season feature evidence.
- `feature_horizon_validation.csv` — formal next-week, next-3, ROS, floor, ceiling, and breakout incremental gates.
- `component_validation.csv` — next-week opportunity/efficiency component tests.
- `regularized_challengers.csv` — Ridge, Elastic Net and nonlinear challenger results under nested chronological validation.
- `conditional_effects.csv` — pre-specified interactions tested *over and above* their main effects.
- `data_expansion_plan.csv` — prioritized history/source expansion actions.
- `FEATURE_EVIDENCE_REPORT.md` — human-readable review.

## Evidence statuses

- `validated`: clears the unchanged robust chronological OOS gate.
- `promising_underpowered`: positive estimate, but temporal-block CI still crosses zero.
- `horizon_specific`: fails the same-week residual gate but clears at least one independently validated future/tail horizon (next week, next 3, ROS, floor, ceiling, breakout, or next season).
- `redundant_or_explanatory`: strongly overlaps another feature and adds little residual value.
- `mechanism_specific`: fails the direct fantasy-point gate but robustly improves prediction of an intermediate football component such as target volume, carry volume, or efficiency.
- `descriptive_not_incremental`: correlates with future fantasy output but does not improve FIE after existing information is known.
- `insufficient_coverage`: too little observed history/source coverage.
- `no_incremental_evidence`: no stable incremental evidence in the current history.

## Statistical rules

1. Outer validation is chronological expanding-window holdout by season.
2. The production-style gate still requires at least four folds, >=1% mean improvement, sufficient positive folds, and temporal-block bootstrap CI strictly above zero.
3. Challenger hyperparameters are selected only inside the outer training period. Phase 4 compares Ridge, Elastic Net, a Ridge-shrunk player-intercept partial-pooling model, and a nonlinear HistGradientBoosting challenger.
4. Exact fold-level sign-flip tests plus Benjamini-Hochberg FDR are reported for weekly features, next-season features, multi-horizon screens, component screens, interactions, and challengers as an additional exploratory multiple-testing safeguard. They do **not** replace the robust gate.
5. Component evidence tests each feature beyond a calibrated persistence baseline for the component itself; conditional effects are tested against models already containing both main effects. This prevents either layer from receiving credit for information already present in its baseline.
6. More history is recommended only where the observed evidence pattern supports an underpowered/coverage diagnosis. The estimated folds-needed field is explicitly a planning heuristic, not a significance guarantee.
7. Nothing in this layer auto-activates. A robust challenger is marked only `eligible_for_manual_consumer_integration` and must be integrated and revalidated separately.

## Run

GitHub Actions → **Build FIE Feature Evidence Research**. Use the same league ID/format as the M7–M9 build. For the 2026 preseason, use 2016–2025 history where the public sources support it.
