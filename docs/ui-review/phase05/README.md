# Phase 5 review — Roster, Players, Trades and League

Branch: `ui/editorial-p05-context`; based on approved Phase 4 `1a93c3ee`.
Main and production are unchanged. Compare this preview with Phase 4 before Phase 6.

## What changed

| Part | Basic | Expand / optional sections | Advanced |
| --- | --- | --- | --- |
| Roster assets | Player, provider role, selected projection/VOR/asset measure, health/eligibility | Source, weekly/season context, replacement, role; unmatched provider IDs | Raw record, canonical rank and scope |
| Players / Targets | Search and compact player table; selected measure | Extra filters/export; source, role and market comparison; acquisition context | Bound player record and authority |
| Shared player reader | Identity, ownership, health, current season projection | Projections/replacement, role/usage/contract, scoring/results, cached cross-league ownership | Exact record, rules and provenance |
| Team | Position counts, existing VOR sums, input coverage | Contributors, named roster measures/weights, selected-roster comparison | Canonical owner records and limitations |
| Trade builder | Two teams, offered asset chips, player/pick selectors | Selected asset facts | Existing pick and valuation assumptions |
| Trade effects | Both teams' before/after utility, change and configured-rule state | Starter/depth measures, asset index effects, received/sent assets | Formula, original output, scope and missing inputs |
| League | Provider record and reported season points | Manager activity, transaction chronology, trade partners and lifecycle | Raw provider/history records and inclusion limits |
| Rules | Format fingerprint, slot table, material unsupported scoring flags | Scoring with bounded numerical examples; settings/timing; all existing override controls | Raw rule keys, slot contracts, audit and fingerprints |

Points, VOR and asset indexes have separate labels. Best Ball roles remain
heuristic and automatic; Chopped survival is not inferred. Ineligible roster
assets stay visible, while unresolved player IDs remain explicitly unvalued.

## Suggested comparison

1. Open Team → Roster Assets. Change roster and use browser Back. Search, switch measure, Expand a player and open Player details or Advanced.
2. Open Team → Power & Structure. Inspect the compact position table, then expand weighting and compare a second roster.
3. Open Players, including Offense/IDP where supported. Check filters, sort, pagination and export access. Inspect a free agent, an owned player and missing projection data.
4. Open Market → Trade Center. Add/remove players and future picks. Change teams; verify that visible effects clear until evaluated again. Check both sides and keep utility distinct from point forecasts.
5. Open League → Rules & Format. Expand scoring examples and overrides. Existing Apply/Reset controls remain under the override disclosure.
6. Open League → League Intel. Review reported totals, manager samples and retained transaction evidence. Missing cutoffs/private claims remain unknown.
7. Compare mobile sizing and keyboard Escape/focus in the shared reader.

## Screenshots

These are explicit fictional fixtures in the real app, not live-league validation.

| View | Desktop | Mobile |
| --- | --- | --- |
| Roster | [1440px](roster-1440.png) | [390px](roster-390.png) |
| Roster expanded | [1440px](roster-expanded-1440.png) | [390px](roster-expanded-390.png) |
| Player reader | [1440px](player-reader-1440.png) | [390px](player-reader-390.png) |
| Player explorer | [1440px](players-1440.png) | [390px](players-390.png) |
| Team | [1440px](team-1440.png) | [390px](team-390.png) |
| Team comparison | [1440px](team-comparison-1440.png) | [390px](team-comparison-390.png) |
| Trade | [1440px](trade-1440.png) | [390px](trade-390.png) |
| Rules | [1440px](rules-1440.png) | [390px](rules-390.png) |
| Scoring | [1440px](scoring-1440.png) | [390px](scoring-390.png) |
| League | [1440px](league-1440.png) | [390px](league-390.png) |
| Managers | [1440px](managers-1440.png) | [390px](managers-390.png) |
| Best Ball | [1440px](bestball-1440.png) | [390px](bestball-390.png) |
| Chopped | [1440px](chopped-1440.png) | [390px](chopped-390.png) |
| Missing league | [1440px](missing-1440.png) | [390px](missing-390.png) |

## Validation and limits

Personal release: **76/76 checks, DEPLOYABLE_SOURCE**. Populated Phase 5 browser
fixtures passed at 1440px and 390px without uncaught errors or page overflow.
Portfolio/Home, Weekly and Waivers regressions passed; frozen-shell comparison
passed at desktop and mobile sizes. JSON reports are saved beside this guide.

This phase reuses current owners. It does not create missing game logs, replay
components or frozen projections. Player scoring/history sections link the
existing result owner or identify missing bindings. Roster utility can include
legacy score fallbacks; pick ownership/slot priors are not guaranteed complete.
History shows up to 80 chronological rows plus the full loaded records in an
Advanced disclosure. Cached ownership is not simultaneous starter exposure.

Phase 6 owns the complete Reports/Research library; Phase 7 owns cross-surface
integration polishing; Phase 8 owns the Draft lifecycle redesign.
