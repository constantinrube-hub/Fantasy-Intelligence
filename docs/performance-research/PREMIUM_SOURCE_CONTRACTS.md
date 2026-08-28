# Optional M7-M9 Premium Source Contracts

The public M7-M9 build requires no paid data. These schemas exist so point-in-time charting can be added without changing model semantics or relabelling public proxies.

All source rows describe realised Week N information. FIE automatically lags them before use. Do not pre-shift them yourself.

## Team trench source

Required keys:

`season, week, team`

At least one supported metric:

`ol_pass_block_win_rate, ol_pressure_allowed_rate, ol_quick_pressure_allowed_rate, ol_time_to_pressure_allowed, ol_run_block_win_rate, ol_yards_before_contact_over_expected, dl_pass_rush_win_rate, dl_pressure_rate, dl_quick_pressure_rate, dl_time_to_pressure, dl_run_stop_win_rate`

There must be at most one row per season/week/team.

## Player OL/DL source

Required keys:

`season, week, team, player_id`

Optional role/workload:

`position_group, pass_block_snaps, run_block_snaps, pass_rush_snaps`

Supported player metrics:

`ol_pass_block_win_rate, ol_pressure_allowed_rate, ol_quick_pressure_allowed_rate, ol_run_block_win_rate, ol_yards_before_contact_over_expected, dl_pass_rush_win_rate, dl_pressure_rate, dl_quick_pressure_rate, dl_run_stop_win_rate`

There must be at most one row per season/week/team/player_id.

## Team coverage source

Required keys:

`season, week, team`

Supported metrics:

`def_man_rate, def_zone_rate, def_two_high_rate, def_single_high_rate, def_press_rate, def_coverage_success_rate, def_explosive_pass_suppression`

## Route/player charting source

Required keys:

`season, week, team, canonical_player_id`

Supported metrics:

`route_participation, targets_per_route, first_read_share, yards_per_route_run, separation_win_rate, pass_block_rate, inline_rate, slot_rate`

## QB coverage/pressure split source

Required keys:

`season, week, team, canonical_player_id`

Supported metrics:

`qb_epa_vs_man, qb_epa_vs_zone, qb_epa_vs_blitz, qb_epa_vs_two_high, qb_pressure_to_sack`

## Rejection rules

FIE rejects or blocks an optional source when:

- required keys are missing,
- no supported metric exists,
- duplicate point-in-time keys exist,
- rows refer to seasons beyond the historical analysis window,
- there are no usable numeric rows.

The system does not average duplicate unit rows because doing so could silently mix player grades, team grades, or different charting definitions.
