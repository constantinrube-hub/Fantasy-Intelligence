# FIE V9.6 Controlled Runtime Integration

V9.6 is the controlled promotion layer downstream of hardened feature evidence and V9.5 production-shadow revalidation.

## What can change the main weekly projection

Only consumers validated directly against canonical FIE may replace the main weekly decision projection:

- QB HistGradientBoosting residual challenger
- RB HistGradientBoosting residual challenger

The existing M4/M5 weekly activation flag remains mandatory. V9.6 cannot rescue or bypass a canonical position/player gate.

The RB backfield-competitor Ridge remains a diagnostic alternate. It is never summed with HistGB and does not change the live decision projection.

## What becomes runtime-visible without replacing canonical consumers

Validated component consumers are published under the league-level `v96_runtime.players` overlay:

- QB pass volume
- QB rush volume
- RB carry volume
- RB target volume
- WR target volume
- TE target volume

Validated horizon consumers are published in the same league-level overlay with stable runtime-field names:

- `v96_next_week_projection`
- `v96_next3_projection`
- `v96_ros_projection`
- `v96_floor_probability`
- `v96_ceiling_probability`
- `v96_breakout_probability`

These do **not** overwrite canonical M5 waiver/risk fields in V9.6. They were validated for their own horizons, not as head-to-head replacements for every existing FIE consumer.

## Fail-closed rules

V9.6 requires all of the following before loading a runtime model package:

- exact league ID
- exact report/current season
- exact structural profile fingerprint
- exact scoring signature
- SHA-256 match for the serialized model package
- current snapshot research compatibility
- current structural profile match
- regular season
- current-season completed-game features
- at least two completed games / existing canonical player activation for live offensive application

There is no prior-season live fallback and no next-season activation.

## Multi-league rollout

A league without `performance/<season>/runtime/v96_runtime.json` remains on canonical FIE. This permits gradual league-by-league promotion without changing the rest of the portfolio.
