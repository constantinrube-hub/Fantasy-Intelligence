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
| Ja'Marr Chase | 1 | 2 | — | 311.1 | 279.3 | 310.6 | 343.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Puka Nacua | 2 | 1 | — | 312.5 | 280.0 | 312.5 | 344.7 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Jaxon Smith-Njigba | 3 | 3 | — | 284.6 | 253.3 | 284.4 | 316.6 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Amon-Ra St. Brown | 4 | 4 | — | 280.5 | 248.6 | 280.1 | 313.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| CeeDee Lamb | 5 | 5 | — | 270.5 | 239.0 | 270.1 | 302.6 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Justin Jefferson | 6 | 7 | — | 250.4 | 218.8 | 250.4 | 281.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Drake London | 7 | 8 | — | 250.2 | 219.3 | 249.6 | 281.6 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| A.J. Brown | 8 | 9 | — | 247.2 | 216.4 | 246.7 | 278.6 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| George Pickens | 9 | 10 | — | 245.7 | 214.7 | 245.5 | 277.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Nico Collins | 10 | 6 | — | 262.0 | 229.8 | 261.8 | 293.7 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Malik Nabers | 11 | 11 | — | 236.7 | 205.8 | 236.3 | 268.3 | 63% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Rashee Rice | 12 | 13 | — | 229.3 | 197.7 | 229.1 | 260.7 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Chris Olave | 13 | 12 | — | 235.9 | 204.6 | 235.8 | 267.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Tee Higgins | 14 | 18 | — | 224.4 | 193.2 | 224.2 | 256.3 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| DeVonta Smith | 15 | 14 | — | 229.2 | 198.2 | 228.9 | 261.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Tetairoa McMillan | 16 | 20 | — | 223.0 | 192.1 | 222.5 | 253.8 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Ladd McConkey | 17 | 16 | — | 228.2 | 197.4 | 227.7 | 259.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Emeka Egbuka | 18 | 19 | — | 224.0 | 192.8 | 223.7 | 255.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Zay Flowers | 19 | 15 | — | 228.2 | 196.5 | 228.2 | 259.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Garrett Wilson | 20 | 17 | — | 224.9 | 194.1 | 224.4 | 256.2 | 63% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Jaylen Waddle | 21 | 22 | — | 221.0 | 190.0 | 220.8 | 252.1 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Davante Adams | 22 | 31 | — | 192.5 | 161.4 | 192.2 | 223.9 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Luther Burden III | 23 | 25 | — | 209.0 | 178.5 | 208.3 | 240.3 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Terry McLaurin | 24 | 23 | — | 213.8 | 182.6 | 213.1 | 245.2 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| DJ Moore | 25 | 34 | — | 179.0 | 149.3 | 178.5 | 209.8 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Jameson Williams | 26 | 28 | — | 206.2 | 175.0 | 205.6 | 237.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Mike Evans | 27 | 21 | — | 222.2 | 191.0 | 221.7 | 253.4 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Rome Odunze | 28 | 26 | — | 207.9 | 177.1 | 207.2 | 239.3 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Carnell Tate | 29 | 36 | — | 177.3 | 147.3 | 176.9 | 208.4 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| Christian Watson | 30 | 27 | — | 207.6 | 176.4 | 207.1 | 239.4 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Brian Thomas Jr. | 31 | 30 | — | 195.4 | 165.0 | 195.3 | 226.0 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| DK Metcalf | 32 | 33 | — | 183.3 | 153.1 | 182.7 | 214.5 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Marvin Harrison Jr. | 33 | 32 | — | 186.2 | 155.6 | 185.8 | 216.9 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Parker Washington | 34 | 24 | — | 212.4 | 181.7 | 211.9 | 243.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Courtland Sutton | 35 | 37 | — | 174.3 | 144.6 | 173.8 | 204.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |
| Michael Wilson | 36 | 47 | — | 166.0 | 135.8 | 165.4 | 196.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt/rush_td/rush_yd |

