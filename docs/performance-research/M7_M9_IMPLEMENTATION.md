# FIE M7-M9 Performance Research Extension

## Purpose

M7-M9 extends the existing league-specific M1-M6 research architecture without replacing its scoring, governance, D/ST, kicker, or runtime contracts.

The extension answers four questions:

1. Which underlying QB/RB/WR/TE metrics predict future fantasy production after the existing FIE projection has already been considered?
2. Do offensive line, pass rush, coverage, and run-front environments add repeatable opponent-specific information?
3. Who is likely to return kicks/punts, how much raw return production should be expected, and does the league actually score it?
4. Can FIE generate a separately validated preseason season projection and calibrated P10/P25/P50/P75/P90 distribution instead of multiplying an in-season weekly model by 17?

## Milestone 7: Position performance drivers

M7 rebuilds the canonical time-safe M3/M4 feature frame and evaluates QB, RB, WR, and TE driver families.

Each family is tested as an incremental residual model on top of historical out-of-sample M4 FIE projections. Descriptive correlation is reported, but it cannot activate a feature.

The gate requires chronological folds, positive mean out-of-sample MAE improvement, and a positive bootstrap confidence interval. Independently validated families then face a joint/composite gate before multiple families may be stacked.

Optional point-in-time player charting can be supplied for route participation, targets per route, first-read share, YPRR, separation, TE pass-block usage/alignment, and QB coverage/pressure splits. Realised Week N charting is always shifted before it can predict Week N+1.

## Milestone 8: Team, trench, defense, and matchup intelligence

M8 deliberately distinguishes public environment proxies from true OL/DL charting.

Public baseline components include:

- offensive pressure/sack environment,
- defensive pass-rush production,
- coverage disruption,
- man/zone context,
- run-front disruption.

These support QB x pass-rush, QB x coverage, RB x run front, WR/TE x pass rush, and WR/TE x coverage residual challengers.

After individual M8 families are screened, M8 performs a second sequential gate. If M7 has a validated composite, the challenger compares a chronologically retrained M7-only residual model against one combined M7+M8 model. Only the combined model may be serialized for runtime use. It replaces the M7-only correction rather than stacking another point adjustment on top of it.

Optional true team OL/DL data can be supplied separately. Optional player-week OL/DL data is aggregated to the team with workload weights when charted snap counts exist. A weak-link metric is exported separately rather than hidden inside the unit average.

Individual WR-DB responsibility and blocker-rusher matchup effects stay blocked unless auditable assignment-level history is supplied. Nearest defender, nominal CB1, or depth-chart order is not accepted as a substitute.

## Milestone 9: Returners, preseason projection, and uncertainty

M9 reconstructs player kick/punt return attempts, yards, and touchdowns from point-in-time play-by-play when player return IDs exist.

It independently validates:

- primary-returner probability,
- weekly return-yard expectation,
- prior-season to next-season KR yards,
- prior-season to next-season PR yards,
- prior-season to next-season KR touchdowns,
- prior-season to next-season PR touchdowns.

Return production only changes fantasy value when the league contains a supported non-zero individual return scoring key and the required return target model cleared its own gate.

The preseason offense model is separate from the weekly FIE model. It predicts next-season per-game raw football outcomes from the prior-season profile, replays those raw outcomes through the league scoring settings, and validates by target season. Changed-team players fail closed because team/role transfer is not yet learned by this portability model.

Historical out-of-sample weekly FIE errors calibrate the season simulation. The simulation uses a deterministic seed and heavy-tailed weekly residuals to produce P10/P25/P50/P75/P90.

## Season comparison report

The report freezes a Sleeper season market snapshot before comparing FIE against the market. It produces:

- Sleeper Top 24 QB,
- Sleeper Top 36 RB,
- Sleeper Top 36 WR,
- Sleeper Top 24 TE,
- up to 5 QB sleeper candidates outside the cutoff,
- up to 10 RB sleeper candidates,
- up to 10 WR sleeper candidates,
- up to 5 TE sleeper candidates.

Each row includes FIE season mean, P10/P25/P50/P75/P90, FIE position rank, frozen Sleeper market rank, rank edge, confidence, projection source, scoring coverage, and the largest model-driver contributions when available.

`MARKET_FALLBACK` is not an FIE opinion. It means the independent FIE preseason contract was not eligible for that player/position/scoring profile. Rank edge is deliberately null for fallback rows.

## Production boundary

M7-M9 is research/evaluation infrastructure first. It does not silently modify the current production weekly player ranking path.

A later runtime integration should consume only features that pass the historical gates and should keep the existing fail-closed governance semantics. M7 and M8 effects must not be stacked merely because each validates independently; the combined consumer needs its own sequential/joint validation gate.
