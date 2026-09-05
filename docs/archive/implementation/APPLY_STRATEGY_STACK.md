# Apply FIE Strategy Stack

Upload the patch using the included repository paths.

## Add

- `research/preseason_projection_v2.py`
- `research/fie_strategy_stack.py`
- `research/build_fie_strategy_stack.py`
- `research/validate_fie_strategy_stack.py`
- `research/integrity_fie_strategy_stack_test.py`
- `research/capture_fie_availability.py`
- `research/verified_market_index.example.json`
- `.github/workflows/build-fie-strategy-stack.yml`
- `.github/workflows/capture-fie-season-market.yml`
- `.github/workflows/capture-fie-availability.yml`
- `docs/STRATEGY_STACK_V97_V104.md`

No existing production file needs replacement in this release.

## Preflight hardening included

- Broad research-cache restores are overlaid with the checked-out committed league state afterwards, so an old cache cannot silently replace newer V9.6/current/runtime/evidence files.
- Current M5 snapshots are hydrated through the existing `current_snapshot_storage.py` split-storage contract before injury or V9.6 action consumers read players.
- ADP key defaults to `AUTO`, deriving redraft/dynasty, reception format and Superflex/2QB market choice from the existing league profile. Explicit overrides remain possible and are disclosed in provenance.
- `strategy_stack.json` records upstream SHA-256 hashes, source commit, resolved ADP market and per-phase readiness/blockers.
- A compact immutable daily Sleeper availability archive is included for prospective injury/opportunity research.

## Run order

1. Run **Capture Daily FIE Season Market** once for 2026. It then captures prospectively each day during the draft-market window.
2. Run **Capture Daily FIE Availability Evidence** once. It then continues daily automatically.
3. Run **Build FIE Strategy Research Stack** for league `1391803939736801280`, format `REDRAFT`, season `2026`, ADP key `AUTO`.
4. Leave current/next pick blank for the first research run.
5. After success, inspect `strategy_stack.json`, `preseason_v2.json`, `league_value_board.csv` and `actionable_findings.json` before any promotion work.

The strategy workflow itself also attempts today's availability capture on a best-effort basis, so a transient Sleeper availability failure cannot block the modelling run.

The workflow may reuse the existing M7-M9 cache. If the compatible cache is unavailable, it rebuilds through the existing `build_performance_research.py` path instead of creating a duplicate historical pipeline.
