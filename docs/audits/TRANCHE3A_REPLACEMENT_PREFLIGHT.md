# Tranche 3A Preflight — C10-004 Replacement / Scarcity / VOR Ownership

Baseline commit: `261bd8539b6ee91d2cfb5a8b6b586a7fdf3e33a0`  
Baseline tree: `20253eccc5130201986e3ca1f2cf38c03bec23df`

## Why 3A is isolated

The audit found three active replacement conventions:

1. `FIECore.ReplacementService` owns structural starter-demand/replacement logic.
2. V9.3.4A3 recomputes demand/replacement in its scoring hot path and can blend actual ownership into the cutoff.
3. V9.3.4D independently defines replacement as the first non-starter and therefore commonly uses `Core cutoff + 1`.

That can change replacement points, VOR, scarcity and downstream value depending on the consumer.

## Frozen target contract

The implementation after this preflight must satisfy all of the following:

- `FIECore.LeagueDemandService` is the sole starter-demand owner.
- `FIECore.ReplacementService` is the sole structural replacement-cutoff owner.
- Canonical cutoff convention is **1-based rank of the replacement player**.
- Actual ownership remains diagnostic and must not feed back into football replacement value.
- Bench reserve influence, if retained, is defined once inside Core.
- A3 remains a hot-path/performance adapter and consumes batched Core profiles.
- D derives starter probability, scarcity, downside and economics from the Core cutoff rather than selecting a separate replacement row.
- Projected VOR is produced from the canonical projected replacement level and carries explicit source/cutoff provenance.
- No hidden format-specific replacement convention is introduced; league structure and scoring/profile inputs remain league-specific.
- ADP remains outside the football model.
- No research/statistical/governance thresholds are weakened.

## This preflight changes no runtime behavior

The preflight only adds:

- a baseline/target characterization test;
- a source-capture helper;
- this audit document;
- a marker JSON;
- a validation workflow.

It does not edit Core, A3, D, VOR, projections, rankings, scarcity, DataClient, identity, or uncertainty code.

## Expected baseline findings

The preflight must reproduce:

- Core/A3 demand parity under the simple zero-influence fixture;
- A3 projected cutoff parity with Core at zero ownership influence;
- D replacement rank using the separate first-non-starter convention;
- A3 cutoff moving when ownership influence is set to 100%;
- Core structural cutoff staying ownership-invariant;
- no canonical VOR source/cutoff tags yet.

## Source capture

The workflow exports exact current bytes for Core, A3, D and their main consumers/tests. The implementation package is built only from that artifact.

## Hard stop

Do not implement C10-006, C10-007, or C10-009 until the 3A target implementation is green.
