# Tranche 6A — Research Completeness and M10 Football Model Design

## Boundary

This is the Sol-only design result required by `CODEX_MODEL_ROUTING.md`. It does not train, promote, activate, or integrate a model. It changes no application, ranking, recommendation, scoring, replacement, market, data-capture, scheduled-workflow, or runtime behavior.

The design preserves the permanent separation:

`football event distribution → exact league scoring → league value → market price → decision`

ADP, draft behavior, roster demand, and replacement economics remain outside the football model.

## Evidence snapshot at the 5E closure

Repository evidence at closure commit `b4c4ef5` supports three simultaneous conclusions:

1. **Pipeline coverage is complete.** All 22 enabled leagues, spanning all six supported formats, report completed M1–M9 pipelines, completed reports, and completed app publication.
2. **Football evidence is incomplete.** All 22 leagues retain `BLOCKED_STATISTICS` or `BLOCKED_SCORING` decisions for QB/RB/WR/TE. All 22 M9.1c candidates are `RESEARCH_ONLY_BLOCKED_PROMOTION` because the required immutable historical Sleeper baseline does not exist. Only 11 of 22 leagues currently contain non-zero M9.1c exact/adjusted rows.
3. **Production promotion remains correctly blocked.** V9.7.4 has no exact comparator pass in any league, V9.7.5 remains diagnostic, M7 has no validated driver family, and M8 has no validated matchup family.

Representative league `1391803939736801280` provides the following bounded source and model evidence:

| Evidence area | Current result |
|---|---|
| M7 public/optional driver-family coverage | QB 5/7 available, RB 4/7, WR 4/7, TE 4/7; zero validated candidate families |
| M8 matchup families | nine aggregate families, three folds each, zero validated candidate families |
| M9 preseason position specs | WR and TE validated candidates; QB and RB remain diagnostic in the inspected league |
| Immutable Sleeper season-market history | three first-write snapshots, all from 2026 |
| Prospective Sleeper availability history | three first-write snapshots, all from 2026 |

Therefore the authoritative verdict is:

```text
PIPELINE_COVERAGE_COMPLETE
FOOTBALL_EVIDENCE_INCOMPLETE
PROMOTION_BLOCKED
```

A completed file or pipeline may never be presented as validated football evidence.

## Research-completeness contract

Tranche 6B must implement a matrix, not a single percentage. A weighted total could hide a critical leakage or statistical failure behind unrelated completed files.

Every position × horizon × feature family × decision domain cell must expose one of:

- `ABSENT`
- `CONTRACT_ONLY`
- `PRESENT_UNVERIFIED`
- `TIME_SAFE_EVALUATED`
- `STATISTICALLY_VALIDATED`
- `DECISION_VALIDATED`
- `PRODUCTION_AUTHORIZED`
- `NOT_APPLICABLE`

Every non-authorized cell must carry one or more typed reasons:

- `MISSING_SOURCE`
- `INSUFFICIENT_HISTORY`
- `LEAKAGE_RISK`
- `STATISTICAL_FAILURE`
- `CALIBRATION_FAILURE`
- `DECISION_UTILITY_FAILURE`
- `REPRODUCIBILITY_FAILURE`
- `GOVERNANCE_BLOCKED`

The matrix must measure these independent dimensions:

1. artifact and league coverage;
2. source provenance and point-in-time eligibility;
3. temporal validation coverage;
4. statistical stability and practical improvement;
5. probabilistic calibration;
6. decision-specific utility;
7. reproducibility and source/dist integrity;
8. explicit production authorization.

The portfolio summary may count states and blockers, but a critical failure remains visible and fail-closed. Cross-league aggregation is descriptive; it cannot promote a model for an individual league.

## M10 forecasting target

M10 is a research challenger to M9, not a replacement declaration. It predicts distributions of raw football outcomes. League scoring is applied afterwards by the existing canonical scoring service.

### Prediction units and horizons

- Weekly: player-game and team-game distributions using only information available before the target kickoff.
- Season: next-season or rest-of-season distributions built from explicit opportunity, efficiency, and availability components. A weekly mean may not be multiplied by 17 and called a preseason model.
- Availability: probability of playing and participation capacity are separate from conditional production. Until sufficient prospective history exists, availability remains an external governed input and uncertainty widens rather than inventing precision.

### Component graph

1. **Team opportunity:** plays, dropbacks, rush attempts, scoring opportunities, and game environment.
2. **Player participation and role:** snap, route, target, carry, red-zone, and return shares subject to team-level budget constraints.
3. **Per-opportunity efficiency:** completions, yards, first downs, turnovers, sacks, tackles, and other position-appropriate outcomes.
4. **Event conversion:** touchdowns and other sparse count events with explicit shrinkage.
5. **Joint simulation:** teammate and opponent dependence is applied once; incompatible independently predicted shares are reconciled before scoring.
6. **Exact scoring transform:** simulated raw outcomes pass through the existing league scoring registry.

Initial implementation is QB/RB/WR/TE only. Existing D/ST and K engines remain authoritative where applicable. IDP, injury redistribution, assignment-level opponent effects, and waiver economics are later bounded reviews; none may be smuggled into the first M10 target.

### Candidate ladder

All candidates use identical source snapshots, rows, targets, and outer folds.

