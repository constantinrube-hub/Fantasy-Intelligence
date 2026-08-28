# Fantasy Intelligence Engine V5 — Exhaustive Evaluation

*Review of `index_2.html` against the four stated goals: improved rankings vs ADP, league-specific waivers/trades/rankings, team analysis, and weekly start/sit.*

---

## Executive summary

This is a genuinely impressive single-file application. It's roughly 850KB of embedded data plus ~1,400 statements of tightly-written vanilla JS, and it already does most of what a good dynasty/redraft decision tool should do: it reads live Sleeper league settings, derives replacement level from *your* roster construction, blends multiple evidence sources with renormalization for missing data, and produces draft, waiver, and start/sit outputs from one shared player object model. The architecture is coherent and the statistical instincts are mostly sound.

The core weakness, measured against your four stated goals, is the same one flagged in your own plan and in the app's own "gaps" panel: **there is no real projection source.** Every "projected fantasy points" number in the app is *reverse-engineered from last season's scoring*, not a forward projection. That undercuts Goals 1 and 4 specifically. Everything else is polish and correctness tuning on top of a solid frame.

---

## Goal-by-goal completeness

### Goal 1 — Improved ranking vs Sleeper ADP (blended rankings + TFG + projections + league scoring)

**Status: Partially complete. Strong on blending, weak on the two headline inputs (ADP and projections).**

What works: `weightedModel()` blends current/future opportunity, TFG, PFF, league fit, contract, production, draft capital, and age curve, with automatic renormalization when an input is null. This is the right way to handle missing evidence and is implemented correctly. Weights are user-adjustable and persisted. League scoring genuinely feeds the model through `scoringFit()` and `scorePublicStats()`.

What's missing or wrong against the goal as written:

- **No ADP anywhere.** Despite the goal being "improved ranking *compared to* Sleeper ADP," ADP is never fetched or displayed. Sleeper exposes ADP via `players/nfl` metadata and separate draft endpoints, but you only pull `search_rank` (stored, never used in scoring). You cannot show an edge-vs-market delta without the market column. This is the single biggest gap for Goal 1.
- **No projections** feed the season ranking. `productionScore` is 2025 PPG percentile — backward-looking. For a 2026 draft board, last year's production is a prior, not a projection, and it structurally punishes rookies and rewards players in decline.
- **TFG grade scale is inconsistent.** TFG grades range 62–99, but they're fed into the weighted average on the *same 0–100 axis* as PFF percentiles and opportunity scores. A compressed 62–99 input with a high weight behaves very differently from a 0–100 input — it adds a near-constant offset with low variance, so TFG mostly nudges everyone up rather than differentiating. It should be re-scaled to a percentile or z-score within its group before entering the blend.
- **Multiple external rankings** ("an accumulation of several rankings") is aspirational — only PFF and TFG are present. There's no FantasyPros consensus, no ECR, no second opinion.

### Goal 2 — League-specific waivers, trade eval, player rankings

**Status: Waivers good. Rankings good. Trade evaluation entirely absent.**

- **Waivers** (`waiverScoreFor`) is the most sophisticated part of the app and it's well-conceived: it combines projected points, role momentum (snap trend + recent form), opportunity shock, buy-low efficiency regression, matchup, and the dynasty target score. FA-only gating is correct. This genuinely serves the goal.
- **League-specific rankings** are real — replacement level recomputes per league from roster slots, FLEX/SF/IDP demand, bench size and actual ownership. This is the app's best idea and it's implemented carefully.
- **Trade evaluation: does not exist.** There is no two-sided value comparison, no "give X get Y" delta, no positional-surplus logic, no trade UI. This is a whole missing pillar of Goal 2.

### Goal 3 — Team analysis (strengths/weaknesses/opportunities/risks)

**Status: Largely absent. The data exists; the feature does not.**

There is a "My roster" tab, but it's just the same player table filtered to your `ownerRosterId`. There is no aggregation: no positional-strength summary, no starter-vs-replacement gap by position, no bye-week or age-cliff exposure, no depth/injury risk rollup, no SWOT framing. Every ingredient needed (VOR per player, replacement baselines per position, age curves, contract expiries, injury status) is already computed per-player — you're one aggregation layer away from this feature, but that layer isn't written. Right now Goal 3 is effectively unaddressed.

### Goal 4 — Weekly start/sit (projected points, floor/ceiling, matchup, opponent)

