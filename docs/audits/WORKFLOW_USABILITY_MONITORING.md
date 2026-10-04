# Automatic workflow usability monitoring

Implementation boundary: operational evidence observability only. This contract does not alter forecasts, model eligibility, lineup decisions, waiver recommendations, scoring, or immutable evidence payloads.

## Problem closed

A green GitHub Actions conclusion proves that a job completed. It does not prove that the invocation produced usable evidence. Scheduled polling also creates legitimate runs where nothing is due. Those outcomes must not be counted together.

The active automatic evidence workflows now emit one small, run-bound artifact named `fie-workflow-usability`. A daily monitor builds a rolling 14-day report from those artifacts and GitHub run identity. The report covers scheduled runs only; manual repair and diagnostic dispatches remain outside the automatic reliability rate.

## Six-state contract

- `USABLE`: the invocation produced or verified a current, contract-valid result for its stated purpose.
- `NO_OP`: nothing was due, the immutable result already existed, or the calendar/poll policy correctly skipped production.
- `PARTIAL`: some intended evidence is usable, but declared source or portfolio coverage is incomplete.
- `BLOCKED`: the workflow completed technically but did not prove a usable result.
- `MISSED`: a time-bound prospective opportunity passed without a valid capture.
- `INFRASTRUCTURE`: the run did not complete successfully because of a technical, runner, validation, or delivery failure.

`USABLE` is the only state counted as a usable result. `NO_OP` is separately healthy and does not automatically merit investigation. `PARTIAL`, `BLOCKED`, `MISSED`, and `INFRASTRUCTURE` are included in the investigation table.

## Fail-closed behavior

- A successful run without a valid run-bound usability artifact is `BLOCKED`, including legacy runs inside the rolling window. It is never inferred usable from the green check alone.
- A failed/cancelled/timed-out run without an artifact is `INFRASTRUCTURE`.
- A producer job skipped by the shared calendar is `NO_OP` when the Actions job record proves that skip.
- Artifact identity must match run ID, workflow path and event.
- Multiple, malformed, expired, or mismatched artifacts cannot produce `USABLE`.
- The report uses exact workflow paths and scheduled events from `config/workflow-usability-monitor.json`; unrelated CI and manual runs are excluded.

## Producer evidence

- Current Refresh compares the exact target league list with successfully rebuilt league IDs, so a mixed run is `PARTIAL`.
- Weekly Actions and Optimal Waiver read their exact invocation output indexes and operational-readiness summaries.
- Waiver evidence reads the exact invocation audit; source failures are `PARTIAL`, while a complete exposed observation remains usable with private absence explicitly unknown.
- Availability reads its exact capture index; first-write duplicates are healthy `NO_OP` results.
- PR2 capture/evaluation use the schedule decision plus whether a due operation committed new lineage-bound evidence.
- The Sunday paired checkpoint reads its direct result (`CREATED`, `EXISTS`, `WINDOW_NOT_REACHED`, or `MISSED`).
- Other first-write capture/build workflows use the commit delta bound to the run's initial SHA. A committed missed-capture record is `MISSED`; no repository change is `NO_OP`.

## Rolling report

`Report FIE Workflow Usability` runs daily during the governed warmup/season/closeout window and is included in the shared January 12–April 25 blackout. It has read-only Actions access and writes only:

- `data/operations/workflow-usability/latest.json`
- `data/operations/workflow-usability/latest.md`

The report contains state totals, per-workflow totals, every scheduled run in the window, direct investigation links, and a separate expected-no-op table. It does not copy logs, provider payloads, credentials, or model data.

## Validation

The no-network integrity test covers every state, exact producer adapters, legacy/missing-artifact fallback, run identity, rolling aggregation, monitored workflow coverage, calendar registration and report-workflow permissions. The contract is part of the deterministic release gate and build manifest.
