# Fantasy Intelligence Engine — Full State Review

**Date:** 2026-08-26
**Artifact reviewed:** live VF2 `index.html` (hash-verified `OK` against `SHA256SUMS_CURRENT_VF2.txt`)
**Method:** Public repo cloned; forensic toolchain run in-session — `sha256sum -c` against both manifests, all 16 Python + 2 JS integrity tests, brace-matched extraction of scoring functions, and a jsdom runtime test of the override chain. Findings are against the live file, not the audit docs.

---

## Verification basis

- **Integrity manifests:** `CURRENT_VF2` manifest is clean — `index.html` and all VF2 artifacts verify `OK`. The older `V8.9_RTS` manifest shows 20 expected mismatches (superseded-by-VF2 files, plus one genuinely missing/quarantined market artifact).
- **Tests:** All 18 pass — 16 Python (`integrity_test`, `integrity_v89_test`, M2–M6, multileague, value-finder, decision-engines, draft-rank-sort, custom-rules, bulk-onboarding, portfolio-home, market-archive) and 2 JS runtime (value-finder eligibility/ranking, Top-100 optimizer).
- **Syntax:** Extracted inline JS (~1.30M chars across 6 classic script blocks) is valid under Node 22.

---

## 1. Correctness — what's actually true right now

**The headline P1 bug (slider reverts to legacy scorer) does not reproduce.** This is the most important correction. The note carried it as an active medium-severity bug with a patch ready. Tested directly: all six inline `<script>` blocks are classic, non-module, non-IIFE. In that setting a top-level `function assignScores(){}` declaration and `window.assignScores` are the **same** global binding — so when block 5 reassigns `window.assignScores` to the V89 wrapper, the bare `assignScores(...)` call inside block 0's slider handler resolves to the wrapper too. jsdom confirmed: slider path and direct window call both return `V89-wrapper(LEGACY-block0)`. The override chain is sound for this symbol.

> **Do not apply the P1 slider patch** — it would fix dead reasoning, not live code. The "scores silently revert" premise is false for this artifact.

The lexical-vs-window distinction in the notes is real, but it only bites when a `function` declaration is shadowed by a *later* `function` declaration of the same name in the same block, or when code runs inside an IIFE/module scope. Neither condition holds here.

**Two memory-flagged low/cosmetic items are already fixed:** `.rank-chip` and `.draft-constraint` are now both emitted by JS and styled in CSS (1:1). The ceiling-clamp and frozen-bucket items were not re-confirmed as active bugs and are not what's limiting the app.

---

## 2. Does the scoring improve your decisions? Signal-by-signal

Architecture: a **Sleeper-projection-anchored multiplicative adjustment stack**. That anchoring is the single best design decision in the app. The answer to "does it help" is **yes, modestly and unevenly**.

### Weekly projections (start/sit, waivers) — strongest path
`weeklyProjectionFor` takes the Sleeper hidden weekly projection as baseline and applies bounded multiplicative nudges:

```
sleeper × (1+adj) × (1+usageAdj) × (1+matchupAdj) × (1+marketδ) × (1+weather) × (1+injury)
```

