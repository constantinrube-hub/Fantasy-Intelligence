# Component forecast recovery — standalone research project

This project restores runnable generation, all-league scoring, actual-outcome
ingestion, baseline freezes and paired weekly review. It is isolated from the
production app, M9/M10 champions, workflows and previously merged forecasts.
The supported entry points are the `recovery_*.py` commands and supplied
PowerShell wrappers. Preserved research modules are included as dependencies;
this is not a replacement installation of unrelated app or M9/M10 workflows.

The missing original WR fitting implementation has **not** been recovered.
The archived defensive inference coefficients are recovered from source tables;
the archived WR offensive TD prior uses a documented coarse-position fallback.
New fits use the separately versioned preweek source reconstruction. Do not
describe regenerated forecasts as identical to all previously saved stages:
consult the supplied comparison results. Historical player projection values
and quantiles are comparison inputs only, never fitting inputs.

## Install on Windows

Extract both Source.zip and Runtime.zip into the **same new empty directory**.
The directories `research`, `config` and `data` must be siblings. Do not extract
over your existing repository. The delivery verifier requires only Python's
standard library and validates both package file manifests before installation.

```powershell
Set-Location 'C:\Users\User\FIE\Component-Recovered'
py -3.13 research\recovery_verify_delivery.py
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed' }
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r research\requirements-recovery.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .\tools\Invoke_FIE_Recovery.ps1 -Action Test
```

These PowerShell wrappers have equivalent Python operations verified in Linux;
PowerShell execution itself is not certified by that test.

## Reproduce the archived-window reconstructed model

```powershell
$Run = 'data/research/components/recovery-20261016/runs/my-replay'
& .\tools\Invoke_FIE_Recovery.ps1 -Action Replay -Stage 4 -Output $Run
```

Replay is retrospective and never claims a new pregame issuance. It uses frozen
2026 W1–5 inputs to generate W6–8. It changes no saved/merged forecast. New
pregame issuance is blocked after first kickoff. Every output uses a new folder.

The primary source-refit report uses the separately reconstructed WR fitter.
To reproduce that exact model, use its fit and matching training revision:

```powershell
& .\tools\Invoke_FIE_Recovery.ps1 -Action Replay -Stage 4 -Fitted 'data/research/components/recovery-20261016/fit/source-refit-final.json' -Training 'data/research/components/recovery-20261016/training/week05' -Output 'data/research/components/recovery-20261016/runs/my-source-refit-replay'
```

## Weekly process

1. After a week is complete, capture a fresh bundle with its actual-stat endpoint:

```powershell
$W = 6
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Obs = "data/research/components/recovery-20261016/runs/$Stamp-outcomes"
& .\.venv\Scripts\python.exe research/recovery_capture.py --output $Obs --start-week ($W + 1) --actual-week $W
if ($LASTEXITCODE -ne 0) { throw 'Capture failed' }
$Actual = "$Obs-actual"
& .\tools\Invoke_FIE_Recovery.ps1 -Action Actuals -Week $W -Bundle "$Obs/observation-bundle.json" -Output $Actual
```

2. Review the immutable forecast freeze. To evaluate a complete three-week
horizon, pass all three actual revisions. Missing weeks and components remain
unknown; sparse provider omissions do not become zeros.

```powershell
& .\tools\Invoke_FIE_Recovery.ps1 -Action Review -Freeze 'data/research/components/recovery-20261016/freeze' -Actuals @($Actual) -Output "$Actual-review"
```

3. Before the following week's first kickoff, capture the new forecast window.
Refit using the new training revision, generate all stages and comparators,
validate them, and freeze them together. Use a fresh capture rather than an
outcome bundle captured after that window's first kickoff.

