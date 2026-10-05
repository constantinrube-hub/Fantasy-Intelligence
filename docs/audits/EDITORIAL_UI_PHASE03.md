# Editorial Phase 3 — Waivers

Isolated candidate `ui/editorial-p03-waivers`, based on user-approved Phase 2
`0d8f6fecf3d955235d47b12b96534e0eb75b1680`. Main and production are unchanged.

## Presentation contract

Desktop uses compact tables; mobile uses labelled evidence cards retaining the
same semantic rows, Expand controls and Advanced reader. No viewport overflow.

Watchlist is a compact alphabetical list of current loaded free agents, with
search and progressive 25-row loading. No activated, scope-bound planner is
served, so supported benefit, legal recommended drop and bid remain unavailable.
Legacy browser FAAB heuristics are not surfaced as waiver-v2 recommendations.
A collapsed existing-browser comparison retains original optimizer add/drop and
weekly estimate context without recommended bids or CLAIM actions.
Expand explains ownership/status/missing support; Advanced shows independent
explicit forecast/ranking/recommendation/transaction fields without transferring
legacy M5 flags or implying research eligibility grants app authority.

Results displays selected-period acquisitions, observed bids including zero,
selected-roster claim outcomes and visibility. Multiple acquisitions remain plural.
Expand retains all exposed claims and actual failure metadata; generic failure
is not automatically outbid. Advanced preserves transaction IDs and source scope.

Market / Budget displays loaded cap, used budget and cap-minus-used arithmetic;
unknown inputs stay unavailable and zero remains zero. Transfers, reserved bids
and replenishments are unverified. Descriptive winner counts/medians/ranges are
not calibrated win probabilities or recommended bids. Samples are selected league,
season and week, with explicit private/omitted claim limitations.

Evidence / Documents separates selected league research captures/ledger coverage
from overarching methodology and operation documents. Reader text uses textContent,
source paths and SHA-256 bindings; no Markdown HTML execution. Scope changes close
disclosures and stale asynchronous loads cannot populate another league.

## Serving ownership

`tools/build_waiver_ui_evidence.py` creates deterministic reporting-only derivatives
from existing Window 1D reports and normalized history bid ledgers. It writes only
dist, preserves source bytes and blocked statuses, and never calculates new waiver
economics or modifies activation gates. Previous-league IDs and previous seasons
are excluded from current-league history derivatives. Public mode serves no league
waiver bundles. The four allowlisted shared documents remain available.

Waiver lenses participate in the existing URL hash/back/forward owner. Existing
season/week/roster controls retain their handlers. Archive reload rereads served
artifacts, not provider workflows; league reload owns live budget refresh.

## Validation and review

Targeted semantic tests cover scope, zero bids, failed versus explicit competitive
loss, multiple acquisitions, null budgets, independent gates and non-promotion.
Adapter tests cover determinism, exact source hashes, public exclusion and source
immutability. Populated browser QA uses explicit fictional fixtures in the real
application on desktop/mobile; it is not evidence of live league correctness.
The existing Weekly and frozen baseline comparison checks remain required.

No research schedules, models, rankings, waiver producer or transaction execution
are changed. User compares this candidate before any main merge or production release.
