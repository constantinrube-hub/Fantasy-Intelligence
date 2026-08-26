# V8.7-M5 Implementation Audit

## Scope audited

Milestone 5 implements Steps 24–27 while preserving the completed M1–M4 research stack and V8.2.2 as the fail-closed fallback decision model.

## Live-model non-regression

Compared these protected function definitions against V8.6-M4 and confirmed exact source equality:

- `assignScores`
- `computeCalibration`
- `computePredictionScores`
- `computeProjectedReplacementLevels`
- `computeProjectionRanksAndEdges`
- `computeReplacementLevels`
- `scorePublicStats`
- `scoreSleeperProjectionStats`
- `seasonDraftScoreFor`
- `waiverScoreFor`
- `tradeAssetValue`
- `weeklyLineupValue`
- `teamPowerMetrics`

Result: **13/13 unchanged**.

M5 wraps the completed legacy calculation afterward. If no M5 decision gate passes, the wrapper returns without changing those legacy values.

## Step 24 audit

- Validation is season-level and uses only M4 out-of-sample weekly predictions.
- Holdout seasons remain chronological.
- Draft-policy candidates require upstream M4 validation plus >=1% MAE improvement and robust positive folds.
- M5 does not label weekly aggregation as a complete preseason injury/availability model.
- Sleeper/engine season projection remains the preseason production anchor.
- Draft Assistant can receive M5 production/future-role inputs only for players whose Draft and format gates pass.
- Weekly-only activation is explicitly prevented from changing Draft Assistant fallback weekly shape.

## Step 25 audit

- Target is future mean fantasy points over the following three games.
- Current/future outcomes are not included as same-row predictors.
- Validation is expanding/chronological.
- Waiver-policy activation requires both M5 waiver evidence and upstream M4 position validation.
- `waiverScore` is overwritten only for eligible free agents and only after the legacy score has already been calculated.

## Step 26 audit

### Mean projection

- Weekly gating uses lineup-oriented evidence, not MAE alone.
- Requires improved rank correlation and non-material deterioration in top-quartile precision/top-1 regret.
- Upstream M4 position validation remains mandatory.

### Risk bands

- Quantiles for a test season are learned from prior holdout seasons only.
- Risk-band validation checks 80% interval coverage and both tails.
- Floor/ceiling cannot activate unless the weekly mean gate also passes.

## Step 27 audit

- One production core feeds five transparent league-format policies.
- All Draft and Waiver weights sum exactly to 1.0 for each format.
- Best Ball and Chopped player-level proxies now include positive-fold robustness and position-level status.
- A globally validated format profile is insufficient by itself; position-specific format gates are also required.
- Dynasty and Dynasty + Best Ball remain partial/diagnostic because a full multi-year asset-value backtest is not yet present. Partial status cannot activate M5 format transforms.
- Best Ball proxy is not misrepresented as a roster-level best-ball simulation.
- Chopped proxy is not misrepresented as a guillotine survival model.

## Scoring compatibility

- M5 carries the exact M1 historical scoring settings in its own bundle.
- Browser compatibility compares the loaded league's non-zero scoring rules with those stored M5 settings.
- M5 refuses cross-scoring activation.
- This fixes a potential cross-script scoping failure that would otherwise have depended on M1-local JavaScript variables.

## Current-season activation

The shipped `data/research/current/milestone5_current.json` is intentionally:

- `awaiting_step29_current_season_automation`
- empty
- incapable of activating any player.

The shipped empirical M5 placeholder also contains empty decision gates. Therefore the deployable package is fail-closed before Step 29.

## Navigation/runtime audit

- `Lab → M5 Decisions` is part of the existing V8.2 section configuration.
- Existing navigation/render logic was extended to toggle the M5 panel rather than replaced with a competing router.
- M5 exports `window.renderMilestone5` only for the existing renderer to invoke.
- No duplicate HTML IDs are present.

## Deterministic fixture QA

The synthetic M1–M5 chain is used only to verify that all code paths execute. It is not NFL evidence.

M5 fixture generated:

- 36 Step 24 Draft season/fold rows across 9 positions.
- 9 Step 24 position aggregates.
- 27 Step 25 Waiver folds.
- 9 Step 25 position aggregates.
- 9 exported Waiver policy specifications.
- 68 Step 26 weekly ranking rows in the deterministic fixture.
- 27 Step 26 risk-calibration folds.
- 9 risk-band summaries.
- Best Ball and Chopped proxy outputs with robustness statuses.
- Separate Weekly/Draft/Waiver/format decision-gate manifests.

The fixture intentionally produced some validated and some diagnostic components. Those statuses are synthetic integrity-test outcomes and must never be interpreted as real NFL findings.

## Validation suite

Passed:

- M1 bundle validator.
- M2 bundle validator.
- M3 bundle validator.
- M4 bundle validator.
- M5 bundle validator.
- M1 integrity test.
- M2 integrity test.
- M3 integrity test.
- M4 integrity test.
- M5 policy integrity test.
- Python compilation for the complete research directory.
- JavaScript syntax check for all inline scripts.
- Cloudflare Function JavaScript syntax checks.
- workflow YAML parsing.
- HTML duplicate-ID check: **174 IDs, 174 unique**.
- shipped placeholder fail-closed assertions.
- protected live-model comparison: **13/13 unchanged**.

## Known limitations retained

- No real M5 empirical conclusions are shipped in the placeholder bundle.
- Current-season automatic M5 player snapshot generation remains Step 29.
- Historical immutable Sleeper projection depth remains dependent on genuinely captured pregame observations.
- Draft season validation is availability-conditioned rather than a complete preseason games-played model.
- Best Ball validation remains player-level.
- Chopped validation remains player-level rather than roster/elimination-level.
- Dynasty lacks a full multi-year asset-value target and therefore remains partial/diagnostic in M5.
