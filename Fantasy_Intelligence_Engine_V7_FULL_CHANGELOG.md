# Fantasy Intelligence Engine V7 — Full Changelog

This document consolidates every material change implemented in this chat, from the original V5 audit through the final V7 pre-deployment build.

## Phase 0 — V6 Foundation

### Technical architecture
- Decoupled UI rendering from full model recomputation.
- Removed the behavior where filtering/searching/sorting could trigger the entire scoring pipeline.
- Added calculation timing and recomputation diagnostics.
- Preserved V5 outputs where possible while isolating future model changes.

### TFG normalization
- Preserved raw TFG grades for display.
- Added position-relative, tie-aware TFG percentiles for modeling.
- Stopped treating raw TFG grades as directly comparable to percentile-scaled components.

### Lineup optimization
- Replaced greedy lineup filling with exact assignment logic.
- Added support for FLEX, SUPER_FLEX, IDP_FLEX and positional slot constraints.

### Data/model health
- Added coverage diagnostics for PFF, TFG and public IDs.
- Added visibility into missing-source and matching issues.
- Missing data continue to be treated as neutral rather than zero.

---

## V6.1 — Public Projections, Market Data and True VOR

### Automatic public projection source
- Added automatic Sleeper season projection feed support.
- Added automatic weekly Sleeper projection feed support.
- No API key required.
- Added fallback behavior if the projection feed fails.

### Exact league scoring
- Re-scored projected raw stats using imported Sleeper `scoring_settings`.
- Improved compatibility with unusual scoring formats and IDP-heavy leagues.

### Projection architecture
- Added separate Sleeper Baseline Projection and Engine Projection.
- Engine Projection uses bounded PFF, TFG, opportunity and production adjustments.
- Season adjustment capped around ±12%.
- Weekly adjustment capped around ±8%.

### Projected fantasy-point VOR
- Added projected replacement level in fantasy points.
- Added projected VOR:
  `Projected VOR = Projected Fantasy Points - League-Specific Replacement Projection`
- Shifted forward decision-making away from abstract 0–100 VOR.

### Market / ADP layer
- Added Sleeper draft-lobby ADP.
- Added format-specific ADP selection:
  - standard
  - half PPR
  - PPR
  - 2QB
  - dynasty
  - IDP where available
- Added Market Edge:
  `Sleeper ADP - Engine Projection Rank`
- Missing ADP/projection values no longer become fake zeroes.

### Draft Board
- Forward projections became the dominant input when available.
- Legacy Season Score became secondary.

### Export / player details
- Added projection, VOR, ADP and market-edge fields to drawers and CSV export.

---

## V6.2 — Team Analysis, Roster-Aware Waivers and Trades

### Team Analysis
- Added league-wide roster comparison.
- Added optimized starter projection by roster.
- Added total projected roster VOR.
- Added positional room strength and league rank.
- Added average-age / youth profile.
- Added identification of weak position rooms.
- Added available-player opportunities tied to roster weaknesses.

### Roster-aware Waiver Engine
- Replaced free-agent-only ranking with add/drop simulation.
- Simulates each waiver add against actual drop candidates.
- Added:
  - net roster improvement
  - starter improvement
  - recommended drop
- Waiver ordering now reflects actual team improvement.

### Trade Center
- Added multi-player trade simulation between Sleeper rosters.
- Added:
  - raw asset value
  - projected VOR
  - dynasty/acquisition value
  - optimized roster impact
  - starter impact
  - fairness
  - mutual-benefit view
- 2-for-1 trades no longer treated as equal just because raw values match.

---

## V6.3 — League Intelligence, FAAB and Validation

### Sleeper transaction history
- Added loading of current and linked prior league seasons.
- Added analysis of:
  - trades
  - waiver claims
  - free-agent moves
  - FAAB bids

### Manager profiles
- Added historical manager activity profiles.
- Added:
  - waiver aggressiveness
  - trade frequency
  - median winning FAAB bid
  - position tendencies
