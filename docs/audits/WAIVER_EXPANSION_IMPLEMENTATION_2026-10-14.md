# Windows implementation and verification

Use the final **AM delivery** package identified in the accompanying verification receipt. S00–S05 files are recovery checkpoints and must not be treated as a release. This guide preserves the old long-path worktrees and imports the final change into a new short-path worktree. No reset, clean, force-push, retraining, model promotion or provider recapture is required.

The additional scope is 16 exact scoring signatures / 64 position units for 19 leagues. The three original signatures and their Week 6 capture remain unchanged. Ultimate ITN stays enabled for source collection but has no additional 2026 active-decision model. The Final Cut remains eliminated research-only. All forecast, ranking, recommendation, transaction and activation eligibility stays false.

## 1. Recover the delivery and preserve your existing worktrees

Download the AM index, all numbered volumes, and the import script into one short folder, for example `C:\Users\User\FIE\AM-20261014`. Run the provided import script with your existing repository path and that delivery folder:

```powershell
$Repo = 'C:\Users\User\Documents\Codex\2026-09-03\look-at-the-chats-repository-audit\work\FIE-P0-weekly-pipeline-2026-10-07'
$Delivery = Join-Path $env:USERPROFILE 'FIE\AM-20261014'
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Delivery 'Import_FIE_Week6_Expansion.ps1') -RepoPath $Repo -DeliveryFolder $Delivery
if ($LASTEXITCODE -ne 0) { throw 'Import failed. Preserve the output and all worktrees.' }
```

Set your working directory to the new `IMPORTED` path printed by the script. It verifies volume sizes and hashes, rejoins the exact bundle, verifies its Git prerequisites, and creates a separate worktree. Stop on any error and preserve its output. Intermediate checkpoint bundles require their own recovery instructions; do not mix volumes from different stages.

The final package states its source base, exported branch, commit and bundle hash. The import script must match those values. Never update an existing dirty worktree to install it.

## 2. Use a short checkout and the established environment

In the imported worktree, confirm `git status --short` is empty and `git log -1 --oneline` matches the AM receipt. Git long-path support is enabled by the importer. Keep the new repository and Python environment under the short `FIE` folder.

