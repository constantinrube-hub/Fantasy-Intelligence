# FIE V8.3-M1 Historical Research Pipeline

This directory implements the approved first research milestone, Steps 0–9. It is deliberately separate from the live V8.2.2 ranking model.

## What it does

- Freezes V8.2.2 as the control build and labels all new outputs `diagnostic_only`.
- Downloads/caches nflverse player-week stats, team-week stats, PFR snap counts and primary-window PBP for 2019–2025. PBP is reduced to red-zone/goal-line team volume and player red-zone opportunity shares, not shipped to the browser.
- Can optionally cache the broader 2016–2025 archive: participation, NGS, PFR advanced stats, rosters, depth charts, historical injuries, FTN charting, contracts, draft picks and combine data with `--full-raw-cache`.
- Builds a canonical player identity table anchored on GSIS ID with PFR/Sleeper-compatible mappings where available.
- Re-scores every historical player-week using either a supplied Sleeper scoring JSON, a live Sleeper league ID, or a default PPR profile. Every non-zero scoring key is audited; the replay is labelled exact only when all keys have usable historical mappings.
- Builds team opportunity and public-core player opportunity metrics without relabeling proxy data as true route participation.
- Separates opportunity/participation variables from realized outcomes.
- Calculates week-to-week, rolling-block and year-to-year stability by position.
- Calculates lagged next-week, next-3, rest-of-season and next-season predictiveness.
- Runs expanding-window validation: 2019–21→2022, 2019–22→2023, 2019–23→2024, 2019–24→2025.

## Important route-data guardrail

nflverse participation includes a `route` field for the **primary receiver on the play**, not routes for every eligible receiver. The M1 pipeline therefore keeps `pass_play_participation_proxy` and `true_route_participation` as separate concepts. It never silently converts the former into the latter.

## Run locally

```bash
pip install -r research/requirements.txt
python research/fie_research.py --derived-dir data/research/derived --output data/research/milestone1.json
python research/validate_bundle.py data/research/milestone1.json
```

Exact league scoring:

```bash
python research/fie_research.py --league-id YOUR_SLEEPER_LEAGUE_ID --derived-dir data/research/derived --output data/research/milestone1.json
```

Or use a scoring-settings JSON:

```bash
python research/fie_research.py --scoring-json research/scoring.example.json --output data/research/milestone1.json
```

Offline integrity test, no downloads:

```bash
python research/fie_research.py --fixture --output /tmp/m1_fixture.json
python research/validate_bundle.py /tmp/m1_fixture.json
```

## GitHub Actions

The included `.github/workflows/build-fie-research.yml` can be run manually. It rebuilds the historical backbone and all installed diagnostic milestone bundles in sequence, validates them, and commits the milestone JSON outputs back to the repository.

The workflow is manual-only in M1 so a generic PPR run cannot accidentally overwrite a league-specific bundle. The optional `full_raw_cache` input downloads the broader research archive for source validation/future milestones but does not commit those raw files. Compact derived CSV.gz tables are also reproducible and git-ignored.

## Compact derived tables

With `--derived-dir data/research/derived`, the pipeline writes reproducible compressed tables for `player_week`, `team_week`, `player_identity`, `player_season`, `team_season` and `game_environment`. They are git-ignored because the browser only needs the compact `milestone1.json` diagnostics.

# Milestone 2, Steps 10–15

`fie_m2.py` consumes the compact Milestone 1 derived tables and adds the next diagnostic research layer without changing the live application model.

It implements:

- Step 10: position production decomposition. Team opportunity, player participation and player opportunity share are predicted separately and recombined into expected opportunity counts.
- Step 11: opportunity-based xFP. The xFP model excludes realized efficiency outcomes such as receptions, yards, touchdowns, tackles, sacks and interceptions.
- Step 12: regression testing. Actual fantasy points minus realized-opportunity xFP are tested against subsequent scoring changes.
- Step 13: opportunity-change detection. Recent three-game opportunity is compared with an older five-game baseline, then tested against subsequent three-game production.
- Step 14: teammate competition. Receiving, backfield, tackle and pass-rush competition/support indices are added one family at a time and tested for incremental out-of-sample MAE improvement.
- Step 15: vacated opportunity. Historical redistribution is measured retrospectively. It is explicitly non-activating until a trustworthy pregame availability/injury source is joined.

## Run after Milestone 1

```bash
python research/fie_m2.py \
  --m1-derived-dir data/research/derived \
  --m1-bundle data/research/milestone1.json \
  --derived-dir data/research/derived \
  --output data/research/milestone2.json
python research/validate_m2_bundle.py data/research/milestone2.json
```

Offline integrity test:

```bash
python research/integrity_m2_test.py
python research/fie_m2.py --fixture --output /tmp/m2_fixture.json
python research/validate_m2_bundle.py /tmp/m2_fixture.json
```

The combined manual GitHub workflow now runs Milestones 1, 2 and 3 in sequence so all bundles share the same historical scoring profile and backbone.

# Milestone 3, Steps 16–18

`fie_m3.py` consumes the M1/M2 research tables and adds richer positional context plus young-player role modelling.

It implements:

