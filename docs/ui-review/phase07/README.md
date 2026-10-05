# Phase 7 — journey review

Candidate: ui/editorial-p07-journeys. Parent: approved Phase 6 commit 941e2514.
Main, operational workflows and model/transaction ownership are unchanged.

## Three preview tasks

1. In a loaded league, open a prior Weekly result, Expand a player, open Advanced,
   then close with Escape. Change roster/week, visit Waivers Results and Evidence,
   and use browser Back/Forward. Confirm each table retains the expected scope and
   no reader from the prior context remains. Compare against Phase 6.
2. Reports → Open selected league research → QB (or another populated lens) →
   Advanced on a player. Use Back to previous details: the same lens, rows, scroll
   and trigger should return. Close/Escape should return to the outside opener.
   Shared document/source readers retain existing read-only behavior.
3. Use Tab/Enter, the Skip to workspace content link, and a narrow window. Try your
   actual browser's 200% zoom too. Check action wrapping, visible focus, table/card
   readability, and absence of full-page horizontal overflow. Long optional tables
   retain their own scroll regions. Test a different format and return to the first
   league; confirm IDP and Superflex remain roster dimensions.

## What changed

- Nested evidence readers have a reversible return path, with DOM/scroll/focus kept.
- Tab changes also clear disclosures when league/roster/period have not changed.
- Readers wrap keyboard focus among their visible controls.
- Skip link moves focus without corrupting the application's route hash.
- Active navigation is announced with aria-current; card tables keep explicit table
  roles and visually hidden, screen-reader-accessible column headings.
- History-load failures show a recoverable status; successful loads/navigation clear it.
- Narrow reader headers/actions/long labels wrap, and 320px gets compact context.
- Footer text uses the editorial contrast token; reduced motion is respected.

## Validation and limits

Deterministic personal release: DEPLOYABLE_SOURCE, 77/77 checks.
Journey suite: real application DOM, explicit fictional provider records, five explicit
format profiles plus Auto; independent Superflex and IDP fixture slots. Covers completed,
upcoming, failure/retry, namespace transitions, history, keyboard and nested evidence.
Registered served documents and captured league records are separately checked for
matching namespaces/source bindings. Capture namespaces include retained/history
leagues; they are not a live portfolio denominator or activation count.

Widths: 1440, 390, 320; 720 CSS pixels at 2x density emulate a 200% desktop layout.
This is not native browser zoom or a live-provider test. The three sampled normal-text
styles exceed 4.5:1; this does not claim a full-site WCAG certification. Existing regression
suites cover source-preserved earlier tabs and the frozen baseline shell.

Cold/warm timings in comparison.json use identical local/offline conditions for Phase 6
and Phase 7. These are single-run descriptive observations, not universal performance
claims. Basic Reports uses one shared index and defers full documents/inventories.

The UI still cannot produce unavailable historic forecasts, live workflow usability,
private waiver bids, calibrated probabilities or promotion authority. Phase 8 Draft
lifecycle is separate and has not been implemented in this branch.
