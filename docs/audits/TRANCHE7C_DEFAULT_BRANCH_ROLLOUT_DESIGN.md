# Tranche 7C-R — Default-Branch Prospective Rollout Design

## Decision

The user has explicitly authorized the operational rollout that was kept outside the closed audit-branch 7C target. This Sol design authorizes Terra to implement and validate the rollout on `audit-implementation-2026-09`. It does not itself activate a schedule. Activation occurs only when the validated workflow and its frozen 2026 season lock reach the repository default branch.

The rollout remains research-only. M9 remains the production champion. It does not authorize 6F, a shadow namespace, app or runtime integration, canonical-rank changes, recommendations, deployment output, model selection, or promotion.

## Gap found at the rollout boundary

The closed 7C adapter validates and stores a time-safe input bundle, exact scoring replay, paired decision traces, and separate outcomes. It deliberately has no provider client and no forecast producer. Merely scheduling that adapter would either do nothing or require an ungoverned caller to manufacture its three inputs. That is not an operational collection system.

The rollout must add a governed producer in front of the closed adapter. It has two immutable layers:

1. a season lock created before the first evaluated capture from historical sources ending in the prior completed regular season; and
2. a weekly source bundle first-written inside the zero-to-18-hour window before the slate's first kickoff.

The weekly runner loads the season lock. It never trains, tunes, selects, or replaces a candidate. A missing or mismatched lock blocks the capture.

## Operational component graph

The scheduled path is:

`verified schedule + public-core completed-game sources + governed identity + captured rosters/profiles`

`→ frozen season-lock inference for M9, M10-Linear, and M10-HGB`

`→ shared team-budget reconciliation`

`→ immutable raw football forecast ledger`

`→ exact replay across all enabled scoring profiles`

`→ research-only legal-choice decision traces`

`→ separately released, append-only outcomes`

No market projection, ADP, draft behavior, roster demand, replacement value, current app rank, or production recommendation is a football-model input.

## 2026 season lock

### Training boundary

The first rollout lock is for the 2026 regular season. Model fitting may use outcome rows from 2019 through 2025. Source rows from 2016 through 2018 may be used only to construct lagged features for early 2019 targets. No 2026 outcome may enter training, candidate selection, residual calibration, feature selection, imputation, or parameter fitting.

The lock records exact hashes for the training matrix, row identity manifest, source files and releases, feature contract, target contract, dependency lock, scorer, training code, candidate configuration, and every exported model specification. The lock is first-write immutable. A source correction after the lock does not rewrite it; the correction may be considered only for a later season.

### Candidate definitions

Every position uses the same eligible training rows and raw targets.

- `M9` is the frozen research comparator corresponding to the existing M4/M9 weekly raw-stat Ridge stack: median imputation, standardization, Ridge alpha 10, and a zero prediction floor.
- `M10_LINEAR` uses the same prospective feature matrix and targets with median imputation, standardization, Ridge alpha 6, and a zero prediction floor.
- `M10_HGB` uses the locked 6D two-member search space. The final inner comparison trains through 2024 and evaluates 2025; the selected specification is then refit on 2019–2025. Count targets use Poisson only when the eligible training target has positive total, otherwise squared error. Continuous targets use squared error. Random state remains 106.

Target-domain clarification from the first real-source build: count labels must be finite and non-negative, while continuous yardage labels must be finite and preserve legitimate negative observations. Missing labels remain missing rather than becoming zero. The zero prediction floor applies only after inference and never clamps training or evaluation labels. See `TRANCHE7CR7_TARGET_DOMAIN_DECISION.md`.

An ensemble is prohibited. The QB HGB research lead receives no preferential rows, inputs, schedule, or decision treatment.

### Portable parameters

Scheduled inference must not load a Python pickle or refit from mutable upstream data.

