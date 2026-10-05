# Phase 4 review — Portfolio and League Home

Branch: `ui/editorial-p04-overviews`, based on approved Phase 3 `cdc7029c`.
This is an isolated UI review candidate. Production and main are unchanged.

## What to compare

- Portfolio: one searchable league table replaces repeated rank cards. Expand a league for cached tasks/results/freshness; Advanced exposes scope and the original cached snapshot.
- Retained leagues: archived, disabled and explicitly eliminated entries stay searchable and reportable. Runtime eligibility alone does not imply elimination.
- Exposure: collapsed initially. Counts reflect known managed-roster snapshots, with explicit missing coverage and denominators. Opponent selection must not change ownership.
- Home: the latest prior regular-week reported result is basic. Expand submitted-player actuals; open Weekly for deeper evidence. Change roster and use browser Back/Forward to check context.
- Reports: collapsed initially. Research restrictions and coverage remain visible when opened; league evidence links to the existing Waivers evidence view.
- Mobile: tables become labelled cards, with details closed initially and no horizontal page overflow.

## Review screenshots

The screenshots use explicit fictional fixtures inside the real application; they do not verify live league correctness.

| View | Desktop | Mobile |
| --- | --- | --- |
| Portfolio basic | [1440px](portfolio-1440.png) | [390px](portfolio-390.png) |
| Portfolio expanded | [1440px](portfolio-expanded-1440.png) | [390px](portfolio-expanded-390.png) |
| Portfolio advanced | [1440px](portfolio-advanced-1440.png) | [390px](portfolio-advanced-390.png) |
| Home basic | [1440px](home-1440.png) | [390px](home-390.png) |
| Home expanded | [1440px](home-expanded-1440.png) | [390px](home-expanded-390.png) |
| Missing result | [1440px](home-blocked-1440.png) | [390px](home-blocked-390.png) |
| Chopped scope | [1440px](home-chopped-1440.png) | [390px](home-chopped-390.png) |
| Known exposure | [1440px](exposure-known-1440.png) | [390px](exposure-known-390.png) |
| Missing exposure | [1440px](exposure-unknown-1440.png) | [390px](exposure-unknown-390.png) |

## Validation

Personal release build: 75/75 checks, DEPLOYABLE_SOURCE. Overview, Weekly and Waiver populated browser checks passed at 1440px and 390px. Frozen-shell comparison results are stored alongside these screenshots.

Checks cover zero/negative actuals, unknown ownership, lifecycle distinctions, stale async responses, roster navigation, report evidence links, disclosure defaults and native Advanced dialog keyboard/focus behavior.

## Limits

Exposure is cached ownership, not simultaneous or starter exposure. Chopped survival and lineup lock policy remain unverified without authoritative inputs. Historical projections and optimal lineups are not reconstructed. The full cross-league research/document library remains Phase 6 work. Draft lifecycle redesign remains a later phase.

Review the preview against Phase 3 before proceeding to Phase 5 (Roster, Players, Trades and League).
