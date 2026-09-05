# Apply V9.7.3

Replace/add these files at the same repository paths:

- `research/preseason_projection_v3.py` (new)
- `research/integrity_v973_preseason_test.py` (new)
- `research/build_fie_strategy_stack.py`
- `research/validate_fie_strategy_stack.py`
- `.github/workflows/build-fie-strategy-stack.yml`
- `research/build-fie-strategy-stack.yml`
- `docs/V973_PRESEASON_HEAD_TO_HEAD.md` (new)

Then run only **Build FIE Strategy Research Stack** with the same pilot inputs used for V9.7.2:

- League ID: `1391803939736801280`
- Format: `REDRAFT`
- Season: `2026`
- ADP key: `AUTO`
- Current pick: blank
- Next pick: blank

Do not rerun the standalone market or availability capture workflows unless you specifically want a newer prospective snapshot. The strategy workflow still performs its own first-write/best-effort captures.

Expected new strategy outputs:

- `preseason_v973_validation.json`
- `preseason_v973_predictions.csv`
- `preseason_v973_calibration.csv`

V9.7.3 remains research-only even if one or more positions pass.
