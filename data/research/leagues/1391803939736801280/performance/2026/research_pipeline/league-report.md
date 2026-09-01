# FIE League Research Report — SLR2026 - Liga 38

Season: **2026**  
League ID: `1391803939736801280`  
Format: **REDRAFT**  
Teams: **12**  
Roster: `QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_ppr`  
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
Pass TD: **4** · Pass INT: **-1**  
Fumble: **-1** · Fumble lost: **-2**  
Superflex/2QB: **No** · D/ST: **Yes** · K: **Yes**

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
League replacement: **222.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 299.6 | 259.6 | 341.2 | 77.1 | 21.3 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Kyler Murray | MIN | 283.1 | 243.7 | 323.7 | 60.6 | 159 | 19 | 17 | VALUE | M9 diagnostic |
| 3 | Matthew Stafford | LAR | 280.2 | 240.1 | 321.8 | 57.7 | 95.8 | 11 | 8 | VALUE | M9 diagnostic |
| 4 | Malik Willis | MIA | 270.1 | 229.7 | 310.6 | 47.6 | 194.5 | 23 | 19 | STRONG_VALUE | M9 diagnostic |
| 5 | Drake Maye | NE | 268.6 | 227.5 | 309.3 | 46.1 | 47.6 | 3 | -2 | FAIR | M9 diagnostic |
| 6 | Brock Purdy | SF | 267.4 | 226.9 | 308.8 | 44.9 | 122.4 | 15 | 9 | VALUE | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 259.3 | 219.3 | 300.2 | 36.9 | 107.3 | 13 | 6 | FAIR | M9 diagnostic |
| 8 | Jalen Hurts | PHI | 241.3 | 200.9 | 282.6 | 18.8 | 59.2 | 5 | -3 | FAIR | M9 diagnostic |
| 9 | Dak Prescott | DAL | 239.6 | 199.8 | 280.6 | 17.1 | 77.8 | 8 | -1 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 233.4 | 193.2 | 273.8 | 10.9 | 100.2 | 12 | 2 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **170**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308.6 | 277 | 340.5 | 138.6 | 5.4 | 3 | 2 | FAIR | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.8 | 255.2 | 318.1 | 116.8 | 2.9 | 2 | 0 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268.5 | 236.3 | 299.9 | 98.6 | 1.1 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 265.4 | 233.9 | 297.1 | 95.4 | 7.3 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 265.2 | 233.3 | 296 | 95.2 | 11.8 | 6 | 1 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.4 | 275.4 | 74 | 19.7 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 238 | 206.6 | 269.3 | 68 | 10.4 | 5 | -2 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 229.2 | 198.4 | 260.5 | 59.2 | 16.7 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 180.9 | 243.4 | 41.8 | 26.7 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.6 | 239 | 38 | 29.5 | 14 | 4 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.7 | 37.7 | 44.6 | 20 | 9 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 207 | 176.3 | 238.2 | 37 | 14.5 | 8 | -4 | FAIR | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.2 | 237.6 | 36.1 | 49 | 21 | 8 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202.6 | 171.6 | 233.9 | 32.6 | 20.2 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 200.4 | 169.9 | 231.6 | 30.5 | 13.7 | 7 | -8 | OVERPRICED | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 200.2 | 170.1 | 231.1 | 30.2 | 43.6 | 19 | 3 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 197.4 | 166.2 | 228.3 | 27.4 | 15.2 | 9 | -8 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 192 | 161.4 | 223.5 | 22 | 31.7 | 15 | -3 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 184 | 153.6 | 214.8 | 14 | 35.8 | 17 | -2 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 181.1 | 149.8 | 212.5 | 11.2 | 55 | 24 | 4 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **170.9**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280 | 344.7 | 141.6 | 4.4 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 309.4 | 277.9 | 341.4 | 138.5 | 5.2 | 3 | 1 | FAIR | M9 production |
| 3 | Ja'Marr Chase | CIN | 285.9 | 254.2 | 318.1 | 115 | 3.1 | 1 | -2 | FAIR | M9 production |
| 4 | Amon-Ra St. Brown | DET | 278 | 246.2 | 310.6 | 107.1 | 8 | 4 | 0 | FAIR | M9 production |
| 5 | Rashee Rice | KC | 264.6 | 232.3 | 296.1 | 93.7 | 28.7 | 12 | 7 | FAIR | M9 production |
| 6 | A.J. Brown | NE | 247.2 | 216.4 | 278.6 | 76.3 | 17.9 | 8 | 2 | FAIR | M9 diagnostic |
| 7 | Drake London | ATL | 242.2 | 211.4 | 273.5 | 71.3 | 17.1 | 7 | 0 | FAIR | M9 production |
| 8 | Chris Olave | NO | 239.7 | 208.3 | 271.6 | 68.8 | 29.9 | 13 | 5 | FAIR | M9 production |
| 9 | George Pickens | DAL | 238.5 | 207.5 | 270.1 | 67.6 | 23.1 | 9 | 0 | FAIR | M9 production |
| 10 | CeeDee Lamb | DAL | 232.8 | 201.7 | 264.6 | 61.9 | 9.5 | 5 | -5 | FAIR | M9 production |
| 11 | Zay Flowers | BAL | 226.5 | 194.7 | 257.9 | 55.6 | 41.1 | 19 | 8 | VALUE | M9 production |
| 12 | Mike Evans | SF | 222.2 | 191 | 253.4 | 51.3 | 61 | 27 | 15 | VALUE | M9 diagnostic |
| 13 | Jaylen Waddle | DEN | 221 | 190 | 252.1 | 50.1 | 46.6 | 21 | 8 | VALUE | M9 diagnostic |
| 14 | Nico Collins | HOU | 219.8 | 188.4 | 251.1 | 48.9 | 25.3 | 10 | -4 | FAIR | M9 production |
| 15 | Garrett Wilson | NYJ | 215.6 | 184.9 | 246.8 | 44.7 | 45.9 | 20 | 5 | FAIR | M9 production |
| 16 | Malik Nabers | NYG | 215.6 | 184.9 | 247 | 44.7 | 27.6 | 11 | -5 | FAIR | M9 production |
| 17 | Courtland Sutton | DEN | 202 | 171.7 | 232.6 | 31.1 | 80.9 | 35 | 18 | STRONG_VALUE | M9 production |
| 18 | Justin Jefferson | MIN | 196.7 | 166.3 | 227.4 | 25.8 | 11.5 | 6 | -12 | OVERPRICED | M9 production |
| 19 | Michael Wilson | ARI | 193.6 | 162.6 | 224.5 | 22.7 | 83 | 36 | 17 | VALUE | M9 production |
| 20 | Davante Adams | LAR | 192.5 | 161.4 | 223.9 | 21.6 | 50.2 | 22 | 2 | FAIR | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **164.7**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 253.4 | 227.4 | 279.7 | 88.6 | 22.4 | 1 | 0 | FAIR | M9 production |
| 2 | George Kittle | SF | 212.3 | 186.9 | 237.4 | 47.5 | 89.4 | 10 | 8 | VALUE | M9 production |
| 3 | Kyle Pitts | ATL | 205.5 | 180.3 | 230.8 | 40.8 | 69.8 | 8 | 5 | FAIR | M9 production |
| 4 | Brock Bowers | LV | 201.8 | 177 | 227.2 | 37.1 | 23.3 | 2 | -2 | FAIR | M9 production |
| 5 | Harold Fannin | CLE | 191.3 | 166 | 216.1 | 26.5 | 68.5 | 7 | 2 | FAIR | M9 production |
| 6 | Tucker Kraft | GB | 189.5 | 164.3 | 215.2 | 24.8 | 63.4 | 6 | 0 | FAIR | M9 production |
| 7 | Tyler Warren | IND | 183.8 | 159 | 208.9 | 19 | 47.5 | 4 | -3 | FAIR | M9 production |
| 8 | Sam LaPorta | DET | 176.5 | 151.7 | 201.4 | 11.7 | 59.6 | 5 | -3 | FAIR | M9 production |
| 9 | Dalton Schultz | HOU | 172.7 | 148 | 197.4 | 7.9 | 191 | 24 | 15 | VALUE | M9 production |
| 10 | Travis Kelce | KC | 171.2 | 146.3 | 196.1 | 6.4 | 92.7 | 11 | 1 | FAIR | M9 production |

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
| 2 | TEN D/ST | TEN | 9.2 | 2.6 | 17.2 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | LAC D/ST | LAC | 8.9 | 2.3 | 17 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | SEA D/ST | SEA | 8.7 | 2.1 | 16.8 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | LAR D/ST | LAR | 8.5 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | PIT D/ST | PIT | 8.3 | 1.7 | 16.4 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | LV D/ST | LV | 8.2 | 1.6 | 16.3 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | DET D/ST | DET | 8.1 | 1.5 | 16.2 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | KC D/ST | KC | 8 | 1.4 | 16.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | NYJ D/ST | NYJ | 7.9 | 1.3 | 16 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

