# UI Contract (v10 "Lean")

Living contract for how the browser presents and recommends. Owner of the decisions
behind every number a manager acts on. Status: **R0 implemented** (classic UI safety
fixes) · **R1 implemented as opt-in preview** (`?ui=v10`: Overview, League Home, Lineup,
Matchup & Standings on a pure core). Sections still marked *planned* belong to R2–R3.

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

**Classic weekly decision value (WP0.10):** every classic weekly lineup decision (optimal lineup, Bench Δ, waiver week
gain, Start/Sit drawer) uses `FIEStatus.recommendationValue(p, weekProj(p))`: Out, IR, PUP, Suspended, NA and BYE count
0, Doubtful only as a tie-break (Doubtful = Out). The Week Proj column still shows the projection. In max-win mode a
simulated lineup that contains an unavailable player is not used; the max-points lineup is shown with a note naming him.

## 4. Recommendations (implemented R1 · `app/core/week-model.js` → `window.FIEWeekModel`)

- Gain = full legal re-optimization delta (`FIECore.LineupOptimizer.optimize`) over the
  **unlocked** slots of the **submitted** Sleeper lineup and the unlocked bench, valued with
  status-adjusted values (`recValue`: Doubtful × `doubtful_tiebreak_factor`, other unavailable 0);
  never single-slot subtraction. Each change is reported as `{slot, inPid, outPid, delta}` with a
  slot-legal pairing.
- Tiers per D5 (`FIEWeekModel.tierFor`); Chopped escalation per N2 only when the field is
  verified (eliminated rosters = `last_scored_leg`); `h2h_margin` stays off (`null`).
- Best Ball: no lineup tiers; the lineup shown is the optimal one (Sleeper sets it automatically).
- Live / locked players: a started player keeps actual + max(0, projection − actual) and is never
  moved; final games count their actual points (`FIEGameState.forTeam`, kickoffs converted from
  US/Eastern with DST).
- R0 classic: waiver actions use `FIEStatus.addPolicy` (`app/decision-ui.js › waiverTransactions`);
  Home/portfolio waiver callouts skip unavailable adds (`app/decision-engines.js › strategicWaiverRows`);
  the lineup callout names a starter who cannot play ("can't play (Out)").

## 5. Alerts

**Classic (R0 · `app/weekly-alerts.js`).** Classic Weekly reads the **submitted** Sleeper
starters for the selected roster and week (`/v1/league/{id}/matchups/{week}` via
`FIEDataClient`, 2-min cache) and shows `#fieStarterAlert` when a starter is
Doubtful/Out/IR/Suspended/PUP/NA/BYE or a starting slot is empty. Doubtful adds the inactives
reminder (~90 min before kickoff). Skipped for Best Ball. Read-only.

**v10 (R1 · `app/core/alerts.js` → `window.FIEAlerts`).** Codes: `EMPTY_SLOT` (names the bench
fill), `STARTER_UNAVAILABLE`, `STARTER_DOUBTFUL` (with inactives time), `SWAP_URGENT` / `SWAP` /
`CLOSE_CALL` (only changes not already covered by a status or empty-slot item; Questionable
swap-ins carry "confirm before lock"), `CHOP_RISK`, `MONITOR_Q`, `DATA_ISSUE` (quiet), `DRAFT`
(Overview, only for Sleeper status `pre_draft`/`drafting` — never in-season, WP0.3).
Lock time of an item = earliest kickoff among the players it touches, else the league's next lock.
Ordering: tier → lock time → league priority → gain.

**§5.8 Portfolio grouping — deviation from the R1 guide (2026-10-18).** The guide asked for
"one grouped line per player across leagues". Replaying Week 6 gave 44 queue rows for 23 leagues,
because every league's fixes were split across status, swap and empty-slot lines. The action
happens league by league in Sleeper, so v10 groups **actions per league** (one row, all items in
its Expand, `FIEAlerts.queue().actions`) and keeps **monitor items grouped per player** across
leagues (`FIEAlerts.queue().monitor`, e.g. "Questionable · starting in 2 leagues").
Not yet: `STATUS_CHANGED`, `WAIVER_ADD` (R2).

## 6. Projection display, dots and layers (implemented R1 in v10 views)