```powershell
$Python = 'C:\Users\User\Documents\Codex\2026-09-03\look-at-the-chats-repository-audit\work\FIE-week6-python-2026-10-13\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) { throw 'Use your existing validated Python 3.12 environment.' }
& $Python --version
node --version
if ($LASTEXITCODE -ne 0) { throw 'Environment check failed.' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

The CI environment uses Python 3.12, Node 22 and `research/requirements.txt`. Install missing dependencies into the existing virtual environment only when necessary. Do not silently switch Python versions or train a replacement model.

## 3. Reconcile the latest main without overwriting evidence

```powershell
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git merge --no-edit origin/main
if ($LASTEXITCODE -ne 0) { throw 'Merge needs review. Preserve this worktree; do not overwrite capture files.' }
```

The package was prepared from the source base in its receipt. Later main commits may refresh replaceable app snapshots or the research view. An immutable source envelope, forecast capture or model lock must never be resolved by choosing a side blindly. If a conflict touches these immutable files, preserve both versions and investigate their hashes. The old long-path checkout remains untouched.

## 4. Verify the scoring, roster and historical artifacts

```powershell
& $Python research/integrity_among_us_roster_evolution_test.py
if ($LASTEXITCODE -ne 0) { throw 'Among Us roster repair failed.' }
& $Python research/integrity_v932_structural_profile_test.py
if ($LASTEXITCODE -ne 0) { throw 'A structural profile still drifts.' }
& $Python research/integrity_waiver_v2_scoped_sources_test.py
if ($LASTEXITCODE -ne 0) { throw 'Scoped event attribution failed.' }
& $Python research/integrity_waiver_v2_expanded_inference_test.py
if ($LASTEXITCODE -ne 0) { throw 'Additional inference boundary failed.' }
& $Python research/waiver_v2_prospective.py --replay-lock data/research/prospective/waiver-v2/locks/2026/revision-1/model-lock.json
if ($LASTEXITCODE -ne 0) { throw 'Original twelve-unit lock replay failed.' }
& $Python research/validate_waiver_v2_expansion.py
if ($LASTEXITCODE -ne 0) { throw 'Additional source/model/capture replay failed.' }
```

Full replay is intentionally substantial: it reconstructs source scope, checks the original scalar scoring owner, rebuilds labels/features, refits all 64 declared historical units and replays the issued capture. It makes zero provider requests. Success must report 64 units, full source/model replay and the AM receipt's capture count. It is verification, not a new parameter selection or a new model lock. Do not increase a timeout to conceal a failing assertion.

The historical audit found ten unblocked missed-field-goal return candidates in the six archived training seasons, not low single digits. Description yardage totals 516. Sleeper `fg_ret_yd` nonzero observations use team IDs. Offensive source relevance is repaired, but exact DST reconciliation remains unresolved. Return yards and 40/50-yard bonuses retain their scoring weights; unverifiable affected outcomes remain null locally.

## 5. Build the synchronized release

```powershell
& $Python tools/release_build.py --mode personal
if ($LASTEXITCODE -ne 0) { throw 'Release blocked. Preserve the worktree and inspect config/release-gate.json.' }
$Gate = Get-Content -LiteralPath 'config\release-gate.json' -Raw | ConvertFrom-Json
$Failed = @($Gate.checks | Where-Object { $_.ok -ne $true })
$Failed | ConvertTo-Json -Depth 10
if ($Failed.Count -ne 0) { throw 'Do not commit or push a blocked release.' }
git status --short
```

Expect `DEPLOYABLE_SOURCE` and the exact check count recorded in the AM verification receipt. Manifest and dist files may update on your machine because the generated release receipt records local execution. Review the diff and stage only intended generated release files. The build must not rewrite original captures, the additional capture, archived sources or either model lock. The package's automated browser tests cover null values, actual capture timestamps, escaping and stale league-switch responses. A real browser visual check after deployment remains a manual post-merge check.

## 6. Review and publish one PR yourself

Read `WAIVER_EXPANSION_LEAGUE_STATUS_2026-10-14.md` for all 20 leagues and each position's remaining historical blocker. Review `git diff origin/main --stat` and `git diff origin/main -- config/league-portfolio.json config/contracts/runtime-contracts.json research/league_profile.py .github/workflows/validate-fie-weekly-pipeline.yml`.

If the local build changed only intended manifest, gate and dist outputs, commit those selected paths. Then push the imported branch normally and create a PR to main. Wait for **Validate FIE Weekly Pipeline**, inspect its full additional replay and personal release results, review the final diff, then merge yourself. Do not enable auto-merge or change governance modes to obtain a green result.

```powershell
git status --short
git diff --stat
# Stage only reviewed generated outputs if your local release changed them.
git push -u origin ops/waiver-profile-expansion-2026-10-14
if ($LASTEXITCODE -ne 0) { throw 'Push failed; preserve the worktree.' }
gh pr create --base main --head ops/waiver-profile-expansion-2026-10-14 --title 'Expand component-scoped offensive research evidence' --body 'Repairs anchored Among Us roster checks, retains supported return and long-play scoring with scoped exclusions, and adds 64 frozen historical research units plus a separately issued Week 6 capture. Original captures remain unchanged and all eligibility remains false. See the included verification receipt and per-league blockers.'
if ($LASTEXITCODE -ne 0) { throw 'Create the PR manually on GitHub if gh is unavailable.' }
```

Only the replaceable `weekly-research-view/2026/week_06.json` pointer may need reconciliation with newer main observations. Rebuild it through `publish_weekly_research_view.publish` using the original/additional captures, their readiness builders and the additional capture's bound source envelope. Verify both capture hashes afterward. Do not choose a conflict side for an immutable source, lock or forecast.

## 7. Verify the merged state in another fresh short worktree

```powershell
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Post-merge fetch failed.' }
$Merged = Join-Path $env:USERPROFILE ('FIE\Merged-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
git worktree add --detach $Merged origin/main
if ($LASTEXITCODE -ne 0) { throw 'Fresh post-merge checkout failed.' }
Set-Location -LiteralPath $Merged
git status --short
git log -1 --oneline
Test-Path 'config\waiver-v2-expanded-scope.json'
Test-Path 'data\research\prospective\waiver-expanded\forecasts\2026\week_06\capture.json'
```

The merged checkout must be clean. Check the old and additional lock/capture SHA-256 values against the AM preservation receipt. `git status` being clean proves checkout consistency, not scientific eligibility.

## 8. Re-run Refresh FIE Current Season

On GitHub Actions, run **Refresh FIE Current Season** on main. Leave league ID blank to target all 23 collection-enabled leagues; use season/week defaults and governance mode **KEEP**. [The failed run](https://github.com/constantinrube-hub/Fantasy-Intelligence/actions/runs/38399352230/job/115302989273) stopped at the release rebuild because `integrity_v932_structural_profile_test.py` detected Among Us roster-contract drift. The repair adds a Week 2 base anchor and checks slot capacities, including the planned Week 6 bench stage. Snapshots had built successfully in the failed run; its final release and commit did not complete.

Evidence after rerun: all 23 targets resolved; league snapshots built; the structural profile gate passed; the personal dist rebuild passed; final intelligence/deploy synchronization committed; and workflow usability evidence has no job-failure blocker. If failure changes to another check, inspect that check rather than repeating the old repair. This run cannot activate the new research models.

## 9. Verify Week 6 capture preservation and the read-only view

The AM package should already contain the additional pre-kickoff capture, bound to the authentic archived Week 6 source envelope. Verify its actual timestamp, Weeks 6–8 targets, model-lock/source/history hashes, coverage for all 16 signatures, abstention reasons and every eligibility flag false. The original three-signature capture must retain its original timestamp and hash.

A Week 6 preparation rerun may report `EXISTS` for both immutable captures. It must preserve their bytes and use new history/report revisions. Do not dispatch a fresh provider capture to reconstruct an older cutoff. If the real calendar has moved beyond the first target kickoff, preserve the issued capture and use the normal future evaluation path.

Open the app's research panel after deployment and switch across the 23 collected leagues. Expect league-specific scoring signatures, separate legacy/additional capture times, null confidence, typed abstentions, and eliminated states for Final Cut/Ultimate ITN. No frozen mean should become a waiver recommendation or a rank. Check among-us slot counts and league switching visually.

## 10. Accrue outcomes and close the remaining evidence

The first Week 6 next-three-week target spans Weeks 6–8. Review no earlier than November 3, 2026, after the Week 8 games; retry around November 5 if source corrections or completion receipts are pending. Evaluation requires the same exact scoring signature, canonical identity, full horizon and same-cutoff baseline. Partial horizons remain `NOT_DUE_FULL_HORIZON`; missing scores stay missing.

Remaining work is explicit: fresh unseen temporal confirmation; material history-coverage regressions for 45 of 64 additional units; calibrated uncertainty; historical publication timing; exact cutoff free-agent and legal-roster decision evidence; private bid/adoption evidence; separate promotion review; and evidence-backed certification of each of the seven report products. 2019/2020 source conflicts and exact DST field-goal-return reconciliation also remain open. Collection for eliminated leagues supports future-season research, without fabricating active-season decisions.

An implementation/CI success closes the mechanical preparation and reproducibility work. It cannot complete future outcomes or scientifically approve every league/position overnight.
