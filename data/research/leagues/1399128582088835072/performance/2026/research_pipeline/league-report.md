# FIE League Research Report — AEF - FFLeague

Season: **2026**  
League ID: `1399128582088835072`  
Format: **REDRAFT**  
Teams: **8**  
Roster: `QB, RB, RB, WR, WR, TE, TE, FLEX, FLEX, SUPER_FLEX, K, DEF, BN, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_2qb`  
Pipeline: **complete_research_only**

## Model overview

| Position | Selected Model | Research Challenger | Validation Status | Exact Scoring | Key Reason |
|---|---|---|---|---|---|
| DST | FIE_DST_DEDICATED | — | PRODUCTION_EXISTING | True | existing_dedicated_specialist_engine |
| K | FIE_KICKER_DEDICATED | — | PRODUCTION_EXISTING | True | existing_dedicated_specialist_engine |
| QB | M9 | V9.7.5 | BLOCKED_STATISTICS | False | one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared |
| RB | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| TE | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| WR | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |

## League/scoring overview

PPR: **PPR** (1 per reception)  
Pass TD: **4** · Pass INT: **-2**  
Fumble: **0** · Fumble lost: **-2**  
Superflex/2QB: **Yes** · D/ST: **Yes** · K: **Yes**

Bonuses: `{"bonus_rec_te": 0.5, "bonus_rush_td_qb": -2.0}`

### How to read Projection Basis

- **M9 production**: the displayed point estimate and P10-P90 come from the validated M9 production view.
- **M9 diagnostic**: production is unavailable for that player, so the canonical league-value layer uses M9's governed market-anchored diagnostic view; its matching diagnostic P10-P90 is shown.
- **Weekly specialist**: D/ST or kicker projection from the dedicated current-week engine.
- Research challengers remain shadow-only and do not replace these displayed canonical values.

## Position-by-position evaluation

### QB