- Basic shows the active value unlabelled. In R1 the active value is the league-scored Sleeper
  weekly projection (`FIEScoringCore.score`, exact port of the classic V8.9 scoring compiler —
  position relevance, D/ST buckets, reception bonuses — parity-tested on every projection row of
  five leagues), a verified bye is 0, otherwise unavailable. Governed FIE rows are not consumed by
  the light path yet (none are activation-eligible today); when they are, they enter as tier
  `FIE_GOVERNED` and get a green dot.
- Dot relative to the league/position **primary source** (`primary_source` in the policy):
  none = primary and fresh; green = higher-tier source; amber = lower-tier or stale
  (> `freshness_minutes.projection_stale`). The win estimate always carries an amber dot until
  WP-V1 calibrates the spread.
- Ranges: "Typical range" (×0.78–×1.22 rule of thumb) — never labelled P10/P90 until calibrated.
- Layers: Basic row → Expand (native `<details>`, several open at once: game, status, typical
  range, source, inactive alternatives such as Sleeper's own published total) → Advanced inside
  Expand (projection age, primary source, status source, IDs, lock, per-rule scoring breakdown).
  Expansion never changes values. Live re-renders keep open rows open (`FIEV10Kit.repaint`).

## 7. v10 interface (R1 preview)

| Item | Implementation |
|---|---|
| Switch | `?ui=v10` on, `?ui=classic` off (remembered in `localStorage.fieUiMode`); default `default_ui` in the policy = `classic` until accepted |
| Coexistence | classic keeps running underneath; v10 hides `.shell` with `body.fie-v10`; no classic function is wrapped or patched |
| Routes | `#/overview` · `#/league/<id>/home|lineup|matchup` · `#/classic/<id>/waivers|trades|draft|lab` (bridge: classic UI, same league, real navigation; "← New view" pill returns) |
| Data ("light pass") | `app/v10/v10-data.js`: live Sleeper league/rosters/users/matchups (never the research snapshot), shared weekly projection feed, nflverse schedule, player catalog — all through `FIEDataClient`, lifetimes from `cache_seconds` |
| One number everywhere | Overview, League Home, Lineup and Matchup render the same `FIEWeekModel` object (A-03, replay check V-CONSISTENCY) |
| Win estimate | closed-form normal on the same per-player spread rules as the classic engine (`FIEDistribution`, parity-tested), amber dot |
| Playoff / survival odds | on demand: loads the league in the classic engine and runs `FIEDecisionEngines.runLeagueSimulation` (amber dot) |
| Refresh | context-bar Refresh re-reads every league-specific URL and the projection feed once; while visible the view re-renders every 2 min |

Known R1 limitations: no week picker (current Sleeper week + last week's results); Waivers,
Trades, Draft and Research Lab open the classic view; the classic Weekly win probability (Monte
Carlo on classic inputs) and the v10 estimate can differ by a few points.

## 8. Classic findings recorded during R1 (not changed in R1)

- `index.html › weeklyLineupValue` treats a weekly projection of 0 as missing and falls back to the
  raw Sleeper projection, so a player zeroed for status by the legacy path can still be started
  (Week 6 replay: Lamar Jackson, player DB "Out", feed "Questionable", started at 20.6 with
  P10/P90 0). v10 does not have this path. Candidate fix for R2: use `FIEStatus.recommendationValue`.
- The two status sources disagreed for Lamar Jackson at capture time (DB "Out" vs feed
  "Questionable"); R0's source order (feed first) is what v10 uses.

## 9. Verification

| Check | Command |
|---|---|
| Status policy + R0 wiring | `node research/integrity_ui_status_policy_test.js` |
| Policy file ↔ generated copy | `python research/integrity_ui_policy_test.py` |
| Replay harness never injects app state | `node research/integrity_ui_replay_no_injection_test.js` |
| v10 core contracts (scoring/distribution parity, kickoffs, WeekModel, alerts) | `node research/integrity_v10_core_test.js` |
| Browser replay on immutable captures | `node research/ui_replay/run.js --dist dist --suite classic` and `--suite v10` (see `TESTING.md`) |

All four integrity checks run in `research/release_gate.py`.
