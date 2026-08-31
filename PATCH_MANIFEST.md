# FIE M9.1 Self-Rehydrating Hotfix — 2026-08-31

## Root cause of run #2 failure

The previous workflow successfully rebuilt `player_week.csv.gz` (124,022 rows), but
then attempted to rerun M9. Canonical M9 training depends on additional ignored M4
OOS cache artifacts such as `milestone4_oos_predictions.csv.gz`, so that was the wrong
rehydration strategy.

## Correct architecture

M9.1 now does **not rerun M9**.

The committed `milestone9.json` already contains the trained preseason specifications
(coefficients, scaler, imputer medians, target/feature contract). The missing artifact
is only the deterministic latest completed-season player profile table.

The M9.1 builder now:
1. uses the existing M9 profile table if present;
2. otherwise reconstructs it from canonical rehydrated `player_week.csv.gz`;
3. uses the committed M9 target/feature contract to select exactly the inputs M9.1 needs;
4. never refits M9 and never requires M4/M7/M8 OOS cache files.

Metadata explicitly records:
- `profile_source`
- `profile_rehydration_refit = false`

## Replace

Replace these three existing files:
- `research/build_m91_season_challenger.py`
- `research/validate_m91_season_challenger.py`
- `research/integrity_m91_transition_test.py`
- `.github/workflows/build-fie-m91-challenger.yml`

Then start a new M9.1 workflow run.

No production output is written or promoted.