**Status: Structurally complete, but resting on a synthetic projection.**

The machinery is all here and mostly sensible: `optimizeLineup()` does a greedy fill that correctly orders slots least-flexible-first, which is the right heuristic for lineup optimization and handles SUPER_FLEX/IDP_FLEX. `weeklyProjectionFor()` multiplies a baseline PPG by role, matchup, team environment, market (Vegas implied total), weather, and injury factors. Floor/ceiling come from a position-specific coefficient of variation. Weather via Open-Meteo and optional odds via The Odds API are wired in.

The problem is `baselinePPG()`: the "projection" is a blend of last-4-game and season-long *actual* PPG. So the weekly projection is really "recent scoring × adjustments." That's a reasonable heuristic mid-season, but:

- In Week 1 with no 2026 games played, it falls back to a crude `posBase × modelScore/60` — essentially a made-up number.
- It has no concept of *projected* target share, snap count, or game script beyond what already happened.
- Matchup strength (`matchupScoreFor`) is computed from **2025** weekly data against the current opponent — i.e., how that defense did last year, ignoring 2025→2026 roster/scheme turnover.

So the start/sit engine is well-built plumbing connected to a weak water source.

---

## Technical code review

**Overall quality is high.** It's dense but disciplined. Concrete issues:

**Correctness bugs / fragilities:**

1. **`render()` calls `assignScores()` on every render**, and `assignScores()` runs the full model + replacement recomputation + `updateWeeklyContext()` (which recomputes every prediction score for every player). Every sort click, filter keystroke, and tab switch re-runs the entire scoring pipeline over the full ~2,000-player pool. On the curated board it's fine; after Sleeper load it will feel sluggish. Scoring should be decoupled from rendering and memoized — recompute only when weights/league/week actually change.

2. **Matchup uses prior-season defense.** `matchupScoreFor` reads `weekly2025` exclusively. Early 2026 that's the only option, but it's never blended toward current-season data as it accumulates. It also silently returns neutral 50 for any position with <3 samples, which will be common for IDP.

3. **Hardcoded magic numbers** in `teamEnvironment` and helpers (`pm||63`, `pr||.57`) are league-average-ish but undocumented and untested against 2026.

4. **Name-matching is the silent failure mode.** Matching across Sleeper → PFF → TFG → nflverse → OTC is all `normName` equality plus an edit-distance≤2 fallback for TFG only. Contract matching falls back to name equality. There's no reporting of match *rate* — a player who fails to match just silently loses that evidence and gets renormalized away. You have KPIs for PFF/TFG counts but no "unmatched players" diagnostic. Given how much rides on joins, a match-quality panel is important.

5. **Percentile function is coarse and slightly biased.** `percentileMap` maps to a fixed 25–95 band (`25+70*(i/n)`), so even the worst player in a group floors at ~25 and the best caps at ~95. That compresses real spread and inflates weak players. It also uses `<=` counting which double-counts ties. Minor, but it feeds `productionScore`.

6. **`snaps2026`/`depth2026`/weekly2026 URLs will 404 early season** — handled gracefully via `Promise.allSettled`, good, but the fallbacks aren't always signposted to the user per-feed.

7. **Single 850KB HTML file** with data inline. It works and it's portable, but it's unversioned, hard to diff, and the daily `/players/nfl` (~5MB) is fetched live every league load with no caching despite your own plan calling for once-daily caching. `localStorage` is used for weights but not for the player map.

**Good practices worth noting:** proper CSV parser with quote handling, `Promise.allSettled` everywhere for resilient loading, HTML escaping via `esc()`, renormalizing weights instead of zero-filling, and the least-flexible-slot-first lineup fill. These are the choices of someone who knew what they were doing.

---

## Statistics review

- **Renormalized weighting: correct and appropriate.** This is the right call and it's implemented properly.
- **Replacement level / VOR: conceptually excellent, one weakness.** Deriving the replacement index from `teams × demand × (1+benchShare)` blended with actual ownership is a genuinely good, league-aware VOR. But VOR is computed off `modelScore`, which is itself a 0–100 blended index, *not* projected points. Real VOR should be in the currency of fantasy points (projected points above the Nth-ranked player at the position). As-is it's "value over replacement grade," which is directionally useful but not the textbook quantity and can't be summed into a roster-value total.
- **Floor/ceiling via fixed CV: reasonable heuristic, not calibrated.** The per-position CVs are plausible but hand-set, and floor/ceiling are symmetric-ish multipliers rather than modeled from the actual game-log distribution. For players with real 2025 game logs you could compute empirical quantiles instead.
- **TFG scale mismatch** (covered above) is the most impactful statistical issue — a 62–99 input masquerading as 0–100.
- **PFF handling is good** — percentile-based within position and shrunk toward the mean for small samples (the reliability field, 0–0.85), which is the correct instinct.
- **Trend bonus** uses `log10(1+adds)` — sensible dampening of the Sleeper trending signal.

