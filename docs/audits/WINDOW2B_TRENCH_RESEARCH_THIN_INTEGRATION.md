# Window 2B — Trench Research + Thin Integration

## Status

**IMPLEMENTED — RESEARCH ONLY**

Window 2B tests whether the team-level trench evidence owned by Window 2A adds out-of-sample predictive value beyond a fixed player-form baseline. It does not modify M9 or any production surface.

## Why this window exists

Window 2A deliberately produces public, reproducible **team trench proxies**, not individual offensive-line or defender grades. Window 2B asks the next scientific question:

> Does any pre-specified trench family improve future player prediction after controlling for simple prior player form?

A football-plausible relationship or an in-sample correlation is not enough.

## Inputs

### Window 2A historical evidence

Expected files:

`data/research/trench/historical/season_<YEAR>-v1.json`

The owner guarantees that each target-week trench snapshot uses only regular-season plays from weeks strictly before the target week.

### nflverse weekly player statistics

Window 2B uses the public nflverse weekly player-stat files as the historical evaluation target and player-history source.

Relevant public contracts:

* player week rows expose season, week, team, opponent team, player identity and position;
* play-by-play exposes possession team, defense team, sack, QB hit, rush attempt, EPA and success;
* nflverse schedules distinguish regular-season games through `game_type=REG`.

The standard-PPR target is a **research screening target only**. It does not replace FIE league scoring or authorize a universal production model across the 22 leagues.

## Pre-specified candidate families

### QB, WR, TE — PASS_PROTECTION_FRONT_CORE

* own prior-week cumulative sack rate allowed
* opponent prior-week cumulative sack rate generated

QB-hit rates remain available as Window 2A diagnostics but are not included in the confirmatory family because Window 2A marks them optional evidence.

### RB — RUN_BLOCK_FRONT_CORE

* own designed-run EPA per attempt
* own designed-run success rate
* own stuff rate allowed
* opponent rush EPA allowed per attempt
* opponent rush success rate allowed
* opponent stuff rate forced

### D/ST

D/ST is fail-closed as `BLOCKED_TARGET_CONTRACT_NOT_BOUND` in Window 2B. The player-week standard-PPR screening target is not a valid team-defense fantasy target. Window 2B therefore does not invent one.

## Baseline

The fixed baseline contains only lagged same-season player form:

1. previous-game fantasy points
2. prior-four-game mean fantasy points
3. season-to-date mean fantasy points
4. number of prior games

A player must have at least two prior games.

## Leakage controls

1. Window 2A target-week trench evidence must report `target_week_realised_stats_excluded=true`.
2. `max_input_week` must be strictly smaller than `target_week`.
3. Player baseline features are shifted before rolling/expanding calculations.
4. Target-week fantasy points are used only as the evaluation outcome.
5. Historical opponent identity comes from the explicit `opponent_team` field in weekly player statistics rather than target-week realized play-by-play.
6. Every model fold trains on seasons strictly earlier than the test season.
7. Baseline and challenger use exactly the same complete-case rows.
8. Missing trench measurements are dropped for that paired benchmark and never zero-imputed.

## Model comparison

Both models use the same fixed pipeline:

* StandardScaler fitted on training rows only
* Ridge regression
* fixed alpha = 10
* no hyperparameter search

Baseline:

`player form`

Challenger:

`player form + one pre-specified trench family`

This is not a competition among many tuned models. Each position/family must independently clear the fixed gates.

## Validation gates

A family becomes `RESEARCH_VALIDATED_CANDIDATE` only if all gates pass:

* at least 300 total out-of-sample rows
* at least 3 chronological test-season folds
* at least 25 rows in every admitted test fold
* at least 100 training rows in every admitted fold
* at least +0.5% paired MAE improvement
* RMSE must not worsen
* at least 60% of folds must improve MAE
* no fold may deteriorate MAE by more than 5%
* 95% bootstrap CI for the mean per-row absolute-error improvement must have lower bound > 0

Otherwise the status is `BLOCKED_NOT_VALIDATED` or `BLOCKED_INSUFFICIENT_EVIDENCE`.

## Thin integration contract

Output:

`data/research/evaluation/2026/trench/thin-integration-v1.json`

A validated family may be exposed only as:

`research_context_only`

Explicitly prohibited:

* production projection input
* canonical ranking input
* waiver-value input
* runtime input
* automatic model promotion

This lets later research windows consume a validated context signal without silently changing the production champion.

## Outputs

* `data/research/evaluation/2026/trench/window2b-trench-research-v1.json`
* `data/research/evaluation/2026/trench/window2b-trench-research-v1.md`
* `data/research/evaluation/2026/trench/thin-integration-v1.json`

The JSON contains source hashes, fold results, aggregate paired metrics, bootstrap intervals, gate decisions and blockers.

## Production governance

Window 2B does **not**:

* change M9
* promote M10
* change canonical rankings
* change current snapshots
* change waiver recommendations or bids
* change app runtime
* use ADP as a football feature
* claim that team trench proxies are isolated player grades

Any future production activation still requires the normal FIE promotion path and league-specific scoring/governance evidence.
