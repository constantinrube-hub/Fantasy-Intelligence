# Fantasy Intelligence Engine V8.4-M2

## Scope

V8.4-M2 continues the approved position-driver roadmap through Steps 10–15. It retains V8.2.2 as the frozen live decision model and V8.3-M1 as the historical research backbone.

### Implemented

1. Position production decomposition: team volume → participation → opportunity share → expected opportunity counts.
2. Opportunity xFP: expected fantasy production using opportunity/participation inputs only.
3. Regression validation: over/under-performance versus xFP is tested for subsequent mean reversion.
4. Opportunity-change detection: recent role change is compared with an older baseline and validated against future scoring.
5. Teammate competition: receiving, backfield, tackle and pass-rush environment indices are tested incrementally.
6. Vacated opportunity: historical redistribution and capture rates are measured retrospectively.

## Guardrails

- `diagnostic_only: true` remains mandatory.
- Live Draft, Waiver, Weekly, Trade and Team scores still use the frozen V8.2.2 control logic.
- xFP cannot use realized receptions, yards, touchdowns, tackles, sacks or interceptions as predictors.
- Pass-play/snap proxies are not relabeled as true routes.
- Vacated opportunity is not eligible for live activation until a trustworthy pregame availability feed exists.
- Validation uses the same expanding windows as M1: 2019–2021→2022, 2019–2022→2023, 2019–2023→2024, 2019–2024→2025.

## Browser surface

Lab now contains separate `M1 Research` and `M2 Research` tabs. M2 displays decomposition validation, xFP performance, regression tests, opportunity-change tests, competition ablations and vacated-opportunity diagnostics.

## Historical outputs

The browser reads `data/research/milestone2.json`. A detailed `milestone2_player_week.csv.gz` can also be generated locally for follow-on research but remains git-ignored.

## Deployment documentation

Intentionally deferred until the full roadmap is completed, per user request.
