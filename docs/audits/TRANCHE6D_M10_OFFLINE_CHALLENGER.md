# Tranche 6D — Offline M10 Offensive Challenger

## Boundary

M10 is an offline research challenger for QB/RB/WR/TE. M9 remains the production champion. This tranche has no app, runtime, ranking, recommendation, model-resolution, shadow, or production-activation write path.

## Locked experiment

`config/m10-offline-experiment.json` owns the experiment contract. Every candidate uses the same rows and expanding outer folds: 2019–2021 → 2022, through 2019–2024 → 2025. The 2026 season is excluded from selection and evaluation.

M10 training retains every eligible row in each locked historical window. M9 out-of-sample predictions are joined only to the corresponding held-out test fold, producing paired comparison rows without truncating M10's training history.

The ladder contains the M9 champion comparator, a median-imputed standardized Ridge baseline, and a shallow regularized histogram-gradient-boosting challenger. Its two-option hyperparameter search is selected using only the final season inside each outer training window. Ensembles are prohibited in 6D.

Count targets use Poisson loss only when the applicable training window contains positive mass. A sparse all-zero count target deterministically falls back to squared-error loss; this avoids an undefined Poisson fit without looking at validation or test rows. Continuous targets always use squared-error loss.

## Component and evaluation contract

M10 predicts raw position-appropriate outcomes from lagged public-core evidence. Team target/carry budgets and completion/reception identities are reconciled before the existing canonical scorer transforms raw outcomes into league fantasy points. The artifact reports paired MAE, bias, rank correlation, pinball loss at P10/P25/P50/P75/P90, and P10–P90 coverage/width for every position and held-out season.

Availability remains an external governed input because adequate prospective history does not exist. No current endpoint reconstructs prior states. ADP, market price, draft behavior, roster demand, and replacement economics are forbidden football-model inputs.

Tranche 6D does not issue a promotion conclusion. Every artifact is marked `NOT_REVIEWED_TRANCHE_6E_REQUIRED`; cross-model, calibration, subgroup, and decision review belongs exclusively to Sol-governed Tranche 6E.
