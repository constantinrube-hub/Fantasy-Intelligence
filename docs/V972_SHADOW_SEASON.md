# V9.7.2 Validated Component Shadow Season Projection

## Purpose

V9.7.2 converts V9.7.1 validated next-season component models into an auditable 2026 shadow projection while preserving the existing M9 season board unchanged.

## Projection contract

For each offensive player, the strategy layer preserves the original M9 fields and adds:

- `m9_strategy_projection`
- `m9_fie_season_mean`
- `m9_fie_diagnostic_mean`
- `m9_fie_production_mean`
- `m9_projection_source`
- `v972_component_ppg`
- `v972_component_mean`
- `v972_games_assumption`
- `v972_profile_season`
- `v972_profile_team`
- `v972_profile_join_method`
- `v972_exact_scoring_replay`
- `v972_shadow_applied`
- `v972_shadow_status`
- `v972_validation_mean_improvement`
- `v972_validation_ci95_low/high`
- `v972_validation_positive_folds`
- `strategy_projection`
- `strategy_projection_source`
- `projection_delta_vs_m9`

The new file is `performance/<season>/strategy/season_projection_v972.csv`.

## Eligibility

A V9.7.2 component projection is used only when:

1. the position cleared the V9.7.1 four-fold promotion gate;
2. exact league scoring replay cleared;
3. a prior-season profile exists;
4. prior-season games >= 3;
5. the player matches the current catalog;
6. a current NFL team is available;
7. current team equals prior-season profile team.

All other rows use the existing M9 strategy projection.

## Transfer and rookie policy

Team changes and rookies without a prior-season profile intentionally fall back to M9. A new-team opportunity / portable-trait model must be validated before those cases can use V9.7.2.

## Statistical interpretation

V9.7.1 was validated against prior-season component persistence. V9.7.2 therefore remains a shadow challenger and does **not** claim a validated head-to-head improvement over M9 yet. Historical M9-vs-V9.7.2 challenger testing is the next promotion gate.

## Governance

- no ADP input into football predictions;
- no canonical M9 fields modified;
- no V9.6 weekly runtime changes;
- no automatic activation;
- no production replacement claim versus M9.