### TE Top 24

| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Trey McBride | 1 | 2 | — | 234.9 | 209.0 | 234.5 | 261.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Brock Bowers | 2 | 1 | — | 253.5 | 228.4 | 253.3 | 279.1 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Colston Loveland | 3 | 3 | — | 215.4 | 190.3 | 215.1 | 240.7 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Tyler Warren | 4 | 4 | — | 201.1 | 176.2 | 200.8 | 226.4 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Sam LaPorta | 5 | 5 | — | 196.5 | 171.5 | 196.3 | 221.7 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Tucker Kraft | 6 | 7 | — | 174.4 | 149.4 | 174.0 | 199.8 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Harold Fannin Jr. | 7 | 6 | — | 180.4 | 155.4 | 180.1 | 205.2 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Kyle Pitts | 8 | 8 | — | 171.6 | 146.8 | 171.6 | 196.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Dalton Kincaid | 9 | 11 | — | 163.6 | 138.9 | 163.3 | 188.4 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| George Kittle | 10 | 10 | — | 169.3 | 144.6 | 169.1 | 194.2 | 64% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Travis Kelce | 11 | 9 | — | 171.4 | 146.5 | 171.3 | 196.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Jake Ferguson | 12 | 14 | — | 159.8 | 134.8 | 159.6 | 185.0 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Isaiah Likely | 13 | 15 | — | 157.3 | 132.9 | 156.9 | 181.7 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt |
| Dallas Goedert | 14 | 23 | — | 136.0 | 111.9 | 135.8 | 160.5 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Oronde Gadsden II | 15 | 21 | — | 141.8 | 117.7 | 141.7 | 166.3 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Mark Andrews | 16 | 12 | — | 162.5 | 137.5 | 162.1 | 187.9 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Hunter Henry | 17 | 17 | — | 153.5 | 128.9 | 153.0 | 178.6 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Brenton Strange | 18 | 13 | — | 161.0 | 136.2 | 160.9 | 185.8 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Kenyon Sadiq | 19 | 31 | — | 100.2 | 77.7 | 99.6 | 123.4 | 62% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: no_validated_preseason_spec |
| T.J. Hockenson | 20 | 16 | — | 155.0 | 130.6 | 154.7 | 179.8 | 65% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| AJ Barner | 21 | 20 | — | 142.4 | 118.4 | 142.4 | 167.1 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Chig Okonkwo | 22 | 19 | — | 144.1 | 120.3 | 143.9 | 168.4 | 55% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; team change: prior-team role features fail closed; scoring gaps: fum_lost/rec_2pt |
| Juwan Johnson | 23 | 22 | — | 140.9 | 116.6 | 140.5 | 165.5 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |
| Dalton Schultz | 24 | 18 | — | 150.9 | 126.6 | 150.6 | 175.3 | 66% | MARKET_FALLBACK | market fallback: preseason FIE gate/player profile unavailable; scoring gaps: fum_lost/rec_2pt |

## Largest FIE vs Sleeper ranking differences

| Player | Pos | Sleeper rank | FIE rank | Edge | Mean | P10 | P90 | Confidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|

## Sleeper candidates outside the requested market cutoffs

No qualified FIE-vs-market sleeper edges were available under the current gates.

## Interpretation rules

- Positive Edge means FIE ranks the player earlier within his position than the frozen Sleeper market.
- P10/P90 come from empirically calibrated historical OOS weekly residuals, not a fixed percentage around the mean.
- `MARKET_FALLBACK` is not a hidden FIE opinion. It means the new independent preseason model was not eligible for that row.
- M8 opponent/trench effects do not stack onto M7 merely because both validate independently. A sequential/joint gate is required before live stacking.
- Individual return yards/TDs enter a FIE season projection only when the league scores them and the matching M9 season-return target has independently cleared its gate.
- Individual WR-DB and blocker-rusher labels remain blocked without auditable assignment/responsibility history.