# V9.7.1 + V10.4.1 Hardening

## Purpose

This patch addresses the two issues exposed by the first successful real Strategy Stack run without changing canonical V9.6 weekly projections.

### V9.7.1 exact offensive fumble scoring

The pilot league scores both total fumbles (`fum=-1`) and fumbles lost (`fum_lost=-2`). The existing M1 scoring layer supports `fum_lost` but does not globally map `fum`. V9.7.1 therefore keeps the change isolated to preseason research:

- reconstructs total fumbles from `fumbles` or split `rushing_fumbles`, `receiving_fumbles`, `sack_fumbles`;
- reconstructs fumbles lost from `fumbles_lost` or split `rushing_fumbles_lost`, `receiving_fumbles_lost`, `sack_fumbles_lost`;
- scores the validation target directly from raw next-season components instead of inheriting M1 fantasy points for this challenger;
- audits exact scoring coverage on every chronological fold;
- does not alter M1, M4, V9.5, V9.6, or canonical runtime projections.

A future global M1 `fum` repair should be treated as a separate scoring migration because changing historical fantasy labels requires revalidating the downstream weekly stack.

### V10.4.1 draft/action relevance

The original rank-edge consumer could classify extremely deep below-replacement players as TARGET because they were ranked less poorly by FIE than by the market. V10.4.1 adds a fail-closed relevance boundary:

1. player must match the hydrated current player catalog by canonical or Sleeper ID;
2. player must be active, team-assigned, offensive QB/RB/WR/TE, and have a valid full name;
3. league draft horizon = teams × roster slots;
4. watchlist horizon = 1.5 × draft horizon;
5. FIE and market positional ranks are recalculated only inside the relevant watchlist universe;
6. `TARGET` requires non-negative league-specific VORP;
7. `FADE` requires market ADP inside the actual draft horizon;
8. deep positive-VORP discrepancies outside the watchlist become `DEEP_MARKET_OUTLIER`, research-only;
9. relative positive edges below replacement become `MARKET_UNDERRATED`, not TARGET.

For the 12-team, 15-slot pilot league this produces a 180-pick draft horizon and a 270-pick watchlist horizon.

## Governance

- ADP remains outside football prediction.
- New preseason specs remain research-only even if they validate.
- `production_activation_allowed` remains false.
- canonical V9.6 weekly projections are untouched.
- historical ADP research remains blocked until verified history exists.
