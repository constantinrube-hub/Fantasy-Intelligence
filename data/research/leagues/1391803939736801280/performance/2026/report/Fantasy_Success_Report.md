# FIE Fantasy Success, M7-M9 Season Report

This report is fail-closed. A player uses the independent FIE preseason projection only when the position-level year-to-year raw-stat gate cleared, the player has a usable prior-season profile, the league scoring is replayable by the model targets, and team-transfer guardrails permit it. Otherwise the frozen Sleeper season projection remains the market fallback.

## Model status

- M7 validated driver families: 0
- M8 validated matchup families: 0
- M8 sequential M7+M8 position specs: none
- M9 weekly returner candidates: none
- M9 season-return targets: none
- M9 preseason position specs: WR, TE

## Position-level predictive evidence

### QB

**M7 driver evidence:** qb_rush_share_prior4 (opportunity), qb_rush_share_prior4 (rushing_leverage), opportunity_xfp_realized_prior4 (regression), qb_pass_attempt_share_prior4 (opportunity), snap_share_prior4 (opportunity), xfp_residual_prior4 (regression)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_pass_rush_matchup [diagnostic_only], public_coverage_matchup [diagnostic_only]

### RB

**M7 driver evidence:** opportunity_xfp_realized_prior4 (regression), offense_snap_share_prior4 (opportunity), carry_share_prior4 (opportunity), target_share_prior4 (receiving_role), target_share_prior4 (opportunity), backfield_competition_index_prior4 (competition)

**M8 matchup evidence:** insufficient

### WR