1. Existing M9 is the champion comparator.
2. A transparent regularized linear/generalized-linear model is the audit baseline.
3. A shallow, regularized histogram gradient-boosting challenger may be evaluated for non-linear interactions. Count targets may use Poisson loss; conditional quantiles may use quantile loss. Hyperparameters must come from a small versioned search space inside the training window.
4. An ensemble is prohibited unless out-of-fold stacking, trained without the final evaluation seasons, beats every component model and passes calibration and decision gates. Model disagreement is evidence to report, not a reason to average automatically.

The available scikit-learn dependency already supports histogram gradient boosting with missing-value handling plus squared-error, absolute-error, Poisson, Gamma, and quantile losses. Adding a new model library is not part of the first M10 experiment.

## Validation protocol

### Temporal separation

- Preserve the existing expanding outer seasons: `2019–2021 → 2022`, `2019–2022 → 2023`, `2019–2023 → 2024`, and `2019–2024 → 2025`.
- Candidate selection and hyperparameter choice occur only inside each outer training window.
- The 2026 season remains prospective evidence. It may not be used to select the model that is later reported as having predicted 2026.
- Stat corrections and source revisions are versioned. Corrected outcomes may train future models, but target-week features remain frozen at their decision-time versions.

### Forecast metrics

- Count/probability targets: Poisson deviance where applicable, Brier score for binary events, and calibration by probability band.
- Point forecasts: MAE, bias, rank correlation, top-k overlap, and exact league-scored fantasy-point error.
- Distributions: pinball loss at P10/P25/P50/P75/P90, interval coverage and width, and CRPS when a coherent forecast distribution is available.
- Subgroups: position, season, week range, team change, rookie/young-player status, participation band, scoring format, and relevant league capability.

Proper scoring rules are required because accuracy of the mean alone cannot establish that upside/downside distributions are honest. Conformalized quantile regression may be evaluated as an outer-fold calibration layer; it is not assumed valid across time without measuring coverage separately in each held-out season.

### Promotion-review gate

A position/horizon candidate reaches `PROMOTION_REVIEW_READY` only when all are true:

1. source lineage and leakage checks pass;
2. at least four completed outer seasons are evaluated on paired rows;
3. practical point/distribution improvement clears the temporal-block bootstrap gate;
4. calibration is non-inferior overall and has no material subgroup failure;
5. exact league-scoring replay passes for every applicable scoring profile;
6. the relevant downstream decision-domain contract improves or is non-inferior;
7. artifacts reproduce deterministically from locked inputs and dependencies;
8. no automatic promotion occurs.

A candidate that improves MAE but worsens tails, calibration, legal-lineup utility, or a material position/format subgroup remains diagnostic.

## Source policy

### Public core

The current public core may continue to use versioned nflverse play-by-play, player/team statistics, rosters, schedules, weekly Next Gen Stats, PFR snap counts/advanced statistics, and FTN charting where their licenses and availability permit. Every joined column needs a source, `as_of`, release cadence, and target-time eligibility record.

The current nflverse availability schedule creates explicit constraints:

- player/team statistics are refreshed after game days and may receive later corrections;
- participation data from 2023 onward is not available during the season and is published after the postseason;
- the nflverse injury source has no post-2024 feed;
- 2025+ depth-chart records are timestamped rather than assigned to a week.

The existing prospective Sleeper availability capture is therefore the current injury-status evidence path. Missing history remains a block.

### Optional tracking or premium sources

NFL Big Data Bowl/Next Gen Stats samples prove that tracking-level research is possible, but competition datasets are not a continuous production feed. Route responsibility, individual WR–DB assignment, blocker–rusher assignment, all-route participation, and premium unit grades remain optional research families until a lawful, versioned, multi-season, point-in-time source exists.

No nominal depth-chart assignment, nearest-defender proxy, current endpoint backfill, or hindsight reconstruction may fill those gaps.

## Ordered implementation tranches

### 6B — Machine-readable completeness inventory (Terra)

Implement the matrix and deterministic validator over existing artifacts only. It must reproduce the evidence snapshot above and change no model or runtime behavior.

### 6C — Point-in-time evidence hardening (Terra)

Record source release/revision metadata, extend the already scheduled prospective market and availability archives, and produce explicit coverage-age reports. Do not backfill historical forecasts from current endpoints.

### 6D — Offline M10 offensive challenger (Terra)

Implement the component graph and locked candidate ladder for QB/RB/WR/TE in research-only artifacts. Preserve M9 as champion and prohibit app integration.

### 6E — Cross-model and decision review (Sol)

Review paired M9/M10 evidence, calibration, disagreement, subgroup stability, and decision-specific utility. This phase may recommend no change.

### 6F — Governed shadow integration (Terra)

Only positions/horizons approved by 6E may enter a namespaced shadow artifact. Production remains unchanged and automatic promotion remains prohibited.

### 6G — Promotion review (Sol, then Terra if approved)

Any production change requires a separate human-readable decision, machine-readable promotion artifact, rollback contract, and full release gate.

## Primary references

- [nflverse data update and availability schedule](https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html)
- [nflreadr source and data-dictionary index](https://nflreadr.nflverse.com/reference/)
- [NFL Football Operations — Big Data Bowl](https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl)
- [scikit-learn `HistGradientBoostingRegressor`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
- [Romano, Patterson, and Candès — Conformalized Quantile Regression](https://papers.neurips.cc/paper_files/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html)
- [Gneiting and Raftery — Strictly Proper Scoring Rules, Prediction, and Estimation](https://doi.org/10.1198/016214506000001437)