```powershell
$Next = $W + 1
$ForecastObs = "data/research/components/recovery-20261016/runs/$Stamp-next"
& .\tools\Invoke_FIE_Recovery.ps1 -Action Capture -StartWeek $Next -Output $ForecastObs
$Fit = "$ForecastObs/fitted.json"
& .\tools\Invoke_FIE_Recovery.ps1 -Action FitFresh -StartWeek $Next -Bundle "$ForecastObs/observation-bundle.json" -Training "$Actual-training" -Output $Fit
$Issuance = "$ForecastObs/forecast"
& .\tools\Invoke_FIE_Recovery.ps1 -Action Forecast -StartWeek $Next -Bundle "$ForecastObs/observation-bundle.json" -Training "$Actual-training" -Fitted $Fit -Output $Issuance
$Basic = "$ForecastObs/baselines"
& .\tools\Invoke_FIE_Recovery.ps1 -Action Baselines -Reference $Issuance -Output $Basic
& .\tools\Invoke_FIE_Recovery.ps1 -Action Freeze -Issuances @($Issuance,$Basic) -Output "$ForecastObs/freeze"
```

Check `$LASTEXITCODE` after direct Python calls. The wrappers throw on failure.
Stage 0 is the team-level opponent model; 1 adds individual efficiency; 2 adds
QB/RB rushing defense; 3 adds RB/TE/WR receiving defense; 4 adds WR tiers. Run
each stage with the same frozen fit and bundle for paired ablations.

## What is forecast and checked

All components demanded by the 23 frozen league profiles are mapped explicitly
and scored from joint scenarios. The source model emits 117 raw, opportunity,
source-convention and threshold keys across QB/RB/WR/TE/K/DL/LB/DB/DST entities.
Unknown scoring keys fail closed. This is arithmetic coverage, not provider
semantic certification or demonstrated accuracy.

Pass completions equal receptions, gross passing yards equal receiving yards,
and passing TD/two-point credits equal receiver credits. Pass attempts equal
targets plus explicitly estimated non-targeted throws. Team plays equal throws
plus sacks plus carries. Opposing sacks/interceptions/fumble recoveries share
the offensive events. Kicking, return capacities, scoring buckets and three-week
totals have explicit consistency checks.

Opponent effects and own availability are used. Weather, rest/travel effects,
individual WR/CB matchups and numerical opposing-injury effects are not modeled.
Questionable/doubtful players receive no invented medical probabilities. OUT
affects the first target week; IR/reserve assumptions extend through the window.

Workload support gates remove tiny initial opportunity weights below 0.1 and
unsupported roles before team normalization. Emitted fractional means are not
rounded independently; doing so would break accounting. Special-team unit
fumbles, field-goal returns and blocked-kick return yards retain explicit zero
forecast defaults. Kicker distance-yard totals use bin midpoints. These are
model policies, not claims of observed zeros.

## Evaluation and baselines

Basic B0 (rolling components), B1 (shrunk volume/rate) and Sleeper are frozen
from the same observation bundle as the candidate. Sleeper fields are used only
when explicitly published; incomplete league scores are excluded, not filled.
When complete custom scoring is unavailable, `SLEEPER_MATCHED_LEAGUE` metrics
compare every model on exactly the scoring terms Sleeper explicitly supplied
for that player/week. These are labeled partial subtotals, not full fantasy
scores. Their covered and total scoring-key counts are retained.
MAE, RMSE, signed bias, interval coverage and common-population paired MAE
differences are grouped by component, position and league. Three-week outcomes
require all three calendar weeks. Report counts/nonzero actuals alongside error
metrics; large zero cohorts can otherwise conceal poor active-player forecasts.

Retrospective reconstruction is labeled separately from prospective forecasts.
No automatic promotion, champion replacement, weather model, learned C6 model,
or claim of superiority over Sleeper is included.

## Publish to your repository

Keep this standalone tree intact under
`research/component-recovered-20261016/` on a separate research branch. This
preserves its relative source paths without replacing shared production files.
Use the delivered importer to create an isolated worktree, extract, verify,
commit and optionally push with your normal Git authentication. One branch and
one reviewable commit are sufficient. No force push or automatic merge is used.
