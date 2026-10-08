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

## Report coverage and league lifecycle

Window 1C reports ready, partial, blocked, unknown and not-applicable counts separately. Partial evidence is not a blocked workflow. Offensive waiver coverage is reported independently from K/D/ST and is based on eligible source rows, not proof of candidate availability or complete position coverage. A successful specialist recommendation does not establish offensive readiness. Model eligibility and recommendation statuses retain their original owners.

Explicit lifecycle declarations live in `config/league-portfolio.json`, scoped to a season and effective week with an evidence source. `ELIMINATED_RESEARCH_ONLY`, `COMPLETED`, `ARCHIVED`, `REFRESH_ONLY` and `RETIRED` suppress operational advice. Missing declarations preserve existing active behavior; malformed declarations block advice. Elimination is never inferred from an empty roster. The Final Cut is research-only from 2026 Week 4 following the user's Week 3 elimination. Window 1D continues to capture its observable bid history and report ledger while skipping the recommendation planner. Current refresh remains enabled. Later seasons require their own explicit lifecycle decision.

## Prospective checkpoint audit

Window 1D appends a read-only checkpoint audit to its Actions summary and first-writes an operational record named `evidence-audit-<run>-<attempt>.json` alongside that invocation's weekly input receipt. Audit states are `NOT_DUE`, `DUE_MISSING`, `MISSED_UNRECORDED`, `MISSED_RECORDED`, `CAPTURED_VALIDATED`, or an explicit blocker. `ON_TRACK` means only the audited checkpoints have no current gap; it does not certify projection coverage or all report products.

The audit reuses an already observed, hash-verified weather schedule envelope for the requested season/week, excludes envelopes captured after its as-of time, and delegates terminal evidence validation to the established M10 and Sunday paired-checkpoint owners. No provider calls occur. Missing evidence after a deadline is reported; the audit cannot recreate a forecast or write an official missed-capture manifest. Only the original capture owner may do that.

Current scope: M10 week-open, Sunday paired M10/Sleeper, PR2 week-open T-7.5 through T-4, and PR2 Sunday-main T-4 through T-2.5. PR2 windows are imported from the capture owner, use New York Sunday-main slate identity, and validate source envelopes, schedule/matchup hashes, captured league scope and observation times. Captures after the audit as-of are excluded. A validated capture is not proof of full-portfolio scope or model eligibility. Daily availability, weather, trench evidence and post-week outcomes still require separate audits. A past missed checkpoint remains missed even after a later refresh succeeds.

Manual inspection (choose a new operational output filename each time):

```powershell
python research/weekly_evidence_audit.py --season 2026 --week 5 --output .cache/weekly-evidence-audit.json
```

## Seven-product report coverage bundle

After Window 1D, the workflow first-writes `report-bundle-<run>-<attempt>.json` under the same operational week directory and appends its coverage table to the Actions summary. The bundle includes existing owner outputs for waiver guidance, start/sit alerts and PR2 exposure when available. It retains source paths, SHA-256 hashes and league scope. Waivers appear Chopped-first without changing the planner's decisions.

Every invocation lists all seven required products: player performance, waiver guide, exposure, start/sit, D/ST hold/stream, kicker hold/stream and post-week review. Included owner outputs are explicitly partial; this adapter does not certify any product as complete. Missing standalone products remain blocked with a next action. A missing D/ST or kicker report is not filled using a waiver watchlist, and a prior-week evaluation is not relabeled as the target week's post-week review. Outcome products naturally remain unavailable before outcomes exist.

Sources with a wrong target, duplicate league IDs, unrecognized schema, future observation/generation time or observation age over 36 hours are excluded with typed reasons. The bundle is read-only and executes no transactions, forecasts or model promotion. It provides a reviewable P0 coverage contract; producing and validating the remaining full products is still unfinished work.

Manual inspection (use a new output filename):

```powershell
python research/weekly_report_bundle.py --season 2026 --week 5 --output .cache/weekly-report-bundle.json
```

## Context, player-performance and current-portfolio artifacts

The checkpoint audit now includes a separate stored-context audit. Availability validates the original capture contract, raw/normalized hashes and coverage, with an explicit 36-hour freshness observation. Weather validates the stored schedule, provider envelopes, per-game provenance and the original hourly normalization; unavailable forecasts remain missing. Trench evidence validates target, prior-week leakage guards, team counts and research authority. Its raw PBP source hash is declared, not replayed by this adapter. A green checkpoint state does not certify weather accuracy, coordinates, complete context coverage or model value.

Window 1D ensures one report for the newest completed week represented by a stored schedule. It reuses the existing PR2 12-hour postgame buffer. The first invocation captures an immutable nflverse retrospective response and generates a team-by-team player-performance JSON and Markdown report under `data/operations/weekly-performance/<season>/week_<week>/`. Later invocations replay the existing report and no-op. Explicit manual revisions use new source/output identities; they never overwrite a prior report. Player IDs absent in the provider response remain unresolved, and snapshots/routes remain unsupported. Provider standard/PPR fantasy points are diagnostics, not exact league scores. Neither elapsed time nor provider rows certify official game finality. These artifacts cannot enter target-week pregame features.

A current `portfolio-surface-<run>-<attempt>.json` plus Markdown binds all weekly input hashes, source commit, observed roster time, forecast time, scoring/profile identities and producer source hash. It includes independent FIE and Sleeper means, deltas, available intervals, component fields and explicit eligibility/missingness. A mean never becomes a median. Existing numeric CSV-ID normalization is reused, with exact live Sleeper-ID rows taking precedence over historical aliases; their forecasts are not merged. A future or stale core blocks that league. Unresolved players remain typed partial coverage.

