# Phase 3 review — Waivers

Candidate: `ui/editorial-p03-waivers`, based on approved Phase 2 `0d8f6fec`.
Compare the candidate with Phase 2 before merging. Main/production remain unchanged.

## What to compare

| View | Basic | Expand | Advanced |
|---|---|---|---|
| Watchlist | Current free agents, alphabetically; blocked recommendations remain visible; search / 25 more | Ownership, provider status, role/depth fields if supplied, missing benefit and bid support | Independent source gates, player ID, capture status and bindings; no legacy eligibility transfer |
| Existing browser comparisons (collapsed) | Original optimizer comparisons only after opening; 25 at a time | Weekly lineup estimate and role score; explicit horizon uncertainty | Original calculation owner, current-state scope, search limit; no bid/CLAIM authority |
| Results | Player, acquiring roster/observed bid, selected-roster outcome and visibility | All exposed claims and actual reported failure metadata | Transaction IDs, source scope, captured time, hashes and unknown revisions |
| Market / Budget | Loaded manager cap/used/cap-minus-used; selected-period winner samples | Initial-cap proportion, cohort and observed range | Unknown adjustments/private bids, source freshness and sample limitations |
| Evidence / Documents | League-specific capture and ledger status; separate shared document list | Capture scope, health, selected vs archived managed roster | Exact report/source bindings and safe full-text methodology documents |

Desktop uses compact tables. Mobile presents each row as a labelled card with
Expand and Advanced together. Cream background, ink text, blue active market lens,
purple research/watchlist label and red blocker follow the approved editorial shell.

## Review checklist

1. Open Market → Waivers in a loaded league. Change week and roster using the
   existing controls. Watchlist ownership is current, even when reviewing an old week.
2. Review Week 3 Results and compare observed claims to Sleeper. A missing/private
   claim remains unknown; a generic failure must not become “outbid”. Zero is a bid.
3. Expand an acquisition with several exposed claims. Verify every supplied claim
   remains accessible. Multiple acquisitions should remain plural.
4. Check budgets. Missing used-budget fields should be unavailable; cap 0 must not
   become 100. Cap less used is descriptive, not a guaranteed spendable balance.
5. Open Evidence / Documents. League capture blockers and shared methodology must
   be separate. Archived blocked research remains blocked after UI changes.
6. Open and close Advanced with Escape; focus should return to the invoking button.
   Change league/period and use browser Back/Forward; prior evidence must not leak.
7. Compare desktop and mobile. Details start closed and mobile has no viewport
   horizontal overflow. Existing Weekly and other tabs remain accessible.

## Screenshots and validation

`watchlist-*.png`, `expanded-*.png`, `advanced-*.png`, `results-*.png`,
`market-*.png`, `documents-*.png`, `missing-period-*.png`, `unavailable-*.png`
use explicit fictional archived/provider fixtures inside the real application.
They show layout and semantics, not live league correctness. `legacy-comparison-*.png` verifies the collapsed legacy comparison surface.
`comparison.json`
records desktop/mobile geometry and pass status.

## Evidence boundaries

No new waiver economics is calculated. Existing producer reports and normalized
bid ledgers are served as deterministic reporting-only derivatives. Public mode
excludes league waiver derivatives. Archived profile drift, current-week mismatch,
stale sources and absent activation cannot be solved by visual changes.

The live main branch was checked at `5dbf213212d27f0600fb45fd758b5072f25e094a`:
only workflow-usability latest reports differ from the frozen implementation base.
No newer waiver producer/capture/UI implementation needs rebasing into this phase.
The candidate does not silently import a newer operations report or imply live
workflow health from an archived methodology document.

Validated closure: **74/74 release checks passed**, `DEPLOYABLE_SOURCE`.
Populated Waiver and Weekly fixtures and frozen shell comparison all passed.
First Basic watchlist row starts at 876 px on desktop (1000 px viewport) and
770 px on mobile (844 px viewport), with no viewport horizontal overflow.
