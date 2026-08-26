# V8.9-VF2 Value Finder + Top-100 Pick Optimizer Changelog

## Built on V8.9-VF1
This release keeps the existing Draft Value Finder modes for ADP 100–200 and ADP 200+ and adds a separate optimization model for premium picks inside the Top 100.

## Top 100 Pick Optimizer
The existing `ADP <100` band is now a dedicated **Top 100 · Pick Optimizer** rather than a normal sleeper list.

For every league-eligible Top-100 player it calculates:
- exact eligible-pool Sleeper overall market rank;
- FIE overall policy rank and raw league rank;
- overall rank divergence;
- M5 preseason policy score;
- roster-fit signal when a live draft/roster is available;
- historical position-level evidence confidence;
- expected same-position replacement if the player is passed;
- replacement-quality drop and **Tier Drop Risk**;
- opponent-adjusted survival to the following own pick when live draft history exists;
- **Value Capture %**, estimating how much of the FIE-to-market discount has already been captured at the planned pick;
- **Reach Cost**, penalizing taking a likely survivor well ahead of market;
- expected **Wait Cost** in FIE policy-score points;
- a labelled **3-pick path proxy** comparing “take now” against “take the best current alternative and try to recover this player later”;
- opportunity labels: Market Value, Structural, Format, Roster, Tier and Wait Value;
- final action: `TAKE NOW`, `TARGET`, `WAIT`, `CONSIDER`, or `PASS AT ADP`.

## Planning mode
If no active Sleeper draft is available, Top-100 mode exposes manual inputs for:
- planning pick;
- following own pick;
- third own pick.

When an active Sleeper draft exists, these are automatically replaced by the live draft sequence.

## Draft Assistant integration
The existing Value Finder / Target Plan columns now support all three market zones:
- **TOP100**: FIE overall rank, market rank, tier risk, value capture, survival and path delta;
- **VALUE**: ADP 100–200 sleeper signal;
- **DEEP**: ADP 200+ snap-path-first signal.

The original Draft Assistant recommendation engine remains visible and unchanged. The optimizer is an additional timing/market layer.

## Interpretation safeguards
- Top-100 optimization is not a claim that the draft has been fully solved stochastically.
- The 3-pick path result is explicitly labelled a planning proxy.
- M6 governance remains unchanged and is not force-enabled.
- Genesis and other hard cohort restrictions continue to use the same legal player universe before market ranks are calculated.
- Roster-level cohort caps remain acquisition constraints, not global exclusions.

## Tests added
- Static integrity checks for Top-100 optimizer wiring and economics.
- Runtime test for eligible-pool ranking, Value Capture, tier replacement, wait cost, survival and path proxy.
- Full existing V8.9/VF1 regression suite continues to pass.
