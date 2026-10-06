# Editorial UI Phase 8C — observed post-draft review

Parent: approved 8B `f772556d14a826d71cd2a43f566f633bf5b90ebb`.
Branch: `ui/editorial-p08c-review`. User comparison precedes merge or production.

## Evidence boundary

Observed Sleeper completed-draft picks and metadata support actual selection order, selected roster, recorded position/name and auction amounts when supplied. The app's compact cross-league archive supplies selection samples and broad season ADP/peer diagnostics; it omits some raw fields and does not authenticate ADP, rankings, legal pools, forecast versions or roster/rule inputs at each historical pick. No pick-time capture owner is available in the inspected app.

8C does not reconstruct such evidence from current ranks or forecasts, invent a grade, retrospectively optimize a draft, or infer the complete final roster by joining post-draft acquisitions. Missing keeps/pre-existing assets, pick-time rules, eligibility, uncertainty and original draft plan remain explicit. This is a presentation boundary, not new statistical methodology. Existing models, scoring, canonical rank, optimizer, archive calculations, schedules, promotion and transaction authority remain unchanged; M9 remains champion and no M10/6F integration is introduced.

## Basic → Expanded → Advanced

| Surface | Basic | Expanded | Advanced |
| --- | --- | --- | --- |
| Review | Draft/roster selectors, provider completion state and last-picked timestamp if supplied; observed own-pick count, ledger integrity and pick-time evidence availability | Allocation, complete observed league draft, current repair workspace and cross-league archive are separate collapsed sections | Direct pick records, structural coverage assumptions and archive input records |
| Your actual picks | Pick number, recorded player/position, round or supplied auction cost, identity source; progressive pagination | Observed roster/slot, identity provenance, subsequent observed selections and clearly labelled current player reference | Raw pick and draft records; current player record in its separate horizon; withheld historical grade/counterfactual and capture limits |
| Drafted allocation | Collapsed to keep actual selections first | Position counts and observed assets; named positional coverage against current slot requirements | Existing canonical optimizer assignment, one per occupied slot solely for coverage; unresolved positions and keeper/experience/rule limitations |
| Full league draft | Collapsed entry point | Ordered raw observations from all rosters, with the same row layers | Same provider records; never a new alternative ranking |
| Current repair | Collapsed entry point | Links to the current Roster, Team and Waiver owners | Their existing detail readers and source evidence |
| Imported archive | Collapsed entry point | Imported draft inventory with league/draft/root/season/profile bindings and source warnings | Full compact records; original cross-league player/manager diagnostics remain a reversible Advanced workspace with pick-time validity warning |
| Current Values | Completed-draft discovery shows current canonical rank/index and observed current ADP only | Current ownership and forecast, explicitly separate from draft-time evidence | Current canonical record/authority; no timing or TAKE NOW surface |

Gold Draft accent, cream tables, shared row disclosure, mobile cards, native modal, Escape and focus restoration remain consistent. A completed provider status changes the Draft subnavigation to Analysis / Review, Your Picks, Draft Results and Current Values. Review opens the selected roster's actual picks with context; Your Picks provides a dedicated own-pick route; Draft Results opens observations across all rosters and includes a roster column. Current Values remains a distinct current-horizon reference. Primary tables start with 20 rows and add at most 20 more per action. Existing route IDs remain bookmark compatible. Pre-draft and live views retain 8A/8B behavior. Analysis / Review can also explain absent/incomplete draft evidence and expose imported history independently of lifecycle.

## Semantics and limits

- Provider pick name/position metadata takes precedence over today's identity record. Missing identity remains explicit; a current fallback is labelled as such.
- Auction amount zero remains zero. Missing/invalid amount is unavailable and is not replaced by a current ADP. Snake/linear selection shows observed round rather than fictitious price.
- Subsequent observed selections show sequence context. They are not an authenticated full available/legal pool, a grade or proof of a superior alternative.
- Allocation counts observed drafted assets only. A current roster asset not present in the ledger is excluded. The structural optimizer uses one per legal occupied starter slot, not player projections or a new football value formula. Current slot requirements and historical experience/keeper limits are disclosed; no draft-time compliance verdict is inferred.
- Last-picked time is labelled as a provider field, not an invented exact completion date. No date is inferred when it is absent.
- Invalid/duplicate pick numbers or IDs, gaps and unresolved ownership retain observable raw selections with a warning and withhold structural interpretation. Wrong league/season/selected draft, sync loading/errors, incomplete lifecycle or unknown roster withhold the selected review.
- Broad season/peer diagnostics are retained without promoting them to authenticated pick-time evidence. Their existing calculations are unchanged and visibly labelled as original diagnostics.
- Direct Value Finder callbacks also respect the completed lifecycle, preventing an old detailed timing surface from reappearing after the review route has handled it.

## Validation

Targeted contract covers completed lifecycle/scope/loading/error/roster binding, metadata precedence, zero/missing auction price, gaps/duplicate identities/unresolved ownership, current-record separation, and post-draft navigation. Fictional real-app browser fixtures at 1440/390/320/720 CSS pixels check own-pick parity, pagination, unresolved IDs, auction zero, current-acquisition exclusion, native readers/Escape/focus, roster switching, construction, reversible legacy diagnostics, current repair and value routes, conflicts, all six formats, and returns to 8A/8B. Prior nine editorial browser suites and deterministic personal release/source-dist parity remain closure gates. Fixtures do not validate a real league or certify historical model accuracy.

## Review / next boundary

Compare against 8B before merging any phase. This phase completes the three lifecycle presentations; further evidence capture or historical grading needs a separate approved owner/design. Today's projections cannot fill the missing authentic draft-time comparison cells. No other release phase or merge is implicitly authorized.
