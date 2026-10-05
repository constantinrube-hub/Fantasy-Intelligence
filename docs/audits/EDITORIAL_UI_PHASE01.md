# Editorial UI — approved Phase 0 / Phase 1 boundary

User approval: October 5, 2026. Candidate branch: `ui/editorial-p01-shell`.
Frozen comparison source: `1272eed30faf9548c128677a2e45e99bafed819a`.
This is a display-only candidate. User comparison and approval are required before
merging to main or releasing to production. Later tab overhauls are separate phases.

## Foundation

| Role | Color | Use |
|---|---|---|
| Page | `#F5F0DF` | Warm editorial workspace |
| Surface | `#FFFDF6` | Tables and readers |
| Expanded | `#EDE5CF` | Inline explanations |
| Ink / secondary | `#211B12` / `#675E50` | Operational text / supporting text |
| Divider | `#D8CFB8` | Quiet hierarchy |
| Link / ochre | `#805817` / `#946821` | Accessible small text / decorative accent |
| Weekly / usable | `#366148` | Accent and labelled positive state |
| Market / context | `#2F6276` | Accent and focus ring |
| Research | `#6B5481` | Evidence accent; no promotion implication |
| Warning / blocked | `#875A18` / `#993E35` | Labelled evidence state |

Georgia headings; system sans-serif for controls and data; tabular numerals;
14px desktop and 15px mobile operational text. A consistent surface palette applies
across sections. Section identity uses a thin accent rule rather than a whole-page
color change. Existing specialized surfaces will migrate in their approved phases;
this first shell does not assert that every legacy inline style has been replaced.

## Disclosure contract

Basic shows the key decision or completed result, actual player points where
available, units, period, scope and every material blocker. Expanded is one tinted,
labelled inline explanation per table. Advanced opens a shared native dialog with
source, scoring, capture identity, method, coverage and gate detail. Advanced is
available directly from Basic. Escape and Close dismiss the reader and return
focus. League and period changes clear incompatible open detail.

Missing values are `Unavailable`, not zero. A research result is not a ranking,
recommendation, promotion or transaction authorization. Each waiver gate is separate.
Projected best lineup needs immutable pregame forecasts; hindsight optimal lineup
needs complete outcomes and the exact legal roster. Never reconstruct a missing
historical forecast from the completed result.

The isolated review page at `app/ui/editorial-review.html` uses visibly fictional
fixtures to demonstrate completed-week and blocked-waiver disclosure. It is not
linked in production navigation and supplies no runtime data or recommendation.

## Shell and ownership

The existing application remains the sole renderer. The league selector and Load
saved action stay visible. Connection/settings and data coverage move into native
disclosures without removing their IDs, listeners or information. The original
status remains visible. All existing sections and subtabs remain reachable. Mobile
uses a section selector and the existing subnavigation.

Navigation serializes `view`, optional `league`, and weekly `season`, `week`,
`roster` into the URL fragment. Back/forward restore through the existing surface
activation and canonical league controller; no parallel loader is introduced.
Only valid views, numeric league IDs and existing select options are restored.
`FIEPortfolio.leave` exposes the existing portfolio exit operation for routing.
The canonical navigation owner exposes `FIE_WORKSPACE_SECTIONS` for view validation.
Portfolio background refreshes render only while Portfolio is active; they cannot
replace a deep-linked tab. The scoring-health warning stays visible outside setup,
and the existing portfolio setup shortcut opens its new connection disclosure.

There are no changes to scoring, model rankings, eligibility, research writers,
workflow schedules, forecast payloads, promotion, or execution. New evidence does
not become app-authorized merely because its producer workflow has completed.

## Acceptance and release

1. Preserve immutable baseline and current source/dist contracts.
2. Test disclosure semantics, visible blockers, zero/missing distinction and focus.
3. Browser-check candidate vs frozen baseline at desktop and mobile: navigation,
   saved selector, management/coverage reachability, direct Advanced, Escape,
   horizontal overflow and deep-link/back/forward behavior.
4. Perform one deterministic personal release build and the full existing gate.
5. Push the isolated candidate and open a draft PR. Provide the deployment preview
   if the existing hosting integration produces one; never assume a branch URL.
6. User compares before any merge or production release. Record unresolved issues
   rather than claiming unperformed browser or live-league checks.

## Following phases

Local desktop/mobile browser evidence and the standalone disclosure preview are in
[`../ui-review/phase01/README.md`](../ui-review/phase01/README.md). Provider requests
were blocked identically in both snapshots; live league evidence was not revalidated.

Phase 2: Weekly upcoming/live/completed, actual player points first, immutable
projection comparison and separately labelled hindsight optimal lineup.
Phase 3: Waivers with independent gates, league-specific evidence and reader links.
Phase 4: Draft pre-draft/in-draft/post-draft, each with its own essential views.
Phase 5: Roster, Trades, League and Players migrated to shared disclosure patterns.
Phase 6: League reports and overarching Research document library, provenance,
cross-links and coverage. Phase 7: cross-format, accessibility, performance and
final density review. Each phase receives its own candidate and approval gate.

Model allocation follows the scoped editorial clause in `CODEX_MODEL_ROUTING.md`;
the existing audit and research escalation policy remains intact.
