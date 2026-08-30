# FIE V9.7.3 Patch Manifest

Build: `V10.4.3-STRATEGY-V973-VALIDATION-1`

## New files

- `research/preseason_projection_v3.py`
- `research/integrity_v973_preseason_test.py`
- `docs/V973_PRESEASON_HEAD_TO_HEAD.md`
- `APPLY_V973.md`

## Replaced files

- `research/build_fie_strategy_stack.py`
- `research/validate_fie_strategy_stack.py`
- `.github/workflows/build-fie-strategy-stack.yml`
- `research/build-fie-strategy-stack.yml`

## New research outputs

- `preseason_v973_validation.json`
- `preseason_v973_predictions.csv`
- `preseason_v973_calibration.csv`

## Governance

- research-only
- no automatic activation
- no runtime modification
- no canonical M9 modification
- no ADP/market input into football models
- no historical market-fallback replacement claim without verified immutable market snapshots
- existing V9.7.2 shadow remains the league-value input until a later explicit promotion step
