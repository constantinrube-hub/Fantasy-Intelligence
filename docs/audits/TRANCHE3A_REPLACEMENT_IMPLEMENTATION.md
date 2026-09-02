# Tranche 3A — C10-004 Replacement / Scarcity / VOR Ownership

Baseline: `a3e75122de8f2ab2ae5ed34f62f4162b896f0f49`

## Purpose

Make starter demand, structural replacement, downstream scarcity and projected VOR use one canonical replacement frontier.

## Canonical ownership

- `FIECore.LeagueDemandService` owns starter-slot demand.
- `FIECore.ReplacementService` owns structural replacement rank/cutoff.
- `cutoff` means the **1-based rank of the replacement player**.
- For an integer structural demand of N players, the replacement player is rank N+1.
- Actual ownership is diagnostic only and does not change football replacement value.
- A3 is a performance adapter over the Core frontier.
- V9.3.4D derives starter probability, scarcity, downside and marginal economics from that frontier.
- Projected VOR is calculated against the canonical projected replacement player and carries `projectedVORSource` and `projectedReplacementCutoff`.

## Why the cutoff changes by one in integer-demand fixtures

Before 3A, Core's `cutoff` identified the last demanded starter while D independently called the next player the replacement player. Both conventions were active.

3A chooses one explicit convention: **replacement-player rank**. Therefore, if four QBs are structurally demanded, QB5 is the replacement player and the canonical cutoff is 5.

This is an intended football-economics correction and can move VOR/scarcity/ranking values.

## Ownership feedback removed

A3 previously blended actual owned-player counts into replacement when `ownershipInfluence` was non-zero and also used ownership pressure inside league-fit scarcity.

After 3A:

- actual owned count remains available for diagnostics;
- `ownershipInfluence` cannot move the structural football cutoff;
- A3 league-fit scarcity uses structural pressure from Core rather than actual ownership.

Market/availability state therefore cannot feed back into player-quality/replacement value.

## D economics

V9.3.4D still owns its derived economics outputs, including starter probability, scarcity multiplier, floor/downside and marginal lineup utility.

It no longer owns a second replacement selector. Its replacement row now carries:

- `replacementRank`
- `structuralCutoff`
- `sourceCutoff`
- `replacementSource`
- `cutoffConvention`

all originating from `FIECore.ReplacementService`.

## Permanent validation

The release gate now includes:

- `integrity_tranche3a_replacement_ownership.js --mode target`
- `integrity_tranche3a_all_league_replacement_profiles.js`

The all-league test evaluates all 22 enabled league profiles and requires Core/A3/D replacement parity for every structurally active position.

## Explicit non-changes

No change to:

- ADP boundary;
- candidate-model promotion;
- research statistical thresholds;
- M6/current-feature promotion gates;
- league-format capability semantics;
- responsive UI behavior;
- DataClient;
- player identity;
- uncertainty/calibration semantics;
- workflow or artifact cleanup.

## First GitHub target run

The canonical release build is allowed to regenerate only:

- `config/build-manifest.json`
- `dist/config/build-manifest.json`

Any additional uncommitted source/dist drift fails the workflow. The exact two generated manifests are then synchronized in a final commit.
