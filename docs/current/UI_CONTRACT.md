# UI Contract (v10 "Lean")

Living contract for how the browser presents and recommends. Owner of the decisions
behind every number a manager acts on. Status: **R0 implemented** (classic UI safety
fixes) · **R1 implemented as opt-in preview** (`?ui=v10`: Overview, League Home, Lineup,
Matchup & Standings on a pure core) · **R2 implemented in the preview** (Waivers, week picker and completed-week
review, Overview v2, player reader and compare tray, Advanced content, switchable variance calibration) · **R3
implemented in the preview** (calibrated spread on, waivers with returning injured players and last-game carry-over,
Kicker & D/ST board, Players, Team, Trades, Research Lab v1 — §1 sign-off, §2.1, §5.12, §7.2, §7.3). Not built:
WP3.6 classic removal (after two clean Sundays on the v10 default).

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

**Sign-off 2026-10-19 (R3 WP3.0):**

| ID | Decision |
|---|---|
| S1 | WP-V1 calibrated spread **on** (`variance.mode = "calibrated"`): QB/RB/WR/TE ranges are P10–P90 and the win estimate loses its amber dot; K, D/ST and IDP keep the rule of thumb (marked *). The Week 6 out-of-sample check still runs; if coverage is far from 80 %, switching back is one policy value |
| S2 | §5.8 portfolio grouping deviation **accepted**: actions one row per league, monitor items grouped per player |
| S3 | Waiver alert thresholds unchanged (1.0 this week / 3.0 over the horizon), with injured starters assumed to return (§5.12 R3, WP3.7) so a healthy fill-in is not over-rated |
| S4 | Doubtful keeps the tie-break factor 0.01 in classic and v10 (Doubtful = Out); the inactives reminder covers late activations |

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

