# V9.7.3 Preseason Head-to-Head and Calibration Gate

## Purpose

V9.7.3 is a research-only validation layer between the V9.7.2 component-first preseason challenger and any future Draft-app promotion.

It answers four separate questions for QB/RB/WR/TE:

1. Does V9.7.2 beat the existing M9 preseason **football model** on the same historical players and seasons?
2. Does it improve absolute PPG error and full-schedule-normalized season point error?
3. Does it preserve or improve rank quality, Top-12 identification, and calibration bias?
4. Can a preseason expected-games model improve expected season-point calibration versus blindly assigning the full NFL schedule?

## Historical comparison

The comparison is chronological and paired by player:

- latest four common target seasons
- training uses only seasons earlier than each test season
- V9.7.2 and M9 are scored with the exact current league scoring contract where supported
- only common player-season holdouts are compared
- ADP and current Sleeper season projections are forbidden inputs

The primary error gate uses FIE's existing temporal-block promotion guardrail:

- at least four chronological folds
- mean MAE improvement of at least 1%
- at least the required share of positive folds
- positive temporal-block bootstrap CI

## Ranking and calibration non-inferiority

A football-model promotion review additionally requires:

- V9.7.2 itself is already a `validated_candidate`
- exact V9.7.2 scoring replay in every comparison fold
- robust PPG MAE improvement versus M9
- robust full-schedule-normalized season MAE improvement versus M9
- rank MAE no more than 1% worse than M9
- Spearman no more than 0.01 worse than M9
- Top-12 overlap no more than 0.02 worse than M9
- absolute PPG calibration bias no more than 0.10 points worse than M9

These tolerances are non-inferiority margins, not score bonuses or hidden weights.

## Expected-games model

V9.7.3 also fits a chronological preseason games-availability model using only information knowable before the target season:

- prior-season games
- age when available
- years of experience when available
- known NFL regular-season schedule length

The same predicted-games value is applied to both V9.7.2 and M9, so availability cannot unfairly favor either football model.

`expected_season_points_ready` requires both the football-model gate and an additional expected-season/availability gate. A football model can therefore be promotion-review-ready while its availability-adjusted season total remains research-only.

## Historical MARKET_FALLBACK limitation

The current M9 board may use `MARKET_FALLBACK` when M9 cannot exactly replay the league scoring contract. V9.7.3 does **not** synthesize historical Sleeper projections to make this benchmark possible.

Until verified immutable historical preseason market snapshots exist, the report records:

`blocked_insufficient_verified_historical_market`

Therefore:

- V9.7.3 may establish a football-model promotion claim.
- It may **not** claim that V9.7.2 historically beat M9's Sleeper market fallback.
- ADP remains outside the football projection.

## New outputs

Under `performance/<season>/strategy/`:

- `preseason_v973_validation.json`
- `preseason_v973_predictions.csv`
- `preseason_v973_calibration.csv`

The existing V9.7.2 strategy projection remains the value-board input in this release. V9.7.3 does not modify M9, V9.6 runtime, canonical projections, or Draft-app production behavior.
