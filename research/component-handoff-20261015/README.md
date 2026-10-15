# Week 6: recover, publish and implement Steps 1–5

The exact saved Weeks 6–8 forecasts are recovered here. **The full Step 1–5 generating and postweek evaluation source is not recovered.** This branch preserves a usable Week 6 research baseline before kickoff; it does not install a functioning new forecast pipeline.

The original Step 2 and Steps 3–5 ZIPs are currently absent from the working environment. GitHub did not contain final commit `5dc4e32237a8abec4ca4818a2d328fdea33b9917`, a research branch containing it, or `research/component_prospective_review.py` on its default branch when checked on 15 October. Repeating the old download/import instructions alone cannot fix this. The exact browser download failure mechanism is unknown; the screenshot only establishes a failed download.

## Do this now: import the small recovered forecast bundle, then push

Remote publication was attempted and blocked: GitHub returned HTTP403 “Resource not accessible by integration” for object and branch creation, and command-line Git lacked push credentials. **This research branch has not been published.** Download the new `FIE-Week6-Forecast-Recovery.bundle` (about 3 MB), not either old large ZIP. Use PowerShell in your existing Fantasy-Intelligence repository. The following makes an isolated sibling worktree and leaves your current working files in place. Replace the first path if your checkout is elsewhere. Python 3.10+ and Git are sufficient; no NumPy/pandas installation is needed for this recovery.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Users\User\Documents\Codex\2026-09-03\look-at-the-chats-repository-audit\work\Fantasy-Intelligence'
$Branch = 'research/week6-component-forecast-recovery-20261015'
$Work = Join-Path (Split-Path $Repo -Parent) 'Fantasy-Intelligence-Week6-Recovered'
$Bundle = Join-Path $env:USERPROFILE 'Downloads/FIE-Week6-Forecast-Recovery.bundle'

git -C $Repo remote get-url origin
if ($LASTEXITCODE -ne 0) { throw 'Repository/origin not found' }
# Confirm the printed origin is constantinrube-hub/Fantasy-Intelligence.
git -C $Repo fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Prerequisite fetch failed' }
git -C $Repo bundle verify $Bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed' }
git -C $Repo fetch $Bundle "refs/heads/${Branch}:refs/remotes/component-delivery/week6-recovered"
if ($LASTEXITCODE -ne 0) { throw 'Bundle import failed' }
if (Test-Path $Work) { throw 'Choose a new $Work path; existing directory is preserved' }
git -C $Repo worktree add --detach $Work 'refs/remotes/component-delivery/week6-recovered'
if ($LASTEXITCODE -ne 0) { throw 'Worktree creation failed' }
Set-Location $Work

$Handoff = 'research/component-handoff-20261015'
python "$Handoff/forecast.py" verify
if ($LASTEXITCODE -ne 0) { throw 'Recovered forecast verification failed' }

$Revision = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$Export = "deliverables/Week6-Recovered-$Revision"
python "$Handoff/forecast.py" export --output $Export
if ($LASTEXITCODE -ne 0) { throw 'Forecast export failed' }
Invoke-Item (Join-Path $Export 'step4-league-scores.csv')

