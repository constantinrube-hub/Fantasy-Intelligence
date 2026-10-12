# Waiver-v2 model-validation checkpoint handoff

Source/target implementation is complete for three bounded scoring cohorts;
full historical/profile closure is not claimed. See
`WAIVER_V2_SOURCE_TARGET_CLOSURE_2026-10-12.md` and the two immutable observation
summaries under `data/research/waiver-v2/source-closure/2026-10-12/`.

## Inputs available

- 2018, 2021, 2022, 2023, 2024, 2025, explicitly excluding conflicting 2019/2020
  source periods before measuring model performance.
- Stoned Lack Bestball 2 (`f407dd1959d9d675`), Stoned Lack Bestball Dynasty 3
  (`fec2fca13ae53e1d`), and Stoned Lack Bestball Dynasty 4 (`0b264245218667cd`).
- 16,059 complete exact next-three-calendar-week targets per signature; QB,
  RB, WR and TE are separate validation units. Those counts are not independent
  observations across profiles or overlapping horizons.
- Potential outer holdouts 2022–2025, starting with 2018 and 2021 as two earlier
  training seasons. Actual feature/domain/fold eligibility remains unverified.
- Labels preserve source/report/ledger hashes and scoring isolation; no missing
  stat rows or omitted roster/bye memberships were zero-imputed.

## Resolve before model implementation or eligibility adjudication

Apply the existing `OFFENSIVE_WAIVER_ELIGIBILITY_DESIGN.md` protocol, not legacy
M5 approvals. Review the point-in-time feature reconstruction and the impact of
incomplete no-stat/bye roster observations on the admitted cohort and live
coverage. Freeze the feature families, nested selection/imputation/coverage
procedure and temporal-block interval method before final outer-fold results
are examined. The legacy Ridge may be a first challenger; its coefficients,
fixed coverage threshold and promotion evidence do not transfer.

Use the same exact rows for recent-production baseline and model metrics.
Keep forecast, ranking, recommendation and transaction gates independent.
Best Ball and Dynasty remain forecast-only even if a football mean passes;
their acquisition policy is a separate design/evidence problem. Do not retrofit
old prospective captures, change scoring rules, reduce four holdouts, or treat
target availability as a forecast result.

The repository routing rule requires a Sol methodology checkpoint before new
statistical-methodology reasoning and later promotion decisions. This handoff
is concrete source evidence for that checkpoint; it is not model approval.
