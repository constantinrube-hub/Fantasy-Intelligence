# Post-merge verification and source closure — 2026-10-11

Base main: `20fd723c76168becc204df700f4ebd4ed1840993`.

PR74 is merged; P1, P2, P3 and the independent waiver repair are present.
The merged main release workflow 38169615249 passed. All 23 enabled/current-refresh
leagues pass the current input guard. All four feature-lab raw source hashes
and sizes replay exactly after restoring the omitted identity archive.

## Findings

- The Week 5 Window 1C/1D reports were generated on October 9 and are rejected
  by the 36-hour report guard. Sunday's automatic chain reports NO_DUE with
  PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY; green runs are not new published products.
- At inspection, all 23 portfolio core snapshots exceed the separate six-hour
  live surface limit. A manual current refresh and chained producers are needed
  to verify current report coverage. No timestamps or freshness limits changed.
- Week 5 postgame products remain NOT_DUE. M10 week-open and PR2 week-open
  captures replay. The Sunday paired checkpoint has a missed record; the PR2
  Sunday deadline is missed without a terminal record at the audit observation.
  Postgame data cannot repair missing pregame captures.
- Visual browser smoke remains unverified: Chromium installation failed and
  the cloud preview service timed out. Runtime/source-dist checks passed.

## Corrections

The earlier delivered P2 revision omitted the already prepared exact PFR→GSIS
snap adapter. This change restores its source, adversarial test, design,
immutable identity source and CI/release registration. The real captured table
binds 5,955/5,970 prior-week rows; 11 unmatched PFR and 4 missing GSIS rows
remain typed blockers. Percentage units and routes remain unavailable.

The fumble reconciler previously selected exactly one lost fumble per
multi-fumbler play. A binary play-level loss flag can represent multiple lost
fumbles. It now enumerates nonempty subsets, accepts only one globally unique
player-week aggregate solution and preserves missing/ambiguous blockers.
The added regression proves two losses on one play while existing tests retain
zero/multiple-solution, null aggregate and duplicate protections.

## Historical evidence

The full 2019–2025 reconstruction used downloaded source snapshots with recorded
hashes; it is historical research, not prospective evidence. The initial replay
resolved 30 of 37 multi-fumbler plays. The corrected replay resolves 35 of 37;
two remain blocked (2019 Week 17; 2020 Week 3). Overall event blockers decrease
from 30 to 25: E2=2, E3=6, E4=15, E5=2. Receiving-yard reconciliation retains
16 mismatches. Individual field-goal return roles remain unavailable.

The dense historical runner produced 90,858 diagnostic roster rows for one
supplied league profile. Final player-stat completeness was not asserted, no
eligible training rows are certified, and no model gates changed. The current
legacy catalog still has 92 offensive scoring failures and 78 format/position
failures across 23 leagues. Legacy catalog eligibility is separate from v2.

## Validation and next action

All 90 deterministic release checks pass (DEPLOYABLE_SOURCE). Focused snap,
feature-lab, event-ledger, historical-runner and profile-batch tests pass.
Generated manifests/dist are synchronized. Windows execution and GitHub CI for
this follow-up commit remain delivery checks.

Merge this one source correction after CI. Run current refresh with governance
KEEP and let the 1C→1D chain finish; inspect invocation receipts and product
coverage. Do not force a pregame recapture for an already closed deadline.
Historical unresolved source semantics must be addressed before exact labels,
model evaluation, calibration or governed promotion. M9 remains champion.
