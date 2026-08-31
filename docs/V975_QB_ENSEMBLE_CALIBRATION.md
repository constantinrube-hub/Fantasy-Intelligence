# V9.7.5 QB Chronological Ensemble + Calibration

## Purpose
Test whether a chronological ensemble of the V9.7.2 component-first QB model and
the V9.7.4 exact-scoring M9 comparator is more stable than either model alone.

## Leakage protection
- 2022: fixed 50/50 blend, no calibration.
- 2023+: blend weight is learned only from prior V9.7.4 out-of-fold seasons.
- Calibration is never fit on the outer test season.
- Calibration can activate only after expanding prior-season validation improves
  MAE and does not worsen absolute bias.

## Promotion rules
The existing 4-fold, >=1% mean improvement, positive-CI head-to-head gates remain.
The ensemble must clear PPG and full-schedule gates versus exact M9 and must also
be no worse than the best standalone aggregate PPG/full-schedule model.
Ranking, Spearman, Top-12 and calibration noninferiority are measured against the
stronger standalone result.

Expected-season readiness additionally requires:
- robust expected-season MAE improvement vs exact M9,
- the existing V9.7.4 availability gate,
- no worse aggregate expected-season MAE than either standalone.

No automatic promotion or runtime activation occurs.

## Outputs
- preseason_v975_validation.json
- preseason_v975_predictions.csv
- preseason_v975_params.csv
- preseason_v975_calibration.csv