Every adjustment is clamped tight (±0.08 on the main channels, ±0.12 total on `boundedProjectionAdjustment`). Starting from a market-grade projection and making small bounded corrections is defensible; worst case is bounded and the anchor is strong. **This will marginally beat raw Sleeper for start/sit and waiver ranking** (goal #2).

### Double-counting — concentrated in opportunity (highest-value fix)
`currentOpportunity` (195 refs) feeds at least three channels simultaneously:
- the `role` term in the fallback projection,
- `boundedProjectionAdjustment` (weight .045 — the largest single signal there),
- `uncertaintyFor` (widens CV below 70).

Then `usageProfile` / `usageAdjustment` layer **another** opportunity-derived signal on top. Opportunity is the most predictive input, so leaning on it is right — but multiplying correlated derivatives of the same underlying quantity inflates its effective weight beyond what the individual clamps suggest, and makes the "6 independent factors" framing misleading. Since the projection is anchored to Sleeper (which already prices opportunity), this double-/triple-counts what Sleeper already knows. **This is the highest-value correctness fix available**, and it directly blocks goal #5 (which factors correlate with success) — the factors are entangled, so the app can't cleanly attribute.

### Draft value (`seasonDraftScoreV89` + `marketEdgeValue`) — sensible, one caveat
Season score = rank-percentile of `playerDecisionValue` + 0.8 × market edge, where
`marketEdge = valueCurve(engineRank) − valueCurve(marketADP)` and `valueCurve(r) = 100 / r^0.43`.
The power-law value curve is a standard, legitimate rank→value transform (steep at top, flat in tail). Anchoring edge to ADP differential is exactly how you beat ADP (goal #1).
**Caveat:** the 0.43 exponent is hand-tuned, not fitted — so the *ordering* is trustworthy, the "how many value units" *magnitude* is not calibrated.

### `playerDecisionValue` — format-aware and genuinely good
Separate branches for chopped / best-ball / dynasty / redraft, each weighting floor vs. ceiling vs. remaining-VOR appropriately (best-ball rewards ceiling spike ×3.2; chopped weights floor; dynasty blends future-opportunity + age curve + talent). The most defensible modeling in the app; serves trade eval and team comparison (goals #3, #4).

### Where magnitudes are NOT yet defensible
Anything presented as a calibrated number — marketEdge "value units," and floor/ceiling bands when they fall back to heuristic CV rather than empirical P10/P90. `applyRiskBands` is honest about this: it tags `rangeSource: 'heuristic low/high, not calibrated P10/P90'` when it lacks ≥40 residuals. Good provenance discipline — but it means for most players early in a season, the ranges are illustrative, not statistical.

---

## 3. The research pipeline — comprehensive, accurate, deep?

**Breadth: strong. Depth of validation: overstated, but honestly gated.**

Real infrastructure in `research/`: M2–M6 modules, forward-snapshot MAE calibration (`computeCalibration`), expanding-window residual machinery, `statistical_guardrails.py`, per-league milestone bundles for ~20 leagues. `computeCalibration` searches alpha ∈ [0, 1.5] to blend engine toward/away from Sleeper and **only accepts the calibration if n ≥ 200 observations, ≥ 4 distinct weeks, and calibratedMAE < baseline × 0.99.** That eligibility gate is good statistical hygiene and is the correct backstop.

**But the evidentiary bar it clears is weak** — as the notes already correctly identified:
- A 1% MAE improvement over ≥4 folds with **no confidence intervals and no multiple-comparisons correction** is not strong evidence; noise can clear that threshold.
- Residual bands need ≥40 per position to escape heuristic fallback — achievable late-season, not early.
- The whole rigorous path is gated behind `FIE_M6_GOVERNANCE_ALLOW` (off by default). **This is the right call** — shipping the hand-tuned stack live while keeping the under-powered "validated" model dormant is honest.

**Critical breadth gap (blocks goal #5):** opportunity is still aggregated at **team level**, not disaggregated to players. Confirmed only `snapShare` exists at player granularity (14 refs); there is **no** `targetShare`, `carryShare`, `routeParticipation`, or `redZoneShare` in the live JS. These are *the* stable, predictive individual signals — the ones that let you find breakouts before ADP. The play-by-play data is fetched but stopped at team aggregation. **Until disaggregated, the app leans on Sleeper's opportunity read rather than computing its own edge.** This is the single biggest limiter on the app doing something Sleeper can't.

**Angles covered:** opportunity, matchup, market/Vegas (`marketContext` — implied team totals, RB-favors-negative-spread logic — a real edge input), weather, injury, talent grades.
**Angles missing that matter:** strength-of-schedule beyond next game, target *quality* / air-yards / aDOT, pace / neutral-script splits, receiver-QB and RB-OL dependency modeling.

---

## 4. Visuals — clean, but minimal

Rendering is **CSS bar-fills and HTML tables only** — no canvas, no SVG charts, no d3/chart.js. `scoreBar` renders horizontal `.bar-fill` bars; everything else is tabular with `.rank-chip` percentile chips (now styled) and a health-diagnostics strip. ~23.8KB CSS across 3 blocks.

**Verdict: clean and fast, but under-optimized for the decisions being made.** For a projection tool, the absence of any distributional visual is a real gap — floor/ceiling bands are computed but shown as numbers, not as range bars / whisker shapes that make start/sit calls instant. No sparkline for role-trend / usage-momentum, which is exactly what the eye needs for waiver decisions. The data to draw all of this already exists in the player objects. Low-effort, high-readability upside.

---

## 5. What's not fully functional / missing

| Item | Status | Impact |
|---|---|---|
| Player-level opportunity disaggregation | Fetched but not computed | Primary data gap — blocks goals #1, #5 |
| Input double-counting (opportunity triple-fed) | Live | Makes factor-attribution unreliable — blocks goal #5 |
| Calibrated uncertainty | Heuristic CV fallback dominates until ≥40 residuals/position | Bands illustrative early-season |
| `2026` hardcoding | **111 instances** in live JS vs. ~39 `state.league.season`/`activeSeason()` derivations | Silent break at season rollover — real, not cosmetic |
| Quarantined market data | `data/research/market/sleeper/2026/week_03.jsonl.gz` quarantined; RTS manifest still points at pre-quarantine path | Confirm nothing downstream depends on it |
| "Validated" research model | Exists, gated off correctly | Not trustworthy enough to unlock as-is |

---

## 6. Next steps — priority order

1. **Disaggregate opportunity to player level** (target share, carry share, route participation, red-zone share). Highest-value work in the project — the only path to an edge Sleeper doesn't already have; unblocks goals #1 and #5. Data is already in hand.
2. **De-correlate the scoring inputs.** Pick one channel for opportunity and remove it from the other two, or orthogonalize (residualize matchup/usage against opportunity). Then re-run `computeCalibration` — the honest MAE improvement may grow once double-counting stops.
3. **Fix the `2026` hardcoding** — derive every season reference from `state.league.season` / `activeSeason()`. Mechanical, but a season-rollover time bomb.
4. **Add distributional visuals** — floor/ceiling range bars on the start/sit table, usage-momentum sparklines on waivers. Cheap, big readability win.
5. **Strengthen the validation bar before unlocking M6** — add bootstrap CIs on the MAE delta and a multiple-comparisons guard. Don't unlock on 1%-over-4-folds.
6. **Do NOT apply the P1 slider patch** — the bug doesn't reproduce; the patch would fix dead reasoning, not live code.

---

## Bottom line

**Will it improve your fantasy decisions? Yes — modestly and unevenly.** The Sleeper-anchored, tightly-bounded, format-aware design means start/sit and waiver *rankings* beat raw Sleeper at the margin, and draft *ordering* against ADP is trustworthy — serving goals #1–#4 today. The provenance discipline (honest `rangeSource` tags, off-by-default governance gate, eligibility thresholds) is better than most hobbyist tools and reflects real statistical maturity.

**The ceiling is capped by two things:** opportunity is still Sleeper's read, not yours (no player-level disaggregation), and correlated inputs mean the app can't yet tell you *why* cleanly (goal #5). Fix those two and it moves from "a well-built re-ranking of Sleeper" to "a tool computing an independent edge." Read the magnitudes (value-units, early-season bands) as directional, not calibrated, until the validation bar is raised.
