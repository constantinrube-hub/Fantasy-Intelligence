# Apply FIE Feature Evidence Hardening

## Upload these new files

### `research/`

- `fie_feature_evidence_hardening.py`
- `validate_feature_evidence_hardening.py`
- `integrity_feature_evidence_hardening_test.py`

### `docs/`

- `FEATURE_EVIDENCE_HARDENING.md`

### Repository root

- `FEATURE_EVIDENCE_HARDENING_RELEASE_NOTES.md`
- `APPLY_FEATURE_EVIDENCE_HARDENING.md`

## Replace this existing file

### `.github/workflows/`

- replace `build-fie-feature-evidence.yml` with the version included in this patch.

Do not rename the workflow file after upload. Its repository path should remain:

`.github/workflows/build-fie-feature-evidence.yml`

## Run

GitHub → Actions → **Build FIE Feature Evidence Research**

For the current 2026 evidence run use:

- `start_season = 2016`
- `end_season = 2025`
- `report_season = 2026`
- the same league ID and league format as before.

The workflow now runs both the original evidence validator and the hardening validator. The hardening validator fails closed if QB/RB/WR/TE do not each have at least four genuine second-stage residual holdouts.

## Expected additional outputs

Under:

`data/research/leagues/<league_id>/performance/2026/evidence/`

look for:

- `consumer_routing.csv`
- `hardening_audit.json`

The existing evidence files are regenerated with fair next-season tests and de-duplicated hypotheses.
