# Combined Tranche 3A Final Sync + Tranche 3B Preflight

Baseline before combined upload: `a11a733dd169af3a8160e599478d41b3398bc068`

## Why these can be combined

The successful Tranche 3A determinism run proved that only the two canonical
build manifests remained unsynchronized. Those exact manifests are included in
this package.

The new Tranche 3B files are characterization/audit files only and are not
components of `research/build_app_manifest.py`, so adding them does not invalidate
the exact 3A manifest sync.

## Formal 3A closure condition

Before the workflow accepts any 3B characterization it reruns:

- six-format semantics;
- responsive correctness;
- production authority;
- one-owner replacement/scarcity/VOR target;
- all-22 Core/A3/D replacement parity;
- deterministic build test;
- canonical release build.

It then requires:

- `STATUS: DEPLOYABLE_SOURCE`
- no tracked/generated/runtime drift at all.

If either fails, Tranche 3A is not considered closed and the workflow stops.

## 3B baseline

Only after the 3A closure proof, the workflow reproduces C10-006:

1. distinct AbortSignal scopes requesting the same URL currently coalesce into
   one in-flight promise;
2. aborting one scope therefore aborts the other scope;
3. the existing delayed A→B league live-overlay abort protection remains good;
4. `ResearchReportService` still owns a primary raw `fetch()` path;
5. all other direct browser fetches remain explicitly classified transport or
   fallback paths.

## Frozen target contract

- FIEDataClient remains the canonical browser transport.
- Same URL + same abort/scope identity may coalesce.
- Same URL + different abort/scope identity must not coalesce.
- Aborting scope A must never reject scope B.
- Existing league live-overlay abort semantics are preserved.
- ResearchReportService routes primary JSON reads through `FIEDataClient.json`.
- ResearchReportService has no primary raw fetch.
- Existing specialist/current fallback paths are not changed in this preflight.

## No production behavior change

This package does not modify DataClient, ResearchReportService, current snapshot
loading, D/ST, kicker, weekly context, projections, ranks, ADP, or model
governance.

The workflow captures the exact current transport files only after both the
final 3A closure and the 3B known gaps are proven.
