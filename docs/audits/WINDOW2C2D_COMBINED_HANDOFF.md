# Window 2C + 2D Combined Handoff

## Purpose

This handoff completes the technical implementation roadmap through **Window 2D** in one controlled package:

* Window 2C: Availability v2 + Opportunity Redistribution
* Window 2D: Context Foundation

It builds on the already completed 1A evidence backbone and 2B trench thin-integration registry. GitHub `main` remains the authority after the package is uploaded and the combined workflow succeeds.

## Included files

1. `research/window2c_availability_v2.py`
2. `research/integrity_window2c_availability_v2_test.py`
3. `config/window2c-availability-v2-redistribution.json`
4. `docs/audits/WINDOW2C_AVAILABILITY_V2_REDISTRIBUTION.md`
5. `research/window2d_context_foundation.py`
6. `research/integrity_window2d_context_foundation_test.py`
7. `config/window2d-context-foundation.json`
8. `docs/audits/WINDOW2D_CONTEXT_FOUNDATION.md`
9. `.github/workflows/build-fie-window2c2d-foundation.yml`
10. `docs/audits/WINDOW2C2D_COMBINED_HANDOFF.md`

## Dependency state at handoff

The Window 2B implementation files are present on `main`, but the generated artifact

`data/research/evaluation/2026/trench/thin-integration-v1.json`

was not present when this handoff was built. That means the Window 2B research workflow still needs to execute at least once. Window 2D treats a missing registry as an explicit `PARTIAL_RESEARCH_ONLY` dependency rather than silently assuming that zero trench candidates passed.

Correct first-run order:

1. `Build FIE Window 2B Trench Research`
2. `Build FIE Window 2C+2D Foundation`
3. final verification/control

If Window 2B completes with zero validated candidates, its registry should still exist; that is a valid scientific result and Window 2D can be fully ready with zero enabled trench candidates.

## Combined workflow

Workflow name:

`Build FIE Window 2C+2D Foundation`

Default manual inputs for the initial 2026 Week 1 run:

* season: `2026`
* week: `1`
* capture fresh evidence: `true`
* opportunity baseline: blank

Leaving the opportunity baseline blank is intentional unless a governed `fie-opportunity-baseline-v1` file exists. Window 2C will still build availability and unquantified recipient scenarios, but it will not fabricate numeric redistribution shares.

The workflow:

1. validates both engines, both integrity suites and both configs
2. optionally refreshes prospective Sleeper availability and weather evidence
3. freezes one shared `as_of` timestamp
4. builds Window 2C
5. builds Window 2D
6. checks that prohibited production/ranking/market surfaces were not modified
7. commits only governed research evidence paths

## Allowed write surfaces

* `data/research/availability/sleeper`
* `data/research/context/weather`
* `data/research/availability/v2`
* `data/research/context/foundation`

The workflow explicitly rejects changes to app/runtime, league current/performance/app artifacts, strategy data and market/ADP surfaces.

## Verification state before GitHub execution

Local/static synthetic validation:

* Window 2C: **26/26 checks passing**
* Window 2D: **34/34 checks passing**
* total: **60/60 checks passing**
* Python syntax checks: passing
* JSON config validation: passing
* workflow YAML parse: passing

Real-source execution remains a GitHub workflow responsibility because it must consume the repository's actual prospective evidence and current 2B registry.

## What is complete after a green run

A green combined run means the repository has technically completed implementation through Window 2D:

* prospective availability normalization is bound
* redistribution scenarios are governed and fail closed
* context identities/provenance are bound
* weather/venue/rest context is assembled descriptively
* 2C is SHA-bound into 2D
* only 2B-validated trench candidates can enter context
* production M9 remains unchanged

## What is not complete

Window 2E is **not** implemented by this handoff.

Window 2E would test whether contextual families add incremental out-of-sample predictive value and, only if they clear pre-specified gates, define a thin research integration. It must not be inferred from 2D descriptive context.

## Recommended next step after the workflow

Run one final repository-wide **verification/control pass for 0.1 through 2D**. That pass should verify:

* all intended files and outputs exist
* all workflows are green
* baseline/hash/governance contracts still hold
* M9/runtime/canonical rankings remain uncontaminated
* research outputs are provenance-complete
* blocked states are genuine evidence gaps, not implementation errors
* offline Season Preview artifacts remain present and readable

Then classify Window 2E as either:

* `REQUIRED_NOW` for context families with sufficient evidence and immediate value, or
* `DEFERRED_RESEARCH` where evidence is not yet mature and no production blocker exists.

This preserves the roadmap without pretending that contextual predictive effects have already been validated.
