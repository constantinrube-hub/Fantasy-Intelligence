# FIE Production Shadow Patch Manifest

New files only. No existing production runtime file is replaced.

- `.github/workflows/build-fie-production-shadow.yml`
- `research/fie_production_shadow.py`
- `research/validate_production_shadow.py`
- `research/integrity_production_shadow_test.py`
- `docs/PRODUCTION_SHADOW_INTEGRATION.md`
- `APPLY_PRODUCTION_SHADOW.md`
- `PRODUCTION_SHADOW_RELEASE_NOTES.md`

The workflow writes generated research outputs only under:

`data/research/leagues/<league_id>/performance/<report_season>/shadow/`
