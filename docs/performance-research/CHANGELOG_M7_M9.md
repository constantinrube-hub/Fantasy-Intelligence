# M7-M9 Implementation Changelog

## Research architecture

- Added M7 position-driver research for QB/RB/WR/TE.
- Added chronological residual validation after canonical M4 OOS projections.
- Added second M7 composite gate to prevent independently validated feature families from double counting correlated mechanisms.
- Added optional point-in-time route and QB coverage/pressure charting adapters.

## Team, trenches, defense, and opponent interaction

- Added M8 public pressure environment, pass rush, coverage disruption, scheme, and run-front context.
- Added explicit pass-rush x coverage synergy to capture the team-level DL/DB ecosystem without claiming individual responsibility.
- Added optional true team OL/DL inputs.
- Added optional player-week OL/DL inputs with snap-weighted unit aggregation and separate weak-link challengers.
- Added optional team coverage charting.
- Added QB x pressure/coverage, RB x run-front, WR/TE x pressure/coverage matchup families.
- Added sequential M7+M8 activation gate. When M7 is active, the exported M8 spec is one jointly validated residual model that replaces the M7-only correction rather than stacking another adjustment.
- Kept individual WR-DB responsibility and blocker-rusher assignments blocked until auditable assignment-level history is supplied.

## Returners and season projections

- Added individual KR/PR attempt, yard, and TD reconstruction from play-by-play returner IDs.
- Added independent weekly returner-role and return-yard gates.
- Added independent prior-season to next-season KR/PR yard and TD gates.
- Added explicit return-scoring bridge. A league that scores returns cannot receive an FIE season projection unless the relevant return targets are validated.
- Added separate year-to-year preseason raw-stat projection instead of multiplying the in-season weekly model over 17 games.
- Added calibrated deterministic P10/P25/P50/P75/P90 season simulations using historical OOS residuals.

## Market comparison and reporting

- Added immutable first-write Sleeper season market capture.
- Added league-aware ADP key selection for 1QB/SF, redraft/dynasty, and PPR variants.
- Added canonical-ID player matching plus a unique exact normalized name+position fallback when Sleeper ID mapping is missing.
- Added fail-closed market fallback. Fallback rows cannot create a fake FIE-vs-Sleeper rank edge.
- Added full requested Top 24 QB/TE and Top 36 RB/WR report tables.
- Added sleeper candidate tables outside those cutoffs.
- Added model-driver attribution, confidence, scoring coverage, and projection-source fields.

## CI and deployment

- Added `Build FIE Performance Research M7-M9` workflow.
- The workflow rebuilds the uncommitted M1-M6 derived backbone on the same runner, reapplies current D/ST and kicker augmentations, then builds M7-M9.
- Added deterministic M7-M9 integrity suite and fixture bundle validators.
- Added optional premium-source schema documentation and operator runbook.

## Safety / integrity invariants covered by tests

- forward labels cannot cross season boundaries,
- realised Week N premium data cannot predict Week N,
- duplicate point-in-time source rows fail closed,
- player trench unit aggregation preserves workload weights and weak-link features separately,
- M8 uses a single sequential replacement spec rather than additive M7+M8 stacking,
- return-season transitions align season N features only with season N+1 outcomes,
- return scoring cannot bypass an unvalidated return model,
- market fallback cannot masquerade as a FIE ranking disagreement,
- season simulation is deterministic for a fixed seed and quantiles remain monotonic.
