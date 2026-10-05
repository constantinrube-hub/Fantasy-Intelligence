# Editorial Phase 5 — Roster, Players, Trades and League

Isolated `ui/editorial-p05-context`, parent approved Phase 4 `1a93c3ee`.
This phase changes presentation only. Model, governance, research promotion,
transaction execution, workflow schedules and football methodology are unchanged.

## Basic, Expanded and Advanced

Roster assets and Players use one shared labelled player table with selectable
season points, weekly points, season projected VOR and (in Dynasty) asset index.
Basic includes identity, ownership/observed roster role, selected value and health
or eligibility. Expand holds role/source/replacement/scoring context; Advanced
holds the exact record and scope. A shared native-dialog player reader has closed
sections for projections, role/contract, scoring/results, cross-league cached
ownership and provenance. Existing Draft and Weekly reader behavior is retained.

Roster inventory includes loaded ineligible assets and explicitly lists unmatched
provider IDs instead of silently shrinking the roster. Best Ball roles reuse the
existing heuristic profile and never imply manual start/sit. Missing health is
unverified; missing projections and VOR remain unavailable, while zero/negative
values remain numeric. The weekly source resolver retains its original authority.

Team shows a small position table rather than large rank cards. Existing measure
components/weighting and same-league roster comparisons open on request. Canonical
metrics can contain legacy fallback inputs; partial projection coverage is stated.
There are no inferred new upgrades, correlations or empirical survival estimates.

Trades preserves the existing roster/player/pick selectors and owner functions.
Two team areas show offered chips. Evaluation shows both teams' before/after
canonical roster utility with configured rule checks; Expand separates starter,
depth and asset-index effects. Advanced explains existing fallback and pick-value
assumptions. Future picks never enter immediate lineup utility. Same-roster offers,
changed player ownership and stale visible results are blocked/cleared. These
checks are not provider trade approval or transaction authority.

League shows provider record/season points in provider order, not invented playoff
or survival rankings. Manager history and transaction records remain descriptive,
lazy-loaded through their original owner. Raw FAAB amounts do not imply normalized
budget comparability or calibrated behavior confidence. Chopped survival/cutoff
remains unverified without an authoritative supplied record.

Rules shows imported slot counts/eligibility first. Full scoring tables/examples,
raw settings/timing and all existing format/pool override controls are disclosures.
Unsupported active scoring rules remain visible before expansion. Linear examples
are restricted to known yards/event keys; bonus/threshold arithmetic is not guessed.
Recognized rules do not prove row-level projection exactness. Imported settings
without a timestamp do not imply an observed local waiver deadline.

## Owners and scope

`context-workspace.js` receives existing filter, legal-player, roster-pool and
exact contribution callbacks from `decision-ui.js`. It reuses `teamPowerMetrics`,
`rosterUtilityFromPool`, `tradeAssetValue`, `pickValue`, pool violations,
`FIEScoringSupport`, runtime slot contracts and provider state. Exposure reuses
Phase 4 cached managed ownership and denominator rules. Native reader focus/Escape
and row disclosure semantics remain owned by the editorial foundation.

No new player history or scoring replay is reconstructed. Missing game logs,
frozen forecasts, category components, private claims and synchronized started
exposure are explicitly unavailable or linked to their existing Weekly/Waivers
owner. Full global evidence/report navigation remains Phase 6; Draft lifecycle
redesign remains Phase 8.

Validation: null/zero and rule-example semantics; two-sided canonical trade effects
and pick separation; populated desktop/mobile fixtures for inventory, shared
reader, comparison, builder, scoring, history and unsupported/missing states;
prior phase regressions; one deterministic personal release closure.
