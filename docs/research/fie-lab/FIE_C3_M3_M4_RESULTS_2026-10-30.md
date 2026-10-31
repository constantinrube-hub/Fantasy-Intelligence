# C3: M3 fringe guard and M4 recalibration for M10, checked on history and registered

**Date:** Fri 30 Oct 2026, ~13:55 Berlin · **Author:** Claude · **Readiness item:** c3 · **Status:** v1
**Registration:** `claude/fie_lab/c3_m3_registration_v1.json`, SHA-256 `370571d7…9b7f`, registered **12:52 UTC**: after the Week 8 Thursday game, before every other Week 8 game.
**Frozen:** `c3_m3k_frozen_v1.json` (`a38e4356…401d`), Week 8 forecasts `c3_m3k_week8_forecasts_v1.csv` (`6162d235…af75`).
**Repository:** read-only clone of `Fantasy-Intelligence` @ `9aefae20`. Nothing in the repository was changed.

---

## 0. Bottom line

1. **M3 (fringe players over-projected) is now CONFIRMED on independent history.** In M10's 2022–25 out-of-sample rows (Weeks 4+), flagged players score **1.22 pts below** M10; unflagged players are within 0.06. Players with 0–1 games this season are **2.39 pts** too high.
2. **The error register's M3 fix had the wrong shape.** "Shrink toward a low base rate" pulls low projections *up*. The error is proportional instead: players with 0–1 games score about 0.5–0.75 × M10 at every projection level. A **multiplicative haircut (M3k)** passes the 2025 check at all four positions. It is registered as the only new challenger.
3. **M4 (compression) is real but not worth a challenger. Closed.**
   - It is a mid-season pattern, not an early-2026 one: history slopes are 1.12–1.19 in Weeks 8–10 at QB/RB/TE.
   - At QB it is the fringe effect: the slope falls from 1.14 to 0.92 once flagged rows are removed.
   - Neither linear form improves squared error out of sample. With slopes of 1.1–1.2, even a perfect stretch could recover only about 1 % of MSE.
4. **The promised timing slipped by one game.** The specs were due "before Week 8 outcomes"; the CAR–GB game was already played. Its 49 rows are excluded from the test, and a test proves no Week 8 data entered anything.
5. **Prior that M3k passes: about one in three.** It passes cleanly on 2025 Weeks 4–17, is mixed on 2025 Weeks 8–10, and overcorrects on 2026 Weeks 4–7 (contaminated).

---

## 1. What was promised, and the timing

The error register (v1, §5) said: specs for the M4 recalibration and M3 fringe guard are written before Week 8 outcomes exist, then tested on Weeks 8–10. The readiness page scheduled this for Mon 2 Nov, assuming outcomes land Tuesday. But Thursday's CAR at GB game was played at 00:15 UTC on 30 Oct, so part of Week 8 already existed.

| Safeguard | How |
|---|---|
| No Week 8 outcome read | Loaders drop every 2026 row with week ≥ 8 before any processing (`C3_CUTOFF_2026`, default 8). |
| Proven, not asserted | Test T2 rewrites all 2026 Week ≥ 8 rows (snaps zeroed, points × 9). Every output stays byte-identical. |
| Already-played game | Week 8 CAR and GB rows (49 of 681) are excluded from the test universe. |

---

## 2. What history shows

**Data.** M10_HGB out-of-sample rows 2022–25 from the season lock (23,510 played rows; predictions rebuilt as nflverse actual − residual; 0 % unmatched). The default-PPR scorer reproduces M10's own points to 3.6 × 10⁻¹⁵ (−2 per INT). Flags come from nflverse snap counts of earlier weeks (99.9 % of rows map to a PFR id).

### 2.1 M3: fringe players (history Weeks 4+ vs 2026 Weeks 4–7)

