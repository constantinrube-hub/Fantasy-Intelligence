# FIE Unified Per-League Research Pipeline

Implementation generation: `fie-research-pipeline-v1`

## Architectural invariant

`Football truth → Fantasy value → Market price → Decision`

The same workflow is reusable across leagues. The **model decision is never portfolio-wide**.

League isolation key:

`league_id + profile_fingerprint + scoring_signature + roster_signature + format + season`

ADP remains outside the football model.

## New canonical files

### Per league

`data/research/leagues/<league_id>/performance/<season>/research_pipeline/`

- `readiness.json`
- `final_player_board.csv`
- `board-meta.json`
- `rankings.json`
- `league-report.json`
- `league-report.md`
- `report-summary.json`
- `stage-manifest.json`
- `matrix-job-status.json` when run from Actions
- `stages/*.json`

### Portfolio

`data/research/portfolio/<season>/`

- `research-overview.json`
- `research-overview.md`
- `model-readiness.csv`
- `outlier-consensus.csv`
- `sleeper-consensus.csv`

## Phase implementation map

### Phase 1 — Contract + one-league orchestrator

- `research/fie_research_pipeline_contract.py`
- `research/run_fie_league_research_pipeline.py`
- `research/fie_pilot_equivalence.py`

The runner validates the registry/profile, reuses or builds M1–M9, hydrates current context, captures market/availability, calls the current strategy stack, runs exact V9.7.4 and V9.7.5, then writes stage evidence.

### Phase 2 — Position model resolver

- `research/resolve_fie_position_models.py`

Offensive production remains M9 unless a separate future `governance/research_model_promotion.json` is explicitly approved and matches league/profile/scoring fingerprints.

`PROMOTION_REVIEW_READY` never activates a challenger.

### Phase 3 — Canonical final player board

- `research/build_fie_final_league_board.py`

Offensive canonical values are produced by calling the existing:

`fie_strategy_stack.build_league_value_board(M9 season board, league profile, market evidence, current context)`

The existing V9.7 shadow board is joined only as research challenger evidence.

D/ST and K use existing dedicated current engines with explicit weekly/current scope.

### Phase 4 — Human + compact report

- `research/build_fie_league_research_report.py`

Required output:

- league/scoring overview;
- position model evaluation;
- Top 10 QB;
- Top 20 RB;
- Top 20 WR;
- Top 10 TE;
- Top 10 D/ST when applicable;
- Top 10 K when applicable;
- Top-100 positive outliers;
- Top-100 negative outliers/fades;
- ADP >100 sleepers by QB/RB/WR/TE.

Reason codes are deterministic. CI does not invoke an LLM.

### Phase 5 — Single unified Action

- `.github/workflows/_fie-league-research-reusable.yml`
- `.github/workflows/build-fie-complete-league-research.yml`

The reusable workflow itself is read-only and artifact-producing. The manual single-league wrapper publishes once after validation.

### Phase 6 — App integration

- `research/publish_fie_research_app_contract.py`
- `app/core/research-report-service.js`
- `app/research-report-ui.js`
- `app/core/research-value-finder-bridge.js`
- updated `tools/sync_league_app_snapshots.py`
- updated `research/build_app_manifest.py`

`core.json` gains only compact paths:

```json
{
  "research": {
    "profile": "...",
    "current": "...",
    "governance": "...",
    "readiness": ".../research_pipeline/readiness.json",
    "rankings": ".../research_pipeline/rankings.json",
    "report_summary": ".../research_pipeline/report-summary.json"
  }
}
```

The report service validates every path/payload against the active league and clears cache on league switching.

The Research UI is contextual only.

The Value Finder bridge hides/shows existing canonical rows according to report membership. It never creates a new FIE rank.

### Phase 7 — Registry-driven all-league matrix

- `.github/workflows/build-fie-all-league-research.yml`

Matrix properties:

```yaml
strategy:
  fail-fast: false
  max-parallel: 3
```

Every enabled registry row appears in the matrix. No league ID list is hardcoded.

Matrix jobs do **not** push Git.

### Phase 8 — Portfolio aggregation

- `research/build_fie_portfolio_research_report.py`
- `research/validate_fie_portfolio_report.py`

The portfolio layer is descriptive. It never pools league results to retroactively change an individual league gate.

A current matrix failure overrides any stale old readiness file when calculating portfolio status.

### Phase 9 — Cleanup

Not automatically executed.

Keep the existing specialized V9.7 workflows until at least two complete portfolio runs establish equivalence and operational stability. Then archive/deprecate workflows only, not the underlying Python research modules.

## Integrity and validation

New tests:

- `research/integrity_fie_research_pipeline_test.py`
- `research/integrity_fie_research_pipeline_league_isolation_test.py`
- `research/integrity_fie_position_model_gate_test.py`
- `research/integrity_fie_final_board_test.py`
- `research/integrity_fie_league_report_test.py`
- `research/integrity_fie_portfolio_report_test.py`
- `research/integrity_fie_app_research_contract_test.js`

Validators:

- `research/validate_fie_research_pipeline.py`
- `research/validate_fie_league_report.py`
- `research/validate_fie_portfolio_report.py`

Key assertions include:

- M9 remains selected unless explicit separate governance approves otherwise;
- promotion-review does not activate a challenger;
- ADP is not a football feature;
- final offense value delegates to existing league-value logic;
- same scoring + different roster structures produce different replacement;
- Top-100 rows cannot have ADP >100;
- sleepers cannot have ADP <=100;
- portfolio count reconciles exactly to enabled registry count;
- app research paths cannot cross league namespaces;
- report/Value Finder bridge cannot calculate a replacement rank.

## Actions to run after applying this patch

### 1. Pilot first

GitHub → Actions → **Build Complete FIE League Research**

Recommended inputs:

```text
league_id: 1391803939736801280
season: 2026
league_format: AUTO
adp_key: AUTO
mode: FULL
force_rebuild: false
publish_app: true
```

The workflow automatically captures and validates pilot equivalence.

Do not proceed to portfolio evaluation if pilot equivalence fails.

### 2. Inspect pilot outputs

Review:

- `readiness.json`
- `league-report.md`
- `final_player_board.csv`
- `stage-manifest.json`

Confirm no model was activated by the research workflow.

### 3. Run all enabled leagues

GitHub → Actions → **Build Complete FIE Research — All Leagues**

Recommended:

```text
season: 2026
force_rebuild: false
publish_app: true
```

The workflow continues all matrix cells even if one fails, aggregates all league artifacts and performs one publication.

### 4. Inspect portfolio audit

Review:

- `data/research/portfolio/2026/research-overview.md`
- `model-readiness.csv`
- `outlier-consensus.csv`
- `sleeper-consensus.csv`

A blocked/failed league remains explicit. It is never silently dropped.

### 5. Promotion remains separate

Do not create a promotion artifact merely because a position is `PROMOTION_REVIEW_READY`.

Promotion should remain a distinct governance review after the all-league evidence is understood.