- Added likely trade-partner identification from complementary strengths/weaknesses.

### League-specific FAAB recommendations
- Added recommended FAAB amount and range.
- Uses league historical winning bids when available.
- Uses position-specific history where available.
- Adjusts for:
  - roster improvement
  - market edge
  - Sleeper trend
  - urgency
- Explicit fallback labeling when league history is insufficient.

### Prospective validation
- Added Validation tab.
- Added immutable first-seen weekly forecast snapshots.
- Snapshots are not overwritten by later updates.
- Added:
  - Engine MAE
  - Sleeper baseline MAE
  - relative improvement/deterioration
  - projection coverage
  - ADP coverage
  - average adjustment magnitude
  - engine-vs-market rank correlation

---

## V6.4 — Projection Uncertainty and Dynamic Season Learning

### Projection uncertainty
- Reframed floor/ceiling into approximate P10/P50/P90 outcomes.
- Added Projection Confidence.
- Confidence incorporates:
  - projection availability
  - role security
  - depth-chart position
  - PFF reliability
  - TFG coverage
  - recent evidence
  - injury uncertainty

### Start/Sit risk modes
- Floor mode now aligns with lower-percentile outcomes.
- Balanced mode aligns with central projection.
- Ceiling mode aligns with upper-percentile outcomes.

### Dynamic 2026 weighting
- Reduced static dependence on 2025 evidence as 2026 progresses.
- Early season:
  - mostly prior-year evidence
- Mid-season:
  - blended
- Later season:
  - predominantly current-season evidence
- Missing current data fall back to prior-year evidence rather than zero.

---

## V6.5 — Draft Assistant, Future Picks and Calibration

### Draft Assistant
- Added live Sleeper draft-state analysis.
- Reads completed picks and identifies future selections.
- Removes drafted players from candidate set.
- Added:
  - Draft Now vs Wait
  - likelihood target survives to next selection
  - projected VOR
  - market disagreement
- Rookie drafts use rookie-relative market ordering.

### Future draft picks in Trade Center
- Added traded-pick ownership from Sleeper.
- Added future picks as trade assets.
- Pick value adjusts for:
  - league size
  - round
  - projected original-owner strength
  - expected draft slot
  - rookie/player value curve
  - future-year uncertainty discount
- Stronger teams imply later/less valuable picks.
- Weaker teams imply earlier/more valuable picks.

### Automatic calibration
- Added learned overlay multiplier.
- Tests model-adjustment multipliers between 0.00× and 1.50×.
- Activates only when:
  - at least 200 completed player-weeks
  - at least 4 weeks of observations
  - calibrated model improves Sleeper baseline MAE by at least 1%
- Prevents early-season overfitting.

---

## V6.6 — Usage Features and Position-Specific Learning

### Position-specific usage
- Added Usage & Features section.

#### QB
- passing volume
- rushing involvement

#### RB
- carries
- weighted targets

#### WR / TE
- target involvement

#### IDP
- tackle involvement
- relevant splash-play opportunity where available

### Rolling backtest
- Added historical next-week usage backtest.
- Uses only information available before the predicted game.
- Avoids look-ahead leakage.

### Learned usage coefficient
- Tested by position.
- Activates only with:
  - at least 80 observations
  - at least 1% MAE improvement
- Usage adjustment capped at ±5%.

### PFF feature preparation
Structured position-specific evidence for future learning:

#### QB
- EPA/play
- BTT%
- TWP%
- pressure-to-sack rate

#### RB
- YCO/attempt
- elusive rating
- breakaway rate
- YPRR

#### WR / TE
- routes
- YPRR
- aDOT
- YAC/reception
- drops

#### DL
- pressures
- pass-rush grade
- run grade
- pass-rush usage

#### LB
- tackles
- stops
- missed-tackle rate
- box usage

#### DB
- tackles
- stops
- box/slot/deep alignment

---

## V6.7 — Opponent-Adjusted Matchups and Feature Attribution