Ridge specifications are exported as canonical JSON containing the feature order, imputer medians, scaler means/scales, coefficients, intercept, training count, and floor. HGB specifications are exported to a repository-owned `fie-hgb-tree-v1` JSON representation containing the baseline, ordered boosting iterations, numeric split nodes, missing-value direction, leaves, and learning metadata. Categorical splits are not permitted in the first lock.

The exporter is allowed to inspect the fitted scikit-learn object only during season-lock creation. An independent repository inference function must match scikit-learn on a frozen probe set with maximum absolute error no greater than `1e-10`. Canonical JSON bytes define each parameter hash. The scheduled runner reads only those JSON specifications.

### Prospective feature contract

Features use only raw public-core football evidence known before the target kickoff. Player and team rolling features use the last four completed regular-season games, crossing a season boundary when those games were already complete. Training applies the identical rule. A minimum of two observations is required for a rolling value; missing values remain missing for the locked model imputer.

Player efficiency history may cross a team change. Team-scoped role shares, competition, and team budgets reset at a team change and remain missing until observed with the new team. Team and opponent identifiers are not numeric predictors. In particular, the 6D diagnostic `factorize` code is not an operational categorical encoding.

The first lock excludes ADP, market values, Sleeper fantasy projections, replacement/scarcity, roster demand, draft behavior, current ranks, target-week results, and post-cutoff status. Sleeper may supply schedule state, current roster membership, league rosters, and availability metadata, but its projection values cannot enter any candidate.

### Reconciliation and distributions

All candidates use the same deterministic team opportunity budgets computed from the last four completed team games under the same cross-season rule. Player targets and carries are proportionally reduced only when their candidate totals exceed the corresponding team pass/rush budget. Completions cannot exceed attempts and receptions cannot exceed targets. Reconciliation occurs before scoring.

P10/P25/P50/P75/P90 use candidate-and-position residual distributions frozen from the historical out-of-sample seasons. The point prediction is shifted by the frozen residual quantile and floored at zero. This is a marginal forecast distribution, not independent simulated component truth. Event probabilities remain `null` with a typed `NOT_DEFINED_BY_2026_SEASON_LOCK` blocker unless the season lock contains a separately validated probabilistic definition. Availability probability remains externally governed and is not invented.

## Weekly source bundle

### Time and schedule

The source producer first-writes a raw source envelope before model inference. It verifies the NFL regular-season state, season, week, complete schedule, and first kickoff from the existing schedule source. The bundle records UTC observation time, provider release/revision when exposed, exact payload hashes, schedule hash, and hours before kickoff.

Before the 18-hour window, the workflow exits successfully without an evidence write. Inside the window, incomplete or unavailable sources cause a failed attempt that remains retryable. Once kickoff has passed without a valid forecast, the first later verified attempt writes exactly one operational missed-capture manifest. `WINDOW_NOT_REACHED` is never written as a permanent miss. A forecast and a missed manifest are mutually exclusive.

### Candidate universe and identity

The weekly universe is the intersection shared by all three candidates: scheduled QB/RB/WR/TE players with an unambiguous canonical identity and sufficient feature construction to run every locked candidate. Model-specific row dropping is prohibited. Conditional football production is captured separately from availability; injury status cannot silently zero a forecast.

Identity input is an immutable snapshot of the existing governed crosswalk plus current provider identifiers. Ambiguous or unresolved rows are excluded symmetrically with typed counts. A material coverage failure blocks the whole capture rather than producing a selectively easy slate.

### Profile replay

The profile snapshot must contain every enabled registry league. For the currently frozen portfolio that means exactly 22 leagues across all six formats. Each row includes the league ID, format, full scoring settings, scoring signature, profile fingerprint, source file hash, and captured time. Registry/profile disagreement, missing coverage, or scorer mismatch blocks the capture. There is no default-PPR fallback for league replay.

### Decision traces

Roster and league-state responses are first-written and hashed at the cutoff. All candidates receive the same legal forecast IDs for a given league, roster, and domain.

