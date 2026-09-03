# Tranche 3D — C10-009 Evidence Semantics

## Status

Target implementation package. Validation must remain fail-closed until the dedicated Tranche 3D workflow is green and the canonical release build reports `DEPLOYABLE_SOURCE`.

## Problem proven by preflight

The preflight showed that FIE already had useful evidence concepts, but each runtime surface described them differently:

- Projection Resolver had source, confidence, availability, bye and calibrated/heuristic range distinctions.
- Current features carried completed-week freshness and lineage.
- Current snapshots carried artifact provenance.
- D/ST and kicker used local `source`, `estimate`, range and future-baseline vocabulary.
- There was no single typed owner for evidence status or uncertainty class.

## Target architecture

`FIEEvidenceSemantics` is the single metadata owner. It adds `fie-evidence-v1` evidence objects to existing public runtime APIs without moving or recomputing any football-model value.

Canonical evidence status:

- `observed`
- `modeled_available`
- `modeled_unavailable`

Canonical uncertainty kind:

- `calibrated_range`
- `heuristic_range`
- `exact`
- `unavailable`
- `not_applicable`

Canonical fields:

- `evidenceStatus`
- `source`
- `asOf`
- `confidence`
- `reason`
- `fallback`
- `uncertaintyKind`
- `availability`
- `byeState`
- `low` / `high`
- `leagueLocalProvenance`

## Adapter boundary

The new owner wraps only public metadata-bearing APIs:

1. `FIEProjectionResolver.week()` / `range()`
2. `FIECurrentFeatures.apply()` / `lineage()`
3. `FIECurrentSnapshotStore.load()`
4. `FIEDST.board()`
5. `FIEKicker.board()`

The wrappers preserve existing keys and values, then append `asOf` and/or `evidence` metadata. D/ST and kicker internal decision scoring remains untouched.

## Important semantic decisions

- A verified schedule bye is `observed`, `available`, `bye`, and `exact`; its projection remains the existing true zero.
- Missing projection data remains `null` / unavailable and is typed `modeled_unavailable`.
- Governed, Sleeper and fallback projections that exist are `modeled_available`.
- Empirical P10/P90 is `calibrated_range`.
- Percentage or season-baseline fallback intervals are `heuristic_range`.
- A season projection divided by 17 remains the existing explicitly-labelled fallback; Tranche 3D does not change the calculation.
- Current research features are evidence from completed historical games; governance eligibility is retained separately from evidence existence.
- `asOf` is derived only from existing artifact/source timestamps. The contract does not invent freshness timestamps.

## Runtime loading

`app/current-snapshot-store.js` boots `app/core/evidence-semantics.js` as a separate adapter module. The module is idempotent and retries attachment at browser lifecycle boundaries so it can safely enrich APIs regardless of static script definition order.

## Validation

The permanent Tranche 3D runtime integrity test requires:

- exact preservation of governed projection values/source/confidence,
- exact preservation of calibrated range values,
- unchanged season/17 fallback value,
- unchanged heuristic 0.78/1.22 range math,
- unavailable remains null,
- verified bye remains zero,
- current feature evidence attachment,
- snapshot evidence attachment,
- D/ST and kicker API evidence attachment,
- source/dist parity for the new module and bootstrap owner.

The existing release gate also continues to execute all earlier Tranche 2A/2B/2C, 3A, 3B and 3C contracts.

## Explicitly not changed

- football coefficients or projections
- format weights
- scarcity/replacement/VOR
- player identity
- DataClient scope semantics
- ADP/model boundary
- research promotion thresholds
- immutable market or availability evidence
- workflow or artifact cleanup
- visual redesign
