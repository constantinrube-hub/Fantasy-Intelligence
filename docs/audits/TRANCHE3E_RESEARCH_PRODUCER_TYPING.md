# Tranche 3E — C10-005 Research Producer Typing

## Status

Target implementation package. It is releasable only after the dedicated workflow is green and the canonical release build reports `DEPLOYABLE_SOURCE`.

## Problem proven by preflight

The unified research manifest gave `feature_evidence`, `production_shadow`, and `controlled_runtime` status labels, but pointed them at unrelated strategy/current artifacts. It did not identify the exact producer, validator, artifact type, or schema even though dedicated governed bundles existed.

## Target contract

Each stage now carries four mandatory identity fields:

- `artifact_type`
- `producer`
- `validator`
- `schema`

The canonical registry lives in `research/fie_research_pipeline_contract.py`. The unified runner resolves the exact output path, validates the dedicated artifact before successful reuse, and records its SHA-256. Missing artifacts remain `blocked_data`; validator failures stop the pipeline.

## Exact ownership

- Feature evidence: base evidence plus hardened evidence producer; base and hardening validators; `fie-feature-evidence-v1`.
- Production shadow: dedicated shadow producer and validator; `fie-production-shadow-v1`.
- Controlled runtime: dedicated V9.6 bundle producer and validator; `fie-v96-runtime-v1`.

Expensive regeneration occurs only through explicit `--force-stage` or `--force-rebuild`. Reuse never silently accepts an untyped or unvalidated artifact.

## Explicitly unchanged

- football-model coefficients, projections, rankings, and format weights
- replacement, scarcity, and VOR economics
- ADP remains outside the football model
- promotion and statistical thresholds
- automatic model promotion remains disabled
- Tranches 3A through 3D and all 22 league/six-format contracts