- Managed-lineup `start_sit` selects the maximum mean-scored legal lineup under the captured roster slots; ties break by canonical player ID.
- `best_ball` stores the same pregame legal lineup optimization under the best-ball profile so later outcomes can measure regret against the realized optimal legal lineup.
- `chopped` selects the legal lineup maximizing the sum of P10 scored values, with P50 then canonical identity as deterministic tie breakers, and stores both mean and downside utility.
- Waiver traces are allowed only when the complete cutoff-time ownership/free-agent pool and the required forward horizon are captured. Otherwise they carry a typed blocker.
- Draft, trade, and multi-season dynasty utility remain `NOT_APPLICABLE` in this weekly path.

These traces are counterfactual research records. They never write to the app or call the production decision service.

## Outcomes and revisions

Outcome collection is a separate scheduled job and namespace. It waits until the target games have completed and the outcome source has an identifiable observed release/payload. Revision 1 contains model-independent raw football outcomes keyed to the frozen forecast IDs. Missing results, postponed games, and identity exclusions are typed and applied symmetrically.

If the source payload later changes, a correction appends revision 2 or higher with a parent-revision hash and source-diff manifest. It never rewrites a forecast or an earlier outcome revision. Every future evaluation declares one revision before reading results.

## Default-branch workflow and write scope

The rollout adds one operational workflow with pregame-capture and outcome-ingestion modes. It uses `workflow_dispatch` and a three-hour schedule during regular-season months. Scheduled writes are permitted only when `github.ref == refs/heads/main`; audit-branch validation uses fixtures and dry-run outputs.

The workflow has `contents: write`, non-cancelling concurrency, fetch/rebase-before-push behavior, and an explicit path allowlist. It may commit only:

- the frozen `data/research/prospective/m10/season-locks/2026` lock;
- immutable weekly forecast/scoring/decision/missed namespaces;
- immutable outcome revisions; and
- their research-only manifests.

It must not stage `app`, `functions`, `dist`, production configuration, ranks, recommendations, or league current snapshots. A no-op run creates no commit. A conflicting first-write loses safely and revalidates the winner after rebase.

## Validation and activation gates

Terra implementation must provide deterministic no-network tests for season-lock export/inference, weekly source eligibility, all-profile replay, decision legal-set parity, missed-capture timing, first-write races, and outcome revisions. The controlled audit target may use networked historical sources to build the proposed 2026 lock, but the target artifact must expose every source and parameter hash.

The implementation target runs focused checks during development and exactly one full personal release gate at target closure. Generated release synchronization remains limited to the established three manifest files. The operational workflow itself does not build or deploy the app.

Default-branch activation requires all of:

1. a green controlled target on `audit-implementation-2026-09`;
2. artifact verification and exact generated synchronization;
3. a validated, first-write 2026 season lock with no 2026 outcomes;
4. fixture proof that the scheduled job cannot write outside the time window or path allowlist;
5. the controlled target returned to manual-only; and
6. merge of the validated rollout to `main`, which is the activation event already authorized by the user.

If activation misses the first valid 2026 window, Week 1 is recorded as missed. It is never reconstructed.

## Ordered Terra implementation

1. Implement the deterministic season-lock builder, portable JSON inference, and lock validator.
2. Implement the time-safe weekly source-envelope and bundle producer, reusing existing schedule, identity, profile, and completed-game owners.
3. Extend the closed 7C storage contract only where needed for operational missed records and monotonic outcome revisions; preserve its fixture semantics.
4. Implement deterministic lineup traces and symmetric eligibility diagnostics.
5. Add the default-branch operational workflow plus an audit-branch controlled target workflow.
6. Run targeted tests, then one release gate in the controlled target.
7. Verify the artifact, close the controlled target, and merge the validated rollout to `main` before evidence accrual begins.

## Review boundary

Tranche 7D is operations, not model review. It accumulates immutable evidence and monitors health. After at least eight completed weeks, a descriptive interim report may be designed, but it cannot select a model or authorize shadow use. Tranche 7E returns to Sol at a declared checkpoint. The four-completed-outer-season promotion gate remains unchanged.
