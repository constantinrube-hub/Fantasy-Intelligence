# Component weekly generation and evaluation operations

## Reviewed baseline

The recovered standalone project was published at
`c5c9273bd0a1a9a60fdaf4c6f3d4fdbf92590ac3`, exactly one commit ahead of
`main` (`8c0f79029bf2a8be02b484de394ac21baf79dac7`) at review time.
It only adds `research/component-recovered-20261016/`. The original merged
Week 6 forecasts and sealed source/runtime manifests remain unchanged.
The user's Windows replay passed 2,847,717 checks, all 23 leagues and 117 keys;
47 output artifacts / 79,359 table rows reproduced exactly with no differences.

This change is an operational adapter, not a model/methodology change or
M9/M10/app activation. The original WR training implementation remains missing;
fresh forecasts use `SOURCE_PREWEEK_ROLE_REFIT_V2` as already implemented.

## Entry points

Run from the repository root with the recovery requirements installed:

```text
python research/component_weekly_ops.py --mode replay --run-id my-replay
python research/component_weekly_ops.py --mode fixture --run-id my-fixture
python research/component_weekly_history.py restore
python research/component_weekly_ops.py --mode weekly --run-id my-weekly --ablations
python research/component_weekly_history.py publish
```

Run IDs must be new. Each invocation writes a sealed receipt, source-commit
identity in CI, command logs, file hashes and an explicit PASS/FAIL status.
The live modes `weekly`, `forecast`, and `review` require main in GitHub Actions.
Replay and fixture may run on the research branch without publishing history.
Local live CLI operations are explicit operator actions; restore history first.

## Manual / CI acceptance

The new workflow is `.github/workflows/component-weekly.yml`. A push touching
its adapter on `research/component-recovered-20261016` triggers read-only CI:

1. Verify both original manifests and scenario archive CRCs.
2. Run targeted operational and preserved recovery regressions.
3. Generate the primary source-refit W6-8 replay (42 games).
4. Independently validate scoring/accounting and all-league coverage.
5. Compare every archived draw and emitted table against the reference.
6. Rebuild real Week 5 actuals and update training in a new directory.
7. Review the W6-8 freeze against W5 and require zero matches / pending status.
8. Upload logs, outputs and receipts for 90 days.

The existing recovery tests additionally exercise matched real-zero/error rows,
paired populations, incomplete horizons and partial Sleeper scoring subtotals.
There is no claim that Week 5 measures W6 forecasting accuracy.

## Live weekly operation

On main, manual dispatch supports `weekly`, `forecast`, and `review`.
The first two review outcomes and may issue; `review` never generates a forecast.

1. Restore the sealed operational history from the dedicated evidence branch.
2. Fetch the current 2026 regular-season calendar. Interpret kickoff clocks as
   America/New_York. Determine the contiguous completed-week prefix.
3. Capture missing completed outcome weeks from W6 onward and refresh the most
   recent completed week to allow later source corrections. A new capture binds
   the exact provider actual endpoint, player/PBP/snap/calendar data and profiles.
4. Build source-basis actual ledgers and training revisions; reject incomplete
   games and missing critical sources. Optional missing projections stay missing.
5. Review the original archived/candidate freezes and every prior operational
   freeze. Select one latest actual revision per week. Three-week totals require
   all three weeks; missing outcome fields are never zero imputed.
6. Issue only if the upcoming week's first kickoff is still future AND training
   can include its fully completed prior week. Supported start weeks are 6-16.
   No new W6 prospective issue is possible after Thursday's kickoff.
7. Capture a separate pregame observation bundle; refit from the declared updated
   training revision. Generate stages 0-4 on identical inputs when ablations are
   requested (scheduled default); otherwise generate stage 4 only.
8. Independently validate every generated stage. Build B0/B1 and explicit-field
   Sleeper comparators, freeze them together and export the HTML/CSV report.
9. Preserve the run, including failed-run diagnostics, on the evidence branch.

