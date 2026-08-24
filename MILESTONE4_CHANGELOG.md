# Fantasy Intelligence Engine V8.6-M4 Changelog

## Scope

Milestone 4 implements roadmap Steps 19–23 on top of V8.5-M3. The V8.2.2 decision model remains the frozen live control.

## Step 19: Position Production Lab

- Added one feature-governance registry across QB, RB, WR, TE, EDGE, IDL, LB, S and CB.
- Registry joins M1 stability/predictiveness evidence, M2 regression/role/competition evidence and M3 advanced-position evidence.
- Separates `graduation_status` from `live_status` so a validated candidate is not automatically activated.
- Added sample size, feature family and classification to the app-facing research bundle.

## Step 20: Activation lock

- Added a bundle-level activation lock with zero live overrides.
- Every feature-registry row must remain `live_status=OFF`.
- Every trained position model spec remains `live_status=OFF`.
- Every learned blend remains `live_status=OFF`.
- Validator fails if a research feature/model/blend is accidentally activated.

## Step 21: Final position-specific forward models

- Added position-specific raw-stat model stacks instead of directly fitting one opaque fantasy-point target.
- Models predict passing, rushing, receiving and IDP stat components appropriate to each position.
- Exact M1 league scoring is applied after raw-stat prediction.
- Uses only pregame/lagged feature families.
- M2 `opportunity_change_score` is shifted one full game before same-week use, because the M2 research score itself includes the just-completed game's opportunity.
- Produces 2022–2025 expanding-window MAE/RMSE/rank-correlation validation.
- Exports transparent Ridge model specifications: feature names, imputation medians, scaler means/scales, coefficients and intercepts for later controlled integration.

## Step 22: FIE versus Sleeper benchmark

- Added an immutable Sleeper projection archive reader.
- Added `capture_sleeper_snapshot.py` for first-write prospective weekly snapshots.
- Only rows explicitly marked `pregame_eligible=true` are accepted into the direct benchmark.
- Retrospective calls to historical Sleeper projection endpoints are not accepted as proof of the projection that existed before kickoff.
- Real M4 therefore reports a blocked Step 22 state until enough verified snapshots exist, rather than fabricating historical Sleeper accuracy.

## Step 23: Position-specific FIE/Sleeper blend

- Added a 0.00–1.00 FIE weight grid by position.
- The weight evaluated in season Y is learned only from earlier completed holdout seasons.
- Reports blend MAE versus FIE alone and Sleeper alone.
- Produces a next-period candidate weight only when enough prior evidence exists.
- Blend remains OFF even when it qualifies as a validated candidate.

## Application UI

- Added `Lab → M4 Research`.
- Shows governance registry, activation lock, final position-model validation, Sleeper benchmark state and blend results.
- Blocked empirical states are surfaced explicitly.

## Deployment

Deployment instructions remain deferred until the roadmap is complete, per user instruction.