- Step 16: position-specific models using lagged NGS, PFR advanced and participation context where public coverage exists. Public pass-play presence is never renamed as routes, and team pressure context is never renamed as an individual pressure/pass-rush snap.
- Step 17: retrospective natural experiments for QB changes, major teammate absences and sustained role changes. These are quasi-experimental matched deltas and explicitly do not claim causality.
- Step 18: Y1/Y2 meaningful-role models, with a preseason prior and an after-Week-3 update.

Run after Milestones 1–2:

```bash
python research/fie_m3.py \
  --derived-dir data/research/derived \
  --m1-bundle data/research/milestone1.json \
  --m2-bundle data/research/milestone2.json \
  --cache-dir .cache/fie-research \
  --seasons 2019-2025 \
  --output data/research/milestone3.json
python research/validate_m3_bundle.py data/research/milestone3.json
```

Offline integrity test:

```bash
python research/integrity_m3_test.py
python research/fie_m3.py --fixture --output /tmp/m3_fixture.json
python research/validate_m3_bundle.py /tmp/m3_fixture.json
```

The combined manual GitHub workflow now runs M1 → M2 → M3 in sequence. Deployment instructions remain intentionally deferred until the roadmap is complete.

# Milestone 4, Steps 19–23

`fie_m4.py` converts the M1–M3 evidence into a formal model-governance and market-benchmark layer while keeping the V8.2.2 live model frozen.

It implements:

- Step 19: Position Production Lab. One position/feature registry combines stability, forward predictiveness, incremental model evidence, sample size, graduation status and a separate live status.
- Step 20: activation lock. Every M1–M4 research feature, trained position model and blend weight remains `OFF` in the application.
- Step 21: final position-specific forward models. The model predicts raw football statistics first, then applies the exact M1 Sleeper scoring profile to the predicted stat line. The raw event models use pregame-only inputs. M2's role-change score is shifted a full game before it can enter a same-week forecast.
- Step 22: FIE versus Sleeper benchmark. Direct benchmarking accepts only first-write Sleeper weekly projection snapshots explicitly marked as pregame eligible. Re-querying an old Sleeper endpoint is not treated as an immutable historical forecast.
- Step 23: position-specific blending. For a holdout season, the FIE/Sleeper weight is learned only from earlier completed holdout seasons, never from the season being evaluated.

Run after M1–M3:

```bash
python research/fie_m4.py \
  --derived-dir data/research/derived \
  --m1-bundle data/research/milestone1.json \
  --m2-bundle data/research/milestone2.json \
  --m3-bundle data/research/milestone3.json \
  --sleeper-archive data/research/market/sleeper \
  --output data/research/milestone4.json
python research/validate_m4_bundle.py data/research/milestone4.json
```

Offline integrity test:

```bash
python research/integrity_m4_test.py
python research/fie_m4.py --fixture --output /tmp/m4_fixture.json
python research/validate_m4_bundle.py /tmp/m4_fixture.json
```

## Immutable Sleeper snapshots

`capture_sleeper_snapshot.py` is included for prospective Step 22 evidence. It stores raw weekly Sleeper projection rows in a first-write gzip JSONL archive. M4 ignores snapshots unless `pregame_eligible=true` was explicitly asserted by a capture process that ran before the week's first kickoff.

This is intentionally stricter than querying historical projection URLs after games have been played. Until enough verified pregame snapshots exist, the real Step 22 and Step 23 bundle status stays blocked rather than manufacturing a historical comparison.

The combined manual GitHub research workflow now runs M1 → M2 → M3 → M4. Detailed production deployment instructions remain intentionally deferred until the full roadmap is complete.

# Milestone 5, Steps 24–27

`fie_m5.py` is the first fail-closed decision-policy layer. It consumes M4 out-of-sample projections and the inherited M1–M3 evidence, but still calculates V8.2.2 first in the browser and only changes a specific decision component after that component clears its own gate.

It implements:

- Step 24: Draft season aggregation validation plus a gated Draft production/future-role contract. Sleeper/engine season projection remains the preseason production anchor until a separate preseason season model is validated.
- Step 25: a position-specific next-three-game Waiver model with chronological validation and exported Ridge specifications.
- Step 26: Start/Sit ranking validation plus chronological residual-quantile P10/P90 calibration. Weekly mean and weekly risk have separate activation gates.
- Step 27: transparent Redraft, Dynasty, Redraft + Best Ball, Dynasty + Best Ball and Chopped policies. Best Ball and Chopped use explicitly labelled player-level proxies and position-level robustness gates.

Run after M1–M4:

```bash
python research/fie_m5.py \
  --derived-dir data/research/derived \
  --m1-bundle data/research/milestone1.json \
  --m2-bundle data/research/milestone2.json \
  --m3-bundle data/research/milestone3.json \
  --m4-bundle data/research/milestone4.json \
  --output data/research/milestone5.json
python research/validate_m5_bundle.py data/research/milestone5.json
```

Policy integrity test:

```bash
python research/integrity_m5_test.py
```

The M5 browser additionally expects `data/research/current/milestone5_current.json`. That file ships intentionally inactive. Current-season automated generation belongs to Step 29, so M5 cannot silently promote historical research into a live model before the current-data pipeline exists.

The combined manual workflow now runs M1 → M2 → M3 → M4 → M5. Detailed deployment instructions remain deferred until all roadmap steps are complete.