---

## Data: present vs. beneficial

**Present and used well:** Sleeper (league, rosters, trending, player map), nflverse players/contracts/2025 stats/snaps, PFF 2025 (2,017 entries, all position groups), Open-Meteo weather, optional Odds API.

**Present but underused:** `search_rank` (stored, never scored), snap counts (only aggregated to a season average, not used as the primary role-momentum driver it could be), contract data (used for a #2-RB path bump but not for a roster-commitment risk view).

**Coverage gaps in your own data:**

- **TFG covers 23 teams, 558 players** — missing BAL, BUF, DEN, DET, HOU, KC, LAR, PHI, SEA (9 teams). The app reweights rather than penalizing, which is correct, but that's a lot of missing talent grades on contenders.
- TFG is grouped as REC (WR+TE combined), which loses TE-specific signal.

**Data that would most improve the tool, in priority order:**

1. **A real projection source** — FantasyPros CSV export (weekly + ROS + season), or a projections API. This is the keystone. It directly fixes Goals 1 and 4 and feeds true VOR. Your plan already identifies this as *the* open decision; it still is.
2. **ADP / ECR** — FantasyPros ECR or Sleeper ADP, to deliver the "vs ADP edge" that Goal 1 is literally named after.
3. **2026 in-season data as it accrues** — you have the URLs; the model just needs to *blend toward* current-season matchup/usage rather than leaning on 2025.
4. **Target share / air yards / route participation** (nflverse advanced or PFR) — far better role signals than depth-chart order for WR/TE/pass-catching RB.
5. **Official injury/practice report feed** — you correctly note nflverse has no post-2024 injury feed; Sleeper's injury field is coarse. A real practice-participation feed sharpens late-week start/sit.
6. **College production + testing** for rookies — you flag this; it's what's needed to move rookie priors past draft-capital + TFG.

---

## Cohesiveness

High. One shared `PLAYERS` array flows through one `assignScores()` pipeline into four tab views and a detail drawer — no duplicated scoring logic, consistent vocabulary (Model vs Target vs Season vs Waiver scores), and the model/data panel honestly documents its own gaps. The main cohesion risk is conceptual: **"Model score" (0–100 index) and "projection" (fantasy points) are two different currencies that the app sometimes mixes** (VOR off model score; baseline PPG partly off model score in Week 1). Picking projected points as the single source of truth and deriving indices from it — rather than the reverse — would make the whole thing more internally consistent.

---

## Prioritized recommendations

**Tier 1 — unblocks the stated goals:**

1. Add a projection source (FantasyPros CSV import is the fastest path) and make it the basis of `baselinePPG` and season ranking.
2. Add ADP/ECR and show a market-delta column — this is what makes Goal 1 an "edge."
3. Re-scale TFG to within-group percentile before blending.
4. Build the trade evaluator (Goal 2's missing pillar) and the team-analysis rollup (Goal 3) — both are mostly aggregation over values you already compute.

**Tier 2 — correctness and trust:**

5. Decouple scoring from `render()`; memoize and recompute only on real input changes.
6. Add a match-quality diagnostic (how many players failed each join).
7. Blend matchup and usage toward 2026 data as the season progresses instead of pure-2025.
8. Cache `/players/nfl` daily in localStorage per your original plan.

**Tier 3 — refinement:**

9. Recompute VOR in projected-points space so roster value is summable.
10. Use empirical game-log quantiles for floor/ceiling where 2025 logs exist.
11. Fill the 9 missing TFG teams when a new workbook is available.

---

## Bottom line

The bones are excellent. The gap between "V5" and "the tool your four goals describe" is mostly **one missing data source** (projections/ADP) and **two unbuilt features** (trade evaluation, team analysis) — not a rearchitecture. The scoring engine, league-specific replacement level, and start/sit optimizer are all solid foundations to build those on.