| Group | Definition | History n | History bias (actual − M10) | 2026 W4–7 n | 2026 bias |
|---|---|---|---|---|---|
| FG1 | ≤ 1 game this season, Week ≥ 4 | 1,333 | **−2.39** | 169 | −1.10 |
| FG2 | Rookie, mean snap share < 40 % | 1,747 | −0.82 | 94 | −0.82 |
| FG3 | Snap share fell ≥ 15 pp in the last game | 2,207 | −1.01 | 130 | −0.04 |
| Any flag | | 4,874 | **−1.22** | 370 | −0.60 |
| No flag | | 14,538 | +0.06 | 946 | +0.51 |

FG1 by M10 projection band (history): 2.6 → 1.3 · 6.5 → 3.4 · 11.8 → 7.8 · 17.4 → 12.7. The ratio is roughly constant, so the error is proportional, not a pull toward a common level.

**Reading.** M3 holds in history with a large n, which upgrades it from LIKELY to CONFIRMED. It is weaker in 2026 (−0.60 vs −1.22), and FG3 is not over-projected at all in 2026. That gap is the main reason for the modest prior.

### 2.2 M4: calibration slope by part of the season (history 2022–25)

| Pos | Wk 1–3 | Wk 4–7 | Wk 8–10 | Wk 11–13 | Wk 14–18 | All weeks | 2026 W4–7 |
|---|---|---|---|---|---|---|---|
| QB | 0.78 | 1.04 | **1.18** | 1.16 | 0.98 | 1.02 | 0.88 |
| RB | 0.99 | 1.10 | **1.12** | 1.05 | 1.00 | 1.04 | 1.15 |
| TE | 0.79 | 1.16 | **1.19** | 1.08 | 1.07 | 1.06 | 1.12 |
| WR | 0.95 | 1.01 | 1.04 | 1.06 | 1.04 | 1.02 | 1.12 |

The deep dive's "history is milder (1.03–1.09)" came from pooling all weeks. Mid-season, history is as compressed as 2026, so the early-2026 explanation in the register is wrong.

At QB the slope is the fringe effect: Weeks 7–11 slope 1.14 with fringe rows, 0.92 without (RB 1.12 → 1.12, TE 1.22 → 1.22, unchanged).

---

## 3. Forms tested on 2025 (fitted on 2022–24)

Two forms came from the register's wording; both failed. One revision of each followed, with a stated reason. The 2025 check was therefore looked at twice. This is disclosed in the registration and weakens 2025 as independent evidence.

**PPR MSE, 2025 Weeks 4–17 (lower is better; M10 = raw):**

| Pos | M10 | M3-shrink (register) | **M3k (registered)** | M4-ab (register) | M4-slope (revision) |
|---|---|---|---|---|---|
| QB | 72.88 | 72.54 | **70.47** | 73.23 | 72.99 |
| RB | 42.61 | 42.77 | **42.16** | 42.70 | 42.53 |
| WR | 34.54 | 34.49 | **34.36** | 34.56 | 34.57 |
| TE | 27.47 | 27.49 | 27.37 | **27.17** | 27.19 |
| Flagged rows: bias / MAE | −1.02 / 3.99 | −0.82 / 4.03 | **+0.20 / 3.60** | −0.60 / 3.82 | −0.90 / 3.92 |

M3k also lowers MAE at all four positions (QB 6.97 → 6.78, RB 4.70 → 4.55, WR 4.37 → 4.29, TE 3.69 → 3.65). Within-week Spearman moves −0.003 to +0.013.

**The same in the test's part of the season (2025 Weeks 8–10):** M3k lowers MSE at QB (71.85 → 69.74) and TE (30.81 → 30.76) only. RB (+0.08) and WR (+0.06) are slightly worse. MAE is lower at all four. Spearman drops 0.021–0.022 at RB and TE, just over the 0.02 guard. Under the registered rule this slice fails.

**2026 Weeks 4–7 (CONTAMINATED, fitted on 2022–25):** M3k lowers MSE only at RB (37.94 → 37.85). MAE is lower at RB, WR and TE. Flagged-row bias overshoots from −0.60 to +0.60: in 2026 the haircut is roughly twice as strong as needed.

