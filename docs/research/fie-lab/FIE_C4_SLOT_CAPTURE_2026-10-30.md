# C4: Slot capture, Task Scheduler generator, paired evaluation v2

**Date:** Fri 30 Oct 2026, ~14:20 Berlin · **Author:** Claude · **Readiness item:** c4 (also replaces w2) · **Status:** v1, tested offline, not yet run against the live APIs
**Files:**
- `research/fie_lab/slot_capture.py`, `slot_schedule.py`, `fie_paired_sleeper_eval.py` (v2)
- `research/fie_lab/tests/test_c4.py` (12 tests) and `tests/fie_paired_sleeper_eval_v1.py` (the registered v1, kept for the identity test)

**Repository:** unchanged by me; you push it with `push_all.ps1`.

---

## 0. Bottom line

1. **`slot_capture.py` takes the decision snapshot for one kickoff slot**, about 75 minutes before its first game, in a single run:
   - Sleeper projections for every position incl. IDP (DL/LB/DB)
   - the full player file with injury statuses
   - player props for the slot's games
   - game lines

   This is the run the market-variants test needs from Week 9. Its registration pairs props with Sleeper **from the same capture run**, and otherwise falls back to the weaker Thursday cutoff.
2. **`slot_schedule.py` writes, but does not run, a PowerShell file** that registers one Task Scheduler entry per slot (T−80, wakes the PC). You review the file, then run it.
3. **`fie_paired_sleeper_eval.py` v2**:
   - adds `--blend`, which applies the registered S-BLEND75 rule;
   - adds `--crosswalk-archive`, dated copies of the crosswalk (replaces w2);
   - without these options, output is **byte-identical** to the registered v1. This is tested against the exact registered file (SHA-256 `a3c04c6b…`), as the registration required.
4. **One deliberate deviation from the c4 spec: the script does not compute "FIE = frozen means × availability" itself.**
   - That rule (F1) lives in the frozen engine on your PC.
   - A second copy inside a capture script would drift from it and quietly change SIM-FIE's inputs.
   - Instead, the slot folder uses `sunday_capture.py`'s file names, so the frozen engine reads it directly (§3).
5. **Not yet proven live.** My sandbox can't reach Sleeper or The Odds API, so every test uses a fake HTTP layer. The first real run should be a 0-credit dry run (§6).

---

## 1. What one run does

| Step | Source | Cost | Saved as |
|---|---|---|---|
| Slot boundaries | Odds API events list | free | `props/events.json` |
| Sleeper projections | 9 position requests + 1 unfiltered | free | `sleeper_projections_<POS>.json.gz`, `_ALL` |
| Injury statuses | Sleeper player file | free | `sleeper_players_full.json.gz`, compact `sleeper_players.json.gz` (offence, K, IDP, team defences) |
| Props | per game, 7 core markets (December: drop kicker points with `--markets`) | markets returned, **once per game per week** | `props/event_<id>.json` |
| Game lines | spreads/totals | 2 | `odds_<season>_w<WW>_<ts>.json`, filtered to this NFL week; unfiltered copy in `raw/` with its hash |

**Slots:**
- Games kicking off within 45 minutes of a slot's first game share that slot, so Sunday 22:05 and 22:25 Berlin form one "late" slot.
- The target cutoff is first kickoff − 75 min, after inactives at about T−90.

**Credits:**
- The script never spends below `--reserve`. Defaults per week follow the November plan: W9 300, W10 200, W11 100, W12 5; 60 otherwise.
- A game whose props an earlier slot run of the same week already bought is skipped and recorded with the folder that holds them. A re-run never pays twice.

**Lines filter:**
- The Odds API returns next week's games too. That is what crashed the Week 8 D/ST add-on (bk8).
- The saved lines file keeps only games before the next Wednesday 12:00 UTC.
- A `fie_lab_filter` block records the rule and the hash of the unfiltered source, as the Week 8 receipt did by hand.

**Manifest (`manifest.json`):**

