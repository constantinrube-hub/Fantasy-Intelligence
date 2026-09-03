# Tranche 3E Preflight — C10-005 Research Producer Typing

## Purpose

This preflight characterizes the research-stage provenance gap that remained
deliberately frozen through Tranches 3A–3D. It changes no runtime behavior,
football value, ranking, projection, league configuration, model-promotion
threshold or application surface.

The validated starting point is Tranche 3D commit
`e89363ab575aa2a35f23cf8e103fb94e2ea37f8e`, GitHub Actions run
`33799110079`.

## Audited baseline

The pilot league `1391803939736801280` has stage-manifest entries for:

- `feature_evidence`
- `production_shadow`
- `controlled_runtime`

Those entries already carry status, reason and governed output paths. Dedicated
implementations and validators also exist. However, the manifest entries do not
identify their exact `artifact_type`, `producer`, `validator` or `schema`, and
the unified runner does not reference the dedicated producer filenames.

The required preflight result is:

`KNOWN_GAP_REPRODUCED unified research stages are status-labelled but not typed to exact dedicated producers`

This is a successful characterization result, not a release failure.

## Later target contract

The target implementation will make the unified runner the explicit
orchestrator of the dedicated research producers and require each governed
stage output to declare:

- artifact type
- exact producer
- exact validator
- schema identity

Missing or ambiguous provenance must fail closed. A stage may not become
production evidence merely because a file exists or a status string says it is
complete.

## Preservation boundary

The preflight permanently preserves the completed contracts from Tranches
3A–3D, all 22 enabled league profiles and six formats, the ADP/model boundary,
league isolation, statistical thresholds, explicit promotion and atomic
publication. No runtime or generated research artifact is rewritten by this
package.

## Preflight exit condition

The preflight is complete only when GitHub Actions:

1. verifies ancestry from the completed Tranche 3D commit;
2. reproduces the exact C10-005 known-gap marker under Bash `pipefail`;
3. preserves the earlier tranche contracts;
4. completes the canonical release build as `DEPLOYABLE_SOURCE`; and
5. captures only the three permitted deterministic synchronization files, if
   the new audit metadata changes the generated manifest.

Only then may the C10-005 target implementation begin.
