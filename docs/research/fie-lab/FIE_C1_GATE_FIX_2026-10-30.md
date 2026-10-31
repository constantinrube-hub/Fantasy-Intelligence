# C1: Component gate window, early exit and monitor coverage

**Date:** Fri 30 Oct 2026, ~14:05 Berlin · **Author:** Claude · **Readiness item:** c1 (your items w6 + w1 apply it) · **Status:** v1, package ready
**Spec:** `FIE_RESEARCH_ENGINE_OVERHAUL_REVIEW_2026-10-26.md` §5.7, P1 (without the completeness wait = bk6) and P2.
**Base:** `Fantasy-Intelligence` @ `9aefae20` (30 Oct 12:38 UTC), read-only clone. **Nothing in the repository was changed**; you apply it with `apply_c1.ps1`.
**Package:** `c1_package.zip` (SHA-256 `52fd2147…c703`): 10 replacement files, a patch for a 3-way fallback, a manifest of git blob ids, the PR text and the PowerShell script.

---

## 0. Bottom line

1. **The component run no longer depends on GitHub starting within one hour.**
   - The gate admits **Tue 19:00 – Thu 18:00 Berlin**; cron fires every 2 h from Tue 19:35 to Thu 11:35.
   - A new `--check-work` step skips runs with nothing left to do, before installing anything. Most of the ~20 weekly slots cost seconds.
2. **Three workflows enter the monitor (13 → 16)**, and the monitor gets a "Known gaps" section. By-design PARTIAL runs no longer flood the investigation table.
3. **I deviated from the spec in two places**, both deliberate:
   - The window opens Tuesday **evening**, not 06:00.
   - Known gaps were added. Without them the new monitor entries would be noise.
4. **I found a latent bug the spec missed.** The shared research-prep workflow stamps its own path into the usability summary, but the monitor checks the caller's path. Adding the two workflows to the config as the review proposed would have shown every one of their runs as BLOCKED (`INVALID_USABILITY_ARTIFACT`). Fixed.
5. **Tests:**

   | Suite | Change | Fails on the old code? |
   |---|---|---|
   | Component | 19 → 26 tests, all pass | yes |
   | Monitor | adapter, known-gap and caller-stamping checks, pass | yes |

   `actionlint` is clean on both changed workflows. Applying the patch to the base gives a tree byte-identical to the replacement files.

---

## 1. Changes, file by file

| File | Change | Why |
|---|---|---|
| `research/component_weekly_ops.py` | `calendar_due` uses `in_window` (Tue 19:00 ≤ t < Thu 18:00 Berlin; constants `WINDOW_OPEN`, `WINDOW_CLOSE`). New `check_work()` and `--check-work`; `prior_pass_runs()` and `fetch_schedule()` factored out of `Runner` (same behaviour). `--check-due` also prints a `reason=` line | A1 of the review: the 07-hour gate turned every delayed run into a green NO_OP |
| `.github/workflows/component-weekly.yml` | Six cron lines with `timezone: Europe/Berlin` (season + January). Git-only `restore` moved before the work check. All heavy steps keyed on `steps.work.outputs.due`. New "Emit workflow usability evidence" and upload steps | Cheap early exit; monitor coverage |
| `research/workflow_usability.py` | Adapter `component-run`; `known_gap` per run, `known_gap_count` per workflow, `known_gap_run_count`; markdown "Known gaps" section and count in the header | P2 |
| `config/workflow-usability-monitor.json` | +3 workflows; `known_gap_reasons: ["OPERATIONAL_READINESS_PARTIAL"]` on Window 1C, 1D and the two research workflows; `known_gap_note` | P2 |
| `.github/workflows/_fie-week6-research-preparation.yml` | Usability summary carries the caller's path and name, from `github.workflow_ref` and `github.workflow` | Without it, every run of the new entries is rejected as an identity mismatch |
| `research/integrity_component_weekly_test.py` | Old 07:35 gate test replaced. New: window incl. CEST/CET, January closeout and blackout, manual dispatch, six `check_work` cases (issue due, Tuesday skip, Wednesday boundary in CET and CEST, done after recapture, stale outcomes, nothing-to-issue) | — |
| `research/integrity_workflow_usability_test.py` | 16 workflows; `component-run` (8 cases); known-gap demotion (4 cases); caller stamping in the reusable workflow | — |
| `CHANGELOG.md`, `docs/audits/COMPONENT_WEEKLY_OPERATIONS_2026-10-16.md`, `docs/audits/WORKFLOW_USABILITY_MONITORING.md` | Entry, schedule section, monitor semantics | Repo convention |

**What a scheduled run now does inside the window:**

| Situation | `--check-work` result | Heavy run? |
|---|---|---|
| Upcoming week not issued | `ISSUE_DUE` | yes |
| Issued, but the completed week's outcomes not captured since Tuesday 00:00 | `OUTCOME_CAPTURE_DUE` | yes |
| Issued and captured, before Wed 06:00 | `ALREADY_DONE_UNTIL_RECAPTURE` | no |
| From Wed 06:00, no capture yet after 06:00 | `RECAPTURE_DUE` (stat corrections, as the old Wednesday slot did) | yes, once |
| From Wed 06:00, recaptured | `ALREADY_DONE` | no |
| Manual dispatch | `MANUAL_DISPATCH_ALWAYS_RUNS` | yes |

**What the monitor records for it (`component-run`):**

