# FIE M9.1 Distribution-Anchored + Transition-Aware Challenger

## Revision

This supersedes the earlier `FIE-M9.1-Transition-Aware-Challenger-2026-08-31.zip`.

### Calibration correction

M9.1 does **not** use an uncalibrated raw FIE season total as the final challenger.
That would be unsafe if FIE has a systematic position-level point bias.

It also does **not** retain M9's single position-wide mean offset.

Instead current-year M9.1 uses a **position empirical quantile anchor**:

1. Sleeper is the fixed current-year baseline distribution.
2. Raw FIE exact-replay projections supply the football ordering signal.
3. Stable-team exact-replay players are preferred to estimate each position's mapping.
4. The raw FIE empirical percentile is mapped to the corresponding Sleeper empirical percentile.
5. This calibrates level, dispersion and shape, while preserving the FIE ranking signal.
6. If the reference sample is insufficient, M9.1 remains at Sleeper.
7. Once 4+ completed point-in-time Sleeper preseason seasons exist, the intended
   `Actual - Sleeper preseason projection` residual model can be trained chronologically
   and may replace this market-neutral research anchor.

This avoids both failure modes:
- one blunt mean shift;
- trusting an uncalibrated raw FIE level.

## Team transitions

`TEAM_CHANGE` is no longer a blocking reason for **QB, RB, WR or TE**.

For all four positions:
- portable player history is retained;
- current new-team Sleeper role/team context is preferred;
- prior-season new-team environmental context can replace old-team environment;
- old-team role/context that cannot be defensibly replaced is cleared;
- uncertainty can widen using empirical historical team-change volatility.

A row can still fail closed for a genuine data/scoring reason (missing identity,
missing model/profile, unsupported active scoring component), but never merely because
the player changed NFL teams.

The integrity test now has explicit synthetic transition cases for QB, RB, WR and TE.

## Files

- `research/build_m91_season_challenger.py`
- `research/validate_m91_season_challenger.py`
- `research/integrity_m91_transition_test.py`
- `.github/workflows/build-fie-m91-challenger.yml`

## Pilot

Run:
**Actions -> Build FIE M9.1 Research Challenger**

- league_id: `1391803939736801280`
- season: `2026`
- adp_key: `adp_ppr`

Inspect artifact:
- `m91_season_board.csv`
- `m91_meta.json`
- `m91_focus_summary.json`

No production promotion occurs.
