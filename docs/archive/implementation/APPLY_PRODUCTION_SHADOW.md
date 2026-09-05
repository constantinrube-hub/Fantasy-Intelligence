# Apply FIE Production Shadow

Upload these files using the exact repository paths:

- `research/fie_production_shadow.py`
- `research/validate_production_shadow.py`
- `research/integrity_production_shadow_test.py`
- `docs/PRODUCTION_SHADOW_INTEGRATION.md`
- `.github/workflows/build-fie-production-shadow.yml`
- `PRODUCTION_SHADOW_RELEASE_NOTES.md`

Then run **Build FIE Production Shadow** with the same league used for the hardened evidence run.

Recommended inputs for the current research league:

- league_id: `1391803939736801280`
- report_season: `2026`
- start_season: `2016`
- end_season: `2025`
- league_format: `REDRAFT`

A successful workflow can legitimately report `blocked_no_current_season_completed_features` for the live-player scoring section before regular-season player-week data exists. That does not invalidate the historical shadow consumer revalidation.
