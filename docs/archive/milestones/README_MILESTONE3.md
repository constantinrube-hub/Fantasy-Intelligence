# Fantasy Intelligence Engine V8.5-M3

## Scope

V8.5-M3 continues the approved position-driver roadmap through Steps 16–18. It retains V8.2.2 as the frozen live decision model and preserves all Milestone 1–2 research.

### Step 16, position-specific advanced models

Adds lagged public advanced context when available:

- QB: NGS time to throw, intended air yards, CPOE/aggressiveness plus PFR pressure/bad-throw context.
- RB: NGS rushing efficiency, defenders in box, time to LOS and rushing yards over expectation.
- WR/TE: NGS air-yard share, separation/cushion and YAC over expectation plus PFR drop rate.
- EDGE/IDL: PFR individual hurry/hit/blitz fields plus public participation pressure context.
- LB/S/CB: defensive participation, man/zone/pressure context and lagged IDP event rates.

All advanced variables are lagged before prediction. The position-specific model is compared with recent-fantasy-point and M2 opportunity-xFP baselines on the same expanding validation folds.

### Step 17, natural experiments

Adds retrospective quasi-experimental studies for:

- QB changes and receiver/RB target/fantasy effects.
- Major receiver absence and teammate target-share redistribution.
- Lead-back absence and remaining-RB carry-share changes.
- Lead LB/S absence and teammate IDP scoring changes.
- Sustained role jumps and subsequent three-game scoring.

These are matched within-player/team deltas. They are explicitly **not causal estimates**. Coordinator-change analysis remains blocked until a reliable time-stamped historical coaching source is added.

### Step 18, rookie / Y1-Y2 opportunity model

Builds two young-player classifiers:

1. **Preseason prior:** draft capital, age, size and combine testing.
2. **After Week 3:** the preseason prior plus Weeks 1–3 NFL snap/opportunity/production evidence.

The target is a position-specific meaningful late-season role rather than fantasy points directly. A stricter high-value-role outcome is also reported descriptively.

## Guardrails

- `diagnostic_only: true` remains mandatory.
- `validated_candidate` means eligible for later integration review, not live-active.
- Public pass-play participation is not called true route participation.
- Being on defense during a pressure is not called an individual pressure or pass-rush snap.
- NGS separation is treated as target/quality context, not evidence that separation caused targets.
- No Step 16–18 output changes Draft, Waiver, Weekly, Trade or Team scoring.

## Browser surface

Lab now includes `M3 Research`, showing:

- advanced model performance by position,
- advanced-source coverage,
- natural-experiment effect estimates,
- Y1/Y2 classifier validation,
- young-player role-hit rates by position,
- methodology limitations and blocked analyses.

## Deployment documentation

Still intentionally deferred until the implementation roadmap is complete, per user request.
