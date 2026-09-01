# Controlled Implementation — Tranche 2A Six-Format Correction

**Change package:** C10-001 FORMAT_CORRECTNESS  
**Scope:** production semantic correction for `CHOPPED_BESTBALL` only  
**Research promotion:** NO  
**ADP football-model influence:** NO  
**Cleanup:** NO

## Canonical capability owner

`config/contracts/runtime-contracts.json` now defines all six supported league formats and their three orthogonal capabilities: dynasty, best ball and chopped. Generated JS/Python contracts carry the same definition.

## Hybrid production semantics

`CHOPPED_BESTBALL` is an explicit equal blend of the already-production Chopped and Redraft Best Ball objectives. It does not activate the V9 research challenger.

- Core / Monte Carlo: 50.0% weekly mean + 22.5% weekly floor + 27.5% weekly ceiling.
- D/ST: 56.5% mean + 21.0% lower bound + 22.5% upper bound, exactly the 50/50 blend of the prior D/ST Chopped and Best Ball scores.
- DraftBase: component weights are the component-wise average of the prior Chopped and Redraft Best Ball production architectures.
- Calibration: hybrid uses scarcity weight 8, equal to both parent formats.

The five pre-existing format objectives retain their previous numerical definitions.

## Boundaries intentionally not changed

Replacement/VOR ownership, DataClient scope behavior, research producer identity, responsive column behavior, documentation lifecycle and cleanup remain for their later controlled tranches.