---

## 4. What was registered: R-M3k

| Element | Rule |
|---|---|
| Base | M10_HGB default-PPR mean |
| Flags | FG1, else FG2, else FG3 (definitions in §2.1; only weeks before the target week) |
| Adjustment | flagged: k[pos, flag] × M10; unflagged: unchanged |
| k | Σ actual / Σ M10 on 2022–25 played rows, Weeks 4+; cells < 100 rows pool positions; clipped to 0.3–1.0 |
| Test | Weeks 8–10 pooled, played players, Week 8 CAR/GB excluded |
| Pass | MSE lower at ≥ 3 of 4 positions **and** MAE not higher by > 0.02 anywhere **and** Spearman not lower by > 0.02 anywhere |
| Status | Shadow. Adoption only on your approval after the verdict (≈ Tue 17 Nov) |

**Frozen k:**

| Pos | FG1 | FG2 | FG3 |
|---|---|---|---|
| QB | 0.58 | 0.90 (pooled) | 0.80 |
| RB | 0.54 | 0.94 | 0.88 |
| WR | 0.61 | 0.84 | 0.89 |
| TE | 0.55 | 0.87 | 0.86 |

**Week 8:** 372 of 681 M10 rows are flagged (FG1 269, FG2 30, FG3 73). Mean cut: FG1 −2.2 pts, FG3 −0.9, FG2 −0.4.

The largest cuts are almost all backup QBs, whom M10 projects at **10–14 PPR** (Jake Browning 14.0, Brady Cook 13.4, Justin Fields 13.0, Garrett Nussmeier 10.9, …). After the haircut they are at 6–8, still too high for a player who doesn't start. This is the M1/M3 combination in its purest form, and a reminder that M10 has no depth chart.

---

## 5. Why M4 is closed rather than registered