| Field | Contents |
|---|---|
| `slot` | Slot and games |
| `timing` | `ON_TIME`, `EARLY` or `LATE_AFTER_KICKOFF` |
| `steps` | Every step's status and credits |
| `aligned_pairs` | Per game: are props and Sleeper from this same run? This is the registration's rule; unaligned games are dropped, never filled from another cutoff |
| `fallback` | For a failed step, the latest earlier slot folder of this week where that step worked. Flagged, never silent |
| `files` | SHA-256 per file |

**Failure handling:**
- A failed step never stops the others.
- Exit code: 0 all OK; 3 any failed or late step; 2 setup error.
- Each run also appends one line to `slot_capture.log`.
- Without an API key, a run with `--slot-kickoff` still captures Sleeper, flagged as `SKIPPED_NO_EVENTS`.

## 2. Task Scheduler

```powershell
py -3 C:\Users\User\FIE\FIE-Lab\slot_schedule.py --week 9 --lab C:\Users\User\FIE\FIE-Lab
# read C:\Users\User\FIE\FIE-Lab\slots\register_slots_w09.ps1, then:
powershell -ExecutionPolicy Bypass -File C:\Users\User\FIE\FIE-Lab\slots\register_slots_w09.ps1
```

- One task per slot, starting at first kickoff − 80 min.
- **Start times are written in UTC** and converted by PowerShell to your PC's time, so clock changes can't shift them.
- Task settings:
  - wake the PC (needs "Allow wake timers" in the power plan);
  - start as soon as possible if missed (the capture then flags itself LATE);
  - stop after 30 minutes;
  - run only while you are logged on, so no password is stored.
- `unregister_slots_w09.ps1` removes the week's tasks.
- Regenerate if the NFL moves a game (flex scheduling).

Week 9 slots from the fixture schedule (the real list comes from the events list on the day):

| Slot | Kickoff (Berlin) | Task starts |
|---|---|---|
| Thursday night | Fri 02:15 | Fri 00:55 |
| International | Sun 15:30 | Sun 14:10 |
| Sunday early | Sun 19:00 | Sun 17:40 |
| Sunday late | Sun 22:05 | Sun 20:45 |
| Sunday night | Mon 02:20 | Mon 01:00 |
| Monday night | Tue 02:15 | Tue 00:55 |

## 3. FIE at the slot cutoff (why not inside the script)

The spec said "FIE = frozen means × availability, computed on your PC in about a minute". Two ways to do that:

| Option | Pros | Cons |
|---|---|---|
| A. Re-implement F1 (status bucket × played last game → P(plays)) in `slot_capture.py` | One script | The exact status mapping is only in the frozen `availability.py`, which isn't in the project. A copy would be my guess at it, would drift, and would change SIM-FIE's numbers without a registration |
| **B. Capture only; let the frozen engine read the slot folder (chosen)** | One implementation of F1; the folder is already in the Sunday-update format | One extra command when you want the FIE view |

Command for B:

```powershell
py -3 -m fie_lab.weekly_run --week 9 --odds <slot folder>\odds_2026_w09_<ts>.json --sunday <slot folder>
```

For research nothing is lost: the decision-time comparison (v5, from Week 10) can compute FIE-with-availability afterwards from the captured statuses, which are point-in-time.

For lineups, your rule is "Sleeper decides", and Sleeper is in the folder.

**If you want B automated:** send me `fie_lab/weekly_run.py` and `fie_lab/availability.py` from your PC. I'll check where `--sunday` writes its output, so several slots can't overwrite each other, and then add it as an optional final step.

## 4. `fie_paired_sleeper_eval.py` v2

| Option | What it adds |
|---|---|
| `--blend` | B75 = 0.75 Sleeper + 0.25 M10 (the registered S-BLEND75) and B50 (context) in the MAE/bias/lift report and the CSV. A rule block applies the registered rule. It prints **VERDICT** only when Weeks 8, 9 and 10 are all present, otherwise **INTERIM**; Weeks 4–7 are printed separately as seen data. |
| `--crosswalk-archive DIR` | The downloaded DynastyProcess crosswalk is saved as `db_playerids_<UTC date>.csv` + `.sha256` (identical content reused), and the file used is printed with its hash. Pass it back with `--crosswalk` to reproduce a run. |

