# D/ST Implementation and Evaluation Guide

## Purpose

Fantasy Intelligence 9.1 now treats team D/ST as a first-class rosterable entity without pretending a team defense is an IDP player. The implementation separates football prediction from league scoring and keeps final value inside the canonical 9.1 lineup, replacement and decision services.

The production rule remains fail-closed: D/ST research may exist diagnostically, but FIE does not replace the Sleeper D/ST baseline unless chronological validation clears the D/ST gate.

## Current managed-league inventory

The repository contains 19 managed leagues. Four currently roster a team D/ST:

| League ID | Format | League | D/ST scoring signature |
| --- | --- | --- | --- |
| `1313697754907697152` | REDRAFT | ReDraft – Pro 🎯 XVI Football | `2ef1ecf44d875b52` |
| `1316165875291668480` | DYNASTY | Genesis Dynasty - sixteen now & for the future | `fb63ba5d2005db9c` |
| `1387106650413887488` | REDRAFT | German Football League | `2ef1ecf44d875b52` |
| `1391803939736801280` | REDRAFT | SLR2026 - Liga 38 | `2ef1ecf44d875b52` |

The other 15 leagues may contain D/ST scoring keys in Sleeper, but they have no `DEF` roster slot. FIE therefore suppresses team D/ST from their actionable pools and UI.

Three D/ST leagues share the same standard-style scoring signature. Genesis has a materially different signature with additional return-yard, pass-defense, fourth-down-stop and return-yard scoring.

Current inventory: 4 D/ST leagues, 2 unique D/ST scoring signatures, 0 unsupported active D/ST scoring keys.

## Architecture

```text
Historical/current NFL events
        ↓
Canonical team-week D/ST outcomes
        ↓
Defense quality + opponent vulnerability + game environment
        ↓
Raw-stat forecasts
(sacks, INT, fumbles, TD, PA, YA, return/ST components)
        ↓
Exact league D/ST scoring signature
        ↓
League-specific projection distribution
        ↓
Canonical FIE 9.1 services
(lineup → replacement → roster marginal → decisions)
        ↓
D/ST Intelligence / Draft / Waiver / Start-Sit
```

### Key rule

The football model is not trained separately for every league. Raw football outcomes are modeled once. Fantasy points are produced afterward through each league's exact scoring rules.

This is what makes league-specific D/ST rankings mathematically coherent while avoiding 19 independent and redundant NFL models.

## Important market-line convention

nflverse `spread_line` is originally home-team perspective. The D/ST research layer normalizes it to the team row:

- positive `spread_line` = this D/ST is favored;
- negative `spread_line` = this D/ST is an underdog.

Opponent implied points are then:

```text
(total_line - team_favored_by) / 2
```

The same convention is used by historical training, current snapshots and the browser UI.

## Files

### New

- `research/fie_dst.py` — team-week construction, exact scoring, features, chronological validation, model export and D/ST milestone augmentation.
- `research/dst_contract.py` — canonical D/ST roster/scoring signatures and scoring-key recognition.
- `research/integrity_dst_test.py` — scorer, Sleeper points-allowed attribution, Genesis custom scoring, market normalization and runtime integration tests.
- `app/dst-intelligence.js` — compact D/ST decision surface.
- `data/research/dst/scoring_inventory.json` — portfolio-wide D/ST scoring audit.

### Integrated

- `research/build_current_snapshot.py`
- `research/league_profile.py`
- `research/fie_research.py`
- `research/generated_runtime_contracts.py`
- `config/contracts/runtime-contracts.json`
- `app/generated/runtime-contracts.js`
- `.github/workflows/build-fie-research.yml`
- `.github/workflows/build-fie-current.yml`
- `index.html`

## What the historical workflow does

For a league with a DEF roster slot, `Build FIE Research Milestones 1-6` now performs the normal M1-M6 build and then runs:

```bash
python research/fie_dst.py augment \
  --profile <league>/profile.json \
  --m1 <league>/milestone1.json \
  --m2 <league>/milestone2.json \
  --m3 <league>/milestone3.json \
  --m4 <league>/milestone4.json \
  --m5 <league>/milestone5.json \
  --m6 <league>/milestone6.json \
  --derived-dir <cache>/derived \
  --cache-dir <cache> \
  --seasons 2016-<last-complete-season>
```

The D/ST stage:

1. downloads/uses historical nflverse data through the existing SourceManager;
2. builds one team-defense row per game;
3. reconstructs Sleeper-style D/ST raw outcomes;
4. creates strictly lagged defense and opponent-vulnerability features;
5. normalizes game-market context;
6. fits raw-outcome candidate models;
7. evaluates them on chronological expanding-season folds;
8. scores model outputs through the exact league D/ST scoring signature;
9. compares against transparent historical baselines;
10. writes D/ST sections into M1-M6;
11. promotes `DEF` only if the validation contract clears;
12. otherwise leaves production on the Sleeper baseline.

## Required workflow sequence after uploading this repository

### Step 1 — Push the complete updated repository

Push the repository to `main`. Do not upload only `index.html`; the D/ST change spans Python research, generated contracts, workflow YAML, data contracts and browser code.

### Step 2 — Run historical research for the four D/ST leagues

In GitHub Actions, run **Build FIE Research Milestones 1-6** separately for:

1. `1313697754907697152`, format `REDRAFT`
2. `1316165875291668480`, format `DYNASTY`
3. `1387106650413887488`, format `REDRAFT`
4. `1391803939736801280`, format `REDRAFT`

`full_raw_cache=false` is sufficient for the initial D/ST evaluation unless you specifically want the broader historical archive retained in cache.