Active roster/start exposure is computed from those same records. The eliminated Final Cut remains inspectable but is excluded from active exposure. Best Ball starter observations are labelled automatic, not manual instructions. A current core does not identify this week's direct opponent, so opponent exposure remains blocked until captured matchup evidence is present. D/ST and kicker owned/available forecast boards retain independent values and explicit missing hold/stream strategy; existing Window 1D specialist advice can be included unchanged. These partial boards do not certify a validated strategy.

When an immutable PR2 portfolio capture and a current portfolio surface both pass their original hash/time checks, the report bundle joins *captured submitted opponent starter IDs* to that league's canonical player view. It verifies the exact week, profile fingerprint, scoring signature and capture time, and publishes a separate direct H2H player-exposure count with league-specific source binding. Missing or conflicting identities remain partial/blocked. The opponent's max-mean advisory is excluded, as are research-only leagues. Chopped active-field exposure remains blocked until its distinct field capture exists. These observed starters may change later and do not establish a final lineup or an opponent intention.

The coverage bundle now saves Markdown alongside JSON. Target-week player performance and post-week review are `NOT_DUE` until the existing outcome buffer elapses. Previous-week reports retain their own week and are never relabelled. Source-only reports and partial forecast boards do not complete the seven-product contract.

Each product now includes a read-only `readiness` diagnostic with observed counts and typed blocking reasons. The Markdown includes these per-product details beside the existing coverage table. Player performance checks scheduled game/team rows, unresolved source IDs, official finality and usage fields; exposure separates observed H2H starter joins from the blocked Chopped field, including Chopped Best Ball; waiver and lineup views count their league scope; specialist boards require a separately validated hold/stream strategy; postweek review separates PR2 revisions, M10 exact scoring and the still-missing paired FIE/Sleeper decision comparison. A diagnostic does not set `complete`, alter advice, or silently certify a report. Week 4 has all 16 scheduled games and 32 team entries but one unattributed provider row, uncertified official finality, and no snap/route source; it remains partial.

After the buffer, the bundle validates a real M10 prospective outcome revision against its original forecast manifest, counts observed versus missing or mismatched source players, and adds this read-only coverage to the post-week review. Exact paired M9/M10 league metrics require the cutoff's first-written full scoring profile, unchanged scorer version, and numeric source fields for every nonzero scoring key in both the realized and predicted raw components. Week 4 has 358 observed provider rows among 782 forecast identities, but no retained cutoff profile; it therefore reports a typed exact-scoring blocker. Provider standard/PPR totals are not substituted, and one week's descriptive metrics cannot promote M10 or certify the full post-week product. The separate Sunday Sleeper baseline has a different cutoff and requires its own paired review.

## Decision accountability

`decision-ledger-<run>-<attempt>.json` plus Markdown creates deterministic IDs from the owner, source-report hash, league, target, kind and unchanged recommendation. It preserves explanations/confidence from the owner and keeps blocked/no-op league states separate from recommendations. Research-only lifecycle states receive no new advice objects.

User adoption, realized outcome, hindsight optimum and ex-ante quality stay unknown. An observed current starter is not proof that the user followed advice. The action-binding API requires a separately hashed `fie-user-action-source-v1` JSON with matching decision/league/season/week, observation time and actual action. It rejects future, pre-issuance, wrong-target and mismatched-source observations. If the recommendation owner did not declare an issuance time, adoption binding is blocked rather than treating its model as-of as publication time. This API observes declared actions; it executes no transaction and assesses no statistical decision quality.

### Immutable PR2 report binding

The weekly bundle replays PR2's existing capture identity against `lineups/captures/portfolio-<capture_id>.json`. Missing archives, altered payloads and impossible publication clocks block that owner. The existing writer's generation-only refresh remains valid. Latest pointers alone do not certify evidence.

Exposure includes unchanged PR2 direct-H2H opponent contexts when available, with the capture and scoring signature retained. Exact maximum-mean opponent lineups are advisory and are never labelled submitted starters or manager intentions. Chopped active-field evidence stays independently blocked until captured; a direct pairing cannot fill that gap. All products remain partial until their complete contracts are satisfied.

### Stale roster recovery and stored postgame review

The portfolio surface retains the existing core freshness limit, typically six hours, even when broader pipeline inputs still pass their 36-hour guard. Stale views display original observation time, age, limit and the Refresh Currentseason recovery action. Run refresh before Window 1C; its successful completion triggers Window 1D. Do not relax freshness to make coverage appear available.

After the established postgame buffer, the bundle inspects stored PR2 evaluation revisions. It validates the immutable capture, provider-source adapter, raw point-in-time envelope, exact scoring replay and unchanged owner evaluation, retaining each file hash. Invalid revisions remain visible. Results are partial owner evaluation, not proof of user adoption or a paired FIE/Sleeper comparison. The provider raw-response hash remains declared by the existing owner rather than independently replayed here. Target-week outcomes remain NOT_DUE before the buffer.

PR2 direct-H2H context now retains submitted opponent starter IDs from the captured matchup response, in the declared Sleeper namespace. Empty slots are counted; an absent starter list stays unknown. These timestamped observations are neither a certified final lineup nor the advisory maximum-mean lineup, and are not joined by display name. Existing immutable captures are not rewritten.
