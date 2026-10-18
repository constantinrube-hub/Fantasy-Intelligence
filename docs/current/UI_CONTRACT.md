# UI Contract (v10 "Lean")

Living contract for how the browser presents and recommends. Owner of the decisions
behind every number a manager acts on. Status: **R0 implemented** (classic UI safety
fixes); R1–R3 sections are binding design for the v10 views and are marked *planned*.

Source of truth for tunable values: `config/ui-decision-policy.json`
(browser copy generated to `app/generated/ui-decision-policy.js` by
`research/generate_ui_policy.py`; checked by `research/integrity_ui_policy_test.py`).

Scope rule: this contract governs presentation, aggregation and recommendation
*policy*. It does not change projections, scoring, rankings, M5/M6 gates, M9/M10
boundaries or waiver-v2 gates. Research outputs may be displayed read-only and
labelled "research"; they never feed totals, the optimizer or recommendations.

## 1. Product decisions (2026-10-17/18)

| ID | Decision |
|---|---|
| D1 | Desktop-first (1280–1600 px); mobile stays usable, no mobile-only features |
| D2 | Advisory only: no lineup submission, claims or trades; plain "Open in Sleeper" links allowed |
| D3 | Governance minimal: one coloured dot per value/recommendation, only on deviation |
| D4 | The active projection is the truth; alternatives only in Expand/Advanced, labelled there |
| D5 | Gain ≥ 3.0 Urgent · 1.0–2.99 Recommended · 0.25–0.99 Close call · < 0.25 nothing |
| D6 | Doubtful is treated as Out; monitor; recommend again only after the status changes |
| D7 | One win probability: quick matchup simulation, replaced by the full simulation on the same inputs |
| N1 | Injury status comes from the weekly projection feed first, the player DB second |
| N2 | Chopped: within 10 pts of the cut line, Recommended becomes Urgent (H2H off) |
| N3 | Range/variance calibration is a separate research work package; until then "Typical range" |
| N5 | Questionable = Monitor, never Urgent on its own |

## 2. Player status (implemented R0 · `app/core/status.js` → `window.FIEStatus`)

**Source order** for the selected league week:

1. Sleeper weekly projection feed `player.injury_status`, recorded per player as
   `weeklyStatusFeed {status, week, season, at}` by `applyWeekProjectionRows()` in
   `app/v9.3.3-runtime-integrity.js`. Used when it matches the selected week and is
   ≤ `status.projection_feed_max_age_minutes` old. A feed row with no designation
   clears an older database status.
2. Sleeper player database `injuryStatus` (edge-cached 24 h; Sleeper asks for at most daily calls).
3. Verified schedule bye → `BYE` (`FIEProjectionResolver.isVerifiedBye`; team codes compared canonically —
   nflverse `LA` = Sleeper `LAR`, `JAC` = `JAX`, `WSH` = `WAS`, `OAK` = `LV`, `SD` = `LAC` — WP0.7).

**Policy** (`status` in the policy file):

| Status | Recommendation value | Waiver add | Alert |
|---|---|---|---|
| none / Active | projection | normal | — |
| Questionable | projection | normal | Monitor |
| Doubtful | 0 (tie-break `doubtful_tiebreak_factor` × projection, never shown) | never CLAIM | Urgent if starting |
| Out, IR, Suspended, PUP, NA | 0 | never CLAIM; dynasty `STASH` when a legal reserve slot is free | Urgent if starting |
| BYE | 0 this week | allowed (rest-of-season value) | Urgent if starting |

`FIEStatus` API: `resolve(p, {week, season})`, `recommendationValue(p, value)`,
`irEligible(code, leagueSettings)`, `freeReserveSlots(roster, leagueSettings)`,
`addPolicy(p, {rosterId, league, rosters, dynasty})`, `normalize(raw)`, `policy()`.
Reserve eligibility follows Sleeper settings `reserve_slots`, `reserve_allow_out`,
`reserve_allow_doubtful`, `reserve_allow_sus`, `reserve_allow_na`.

## 3. League data freshness and week (implemented R0)

