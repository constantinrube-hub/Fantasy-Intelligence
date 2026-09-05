# Tranche 3A Final Release-Gate Compatibility Patch

## Scope

This patch changes validation only. It does not modify Core, A3, D, rankings,
projections, replacement/scarcity/VOR calculations, ADP handling, or research
promotion/governance.

## Failure addressed

The Tranche 3A target and all 22-league Core/A3/D parity tests passed. The
canonical release build was blocked only by the legacy V9.3.1 completion test,
which still searched Core source text for the historical literal:

`canonical structural starter-slot demand`

C10-004 replaced that old implementation wording with the canonical
`FIECore.ReplacementService` contract.

## Replacement guard

The legacy completion test now verifies the current structural ownership
contract instead:

- `FIECore.ReplacementService`
- `replacement_player_rank_1_based`
- `replacementRankForDemand`
- canonical replacement level from structural cutoff
- absence of the old `projectedReplacementLevels` duplicate implementation

Numerical and cross-layer correctness remain governed by the permanent Tranche
3A tests already present in the release gate:

- `integrity_tranche3a_replacement_ownership.js --mode target`
- `integrity_tranche3a_all_league_replacement_profiles.js`

## Workflow trigger

The active Tranche 3A workflow now explicitly watches this completion test, so
this patch automatically reruns Tranche 3A.
