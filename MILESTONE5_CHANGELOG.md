# Fantasy Intelligence Engine V8.7-M5 Changelog

## Scope

V8.7-M5 implements roadmap Steps 24–27 on top of the completed V8.6-M4 research stack. It is the first decision-integration milestone, but integration is deliberately fail-closed. The frozen V8.2.2 live path is calculated first and remains the fallback for every player and every decision domain that has not independently cleared its historical gate.

## Step 24: Draft integration

- Added an availability-conditioned player-season validation layer built from the M4 out-of-sample weekly projections.
- Evaluates season-total MAE, positional rank correlation and top-quartile identification versus the existing baseline.
- A position receives a Draft-policy gate only when:
  - its upstream M4 position model is a validated candidate,
  - season-level MAE improves by at least 1%, and
  - the improvement is positive in at least 67% of eligible holdout folds, with at least two positive folds.
- The existing Sleeper/engine season projection remains the preseason production anchor. M5 does not pretend observed weekly aggregation is a complete injury/availability-aware preseason season model.
- When a Draft gate and the active format gate both pass, M5 may contribute:
  - validated production shape,
  - M3 young-player role evidence,
  - league VOR,
  - market edge,
  - format-specific utility.
- Draft Assistant remains responsible for manager tendencies, pick survival and roster-specific context. M5 only supplies gated production/future-role inputs rather than replacing those existing mechanisms.
- Weekly-only M5 activation is isolated from Draft Assistant fallback inputs, so a good weekly model cannot silently alter Draft value if Step 24 did not pass.

## Step 25: Waiver integration

- Added a position-specific Ridge policy predicting mean fantasy points over the next three games.
- Candidate inputs are pre-decision information from M4/M2, including:
  - current FIE projection,
  - recent fantasy baseline,
  - opportunity xFP,
  - lagged xFP residual/regression evidence,
  - lagged opportunity-change signal,
  - role-breakout evidence,
  - teammate competition signals where available.
- Expanding validation is performed chronologically.
- A Waiver-policy gate requires:
  - upstream M4 position validation,
  - at least 1% MAE improvement versus recent fantasy production,
  - positive improvement in at least 67% of eligible folds, with at least two positive folds.
- Deployable model specifications export imputation, scaling and Ridge parameters rather than opaque Python objects.
- M5 can overwrite `waiverScore` only for free agents whose current row, position, waiver gate and format gate all pass.

## Step 26: Weekly Start/Sit integration

### Weekly ranking gate

- Added direct lineup-oriented validation rather than relying on MAE alone.
- Evaluates by position/week:
  - Spearman rank correlation,
  - top-quartile precision,
  - top-1 regret versus the best actual scorer.
- A weekly mean projection can enter the live decision path only when:
  - the M4 position model is validated,
  - rank correlation improves by at least 0.01,
  - top-quartile precision does not materially deteriorate,
  - top-1 regret does not materially deteriorate.

### Risk calibration gate

- Added chronological residual-quantile calibration for P10/P25/P50/P75/P90-style risk bands.
- For test season Y, residual quantiles are learned only from earlier completed holdout seasons.
- P10/P90 can replace the legacy range only when both:
  - the weekly mean gate passes, and
  - the position's historical risk calibration passes coverage/tail checks.
- A validated mean model therefore cannot automatically overwrite floor/ceiling estimates.

## Step 27: Format-specific strategy

A single football projection core now feeds transparent downstream decision policies for:

- Redraft
- Dynasty
- Redraft + Best Ball
- Dynasty + Best Ball
- Chopped

### Redraft

- Emphasizes season production, league VOR, current role, weekly shape and market edge.
- Short-horizon waiver policy emphasizes next-three-game projection and role change.

### Dynasty

- Adds future-role probability, age curve, talent and market context.
- Remains `partial_validated` at most until a full multi-year dynasty asset-value backtest exists.
- Partial validation is not sufficient for M5 live format activation.

### Best Ball

- Added a player-level spike-week proxy based on top-quartile weekly finishes.
- Validation now records average improvement, positive folds and a position-level candidate status.
- Best Ball format activation requires both a validated format profile and position-specific Best Ball proxy evidence.
- This is explicitly not represented as a full historical roster-level best-ball simulation.

### Chopped

- Added player-level bust-risk validation using bottom-quartile weekly outcomes and ROC AUC.
- Position-level validation requires robustness across folds.
- Chopped activation additionally requires validated downside calibration for that position.
- Full guillotine survival modelling still requires historical roster/elimination data and remains a later limitation.

## Fail-closed runtime integration

New research bundle:

- `data/research/milestone5.json`

New current-season contract:

- `data/research/current/milestone5_current.json`

A current player can receive an M5 decision value only when all applicable conditions pass:

1. empirical M5 bundle status is complete,
2. current snapshot build matches `V8.7-M5`,
3. snapshot is explicitly marked active/ready/complete,
4. historical scoring profile matches the loaded Sleeper league,
5. current player row has `activation_eligible=true`,
6. the specific position passes the relevant Weekly/Draft/Waiver gate,
7. format-specific transforms additionally pass their format and position proxy gates.

Otherwise the already-calculated V8.2.2 value is retained.

## Separate decision gates

M5 now exports explicit independent gates for:

- weekly mean positions,
- weekly risk positions,
- Draft-policy positions,
- Waiver-policy positions,
- validated format profiles,
- position-level format proxy gates.

This prevents evidence from one decision problem from being reused as permission for another.

## UI

Added `Lab → M5 Decisions` with:

- bundle/current snapshot state,
- loaded-league scoring compatibility,
- Weekly/Draft/Waiver gate counts,
- Step 24 season validation,
- Step 25 next-three-game waiver validation,
- Step 26 ranking/risk calibration,
- Step 27 format strategy profiles,
- activation contract,
- retained limitations.

## Research automation

- Existing manual research workflow now builds Milestones 1–5 in order.
- M5 bundle validation is included.
- Current-season snapshot generation is deliberately not automated in M5; that is roadmap Step 29.

## QA corrections made during M5

- Removed an invalid cross-script dependency on M1-local JavaScript state by carrying `scoring_settings` directly in the M5 bundle.
- Routed M5 research navigation through the existing V8.2 navigation renderer instead of an unsafe parallel render wrapper.
- Added independent decision-domain gates after detecting that upstream model validation alone was insufficient permission for Draft/Waiver/Weekly changes.
- Added position-level Best Ball/Chopped format gates rather than allowing evidence from one position to authorize another.
- Isolated Draft Assistant fallback weekly shape from weekly-only M5 activation.
- Strengthened Waiver activation so it also requires a validated upstream position model.
- Added direct weekly ranking validation before M5 can change Start/Sit means.

## Deferred by design

- Step 28 advanced second-wave research.
- Step 29 current-season automated model/snapshot generation.
- Step 30 permanent live model governance/rollback layer.
- Detailed deployment instructions, per user request, until all roadmap steps are complete.
