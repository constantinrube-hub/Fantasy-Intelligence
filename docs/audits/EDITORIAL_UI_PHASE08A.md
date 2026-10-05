# Editorial UI Phase 8A — pre-draft preparation

Parent: approved Phase 7 `3923a5c361ed9b9cc65d930e4929aff8cafe2db0`.
Branch: `ui/editorial-p08a-predraft`. User comparison precedes merge/production.

## Ownership

Display-only preparation consumes `FIEDraftBaseValueService`, the current league eligibility owner, `FIE_VALUE_FINDER` and the existing legal lineup optimizer. No new ranking, statistical methodology, timing probability, calibration, model, workflow schedule or transaction execution. M9 remains champion; no M10/6F activation.

## Composition

- Preparation Assistant: five conditional opening targets; canonical rank, player, tier, base index and observed ADP. Expand shows condition, fallback, coverage and football inputs, with an on-demand reader for the existing roster marginal / timing decision row; Advanced opens raw canonical/player records and assumptions directly in the native reader.
- Draft Board: same five-column reference, filters and progressive 40-row pagination. Rank/value remain the canonical full eligible-pool order and values, independent of market price.
- Value Finder: observed ADP, positional rank edge, role path and evidence category. Separate expandable discovery filters. Expanded distinguishes heuristic windows, discovery strength and evidence limitations. Advanced includes policy coverage, evidence and captured owner records. The full original pick optimizer/scenario controls remain available behind an explicit Advanced tools action and a Basic return action.
- Roster construction: collapsed by default; provider slot counts, loaded assets and overlapping-slot explanation. Advanced invokes the existing legal assignment owner, with missing projection handling explicitly disclosed.
- Context/assumptions: provider status, league/season/format, provider slot, sync state and loaded projection readiness. No invented slot or timing advice.

## Lifecycle / scope

`draftIntel.loaded` describes sync, not lifecycle. A trusted record must match league ID, season and selected draft ID. `pre_draft` with no picks opens preparation; `drafting`/`paused` or any picks use the original live surface; `complete` uses the existing surface until separately approved 8C. Missing, loading, failed or unknown context shows roster-neutral conditional preparation without slot-specific advice. A mismatched record blocks preparation candidate/value advice until refreshed. Draft Board remains a league-bound reference, never a current-pick decision surface.

Provider roster picker and refresh/select controls retain their nodes and handlers. Leaving Draft removes the reference host before another context surface renders. Candidate/player readers reuse native dialog, Escape/focus return and nested details. Gold is the Draft accent; level labels and actions retain shared editorial grammar.

## Verification

Targeted display-contract test covers lifecycle/league/season/selected-draft mismatch, sync failures, provider slots, missing vs zero and units. Real-app browser fixtures cover canonical rank/value parity, pagination/search, eligibility, conditional labels, source readers, Escape/focus, roster selection, construction, original scenario input preservation, context changes and return, and five formats at desktop/mobile/320px/720px (equivalent CSS width to 1440px at 200% zoom). Fixtures are fictional, not live provider evidence. Original baseline, Weekly, Waivers, Overviews, Context, Reports and Journey suites remain required. Deterministic personal release, DEPLOYABLE_SOURCE and source/dist parity are the closure gates.

## Review boundary

8A does not redesign live decisions or completed draft review. Those are 8B/8C, following the user's approval of this candidate. Full optimizer/scenario presentation is preserved as an Advanced tool; it remains the existing detailed layout pending a later dedicated refinement. Missing ADP is visible on the reference board; the existing Value Finder owner excludes missing ADP from market-band discovery and does not fabricate an edge.

The retained optimizer may call an attached pre-draft provider sequence "Live pick context"; the Advanced banner explicitly explains this inherited owner label. Editable planning inputs remain available when no draft sequence is attached. No lifecycle or timing algorithm is silently replaced.
