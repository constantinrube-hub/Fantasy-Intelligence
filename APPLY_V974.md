# Apply V9.7.4

Upload these files at the exact repository paths:

- `.github/workflows/build-fie-v974-comparator-audit.yml`
- `research/preseason_projection_v4.py`
- `research/integrity_v974_preseason_test.py`
- `research/validate_v974_preseason.py`
- `docs/V974_EXACT_M9_COMPARATOR.md`

Then run the GitHub Action:

**Build FIE V9.7.4 Exact M9 Comparator Audit**

Inputs for the pilot:
- League ID: `1391803939736801280`
- League format: `REDRAFT`
- Season: `2026`

Do not rerun market or availability workflows. This audit does not consume them.

The successful run should print:
- `PASS integrity_v974_preseason_test exact-M9 comparator`
- `PASS V9.7.4 comparator audit ...`
- `PASS V9.7.4 governance ...`
- `Post-commit worktree status:`

After success, inspect `preseason_v974_validation.json` before promoting anything.
