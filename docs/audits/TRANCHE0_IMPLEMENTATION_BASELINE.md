# Controlled Implementation — Tranche 0 Baseline

**Status:** IMPLEMENTATION BASELINE HARNESS  
**Production semantics changed:** NO  
**Cleanup performed:** NO  
**Statistical thresholds changed:** NO

## Frozen implementation starting point

- Repository: `constantinrube-hub/Fantasy-Intelligence`
- Implementation branch: `audit-implementation-2026-09`
- Baseline commit: `8bcf13224c665be5a08f40b3aae2921ead5bfb1f`
- Baseline tree: `f35438636c0ca443d4757c0183b1def08de4a090`
- Audited source parent: `b7027905e9a2e25010fd5eb73ed3bdec54d41e82`
- Audited source tree: `e0209cf0bc91083c5822c78c916a6b450841dc6b`

The baseline commit is the September 1 availability-evidence child of the audited source
commit. Its repository change is prospective availability evidence only; the frontend/runtime
source tree audited in Phases 0–10 remains unchanged.

## Purpose

Tranche 0 does not fix any audit finding yet.

It establishes the reproducible comparison point that all Tranche 1+ changes must beat.

The baseline harness:

1. proves the implementation branch descends from the frozen commit;
2. rejects production/source changes other than the Tranche 0 harness files;
3. inventories all enabled leagues by all six supported formats;
4. fingerprints one representative league profile per format;
5. runs the canonical deterministic release build;
6. runs critical baseline checks that are outside the direct release gate;
7. requires `STATUS: DEPLOYABLE_SOURCE`;
8. requires committed `dist/` to remain synchronized;
9. uploads JSON + Markdown baseline artifacts.

## Representative format fixtures

| Format | League |
|---|---|
| REDRAFT | `1391803939736801280` |
| DYNASTY | `1316165875291668480` |
| CHOPPED | `1313696967989157888` |
| REDRAFT_BESTBALL | `1314007486205804544` |
| DYNASTY_BESTBALL | `1332838151168724992` |
| CHOPPED_BESTBALL | `1399318410818519040` |

The hybrid fixture is intentionally the real enabled league identified in the audit.

## Tranche 0 pass condition

The workflow must be green and its artifact must report:

- `release_gate_status = DEPLOYABLE_SOURCE`
- `dist_synced_after_release_build = true`
- `unexpected_changes_vs_baseline = []`
- `pass = true`

A green Tranche 0 does **not** mean the known hybrid/runtime issues are fixed. It means
we have frozen the existing behavior safely enough to begin Tranche 1 characterization tests.