Selected model: **M9**  
Research challenger: **V9.7.5**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **False**  
Reason: one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared  
League replacement: **203.4**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 295.3 | 254.2 | 336.3 | 92 | 3.6 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 76.8 | 60.9 | 15 | 13 | VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 69.7 | 82.2 | 19 | 16 | VALUE | M9 diagnostic |
| 4 | Drake Maye | NE | 264.5 | 224.7 | 305.6 | 61.1 | 11.2 | 3 | -1 | FAIR | M9 diagnostic |
| 5 | Malik Willis | MIA | 261.1 | 221.9 | 301.9 | 57.7 | 104.9 | 23 | 18 | STRONG_VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 257.2 | 216.8 | 297.6 | 53.8 | 55.9 | 14 | 8 | VALUE | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 253.1 | 213.4 | 293.3 | 49.7 | 44.4 | 12 | 5 | FAIR | M9 diagnostic |
| 8 | Dak Prescott | DAL | 235.6 | 195.5 | 276.4 | 32.2 | 35.6 | 9 | 1 | FAIR | M9 diagnostic |
| 9 | Jalen Hurts | PHI | 234.2 | 194.2 | 274.3 | 30.8 | 28.7 | 7 | -2 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 229.8 | 189 | 271 | 26.4 | 40.5 | 10 | 0 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **177.7**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308 | 276.3 | 339.9 | 130.3 | 7 | 3 | 2 | FAIR | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.3 | 253.9 | 318.9 | 108.5 | 2 | 2 | 0 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268 | 236 | 300.6 | 90.2 | 1.8 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 264.9 | 233.3 | 295.8 | 87.1 | 8 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 264.6 | 232.5 | 296.3 | 86.8 | 16.4 | 6 | 1 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.3 | 275.9 | 66.3 | 22.3 | 9 | 3 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 237.4 | 205.8 | 269.4 | 59.6 | 12.4 | 5 | -2 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 228.6 | 197.1 | 259.9 | 50.8 | 25.3 | 11 | 3 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 181.2 | 242.8 | 34.1 | 33.4 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.5 | 238.9 | 30.3 | 38.6 | 14 | 4 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 30 | 58.2 | 20 | 9 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174.9 | 237.5 | 28.6 | 17.8 | 8 | -4 | FAIR | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 28.4 | 65.2 | 22 | 9 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202 | 170.7 | 233.7 | 24.3 | 29.2 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.8 | 168.2 | 231.2 | 22.1 | 17.5 | 7 | -8 | OVERPRICED | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 199.6 | 168.9 | 231 | 21.8 | 53.3 | 19 | 3 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 19.1 | 23.1 | 10 | -7 | FAIR | M9 diagnostic |
| 18 | Josh Jacobs | GB | 191.4 | 165.8 | 218.5 | 13.7 | 41.9 | 15 | -3 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 183.4 | 152.8 | 214.9 | 5.7 | 47.7 | 17 | -2 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.6 | 150 | 212 | 2.8 | 62.8 | 21 | 1 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **174.7**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280.3 | 344.9 | 137.8 | 5.9 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 295.4 | 263.5 | 327.8 | 120.8 | 6.3 | 3 | 1 | FAIR | M9 diagnostic |
| 3 | Ja'Marr Chase | CIN | 271.9 | 239.7 | 304 | 97.2 | 4.9 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Amon-Ra St. Brown | DET | 264.1 | 232.1 | 295.8 | 89.4 | 10.9 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | Rashee Rice | KC | 250.6 | 219 | 282 | 75.9 | 37.6 | 13 | 8 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 72.5 | 24.9 | 7 | 1 | FAIR | M9 diagnostic |
| 7 | Drake London | ATL | 228.2 | 196.6 | 260.2 | 53.5 | 26.7 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chris Olave | NO | 225.3 | 194.3 | 256.9 | 50.6 | 35.9 | 12 | 4 | FAIR | M9 diagnostic |
| 9 | George Pickens | DAL | 224.5 | 193.2 | 256.6 | 49.8 | 31.2 | 10 | 1 | FAIR | M9 diagnostic |
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 47.5 | 77.6 | 27 | 17 | VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 46.3 | 59.8 | 21 | 10 | VALUE | M9 diagnostic |
| 12 | CeeDee Lamb | DAL | 218.8 | 187.1 | 250.4 | 44.2 | 13.3 | 5 | -7 | FAIR | M9 diagnostic |
| 13 | Zay Flowers | BAL | 212.5 | 180.6 | 244.2 | 37.8 | 50 | 17 | 4 | FAIR | M9 diagnostic |
| 14 | Nico Collins | HOU | 205.8 | 173.8 | 238 | 31.1 | 30.8 | 9 | -5 | FAIR | M9 diagnostic |
| 15 | Garrett Wilson | NYJ | 201.7 | 170.4 | 233 | 27 | 56.4 | 19 | 4 | FAIR | M9 diagnostic |
| 16 | Malik Nabers | NYG | 201.6 | 170.5 | 233 | 26.9 | 34.6 | 11 | -5 | FAIR | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 17.8 | 62.8 | 22 | 5 | FAIR | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 188 | 157.7 | 218.7 | 13.3 | 94 | 35 | 17 | VALUE | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.7 | 151.2 | 214.8 | 8.1 | 15.2 | 6 | -13 | OVERPRICED | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.5 | 209.9 | 5 | 98.6 | 36 | 16 | VALUE | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **164.2**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 282.5 | 253.4 | 312.4 | 118.3 | 20.3 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | George Kittle | SF | 232.1 | 203.6 | 260.4 | 67.9 | 97.9 | 11 | 9 | VALUE | M9 diagnostic |
| 3 | Kyle Pitts | ATL | 225.2 | 196.7 | 253.9 | 60.9 | 78.4 | 8 | 5 | FAIR | M9 diagnostic |
| 4 | Brock Bowers | LV | 218.4 | 188 | 248.7 | 54.2 | 21.9 | 2 | -2 | FAIR | M9 diagnostic |
| 5 | Harold Fannin | CLE | 208.1 | 179.2 | 237.1 | 43.9 | 76 | 7 | 2 | FAIR | M9 diagnostic |
| 6 | Tucker Kraft | GB | 200.9 | 172.2 | 229.7 | 36.7 | 75.6 | 6 | 0 | FAIR | M9 diagnostic |
| 7 | Tyler Warren | IND | 196.8 | 168 | 225.7 | 32.6 | 51.7 | 4 | -3 | FAIR | M9 diagnostic |
| 8 | Sam LaPorta | DET | 188.3 | 159.7 | 217.2 | 24.1 | 68.5 | 5 | -3 | FAIR | M9 diagnostic |
| 9 | Isaiah Likely | NYG | 188.3 | 160.2 | 216.8 | 24.1 | 109.6 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Dalton Schultz | HOU | 185.2 | 157.1 | 213.3 | 20.9 | 176.5 | 22 | 12 | VALUE | M9 diagnostic |

