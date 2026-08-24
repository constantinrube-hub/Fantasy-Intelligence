# V8.4-M2 Implementation Audit

## Scope audited

Milestone 2 implements Steps 10–15 while retaining the V8.2.2 live model as control.

## Passed controls

### Live-model non-regression

Compared these functions against V8.3-M1 and confirmed exact source equality:

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

### Python / research

Passed:

- Python compilation for M1 and M2 scripts/validators/tests.
- Existing M1 deterministic integrity test.
- New M2 deterministic integrity test.
- Full fixture chain: M1 derived tables → M2 analysis.
- M1 bundle validation.
- M2 bundle validation.

Fixture-only QA generated:

- 60 decomposition component-validation rows.
- 44 recombined opportunity-count validation rows.
- 20 xFP fold-validation rows.
- Regression and opportunity-change validation across all nine model positions.
- Competition ablation results across the position components.
- A deterministic retrospective vacated-receiving episode to exercise Step 15.

These fixture figures are tests only and are not empirical NFL findings.

### Leakage / governance

- xFP validator rejects realized outcome features.
- Historical folds remain time ordered.
- Vacated opportunity cannot become live-active.
- Route proxy guardrail retained.
- `diagnostic_only` retained.

### Browser / Cloudflare syntax

Passed:

- Combined JavaScript extraction and `node --check`.
- Cloudflare health function syntax.
- Cloudflare data-proxy function syntax.
- GitHub workflow YAML parsing.

## Known limitations retained intentionally

- M2 xFP is opportunity-based at the player-week/position layer, not yet the final per-target/per-carry tracking model planned for later position-specialized work.
- True route participation is not reconstructed from public snap data.
- Public-core defensive opportunity remains proxy-based until richer participation/advanced data are parsed in Step 16.
- Vacated opportunity is retrospective because current trusted pregame injury/availability data have not yet been integrated.
- No M2 diagnostic has permission to modify live rankings.

## Deployment

Not documented in this milestone, per explicit user instruction to defer the deployment guide until all roadmap steps are complete.
