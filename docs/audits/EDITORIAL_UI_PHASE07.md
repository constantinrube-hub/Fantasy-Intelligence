# Editorial Phase 7 — journeys, recovery and accessibility

Isolated display-only branch ui/editorial-p07-journeys, based on approved Phase 6
941e2514. No merge, production activation or workflow schedule changes.

Shared reader: nested evidence includes Back to previous details. The prior DOM,
scroll and trigger focus are restored; Close/Escape returns to the outside trigger.
League, roster, period, history and tab transitions clear context-bound disclosure.
Readers are not persisted into another league namespace.

Keyboard: Skip to workspace content does not mutate the route hash. Visible focus
styles are retained; active primary/subnavigation have aria-current. Explicit table
roles preserve row/column semantics when CSS turns tables into mobile cards.
Rejected history restoration receives a recoverable status message and cannot
label previous-league evidence with the requested league.

Narrow/zoom: shared action groups wrap; reader headers and long IDs remain usable;
320px layout gets a compact context row. Footer and research UI use editorial
contrast tokens. Reduced-motion preference disables decorative motion.

Evidence: real app DOM with explicitly fictional provider records exercises completed,
upcoming, failed/recovered results, A→B→A, waiver history and all five explicit format
profiles plus Auto detection. Superflex/IDP are independent roster structure, not new
format keys. Registered served archive document bindings are checked separately.
No live provider result, deadline, recommendation or activation is inferred.

Performance: compare cold application readiness and cold/warm Reports navigation
against Phase 6 under identical offline conditions. Measurements are descriptive
single-run hardware observations, not general speed guarantees. Basic Reports must
request one shared index and no bulk document/inventory files.

Browser coverage: 1440px, 390px, 320px, and 720 CSS px at 2x density representing
200% equivalent desktop layout (not native browser zoom). All prior regression
suites remain in the candidate CI workflow. Live league/capture transitions must
still be reviewed by the user on the deployed preview; offline tests do not claim
live completeness. Long optional matrices can scroll inside their own regions.

Canonical scoring, optimizer, identity, transactions, model/governance and research
owners are unchanged. Phase 8 Draft lifecycle remains a separate approval.
