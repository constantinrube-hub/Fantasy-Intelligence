# FIE Production Shadow Report

Generated: 2026-08-30T08:52:08.945323+00:00

## Governance

This is a **shadow-only** integration. It does not alter canonical FIE projections, current snapshots, governance, or deployed app artifacts.

## Consumer revalidation

| Position | Consumer | Model | Δ loss | Folds | CI low | Shadow eligible |
|---|---|---|---:|---:|---:|---|
| WR | weekly_projection_residual | histgb | 0.00% | 0 | None | no |
| TE | weekly_projection_residual | histgb | 0.00% | 0 | None | no |
| QB | weekly_projection_residual | histgb | 1.40% | 4 | 0.0005518647476741547 | YES |
| RB | weekly_projection_residual | histgb | 2.37% | 4 | 0.01776898260963914 | YES |
| RB | weekly_projection_residual | ridge_backfield_competitor_count | 1.43% | 4 | 0.012076048128560413 | YES |
| QB | pass_volume | ridge_component_all_features | 2.80% | 4 | 0.020134104225721903 | YES |
| QB | rush_volume | ridge_component_all_features | 7.09% | 4 | 0.05949612759838703 | YES |
| RB | carry_volume | ridge_component_all_features | 10.90% | 4 | 0.09637200770855545 | YES |
| RB | target_volume | ridge_component_all_features | 9.50% | 4 | 0.08776891498059641 | YES |
| TE | target_volume | ridge_component_all_features | 10.59% | 4 | 0.09492058807281581 | YES |
| WR | target_volume | ridge_component_all_features | 11.02% | 4 | 0.09851243565777142 | YES |
| RB | breakout | ridge_multivariate_horizon | 6.56% | 4 | 0.044851966458634894 | YES |
| RB | ceiling | ridge_multivariate_horizon | 1.48% | 4 | 0.007194097014185059 | YES |
| RB | floor | ridge_multivariate_horizon | 5.05% | 4 | 0.04500978083798685 | YES |
| RB | next_3_games | ridge_multivariate_horizon | 4.03% | 4 | 0.02768566007856356 | YES |
| RB | next_week | ridge_multivariate_horizon | 2.58% | 4 | 0.02123825325302656 | YES |
| RB | rest_of_season | ridge_multivariate_horizon | 5.89% | 4 | 0.03699919787591987 | YES |
| WR | breakout | ridge_multivariate_horizon | 7.13% | 4 | 0.04625280093133515 | YES |
| WR | ceiling | ridge_multivariate_horizon | 1.61% | 4 | 0.007027894068446039 | YES |
| WR | floor | ridge_multivariate_horizon | 6.57% | 4 | 0.051754011696136436 | YES |
| WR | next_3_games | ridge_multivariate_horizon | 4.63% | 4 | 0.03729328586404929 | YES |
| WR | next_week | ridge_multivariate_horizon | 2.90% | 4 | 0.02371677368193001 | YES |
| WR | rest_of_season | ridge_multivariate_horizon | 5.24% | 4 | 0.0334784691035795 | YES |
| TE | breakout | ridge_multivariate_horizon | 8.16% | 4 | 0.060453109856452754 | YES |
| TE | ceiling | ridge_multivariate_horizon | 3.54% | 4 | 0.024989675741137533 | YES |
| TE | floor | ridge_multivariate_horizon | 4.14% | 4 | 0.03079842497465024 | YES |
| TE | next_3_games | ridge_multivariate_horizon | 5.98% | 4 | 0.051059665937351645 | YES |
| TE | next_week | ridge_multivariate_horizon | 3.30% | 4 | 0.02267803104216735 | YES |
| TE | rest_of_season | ridge_multivariate_horizon | 7.30% | 4 | 0.062078455075391725 | YES |

## Current-season shadow

Status: `blocked_no_current_season_completed_features`

Reason: season_type_preseason

- Weekly shadow candidates scored: 0
- Component forecasts scored: 0
- Horizon forecasts scored: 0

## Promotion

Shadow eligibility is not runtime eligibility. A separate runtime integration and post-integration validation are still required before any live projection may change.