- The V9.3.3 DataClient fast path serves `league`, `rosters` and `users` from the
  research snapshot (`data/research/leagues/<id>/app/core.json`, rebuilt about every
  6 h, cached in the browser for up to a day). After the core stage of each league
  load, `scheduleLiveOverlay()` refreshes those parts from Sleeper once per league
  per 60 s via `FIEDataClient.refreshLeague`; `applyLiveOverlay()` merges them. When rosters change it rebuilds
  the player universe and then re-applies the selected week's Sleeper rows (`loadSelectedWeek`, cached) before
  rendering (WP0.8), so Weekly never shows legacy model values after an overlay.
- **Week:** the live Sleeper `settings.leg` wins over the snapshot week.
  `syncLiveLeagueWeek()` re-binds the selected week (`setWeek(…, {reason:'live-league-week'})`)
  unless the user picked a week for this league. When they differ, `#fieWeekSourceNotice`
  states: "Live Sleeper week N in use · research snapshot was built for Week M."
- Known limitation: if Sleeper is unreachable the snapshot values remain in use without
  an explicit offline notice (planned in R1 context bar: "data as of").

**Classic weekly lineup pool (WP0.9):** the Weekly optimiser (`app/decision-ui.js › lineupPool`) uses the active
roster only — players in reserve (IR) or taxi slots cannot be started in Sleeper and are shown as bench rows.

## 4. Recommendations (thresholds implemented in policy; v10 views *planned* R1)

- Gain = full legal re-optimization delta (`FIECore.LineupOptimizer.optimize`) over
  unlocked players with status-adjusted values; never single-slot subtraction.
- Tiers per D5; escalation per N2; Best Ball has no lineup tiers.
- R0 classic: waiver actions use `FIEStatus.addPolicy` (`app/decision-ui.js › waiverTransactions`);
  Home/portfolio waiver callouts skip unavailable adds (`app/decision-engines.js › strategicWaiverRows`);
  the lineup callout names a starter who cannot play ("can't play (Out)").

## 5. Alerts (R0 subset implemented · `app/weekly-alerts.js`)

Classic Weekly reads the **submitted** Sleeper starters for the selected roster and week
(`/v1/league/{id}/matchups/{week}` via `FIEDataClient`, 2-min cache) and shows
`#fieStarterAlert` when a starter is Doubtful/Out/IR/Suspended/PUP/NA/BYE or a starting
slot is empty. Doubtful adds the inactives reminder (~90 min before kickoff). Skipped for
Best Ball. Read-only.

Full catalogue (*planned* R1): EMPTY_SLOT, STARTER_UNAVAILABLE, STARTER_DOUBTFUL,
SWAP_URGENT/SWAP, CHOP_RISK, WAIVER_ADD (R2), STATUS_CHANGED, DATA_ISSUE, MONITOR_Q;
ordering Urgent → lock time → league priority → gain; one grouped line per player across leagues.

## 6. Projection display, dots and layers (*planned* R1)

- Basic shows the active value from `FIEProjectionResolver.week()` unlabelled.
- Dot relative to the league/position **primary source** (`primary_source` in the policy):
  none = primary and fresh; green = higher-tier source (e.g. FIE governed); amber =
  lower-tier, stale (> `freshness_minutes.projection_stale`), or partial scoring coverage.
- Ranges: "P10–P90" only when `range().calibrated === true`, else "Typical range".
- Layers: Basic (what/when) → Expand (row click, multi-open: why, alternatives) →
  Advanced inside Expand (stat line, scoring, distribution, drivers, provenance last).
  Expansion never changes values, model, horizon or selection.

## 7. Verification

| Check | Command |
|---|---|
| Status policy + R0 wiring | `node research/integrity_ui_status_policy_test.js` |
| Policy file ↔ generated copy | `python research/integrity_ui_policy_test.py` |
| Replay harness never injects app state | `node research/integrity_ui_replay_no_injection_test.js` |
| Browser replay on immutable captures | `node research/ui_replay/run.js --dist dist --suite classic` (see `TESTING.md`) |

All three integrity checks run in `research/release_gate.py`.
