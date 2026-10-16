# Parameter stability, error decomposition and challenger interface

This additive update extends the established weekly component workflow. It does
not overwrite the sealed recovery project, original Week 6 forecasts or prior
operational runs. All diagnostic outputs are source-bound and research only.

## What runs automatically after merge

Every replay, fixture and weekly run snapshots the preserved source-refit baseline
and creates an explicit challenger-interface plan. Every new weekly fit receives
a parameter snapshot, support report and comparable-version predecessor analysis.
Every frozen-forecast review receives postgame diagnostic tables and an HTML report.
The existing Tuesday/Wednesday schedule and evidence-branch publisher retain these
outputs inside the same immutable run, with 90-day Actions artifacts as a second
download route. The user's PC is not needed for routine operation.

New outputs are under each run's `diagnostics/` directory:

* `parameters-baseline/` and, when a fit is generated, `parameters-fresh/`:
  `snapshot.json`, `parameter-changes.jsonl.gz`, `context-changes.jsonl.gz`,
  `summary.json`, `report.html`, `diagnostic-receipt.json`.
* `reviews/<freeze>/`: `raw-errors`, `component-decomposition`, `group-metrics`,
  `factor-metrics`, `probability-metrics`, `league-component-impact` compressed
  JSONL tables, plus summary, HTML and receipt.
* `challenger-interface-*`: explicit source-bound training plan and receipt.

The HTML is a readable top-100 preview; the companion compressed tables are the
complete outputs. Snapshots bind the fit and configuration hashes and retain
historical/current exposures, current shrinkage influence and observed opponent
support. Relative changes from zero remain undefined. Comparisons reject future
predecessors and do not attribute methodology changes to new performance data.
Team/position/availability/depth changes have their own context-change table.

Error decomposition covers passing/receiving/rushing yards and TDs, completions,
interceptions, catches, lost fumbles, return yards, kicking makes, tackle splits
and defensive return yards where their parent opportunities are observed.
Other components still receive raw errors and subgroup metrics; they do not get
invented causal factors. Symmetric product attribution sums to forecast minus
actual. Its implied efficiencies are ratios of projected/observed totals, not
the fitted conditional parameters themselves. Team-volume/share effects require
complete actor sums and matching team membership. Unknown and zero-parent cases
are labelled, not imputed into efficiency estimates.

Groups include model, position, team, pregame component rank, cutoff activity
cohort, week and lead week (1/2/3). Ranks are frozen-prediction ranks, not actual
performance ranks. Probability diagnostics include Brier score and reliability
bins only where the actual label is binary. League component error contributions
translate the same football evidence; they are not extra independent samples.
Incomplete rule coverage stays explicitly partial. No provider-exact semantic
certification or predictive superiority is claimed.

## Opponent source-column repair

The diagnostics exposed a real source-adapter issue: the V2 player-week source has
`opponent_team`, but the V2 refitter reads `opponent`. All 256 role-defense cells
in the saved source-refit fit consequently have zero current observed support.
This does NOT remove the separate team-level opponent PBP effects, and it does
not alter the original archived Step 2-4 coefficient-based forecast outputs.

`component_refit_v3.py` normalizes that column, rejects conflicting/missing values,
checks every opponent against the bound regular-season schedule, then executes
the preserved fitting method. It writes a distinct V3 fit and retains the
normalized intermediate. Real-source validation restored all 256 supported cells.
Future fresh weekly fits use this labelled source-schema repair. V2 frozen
forecasts and exact archived replay remain unchanged. The first V3 snapshot is
not numerically compared with V2 as though only a week of evidence had changed;
subsequent V3 fits can be compared with each other.

The row-level `RECOVERED_V2_STAGE_*` labels are legacy engine stage labels;
the fitted method version and pipeline-lock hashes identify V2 versus V3.
Do not pool different versions without retaining that provenance.

## Learned weights: interface only

`component_challenger.py` validates the training cutoff/hash, writes a versioned
plan, lists required candidate artifacts and enforces chronological folds.
Training and feature selection remain disabled. Setting a configuration Boolean
does not bypass the methodological checkpoint. No weights were learned, no
feature search was performed, and no candidate silently replaces the baseline.
This is the separately gated interface requested before actual challenger design.
The repository routing contract for new statistical methodology remains at
`docs/audits/CODEX_MODEL_ROUTING.md`. Original 2026 W6-8 outcomes are protected
from iterative hyperparameter selection at this initial checkpoint.

## Publish and activate

Apply the small diagnostics update on `research/component-diagnostics-20261016`.
Its push triggers the workflow's read-only acceptance job: package integrity,
operational/diagnostic/preserved tests, full baseline replay and comparison,
real W5 actual ingestion, plus the separate V3 source refit.
After that CI run passes, merge the branch into main. The existing schedule then
includes diagnostics automatically. To seed the first durable snapshot now,
manually run the workflow on main with `mode=diagnostics`. That mode needs no
completed W6 outcomes and generates no new football forecast.

PowerShell with GitHub CLI after merge:

```powershell
gh workflow run component-weekly.yml --repo constantinrube-hub/Fantasy-Intelligence --ref main -f mode=diagnostics
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic seed dispatch failed' }
```

Local commands, from repository root with recovery dependencies installed:

```text
python -m unittest discover -s research -p integrity_component_diagnostics_test.py -v
python research/component_weekly_ops.py --mode diagnostics --run-id diagnostics-first-seed
```

The release remains pending cloud CI, merge and a main-branch seed run until
those operations are independently verified. Local test success is not an
assertion that this update has already been deployed.
