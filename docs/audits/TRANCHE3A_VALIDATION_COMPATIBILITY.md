# Tranche 3A Validation Compatibility Patch

Implementation head: `62c99d394d2d4d8197426a40a6cb32947b243ea5`

## Failure classification

The first Tranche 3A implementation run failed before reaching the new 3A target tests.

The preservation step called the forward Tranche 2A test, which still froze exact DraftBase values from the original Tranche 2A fixture. C10-004 intentionally changes canonical replacement/scarcity economics, and DraftBase consumes structural scarcity. The absolute-value freeze therefore became an invalid cross-tranche invariant.

The separate `Validate FIE V9.3.4C-E` run failed because its smoke harness replaced `FIECore` with a Diagnostics-only stub. After C10-004, V9.3.4D correctly requires the canonical `FIECore.ReplacementService`.

Neither failure requires a runtime rollback.

## Forward Tranche 2A protection

The current six-format test still requires:

- exactly six format capabilities;
- unchanged Core lineup objectives;
- the exact DraftBase architecture for every format;
- finite DraftBase values and a stable player set;
- `CHOPPED_BESTBALL` raw DraftBase value as the exact 50/50 component-weight blend of CHOPPED and REDRAFT_BESTBALL;
- no hybrid collapse to Redraft, Chopped, or Best Ball;
- legacy shell capability parity;
- hybrid worker floor/ceiling serialization;
- D/ST format objectives;
- Monte Carlo worker objectives.

Only the obsolete absolute DraftBase fixture values are removed from forward validation.

## Historical Tranche 2A proof

The completed Tranche 2A workflow becomes manual-only and checks out the validated target:

`7533ce190a8732b4447d2e14c489153db05b8746`

That preserves the original absolute numeric proof and prevents later, separately governed correctness changes from producing misleading Tranche 2A red runs.

## V9.3.4C-E smoke

The smoke now loads the generated runtime contracts and real Core before C/D/E. It also verifies that D replacement provenance is `FIECore.ReplacementService`.

## Release protection

`research/release_gate.py` now runs the forward six-format semantic contract before the permanent Tranche 3A replacement tests.

## Runtime behavior

No Core, A3, D, projection, VOR, scarcity, ranking, ADP, or governance behavior is changed by this compatibility patch.
