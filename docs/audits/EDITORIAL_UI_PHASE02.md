# Editorial UI — Phase 2 candidate

User authorized Phase 2 on October 5, 2026 after comparing the hosted Phase 0/1 preview.
Branch: `ui/editorial-p02-weekly`, stacked on approved candidate `04ddfcd9051e2948afdbaf4ef568da60a60fc337`.
Main and production are unchanged. User comparison is required before any release.

## Display ownership and scope

Upcoming uses the existing `FIEUX93.weeklyDecisionState`, canonical exact assignment and existing projection resolver. No football method, rank, model, promotion, schedule or transaction authority changes.
Live/unknown/completed uses reported Sleeper matchup totals, ordered submitted starters and player actual points. Unknown timing does not produce a final outcome. Prior regular-season weeks are classified using observed Sleeper NFL state. NFL schedule kickoff conversion uses America/New_York, independent of browser timezone.

Basic: result band, submitted player/slot/actual points, explicit blockers. Upcoming: projected starters, source/estimate flags and roster coverage. Best Ball uses contribution language. Chopped shows observed rank and explicitly unverified survival; no invented head-to-head win or cutoff.
Expanded: scoring category coverage, separate frozen-forecast availability, usage, opponent/range/source and eligible bench slot comparisons. Bench, lineup review and other league records are collapsed.
Advanced: reported IDs/scope, canonical scoring inputs/weights, replay discrepancy, capture requirements and corrections. Native reader supports direct access and focus return.

D/ST and K follow selected-week timing. Historical specialist views show actuals, not recycled current forecasts. Upcoming boards retain the existing specialist action/rank/projection owners; ranges/replacement/next-three context are expanded. Original detailed specialist drawers and Weeks 1–18 remain reachable.

## Evidence limitations (intentional, visible)

- Browser-local legacy projection snapshots have no immutable profile/eligible-roster binding; they are not admitted as verified historical pregame evidence.
- M10 prospective research captures are offensive-only, separately governed and not promoted. They are not substituted for full-lineup historical totals.
- No served PR2 historical eligible-roster/rule/lock capture exists in this inspected baseline. Projected-best and hindsight legal-best scores are unavailable until that adapter is implemented with valid inputs. Current rosters are not historical candidate pools.
- Scoring categories read loaded nflverse selected-week stats through canonical identity and a read-only method attached to `FIE89`. Missing raw/unsupported rules stay unavailable. Partial replay cannot replace reported totals.
- Provider actuals may be corrected. `custom_points` and player-total discrepancies are visible; values are not silently reconciled.
- Upcoming player locks are unverified. Started weeks show reported submissions instead of proposing unlocked reoptimization. Current-week game completion and remaining forecast need a reliable live schedule/status source; absent states remain explicit.

This is a releasable Phase 2A/B display candidate with conditional 2C detail, not a claim that missing 2C/D evidence exists. Evidence-backed historical alternatives remain a later incremental slice within Phase 2.

## Workflow reconciliation

Inspected `main` at `5dbf213212d27f0600fb45fd758b5072f25e094a`: only the workflow-usability latest JSON/Markdown differ from frozen source `1272eed3`. Weekly code and captures do not differ. Reported Actions success does not confer evidence usability or runtime promotion. The report lists PR2 capture runs as NO_OP and no usable M10 run in its rolling window, reinforcing unavailable capture states. No workflow schedule or research payload is changed here.

## Validation

Run `node research/integrity_editorial_weekly_test.js` for period, Eastern DST conversion, zero/negative/missing points and non-head-to-head pairing.
Run `node research/editorial_weekly_browser_qa.js dist` with Playwright for populated fictional fixtures in the real app: desktop/mobile actuals, disclosure, historical alternatives blocked, upcoming/current, provider error, navigation cleanup, Best Ball and specialist results.
Run `python tools/release_build.py --mode personal` once at closure for source/dist and full preservation gate. Browser tests are explicitly fixtures, not live provider validation.

## Completed local checks

Populated full-app browser fixtures pass at 1440×1000 and 390×844: actual zero/negative points, visible partial scoring, one inline expansion, direct Advanced and Escape focus, missing historical alternatives, upcoming period binding, current-week unknown timing, provider HTTP 503, navigation cleanup, Best Ball, Chopped, and historical D/ST/K. The basic submitted player row and its actual value enter the first viewport; detailed captions and explanations remain accessible. Forecast source tools sit inside global coverage for past weeks, preserving original IDs and actions. Fixture screenshots are in `docs/ui-review/phase02`. These are not live-league source validation.