If a week is already frozen, retries review outcomes without replacing that
issue. Explicit manual `revise=true` creates an additional pregame revision.
It cannot bypass kickoff checks. An unfinished prior week blocks the next issue.
Live external-source execution remains subject to provider availability and the
first real manual main-branch run; local replay is not proof of provider access.

## Durable retention and write boundaries

New paths, relative to the sealed project, are exclusively:
`data/research/components/operational-v1/2026/runs/<run-id>/`.

The dedicated Git branch is `research/component-weekly-evidence-2026`.
An isolated Git worktree publishes only the allowlisted operational subtree.
Existing paths must have identical bytes; collisions and unsealed histories
fail closed. A normal push is used with one fetch-and-retry; no force push,
main push, or unrelated file staging. The source branch remains unchanged.
Git history is the durable archive; 90-day Actions downloads are supplementary.
No claim of unlimited storage: all-stage weekly draws increase repository size.

The Actions summary distinguishes calendar NO_OP, missing-receipt BLOCKED,
run FAIL, and successful run PASS. PASS does not imply a new forecast or validated
accuracy: forecast status and outcome coverage are separate fields. A source
failure remains a failed job even when its diagnostic run is archived successfully.

## Schedule and activation

Scheduled operation (since 30 Oct 2026, readiness item c1) is a window from
Tuesday 19:00 to Thursday 18:00 Europe/Berlin. Cron fires every 2 hours from
Tue 19:35 to Thu 11:35 Berlin (`timezone: Europe/Berlin`); the runner gate admits
starts up to Thu 18:00 because GitHub cron on this repository starts 1.5-4.5 h
late and drops up to half of the slots. The window opens Tuesday evening, not
morning, because Monday-night snap counts reach nflverse during Tuesday
(Week 6: 13/14 games at 10:01 UTC, 14/14 by 17:59 UTC) and a week is issued only
once.

Inside the window, `--check-work` (after a git-only history restore) skips runs
with nothing left to do, before any dependency install or download:
`ISSUE_DUE` until the upcoming week is FROZEN; `OUTCOME_CAPTURE_DUE` until the
completed week's outcomes were captured this week; `ALREADY_DONE_UNTIL_RECAPTURE`
until Wednesday 06:00; then one `RECAPTURE_DUE` for stat corrections; then
`ALREADY_DONE`. Manual dispatches are never skipped. Previously (16-29 Oct) the
gate admitted only the 07 local hour on Tuesday/Wednesday, so every delayed
scheduled run ended as a green NO_OP. Each run emits a `fie-workflow-usability`
summary (adapter `component-run`) and is listed in the usability monitor.
Not yet included: the completeness wait (skip issuance while the completed
week's pbp/player_week/snaps are incomplete); see backlog bk6. The default-branch calendar's September-
January window, January 11 closeout and January 12-April 25 blackout are respected.
The adapter is season-bound to 2026, including January 2027 closeout. It refuses
to issue unsupported shortened late-season windows or silently switch seasons.

The schedule becomes available only after the workflow is merged to main.
Before merging, require the push-triggered replay/fixture job to pass. After
merging, manually dispatch `mode=weekly` once and inspect its actual receipt,
artifact and evidence-branch commit. Routine scheduling then needs no PC.
Repository Actions write permissions / branch rules must allow the dedicated
evidence branch; a permission rejection is a failure, not a successful archive.

PowerShell after merge (GitHub CLI installed and authenticated):

```powershell
gh workflow run component-weekly.yml --repo constantinrube-hub/Fantasy-Intelligence --ref main -f mode=weekly -f ablations=true -f revise=false
if ($LASTEXITCODE -ne 0) { throw 'Workflow dispatch failed' }
gh run list --repo constantinrube-hub/Fantasy-Intelligence --workflow component-weekly.yml --limit 5
```

There is no weather/rest model, calibrated interval claim, model promotion,
lineup/waiver action, production ranking change or app integration in this change.
The original and retrospective model labels remain separate. Full custom league
Sleeper scores still require complete provider fields; matched subtotals are
explicitly labelled. Outcome reporting is diagnostic, with no automatic winner.

Official workflow trigger reference:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