git push origin "HEAD:refs/heads/$Branch"
if ($LASTEXITCODE -ne 0) { throw 'Push failed: use your normal authenticated Git/GitHub Desktop session' }
```

The bundle prerequisite is existing main commit `25ade019f989b2f7c240d5ff493a579631b34099`; fetching main obtains that history. If using sparse checkout and the handoff directory is omitted, run `git sparse-checkout add research/component-handoff-20261015` in the new worktree first. Publishing this branch preserves the recovered forecast outputs; it does not install the missing full model pipeline.

If this small bundle also fails to download, open the saved report directly, download it through its own file menu, and preserve that exact file on a separate research branch. The standalone Step4 report contains its complete 5,577 raw component rows and 55,242 league scoring rows. The Step5 report contains all seven comparison models. This fallback preserves the original forecasts without claiming the missing code is present:

- [Step4 latest forecast](https://chatgpt.com/api/library/files/libfile_82cecaf4dc3c81919d48a4925b7878ed/download)
- [Step5 comparison](https://chatgpt.com/api/library/files/libfile_d398fbc53b088191a017ea9453b7b64b/download)
- [Step3 forecast](https://chatgpt.com/api/library/files/libfile_01e9c29d2d208191a8a74f9c78a4dea7/download)
- [Step2 forecast](https://chatgpt.com/api/library/files/libfile_6ba61b15bd448191a4e5482ad5b8be36/download)
- [Step1 forecast](https://chatgpt.com/api/library/files/libfile_2cb979bb80ec8191ae90182100f743d6/download)

The verifier checks file hashes, unique identities, all 117 component keys, 5,577 entity-week rows, 23 profiles, 39,000 comparison model rows, Step4 equality with the saved Step5 comparison on every supported cell, all 110,484 Step1/Step4 mean-score calculations, quantile order and Step4 team passing/reception mean credits. **It does not rerun the lost draw-level or source-fit validators.**

## What you have immediately

| Export | Contents |
|---|---|
| `step4-components.csv` | Latest forecast: all 117 components for all 5,577 entity-weeks, with opponent, availability and injury fields |
| `step4-league-scores.csv` | 55,242 weekly league rows: mean, P10, P50, P90, directly recovered from the saved report |
| `step4-three-week-mean-scores.csv` | 18,414 Weeks 6–8 expected score totals; no fabricated aggregate quantiles |
| `step1-components.csv`, `step1-league-scores.csv` | Recovered original Step1 output for component and league comparison |
| `step1-three-week-mean-scores.csv` | Corresponding Step1 three-week means |
| `comparison-components.csv` | Original Step5 frozen vectors for J1, Step2, Step3, Step4, Basic B0, B1 and Sleeper; blank remains missing/unsupported |
| `leagues.csv` | All 23 exact league IDs and names |

The original report JSON is retained in three small compressed files. `manifest.json` binds their hashes and the source report hashes. This is an extraction of already-issued values, not a rerun using today's refreshed inputs. The saved Step5 report records its original freeze at **2026-10-15T12:05:47.489779+00:00**; publication time is a separate timestamp and does not independently certify that earlier freeze. GitHub's new commit establishes the publication record.

The Step4 raw output contains structural zeros. The comparison retains the original per-component applicability masks, so unsupported fields remain blank. Do not zero-fill these blanks or filter away tiny raw projections. Rounded display values must not enter scoring/evaluation. Bonus/bucket values are already expected components from the original simulations; do not replace their probabilities with a threshold of mean yards.

Step4 is the final forecast. Step5 is the comparison/evaluation layer, not another model. Forecast availability for Weeks 7–8 remains the original assumption. Weather has not been added. Original event-level scenarios, complete audit/source artifacts, three-week distribution quantiles, source-fit code and the original Step5 outcome adapter are not reconstructed by these files.

## Check whether your PC already has the missing full implementation

Run this in your **original repository**, separately from the recovery worktree:

```powershell
Set-Location $Repo
git status --short
git branch --all --list '*component*' '*step2*'
git cat-file -e '467db370b8ef3f1b2dade6bc260c5eb0e772d65a^{commit}'
$HaveStep2 = ($LASTEXITCODE -eq 0)
git cat-file -e '5dc4e32237a8abec4ca4818a2d328fdea33b9917^{commit}'
$HaveSteps35 = ($LASTEXITCODE -eq 0)
Write-Host "Step2 commit available: $HaveStep2; final Steps3-5 commit available: $HaveSteps35"
```

These are historical commit IDs, **not remotely available fetch targets**. A negative result means that route is blocked. Do not assume `git fetch origin <old-sha>` will recover them. A downloaded bundle that actually exists on your PC may still be recoverable with `git bundle verify`; do not use a partial download. The old ZIP SHA-256 values were Step2 `93b907645309c449a67fc0903b6d006534e3130419d2b8648bf5da5672480165` and Steps3–5 `e0b98906d9f3deb1768522289a2118e68c22bf5f157f63a87a69fc02a1a8f009`.

If the **final commit exists locally**, it includes the recovered Step2 ancestry, so one isolated worktree and one push can publish all five steps:

```powershell
if (-not $HaveSteps35) { throw 'Full implementation unavailable; keep the recovered forecast baseline instead' }
$FullWork = Join-Path (Split-Path $Repo -Parent) 'Fantasy-Intelligence-Components-Full'
if (Test-Path $FullWork) { throw 'Choose a new $FullWork path' }
git -C $Repo worktree add --detach $FullWork '5dc4e32237a8abec4ca4818a2d328fdea33b9917'
if ($LASTEXITCODE -ne 0) { throw 'Full implementation worktree failed' }
Set-Location $FullWork
python research/verify_step2_completion.py
if ($LASTEXITCODE -ne 0) { throw 'Step2 receipt failed' }
python research/verify_component_steps3_5_completion.py
if ($LASTEXITCODE -ne 0) { throw 'Steps3-5 receipt failed' }
git push origin 'HEAD:refs/heads/research/component-steps1-5-20261015'
if ($LASTEXITCODE -ne 0) { throw 'Full implementation branch push failed' }
```

Do not use `git add .`, overwrite current files, reset your checkout or force-push. The original research branch requires no main merge to preserve/evaluate Week6. A research push also does not make Refresh Current Season run this model.

## Full Steps 1–5 implementation sequence

This section specifies the remaining recovery/install work if the final commit is absent locally. **The model files listed here are not supplied by this outputs-only branch.** Restoring/rebuilding them is a real prerequisite; there is no copy-paste command that turns the recovered vectors back into the missing simulation engine. Recovered reports provide numeric reference outputs for verification.

### 0. Preserve the pre-kickoff baseline first

Complete the import, verification, export and local push above. Keep this immutable research revision for Week6 even if the full source is rebuilt later. Record future rebuild/publication timestamps accurately. Do not overwrite or backdate a new forecast to appear pregame. Preserve existing M9/M10, runtime, rankings, scheduled workflows and all league scoring owners.

### 1. Restore individual offensive efficiencies

Restore the original Step1 behavior, or the recovered Step2 engine with role-defense disabled:

- Player catch rate, yards/reception and yards/carry from 2021–25 with historical recency decay `0.5^(2025-season)`.
- Historical player estimates shrink toward position priors with 20 exposure equivalents; current W1–5 estimates shrink toward historical player priors with 20 equivalents.
- Missing observations stay missing. Zero-denominator/nonzero-numerator records cannot fit rates.
- Reuse existing eligible-player budgets and broad opponent reconciliation. Catch rate combines in logit space; YPR/YPC average offensive and opposing rates.
- Required reconstructed owners: `research/component_step2_parameters.py`, `research/component_step2_recovery.py`, methodology config and source contracts. Do not introduce a separate competing scoring owner.
- Completion gate: reproduce original J1 when both added layers are disabled; reproduce the saved Step1 reference on all comparable values; preserve existing archives.

### 2. Restore opponent QB/RB rushing defense

- Exact PBP game/player-to-weekly-position joins; QB/RB/OTHER role separation; completed regular-season ordinary carries, with the documented lateral efficiency exclusions.
- Historical data 73,156 carries; current W1–5 4,219 carries. Fit 2026 defensive expectations from strictly earlier weeks, updating after each whole week.
- Role-volume effects use 100 carry equivalents and square-root adjustments to existing eligible weights; normalize without changing total team carries or within-role ordering.
- Yard efficiency uses 40 role-carry equivalents; TD rate uses 120. OTHER retains the parent broad-defense behavior.
- Restore `research/validate_step2_recovery.py`, `research/integrity_step2_recovery_test.py`, `research/verify_step2_completion.py` and completion receipts.
- Completion gate: role-disabled exact Step1 preservation; zero source/join/leakage errors; exact shared team budgets and offensive/defensive credits; saved Step2 report reproduction. Historical four-test/check counts are evidence of the earlier build, not a substitute for verifying the recovered implementation.

### 3. Restore RB/TE/WR receiving defense

- Restore `research/component_receiving_parameters.py`, `research/component_receiving_matchup.py`, `research/validate_receiving_fit.py`, `research/validate_component_receiving.py`, and `research/integrity_receiving_defense_test.py`.
- Fit role target shares, catch rate, YPR and TD/reception using historical 86,468 attributed targets and current W1–5 4,979 targets. Separate explicit non-targeted throws, unknown/unattributed throws and OTHER.
- Role target-share prior 100 total targets; catch prior 40 role targets; YPR prior 40 receptions; TD prior 120 receptions. Use strictly preweek expected exposure.
- Adjust normalized eligible target weights; replace the broad defensive efficiency input rather than stacking another full multiplier on it. Preserve QB/receiver event pairing, interception veto, positive scoring gains and shared drive budgets.
- Completion gate: disabled receiving layer reproduces Step2 draws; source-fit replay passes; saved Step3 outputs match; every league scoring replay passes.

### 4. Restore WR1/WR2/WR3+ opponent hierarchy

- Restore `research/component_wr_parameters.py`, `research/component_wr_matchup.py`, `research/validate_wr_fit.py`, `research/validate_component_wr.py`, and `research/integrity_wr_hierarchy_test.py`.
- Upcoming ranks use supported, available original target weights **before** opponent adjustment; descending weight, canonical-ID ties. Remaining supported receivers are WR3+. Unsupported weights are not promoted to active receiving roles.
- Historical ranks use only lagged usage/membership. They are proxies; historical injury/depth availability was not reconstructed. Exclude unranked targets from rank-specific fitting and report coverage.
- Preserve the Step3 overall WR target-share budget exactly while redistributing within WR; shrink sparse rank defenses toward broad WR effects. Replace parent efficiency inputs without double counting.
- Completion gate: disabling rank effects exactly restores Step3 draws; no current/future game targets influence pregame ranks; OUT WR1 promotes next eligible WR; original Step2/3 parameter files remain unchanged; all credit/scoring checks pass.
- Latest saved Thursday team points: SEA 21.15625, DEN 19.984375. This is a recovery reference, not a new forecast issued during this handoff.

### 5. Restore frozen comparisons and postweek evaluation

- Restore `research/component_prospective_review.py`, `research/component_review_outcomes.py`, `research/component_weekly_outcome_view.py`, `research/validate_prospective_component_freeze.py`, `research/validate_component_review_outcome_adapter.py`, `research/integrity_prospective_component_review_test.py`, `research/build_component_review_report.py`, `research/verify_component_steps3_5_completion.py`, and `tools/Invoke_FIE_Component_Weekly_Review.ps1`.
- Restore selected `step5-prospective-review-v2` and its source-bound receipt from genuine source artifacts if available. Do not relabel this report extraction as that complete original namespace.
- Freeze J1/Step2/Step3/Step4 on their common input bundle. Basic B0/B1 use an earlier cutoff and are secondary comparisons. Sleeper is an external baseline with unknown internal feature cutoff; compare only explicitly available matching components/scoring terms.
- Weekly metrics: component × position × frozen pregame role MAE, RMSE and signed bias; Brier scores for binary event probabilities; true-zero/missing/source-basis coverage; identical paired cohorts against J1 and Sleeper where supported.
- League metrics must compare the full common supported score, or label an identical matched-term subtotal. Never compare a partial Sleeper subtotal against a full FIE score.
- Three-week metrics require all three actual calendar weeks. New actual revisions must preserve previous outcomes/reviews, use portable archived source references and never overwrite forecasts.
- Keep a feature experiment register: component, position/role, source/layer enabled, rationale, registration timestamp, effective future week. Changes apply only to a new future issuance; no automatic winner promotion.
- Completion gate: complete receipt verification, source-masked outcome-adapter preservation, missing/zero tests, paired-cohort and scoring tests, portable archive references and overwrite rejection. There are no observed Week6–8 accuracy results in the recovered freeze.

## Once the full code is genuinely restored: validate, then publish

Run in a worktree containing the actual full source and immutable candidate inputs. These commands cannot run from this outputs-only handoff.

```powershell
python research/verify_step2_completion.py
if ($LASTEXITCODE -ne 0) { throw 'Step2 completion failed' }
python research/verify_component_steps3_5_completion.py
if ($LASTEXITCODE -ne 0) { throw 'Steps3-5 completion failed' }
python research/integrity_step2_recovery_test.py
if ($LASTEXITCODE -ne 0) { throw 'Step2 tests failed' }
python research/integrity_receiving_defense_test.py
if ($LASTEXITCODE -ne 0) { throw 'Step3 tests failed' }
python research/integrity_wr_hierarchy_test.py
if ($LASTEXITCODE -ne 0) { throw 'Step4 tests failed' }
python research/integrity_prospective_component_review_test.py
if ($LASTEXITCODE -ne 0) { throw 'Step5 tests failed' }
```

Use the project's NumPy/pandas environment for these full-model checks. Never rerun issuance into an existing frozen namespace. If rebuilding from scratch instead of restoring the original files, issue to new names, generate new provenance-bound receipts and do not claim the old completion hashes apply. Review only intended research/config/audit/tool paths in `git diff --stat` and `git diff --cached --name-only`; add explicit paths, commit and push a new research branch. Merge/workflow integration requires its own working implementation and verification; it is not achieved by pushing CSVs.

After Week6 is complete, first run Refresh Current Season and require a source envelope covering completed Week6. Then, **only with the restored Step5 tools**:

```powershell
.\tools\Invoke_FIE_Component_Weekly_Review.ps1 -Week 6
if ($LASTEXITCODE -ne 0) { throw 'Weekly review failed' }
```

Repeat for Weeks7/8 after their actuals exist. The script evaluates the frozen W6–8 window; it does not issue a new W7–9 forecast. Capture missing/late/revised actuals transparently. Until the Step5 adapter is restored, the recovered vectors can be retained and inspected but the original automated weekly review is blocked.

## Required, recommended, optional

**Required now:** preserve and verify the exact forecast output on GitHub before kickoff; use Step4 as the component baseline; retain comparison missingness, identities, scoring rules and original timestamps.

**Required for full operation:** restore the Step1–4 model generators and source/scenario evidence; restore the Step5 actuals adapter/reviewer; pass the completion gates; publish the full research branch. A new run with refreshed sources must have a new issuance identity.

**Recommended:** one immutable pregame revision, one postweek review revision, component/position error review before changing features, and separately versioned new forecasts for later three-week windows.

**Optional later:** scheduled issuance/review, a combined UI, weather (Step6), uncertainty calibration and richer automatic feature-ablation reporting. None is needed to preserve today's already-issued Week6 baseline.