**M7 driver evidence:** opportunity_xfp_realized_prior4 (regression), target_share_prior4 (opportunity), offense_snap_share_prior4 (opportunity), receiving_competition_index_prior4 (competition), receiving_competitor_count (competition), red_zone_target_share_prior4 (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

### TE

**M7 driver evidence:** opportunity_xfp_realized_prior4 (regression), target_share_prior4 (opportunity), offense_snap_share_prior4 (opportunity), receiving_competition_index_prior4 (competition), receiving_competitor_count (competition), red_zone_target_share_prior4 (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

## Requested Sleeper market universe

### QB Top 24

| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Josh Allen | 1 | 1 | — | 361.5 | 321.2 | 361.0 | 403.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Lamar Jackson | 2 | 2 | — | 326.0 | 285.3 | 326.0 | 367.1 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Drake Maye | 3 | 3 | — | 320.8 | 279.4 | 320.4 | 361.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Joe Burrow | 4 | 6 | — | 306.1 | 265.7 | 305.8 | 347.1 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jalen Hurts | 5 | 4 | — | 310.5 | 269.9 | 309.9 | 352.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jayden Daniels | 6 | 5 | — | 308.7 | 268.2 | 308.3 | 349.3 | 63% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Caleb Williams | 7 | 10 | — | 299.3 | 259.8 | 298.9 | 339.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Dak Prescott | 8 | 7 | — | 303.9 | 263.9 | 303.2 | 345.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Justin Herbert | 9 | 13 | — | 295.5 | 254.5 | 294.8 | 336.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jaxson Dart | 10 | 11 | — | 296.5 | 257.0 | 296.2 | 336.6 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Matthew Stafford | 11 | 17 | — | 280.2 | 239.9 | 279.6 | 322.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Trevor Lawrence | 12 | 8 | — | 303.4 | 263.0 | 303.0 | 344.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Patrick Mahomes | 13 | 14 | — | 286.7 | 246.5 | 286.0 | 327.7 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Bo Nix | 14 | 12 | — | 295.7 | 255.0 | 295.5 | 337.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Brock Purdy | 15 | 9 | — | 303.2 | 262.5 | 302.7 | 344.9 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jared Goff | 16 | 15 | — | 283.5 | 243.7 | 282.8 | 323.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Baker Mayfield | 17 | 19 | — | 274.9 | 235.4 | 274.5 | 314.9 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jordan Love | 18 | 18 | — | 278.5 | 238.7 | 278.1 | 318.5 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Kyler Murray | 19 | 16 | — | 283.1 | 243.6 | 282.1 | 323.9 | 63% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Sam Darnold | 20 | 22 | — | 262.7 | 222.6 | 262.3 | 303.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Fernando Mendoza | 21 | 28 | — | 212.2 | 174.7 | 211.3 | 251.1 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Tyler Shough | 22 | 20 | — | 270.9 | 231.0 | 270.4 | 310.9 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Malik Willis | 23 | 21 | — | 270.1 | 229.5 | 269.7 | 310.8 | 63% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| C.J. Stroud | 24 | 23 | — | 247.8 | 208.8 | 247.0 | 287.7 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |

### RB Top 36

| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jahmyr Gibbs | 1 | 1 | — | 331.4 | 299.1 | 331.5 | 362.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Bijan Robinson | 2 | 2 | — | 324.9 | 293.3 | 324.8 | 356.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Christian McCaffrey | 3 | 3 | — | 291.0 | 259.5 | 290.6 | 322.9 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jonathan Taylor | 4 | 4 | — | 272.3 | 240.8 | 272.3 | 304.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| James Cook | 5 | 5 | — | 260.8 | 229.4 | 260.5 | 292.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| De'Von Achane | 6 | 6 | — | 257.4 | 225.5 | 257.5 | 288.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Saquon Barkley | 7 | 9 | — | 246.7 | 216.2 | 246.4 | 277.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Ashton Jeanty | 8 | 12 | — | 233.9 | 203.3 | 233.3 | 265.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Omarion Hampton | 9 | 11 | — | 242.9 | 211.7 | 242.8 | 273.8 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Chase Brown | 10 | 7 | — | 255.2 | 224.5 | 254.8 | 286.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Kenneth Walker III | 11 | 10 | — | 244.0 | 212.4 | 243.7 | 275.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Derrick Henry | 12 | 8 | — | 246.9 | 215.9 | 246.7 | 278.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jeremiyah Love | 13 | 13 | — | 211.8 | 180.9 | 211.4 | 243.4 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Kyren Williams | 14 | 15 | — | 208.0 | 177.6 | 207.5 | 239.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Josh Jacobs | 15 | 20 | — | 202.6 | 172.0 | 201.9 | 234.1 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Breece Hall | 16 | 14 | — | 211.0 | 180.4 | 210.8 | 242.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Javonte Williams | 17 | 18 | — | 207.3 | 176.9 | 206.9 | 238.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Bucky Irving | 18 | 22 | — | 197.3 | 166.8 | 196.9 | 228.2 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Cam Skattebo | 19 | 21 | — | 201.2 | 171.2 | 200.8 | 232.2 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Travis Etienne | 20 | 17 | — | 207.7 | 176.9 | 207.2 | 238.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| David Montgomery | 21 | 19 | — | 206.1 | 175.2 | 205.8 | 237.6 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Quinshon Judkins | 22 | 23 | — | 196.0 | 165.9 | 195.7 | 226.5 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| TreVeyon Henderson | 23 | 25 | — | 171.0 | 141.0 | 170.4 | 201.9 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| D'Andre Swift | 24 | 15 | — | 208.0 | 176.7 | 207.2 | 239.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Bhayshul Tuten | 25 | 24 | — | 174.8 | 144.9 | 174.3 | 205.6 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jadarian Price | 26 | 27 | — | 170.0 | 140.8 | 169.3 | 200.6 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jaylen Warren | 27 | 26 | — | 170.6 | 140.5 | 170.2 | 200.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Chuba Hubbard | 28 | 36 | — | 147.9 | 118.6 | 146.9 | 178.0 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| RJ Harvey | 29 | 37 | — | 144.1 | 115.2 | 143.4 | 173.6 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Rhamondre Stevenson | 30 | 28 | — | 169.0 | 139.2 | 168.4 | 199.4 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Tony Pollard | 31 | 31 | — | 160.1 | 130.7 | 159.7 | 190.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Rico Dowdle | 32 | 29 | — | 161.1 | 131.3 | 160.3 | 191.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| J.K. Dobbins | 33 | 30 | — | 160.2 | 130.6 | 159.8 | 189.6 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Kyle Monangai | 34 | 33 | — | 154.6 | 125.3 | 153.8 | 185.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Blake Corum | 35 | 39 | — | 135.3 | 106.6 | 134.8 | 164.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Jonathon Brooks | 36 | 32 | — | 154.9 | 126.5 | 154.3 | 184.1 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |

### WR Top 36

| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 1 | 3 | -2 | 285.8 | 254.2 | 285.3 | 318.1 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +4.34 PPG; prev__receiving_yards +2.61 PPG; offense_snap_share_prior4 -0.18 PPG |
| Puka Nacua | 2 | 1 | — | 312.5 | 280.0 | 312.5 | 344.7 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Jaxon Smith-Njigba | 3 | 2 | 1 | 309.4 | 277.9 | 309.2 | 341.4 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +4.91 PPG; prev__receiving_yards +3.45 PPG; offense_snap_share_prior4 -0.17 PPG; opportunity_change_score_prior1 -0.11 PPG |
| Amon-Ra St. Brown | 4 | 4 | 0 | 278.0 | 246.2 | 277.7 | 310.6 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +4.15 PPG; prev__receiving_yards +2.33 PPG; offense_snap_share_prior4 -0.19 PPG; opportunity_change_score_prior1 -0.16 PPG |
| CeeDee Lamb | 5 | 10 | -5 | 232.8 | 201.7 | 232.3 | 264.6 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.85 PPG; prev__receiving_yards +2.35 PPG; offense_snap_share_prior4 -0.11 PPG; opportunity_change_score_prior1 -0.05 PPG |
| Justin Jefferson | 6 | 19 | -13 | 196.7 | 166.3 | 196.4 | 227.4 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.55 PPG; prev__receiving_yards +1.33 PPG; offense_snap_share_prior4 -0.19 PPG |
| Drake London | 7 | 7 | 0 | 242.2 | 211.4 | 241.5 | 273.5 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +3.34 PPG; prev__receiving_yards +2.05 PPG; offense_snap_share_prior4 -0.18 PPG |
| A.J. Brown | 8 | 6 | — | 247.2 | 216.4 | 246.7 | 278.6 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| George Pickens | 9 | 9 | 0 | 238.5 | 207.5 | 238.2 | 270.1 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +3.46 PPG; prev__receiving_yards +2.41 PPG; offense_snap_share_prior4 -0.16 PPG; prev__rushing_yards -0.05 PPG |
| Nico Collins | 10 | 14 | -4 | 219.8 | 188.3 | 219.4 | 251.1 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.71 PPG; prev__receiving_yards +1.95 PPG; xfp_residual_prior4 -0.13 PPG; offense_snap_share_prior4 -0.12 PPG |
| Malik Nabers | 11 | 16 | -5 | 215.6 | 184.9 | 215.1 | 247.0 | 91% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.42 PPG; prev__receiving_yards +1.62 PPG; offense_snap_share_prior4 -0.21 PPG |
| Rashee Rice | 12 | 5 | 7 | 264.6 | 232.3 | 264.5 | 296.1 | 92% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +4.04 PPG; prev__receiving_yards +1.80 PPG |
| Chris Olave | 13 | 8 | 5 | 240.1 | 208.6 | 239.9 | 272.0 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +3.36 PPG; prev__receiving_yards +1.86 PPG; offense_snap_share_prior4 -0.16 PPG; receiving_competitor_count -0.12 PPG |
| Tee Higgins | 14 | 23 | -9 | 189.3 | 158.9 | 189.0 | 220.6 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.36 PPG; prev__receiving_yards +1.07 PPG; xfp_residual_prior4 -0.14 PPG; offense_snap_share_prior4 -0.06 PPG |
| DeVonta Smith | 15 | 27 | -12 | 180.7 | 150.8 | 180.1 | 211.9 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.55 PPG; prev__receiving_yards +1.21 PPG; receiving_competitor_count -0.16 PPG; offense_snap_share_prior4 -0.13 PPG |
| Tetairoa McMillan | 16 | 25 | -9 | 185.8 | 155.6 | 185.3 | 216.1 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.80 PPG; prev__receiving_yards +1.23 PPG; offense_snap_share_prior4 -0.14 PPG; prev__rushing_yards -0.05 PPG |
| Ladd McConkey | 17 | 39 | -22 | 167.3 | 137.9 | 166.6 | 197.6 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.35 PPG; prev__receiving_yards +0.73 PPG; offense_snap_share_prior4 -0.12 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| Emeka Egbuka | 18 | 31 | -13 | 178.7 | 148.6 | 178.3 | 209.2 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.42 PPG; prev__receiving_yards +1.02 PPG |
| Zay Flowers | 19 | 11 | 8 | 226.5 | 194.7 | 226.4 | 257.9 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.43 PPG; prev__receiving_yards +1.79 PPG; xfp_residual_prior4 -0.15 PPG; offense_snap_share_prior4 -0.14 PPG |
| Garrett Wilson | 20 | 15 | 5 | 215.6 | 184.9 | 215.1 | 246.8 | 91% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.40 PPG; target_share_prior4 +1.24 PPG; offense_snap_share_prior4 -0.20 PPG |
| Jaylen Waddle | 21 | 13 | — | 221.0 | 190.0 | 220.8 | 252.1 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Davante Adams | 22 | 21 | — | 192.5 | 161.4 | 192.2 | 223.9 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Luther Burden III | 23 | 55 | -32 | 139.3 | 110.8 | 138.4 | 169.1 | 93% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +0.45 PPG; target_share_prior4 +0.43 PPG; opportunity_change_score_prior1 -0.13 PPG; xfp_residual_prior4 -0.11 PPG |
| Terry McLaurin | 24 | 35 | -11 | 172.3 | 142.2 | 171.7 | 203.0 | 92% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.39 PPG; prev__receiving_yards +1.16 PPG; offense_snap_share_prior4 -0.11 PPG; opportunity_change_score_prior1 -0.10 PPG |
| DJ Moore | 25 | 30 | — | 179.0 | 149.3 | 178.5 | 209.8 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Jameson Williams | 26 | 22 | 4 | 189.4 | 158.7 | 188.8 | 220.7 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.94 PPG; prev__receiving_yards +1.52 PPG; offense_snap_share_prior4 -0.18 PPG; red_zone_target_share_prior4 -0.08 PPG |
| Mike Evans | 27 | 12 | — | 222.2 | 191.0 | 221.7 | 253.4 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Rome Odunze | 28 | 28 | 0 | 180.2 | 149.9 | 179.6 | 211.2 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.66 PPG; prev__receiving_yards +1.01 PPG; offense_snap_share_prior4 -0.15 PPG |
| Carnell Tate | 29 | 32 | — | 177.3 | 147.3 | 176.9 | 208.4 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Christian Watson | 30 | 24 | 6 | 188.6 | 157.9 | 188.0 | 220.3 | 92% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +2.05 PPG; prev__receiving_yards +1.30 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| Brian Thomas Jr. | 31 | 47 | -16 | 153.7 | 124.4 | 153.3 | 183.4 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +0.85 PPG; prev__receiving_yards +0.79 PPG; offense_snap_share_prior4 -0.12 PPG; prev__receiving_tds -0.04 PPG |
| DK Metcalf | 32 | 26 | 6 | 183.4 | 153.2 | 182.7 | 214.6 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.77 PPG; prev__receiving_yards +1.09 PPG; offense_snap_share_prior4 -0.15 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| Marvin Harrison Jr. | 33 | 41 | -8 | 165.6 | 135.7 | 165.1 | 195.8 | 93% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.11 PPG; prev__receiving_yards +0.80 PPG; offense_snap_share_prior4 -0.07 PPG |
| Parker Washington | 34 | 40 | -6 | 167.2 | 137.6 | 166.6 | 197.5 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.25 PPG; prev__receiving_yards +0.91 PPG; xfp_residual_prior4 -0.08 PPG |
| Courtland Sutton | 35 | 17 | 18 | 202.0 | 171.7 | 201.8 | 232.6 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.93 PPG; prev__receiving_yards +1.24 PPG; offense_snap_share_prior4 -0.14 PPG; opportunity_change_score_prior1 -0.11 PPG |
| Michael Wilson | 36 | 20 | 16 | 193.6 | 162.6 | 193.1 | 224.5 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.95 PPG; prev__receiving_yards +1.21 PPG; offense_snap_share_prior4 -0.15 PPG; xfp_residual_prior4 -0.13 PPG |

### TE Top 24

| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Trey McBride | 1 | 1 | 0 | 253.3 | 227.3 | 252.9 | 279.7 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +2.70 PPG; prev_fantasy_ppg +2.31 PPG; opportunity_change_score_prior1 -0.73 PPG |
| Brock Bowers | 2 | 4 | -2 | 201.7 | 176.8 | 201.5 | 227.1 | 93% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.70 PPG; prev_fantasy_ppg +1.64 PPG |
| Colston Loveland | 3 | 19 | -16 | 145.6 | 121.6 | 145.1 | 170.0 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.18 PPG; prev__receiving_yards +1.04 PPG; receiving_competition_index_prior4 -0.31 PPG; opportunity_change_score_prior1 -0.29 PPG |
| Tyler Warren | 4 | 7 | -3 | 183.9 | 159.1 | 183.6 | 209.1 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.51 PPG; prev__receiving_yards +1.19 PPG |
| Sam LaPorta | 5 | 8 | -3 | 176.3 | 151.5 | 176.1 | 201.3 | 92% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.47 PPG; target_share_prior4 +1.43 PPG; xfp_residual_prior4 -0.17 PPG |
| Tucker Kraft | 6 | 6 | 0 | 189.3 | 164.1 | 189.0 | 215.0 | 92% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.77 PPG; prev_fantasy_ppg +1.63 PPG; opportunity_change_score_prior1 -0.30 PPG |
| Harold Fannin Jr. | 7 | 5 | 2 | 191.2 | 166.0 | 191.0 | 216.1 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +2.40 PPG; prev_fantasy_ppg +1.12 PPG; opportunity_change_score_prior1 -0.41 PPG |
| Kyle Pitts | 8 | 3 | 5 | 205.5 | 180.2 | 205.5 | 230.8 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +2.26 PPG; prev__receiving_yards +1.48 PPG; xfp_residual_prior4 -0.18 PPG |
| Dalton Kincaid | 9 | 23 | -14 | 129.3 | 105.7 | 128.8 | 153.4 | 93% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.17 PPG; prev_fantasy_ppg +0.92 PPG; offense_snap_share_prior4 -0.19 PPG; red_zone_target_share_prior4 -0.11 PPG |
| George Kittle | 10 | 2 | 8 | 212.2 | 186.8 | 212.0 | 237.3 | 92% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +2.26 PPG; prev_fantasy_ppg +1.64 PPG |
| Travis Kelce | 11 | 10 | 1 | 171.3 | 146.4 | 171.2 | 196.2 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.73 PPG; prev__receiving_yards +1.28 PPG; opportunity_change_score_prior1 -0.38 PPG |
| Jake Ferguson | 12 | 13 | -1 | 157.9 | 133.0 | 157.7 | 183.0 | 94% | FIE_M9_VALIDATED_PRESEASON | prev_fantasy_ppg +1.01 PPG; opportunity_change_score_prior1 +0.99 PPG |
| Isaiah Likely | 13 | 14 | — | 157.3 | 132.9 | 156.9 | 181.7 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Dallas Goedert | 14 | 12 | 2 | 164.7 | 139.7 | 164.5 | 189.7 | 93% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.71 PPG; prev_fantasy_ppg +1.24 PPG; opportunity_change_score_prior1 -0.86 PPG |
| Oronde Gadsden II | 15 | 18 | -3 | 146.2 | 121.9 | 146.1 | 170.7 | 93% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.02 PPG; target_share_prior4 +0.63 PPG |
| Mark Andrews | 16 | 28 | -12 | 124.8 | 101.0 | 124.4 | 149.5 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.31 PPG; prev_fantasy_ppg +0.43 PPG; opportunity_change_score_prior1 -0.10 PPG |
| Hunter Henry | 17 | 15 | 2 | 157.2 | 132.5 | 156.7 | 182.4 | 94% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.06 PPG; prev_fantasy_ppg +0.92 PPG |
| Brenton Strange | 18 | 21 | -3 | 141.3 | 117.0 | 141.1 | 165.8 | 93% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.05 PPG; target_share_prior4 +0.87 PPG; pfr_receiving_drop_pct_prior4 -0.24 PPG; opportunity_change_score_prior1 -0.11 PPG |
| Kenyon Sadiq | 19 | 37 | — | 100.2 | 77.7 | 99.6 | 123.4 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| T.J. Hockenson | 20 | 27 | -7 | 127.9 | 104.4 | 127.5 | 152.1 | 93% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.33 PPG; prev_fantasy_ppg +0.40 PPG; opportunity_change_score_prior1 -0.26 PPG |
| AJ Barner | 21 | 26 | -5 | 128.2 | 104.6 | 128.2 | 152.4 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +0.76 PPG; prev_fantasy_ppg +0.60 PPG; opportunity_change_score_prior1 -0.30 PPG |
| Chig Okonkwo | 22 | 20 | — | 144.1 | 120.3 | 143.9 | 168.4 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed |
| Juwan Johnson | 23 | 11 | 12 | 165.0 | 140.2 | 164.7 | 190.0 | 94% | FIE_M9_VALIDATED_PRESEASON | prev__receiving_yards +1.38 PPG; target_share_prior4 +0.98 PPG; receiving_competition_index_prior4 -0.24 PPG |
| Dalton Schultz | 24 | 9 | 15 | 172.6 | 147.9 | 172.4 | 197.3 | 94% | FIE_M9_VALIDATED_PRESEASON | target_share_prior4 +1.25 PPG; prev__receiving_yards +1.09 PPG |

## Largest FIE vs Sleeper ranking differences

| Player | Pos | Sleeper rank | FIE rank | Edge | Mean | P10 | P90 | Confidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Luther Burden III | WR | 23 | 55 | -32 | 139.3 | 110.8 | 169.1 | 93% | prev__receiving_yards +0.45 PPG; target_share_prior4 +0.43 PPG; opportunity_change_score_prior1 -0.13 PPG; xfp_residual_prior4 -0.11 PPG |
| Ladd McConkey | WR | 17 | 39 | -22 | 167.3 | 137.9 | 197.6 | 94% | prev_fantasy_ppg +1.35 PPG; prev__receiving_yards +0.73 PPG; offense_snap_share_prior4 -0.12 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| Courtland Sutton | WR | 35 | 17 | 18 | 202.0 | 171.7 | 232.6 | 94% | prev_fantasy_ppg +1.93 PPG; prev__receiving_yards +1.24 PPG; offense_snap_share_prior4 -0.14 PPG; opportunity_change_score_prior1 -0.11 PPG |
| Michael Wilson | WR | 36 | 20 | 16 | 193.6 | 162.6 | 224.5 | 94% | prev_fantasy_ppg +1.95 PPG; prev__receiving_yards +1.21 PPG; offense_snap_share_prior4 -0.15 PPG; xfp_residual_prior4 -0.13 PPG |
| Brian Thomas Jr. | WR | 31 | 47 | -16 | 153.7 | 124.4 | 183.4 | 93% | prev_fantasy_ppg +0.85 PPG; prev__receiving_yards +0.79 PPG; offense_snap_share_prior4 -0.12 PPG; prev__receiving_tds -0.04 PPG |
| Colston Loveland | TE | 3 | 19 | -16 | 145.6 | 121.6 | 170.0 | 94% | target_share_prior4 +1.18 PPG; prev__receiving_yards +1.04 PPG; receiving_competition_index_prior4 -0.31 PPG; opportunity_change_score_prior1 -0.29 PPG |
| Dalton Schultz | TE | 24 | 9 | 15 | 172.6 | 147.9 | 197.3 | 94% | target_share_prior4 +1.25 PPG; prev__receiving_yards +1.09 PPG |
| Dalton Kincaid | TE | 9 | 23 | -14 | 129.3 | 105.7 | 153.4 | 93% | prev__receiving_yards +1.17 PPG; prev_fantasy_ppg +0.92 PPG; offense_snap_share_prior4 -0.19 PPG; red_zone_target_share_prior4 -0.11 PPG |
| Emeka Egbuka | WR | 18 | 31 | -13 | 178.7 | 148.6 | 209.2 | 94% | prev_fantasy_ppg +1.42 PPG; prev__receiving_yards +1.02 PPG |
| Justin Jefferson | WR | 6 | 19 | -13 | 196.7 | 166.3 | 227.4 | 94% | prev_fantasy_ppg +1.55 PPG; prev__receiving_yards +1.33 PPG; offense_snap_share_prior4 -0.19 PPG |
| DeVonta Smith | WR | 15 | 27 | -12 | 180.7 | 150.8 | 211.9 | 94% | prev_fantasy_ppg +1.55 PPG; prev__receiving_yards +1.21 PPG; receiving_competitor_count -0.16 PPG; offense_snap_share_prior4 -0.13 PPG |
| Juwan Johnson | TE | 23 | 11 | 12 | 165.0 | 140.2 | 190.0 | 94% | prev__receiving_yards +1.38 PPG; target_share_prior4 +0.98 PPG; receiving_competition_index_prior4 -0.24 PPG |
| Mark Andrews | TE | 16 | 28 | -12 | 124.8 | 101.0 | 149.5 | 94% | target_share_prior4 +1.31 PPG; prev_fantasy_ppg +0.43 PPG; opportunity_change_score_prior1 -0.10 PPG |
| Terry McLaurin | WR | 24 | 35 | -11 | 172.3 | 142.2 | 203.0 | 92% | prev_fantasy_ppg +1.39 PPG; prev__receiving_yards +1.16 PPG; offense_snap_share_prior4 -0.11 PPG; opportunity_change_score_prior1 -0.10 PPG |
| Tetairoa McMillan | WR | 16 | 25 | -9 | 185.8 | 155.6 | 216.1 | 94% | prev_fantasy_ppg +1.80 PPG; prev__receiving_yards +1.23 PPG; offense_snap_share_prior4 -0.14 PPG; prev__rushing_yards -0.05 PPG |
| Tee Higgins | WR | 14 | 23 | -9 | 189.3 | 158.9 | 220.6 | 93% | prev_fantasy_ppg +2.36 PPG; prev__receiving_yards +1.07 PPG; xfp_residual_prior4 -0.14 PPG; offense_snap_share_prior4 -0.06 PPG |
| Marvin Harrison Jr. | WR | 33 | 41 | -8 | 165.6 | 135.7 | 195.8 | 93% | prev_fantasy_ppg +1.11 PPG; prev__receiving_yards +0.80 PPG; offense_snap_share_prior4 -0.07 PPG |
| Zay Flowers | WR | 19 | 11 | 8 | 226.5 | 194.7 | 257.9 | 94% | prev_fantasy_ppg +2.43 PPG; prev__receiving_yards +1.79 PPG; xfp_residual_prior4 -0.15 PPG; offense_snap_share_prior4 -0.14 PPG |
| George Kittle | TE | 10 | 2 | 8 | 212.2 | 186.8 | 237.3 | 92% | target_share_prior4 +2.26 PPG; prev_fantasy_ppg +1.64 PPG |
| Rashee Rice | WR | 12 | 5 | 7 | 264.6 | 232.3 | 296.1 | 92% | prev_fantasy_ppg +4.04 PPG; prev__receiving_yards +1.80 PPG |
| T.J. Hockenson | TE | 20 | 27 | -7 | 127.9 | 104.4 | 152.1 | 93% | target_share_prior4 +1.33 PPG; prev_fantasy_ppg +0.40 PPG; opportunity_change_score_prior1 -0.26 PPG |
| Christian Watson | WR | 30 | 24 | 6 | 188.6 | 157.9 | 220.3 | 92% | prev_fantasy_ppg +2.05 PPG; prev__receiving_yards +1.30 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| DK Metcalf | WR | 32 | 26 | 6 | 183.4 | 153.2 | 214.6 | 93% | prev_fantasy_ppg +1.77 PPG; prev__receiving_yards +1.09 PPG; offense_snap_share_prior4 -0.15 PPG; pfr_receiving_drop_pct_prior4 -0.08 PPG |
| Parker Washington | WR | 34 | 40 | -6 | 167.2 | 137.6 | 197.5 | 94% | prev_fantasy_ppg +1.25 PPG; prev__receiving_yards +0.91 PPG; xfp_residual_prior4 -0.08 PPG |
| Malik Nabers | WR | 11 | 16 | -5 | 215.6 | 184.9 | 247.0 | 91% | prev_fantasy_ppg +2.42 PPG; prev__receiving_yards +1.62 PPG; offense_snap_share_prior4 -0.21 PPG |
| CeeDee Lamb | WR | 5 | 10 | -5 | 232.8 | 201.7 | 264.6 | 93% | prev_fantasy_ppg +2.85 PPG; prev__receiving_yards +2.35 PPG; offense_snap_share_prior4 -0.11 PPG; opportunity_change_score_prior1 -0.05 PPG |
| Kyle Pitts | TE | 8 | 3 | 5 | 205.5 | 180.2 | 230.8 | 94% | target_share_prior4 +2.26 PPG; prev__receiving_yards +1.48 PPG; xfp_residual_prior4 -0.18 PPG |
| Chris Olave | WR | 13 | 8 | 5 | 240.1 | 208.6 | 272.0 | 94% | prev_fantasy_ppg +3.36 PPG; prev__receiving_yards +1.86 PPG; offense_snap_share_prior4 -0.16 PPG; receiving_competitor_count -0.12 PPG |
| AJ Barner | TE | 21 | 26 | -5 | 128.2 | 104.6 | 152.4 | 94% | target_share_prior4 +0.76 PPG; prev_fantasy_ppg +0.60 PPG; opportunity_change_score_prior1 -0.30 PPG |
| Garrett Wilson | WR | 20 | 15 | 5 | 215.6 | 184.9 | 246.8 | 91% | prev_fantasy_ppg +2.40 PPG; target_share_prior4 +1.24 PPG; offense_snap_share_prior4 -0.20 PPG |

## Sleeper candidates outside the requested market cutoffs

| Player | Pos | Sleeper rank | FIE rank | Edge | Mean | P10 | P90 | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Hunter Renfrow | WR | 606 | 99 | 507 | 88.5 | 62.4 | 116.1 | prev__receiving_tds +0.08 PPG; prev__receiving_yards -0.94 PPG; prev_fantasy_ppg -0.57 PPG |
| Justin Watson | WR | 613 | 167 | 446 | 44.4 | 21.9 | 68.5 | prev_fantasy_ppg -2.01 PPG; prev__receiving_yards -1.17 PPG |
| Allen Lazard | WR | 609 | 164 | 445 | 45.9 | 22.7 | 70.7 | offense_snap_share_prior4 +0.07 PPG; prev_fantasy_ppg -1.81 PPG; prev__receiving_yards -1.28 PPG |
| Jonathan Mingo | WR | 634 | 190 | 444 | 31.8 | 10.2 | 54.7 | pfr_receiving_drop_pct_prior4 +0.39 PPG; offense_snap_share_prior4 +0.19 PPG; prev_fantasy_ppg -2.48 PPG; prev__receiving_yards -1.41 PPG |
| Jared Wayne | WR | 556 | 118 | 438 | 73.3 | 48.5 | 99.5 | prev_fantasy_ppg -1.29 PPG; prev__receiving_yards -0.69 PPG |
| Ronnie Bell | WR | 571 | 140 | 431 | 63.7 | 39.2 | 89.4 | prev__receiving_tds +0.18 PPG; prev__receiving_yards -1.10 PPG; prev_fantasy_ppg -0.87 PPG |
| Curtis Samuel | WR | 587 | 158 | 429 | 50.9 | 27.7 | 75.2 | offense_snap_share_prior4 +0.08 PPG; prev_fantasy_ppg -1.46 PPG; prev__receiving_yards -1.00 PPG |
| Bo Melton | WR | 610 | 182 | 428 | 37.0 | 15.2 | 60.3 | offense_snap_share_prior4 +0.20 PPG; prev_fantasy_ppg -2.06 PPG; prev__receiving_yards -1.25 PPG |
| Jalen Brooks | WR | 595 | 171 | 424 | 41.4 | 18.9 | 65.2 | pfr_receiving_drop_pct_prior4 +0.23 PPG; offense_snap_share_prior4 +0.12 PPG; prev_fantasy_ppg -2.15 PPG; prev__receiving_yards -1.16 PPG |
| Xavier Restrepo | WR | 524 | 123 | 401 | 71.0 | 46.3 | 97.5 | receiving_competitor_count +0.12 PPG; prev_fantasy_ppg -1.45 PPG; prev__receiving_yards -0.66 PPG |
| Brock Wright | TE | 280 | 41 | 239 | 83.7 | 61.8 | 106.6 | receiving_competitor_count +0.20 PPG; opportunity_change_score_prior1 +0.11 PPG; prev__receiving_yards -0.35 PPG; prev_fantasy_ppg -0.10 PPG |
| Will Mallory | TE | 298 | 72 | 226 | 51.4 | 31.7 | 71.9 | pfr_receiving_drop_pct_prior4 +0.09 PPG; target_share_prior4 -0.74 PPG; prev_fantasy_ppg -0.45 PPG |
| Josh Whyle | TE | 290 | 65 | 225 | 55.4 | 36.0 | 76.5 | receiving_competitor_count +0.69 PPG; pfr_receiving_drop_pct_prior4 +0.09 PPG; target_share_prior4 -0.74 PPG; prev__receiving_yards -0.68 PPG |
| Grant Calcaterra | TE | 275 | 55 | 220 | 61.9 | 41.6 | 82.9 | receiving_competitor_count +0.53 PPG; opportunity_change_score_prior1 +0.42 PPG; target_share_prior4 -0.75 PPG; prev__receiving_yards -0.57 PPG |
| Adam Trautman | TE | 271 | 52 | 219 | 63.1 | 42.6 | 84.7 | receiving_competition_index_prior4 +0.16 PPG; offense_snap_share_prior4 +0.14 PPG; target_share_prior4 -0.48 PPG; prev_fantasy_ppg -0.29 PPG |

## Interpretation rules

- Positive Edge means FIE ranks the player earlier within his position than the frozen Sleeper market.
- P10/P90 come from empirically calibrated historical OOS weekly residuals, not a fixed percentage around the mean.
- `MARKET_FALLBACK` is not a hidden FIE opinion. It means the new independent preseason model was not eligible for that row.
- M8 opponent/trench effects do not stack onto M7 merely because both validate independently. A sequential/joint gate is required before live stacking.
- Individual return yards/TDs enter a FIE season projection only when the league scores them and the matching M9 season-return target has independently cleared its gate.
- Individual WR-DB and blocker-rusher labels remain blocked without auditable assignment/responsibility history.