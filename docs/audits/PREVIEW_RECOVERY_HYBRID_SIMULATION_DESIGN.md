# Preview Recovery: Bounded Chopped + Best Ball Simulation

## Status and scope

This design addresses the served-preview failure observed on commit `a5261997`: the 18-team `CHOPPED_BESTBALL` league loads correctly, but Matchup & Playoffs stalls while plain Chopped completes 450 paths.

The change is limited to the Beta league survival simulation and its counterfactual waiver use. It does not alter M9, M10, governed player projections, League Rank, Decision Rank, scoring contracts, research promotion, or production activation.

## Cause

The current Chopped loop evaluates released players against every surviving roster. For Best Ball, each distinct candidate roster invokes a 260-sample legal-lineup model. A representative 18-team, 450-path diagnostic reached 139,964 distinct roster-model requests, which implies roughly 36 million lineup optimizations. Caching identical pools cannot bound this workload because most hypothetical add combinations are unique.

## Required semantics

1. Initial team strength continues to use the existing 260-sample Best Ball legal-lineup distribution.
2. Every Chopped path still eliminates the configured number of teams each period.
3. Released players still enter a simulated FAAB market, remaining budget still constrains bids, and acquired players still improve later-period team strength.
4. `CHOPPED_BESTBALL` marginal value uses the established common format weights: 50% mean, 22.5% lower-tail and 27.5% ceiling lineup value.
5. Results remain current-strength simulation estimates and the released-player market remains labelled heuristic and uncalibrated.

## Bounded method

Before path simulation, build one marginal-value table over:

- every starting roster; and
- the union of the top three releasable players on every starting roster.

For each roster/player pair, calculate the change in exact legal-lineup objective at the mean, lower-tail and ceiling player values. This requires a fixed number of lineup optimizations determined by team count and released-candidate count. The path loop then uses table lookups rather than rebuilding sampled Best Ball distributions for every hypothetical bid.

When a team actually acquires a player, its sampled starting-roster distribution receives the precomputed marginal shift. Repeated acquisitions at the same position receive a bounded diminishing-return factor so the initial-roster marginal is not applied at full strength indefinitely. This is an explicit approximation inside the already heuristic post-chop market, while the starting-roster distribution remains the existing sampled Best Ball model.

The 450 paths run in cooperative batches. The UI publishes completed-path progress between batches and yields to the browser. A league or week change cancels the job, and a cancelled or stale job cannot publish results.

## Budgets and gates

- Default paths: 450.
- Cooperative batch: at most 25 paths.
- Initial sampled Best Ball model: unchanged at 260 lineup samples per roster.
- Marginal candidate universe: at most three initially releasable players per roster, deduplicated by canonical player ID.
- Live UI must remain responsive between batches and complete the 18-team hybrid preview without browser-control timeout.
- Plain Chopped results retain direct elimination and redistribution behavior.
- Determinism: identical league state, seed and path count produce identical results regardless of batch size.
- Source and `dist` must be synchronized.

## Required validation

1. Structural `CHOPPED_BESTBALL` integrity test remains green.
2. Preview recovery test verifies bounded marginal-table construction, deterministic aggregation, progress and cancellation.
3. Decision-engine integration test remains green.
4. Personal release build and governed release gate run after source closure.
5. Served-browser smoke must show a completed hybrid survival table, responsive navigation, and no cross-league result publication.
