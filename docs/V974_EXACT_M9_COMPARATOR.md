# V9.7.4 Exact M9 Comparator Audit

## Purpose
V9.7.3 found a promising QB challenger result, but the historical M9 comparator
did not replay the league's separate total-fumble (`fum`) scoring key exactly.

V9.7.4 answers only this question:

> Does the V9.7.2 challenger still beat M9 when the M9 historical comparator is
> given the same exact fumble-scoring reconstruction?

## Comparator-only change
Inside the audit process only:
- `fumbles` = aggregate total when available, otherwise split rushing + receiving + sack fumbles.
- `fumbles_lost` = aggregate loss total when available, otherwise split rushing + receiving + sack losses.
- M9's audit target catalog receives both fields.
- M9 comparator scoring uses the same isolated `fum` scoring boundary as V9.7.1.

The canonical `preseason_projection.py` file is not modified.

## Gates
V9.7.3 thresholds are unchanged:
- four chronological folds,
- minimum +1% mean MAE improvement,
- positive confidence interval,
- PPG and full-schedule gates,
- ranking/top-12/calibration non-inferiority,
- availability gate for expected-season readiness.

V9.7.4 additionally requires exact M9 comparator scoring in every fold.

## Outputs
Written under `performance/<season>/strategy/`:
- `preseason_v974_validation.json`
- `preseason_v974_predictions.csv`
- `preseason_v974_calibration.csv`

## Promotion semantics
`promotion_review_ready` means evidence is sufficient for a separate promotion
decision. It does not activate or change production automatically.
