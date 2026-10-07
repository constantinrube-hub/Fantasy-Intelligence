# Weekly operations and recovery

## Production sequence

`Refresh FIE Current Season` remains the scheduled current-state owner. Its
non-cancelling concurrency group serializes refreshes instead of interrupting a
long build. A successful completion on `main` starts `Build FIE Window 1C Weekly
Actions`; completion of that workflow starts `Build FIE Window 1D Optimal
Waiver`. The independent Window 1C/1D clock schedules have been replaced by
completion dependencies. All three workflows retain manual dispatch.

Automatic decision work is due on Tuesday and Wednesday in New York. Each
successful scheduled refresh on those days produces a new checkpoint, up to
four per day under the existing refresh schedule. Other days generate a
`NO_DUE` receipt and a truthful usability `NO_OP`; an explicit manual refresh or
Window 1C recovery propagates through the chain on any day. Seasonal calendar
policy and the repository blackout controller still apply to automatic work.

The jobs check out published `main`, never an upstream pull request branch.
Automatic triggers require a successful, completed upstream run on `main` from
the same repository and an allowed upstream event. Git ancestry is checked.
Window 1D downloads only the named input artifact from the triggering Window
1C run, using read-only Actions access; a generic latest artifact is insufficient.

## Published-input gate

`research/weekly_pipeline_readiness.py` resolves the NFL target from the shared
regular-season schedule contract. It does not select a week from stored
snapshots. An explicit manual season/week remains available for bounded
recovery; downstream automatic work rejects a target that has expired.

Before either producer can run, the guard verifies every intended enabled,
current-refresh league (23 in the current registry), or the explicitly selected
manual league:

- Source and deploy snapshots hydrate successfully for the target season/week.
- Generation timestamps include a timezone, are not in the future, and satisfy
  the default 36-hour freshness limit.
- On automatic refresh-to-actions runs, every league was generated no earlier
  than the triggering refresh's start. A technically green partial refresh
  cannot authorize a full-portfolio decision build using preserved old data.
- Registry, profile, current snapshot, app manifest, and app core retain their
  league-specific profile/scoring bindings.
- Source and deploy metadata agree, app core hashes verify, and the explicit
  target-week realized-stat exclusion guard is present.

The guard hashes source/deploy current manifests, shared player bases, scoring
overlays, profiles, app manifests and cores, plus the registry. Window 1D must
match Window 1C's target, scope and entire input-hash map. A newer refresh during
the chain blocks the follow-up as `BLOCKED_PIPELINE_UPSTREAM_INPUT_CHANGED`,
rather than quietly mixing decision evidence. Unrelated evidence commits that
do not change these inputs can proceed.

A `READY` input receipt is not proof that a recommendation model is eligible.
The existing producer retains format, scoring, identity, exact-lineup,
prospective-cutoff, feature-coverage and model gates. Genuine remaining
recommendation blockers remain visible in its report.

## Provenance and monitoring

The `fie-weekly-inputs` Actions artifact carries the run's verified input
receipt, including typed blocked/no-due observations. Successful decision
builds commit first-written records under:

`data/operations/weekly-pipeline/<season>/week_<week>/<stage>-<run_id>-<attempt>.json`

Records bind input commit, verification time, target identity, schedule hash
where available, league scope, exact input hashes and upstream run identity.
Run attempts have separate identities. Conflicting writes to an existing
record are blocked; these operational receipts do not overwrite immutable
forecast, recommendation or outcome captures.

The `weekly-pipeline` usability adapter distinguishes an input blocker, an
expected no-op, an infrastructure failure, and the producer's real readiness.
`workflow_run` events are included in the rolling usability report. Source
input readiness alone can never classify a missing decision report as usable.

## Release and recovery

1. Apply the code changes on a branch from current `main`.
2. Run `python research/integrity_m10_legal_roster_assignment_test.py`,
   `python research/integrity_weekly_pipeline_readiness_test.py`, the usability
   and seasonal-calendar tests, then
   `python tools/release_build.py --mode personal`.
3. Commit the source changes and the generated release synchronization. Keep
   CI and release gates intact. Merge only after current-main checks pass.
4. Manually dispatch `Refresh FIE Current Season` with blank league/season/week
   inputs for a full current-portfolio refresh. Observe its completion before
   validating the automatic Window 1C then Window 1D chain.
5. Verify target-week source/deploy data, both input receipts and both
   operational reports. For the 7 October 2026 rollout the target is Week 5.

For `BLOCKED_PIPELINE_REFRESH_DID_NOT_PUBLISH_LEAGUE`, inspect the refresh's
per-league build failure and rerun a full refresh. For source/deploy binding
failures, regenerate the governed deploy tree; do not copy another league's
data. For changed-input or expired-target blockers, rerun Window 1C to establish
a new receipt, then allow its Window 1D follow-up. Manual Window 1D can verify
fresh inputs independently when that is the intended recovery, but it cannot
claim Window 1C lineage.

No prospective capture is recreated as if it had existed before kickoff. M9
remains the production champion; this change grants no feature/model promotion
and executes no Sleeper transactions. Weekly report completeness, league
lifecycle formalization and recommendation/action/outcome evaluation remain
separate unfinished P0 work.
