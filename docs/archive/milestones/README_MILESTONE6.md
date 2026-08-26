# V8.8-M6 — Final Production Milestone

V8.8-M6 completes Steps 28–30 of the Fantasy Intelligence Engine position-production roadmap.

## What this milestone adds

- Advanced second-wave research with explicit validation or blocked-source status.
- Automated current-season pregame feature/projection snapshots.
- Immutable Sleeper market snapshots for honest future benchmarking.
- Permanent fail-closed runtime governance.
- Code-free `CONTROL` rollback to the frozen V8.2.2 decision path.
- Versioned model lineage and artifact hashes.

## Key files

- `index.html` — deployable V8.8-M6 app.
- `research/fie_m6.py` — Step 28 research + Step 29/30 contracts.
- `research/build_current_snapshot.py` — Step 29 current-season builder.
- `research/fie_governance.py` — Step 30 promotion/rollback builder.
- `.github/workflows/build-fie-research.yml` — manual empirical M1–M6 rebuild.
- `.github/workflows/build-fie-current.yml` — manual/scheduled current-season refresh.
- `data/research/governance/operator_override.json` — AUTO/CONTROL operator state.
- `data/research/governance/active_release.json` — generated runtime manifest.
- `DEPLOYMENT_GUIDE_V8_8_M6.md` — complete deployment and operating guide.

## Fail-closed default

The distributed placeholder bundles do not contain fabricated NFL findings. Until the empirical research workflow and current-season workflow successfully run, governance keeps the app on the V8.2.2 fallback path.

## Scoring-profile behavior

The empirical research stack is generated against one Sleeper scoring profile at a time. If the loaded league does not match that research scoring signature, research-driven current overrides remain disabled and the app safely uses its legacy league-specific logic.
