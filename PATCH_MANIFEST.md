# Patch Manifest — FIE Unified Per-League Research Pipeline

Base audited: `constantinrube-hub/Fantasy-Intelligence@36f687712b3c2aebc07b1f7bfef456a087cfdfe3`

## Add

### Research pipeline

- `research/fie_research_pipeline_contract.py`
- `research/run_fie_league_research_pipeline.py`
- `research/resolve_fie_position_models.py`
- `research/build_fie_final_league_board.py`
- `research/build_fie_league_research_report.py`
- `research/build_fie_portfolio_research_report.py`
- `research/fie_pilot_equivalence.py`
- `research/publish_fie_research_app_contract.py`

### Validators / integrity

- `research/validate_fie_research_pipeline.py`
- `research/validate_fie_league_report.py`
- `research/validate_fie_portfolio_report.py`
- `research/integrity_fie_research_pipeline_test.py`
- `research/integrity_fie_research_pipeline_league_isolation_test.py`
- `research/integrity_fie_position_model_gate_test.py`
- `research/integrity_fie_final_board_test.py`
- `research/integrity_fie_league_report_test.py`
- `research/integrity_fie_portfolio_report_test.py`
- `research/integrity_fie_app_research_contract_test.js`

### App

- `app/core/research-report-service.js`
- `app/core/research-value-finder-bridge.js`
- `app/research-report-ui.js`

### Workflows

- `.github/workflows/_fie-league-research-reusable.yml`
- `.github/workflows/build-fie-complete-league-research.yml`
- `.github/workflows/build-fie-all-league-research.yml`

### Documentation

- `docs/FIE_UNIFIED_RESEARCH_AUDIT_2026-08-31.md`
- `docs/FIE_UNIFIED_RESEARCH_PIPELINE.md`

## Replace existing

- `research/build_app_manifest.py`
- `tools/sync_league_app_snapshots.py`

These replacements are based on the audited live versions and add only unified research components/dist syncing while retaining existing responsibilities.

## Do not delete yet

Do not delete/deprecate the existing specialized V9.7 workflows until two successful portfolio runs establish equivalence.
