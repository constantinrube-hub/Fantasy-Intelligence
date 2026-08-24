# Fantasy Intelligence Engine V8.8-M6 — Milestone 6 Changelog

## Scope

Milestone 6 completes roadmap Steps 28–30 on top of V8.7-M5. It adds second-wave research, a production current-season pipeline, and permanent promotion/rollback governance without modifying the frozen V8.2.2 live scoring functions.

## Step 28 — Advanced second-wave research

### Opponent-role context
- Adds time-safe opponent fantasy allowance priors by model position.
- Uses shifted rolling windows, so the target game never contributes to its own matchup feature.
- Tests the signal only as an incremental residual correction on top of M4 out-of-sample FIE projections.
- Requires at least 1% mean MAE improvement plus robust positive chronological folds to become `validated_candidate`.
- Remains diagnostic in M6. It is not automatically promoted to live scoring.

### Position-specific interaction hypotheses
- QB: time-to-throw × pressure, CPOE × pressure.
- RB: defenders-in-box × RYOE, carry share × RYOE.
- WR/TE: target share × intended-air-yard share, target share × target-conditioned separation.
- EDGE/IDL: defensive snap share × team pressure context.
- LB/S/CB: defensive snap share × man-coverage context.
- Each interaction is evaluated incrementally against the M4 projection using the same expanding-window holdouts.

### Player archetypes
- Adds descriptive KMeans archetypes where sufficient feature coverage exists.
- Archetypes are `descriptive_only`; clustering itself is never treated as causal evidence or a live projection feature.

### Explicitly blocked second-wave analyses
The bundle records why the following are not implemented as validated signals:
- coordinator tendency portability: no trustworthy versioned historical coordinator/scheme assignment source across the full window;
- offensive-line unit quality: no consistent free comparable OL-unit history across 2019–2025;
- stadium/stat-crew tackle bias: venue is insufficient without an auditable official/scorer identifier;
- all-route alignment/separation: public participation does not provide every eligible receiver's route/alignment/separation on every route;
- individual double-team rate: no consistent free league-wide historical series is bundled.

## Step 29 — Current-season automation

### New builder
`research/build_current_snapshot.py`

The builder:
- resolves the current NFL season/week from Sleeper unless manually overridden;
- loads current nflverse player/team weekly stats, snaps and available advanced context;
- drops every observed row from the target week before feature generation;
- reconstructs the exact pregame feature names required by M4 model specifications;
- predicts raw football statistics using the exported M4 Ridge specifications;
- converts predicted raw stats through the empirically matched league scoring profile;
- applies a validated historical FIE/Sleeper blend only when M4 supports it;
- applies M5 risk bands and waiver models only when their own position gates pass;
- requires at least two completed prior games and >=45% observed feature coverage for FIE activation eligibility;
- surfaces feature coverage and confidence for every current player;
- writes `data/research/current/milestone5_current.json`.

### Immutable Sleeper market snapshots
- The current builder captures the Sleeper weekly projection feed before first kickoff where possible.
- Snapshots are first-write immutable by default and stored under `data/research/market/sleeper/{season}/week_XX.jsonl.gz`.
- M4 can later use only genuinely pregame-eligible observations for direct FIE-vs-Sleeper and blend validation.

### Scheduled workflow
`.github/workflows/build-fie-current.yml`

- Manual dispatch is supported.
- Default schedule: four refreshes per day during January, February and August–December.
- The workflow validates M4/M5/M6 before building current intelligence.
- It commits the current snapshot, immutable Sleeper archive and governance manifest back to GitHub.

## Step 30 — Permanent governance, promotion and rollback

### Governance builder
`research/fie_governance.py`

AUTO runtime promotion requires every check to pass:
- operator mode is AUTO;
- M4, M5 and M6 empirical bundles are complete;
- current snapshot is complete/ready/active;
- current snapshot producer is V8.8-M6;
- current snapshot retains the V8.7-M5 browser contract;
- research/current scoring signatures match;
- current snapshot is no older than its configured 18-hour limit;
- target-week realized stats are explicitly excluded;
- at least one current player is activation-eligible.

Failure of any check automatically returns to the frozen V8.2.2 decision path.

### Code-free model rollback
`data/research/governance/operator_override.json`

- `AUTO`: normal promotion checks.
- `CONTROL`: hard-disable all M5/M6 research-driven overrides.
- CONTROL requires no JavaScript/model code modification.
- Re-enabling AUTO re-runs the same evidence/freshness/compatibility gates.

### Audit lineage
The active manifest records:
- research/model build versions;
- primary/extended research windows;
- chronological holdout folds;
- validated position lists;
- decision gates;
- SHA-256 hashes for M4, M5, M6 and the current snapshot;
- explicit fallback build and rollback rule.

Detailed feature lists, coefficients, sample sizes and holdout metrics remain versioned in their originating M4/M5/M6 research bundles.

## Browser integration

New Lab tab: **M6 Production**.

It displays:
- AUTO vs CONTROL mode;
- runtime enabled/fallback state;
- current snapshot season/week/age/eligible players;
- every Step 30 governance check;
- Step 28 opponent-role results;
- Step 28 interaction results;
- descriptive archetypes;
- blocked advanced analyses;
- Step 29 automation contract;
- code-free rollback guidance.

M5 current-model compatibility now additionally requires the M6 governance global permission and matching current season/week.

## Deployment behavior

- The shipped package remains fail-closed because empirical M1–M6 research and a fresh current-season snapshot have not been generated inside this build environment.
- Once GitHub Actions creates valid empirical artifacts, the app can promote only the individually validated M5 decision gates.
- Loading a league whose scoring does not match the active empirical scoring signature causes a safe fallback instead of cross-scoring the wrong research model.