### K

Selected model: **FIE_KICKER_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cameron Dicker | LAC | 9.4 | 4.2 | 15.9 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | Brandon Aubrey | DAL | 9.1 | 3.9 | 15.7 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | Jake Bates | DET | 8.6 | 3.3 | 15.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | Will Reichard | MIN | 8.5 | 3.3 | 15.1 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | Cam Little | JAX | 8.4 | 3.2 | 14.9 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | Harrison Butker | KC | 8.4 | 3.2 | 14.9 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | Evan McPherson | CIN | 8.4 | 3.1 | 14.9 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | Jason Myers | SEA | 8.3 | 3.1 | 14.8 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | Ka'imi Fairbairn | HOU | 8.3 | 3 | 14.8 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | Tyler Loop | BAL | 8.2 | 2.9 | 14.7 | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 17 | Courtland Sutton | DEN | 202 | 171.7 | 232.6 | 31.1 | 80.9 | 35 | 18 | STRONG_VALUE | M9 production |
| 19 | Michael Wilson | ARI | 193.6 | 162.6 | 224.5 | 22.7 | 83 | 36 | 17 | VALUE | M9 production |
| 12 | Mike Evans | SF | 222.2 | 191 | 253.4 | 51.3 | 61 | 27 | 15 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.7 | 37.7 | 44.6 | 20 | 9 | VALUE | M9 diagnostic |
| 3 | Matthew Stafford | LAR | 280.2 | 240.1 | 321.8 | 57.7 | 95.8 | 11 | 8 | VALUE | M9 diagnostic |
| 11 | Zay Flowers | BAL | 226.5 | 194.7 | 257.9 | 55.6 | 41.1 | 19 | 8 | VALUE | M9 production |
| 13 | Jaylen Waddle | DEN | 221 | 190 | 252.1 | 50.1 | 46.6 | 21 | 8 | VALUE | M9 diagnostic |
| 2 | George Kittle | SF | 212.3 | 186.9 | 237.4 | 47.5 | 89.4 | 10 | 8 | VALUE | M9 production |
| 13 | David Montgomery | HOU | 206.1 | 175.2 | 237.6 | 36.1 | 49 | 21 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 58 | Bhayshul Tuten | JAX | 64.4 | 34.5 | 95.3 | -105.5 | 62.5 | 25 | -33 | STRONG_FADE | M9 diagnostic |
| 71 | Jordyn Tyson | NO | 111 | 83.7 | 139.5 | -59.9 | 89.4 | 38 | -33 | STRONG_FADE | M9 diagnostic |
| 54 | Luther Burden | CHI | 139.3 | 110.8 | 169.1 | -31.6 | 52.4 | 23 | -31 | STRONG_FADE | M9 production |
| 38 | Ladd McConkey | LAC | 167.3 | 137.9 | 197.6 | -3.6 | 38.4 | 17 | -21 | STRONG_FADE | M9 production |
| 48 | Chuba Hubbard | CAR | 100.4 | 71 | 130.5 | -69.6 | 77 | 28 | -20 | STRONG_FADE | M9 diagnostic |
| 21 | Joe Burrow | CIN | 187.8 | 147.6 | 228.6 | -34.7 | 51.1 | 4 | -17 | OVERPRICED | M9 diagnostic |
| 23 | Caleb Williams | CHI | 186.5 | 147.2 | 226 | -36 | 71.2 | 7 | -16 | OVERPRICED | M9 diagnostic |
| 18 | Colston Loveland | CHI | 145.7 | 121.6 | 170.1 | -19.1 | 40.8 | 3 | -15 | OVERPRICED | M9 production |
| 46 | Brian Thomas | JAX | 153.7 | 124.4 | 183.4 | -17.2 | 73.1 | 31 | -15 | OVERPRICED | M9 production |
| 22 | Dalton Kincaid | BUF | 129.4 | 105.7 | 153.4 | -35.4 | 87.4 | 9 | -13 | OVERPRICED | M9 production |
| 52 | Chris Godwin | TB | 141.1 | 112 | 170.9 | -29.8 | 95.5 | 39 | -13 | OVERPRICED | M9 production |
| 46 | Kyle Monangai | CHI | 103.7 | 74.4 | 134.3 | -66.3 | 99.8 | 34 | -12 | OVERPRICED | M9 diagnostic |
| 22 | Jaxson Dart | NYG | 187.7 | 148.3 | 227.6 | -34.8 | 91.5 | 10 | -12 | OVERPRICED | M9 diagnostic |
| 30 | Emeka Egbuka | TB | 178.7 | 148.6 | 209.2 | 7.8 | 39.8 | 18 | -12 | OVERPRICED | M9 production |
| 18 | Justin Jefferson | MIN | 196.7 | 166.3 | 227.4 | 25.8 | 11.5 | 6 | -12 | OVERPRICED | M9 production |
| 13 | Lamar Jackson | BAL | 218.1 | 177.6 | 259.1 | -4.4 | 32.5 | 2 | -11 | OVERPRICED | M9 diagnostic |
| 26 | DeVonta Smith | PHI | 180.7 | 150.8 | 211.9 | 9.8 | 35.2 | 15 | -11 | OVERPRICED | M9 production |
| 34 | Terry McLaurin | WAS | 172.4 | 142.2 | 203 | 1.5 | 56.1 | 24 | -10 | OVERPRICED | M9 production |
| 24 | Breece Hall | NYJ | 170 | 139.4 | 200.9 | 0 | 33.5 | 16 | -8 | OVERPRICED | M9 diagnostic |
| 24 | Tetairoa McMillan | CAR | 185.8 | 155.6 | 216.1 | 14.9 | 37 | 16 | -8 | OVERPRICED | M9 production |
| 22 | Tee Higgins | CIN | 189.3 | 158.9 | 220.6 | 18.4 | 34.4 | 14 | -8 | OVERPRICED | M9 production |
| 17 | Omarion Hampton | LAC | 197.4 | 166.2 | 228.3 | 27.4 | 15.2 | 9 | -8 | OVERPRICED | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 200.4 | 169.9 | 231.6 | 30.5 | 13.7 | 7 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 194.5 | Malik Willis | MIA | 4 | 23 | 19 | 270.1 | 47.6 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 159 | Kyler Murray | MIN | 2 | 19 | 17 | 283.1 | 60.6 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |
| 122.4 | Brock Purdy | SF | 6 | 15 | 9 | 267.4 | 44.9 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 113.9 | Quentin Johnston | LAC | 28 | 46 | 18 | 179.3 | 8.4 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 115.5 | Jakobi Meyers | JAX | 32 | 47 | 15 | 176.2 | 5.3 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 101.7 | Alec Pierce | IND | 33 | 41 | 8 | 172.5 | 1.6 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 191 | Dalton Schultz | HOU | 9 | 24 | 15 | 172.7 | 7.9 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |
| 187.1 | Juwan Johnson | NO | 11 | 23 | 12 | 165.1 | 0.3 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |

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
| Christian McCaffrey | RB | SF | 29.6 | 2.16 | 0.41 | CLEAR_STARTER |
| Jaxon Smith-Njigba | WR | SEA | 24.3 | 0.91 | 0.44 | CLEAR_STARTER |
| Keenan Allen | WR | IND | 20.4 | 2.29 | 0.55 | COMMITTEE_FRINGE |
| Jakobi Meyers | WR | JAX | 19.9 | 2.02 | 0.35 | COMMITTEE_FRINGE |
| Jauan Jennings | WR | MIN | 19.3 | 2.28 | 0.56 | COMMITTEE_FRINGE |
| Mack Hollins | WR | NE | 17.6 | 1.75 | 0.62 | DEPTH |
| Deebo Samuel | WR | SF | 16.4 | 2.54 | 0.51 | STARTER |
| Marquise Brown | WR | PHI | 16.3 | 1.56 | 0.54 | DEPTH |
| Trey McBride | TE | ARI | 16.3 | 2.64 | 0.25 | CLEAR_STARTER |
| Quentin Johnston | WR | LAC | 16 | 3.17 | 0.5 | STARTER |

### Largest negative M9.1c adjustments

| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |
|---|---|---|---:|---:|---:|---|
| Sam Darnold | QB | SEA | -17.5 | -1.51 | 0.72 | CLEAR_STARTER |
| Nick Westbrook-Ikhine | WR | IND | -16.7 | -6.03 | 0.47 | COMMITTEE_FRINGE |
| Jack Bech | WR | LV | -16.1 | -1.06 | 0.57 | DEPTH |
| Blake Corum | RB | LAR | -14 | -0.93 | 0.57 | STARTER |
| Quinshon Judkins | RB | CLE | -13.5 | -0.71 | 0.65 | CLEAR_STARTER |
| Jahan Dotson | WR | ATL | -12.3 | -4.28 | 0.51 | STARTER |
| Kenneth Walker | RB | KC | -12.3 | -3.13 | 0.53 | CLEAR_STARTER |
| Derrick Henry | RB | BAL | -11.8 | -1.26 | 0.6 | CLEAR_STARTER |
| Saquon Barkley | RB | PHI | -11.8 | -1.16 | 0.6 | CLEAR_STARTER |
| Marquez Valdes-Scantling | WR | DAL | -11.6 | -0.67 | 0.48 | COMMITTEE_FRINGE |
