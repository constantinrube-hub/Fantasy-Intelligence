# General Season Preview Model Design

## Decision

The Season Preview is split into two ordered layers:

1. **Phase A — league-neutral football forecast:** predict 2026 raw player and NFL team statistics once, without fantasy scoring, rosters, replacement value, ADP, or market projections.
2. **Phase B — league application:** replay the Phase A raw distributions through each frozen league's exact scoring contract, then apply that league's roster, scarcity, replacement, and format rules.

This is the Sol methodology checkpoint required by `docs/audits/CODEX_MODEL_ROUTING.md`. It changes no model, application, runtime, ranking, recommendation, or workflow behavior. Terra implementation is authorized only within the boundaries below.

The permanent order remains:

`football-stat distribution -> exact league scoring -> league value -> market comparison -> decision`

## Why the existing boards cannot be the Phase A source

The existing M9 season boards correctly predict raw football components before scoring, but model selection and promotion gates are evaluated through each league's scoring profile. An empirical audit at design time found 290 players with raw projections across the 22 frozen league boards; 288 appeared in multiple leagues, and every one of those 288 had at least one differing raw component across league outputs.

Consequently, Phase A must not select one league as canonical, average the 22 boards, or pool their projections. It must train and validate one football-stat model from canonical historical football data. Phase B is the first point at which a league profile may enter.

The already-frozen `season-preview-v1` remains immutable and retains its documented meaning: a transparent aggregation of existing league-specific M9 ranking rows, not a new predictive model. The new artifacts use separate namespaces.

## Phase A prediction contract

### Forecast cutoff and population

The first release is bound to `data/research/baselines/2026/baseline-v1.json` and its `PRESEASON_ELIGIBLE` source cutoff. Training outcomes end with the 2025 regular season. No 2026 result, later roster fact, current endpoint backfill, or reconstructed preseason snapshot may enter a 2026 forecast.

The canonical NFL population is independent of fantasy ownership. Current team and position assignments must be resolved from cutoff-eligible identity/roster evidence. Conflicting identities are retained as typed blockers and never resolved by choosing a convenient league copy.

### Output semantics

Every modeled stat exposes both:

- `conditional_per_game`: expected production when active; and
- `availability_adjusted_season_total`: conditional production combined with a separately modeled expected-games distribution.

A weekly mean may not be multiplied by 17 and relabelled as a preseason model. Expected games, conditional production, and schedule length remain separate fields. Quantiles are P10/P25/P50/P75/P90 and describe football-stat uncertainty, not injury certainty.

Each entity/stat family has one of:

- `READY_RESEARCH_ONLY`: provenance, chronological point accuracy, distribution calibration, and reconciliation gates pass;
- `BASELINE_ONLY`: a reproducible transparent baseline is available but no challenger clears the validation gate;
- `DIAGNOSTIC_ONLY`: evidence exists but is not fit for preview publication;
- `BLOCKED_MISSING_SOURCE`;
- `BLOCKED_IDENTITY`;
- `BLOCKED_INSUFFICIENT_HISTORY`;
- `NOT_MODELED_V1`.

`BASELINE_ONLY` must be shown visibly in both machine and human reports. It is not equivalent to a validated model.

### V1 target inventory

| Entity | V1 raw-stat families | Initial policy |
|---|---|---|
| NFL team offense | plays, dropbacks, pass attempts, completions, gross passing yards, passing TDs, interceptions thrown, sacks allowed, rush attempts, rush yards, rush TDs, points scored | Required |
| NFL team defense / DEF entity | sacks, interceptions, forced fumbles, fumble recoveries, defensive/ST TDs, points allowed, yards allowed | Required; preserve existing DEF entity semantics |
| Team kicking | field-goal attempts/makes/misses by governed distance bucket, made FG yards, extra-point attempts/makes/misses | Required; individual K binding only with cutoff-safe identity |
| QB | pass attempts, completions, passing yards/TDs/interceptions/2PT/first downs; rush attempts/yards/TDs/2PT/first downs; fumbles/lost | Required |
| RB | rush and receiving opportunity, yards, TDs, 2PT, first downs, fumbles/lost | Required |
| WR | rush and receiving opportunity, yards, TDs, 2PT, first downs, fumbles/lost | Required |
| TE | rush and receiving opportunity, yards, TDs, 2PT, first downs, fumbles/lost | Required |
| K player | team-kicking allocation to an exact current kicker | Conditional on cutoff-safe role identity; otherwise `BLOCKED_IDENTITY` while team kicking remains available |
| EDGE / IDL / LB / S / CB | tackles, assists, TFL, sacks, hits, interceptions, passes defended, forced/recovered fumbles, TDs as position-appropriate | `DIAGNOSTIC_ONLY` or typed blocker in V1; no league use until separate season-level calibration and identity gates pass |

