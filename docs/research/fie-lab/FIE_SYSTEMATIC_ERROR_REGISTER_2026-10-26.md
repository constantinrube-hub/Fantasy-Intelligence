# Systematic Error Register: M10, Component Model, Sleeper

**Date:** Mon 26 Oct 2026, 00:26 Berlin (v1.1: Fri 30 Oct, ~14:00 Berlin) · **Author:** Claude · **Status:** v1.1, living document (update after every graded week)
**Sources:**
- `FIE_M10_VS_SLEEPER_DEEP_DIVE_2026-10-26.md` (M10 vs Sleeper, 2026 Weeks 4–6, n = 1,007, plus M10's 2022–25 out-of-sample history)
- `FIE_COMPONENT_VS_M10_VS_SLEEPER_2026-10-26.md` (Week 6 only, n = 312)
- v1.1: `FIE_C3_M3_M4_RESULTS_2026-10-30.md` (M3 and M4 checked on M10's 2022–25 history; registration `c3_m3_registration_v1.json`)

Week 7 is not used anywhere; it's the pre-registered clean test.

**How to read the verdicts**

| Verdict | Meaning |
|---|---|
| **CONFIRMED** | Seen in 2026 **and** in independent history, with a mechanism that explains it. Correct for it. |
| **LIKELY** | Seen in 2026 with a clear mechanism, but no independent history yet. Correct for it cautiously and re-check after Week 9. |
| **UNCONFIRMED** | Seen in one week only (all component findings), or a small subgroup. Don't correct yet; watch it. |
| **NOISE** | Looked like something but didn't hold up, or was a statistical artefact. Ignore. |
| **REAL, NOT EXPLOITABLE** *(v1.1)* | Confirmed, but no correction tested so far improves forecasts out of sample. Closed until a structural rebuild. |

---

## 1. M10 (M10_HGB)

| # | Error | Size | Verdict | Cause | Fix | Fix status | Interim rule for your own decisions |
|---|---|---|---|---|---|---|---|
| M1 | **QB rushing is essentially random** | Correlation with actual rushing yards 0.04 (Sleeper 0.46); carries −0.13 to 0.24 (Sleeper 0.46). Rushing ≈ 2.3 PPR pts per QB-game, much more for running QBs | **CONFIRMED** (mechanism is certain) | Carries are added to pass attempts and all yards are divided by that total, so the model can't tell rushing from passing | **Q1:** replace M10's QB carries and rushing yards with the QB's own recent rushing, shrunk toward his 2025 average | Registered; tested on Week 7 (Tue), in Week 8 if it passes | **Never use M10 to rank running QBs.** Use Sleeper's QB projection, or M10's passing plus Sleeper's rushing |
| M2 | **Ignores how good the offence is** | Too high by ≈ +0.9 pts when the team's implied total is ≤ 19; too low by ≈ −1.1 when it is > 28. A steady slope, same size in 2022–25 (n ≈ 10,400) | **CONFIRMED** | No betting line, opponent or team-scoring input. Its "team" feature is play volume, not points | **F5:** multiply M10 by 1 + b × (implied − 22.5) / 10, with b = QB 0.25, RB 0.19, TE 0.17, WR 0.18. Out of sample on 2026 W4–6 it improved all 4 positions; QB ranking 0.39 → 0.47 | Registered; tested on Week 7, in Week 8 if it passes | Adjust by hand: see the multiplier table in §4 |
| M3 | **Fringe and new players projected too high** | 2026 W4–6: players Sleeper puts under 5 pts: actual 2.9, M10 3.5–3.9; 0–1 games: +1.2 too high; rookie RBs +2.6, team-changers +0.6. **History 2022–25 (v1.1):** flagged players (≤ 1 game, low-snap rookie, or snap share −15 pp) −1.22 vs unflagged +0.06; ≤ 1 game −2.39, proportional at every projection level (actual ≈ 0.5–0.75 × M10). 2026 W4–7: −0.60 | **CONFIRMED** (v1.1; was LIKELY). Smaller in 2026 than in history | Missing or thin recent-games data → generic fallback; one big game dominates a 2-game average; history crosses seasons; no depth chart | **R-M3k:** multiplicative haircut k[pos, flag] × M10 for flagged players (FG1 ≈ 0.54–0.61, FG2 0.84–0.94, FG3 0.80–0.89). The v1 idea ("shrink toward a base rate") failed the 2025 check | **Registered 30 Oct 12:52 UTC**; shadow; tested Weeks 8–10 (W8 CAR/GB excluded); verdict ≈ Tue 17 Nov; prior about one in three | **When M10 is more bullish than Sleeper, believe Sleeper more.** For a player with 0–1 games this season, read M10 at about 55–60 % |
| M4 | **Projections too bunched together** ("star shrinkage", corrected) | 2026 calibration slope 1.12–1.18 (RB/TE/WR). **History (v1.1):** the same in mid-season (Weeks 8–10: QB 1.18, RB 1.12, TE 1.19, WR 1.04); pooled over all weeks it looks milder (1.02–1.06) because Weeks 1–3 and 14–18 are near 1. At QB it is the fringe effect (slope 1.14 → 0.92 without flagged players) | **REAL, NOT EXPLOITABLE** (v1.1; was LIKELY). The "early-2026" explanation was wrong: it's a mid-season pattern | Model trained to hit the typical outcome; few features to separate stars from the middle | Tested on 2025: a + b × M10 worse at 3 of 4 positions (the intercept imports the history level); a level-preserving stretch moves MSE inconsistently (−0.8 to +0.4 pts² by position and season part). Ceiling ≈ 0.1–1.5 % of MSE | **Closed 30 Oct** (no challenger). Revisit only in M11. Spread for win probabilities is carried by the residual distributions | RB/TE only: stretch M10 by about 10–20 % of its distance from the position average (at 15+: ≈ +1 pt RB, ≈ +2 pts TE). No stretch at QB or WR |
| M5 | **Slow to react to role changes** | After a snap-share drop of 5 pp or more, Sleeper is ≈ 0.45 pts better. After a jump of 15 pp or more, M10's RB level is 2.9 pts too low (yet its total error is no worse) | **LIKELY** for demotions; **UNCONFIRMED** for promotions (subgroups of 22–151) | Uses only the last 4 games; no snap share, no depth chart | Snap-share trend as a feature (free from nflverse) in the M11 rebuild. Partly covered by R-M3k's FG3 flag (drop ≥ 15 pp; history −1.01, 2026 −0.04) | Planned (M11) | After news of a demotion, trust Sleeper. After an RB's snap share jumps, nudge M10 up |
| M6 | RB carries too low, yards per carry too high | −1.6 carries per game, rushing yards unbiased | **LIKELY**, small fantasy impact (yards are right) | Each stat is predicted separately, with nothing tying carries to yards | Tie carries and yards in M11 | Low priority | Matters only in leagues that score carries |
| M7 | Small phantom rushing for WRs/TEs | TE 0.27 rushing yards per game vs actual 0.06 | LIKELY, negligible | Same mixed efficiency feature as M1 | M11 | — | Ignore |
| M8 *(v1.1)* | **Backup QBs projected like starters** | Week 8: Jake Browning 14.0, Brady Cook 13.4, Justin Fields 13.0 PPR (0–1 games). R-M3k cuts them to 6–8, still too high for a non-starter | **CONFIRMED** (mechanism certain; same root as M1 + M3) | No depth chart; QB efficiency feature mixes rushing | CM2's starting-QB rule (15 % for non-starters) is the right fix; in M10 only via M11 | — | Ignore M10 for any QB who isn't the named starter |
| — | ~~"Sleeper's level is right for stars, M10 is 2–5 pts low"~~ | — | **NOISE (artefact)** | Grouping players by one forecaster's projection always makes the other look wrong at the extremes. The real part is M4 | — | Corrected in plan §8g | — |
| — | Questionable players, home/away, opponent's implied total, M10 winning QB in Week 6 | No difference, or within noise | **NOISE** | — | — | — | Ignore |

**Where M10 is genuinely good (keep it):**
- RB receiving yards (correlation 0.45 vs Sleeper 0.41) and RB rushing TDs (0.44 vs 0.40).
- Overall level: bias closer to zero than Sleeper's.
- Independent information at RB and WR: in a combined regression M10's weight is 0.62 at RB and 0.40 at WR, alongside Sleeper.

---

## 2. Component model (RECOVERED stage 4)

**Every component finding rests on one week (Week 6).** None is confirmed. The component workflow must run weekly before any of this can be checked.

| # | Error | Size | Verdict | Plausible cause | Fix | Interim rule |
|---|---|---|---|---|---|---|
| C1 | **Level too low** | Bias −0.85 RB, −0.78 WR, −0.59 TE; ≈ −1.0 for teams implied above 20 | **UNCONFIRMED**, but the same sign at three positions makes it plausible | Team budget or TD priors set conservatively | Level recalibration once 3+ weeks exist | Add ≈ +0.5 to +0.9 pts to RB/WR/TE when you read it |
| C2 | **Weak at QB** | Error 6.02 (worst of the three), ranking 0.46, calibration slope 0.21 | **UNCONFIRMED** (29 QBs) | QB passing model; QB TDs | Re-check on Weeks 7–8 | Don't use it for QBs; its QB carries (0.45) are fine |
| C3 | TE ranking near zero | Spearman 0.06 (M10 0.07, Sleeper 0.23) | **Probably NOISE**: TEs are hard for everyone in a single week | — | — | Use Sleeper for TEs |
| C4 | **Bullish disagreements unreliable** | When ≥ 3 pts above Sleeper, closer only 32 % of the time (n = 19) | **LIKELY**, because it repeats M10's pattern (M3). Probably a general "FIE models don't see depth charts and news" effect | No news or depth-chart input | Fringe guard, and depth charts in M11. *v1.1:* the R-M3k flags (FG1–FG3) are model-independent and could be tested on CM2 inside CM2-P (x1) | Same rule as M3: when an FIE model is the more bullish one, trust Sleeper |

**Where the component model looked strong (to verify):**
- QB carries (0.45, like Sleeper; M10 0.24).
- No betting-line slope (it simulates team scoring).
- RB targets (0.61, best of the three).
- Players Sleeper projects for 15+ (error 4.95, best).
- WR calibration (slope 1.00).
- Best WR accuracy and ranking in Week 6.

These are exactly the areas where M10 is structurally weak, which makes an M10 + component average attractive. It's registered as **FIE-ENS**, verdict after 4 eligible weeks.

---

## 3. Sleeper (so you can read SIM-SLP correctly)

| # | Error | Size | Verdict | Interim rule |
|---|---|---|---|---|
| S1 | **Projections too spread out** | Calibration slope 0.75–0.89 (2026 W4–6): its stars are a bit too high and its scrubs too low. In Week 6 its 15+ group was 2.6 pts too high | **LIKELY** (2026 only; no clean Sleeper history exists) | Shade Sleeper's top projections down by ≈ 1 pt; its sub-5 projections are ≈ 1.3 pts too low |
| S2 | **WR level too low** | −1.0 pts per WR among players who play (−0.8 targets, −4.6 yards) | **LIKELY**. Probably a deliberate "might not play" discount inside its means | Doesn't change rankings; matters for win probabilities. Our availability layer is applied on top in SIM-FIE only, so SIM-SLP isn't double-discounted |
| S3 | No availability discount for questionable players | Full projections for Q players | By design | SIM-SLP is optimistic for rosters with Q players; SIM-FIE (F1/F1b) is the more realistic one there |

---

## 4. Interim adjustment cheat-sheet (until the fixes pass their tests)

**M2: multiply M10 by** (team implied points → factor):

| Implied team points | 17 | 20 | 22.5 | 25 | 28 |
|---|---|---|---|---|---|
| QB | 0.86 | 0.94 | 1.00 | 1.06 | 1.14 |
| RB | 0.89 | 0.95 | 1.00 | 1.05 | 1.11 |
| TE | 0.91 | 0.96 | 1.00 | 1.04 | 1.10 |
| WR | 0.90 | 0.96 | 1.00 | 1.04 | 1.10 |

**M3 (v1.1): multiply M10 for flagged players by** (history 2022–25; registered as R-M3k, not yet proven prospectively):

| Flag | QB | RB | WR | TE |
|---|---|---|---|---|
| ≤ 1 game this season (Week 4+) | 0.58 | 0.54 | 0.61 | 0.55 |
| Rookie with < 40 % snap share | 0.90 | 0.94 | 0.84 | 0.87 |
| Snap share fell ≥ 15 pp last game | 0.80 | 0.88 | 0.89 | 0.86 |

In 2026 so far these factors are roughly twice as strong as needed. Treat them as an upper bound on the correction.

**When M10 and Sleeper disagree** (2026 W4–6): on average the actual result lands **40–65 % of the way from Sleeper toward M10**. But when M10 is the higher one, Sleeper is closer in two of three games.
- For start/sit (getting the order right), a **75 % Sleeper / 25 % M10** mix was the most accurate.
- For win probabilities, an even mix is closer on average.

**Order of trust by task** (current evidence):

| Task | First choice | Second | Avoid |
|---|---|---|---|
| QB start/sit | Sleeper | Component (rushing part) | M10 for rushing QBs; M10 for any non-starter (M8) |
| RB start/sit | Sleeper, with M10 for receiving backs | Component | — |
| WR start/sit | Sleeper ≈ component ≈ M10 (Week 6 tie) | — | Any FIE model when it's the bullish outlier on a fringe player |
| TE start/sit | Sleeper | — | Both FIE models (ranking near zero) |
| Team win / survival odds | SIM-SLP (Brier 0.185) | SIM-FIE with F1b | — |
| D/ST | Your production D/ST model (small ranking edge; hypothesis) | Sleeper | — |
| K | Sleeper | — | Production K model |

---

## 5. Test schedule for the fixes

| Fix | Registered | Tested | Enters | Confirmed / reverted |
|---|---|---|---|---|
| F1b availability bands | 25 Oct 23:06 UTC | Week 7 (Tue 27 Oct) | Week 8, if not worse | Weeks 7–9 |
| F5 line environment | 26 Oct 00:11 | Week 7 | Week 8, if better at ≥ 3 of 4 positions without hurting ranking | Weeks 7–9 pooled |
| Q1 QB rushing | 26 Oct 00:11 | Week 7 | Week 8, if QB rushing error drops without hurting QB points | Weeks 7–9 pooled |
| FIE-ENS (M10 + component) | 26 Oct 00:22 | First 4 weeks where both FIE models issue 1-week-ahead forecasts | After 4 weeks | — |
| **R-M3k fringe guard (M3)** *(v1.1)* | **30 Oct 12:52 UTC** (after the CAR–GB game, before all other Week 8 games) | Weeks 8–10 pooled, CAR/GB Week 8 excluded | Shadow only; adoption on approval | Verdict ≈ Tue 17 Nov |
| ~~Recalibration (M4)~~ | **Closed 30 Oct** without registration (no out-of-sample gain; see M4) | — | — | — |

Registrations up to 26 Oct are in `fie_lab/data/derived/w7_freeze_v1.json` (with SHA-256 hashes of the code). R-M3k: `claude/fie_lab/c3_m3_registration_v1.json` (`370571d7…9b7f`).

*Note (Week 7 outcome, 28 Oct):* F1b, F5 and Q1 each failed one Week 7 criterion by a small margin and continue as shadow variants (S-F1B, S-F5, S-Q1) with a pooled Weeks 7–9 verdict; see `w8_shadow_registration_v1.json`.

## Change log
- v1 (26 Oct 2026, 00:26 Berlin): first version, compiled from the two deep-dive reports. No new analysis; no repository changes.
- v1.1 (30 Oct 2026, ~14:00 Berlin), readiness item c3:
  - **M3:** LIKELY → CONFIRMED on 2022–25 history; fix changed from "shrink toward a base rate" (failed the 2025 check) to the multiplicative haircut R-M3k, registered; interim rule adds the 55–60 % reading.
  - **M4:** LIKELY → REAL, NOT EXPLOITABLE. "Early-2026" explanation replaced by "mid-season pattern". Closed without registration. Interim rule narrowed from "+1 to +3 pts at 10+, all positions" to "RB/TE only, ≈ +1 (RB) to +2 (TE) pts at 15+".
  - **New verdict class** "REAL, NOT EXPLOITABLE".
  - **New row M8** (backup QBs projected like starters).
  - **M5 and C4:** notes on overlap with the R-M3k flags.
  - **§4:** M3 factor table added; QB trust row extended.
  - **§5:** R-M3k row added, M4 row closed, note on the Week 7 shadow outcome added.
  - No repository changes.
