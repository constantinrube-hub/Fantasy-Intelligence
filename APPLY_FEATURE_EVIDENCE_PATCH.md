# Apply FIE Feature Evidence Phases 1–7

This is an **additive patch** for the current `main` architecture. It does not replace M1–M9, `index.html`, or any existing production model/runtime file.

## Add these files at the same repository paths

- `research/fie_feature_evidence.py`
- `research/validate_feature_evidence_bundle.py`
- `research/integrity_feature_evidence_test.py`
- `.github/workflows/build-fie-feature-evidence.yml`
- `docs/FEATURE_EVIDENCE_RESEARCH.md`
- `FEATURE_EVIDENCE_PHASE1_7_RELEASE_NOTES.md`

## Pre-flight

Run locally or let GitHub Actions run:

```bash
python -m py_compile research/fie_feature_evidence.py research/validate_feature_evidence_bundle.py research/integrity_feature_evidence_test.py
python research/integrity_feature_evidence_test.py
```

## Full league run

After the files are on `main`:

1. Open **Actions**.
2. Select **Build FIE Feature Evidence Research**.
3. Click **Run workflow**.
4. Use your Sleeper league ID and the correct league format.
5. For the 2026 preseason research window, keep `start_season=2016`, `end_season=2025`, `report_season=2026` unless source coverage requires a shorter window.
6. Run it.

The workflow reuses the existing M1–M8 performance checkpoint where possible and rebuilds it if unavailable. It then writes the evidence package under:

`data/research/leagues/<league_id>/performance/<report_season>/evidence/`

## Review in this order

1. `FEATURE_EVIDENCE_REPORT.md`
2. `feature_evidence_matrix.csv`
3. `feature_horizon_validation.csv`
4. `regularized_challengers.csv`
5. `conditional_effects.csv`
6. `data_expansion_plan.csv`
7. `feature_evidence.json` for the full fold-level audit trail

## Production safety

- `validated`, `horizon_specific`, or `eligible_for_manual_consumer_integration` are research conclusions only.
- Nothing in this patch auto-activates a feature or challenger in FIE runtime.
- The existing M7/M8/M9 production gates remain untouched.
- A challenger that clears this audit must be integrated separately and revalidated before it may affect rankings/projections.