The registration said the blend "will be added as an option without changing the existing outputs". Test T10 proves this: stdout and CSV are byte-identical to v1 on a fixture repo, for Weeks 4–7 and 4–10.

Use from Tuesday (s2):

```powershell
py -3 C:\Users\User\FIE\FIE-Lab\fie_paired_sleeper_eval.py --repo C:\Users\User\FIE\FI --weeks 4-8 --blend --crosswalk-archive C:\Users\User\FIE\FIE-Lab\crosswalk
```

## 5. Tests (`python -I research/fie_lab/tests/test_c4.py`, all 12 pass)

| # | What it proves |
|---|---|
| T1 | Slot grouping (10 games → 7 slots incl. next week's Thursday), late games merged, T−75 and week end correct |
| T2 | Full run: all steps OK, file names identical to sunday_capture.py, IDP kept and linemen dropped, 20 credits; a re-run buys 0 props and marks its pairs unaligned |
| T3 | Lines file excludes next week's game; filter block and source hash present |
| T4 | Reserve guard stops before the limit; step FAILED, exit 3 |
| T5 | Sleeper down and one props error: other steps still run, fallback = earlier slot folder, LATE flagged, logged |
| T6 | No key: Sleeper-only run with `--slot-kickoff`; `--slot next` refuses |
| T7 | The API key appears in none of the 114 written files |
| T8 | Dry run writes and buys nothing |
| T9 | Generator: 6 tasks for Week 9, next week's game excluded, start times in UTC, wake and catch-up settings |
| T10 | Eval v2 without new options = registered v1, byte for byte |
| T11 | `--blend` arithmetic exact; VERDICT only with Weeks 8–10 complete |
| T12 | Crosswalk archive written once, reused for identical content |

## 6. Devil's advocate and rollout

1. **The night slots depend on your PC.**
   - Thursday 00:55, Sunday-night 01:00 and Monday-night 00:55 need the PC on (or asleep with wake timers allowed) and you logged in.
   - A missed night slot isn't a loss for lineups if you set lineups before sleeping, but it is a lost aligned pair for the market test.
   - The real fix stays the Cloudflare Worker (bk1).
2. **Props are bought once per game, at the first slot that covers it.** A later re-run or a late slot doesn't refresh them, which keeps November's credits inside the plan.
   - Projected spend: W9 has about 14 games × ≤ 7 markets + 6 slots × 2 for lines, ≈ 110 credits against the 200 the W9 reserve allows.
   - Refreshing late props needs a paid month (decision v3).
3. **The 45-minute slot rule is a heuristic.** A 20:30 Berlin game would join neither the early nor the late slot and get its own task. That's correct, but it costs 2 more credits for lines.
4. **Untested against the live APIs.** The response shapes come from the Week 8 runs of `props_capture.py` and `odds_capture.py`, but a field name could still differ.
5. **"Run only while logged on" is a trade-off.** It avoids storing your Windows password, but a reboot without logging in kills the night slots. The alternative, "run whether logged on or not", needs the password and is your call.

**Rollout, Week 9:**

| When | Command | Cost |
|---|---|---|
| Thu 5 Nov afternoon | `py -3 slot_capture.py --week 9 --slot next --out ...\slots --dry-run` | 0 credits |
| then | `py -3 slot_capture.py --week 9 --slot next --out ...\slots --no-props --no-lines` (one real Sleeper-only run) | 0 credits |
| then | `slot_schedule.py --week 9 ...`, review, register | — |
| Fri ~01:00 | TNF slot runs automatically; check `slot_capture.log` in the morning | ≈ 8 credits |

## Change log
- v1 (30 Oct 2026, ~14:20 Berlin): first version.
