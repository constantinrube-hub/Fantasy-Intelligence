# Tranche 6C — Point-in-Time Evidence Hardening

## Boundary

Tranche 6C records provenance for evidence that is actually captured prospectively. It changes neither FIE forecasts, rankings, recommendations, scoring, runtime behavior, model selection, nor production authorization. M9 remains champion and the Tranche 6A/6B verdict remains `PROMOTION_BLOCKED`.

## Artifact and validation

- Evidence and coverage-age report: `data/research/portfolio/2026/point-in-time-evidence-report.json`
- Builder: `research/build_fie_point_in_time_evidence_report.py`
- Deterministic validator: `research/validate_fie_point_in_time_evidence_report.py --verify-deterministic`
- Focused contract: `research/integrity_tranche6c_point_in_time_evidence.py --mode preflight`

The report inventories only committed immutable snapshot files and their sidecars. For each source it records the source endpoint/release-cadence contract, captured time, evidence `as_of`, exact snapshot SHA-256, first-write status, provider release/revision availability, and capture age relative to the latest stored capture. That reference is itself stored evidence, not the clock or a current provider request, so a rebuild is deterministic.

## Provider revision semantics

The Sleeper endpoints used by these archives do not expose an immutable provider release or revision identifier. New captures therefore write explicit metadata stating `NOT_EXPOSED_BY_PROVIDER`; this is honest missing metadata, not a synthetic revision. Older immutable captures retain their original sidecars and appear as `LEGACY_METADATA_INCOMPLETE` until future first-write captures use the hardened schema.

The scheduled season-market, availability, and pregame-market workflows now rebuild and validate the report whenever they capture a new immutable snapshot, then commit the report with that snapshot.

## Fail-closed coverage policy

Existing 2026 captures are prospective evidence only. They are not completed historical seasons, and the report explicitly keeps `completed_historical_seasons` empty. No present-day endpoint, date label, depth-chart order, or later result may create an earlier forecast, injury state, market value, or release revision. Missing history remains an `INSUFFICIENT_HISTORY` blocker for research and promotion.

## Controlled validation lifecycle

The target validated successfully at `7b80acc95603f81794c7ef1ffd8d2caaf9f6e3a4` in GitHub Actions run `33932408549` (54 seconds, `DEPLOYABLE_SOURCE`). Its release artifact SHA-256 is `b0914c05338f0201bbc72c754f3b968efb9b163dce9fc611a52aac7d48083a44`. The verified generated synchronization is limited to `config/build-manifest.json`, `config/release-gate.json`, and `dist/config/build-manifest.json`.

The validator has returned to the repository-wide manual-only historical-validation policy. Scheduled market and availability evidence capture remain active operational workflows.
