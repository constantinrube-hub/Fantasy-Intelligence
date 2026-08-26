# V8.5-M3 Implementation Audit

## Scope audited

Milestone 3 implements Steps 16–18 while retaining V8.2.2 as the frozen live decision model and preserving M1/M2 research.

## Live-model non-regression

Compared these live functions against V8.4-M2 and confirmed exact source equality:

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

Therefore M3 does not alter current Draft, Waiver, Weekly, Trade or Team score calculations.

## Step 16 checks

- NGS/PFR/participation advanced variables are joined by canonical GSIS/PFR identity.
- Seasonal PFR/participation data are concatenated before merging, preventing duplicate `_x/_y` feature corruption.
- All advanced inputs are lagged within player/season before forecast use.
- Public participation pass-play presence remains explicitly different from true routes.
- Public participation team-pressure context remains explicitly different from an individual pressure/pass-rush snap.
- Position models are validated on 2022, 2023, 2024 and 2025 chronological holdouts.
- `validated_candidate` requires >=1% average MAE improvement against M2 xFP and positive improvement in >=3 holdout folds.

## Step 17 checks

- Natural experiments cover QB changes, major receiver absences, lead-back absences, lead LB/S absences and sustained role jumps.
- All estimates are retrospective within-player/role deltas.
- Bundle-level `causal_claim` is hard-coded false and validated.
- Coordinator-change research is explicitly blocked until a reliable historical coaching source exists.

## Step 18 checks

- Y1/Y2 status derives from draft year and season.
- Preseason model uses only draft/biographical/combine priors.
- After-Week-3 model adds only Weeks 1–3 NFL evidence.
- The target is a position-specific meaningful late-season role, not fantasy points.
- Validation reports Brier score, ROC AUC and accuracy on chronological holdouts.

## Deterministic fixture QA

Fixture-only QA generated:

- 36 Step 16 position/fold validation rows.
- 9 position aggregates.
- 6 Step 17 natural-experiment outputs.
- 70 Y1/Y2 player-season rows.
- 8 Step 18 validation rows across preseason and after-Week-3 variants.
- 9 young-player position summaries.
- 4,754 M3 player-week derived rows.

These figures are integrity-test outputs only and are not empirical NFL findings.

## Syntax / packaging QA

Passed:

- Python compilation for all research scripts, validators and tests.
- Existing M1 integrity tests.
- Existing M2 integrity tests.
- New M3 deterministic integrity test.
- M3 bundle validator.
- Combined browser JavaScript extraction and `node --check`.
- Cloudflare health Function syntax.
- Cloudflare allowlisted data-proxy Function syntax.
- Duplicate HTML-ID check.
- GitHub workflow YAML parsing.

## Known limitations retained intentionally

- True all-route participation is still unavailable in the public-core historical pipeline.
- Participation identifies defenders on field when pressure occurred, not the defender who caused pressure.
- NGS receiver separation is target-conditioned and is therefore treated as conversion/target-quality context, not a direct cause of targets.
- Historical coordinator/scheme metadata is not yet integrated.
- Historical college production is not yet integrated into Y1/Y2 priors.
- Preseason depth-chart rank remains excluded until a time-safe extraction is validated across the source schema change after 2024.
- No M3 diagnostic has permission to modify live rankings.

## Deployment

Detailed deployment instructions remain intentionally deferred until all roadmap steps are complete, per user instruction.
