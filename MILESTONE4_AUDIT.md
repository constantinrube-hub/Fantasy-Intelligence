# V8.6-M4 Implementation Audit

## Scope audited

Milestone 4 implements Steps 19–23 while retaining V8.2.2 as the frozen live decision model and preserving M1–M3 research.

## Live-model non-regression

Compared these live functions against V8.5-M3 and confirmed exact source equality:

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

Cloudflare health/proxy version metadata was updated to V8.6-M4, but no proxy routing/model calculation was changed.

## Step 19 checks

- One governance registry spans all nine model positions.
- M1 stability/predictiveness, M2 regression/role/competition and M3 advanced-position evidence are represented as separate families.
- `graduation_status` and `live_status` are different fields.
- A candidate can be validated while remaining live `OFF`.
- Outcomes are explicitly classified as label/regression-only rather than silently promoted as opportunity features.

## Step 20 checks

- Bundle-level activation lock is enabled.
- `live_model_overrides` is empty.
- Feature registry requires `live_status=OFF`.
- Exported model specs require `live_status=OFF`.
- Blend requires `live_status=OFF`.
- Bundle validator fails if these conditions are violated.

## Step 21 checks

- Models predict position-appropriate raw football stat components before league scoring.
- Raw-stat target families cover passing, rushing, receiving and IDP events.
- Exact M1 scoring settings are applied to the predicted stat line after prediction.
- Current-week `fantasy_points`, `xfp_residual` and `opportunity_xfp_realized` cannot appear as model inputs.
- M2 `opportunity_change_score` is shifted one full game before M4 same-week use. The unlagged version is explicitly rejected by validation.
- Expanding-window holdouts remain 2022, 2023, 2024 and 2025.
- Model specifications export the imputer/scaler/Ridge parameters required for later controlled integration without serializing opaque Python objects.

## Step 22 checks

- Added an immutable gzip JSONL Sleeper snapshot archive format.
- `capture_sleeper_snapshot.py` is first-write by default.
- M4 accepts direct market rows only when `pregame_eligible=true`.
- Rows captured without a verified pregame assertion are counted as rejected and excluded from benchmarking.
- The M4 pipeline never backfills old weeks by querying historical Sleeper endpoints and labelling the response as the original pregame projection.
- If immutable history is insufficient, the bundle reports `blocked_insufficient_immutable_sleeper_history` rather than a fake FIE-vs-Sleeper result.

## Step 23 checks

- Blend search tests FIE weights from 0.00 to 1.00 in 0.05 increments.
- For test season Y, weight selection uses only prior completed joined holdout seasons.
- No test-year outcomes can select the weight evaluated in that same year.
- Reports blend MAE versus FIE alone and market alone.
- Even a validated blend candidate remains live `OFF`.

## Deterministic fixture QA

The full M1–M4 fixture chain generated:

- 109 governance-registry rows across 9 positions.
- 13 fixture-only validated candidates, 86 diagnostic-only rows and 10 blocked/insufficient rows.
- 0 live research features.
- 36 final position/fold validation rows.
- 268 raw-stat target/fold diagnostics.
- 9 deployable-but-OFF position model specifications.
- 2,714 out-of-sample M4 prediction rows.
- 36 fixture Sleeper benchmark rows.
- 27 time-safe blend validation rows.
- 9 position-level blend summaries.

These are deterministic integrity-test outputs only and are not empirical NFL findings.

## Syntax / packaging QA

Passed:

- Python compilation for all research scripts, validators and integrity tests.
- Existing M1 integrity test.
- Existing M2 integrity test.
- Existing M3 integrity test.
- New M4 integrity test.
- M1, M2, M3 and M4 fixture bundle validators.
- Combined browser JavaScript extraction and `node --check`.
- Cloudflare health Function syntax.
- Cloudflare allowlisted data-proxy Function syntax.
- Duplicate HTML-ID check: 169 IDs, 169 unique.
- GitHub workflow YAML parsing.

## Known limitations retained intentionally

- Real direct Sleeper history is not fabricated. Step 22/23 remain blocked until immutable pregame snapshots accumulate.
- The event stack uses transparent Ridge models for this milestone. Higher-capacity learners can later be benchmarked under identical folds rather than assumed superior.
- Count events are modelled as continuous expectations, so predicted counts may be fractional.
- Yardage bonus rules applied to a mean predicted stat line are an approximation to expected bonus probability; a later simulation layer can model threshold probabilities directly.
- Public all-route/pass-rush guardrails from M3 remain unchanged.
- No M4 diagnostic has permission to modify live rankings.

## Deployment

Detailed deployment instructions remain intentionally deferred until all roadmap steps are complete, per user instruction.