### DST

Selected model: **FIE_DST_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | JAX D/ST | JAX | 9.3 | 2.7 | 17.4 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | TEN D/ST | TEN | 9 | 2.4 | 17.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | LAC D/ST | LAC | 8.9 | 2.3 | 17 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | SEA D/ST | SEA | 8.7 | 2.1 | 16.8 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | LAR D/ST | LAR | 8.5 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | PIT D/ST | PIT | 8.2 | 1.6 | 16.3 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | LV D/ST | LV | 8.2 | 1.6 | 16.3 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | NYJ D/ST | NYJ | 8.1 | 1.5 | 16.2 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | KC D/ST | KC | 8 | 1.4 | 16.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | DET D/ST | DET | 8 | 1.4 | 16.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

### K

Selected model: **FIE_KICKER_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cameron Dicker | LAC | 9.4 | 4.2 | 16 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | Brandon Aubrey | DAL | 9.2 | 3.9 | 15.7 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | Jake Bates | DET | 8.6 | 3.4 | 15.2 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | Will Reichard | MIN | 8.6 | 3.3 | 15.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | Evan McPherson | CIN | 8.5 | 3.2 | 15 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | Cam Little | JAX | 8.4 | 3.2 | 15 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | Harrison Butker | KC | 8.4 | 3.2 | 15 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | Jason Myers | SEA | 8.3 | 3.1 | 14.9 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | Ka'imi Fairbairn | HOU | 8.3 | 3 | 14.8 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | Tyler Loop | BAL | 8.2 | 2.9 | 14.7 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 47.5 | 77.6 | 27 | 17 | VALUE | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 188 | 157.7 | 218.7 | 13.3 | 94 | 35 | 17 | VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 69.7 | 82.2 | 19 | 16 | VALUE | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.5 | 209.9 | 5 | 98.6 | 36 | 16 | VALUE | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 76.8 | 60.9 | 15 | 13 | VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 46.3 | 59.8 | 21 | 10 | VALUE | M9 diagnostic |
| 2 | George Kittle | SF | 232.1 | 203.6 | 260.4 | 67.9 | 97.9 | 11 | 9 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 30 | 58.2 | 20 | 9 | VALUE | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 28.4 | 65.2 | 22 | 9 | VALUE | M9 diagnostic |
| 12 | Tyler Shough | NO | 215.4 | 175.7 | 254.9 | 12.1 | 87.6 | 21 | 9 | VALUE | M9 diagnostic |
| 5 | Rashee Rice | KC | 250.6 | 219 | 282 | 75.9 | 37.6 | 13 | 8 | VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 257.2 | 216.8 | 297.6 | 53.8 | 55.9 | 14 | 8 | VALUE | M9 diagnostic |
| 22 | Carnell Tate | TEN | 177.3 | 147.7 | 208.3 | 2.6 | 80.7 | 30 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 56 | Luther Burden | CHI | 125.4 | 93.9 | 156.8 | -49.3 | 64.7 | 23 | -33 | STRONG_FADE | M9 diagnostic |
| 55 | Bhayshul Tuten | JAX | 63.9 | 34 | 93.9 | -113.9 | 74.4 | 25 | -30 | STRONG_FADE | M9 diagnostic |
| 42 | Ladd McConkey | LAC | 153.3 | 122 | 184.4 | -21.3 | 52.1 | 18 | -24 | STRONG_FADE | M9 diagnostic |
| 24 | Joe Burrow | CIN | 181.4 | 141.4 | 222.6 | -22 | 14.3 | 4 | -20 | STRONG_FADE | M9 diagnostic |
| 21 | Caleb Williams | CHI | 184.4 | 144.4 | 224 | -18.9 | 26.4 | 6 | -15 | OVERPRICED | M9 diagnostic |
| 31 | DeVonta Smith | PHI | 166.7 | 136.3 | 197.9 | -7.9 | 49.6 | 16 | -15 | OVERPRICED | M9 diagnostic |
| 23 | Dalton Kincaid | BUF | 129.6 | 101.4 | 158.2 | -34.6 | 93.1 | 9 | -14 | OVERPRICED | M9 diagnostic |
| 38 | Terry McLaurin | WAS | 158.4 | 127.3 | 189.9 | -16.3 | 69.7 | 24 | -14 | OVERPRICED | M9 diagnostic |
| 17 | Colston Loveland | CHI | 152.2 | 123.2 | 181.6 | -12 | 39.1 | 3 | -14 | OVERPRICED | M9 diagnostic |
| 34 | Emeka Egbuka | TB | 164.7 | 133.9 | 196.3 | -10 | 57.6 | 20 | -14 | OVERPRICED | M9 diagnostic |
| 46 | Brian Thomas | JAX | 139.8 | 109.1 | 170.9 | -34.9 | 89.5 | 33 | -13 | OVERPRICED | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.7 | 151.2 | 214.8 | 8.1 | 15.2 | 6 | -13 | OVERPRICED | M9 diagnostic |
| 44 | Marvin Harrison | ARI | 151.6 | 121.6 | 182.6 | -23.1 | 89.2 | 32 | -12 | OVERPRICED | M9 diagnostic |
| 43 | Parker Washington | JAX | 153.2 | 121.7 | 184.1 | -21.4 | 85.9 | 31 | -12 | OVERPRICED | M9 diagnostic |
| 26 | Tetairoa McMillan | CAR | 171.8 | 141.1 | 202.9 | -2.8 | 44.8 | 14 | -12 | OVERPRICED | M9 diagnostic |
| 13 | Lamar Jackson | BAL | 212.4 | 171.9 | 252.7 | 9.1 | 8.5 | 2 | -11 | OVERPRICED | M9 diagnostic |
| 20 | Jaxson Dart | NYG | 186.8 | 146.7 | 227.3 | -16.6 | 42.8 | 11 | -9 | OVERPRICED | M9 diagnostic |
| 24 | Tee Higgins | CIN | 175.4 | 144.5 | 206.4 | 0.7 | 46.4 | 15 | -9 | OVERPRICED | M9 diagnostic |
| 25 | Jordan Love | GB | 168.9 | 129.1 | 209 | -34.5 | 71.9 | 17 | -8 | OVERPRICED | M9 diagnostic |
| 24 | Breece Hall | NYJ | 169.4 | 138 | 200.8 | -8.4 | 43.5 | 16 | -8 | OVERPRICED | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.8 | 168.2 | 231.2 | 22.1 | 17.5 | 7 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 104.9 | Malik Willis | MIA | 5 | 23 | 18 | 261.1 | 57.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 173.5 | Geno Smith | NYJ | 14 | 30 | 16 | 208.5 | 5.1 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 110.1 | Daniel Jones | IND | 16 | 25 | 9 | 203.4 | 0 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 176.5 | Dalton Schultz | HOU | 10 | 22 | 12 | 185.2 | 20.9 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 179.8 | Chig Okonkwo | WAS | 13 | 23 | 10 | 174.6 | 10.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |

## Governance

- ADP remains outside the football model.
- This report does not calculate or activate a parallel ranking model.
- Promotion-review-ready research remains non-production until a separate governance decision.
- D/ST and K tables use the existing dedicated current specialist engines and are explicitly weekly/current in scope.

## M9.1c Preseason Projection Challenger

M9 remains the governed production preseason model. M9.1c is research-only and changes no canonical VORP, replacement, ranking, or actionability field. Its current promotion gate remains the historical Actual-minus-Sleeper preseason residual test.

### Largest positive M9.1c adjustments

| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |
|---|---|---|---:|---:|---:|---|

### Largest negative M9.1c adjustments

| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |
|---|---|---|---:|---:|---:|---|