**§2.1 Last-game carry-over (v10 WeekModel only · R3 WP3.7).** Sleeper keeps a game designation until the next
injury report, so on Monday–Wednesday "Out" usually refers to last Sunday. Evidence (committed captures): in the
game week Sleeper projects 0 for 56 of 57 Out/Doubtful players; during Week 6 it already projected Week 7 for about
half of them (e.g. Lamar Jackson: Out, 23.1). Rule: an `Out`/`Doubtful` tag from the projection feed (policy
`status.last_game_carry_over`) next to a **positive Sleeper projection for the modelled week**, while the game is
pregame and kickoff is more than `status.last_game_carry_over_min_hours` (108 h ≈ before Wednesday's first report for
a Sunday game) away, is shown as `O·prev` / `D·prev` and treated like Questionable (Monitor, full value, alert "Out
last game — check this week's report"). From the first report of the week every tag counts again; TNF teams never
carry over. IR, PUP, Suspended and NA never carry over. Classic (`FIEStatus`, R0) is unchanged.

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
**R2 additions.** `WAIVER_ADD` (Recommended, never Urgent): the best free agent when its lineup gain is ≥
`waivers.alert_week_gain` this week or ≥ `waivers.alert_horizon_gain` over the horizon; Best Ball leagues keep
waiver tasks (no lineup tasks). `EMPTY_SLOT` / `STARTER_UNAVAILABLE` without a bench replacement name the best
free agent. Status changes are not queue items: they appear in the Overview's "Since your last visit" feed.

## 6. Projection display, dots and layers (implemented R1 in v10 views)

- Basic shows the active value unlabelled. In R1 the active value is the league-scored Sleeper
  weekly projection (`FIEScoringCore.score`, exact port of the classic V8.9 scoring compiler —
  position relevance, D/ST buckets, reception bonuses — parity-tested on every projection row of
  five leagues), a verified bye is 0, otherwise unavailable. Governed FIE rows are not consumed by
  the light path yet (none are activation-eligible today); when they are, they enter as tier
  `FIE_GOVERNED` and get a green dot.
- Dot relative to the league/position **primary source** (`primary_source` in the policy):
  none = primary and fresh; green = higher-tier source; amber = lower-tier or stale
  (> `freshness_minutes.projection_stale`). The win estimate carries an amber dot only in rule-of-thumb
  mode; with WP-V1 on (S1) it has none, and its Expand note states the in-sample calibration.
- Ranges: "Typical range" (×0.78–×1.22 rule of thumb) — never labelled P10/P90 until calibrated. R2: policy
  `variance.mode = "calibrated"` (on since R3 WP3.0, S1; measurement and decision note in the project doc
  `claude/FIE_WPV1_VARIANCE_CALIBRATION_2026-10-18.md`, reproducible with `research/wpv1_measure_spread.py`) switches QB/RB/WR/TE to "P10–P90" = projection × the
  measured outcome ratios; the win estimate's spread follows (σ = (P90 − P10)/2.563). K and D/ST keep the rule of
  thumb. Lineups, recommendations and waiver gains use means only and never change with this switch.
- Layers: Basic row → Expand (native `<details>`, several open at once: game, status, typical
  range, source, inactive alternatives such as Sleeper's own published total, or "No alternative projection
  differs") → Advanced inside Expand in the §5.2 order (R2 · WP2.1): projected stat line → scoring under your
  league rules → distribution (mean, σ, range, calibration) → lineup context (in your best lineup: cost if he
  can't play; otherwise: gain if forced to start, best slot) → provenance (sources, ages, kickoff UTC, IDs).
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

### 7.1 R2 additions (preview)

| Item | Implementation |
|---|---|
| Week picker | League header select (W1–W18; live / review marked); `#/league/<id>/<tab>?week=N`. Past week → Lineup shows the completed-week review; future week → projections for the current roster; Waivers always use the live week |
| Waivers (§5.12) | `app/core/waivers.js` + `app/v10/v10-waivers.js`, tab replaces the classic bridge |
| Review (§5.13) | `app/core/review.js`, shown in Lineup for past weeks |
| Overview v2 (§5.14) | WAIVER_ADD in the queue; "Since your last visit" feed; "My players this week" |
| Reader / compare (§4.5) | `app/v10/v10-reader.js`: every player name opens one side panel; pin up to 3; Compare in the current league's scoring |

### 7.2 R3 additions (preview)

| Item | Implementation |
|---|---|
| Kicker & D/ST board (WP3.5) | `app/v10/v10-specialists.js`, in Lineup (live week) for every specialist position the league starts. Rows: your rostered K / D/ST (this week as in the lineup, later weeks Sleeper's projection with opponent; byes from the schedule even before Sleeper publishes the week) and the top 5 free agents by lineup gain, then projected points, with the drop only when there is a gain. Gains are `FIEWaivers` rows (identical to the Waivers tab, replay V-SPECIAL). A chip warns when no rostered player at the position plays in a horizon week (bye). Opens by itself when the best add gains ≥ `waivers.alert_week_gain` this week. In-season copy only: no PAY / WAIT / STREAM |
| Players (WP3.2) | League tab `players` (`app/v10/v10-team.js`, numbers `app/core/team-views.js › FIETeamViews.players`): every projected player the league can start, in league scoring and status-adjusted exactly as in Lineup; columns # · player (status chip, reader link) · game · this week · later horizon weeks · horizon sum · owner (yours / team / free agent; IR/taxi marked). Visible filters: position, owner (all / free agents / mine / other teams), sort horizon (this week / W–W+2), search (name or team code). Filters live in the view and **reset when the league changes**; 50 rows, "Show 50 more". Rows expand to the shared player detail. Always the live week |
| Team (WP3.3) | League tab `team` (`FIETeamViews.team`): (1) **position strength** — every active team's optimal lineup this week (status-adjusted), points credited to the player's position, your rank, league median and best team, bottom quarter shaded; total rank. (2) **Depth** — for each starter of your best lineup the points lost if he can't play (`WeekModel.lineupContext`, full re-optimisation) and the share your bench recovers; **thin** = below `team.thin_recovery` (policy, 0.4). (3) **Byes** in the later horizon weeks: points lost = best lineup with this week's values minus the same with bye players at 0 (works before Sleeper publishes the week). (4) **Roster** with real Sleeper slots (starter slot / BN / IR / TAXI), this and later weeks, season projection per game (none for D/ST: bucket scoring cannot be applied to season totals), ADP (dynasty ADP in dynasty) and the gap to the best free agent at the position — a replacement gap, labelled as a simple VOR proxy |
| Trades (WP3.4) | League tab `trades` (`app/v10/v10-trades.js`, numbers `app/core/trades.js › FIETrades.evaluate`): choose a partner, tick players on both sides (reserve/taxi marked); the effect on **both** teams' optimal legal lineups per horizon week and in total, plus a **season rate** (Sleeper season projection in league scoring ÷ games, optimal lineup per game; D/ST excluded) and a one-line verdict that flags when short-term and season effects disagree. Rules: reserve/taxi players don't start; if a traded player is locked this week, this week is not counted; drops needed for roster size are reported (lineups assume the weakest bench players go); entry-class floor and legacy cap are checked. Expand "Assets" = Sleeper market ADP (dynasty ADP in dynasty), season rate, age — labelled "market view, not an FIE value". **No fairness score, no offer is sent.** Picks are not valued in v10: dynasty leagues link to the classic evaluator (asset index) |
| Draft placement (WP3.4) | No v10 Draft view; the classic Draft link appears only where the lifecycle needs it — leagues `pre_draft`/`drafting` and dynasty leagues (rookie drafts). In-season redraft leagues no longer show it |

### 7.3 Research Lab v1 (R3 · WP3.1)

Route `#/lab/<state|eval|forecasts|rankings|docs>?league=<id>` (`app/v10/v10-lab.js`, computations
`app/core/lab.js › FIELab`), linked from the top bar and every league. **Display only** — nothing in the Lab feeds a
total, the optimiser or a recommendation; research artifacts are labelled "research". The classic Lab (validation,
model detail) stays reachable from the Lab's tab bar.

| Tab | Content |
|---|---|
| Model state | One line for the whole portfolio ("Sleeper-only mode: 0 of N rostered players use a governed FIE projection", weekly research view blocker, runtime model activation). Per league: active projection source per position for your players (from the WeekModels) and the weekly research view status/blockers. For the selected league: the research pipeline's per-position decisions (production model, decision, best challenger, reason) — fetched for that league only, because no index of pipeline runs is served |
| Evaluations | Week picker (completed weeks). Projection error by position for every rostered player of the league projected ≥ 3, **in league scoring**: Sleeper's projection for that week (as published now) re-scored vs Sleeper's `players_points`; MAE, bias (actual − projection), RMSE, biggest misses; did not play = 0. An unscored week (pregame payload) is "not scored", never a 100 % miss; the newest week may be partial while games run. "Review all leagues" (on demand): the four-row review (`FIEReview`) for every league that week and the portfolio sum |
| Forecasts | This week by game (kickoff order): rostered players projected ≥ 3 with active value, Sleeper's own published total and the last-4 average in league scoring (`FIELab.lastN`, Sleeper matchups, unscored weeks skipped). FIE research (M10) is not shown while the weekly research view is blocked |
| Rankings | Per position: this week and the horizon in league scoring (`FIETeamViews.players`) beside the FIE league season board p50 and board rank from the research pipeline (`rankings.json`, joined by `sleeper_id`; preseason run, full-season value, not refreshed weekly) |
| Documents | The league's served research artifacts (readiness, report summary, season board, weekly research view) with status, generation time and raw JSON |

### 4.5 Player reader and compare tray (R2 · WP2.2)

One reader for every view. It shows the player in the league being viewed:
- this week and the next weeks of the waiver horizon (league scoring), with "not yet" for unpublished weeks;
- who rosters him;
- his value to your lineup: on your roster, the lineup context; elsewhere, the gain if you added or acquired him
  and the drop (FIEWaivers in exact mode);
- your other leagues (from the Overview);
- the shared Expand/Advanced.

"Pin" keeps up to 3 players for this browser session; "Compare" shows them side by side with the same rows.

### 5.12 Waivers (R2 · WP2.4 · `app/core/waivers.js`)

- **Pool:** players with a Sleeper projection in the horizon, not on any roster (players, reserve, taxi), with
  a position eligible for a starting slot and an NFL team (or a team D/ST). League rules apply: an entry-class
  floor removes ineligible players; a legacy cap forces a legacy drop. Pre-selection takes the top 40 per position
  by Sleeper's published points, then exact league scoring.
- **Gain:** for each week of the horizon (`waivers.horizon_weeks`, default 3; unpublished weeks are reported and
  never counted), optimal legal lineup with the add (and the drop) minus without it, using the same
  status-adjusted values as the Lineup tab. In the current week, started games are locked: locked free agents add
  0, locked starters keep their slots, locked players are never dropped.
- **Exact pruning:** adding one player changes an optimal assignment by one augmenting path, so the gain is at most
  the add's value minus the lowest starter value that week. Candidates that cannot gain in any week are not
  optimised. Equality with exhaustive search is tested on every captured league.
- **Drop:**
  - none if there is a free roster spot;
  - otherwise the least valuable legal player (active roster, not locked) who is not in any week's optimal
    lineup with the add, else the best of the 4 weakest.
  - "Value" = horizon value + the season projection per game for unpublished weeks, ties broken by ADP.
  - Dynasty: dynasty ADP ≤ `waivers.dynasty_protect_adp` (150) is never suggested. Any drop with ADP ≤ 150 shows
    a "costly" chip.
- **Status:**
  - Out / IR / Doubtful / … players are never adds; they go to "Injured — watch / stash" (STASH only in dynasty
    with a legal reserve slot).
  - **R3 WP3.7 — later weeks follow Sleeper.** The current week uses the status policy (§2, §2.1). For every later
    week the value is Sleeper's published projection for that week: Sleeper projects 0 (or nothing) for players it
    expects to miss that game and a value once it expects them back. `waivers.long_term_zero` (now empty; R2 had
    IR/PUP/NA/Suspended) can still force statuses to 0 in all weeks.
  - **Returning players:** your injured players (unavailable now, not on bye) count again from the first week Sleeper
    projects them into your best lineup — **including players in an IR slot**, who rejoin the pool (activating
    them then needs a roster spot; the Waivers card says so). `returning` lists each with that week or "not within
    the horizon".
  - **Fill-in:** an add whose gain is ≥ 0.25 before such a return and ≤ 0.25 from the return week on is labelled
    "fill-in until X Wn" — only if holding X out in that week would raise the add's gain by ≥ 0.5 (causal check; a
    D/ST is never a fill-in for an RB).
  - **If he stays out:** Expand shows the horizon gain with all returning players held at 0. Other players'
    projections are unchanged, so a backup's projection still assumes the starter plays (handcuffs are understated).
  - **Injured starters are never drop suggestions:** an injured player whose healthy value (season projection per
    game, or a later-week projection) is at least your weakest starter is listed under protected drops.
  - Ranking (horizon gain) and alert thresholds (S3) are unchanged; they now use the return-aware gains.
- **Display:**
  - Basic: up to 15 rows, at most 3 per position (one streamable position cannot crowd the list), per-position
    chips; **no CLAIM and no bid** (A-25).
  - Expand: per-week projection, gain, whom the add replaces, drop values, the league's FAAB market for the
    position (median / P75 / max winning bid this season) and your budget.
  - Advanced: provenance.
  - Sections: last processed waiver run, FAAB budgets. An eliminated team gets no adds.

### 5.13 Completed-week review (R2 · WP2.3 · `app/core/review.js`)

On actual points from Sleeper's matchup payload of that week:
1. **Submitted** — Sleeper's official points.
2. **Best by Sleeper projection** — the optimal legal lineup by the projection for that week (Sleeper's endpoint
   as published now; status-adjusted), scored with actual points.
3. **Best in hindsight** — the optimal lineup by actual points (upper bound).

Also shown: lineup efficiency, points left on the bench, best unused players, and every player's projected vs
actual. Pool = the players in that week's matchup without current IR/taxi (approximation for mid-season moves).
Best Ball: submitted = hindsight by definition. A week without non-zero points is "not scored yet".

### 5.14 Overview v2 (R2 · WP2.5 · `app/core/portfolio.js`)

- **Since your last visit:**
  - status changes of your players (Urgent when he now can't play and starts somewhere; a bye is not a status
    change);
  - your processed waiver claims (won with bid / failed), trades and free-agent moves since the previous visit
    (transactions of the previous and current week).
  - The baseline is the previous visit's snapshot in this browser (localStorage), frozen for the browser session
    so live re-renders keep the same feed.
- **My players this week:** every player on your rosters with the number of leagues he starts in and is rostered
  in, status and game; Expand lists the leagues with slot and projection. A-26: counts equal roster contents
  (tested).

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
| v10 R2 contracts (waivers exactness and legality on 23 leagues, market, review, portfolio, context, aliases, calibration switch) | `node research/integrity_v10_r2_test.js` |
| v10 R3 contracts (carry-over and its 108 h guard, returning players, fill-in causality, injured-starter protection, Players/Team, Trades reversibility, Lab evaluation) | `node research/integrity_v10_r3_test.js` |
| WP-V1 spread measurement (research, read-only) | `python research/wpv1_measure_spread.py --weeks 1-5 [--check]` |
| Browser replay on immutable captures | `node research/ui_replay/run.js --dist dist --suite all` (classic 10, v10 17 checks; see `TESTING.md`) |

All six integrity checks run in `research/release_gate.py`.
