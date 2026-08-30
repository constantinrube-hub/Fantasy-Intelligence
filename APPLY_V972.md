# Apply V9.7.2 Shadow Season Patch

Upload these files at the exact repository paths:

- `.github/workflows/build-fie-strategy-stack-v4.yml`
- `research/preseason_projection_v2.py`
- `research/fie_strategy_stack.py`
- `research/build_fie_strategy_stack.py`
- `research/integrity_fie_strategy_stack_test.py`
- `research/validate_fie_strategy_stack.py`
- `docs/V972_SHADOW_SEASON.md`

Then run **Build FIE Strategy Research Stack V4** with:

- League ID: `1391803939736801280`
- Format: `REDRAFT`
- Season: `2026`
- ADP: `AUTO`
- Current pick: blank
- Next pick: blank

The standalone market/availability workflows do not need to be rerun first.

After V4 succeeds, inspect `season_projection_v972.csv`, `league_value_board.csv`, `actionable_findings.json`, and `strategy_stack.json` before any promotion decision.
