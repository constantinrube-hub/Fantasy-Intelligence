# Window 2A: Trench Evidence + Feature Owner

## Status

`IMPLEMENTED_RESEARCH_ONLY`

Window 2A creates the evidence and ownership layer required before FIE can test offensive-line and defensive-front context. It does not alter M9, canonical player rankings, production projections, waiver decisions, or the app.

## Why this layer exists

FIE already contains public player, team, snap, PFR, NGS, schedule and play-by-play sources, but it did not have one explicit owner for trench context. Adding line/front formulas independently inside QB, RB, WR, TE, D/ST or IDP models would create duplicate definitions and make later audit/research difficult.

`research/window2a_trench_evidence.py` is now the sole Window 2A owner. Window 2B must consume this owner instead of recreating the same rates elsewhere.

## Evidence source

Primary source: nflverse/nflfastR play-by-play.

The owner uses public play-level fields that identify the possession team and defense, week, pass attempts including sacks, sacks, QB hits, rush attempts, EPA and play success. Designed-run evidence additionally excludes QB scrambles and kneels. No proprietary grade is inferred.

The repository's existing `research/fie_research.py` already uses the same nflverse play-by-play release family as an optional reproducibility source. Window 2A therefore extends an existing public-data family rather than introducing an unrelated provider.

## Owned features

### Offensive-line context proxy

Core components:

1. sack rate allowed, lower is better
2. designed-run EPA per attempt, higher is better
3. designed-run success rate, higher is better
4. designed-run stuff rate allowed, lower is better

Optional component:

5. QB-hit rate allowed, lower is better

### Defensive-front context proxy

Core components:

1. sack rate generated, higher is better
2. opponent designed-run EPA per attempt, lower is better
3. opponent designed-run success rate, lower is better
4. stuff rate forced, higher is better

Optional component:

5. QB-hit rate generated, higher is better

Each raw rate is retained. The owner then computes cross-team population z-scores and a transparent equal-weight `research_proxy_v1`. A proxy is emitted only after every core component is available. Missing optional measurements remain missing and simply do not enter the proxy.

These are deliberately labelled **team trench proxies**, not true offensive-line or individual defender grades. Quarterback pocket behaviour, running-back decisions, scheme, game state and opponent quality can all influence them.

## Leakage and point-in-time rules

For target week `W`, Window 2A may consume only regular-season plays where `week < W`.

Therefore:

- target-week realised plays are excluded even if the downloaded season file already contains them
- Week 1 has no current-season prior-week trench evidence and returns `BLOCKED_INSUFFICIENT_PRIOR_WEEK_EVIDENCE`
- public-source failure returns a typed blocker
- insufficient NFL-team coverage returns a typed blocker
- unavailable QB-hit/EPA/success/yards evidence is never replaced with zero
- ready prospective captures are immutable first-write artifacts
- blocked `status.json` is intentionally mutable so a temporary public-data outage can recover without poisoning the canonical evidence path

## Output paths

Prospective:

`data/research/trench/<season>/prospective/week_<WW>/trench-evidence-v1.json`

Operational blocker/readiness state:

`data/research/trench/<season>/prospective/week_<WW>/status.json`

Historical research matrix by season:

`data/research/trench/historical/season_<season>-v1.json`

Historical manifest:

`data/research/trench/historical/manifest.json`

## Historical builder

The `history` command builds chronological team snapshots for completed seasons. Every historical target-week row is constructed only from earlier weeks in that season. This gives Window 2B a leakage-safe feature matrix for actual predictive tests without moving feature engineering into the validation layer.

Example:

```bash
python research/window2a_trench_evidence.py history --seasons 2019-2025
```

## Prospective builder

```bash
python research/window2a_trench_evidence.py prospective --season 2026 --target-week 2
```

If season/week are omitted, the producer resolves them from Sleeper NFL state. Week 1 correctly produces a blocker because there are no 2026 regular-season prior weeks.

## Governance boundary

Window 2A does **not**:

- change the M9 production champion
- activate M10
- alter any league scoring, scarcity or replacement-level contract
- alter canonical player boards
- change current/runtime projections
- use ADP or market data as football-model input
- claim the proxy is causally attributable to an offensive lineman or defender
- claim the proxy improves fantasy prediction
- authorize production integration

Only Window 2B may test incremental predictive value. Existing fail-closed statistical gates remain controlling.

## Window 2B handoff

Window 2B should test the owned component features and proxy chronologically, by fantasy position and use case. The minimum required question is incremental value over the existing FIE baseline, not standalone correlation.

Candidate mappings for validation include:

- QB: pass-protection evidence and opposing pass-rush evidence
- RB: run-block evidence and opposing run-front evidence
- WR/TE: protection/pass-rush context only where incremental evidence survives
- D/ST: opposing pass-protection/run-block context
- IDP EDGE/IDL/LB: opposing protection/run-block context

Any component that does not pass the existing statistical/governance gates remains diagnostic or unused. No threshold may be weakened to force trench integration.
