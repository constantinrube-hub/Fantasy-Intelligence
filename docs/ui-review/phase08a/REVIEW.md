# Phase 8A comparison guide

Candidate branch: `ui/editorial-p08a-predraft`, based on approved Phase 7.

## What to review

1. Open Draft → Draft Assistant in a league with an upcoming draft. Expect Preparation Assistant and five Top Picks, with compact rank/player/tier/base index/market columns. The selected provider slot is shown only when verified.
2. Expand a candidate. Inspect the conditional target, fallback, league value lens, projections, coverage and health. Further details requests the existing roster marginal and timing inputs on demand, with utility units and conditional assumptions. Advanced opens captured records directly; Escape returns focus. Player details opens the shared layered player reader.
3. Open Draft Board. Search or filter by position; use Show more to grow the reference list. It retains full-pool canonical ranks even when filtered. Compare these ranks/values against Phase 7.
4. Open roster construction. Inspect actual provider slots, asset counts and the overlapping FLEX / Superflex / IDP explanation. Advanced opens the current legal roster assignment; it is not a simulated final draft roster.
5. Open Value Finder. Change observed market range, position and sort. Expand Discovery filters for role path, experience and evidence categories. Expand rows for heuristic target ranges and source limitations. Missing ADP remains on the board and is excluded by the existing market-discovery owner.
6. Open Advanced → Existing pick optimizer and scenarios. Original controls, rankings and estimates remain available. An attached pre-draft pick sequence can be called Live pick context by this retained owner; the Advanced banner explains the distinction. Without an attached sequence, edit planning/following/third picks. Use Back to Basic preparation.
7. Change league, season, draft or roster. Preparation must not retain a foreign draft slot or value advice. Loading, missing or failed state stays conditional; mismatched records block advice. Live and completed drafts retain the existing views until 8B/8C.
8. Test a narrow phone width and keyboard-only operation. Tables become labeled cards; Expanded stays local and Advanced uses a native dialog.

## Automated evidence

`comparison.json` records populated fictional browser runs at 1440, 390, 320 and 720 CSS pixels. 720px checks layout equivalent to a 1440px viewport at 200% zoom, not browser zoom itself. PNGs capture Basic, Expanded, Advanced, construction, reference board, values and unknown-context states. They are deliberately fictional; they do not prove live provider freshness or projections.

All eight browser suites passed: pre-draft preparation, frozen baseline comparison, Weekly, Waivers, Portfolio/Home, Context, Reports and Journeys. The release report is recorded alongside these results after final source/dist synchronization. Main and production are unchanged. Approve this preview before starting Phase 8B.