### Opponent-adjusted matchup model
- Replaced raw fantasy-points-allowed logic.
- Measures opponent performance relative to each player's own prior baseline.
- Reduces schedule-strength distortion.

### Position-specific IDP matchup drivers

#### DL
- opposing pass volume
- total play volume
- protection context

#### LB
- opposing rush volume
- total play volume

#### DB
- opposing pass volume
- total play volume

### Learned matchup coefficients
- Separate calibration by position.
- Requires:
  - at least 100 observations
  - at least 1% MAE improvement
- Active impact capped at ±8%.

### Expanded forecast snapshots
Snapshots now preserve:
- PFF score
- PFF reliability
- TFG percentile
- usage signal
- matchup signal
- role momentum
- opportunity shock

---

## V6.8 — Team Context and Environment

### Team Context Lab
Added league-relative signals for:
- offensive play volume
- pass volume
- rush volume
- scoring/TD environment
- red-zone touches when supplied
- sacks/protection context when supplied

### Position-specific team-context interpretation

#### QB
- pass volume
- scoring
- pace
- protection

#### RB
- rush volume
- scoring
- pace
- red-zone environment

#### WR / TE
- pass volume
- scoring
- pace
- red-zone environment

#### DL
- opposing pass volume
- pace
- protection context

#### LB
- rush volume
- total play volume

#### DB
- pass volume
- total play volume

### Safeguard
- Team-context signal remains diagnostic only.
- Projection multiplier remains 1.00 until validation proves incremental value.

---

## V6.9 — Model Governance and Consolidation

### Model Governance panel
Added visible states:
- ACTIVE
- BOUNDED
- PARTLY ACTIVE
- DIAGNOSTIC
- CONTEXT
- SECONDARY
- UNAVAILABLE

### Explicit double-counting controls

#### Opportunity cluster
- injury
- teammate injury
- depth chart
- recent usage
- role momentum

#### Environment cluster
- Vegas totals
- team scoring environment
- matchup

#### Talent cluster
- Sleeper baseline projection
- PFF
- TFG

### Formal governance rule
A new feature family only becomes active if it improves out-of-sample accuracy over the same model without that feature.

### Decision hierarchy
Formalized:

`Projected Fantasy Points`
→ `Projected VOR`
→ `Roster Utility`
→ `Draft / Waiver / Trade / Team / Start-Sit Decision`

Legacy 0–100 scoring became explicitly secondary/fallback.

### Static audit
- Duplicate HTML IDs: none.
- Large single-file architecture identified as the main future technical maintenance concern.

---

## V7 — Pre-Deployment Consolidation

### Unified valuation layer
Added a canonical compatibility layer for:
- season value
- weekly value
- projected VOR
- fallback value

### Shared decision-engine hierarchy
All five decision engines now explicitly use the same forward-value structure.

#### Draft
- projected VOR
- projection rank
- market/ADP edge

#### Waivers
- roster improvement of add minus actual drop

#### Trades
- asset value
- projected VOR
- optimized roster impact

#### Team Analysis
- optimized starters
- positional VOR
- depth

#### Start/Sit
- weekly projection
- uncertainty
- exact lineup assignment

### Pre-Deployment Integrity panel
Added runtime/data checks for:
- player pool
- projection coverage
- VOR coverage
- optimizer status
- team-context activation state
- model-governance presence

### Architecture formalized as
`Sources`
→ `Identity`
→ `Features`
→ `Projection`
→ `Valuation`
→ `Decision Engines`
→ `UI`
→ `Validation`

### Deployment
- Final artifact remains a single self-contained HTML file.
- Designed for static hosting such as Cloudflare Pages.

---

## Final packaging pass
- Updated visible app version branding to **V7**.
- Added explicit `Release: V7` marker.
- Removed remaining visible V6.x release labels where applicable.
- Preserved historical references only inside changelog/audit context.
- Re-ran duplicate-ID integrity check.
