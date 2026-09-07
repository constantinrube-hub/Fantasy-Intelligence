# Window 2C — Availability v2 + Opportunity Redistribution

## Status

`IMPLEMENTED_RESEARCH_ONLY`

Window 2C upgrades the prospective Window 1A Sleeper availability archive into a typed, pre-kickoff contract and a guarded opportunity-redistribution scenario layer. It does not change M9, app/runtime projections, canonical rankings, waiver values, or market/ADP handling.

## Why this layer exists

A player's injury or roster designation has two separate questions:

1. Is the player expected to be available?
2. If the player is absent, where could the player's role/opportunity move?

Window 2C intentionally does not collapse those questions into a fantasy-point multiplier. Availability evidence is preserved first. Redistribution is a separate scenario and is quantified only when an explicit pre-cutoff opportunity-share baseline exists.

## Inputs

Primary evidence owner:

`research/capture_fie_availability.py`

Archive:

`data/research/availability/sleeper/<season>/availability_<date>.jsonl.gz`

Schedule/kickoff binding is taken from the point-in-time weather/context archive produced by:

`research/capture_fie_weather.py`

Each team is bound to its own game kickoff. For that team, Window 2C selects the latest availability snapshot observed no later than both:

* the team's kickoff
* the Window 2C run `as_of`

A later snapshot is never used to reconstruct an earlier game state.

## Availability states

The normalized contract is deliberately conservative:

* `AVAILABLE`
* `LIMITED`
* `QUESTIONABLE`
* `DOUBTFUL`
* `OUT`
* `IR`
* `PUP`
* `NFI`
* `SUSPENDED`
* `INACTIVE`
* `UNKNOWN`

Confirmed unavailable states:

`OUT`, `IR`, `PUP`, `NFI`, `SUSPENDED`, `INACTIVE`

Uncertain states:

`LIMITED`, `QUESTIONABLE`, `DOUBTFUL`

Uncertain states are never automatically converted into absences. Missing evidence is never interpreted as healthy/available.

## Redistribution contract

Window 2C does not invent opportunity shares from rankings, ADP, fantasy projections or depth-chart order.

Quantified redistribution requires an explicit JSON input with schema:

`fie-opportunity-baseline-v1`

Each row must include:

* `sleeper_id`
* `team`
* `role_family`
* `baseline_share`
* `observed_at`
* optional provenance/source metadata

A player may have multiple rows when opportunity is decomposed into distinct role families such as `CARRIES`, `TARGETS` or `SNAPS`. Each role family is redistributed and conserved separately.

The opportunity evidence must be observed before the player's kickoff.

For a confirmed absence, the scenario type is:

`CONFIRMED_ABSENCE`

For `LIMITED`, `QUESTIONABLE` or `DOUBTFUL`, the scenario type is only:

`IF_ABSENT_SCENARIO`

Allocation rules:

* same team only
* same explicit role family only
* unavailable recipients excluded
* recipient weights come only from the supplied baseline opportunity shares
* vacated share must equal redistributed share plus explicit unallocated residual
* no zero-imputation
* no cross-team fallback
* depth-chart order may sort candidate recipients but is never a quantitative allocation weight

Existing FIE/M7 research includes lagged opportunity features such as carry, target and snap shares, but Window 2C does not silently reinterpret a model feature as a redistribution contract. A later adapter may expose those fields through `fie-opportunity-baseline-v1` once identity, role-family semantics and point-in-time provenance are explicitly bound.

If the trigger player's baseline share is missing, the scenario remains:

`BLOCKED_OPPORTUNITY_BASELINE_MISSING`

Candidate recipients can still be listed as unquantified context, but no numerical opportunity gain is invented.

## Outputs

Point-in-time snapshots are first-write immutable:

`data/research/availability/v2/<season>/week_<week>/<timestamp>/availability-v2.json`

`data/research/availability/v2/<season>/week_<week>/<timestamp>/redistribution-v2.json`

The timestamped layout allows later in-week evidence to create a new prospective snapshot without mutating earlier evidence.

## Governance invariants

* production champion remains M9
* research only
* no fantasy-point injury haircut
* no calibrated absence probability is invented
* no automatic model promotion
* canonical rankings unchanged
* runtime unchanged
* waiver values unchanged
* ADP and market excluded as football features
* target-week realized stats excluded
* post-kickoff evidence rejected
* missing opportunity evidence remains missing

## Integrity coverage

`research/integrity_window2c_availability_v2_test.py`

Current synthetic suite: **26/26 checks passing**.

Coverage includes typed state mapping, team-specific cutoff selection, post-kickoff rejection, uncertainty semantics, same-team/same-role allocation, unavailable-recipient exclusion, conservation, missing-opportunity blocking, invalid-share rejection, immutable first-write behavior and deterministic rebuilds.

## What Window 2C does not claim

Window 2C does not claim that an OUT designation causes a specific fantasy-point reduction or that a recipient receives a specific fantasy-point increase. It models only a governed availability state and, where supported, a counterfactual opportunity-share redistribution scenario. Any predictive fantasy effect still requires downstream validation.
