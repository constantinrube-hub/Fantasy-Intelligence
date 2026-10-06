# Editorial UI Phase 8B — captured live-draft workspace

Parent: approved 8A `87e8b1a74729909a79d537956c97e3cb36742f54`.
Branch: `ui/editorial-p08b-live`. Separate user comparison before merge or release.

## Scope and owners

Display-only live Draft Board, Draft Assistant and Value Finder. The full eligible-pool canonical rank/index remains `FIEDraftBaseValueService`; current roster and timing priority remains `FIEDecisionService`. Eligibility, snake/third-round reversal, acquired roster and legal assignment reuse their existing owners. No football model, score formula, market-edge formula, workflow schedule, promotion, transaction, or provider endpoint is introduced. M9 remains champion; no M10/6F activation. The editorial comparison workflow adds fixture checks only.

## Basic → Expanded → Advanced

| Surface | Basic | Expanded | Advanced |
| --- | --- | --- | --- |
| Live context | Scope, reported next pick, selected slot, next own pick, ticking snapshot age and blocking reason | Context remains visible while individual rows expand | Provider draft/picks/trades, existing sequence, display-health inputs and freshness/ownership limitations |
| Assistant | Three available candidates: canonical league rank, current decision rank, base index and estimated advice state | Existing why, roster/starter marginal, waiting trade-off, owner label, coverage and season projection | Captured canonical/decision/player records, units and authority |
| Available board | Player, canonical rank/index, decision rank and advice state; shared filters, 40-row progressive pagination | Same candidate explanation | Same direct native evidence reader and separate Player details |
| Available values | Player, observed ADP, existing comparable rank edge, estimated following-own-pick window and advice state | Roster consequence, market/timing limitations and existing why | Same records; original optimizer/scenarios remain an explicit Advanced workspace with Basic return |
| Your acquired roster | Assistant shows first six assets: player, position, acquisition pick and identity coverage; raw slot requirements below | Complete roster, eligibility and projection per row; slot consequences on demand | Existing legal optimizer result, missing projections and unresolved picks disclosed; no final-roster forecast |
| Draft log | Collapsed entry point avoids flooding the primary decision view | Observed ordered picks, player and roster/slot; round, picker and coverage per row | Raw provider pick and ledger integrity |

Gold Draft accent and shared editorial level labels, row disclosure, native modal, Escape/focus restoration and mobile cards are retained. Completed drafts remain on the original view pending 8C; pre-draft preparation remains 8A. Original scenario tools preserve their calculations and are admitted only with fresh usable live context; expiry returns to Basic and removes their timing labels.

## Freshness and fail-closed behavior

Existing provider URLs are read through the central DataClient with `cache: no-store`. A browser completion receipt binds league, season, selected draft and the exact draft/picks/trades payload. Cached historical completion times are never stamped as fresh. A 30-second local display budget expires advisory fields and closes opened evidence, including the retained original scenario workspace. The clock timer updates UI only; it makes no provider requests. This is deliberately not a claim of provider event-time accuracy, real-time latency or calibrated survival.

Unknown receipt, modified payload, stale age, pause, unknown slot, invalid or duplicated pick/player IDs, missing observed slot/roster ownership, ledger gaps, provider-slot/roster-sequence conflict, exhausted sequence and lifecycle conflict withhold pick advice. Bound snapshots may retain clearly labelled roster-neutral reference candidates; mismatched league/season/draft, loading or error show no live candidate or roster tables. Picked IDs and independently flagged drafted candidates are excluded even if returned by a decision owner. Missing ADP never fabricates a waiting estimate or edge; zero numeric values remain zero.

Existing timing owners do not reconcile current-season traded picks. Missing traded-pick coverage or any current-season/unknown-season trade therefore withholds pick timing rather than inventing transferred ownership. Future-season-only trades do not block the current sequence. Full provider records remain in Advanced context. This known limitation is displayed, not silently solved by new architecture.

## Scoped refresh correction

The old loader wrote into whichever global league happened to be selected when an awaited response finished. 8B retains the request's draftIntel object, league, season and requested draft ID, stages the payload and publishes atomically only into that matching scope. Old responses cannot replace a newer league's picks or clear its loading flag. A user-selected draft change during the request discards the old result and queues the already-requested new selection once. This is a known-target race correction, not a new polling workflow. The existing draft-update event/horizon wrapper is preserved.

## Verification and comparison

Two targeted Node contracts cover uncached receipt binding, expiry, ledger integrity, scope/slot/lifecycle/ownership gates, late league-switch responses and selected-draft races. Real-app browser QA uses explicitly fictional provider responses at 1440, 390, 320 and 720 CSS pixels. It checks candidate and roster composition, canonical rank/index and existing decision-rank parity, picked/ineligible exclusion, zeros/missing ADP, filters/pagination, roster switching, existing legal optimizer and scenarios, observed log, uncaught errors, readers/Escape/focus, expiry, conflicts and all six formats. Fixtures are not live league validation. Prior eight editorial browser suites remain regression gates; deterministic personal release and source/dist parity remain required.

User comparison boundary: import/push this branch only, let candidate CI/preview complete, compare against approved 8A, then approve 8C or request refinements. No merge into main is authorized here.