1. **M4-ab** (actual = a + b × M10, the register's wording) is worse on 2025 MSE at 3 of 4 positions. The intercept carries the history *level* into a season whose level differs: 2026 M10 bias at RB is +0.54, history −0.37.
2. **M4-slope** (stretch around the mean, level unchanged) moves 2025 MSE by −0.29 to +0.11 pts². In Weeks 8–10 it helps TE (−0.82) but hurts QB (+0.42). In 2026 Weeks 4–7 TE is worse (+0.20). Nothing is consistent.
3. **The ceiling is low by arithmetic.** If the true slope is b, a perfect stretch removes (b − 1)² × Var(M10) from the MSE:

   | | QB | RB | WR | TE |
   |---|---|---|---|---|
   | Ceiling (% of MSE) | ≈ 0.6 % | ≈ 0.8 % | ≈ 0.1–0.7 % | ≈ 1.5 % |

   Estimation noise in b easily eats that. *Correction to the registration text:* it states 0.6–0.8 % for QB/RB/WR. For WR that holds only with the 2026 slope (1.12); with the history Weeks 8–10 slope (1.04) it is ≈ 0.1 %. Descriptive text only; the registered rule is unaffected, so the registration file is left unchanged (its hash stays valid).
4. **Where compression does matter** is the spread of simulated team scores, which drives win probabilities. The simulator draws from M10's residual distributions, which already contain the spread. A point-mean stretch would double-count it.

**Decision recorded:** M4 is "real, not exploitable with a linear layer". It is revisited only inside the M11 rebuild, where features (snap share, depth chart) attack the cause.

---

## 6. Devil's advocate

1. **Is this worth doing for M10 at all?** On 29 Oct you moved the research focus to the component model and keep Sleeper for lineups. M10 now matters mainly as SIM-FIE's centre and as the base of S-BLEND75, S-F5 and S-Q1. Counter: c3 was a promise in the error register, and the result has value regardless of M10's future. "Fringe players are over-projected by about 40 % when they have 0–1 games" applies to any FIE model without a depth chart, including CM2.
2. **The haircut is crude.** One factor per position and flag treats a returning starter (FG1 with high snaps in 2025) like a practice-squad call-up. A better design would separate "returning from injury" from "no role". I didn't build it: more parameters, more forking paths, and the data to separate the two (injury designations by week) isn't in the history set.
3. **2026 disagrees with history.** Flagged 2026 players are over-projected half as much as in history. If that persists, M3k fails its MSE rule while still lowering MAE. In that case the right reading is "direction confirmed, size not", and the fix belongs in CM2-P (x1), not M10.
4. **The 2025 check was looked at twice.** That is a real, if small, forking path. The prospective Weeks 8–10 test is the only clean evidence. It was set up with one arm to keep it clean.
5. **The pass rule could pass the wrong thing.** MSE is dominated by large misses, and the haircut mostly reduces big over-projections of players who then score little. That is the intended effect for SIM-FIE. For start/sit, the Spearman guard protects ranking.

**Alternatives not taken:**

| Alternative | Why not |
|---|---|
| Use Sleeper's projection for flagged players instead of a haircut | Not FIE-pure; already covered by S-BLEND75 |
| Drop flagged players from SIM-FIE | Hides the problem; the availability layer handles "won't play" |
| Register M4-slope for TE only | Chosen after seeing that TE was the best case; that's exactly the forking path the single-arm design avoids |

---

## 7. How the test runs

| When | Command (in the FIE Lab folder with the c3 files) | Output |
|---|---|---|
| Week 9 Thursday session (or any time before grading) | `py -3 -I c3_week.py 9 c3_m3k_frozen_v1.json c3_m3k_week9_forecasts.csv` | Week 9 forecasts |
| Week 10 Thursday session | same with `10` | Week 10 forecasts |
| After Week 10 outcomes (≈ Tue 17 Nov) | copy the Week 8 file as `c3_m3k_week8_forecasts.csv`, then `py -3 -I c3_grade_run.py . c3_verdict.json` | verdict |

Requirements:
- Week 9/10 runs need the nflverse files in `raw/`.
- Grading needs the M10 outcome files of Weeks 8–10 from the repo.
- `c3_grade_run.py` refuses to run if the Week 8 file differs from the frozen hash.

**Tests (`c3_test.py`, all pass):**

| Test | Result |
|---|---|
| T1 | Byte-identical rebuild |
| T2 | Week ≥ 8 rows rewritten → identical outputs |
| T3 | k independent of all 2026 data |
| T4 | Scorer exact |
| T5 | `c3_week.py 8` reproduces the frozen Week 8 file |
| T6 | Grading code dry run |

---

## 8. Files

| File | SHA-256 (first 8) | What |
|---|---|---|
| `c3_m3_registration_v1.json` | `370571d7` | registration |
| `c3_m3k_frozen_v1.json` | `a38e4356` | k factors, constants |
| `c3_m3k_week8_forecasts_v1.csv` | `6162d235` | Week 8: M10, R-M3k, flags, test exclusion |
| `c3_check_tables.json` | `a291917e` | every table in §3 |
| `c3_lib.py` | `bf206e4b` | data layer and leakage cutoff |
| `c3_model.py` | `15a0dc89` | registered arm |
| `c3_grade.py`, `c3_grade_run.py` | `87769b69`, `58876dd4` | registered evaluation |
| `c3_week.py` | `7140e132` | Week 9/10 forecasts |
| `c3_build.py`, `c3_explore.py`, `c3_test.py` | `de2103aa`, `a38e419c`, `71db6381` | build, rejected forms, tests |

All are in `claude/fie_lab/`. For the repo package (w5), they belong on `research/fie-lab-2026` alongside the other registrations.

## Change log
- v1 (30 Oct 2026, ~13:55 Berlin): first version. Error register updated to v1.1 in the same session (M3 → CONFIRMED with the registered fix; M4 → closed; cheat-sheet and test schedule updated).
