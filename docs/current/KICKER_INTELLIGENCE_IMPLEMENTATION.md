# Kicker Intelligence Implementation

## Purpose
Kicker is now a first-class specialist position in Fantasy Intelligence. The engine does not treat K as an ordinary offensive player and does not rank kickers from raw fantasy-point history alone. It separates team opportunity, kick distance, conversion, league scoring, replacement scarcity, and streaming depth.

## Architecture
1. `research/kicker_contract.py` owns K roster detection, scoring-key recognition, signatures and exact-scoring profile metadata.
2. `research/fie_kicker.py` builds historical kicker-week rows from nflverse play-by-play, creates leakage-safe rolling opportunity/skill features, performs chronological validation, exports raw-outcome models, augments M1-M6, and maintains the portfolio K scoring inventory.
3. `research/build_current_snapshot.py` uses the governed K model for current-week raw kick outcomes and then applies exact Sleeper scoring. If validation is not cleared, Sleeper remains the decision baseline.
4. `app/kicker-intelligence.js` exposes weekly rankings, floor/ceiling when validated, next-three streaming value, replacement level, streaming depth, and PAY / WAIT / STREAM draft strategy.

## Exact scoring support
Supported K scoring includes:
- `fgm`
- arbitrary made-FG distance buckets such as `fgm_0_19`, `fgm_40_49`, `fgm_50p`
- `fgm_yds`, including Genesis-style points per made field-goal yard
- `fgmiss`
- arbitrary missed-FG distance buckets such as `fgmiss_0_19`, `fgmiss_30_39`, `fgmiss_50p`
- `xpm`
- `xpmiss`

The football projection is independent of fantasy scoring. Raw distance/opportunity outcomes are scored afterward for the exact loaded league.

## Historical baseline and validation
Historical K rows are built from play-by-play and schedules. The baseline intentionally remains transparent: recent FGA/XPA opportunity plus league-average conversion. FIE then adds leakage-safe features for recent team FGA, XP opportunity, long-field-goal usage, team scoring, shrunken make rate, shrunken long-distance make rate, home/away and available market context.

Validation is chronological by season. K promotion requires multiple positive holdout seasons, positive mean MAE improvement versus baseline, and rank correlation at least as strong as the baseline. Otherwise the K model remains diagnostic only.

## Draft versus stream logic
The browser evaluates:
- league teams and K starter count
- number and quality of available K
- top-kicker weekly edge over league-adjusted replacement
- free-agent streaming depth per team
- scarcity pressure

Output is deliberately simple:
- **PAY**: a meaningful top-K hold edge plus thin replacement/streaming pool
- **WAIT**: some hold value or scarcity, but not enough to spend a meaningful premium
- **STREAM**: replacement and free-agent quality are close enough that draft capital should be allocated elsewhere

This is a decision aid, not a hard-coded rule. The historical K model remains fail-closed, and the UI labels whether the active projection is FIE or Sleeper.

## Portfolio status
The current 19-league registry contains 5 kicker leagues. The generated inventory is `data/research/kicker/scoring_inventory.json`. All currently registered K scoring keys are recognized, including the Genesis exact-yard and distance-specific miss rules.

## Workflow
`build-fie-research.yml` now runs K integrity tests, builds K research after D/ST augmentation, validates M4-M6 again, and refreshes the kicker scoring inventory. `build-fie-current.yml` refreshes both specialist inventories and packages K current rows when present.

After deploying this repository:
1. Run **Build FIE Research Milestones 1-6** for a league that starts K. This creates/updates the governed K historical model for that league.
2. Run **Refresh FIE Current Season** to create the current K board from the validated model or Sleeper fallback.
3. Open **Weekly → Kicker Intelligence** in the app.
4. For leagues without K, the tab remains hidden and the specialist engine is not activated.

## Current baseline scope and next challengers
The production baseline is intentionally public-data and interpretable. The next research challengers are red-zone stall rate, fourth-down/field-goal coaching aggressiveness, point-in-time weather and wind, stadium/roof effects, injuries, and market-line movement. These should be promoted only if they beat the baseline in point-in-time chronological validation.
