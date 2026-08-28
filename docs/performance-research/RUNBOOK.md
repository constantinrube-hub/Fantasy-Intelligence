# M7-M9 GitHub Runbook

## First deployment

Upload the additive patch files at their exact repository paths. No existing V9.3.x app/runtime file needs to be replaced.

The new workflow is:

`Build FIE Performance Research M7-M9`

## Recommended first run

Run it for Genesis League with:

- `league_id`: `1316165875291668480`
- `league_format`: `REDRAFT`
- `season`: `2026`
- `full_raw_cache`: `false`
- `build_report`: `true`

The workflow intentionally rebuilds the M1-M6 derived backbone on the same runner because the large player/team/OOS derived tables are not committed to Git. It then reapplies the repository's current D/ST and kicker augmentations, builds M7-M9, freezes the Sleeper season market, and produces the season report.

## Expected outputs

League namespace:

- `data/research/leagues/<league_id>/milestone7.json`
- `data/research/leagues/<league_id>/milestone8.json`
- `data/research/leagues/<league_id>/milestone9.json`

Frozen market:

- `data/research/market/sleeper/2026/season_market_<UTC-date>.jsonl.gz`
- matching `.meta.json`

Report:

- `data/research/leagues/<league_id>/performance/2026/season_board.csv`
- `data/research/leagues/<league_id>/performance/2026/report/Fantasy_Success_Report.md`
- `top_market_universe.csv`
- `sleepers.csv`
- `full_season_board.csv`
- `report_manifest.json`

The same files are uploaded as a GitHub Actions artifact even if the commit/push step later encounters a branch conflict.

## What to inspect after the run

1. In the workflow summary, note which M7 driver families cleared.
2. Note which M8 matchup families cleared.
3. Note which weekly and season-level return targets cleared.
4. Note which QB/RB/WR/TE preseason position specs cleared.
5. Open `Fantasy_Success_Report.md`.
6. Check whether the requested Top 24/36 rows show independent FIE projections or `MARKET_FALLBACK`.
7. Focus first on rows with a non-null `rank_edge`. Those are actual FIE-vs-Sleeper disagreements.
8. Review any `scoring_unsupported` fields. A non-empty field intentionally prevents the row from claiming full FIE eligibility.

## Chopped league second run

After Genesis succeeds, run the same workflow for:

- `league_id`: `1313696967989157888`
- `league_format`: `CHOPPED`
- `season`: `2026`

Because the entire build is League-ID namespaced and the raw football projection is rescored through that exact profile, the two reports can differ without overwriting each other.

## Premium data later

Premium source files are optional. Put a point-in-time file in the repository or another runner-accessible path and pass it to `research/build_performance_research.py` via the relevant source argument. The initial GitHub workflow intentionally leaves these blank so the public-data baseline can be validated first.
