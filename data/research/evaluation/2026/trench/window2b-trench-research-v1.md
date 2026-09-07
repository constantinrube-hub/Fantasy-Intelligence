# FIE Window 2B: Trench Research + Thin Integration

## Governance

This is a research-only chronological benchmark. M9 remains the production champion. A validated trench family may appear only as research context; it does not change projections, canonical rankings, waiver values, runtime behavior, or ADP handling.

## Validation design

- Baseline and challenger use exactly the same complete-case player rows.
- Window 2A trench features use only weeks strictly before the target week.
- Player-form baseline uses only prior games from the same season.
- Each test season is predicted by models trained only on earlier seasons.
- Ridge alpha and all gates are fixed before seeing results; no hyperparameter tuning or family winner-picking occurs.
- Standard PPR is only a cross-league screening target. Any production promotion would still require the normal league-scoring governance path.

## Results

| Position | Family | Status | OOS rows | Folds | MAE improvement | CI low | RMSE improvement | Fold wins |
|---|---|---|---:|---:|---:|---:|---:|---:|
| QB | PASS_PROTECTION_FRONT_CORE | BLOCKED_NOT_VALIDATED | 2515 | 5 | -0.11% | -0.035 pts | -0.20% | +40.00% |
| RB | RUN_BLOCK_FRONT_CORE | BLOCKED_NOT_VALIDATED | 6219 | 5 | -0.26% | -0.027 pts | +0.02% | +60.00% |
| WR | PASS_PROTECTION_FRONT_CORE | BLOCKED_NOT_VALIDATED | 9991 | 5 | -0.04% | -0.009 pts | -0.15% | +60.00% |
| TE | PASS_PROTECTION_FRONT_CORE | BLOCKED_NOT_VALIDATED | 4870 | 5 | +0.30% | +0.005 pts | +0.12% | +80.00% |
| D/ST | TRENCH_MATCHUP_CONTEXT | BLOCKED_TARGET_CONTRACT_NOT_BOUND | 0 | 0 | — | — | — | — |

## D/ST

D/ST is intentionally `BLOCKED_TARGET_CONTRACT_NOT_BOUND` in Window 2B. The player-week screening target is not a trustworthy D/ST fantasy-scoring target, so no synthetic team-defense outcome is invented.

## Thin integration

- No family cleared every pre-specified gate. Thin integration remains empty and fail-closed.

## Interpretation

A blocked result is a valid scientific outcome. Correlation, intuitive football logic, or a single winning season is not sufficient for integration. Window 2C can consume only the explicit research-context registry, never an unvalidated trench proxy.
