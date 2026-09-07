# Window 2D — Context Foundation

## Status

`IMPLEMENTED_RESEARCH_ONLY`

Window 2D creates the governed point-in-time context surface required for later contextual research. It does not estimate or apply weather, rest, venue, coaching, travel, availability or trench multipliers.

## Objective

The foundation joins context with stable identifiers and exact provenance before asking whether any context is predictive. This prevents a later research phase from mixing post-game facts, stale current data, unvalidated trench signals, market information or silently imputed context.

## Bound context families

### Game identity

* season
* week
* game ID
* kickoff
* home team
* away team
* opponent symmetry

Primary schedule source:

`nflverse nfldata games.csv`

### Venue

Where available from the governed schedule/weather evidence:

* roof
* surface
* stadium
* stadium ID

Venue is descriptive only in Window 2D.

### Weather

Consumes Window 1A point-in-time weather evidence.

Fields can include:

* forecast observed time
* forecast effective time
* temperature
* precipitation probability
* wind
* gusts
* roof/surface

A forecast observed after the applicable cutoff is rejected. Missing forecast values remain missing.

### Rest

Rest is calculated only from scheduled regular-season kickoffs that occurred before the current game's point-in-time cutoff.

Descriptive classes:

* `< 6.5 days`: `SHORT_REST`
* `6.5–8.5 days`: `NORMAL_REST`
* `> 8.5 days`: `EXTENDED_REST`

These are labels only. No fantasy effect is assumed.

### Availability v2

Window 2D binds the exact Window 2C artifact by path and SHA256 and exposes team/player availability context without adding projections.

### Trench

Window 2D reads:

`data/research/evaluation/2026/trench/thin-integration-v1.json`

Only rows satisfying all of the following may appear:

* `enabled = true`
* `status = RESEARCH_VALIDATED_CANDIDATE`
* `allowed_surface = research_context_only`

A malformed enabled row fails closed. Rejected Window 2B trench families do not enter the context surface. If the Window 2B registry itself has not yet been generated, the overall 2D bundle is explicitly `PARTIAL_RESEARCH_ONLY` with `window2b_thin_integration` listed as a missing dependency. A present registry with zero validated candidates is fully valid.

## Explicitly not bound in v1

### Travel

`NOT_BOUND_V1`

Window 2D does not fabricate travel distance, time-zone shift or neutral-site routing from incomplete coordinates.

### Coaching

`NOT_BOUND_V1`

Window 2D does not assume a point-in-time coaching history source that has not yet been governed. HC/OC/DC fields remain null.

These families can be bound later without changing the context contract once trustworthy prospective/historical evidence exists.

## Output

`data/research/context/foundation/<season>/week_<week>/<timestamp>/context-foundation-v1.json`

The snapshot contains:

* source bindings and hashes
* feature-family readiness/status
* game context
* team context
* player availability context
* validated trench registry context
* explicit governance flags

It is immutable first-write at its point-in-time timestamp.

## Governance invariants

* production champion remains M9
* research-context surface only
* no context predictive weights
* no projection deltas
* no ranking deltas
* no waiver-value changes
* no automatic promotion
* ADP/market excluded
* target-week realized stats excluded
* missing context not zero-imputed
* post-cutoff weather/availability rejected
* Window 2B rejected signals remain rejected

## Integrity coverage

`research/integrity_window2d_context_foundation_test.py`

Current synthetic suite: **34/34 checks passing**.

Coverage includes game and opponent symmetry, site identity, kickoff binding, pre-cutoff weather, missing weather, rest chronology, future-game exclusion, 2C availability linkage, unbound travel/coaching behavior, validated-only trench integration, M9/runtime/ranking/waiver protections, market/ADP exclusion, exact artifact hashes, post-as-of rejection, immutable first-write behavior and deterministic assembly.

## Relationship to Window 2E

Window 2D is the final **foundation/build** stage through the roadmap's 2D target. It deliberately does not answer whether weather, rest, home/away, coaching, travel or other context improves predictions.

That empirical question belongs to **Window 2E — Context Research + Integration**. Final verification/control after 2D should decide which 2D families have sufficient evidence to justify 2E now and which can remain deferred without blocking the current production system.