The workflow commits each league's rebuilt artifacts back to `main` after a successful run.

### Step 3 — Inspect the D/ST validation result

For each D/ST league inspect:

- `data/research/leagues/<league_id>/milestone4.json`
- `data/research/leagues/<league_id>/milestone5.json`
- `data/research/leagues/<league_id>/milestone6.json`

The most important fields are under `dst`.

Key result:

```text
status = validated_candidate
```

means the historical candidate cleared the current D/ST validation contract.

```text
status = diagnostic_only
```

means the code ran successfully but the model did not beat the required baselines strongly/consistently enough. This is a useful research result and should NOT be manually forced into production.

Review:

- number of chronological folds;
- positive folds;
- mean MAE improvement;
- model vs baseline Spearman rank correlation;
- residual P10/P90;
- scoring coverage;
- D/ST scoring signature;
- supported/unsupported rule list.

### Step 4 — Refresh current-season snapshots

After the four historical builds succeed, run **Refresh FIE Current Season**.

Recommended initial inputs:

```text
league_id: [leave blank]
season: [leave blank]
week: [leave blank]
governance_mode: AUTO
```

Leaving `league_id` blank refreshes all enabled registered leagues. Non-D/ST leagues stay clean because the current builder now excludes `DEF` when the roster contract has no D/ST slot.

The refresh workflow:

- rebuilds the league-specific current snapshot;
- uses the validated D/ST model if its gate is open;
- otherwise keeps Sleeper as the baseline;
- updates governance;
- refreshes the D/ST scoring inventory;
- commits the resulting snapshots.

### Step 5 — Evaluate in the browser

Open one of the four D/ST leagues and use **D/ST Intelligence**.

The UI is intentionally ordered around decisions:

1. **Your D/ST**
2. **Best available**
3. **Best stash**
4. **Replacement line**
5. ranking table
6. selected-team explanation

The table exposes:

- league rank;
- opponent;
- ownership;
- action;
- projection;
- FIE vs Sleeper disagreement;
- low/high range when validated;
- next-three signal when validated;
- active model source.

A league without a D/ST slot should not show the D/ST Intelligence surface as an actionable section.

## How to interpret the first workflow results

### Best case

```text
D/ST historical status: validated_candidate
current row: weekly_activation_eligible = true
projection source: M6 FIE D/ST raw-outcome model
```

Then FIE is allowed to replace the Sleeper baseline for the validated decision domain.

### Model runs but fails validation

```text
D/ST historical status: diagnostic_only
projection source: Sleeper D/ST baseline (FIE gate off)
```

This is not a deployment failure. It means the candidate model needs better features/model structure before it deserves production authority.

Use the fold diagnostics to decide what to improve next.

### Scoring failure

Any active D/ST scoring key that cannot be reconstructed should block exact D/ST activation for that scoring signature. The current four active D/ST leagues have zero unsupported keys in the repository inventory.

## What to evaluate after the first connected run

Do not judge only by whether the model activates. Review the following in order.

### 1. Scoring correctness

- 100% active-rule coverage;
- bucket boundaries behave correctly;
- opponent defensive TDs are excluded from points allowed;
- ensuing PAT/2PT semantics match Sleeper;
- Genesis return/pass-defense/fourth-down rules are represented.

### 2. Historical predictive value

- MAE improvement vs baseline;
- rank correlation improvement;
- fold-to-fold stability;
- whether a small average gain is driven by one season only.

### 3. Early-season behavior

- Week 1 produces a meaningful prior rather than zero-history rejection;
- prior-season information is regressed rather than copied blindly;
- current-season observations gradually replace prior history.

### 4. League specificity

Compare the same D/ST across the standard scoring leagues and Genesis. The football prediction may be the same, but the fantasy score/rank should change when Genesis-specific return/pass-defense/fourth-down production matters.

### 5. Decision usefulness

Check whether the board provides a clear answer to:

- start my current D/ST or stream another one;
- which available D/ST has the best current-week value;
- whether carrying a second D/ST is justified by the next-three schedule;
- where the actual league replacement line sits.

## What is deliberately not auto-promoted yet

The current implementation keeps several advanced ideas as challengers until they have point-in-time history and independent validation:

- FTN charting;
- aggregated IDP personnel quality;
- richer injury impact;
- PFF-derived personnel signals;
- point-in-time weather;
- betting-line movement;
- independently validated stash/next-three policy;
- independently validated draft policy;
- D/ST-pair optimization for Best Ball.

These should be added as challenger features after the public-data baseline is measured, not mixed into the baseline simply because they sound predictive.

## Local release validation

Before packaging this repository, the following release command is the supported local build:

```bash
python tools/release_build.py --mode personal
```

The final source release gate must report:

```text
DEPLOYABLE_SOURCE
```

A browser preview remains required after deployment.

## Definition of the next review

After the four historical workflows and one current refresh have completed, the next D/ST review should answer:

1. Did both scoring signatures achieve exact reconstruction?
2. Did the FIE raw-outcome model beat the simple baseline chronologically?
3. Which raw components are strongest/weakest?
4. Is rank ordering improved even where MAE gain is modest?
5. Are residual ranges calibrated enough to expose Low/High?
6. Does Genesis materially reorder defenses vs standard scoring?
7. Does the actual replacement line change recommendations in the 16-team leagues?
8. Are Week 1 priors sensible?
9. Is next-three output trustworthy enough to graduate from diagnostic to decision policy?
10. Which advanced challenger family is most likely to add incremental value next?

That connected result set is the point at which D/ST can be evaluated empirically rather than architecturally.
