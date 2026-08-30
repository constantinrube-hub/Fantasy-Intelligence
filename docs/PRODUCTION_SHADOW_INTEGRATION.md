# FIE Production Shadow Integration

## Purpose

The production-shadow layer is the controlled bridge between hardened research evidence and eventual runtime integration. It does **not** change live FIE projections.

## What enters shadow testing

1. QB HistGradientBoosting residual challenger, only because the hardened Phase 4 evidence gate passed.
2. RB HistGradientBoosting residual challenger, only because the hardened Phase 4 evidence gate passed.
3. RB backfield competitor-count Ridge as a transparent alternate weekly challenger.
4. Validated all-feature component models for QB pass/rush volume, RB carry/target volume, WR target volume, and TE target volume.
5. Horizon-specific multivariate consumers built only from features already routed by the hardened evidence layer.

## Independent consumer revalidation

Research-level feature evidence is not treated as sufficient for runtime use. Each downstream consumer is rebuilt and tested chronologically again:

- at least four outer seasonal holdouts;
- unchanged robust gate: mean improvement >= 1%, >= 67% positive folds, temporal-block 95% CI strictly above zero;
- historical-only training and inner validation for model/hyperparameter selection;
- current-season scoring only after the consumer itself passes.

## No double counting

RB HistGB and the transparent competitor-count adjustment are **alternate** shadow candidates. They are not added together. A future stacked model would need a completely new out-of-sample validation.

Likewise, individually validated horizon features are not added as independent point bonuses. They are combined inside a single multivariate horizon consumer, which must independently clear the gate.

## Week 1 / preseason

Within-season component and horizon evidence does not justify carrying last season's role state across the offseason. Therefore:

- current-season offensive shadow scoring requires completed current-season games;
- prior-season feature fallback is forbidden;
- the workflow may succeed before Week 2 while reporting the live shadow stage as blocked/no-current-season-features;
- historical consumer revalidation and model readiness remain valid.

This is intentional fail-closed behavior.

## Outputs

Under:

`data/research/leagues/<league_id>/performance/<report_season>/shadow/`

- `production_shadow.json`
- `shadow_model_registry.csv`
- `shadow_current_players.csv`
- `shadow_component_predictions.csv`
- `shadow_horizon_predictions.csv`
- `PRODUCTION_SHADOW_REPORT.md`

## Promotion semantics

`shadow_eligible=true` means the downstream consumer survived independent chronological revalidation and may run beside canonical FIE.

It does **not** mean the app should use that value. Runtime activation requires a later explicit integration patch plus post-integration validation against the exact live consumer path.
