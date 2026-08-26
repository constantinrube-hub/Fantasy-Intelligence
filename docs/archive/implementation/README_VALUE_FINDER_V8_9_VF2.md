# FIE V8.9-VF2 · Draft Value Finder + Top-100 Pick Optimizer

## Draft workflow
The Draft workspace now covers the full market:

1. **Draft Board**: broad league-specific ranking universe.
2. **Value Finder → Top 100 Pick Optimizer**: premium-pick value and timing.
3. **Value Finder → ADP 100–200**: evidence-supported sleeper discovery.
4. **Value Finder → ADP 200+**: snap-path-first deep sleeper discovery.
5. **Draft Player Analysis**: league/manager draft tendencies.
6. **Draft Assistant**: live execution using the same market/timing signals.

## Top-100 objective
Top-100 mode does not simply sort `FIE rank - ADP`. It tries to answer:

> If I like this player, should I take him now or can I safely capture more of the market discount later?

The optimizer therefore combines:
- absolute FIE/M5 value;
- market divergence;
- positional replacement cliff;
- VOR/scarcity;
- roster fit;
- historical evidence strength;
- estimated survival;
- opponent reach pressure;
- Value Capture;
- Reach Cost;
- Wait Cost;
- a 3-pick path proxy.

## Value Capture
For an undervalued player, Value Capture measures how far the current/planned pick has moved from the FIE valuation toward the player's Sleeper market price. This prevents the app from treating “FIE likes him” as synonymous with “take him immediately.”

## Tier Drop Risk
The optimizer searches the same-position legal pool for the best credible option expected to remain for the next pick. The policy-score drop, number of same-tier alternatives and VOR/scarcity create a Tier Drop Risk score.

## Live draft behavior
When the live Sleeper draft is available, survival incorporates the existing saved-draft manager/league pressure model. The Draft Assistant then shows TOP100 / VALUE / DEEP information beside its original recommendation.

## Governance
M6 is unchanged. Value Finder and Top-100 optimization use preseason/draft evidence and market timing; they do not bypass the weekly M6 production gate.

## Deployment
Commit/deploy the full release repository. Runtime changes are limited to:
- `index.html`
- `app/value-finder.js`

No Cloudflare build or configuration change is required.