| Run outcome | Monitor state |
|---|---|
| Skipped by calendar or work check | NO_OP, with the reason |
| `FROZEN` | USABLE |
| `ALREADY_FROZEN` (the recapture pass) | USABLE |
| Receipt `FAIL` | BLOCKED, with the error class |
| PASS receipt that issued nothing inside the window | BLOCKED (`COMPONENT_FORECAST_NOT_ISSUED`) |
| Job failure | INFRASTRUCTURE |

---

## 2. Deviations from the review, and why

1. **Window opens Tue 19:00, not 06:00.**
   - The review paired the 06:00 start with a completeness wait. The readiness page split that wait out to bk6.
   - Shipping the early start alone would issue the week on Tuesday morning, when Monday-night snaps can be missing (Week 6: 13/14 games at 10:01 UTC).
   - The `issued` check then locks that forecast for the week.
   - 19:00 matches your manual run (s4), which was chosen for exactly this reason.
2. **Gate closes Thu 18:00 while the last cron slot is 11:35.** A run delayed by 4–5 h (p90 here) still issues before your Thursday 19:00 session, instead of being rejected.
3. **Known gaps.**
   - The research workflows report PARTIAL by design: the code never claims a complete cycle.
   - Without the section, the two new entries add about 45 permanent "investigate" rows per 14 days (about 20 research-prep runs plus 3 evaluation runs a week), on top of the 24 from Window 1C/1D.
   - The review's P2 already proposed demoting 1C/1D; I made it config-driven and applied it to all four.
4. **Caller stamping.** Not in the review; found while wiring P2 (§0 point 4).

---

## 3. Devil's advocate

1. **Is this worth it if the Cloudflare Worker (bk1) replaces it in Weeks 10–11?** It protects at least Weeks 9 and 10, and the Worker plan is not built yet. The early-exit logic stays useful under the Worker too: precise triggers still need "is there work left?". So it isn't throwaway.
2. **The window can still miss.**
   - If GitHub drops every slot from Tue 19:35 to Thu 11:35 (11 slots), nothing issues. At the observed 52 % drop rate for the M10 workflow, that has probability ≈ 0.48¹¹ ≈ 0.0003.
   - The realistic failure is a run that *starts* and fails (source outage). That repeats every 2 h, which is the intended retry, but each failure is archived on the evidence branch (≈ 10 commits in a bad week).
3. **Tuesday 19:00 doesn't prove completeness; it only makes it likely.** The real fix is bk6. Until then, a late-arriving Monday game could still issue on incomplete data, though at a much lower rate than at 06:00.
4. **Known gaps can hide a real regression that reuses the same reason code.** The monitor can't tell a by-design `OPERATIONAL_READINESS_PARTIAL` from a new one. Counts stay visible per workflow. The proper fix is for producers to emit distinct reasons (e.g. `RESEARCH_CYCLE_NEVER_COMPLETE`), which needs changes in their code. Not done here.
5. **Manual dispatch always runs, by design.** A dispatch while a scheduled run is queued is serialized by the existing concurrency group and then ends `ALREADY_FROZEN`. That costs one heavy run, not a double issue.
6. **The Wednesday recapture rule is a judgment call.**
   - It mirrors the old Tue + Wed design.
   - If stat corrections usually land Thursday, the recapture is early. A later `RECAPTURE_FROM` (e.g. Wed 18:00) would catch more corrections, but would also push the run closer to your Thursday session.
   - Kept at Wed 06:00 to match the existing behaviour; it's one constant.

**Alternatives not taken:**

| Alternative | Why not |
|---|---|
| Keep the 07-hour gate and just add more cron lines | Every line still needs to start inside one hour; the drop and delay pattern makes that a coin flip |
| `workflow_run` chaining from the Tuesday outcome workflow | Couples two pipelines; a failure upstream silently stops issuance |
| Do the completeness wait now | Needs the sealed capture bundle's internals; I didn't want to rush a check that blocks issuance on Monday night |

---

## 4. How you apply it (w6 + w1)

1. Unzip `c1_package.zip` to `Downloads`.
2. In PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\c1_package\apply_c1.ps1"
   ```
   The script:
   - stops if your clone isn't clean;
   - checks the 10 files on `origin/main` are still the base versions (by git blob id, so line endings don't matter), and uses the 3-way patch if main moved;
   - copies and verifies the files, then runs both test suites;
   - commits with the attribution trailers, pushes `research/component-gate-c1` and opens a **draft PR**.

   Add `-NoPush` to stop after the local commit.
3. The push triggers the existing replay/fixture CI job (the branch matches `research/component-*`). Merge when it's green.
4. **After merge, Tuesday 3 Nov:** keep your manual start at ~19:30 (s4) as the safety net for the first week. Expected trace:
   - scheduled runs that night: NO_OP `ALREADY_DONE_UNTIL_RECAPTURE`;
   - first run from Wed 06:00: one `RECAPTURE_DUE` heavy pass;
   - then `ALREADY_DONE`;
   - `latest.md` shows 16 workflows and "Known gaps".

   If that trace appears, s4 can be dropped from Week 10 on.

**Local test note:** the component suite includes real-git and symlink cases written for Linux CI. On Windows they may fail for environment reasons. The script asks before continuing, and CI runs the same tests on push.

---

## 5. Files

| File | Where |
|---|---|
| `c1_package.zip` (`52fd2147`) | sent in chat; contents listed in its `README.txt` |
| `c1_component_gate.patch` | in the package and in the project (`claude/fie_lab/c1_component_gate.patch`) |
| This document | `claude/FIE_C1_GATE_FIX_2026-10-30.md` |

## Change log
- v1 (30 Oct 2026, ~14:05 Berlin): first version.
