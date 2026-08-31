# Apply V9.7.5

Upload these files at the same repository paths:

- `.github/workflows/build-fie-v975-qb-ensemble.yml`
- `research/preseason_projection_v5.py`
- `research/integrity_v975_preseason_test.py`
- `research/validate_v975_preseason.py`
- `docs/V975_QB_ENSEMBLE_CALIBRATION.md`
- `docs/UNIFIED_PER_LEAGUE_RESEARCH_PIPELINE_PLAN.md`

Then run the new Action:

**Build FIE V9.7.5 QB Ensemble Audit**

Pilot inputs:
- league_id: `1391803939736801280`
- league_format: `REDRAFT`
- season: `2026`

The workflow reuses the committed V9.7.4 exact-comparator artifacts. If they are
missing for another league, it can rebuild V9.7.4 automatically before running V9.7.5.

No strategy stack, market capture, or availability workflow needs to be run first.