Return yards and touchdowns may be included only through the repository's existing authoritative returner evidence. Nominal depth-chart labels may not fill missing returner IDs.

## Model structure

Phase A uses one versioned candidate ladder on identical outer folds and eligible rows:

1. transparent prior-season/shrunk role baseline;
2. regularized linear component model;
3. shallow regularized histogram-gradient-boosting challenger where sample size permits.

Candidate selection is per entity type, position, and stat family. A win for receiving volume does not promote touchdown conversion, another position, or the whole preview. Ensembles are not authorized by this design.

The model graph is:

1. team opportunity and scoring environment;
2. player active-game participation and team opportunity share;
3. per-opportunity efficiency;
4. sparse event conversion with shrinkage;
5. expected-games/availability distribution;
6. joint scenario simulation and reconciliation.

Features may use only cutoff-safe football evidence. Scoring settings, league format, roster ownership, replacement value, ADP, and market projections are prohibited features.

## Coherence and reconciliation

Independent component forecasts are not published directly. Reconciliation occurs within each simulated scenario before quantiles or league scoring are calculated.

### Player-to-team budgets

- QB pass attempts reconcile to team pass attempts.
- Player receptions reconcile to team completions.
- Player targets reconcile to a canonical team target pool derived under the same nflverse definitions; targets are never forced to equal pass attempts.
- Player rush attempts reconcile to team rush attempts.
- Player passing, rushing, and receiving yards/TDs reconcile to compatible team gross totals under the same definitions.
- Interceptions thrown reconcile to opponent interceptions, and sacks allowed reconcile to opponent sacks at the league-total level.
- Nonnegative counts and structural inequalities such as completions <= attempts and receptions <= targets are mandatory.

A named `UNALLOCATED` entity absorbs genuinely unresolved roster share, uncommon play attribution, and source-definition residuals. It may not be silently redistributed to known players. Reports expose its share by team/stat; excessive unallocated share blocks that family.

### Team-to-league budgets

Across the scheduled regular season, league-wide offense and defense totals must match for mirrored outcomes such as points scored/allowed, sacks allowed/made, and interceptions thrown/caught. Any permissible source-definition mismatch must be named, quantified, and kept outside player value rather than hidden by rounding.

Reconciliation changes, constraint residuals, and pre/post values are auditable. Passing a point-forecast gate without passing coherence is insufficient for `READY_RESEARCH_ONLY`.

## Validation protocol

### Temporal folds and baselines

Use expanding target-season folds `2019-2021 -> 2022`, `2019-2022 -> 2023`, `2019-2023 -> 2024`, and `2019-2024 -> 2025`. Candidate choice and tuning occur only inside each training window. Player comparisons use identical eligible identities; team comparisons use all available teams in the held-out season.

Every target is compared with a declared simple baseline on the same rows. Baselines include prior-season per-game production with empirical shrinkage, prior role/team shares, and team trailing-season volume. Missing prior history is handled through a declared cohort prior, never a hindsight value.

### Required metrics

- Point: MAE, RMSE, mean bias, Spearman rank correlation, and top-k overlap.
- Count targets: mean Poisson deviance when mathematically applicable.
- Distribution: pinball loss at all five quantiles, weighted interval score or CRPS, P10-P90 coverage and width.
- Availability: expected-games MAE and interval coverage, evaluated separately from conditional production.
- Coherence: maximum and aggregate residual for every equality/inequality, plus unallocated share.
- Subgroups: position, target season, team change, experience band, prior participation band, and modeled stat family.

### Publication gate

A challenger family reaches `READY_RESEARCH_ONLY` only when all are true:

1. four outer seasons and the contract's minimum paired rows are present;
2. mean paired MAE improvement is positive, at least three of four seasons are non-negative, and the temporal-block bootstrap 95% lower bound is above zero;
3. weighted interval score is non-inferior to the baseline and P10-P90 empirical coverage is within five percentage points of 80% overall;
4. no material subgroup has a predeclared calibration or error regression above tolerance;
5. post-reconciliation structural constraints pass and unallocated share remains within the configured limit;
6. identity, input lineage, deterministic reproduction, and cutoff tests pass.

If no challenger passes but the transparent baseline passes provenance, coverage, calibration, and coherence checks, the family may publish as `BASELINE_ONLY`. Otherwise it remains diagnostic or blocked. No status causes automatic production promotion.

## Phase A artifacts

Phase A writes a new immutable first-write bundle:

- `data/research/evaluation/2026/preseason/general-preview-v2/manifest.json`
- `data/research/evaluation/2026/preseason/general-preview-v2/player-stat-projections.csv`
- `data/research/evaluation/2026/preseason/general-preview-v2/team-stat-projections.csv`
- `data/research/evaluation/2026/preseason/general-preview-v2/validation.json`
- `data/research/evaluation/2026/preseason/general-preview-v2/general-preview.md`

The manifest binds the frozen baseline, sources, code, dependency lock, target contracts, models, seed, outputs, and validation hashes. CSV rows include status and blockers rather than omitting failed families. The Markdown report presents raw football leaders, team profiles, uncertainty, coverage, and limitations; it contains no fantasy rank.

## Phase B league application

Phase B consumes the exact Phase A manifest and no other football forecast. It validates each frozen league profile and scoring hash before replay.

For each of the 22 leagues it:

1. applies supported scoring keys to every reconciled Phase A scenario;
2. derives fantasy-point quantiles from scored scenarios, not by scoring marginal stat quantiles independently;
3. applies that league's canonical position eligibility, roster demand, replacement/scarcity, and format semantics;
4. reports component coverage and typed unsupported-rule blockers;
5. keeps ADP/market as a later comparison surface only.

A missing Phase A family is never zero-scored. Phase B may preserve the existing governed M9/market fallback for a league-specific presentation, but must identify it as an external fallback and may not blend it into or relabel it as the general forecast.

New Phase B outputs use the `league-preview-v3` namespace; they do not overwrite `season-preview-v1`. Team-strength aggregation remains descriptive unless a separately validated game/season simulator is later authorized. V1 does not claim projected wins, playoff odds, or championship odds.

## Terra implementation boundary

Terra may implement, in order:

1. a deterministic canonical team/player-season training table and source manifest;
2. the Phase A baseline and candidate ladder with outer-fold predictions;
3. joint reconciliation, quantiles, validation, and the immutable general-preview bundle;
4. the Phase B exact-scoring adapter for all 22 frozen profiles;
5. focused synthetic integrity tests, a no-network fixture, and one final repository release gate.

The implementation must stop if the frozen baseline cannot supply a canonical cutoff-safe 2026 player/team universe. It may not fetch a current endpoint and call that evidence preseason-eligible.

This authorization excludes production M9/M10 changes, app/runtime or canonical ranking writes, model promotion, scheduling, waiver logic, season-outcome probabilities, historical forecast reconstruction, and generated source/dist synchronization outside the repository's existing release process.

## Implemented research surface

Terra implemented the bounded producer in `research/general_season_preview.py` and its no-network integrity fixture in `research/integrity_general_season_preview_test.py`.

- `build-general` verifies the frozen baseline, derives a cutoff-safe player catalogue from frozen ranking sources, loads one shared 2019-2025 historical player/team dataset, produces independent baseline/challenger evidence, reconciles every scenario to team budgets, and first-writes the Phase A bundle.
- `apply-leagues` verifies every frozen profile fingerprint and scoring signature, replays the reconciled scenarios for QB/RB/WR/TE, and first-writes the Phase B league bundle without changing canonical rankings.
- Team-defense totals supported by mirrored opponent offense are emitted as `BASELINE_ONLY`. Sparse D/ST event components, individual kicker allocation, and IDP stay explicitly blocked until their separate source/identity/calibration contracts exist; no score is silently set to zero.
- `.github/workflows/build-fie-general-season-preview.yml` is manual-only and main-only. It validates the no-network fixture, runs Phase A and/or Phase B, guards production surfaces and the immutable Window 1B `season-preview-v1`, and commits only the two new research artifact namespaces.

The initial real historical build into `general-preview-v1` / `league-preview-v2` exposed a player-to-team reconciliation implementation defect: `LAR` player rows did not match the `LA` team budget, QB completions were not bound to team completions, and player receiving yards/TDs were not bound to compatible passing budgets. Those immutable artifacts remain preserved but are superseded and must not feed value or market work. The corrected implementation writes `general-preview-v2` / `league-preview-v3`, validates every declared p50 and scenario accounting relation, and requires a green workflow before any corrected output is treated as available.

## Primary references

- [nflverse player-stat data dictionary](https://nflreadr.nflverse.com/articles/dictionary_player_stats.html)
- [nflverse player-stat loader and release family](https://nflreadr.nflverse.com/reference/load_player_stats.html)
- [nflverse data availability schedule](https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html)
- [Gneiting and Raftery — strictly proper scoring rules](https://stat.uw.edu/research/tech-reports/strictly-proper-scoring-rules-prediction-and-estimation)
- [Taieb, Taylor, and Hyndman — coherent probabilistic forecasts](https://proceedings.mlr.press/v70/taieb17a.html)
