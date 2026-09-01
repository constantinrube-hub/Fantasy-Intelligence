# FIE League Research Report — Stoned Lack Bestball Dynasty 3

Season: **2026**  
League ID: `1341105213464924160`  
Format: **DYNASTY_BESTBALL**  
Teams: **12**  
Roster: `QB, RB, RB, WR, WR, TE, FLEX, FLEX, SUPER_FLEX, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_dynasty_2qb`  
Pipeline: **complete_research_only**

## Model overview

| Position | Selected Model | Research Challenger | Validation Status | Exact Scoring | Key Reason |
|---|---|---|---|---|---|
| DST | — | — | NOT_APPLICABLE | None | position_not_rosterable |
| K | — | — | NOT_APPLICABLE | None | position_not_rosterable |
| QB | M9 | V9.7.5 | BLOCKED_STATISTICS | False | one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared |
| RB | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| TE | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| WR | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |

## League/scoring overview

PPR: **PPR** (1 per reception)  
Pass TD: **4** · Pass INT: **-2**  
Fumble: **-1** · Fumble lost: **-2**  
Superflex/2QB: **Yes** · D/ST: **No** · K: **No**

Bonuses: `{"bonus_rec_te": 0.5}`

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
League replacement: **182.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 295.4 | 254.2 | 336.3 | 112.8 | 1.7 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 97.7 | 86.9 | 21 | 19 | STRONG_VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 90.5 | 93.3 | 23 | 20 | STRONG_VALUE | M9 diagnostic |
| 4 | Drake Maye | NE | 264.5 | 224.7 | 305.6 | 82 | 5.7 | 2 | -2 | FAIR | M9 diagnostic |
| 5 | Malik Willis | MIA | 261.1 | 221.9 | 301.9 | 78.6 | 115.4 | 26 | 21 | STRONG_VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 257.2 | 216.8 | 297.6 | 74.6 | 47.7 | 13 | 7 | FAIR | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 253.1 | 213.5 | 293.3 | 70.6 | 37.2 | 11 | 4 | FAIR | M9 diagnostic |
| 8 | Dak Prescott | DAL | 235.7 | 195.5 | 276.4 | 53.1 | 51 | 14 | 6 | FAIR | M9 diagnostic |
| 9 | Jalen Hurts | PHI | 234.2 | 194.2 | 274.3 | 51.7 | 26.7 | 8 | -1 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 229.8 | 189 | 271 | 47.3 | 35.4 | 10 | 0 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **167.8**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308.3 | 276.5 | 340.2 | 140.4 | 31 | 9 | 8 | VALUE | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.5 | 254.2 | 319.2 | 118.7 | 2.7 | 1 | -1 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268.2 | 236.1 | 300.8 | 100.3 | 3.2 | 2 | -1 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 264.9 | 233.3 | 295.9 | 97.1 | 22.2 | 7 | 3 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 264.6 | 232.5 | 296.3 | 96.7 | 21.3 | 6 | 1 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.3 | 275.9 | 76.2 | 35.5 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 237.3 | 205.7 | 269.3 | 69.4 | 23.9 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 228.5 | 197 | 259.8 | 60.7 | 33.5 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 181.2 | 242.8 | 44 | 17.3 | 4 | -5 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.5 | 238.9 | 40.2 | 53.4 | 16 | 6 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 39.9 | 71.1 | 22 | 11 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.2 | 174.7 | 237.3 | 38.3 | 12.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 38.3 | 85.1 | 26 | 13 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202 | 170.6 | 233.7 | 34.1 | 62.1 | 19 | 5 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.7 | 168 | 231.1 | 31.8 | 41.8 | 12 | -3 | FAIR | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 199.7 | 168.9 | 231.1 | 31.8 | 57.9 | 18 | 2 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.9 | 165.9 | 228.1 | 29.1 | 20.9 | 5 | -12 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 191.5 | 165.9 | 218.6 | 23.7 | 73.5 | 23 | 5 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 183.3 | 152.8 | 214.8 | 15.5 | 62.6 | 20 | 1 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.6 | 150.1 | 212 | 12.7 | 80.9 | 25 | 5 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **168.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280.3 | 344.9 | 144 | 6.1 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 309.5 | 277.5 | 342 | 141 | 7.2 | 3 | 1 | FAIR | M9 production |
| 3 | Ja'Marr Chase | CIN | 285.8 | 253.8 | 317.8 | 117.3 | 4 | 1 | -2 | FAIR | M9 production |
| 4 | Amon-Ra St. Brown | DET | 278.1 | 246.1 | 309.8 | 109.6 | 8.6 | 4 | 0 | FAIR | M9 production |
| 5 | Rashee Rice | KC | 264.7 | 232.5 | 296.3 | 96.2 | 50.6 | 18 | 13 | VALUE | M9 production |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 78.7 | 48.8 | 17 | 11 | VALUE | M9 diagnostic |
| 7 | Drake London | ATL | 242.1 | 210.6 | 274 | 73.6 | 24.7 | 8 | 1 | FAIR | M9 production |
| 8 | Chris Olave | NO | 239.6 | 208.6 | 271.2 | 71.1 | 40.8 | 13 | 5 | FAIR | M9 production |
| 9 | George Pickens | DAL | 238.6 | 207.3 | 270.5 | 70.1 | 30.4 | 10 | 1 | FAIR | M9 production |
| 10 | CeeDee Lamb | DAL | 232.8 | 201.4 | 263.9 | 64.3 | 17.7 | 7 | -3 | FAIR | M9 production |
| 11 | Zay Flowers | BAL | 226.7 | 194.9 | 258.4 | 58.2 | 55.7 | 20 | 9 | VALUE | M9 production |
| 12 | Mike Evans | SF | 222.2 | 191.2 | 254 | 53.7 | 106.9 | 40 | 28 | STRONG_VALUE | M9 diagnostic |
| 13 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 52.5 | 70.6 | 26 | 13 | VALUE | M9 diagnostic |
| 14 | Nico Collins | HOU | 220 | 188.5 | 251.7 | 51.5 | 34.1 | 12 | -2 | FAIR | M9 production |
| 15 | Garrett Wilson | NYJ | 215.6 | 184.5 | 246.7 | 47.1 | 44.5 | 15 | 0 | FAIR | M9 production |
| 16 | Malik Nabers | NYG | 215.4 | 184.6 | 246.5 | 46.9 | 16.5 | 6 | -10 | OVERPRICED | M9 production |
| 17 | Courtland Sutton | DEN | 201.9 | 170.9 | 233 | 33.4 | 127.1 | 49 | 32 | STRONG_VALUE | M9 production |
| 18 | Justin Jefferson | MIN | 196.6 | 166 | 227.9 | 28.1 | 14.3 | 5 | -13 | OVERPRICED | M9 production |
| 19 | Michael Wilson | ARI | 193.8 | 162.8 | 224.7 | 25.3 | 94.9 | 35 | 16 | VALUE | M9 production |
| 20 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 24 | 96.5 | 36 | 16 | VALUE | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **169.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 305.3 | 276 | 335.2 | 135.8 | 19.5 | 2 | 1 | FAIR | M9 production |
| 2 | George Kittle | SF | 254.9 | 226 | 283.7 | 85.5 | 114.5 | 14 | 12 | VALUE | M9 production |
| 3 | Kyle Pitts | ATL | 248 | 218.9 | 277.1 | 78.6 | 74.4 | 8 | 5 | FAIR | M9 production |
| 4 | Brock Bowers | LV | 241.2 | 211.2 | 271.2 | 71.7 | 11.5 | 1 | -3 | FAIR | M9 production |
| 5 | Harold Fannin | CLE | 230.9 | 201.8 | 260.1 | 61.4 | 56.3 | 5 | 0 | FAIR | M9 production |
| 6 | Tucker Kraft | GB | 223.8 | 195 | 252.8 | 54.4 | 61.4 | 6 | 0 | FAIR | M9 production |
| 7 | Tyler Warren | IND | 219.4 | 190.9 | 248 | 49.9 | 38.3 | 4 | -3 | FAIR | M9 production |
| 8 | Sam LaPorta | DET | 211.2 | 182.7 | 239.9 | 41.7 | 64 | 7 | -1 | FAIR | M9 production |
| 9 | Dalton Schultz | HOU | 207.9 | 179.4 | 236.5 | 38.5 | 195.1 | 27 | 18 | STRONG_VALUE | M9 production |
| 10 | Travis Kelce | KC | 205.2 | 176.8 | 233.7 | 35.8 | 137.1 | 17 | 7 | FAIR | M9 production |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 90.5 | 93.3 | 23 | 20 | STRONG_VALUE | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 97.7 | 86.9 | 21 | 19 | STRONG_VALUE | M9 diagnostic |
| 19 | Michael Wilson | ARI | 193.8 | 162.8 | 224.7 | 25.3 | 94.9 | 35 | 16 | VALUE | M9 production |
| 20 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 24 | 96.5 | 36 | 16 | VALUE | M9 diagnostic |
| 5 | Rashee Rice | KC | 264.7 | 232.5 | 296.3 | 96.2 | 50.6 | 18 | 13 | VALUE | M9 production |
| 13 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 52.5 | 70.6 | 26 | 13 | VALUE | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 38.3 | 85.1 | 26 | 13 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 78.7 | 48.8 | 17 | 11 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 39.9 | 71.1 | 22 | 11 | VALUE | M9 diagnostic |
| 11 | Zay Flowers | BAL | 226.7 | 194.9 | 258.4 | 58.2 | 55.7 | 20 | 9 | VALUE | M9 production |
| 23 | Christian Watson | GB | 188.7 | 158.1 | 219.9 | 20.2 | 87.5 | 32 | 9 | VALUE | M9 production |
| 1 | Christian McCaffrey | SF | 308.3 | 276.5 | 340.2 | 140.4 | 31 | 9 | 8 | VALUE | M9 diagnostic |
| 12 | Tyler Shough | NO | 215.5 | 175.7 | 254.9 | 32.9 | 83.4 | 20 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 72 | Jordyn Tyson | NO | 111 | 83.2 | 139.3 | -57.5 | 69.5 | 25 | -47 | STRONG_FADE | M9 diagnostic |
| 61 | Bhayshul Tuten | JAX | 63.9 | 34 | 93.9 | -104 | 79.1 | 24 | -37 | STRONG_FADE | M9 diagnostic |
| 53 | Luther Burden | CHI | 139.8 | 110.7 | 169.7 | -28.7 | 52.8 | 19 | -34 | STRONG_FADE | M9 production |
| 35 | Kenyon Sadiq | NYJ | 120.2 | 94.1 | 147.6 | -49.3 | 89.3 | 9 | -26 | STRONG_FADE | M9 diagnostic |
| 38 | Ladd McConkey | LAC | 167.4 | 137.3 | 197.3 | -1.1 | 42.1 | 14 | -24 | STRONG_FADE | M9 production |
| 39 | Cam Ward | TEN | 114.8 | 77.2 | 153.5 | -67.7 | 82.7 | 19 | -20 | STRONG_FADE | M9 diagnostic |
| 46 | Brian Thomas | JAX | 153.7 | 124.5 | 184 | -14.8 | 71.7 | 27 | -19 | STRONG_FADE | M9 production |
| 25 | Joe Burrow | CIN | 181.4 | 141.4 | 222.6 | -1.1 | 15.1 | 6 | -19 | STRONG_FADE | M9 diagnostic |
| 30 | Emeka Egbuka | TB | 178.4 | 148.4 | 209 | 9.9 | 32.8 | 11 | -19 | STRONG_FADE | M9 production |
| 46 | Kyle Monangai | CHI | 103.2 | 74.5 | 132.3 | -64.6 | 98.6 | 28 | -18 | STRONG_FADE | M9 diagnostic |
| 26 | Dalton Kincaid | BUF | 152.4 | 125.2 | 180 | -17 | 98.4 | 10 | -16 | OVERPRICED | M9 production |
| 40 | Marvin Harrison | ARI | 165.6 | 136.4 | 196 | -2.9 | 68.3 | 24 | -16 | OVERPRICED | M9 production |
| 21 | Caleb Williams | CHI | 184.5 | 144.4 | 224.1 | 1.9 | 13.7 | 5 | -16 | OVERPRICED | M9 diagnostic |
| 28 | TreVeyon Henderson | NE | 156.7 | 126.7 | 187.9 | -11.2 | 43.8 | 13 | -15 | OVERPRICED | M9 diagnostic |
| 31 | Carnell Tate | TEN | 177.3 | 147.7 | 208.2 | 8.8 | 44.6 | 16 | -15 | OVERPRICED | M9 diagnostic |
| 24 | Tetairoa McMillan | CAR | 185.9 | 155.8 | 216.4 | 17.4 | 29.6 | 9 | -15 | OVERPRICED | M9 production |
| 17 | Colston Loveland | CHI | 175 | 147.1 | 203.4 | 5.5 | 28.2 | 3 | -14 | OVERPRICED | M9 production |
| 50 | Jordan Addison | MIN | 145.4 | 116 | 174.8 | -23.1 | 97.7 | 37 | -13 | OVERPRICED | M9 production |
| 44 | KC Concepcion | CLE | 156.4 | 126.8 | 186.6 | -12.1 | 84.6 | 31 | -13 | OVERPRICED | M9 diagnostic |
| 18 | Justin Jefferson | MIN | 196.6 | 166 | 227.9 | 28.1 | 14.3 | 5 | -13 | OVERPRICED | M9 production |
| 17 | Omarion Hampton | LAC | 196.9 | 165.9 | 228.1 | 29.1 | 20.9 | 5 | -12 | OVERPRICED | M9 diagnostic |
| 33 | C.J. Stroud | HOU | 146 | 107.1 | 185.4 | -36.5 | 91.7 | 22 | -11 | OVERPRICED | M9 diagnostic |
| 26 | Jordan Love | GB | 168.9 | 129.1 | 209.1 | -13.6 | 58.4 | 15 | -11 | OVERPRICED | M9 diagnostic |
| 20 | Jaxson Dart | NYG | 186.8 | 146.7 | 227.3 | 4.3 | 27 | 9 | -11 | OVERPRICED | M9 diagnostic |
| 25 | Quinshon Judkins | CLE | 167.8 | 137.5 | 198.9 | 0 | 49.5 | 15 | -10 | OVERPRICED | M9 diagnostic |
| 24 | Breece Hall | NYJ | 169.4 | 138 | 200.8 | 1.5 | 46.1 | 14 | -10 | OVERPRICED | M9 diagnostic |
| 13 | Lamar Jackson | BAL | 212.5 | 172 | 252.7 | 30 | 8.2 | 3 | -10 | OVERPRICED | M9 diagnostic |
| 16 | Malik Nabers | NYG | 215.4 | 184.6 | 246.5 | 46.9 | 16.5 | 6 | -10 | OVERPRICED | M9 production |
| 37 | Makai Lemon | PHI | 168.5 | 139 | 198.7 | 0 | 76.4 | 28 | -9 | OVERPRICED | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.2 | 174.7 | 237.3 | 38.3 | 12.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 19 | Oronde Gadsden | LAC | 173.4 | 145.8 | 201.8 | 3.9 | 100 | 11 | -8 | OVERPRICED | M9 production |
| 15 | Justin Herbert | LAC | 203.9 | 163.6 | 244.9 | 21.4 | 25.8 | 7 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 115.4 | Malik Willis | MIA | 5 | 26 | 21 | 261.1 | 78.6 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 184.2 | Geno Smith | NYJ | 14 | 33 | 19 | 208.5 | 26 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 120.3 | Daniel Jones | IND | 16 | 27 | 11 | 203.4 | 20.9 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 127.1 | Courtland Sutton | DEN | 17 | 49 | 32 | 201.9 | 33.4 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 106.9 | Mike Evans | SF | 12 | 40 | 28 | 222.2 | 53.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 148.1 | Jakobi Meyers | JAX | 32 | 56 | 24 | 176 | 7.5 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 116.1 | Quentin Johnston | LAC | 28 | 44 | 16 | 179.5 | 11 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 103.8 | DK Metcalf | PIT | 25 | 39 | 14 | 183.5 | 15 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 123.8 | Michael Pittman | PIT | 35 | 47 | 12 | 170.9 | 2.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 251.4 | Theo Johnson | NYG | 16 | 38 | 22 | 176.3 | 6.9 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |
| 195.1 | Dalton Schultz | HOU | 9 | 27 | 18 | 207.9 | 38.5 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 114.5 | George Kittle | SF | 2 | 14 | 12 | 254.9 | 85.5 | 92 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 159 | Juwan Johnson | NO | 11 | 22 | 11 | 198.1 | 28.6 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 181.1 | Hunter Henry | NE | 15 | 26 | 11 | 187 | 17.6 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 152.9 | Dallas Goedert | PHI | 12 | 20 | 8 | 197.1 | 27.7 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included, ADP has improved over the last 7 days |

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
| Christian McCaffrey | RB | SF | 29.6 | 1.69 | 0.41 | CLEAR_STARTER |
| Jaxon Smith-Njigba | WR | SEA | 24.3 | 0.87 | 0.44 | CLEAR_STARTER |
| Keenan Allen | WR | IND | 20.4 | 1.67 | 0.55 | COMMITTEE_FRINGE |
| Jakobi Meyers | WR | JAX | 19.9 | 1.83 | 0.35 | COMMITTEE_FRINGE |
| Trey McBride | TE | ARI | 19.4 | 2.39 | 0.25 | CLEAR_STARTER |
| Jauan Jennings | WR | MIN | 19.3 | 1.61 | 0.56 | COMMITTEE_FRINGE |
| Mack Hollins | WR | NE | 17.6 | 1.71 | 0.62 | DEPTH |
| Deebo Samuel | WR | SF | 16.4 | 1.51 | 0.51 | STARTER |
| Marquise Brown | WR | PHI | 16.3 | 1.44 | 0.54 | DEPTH |
| Quentin Johnston | WR | LAC | 16 | 1.75 | 0.5 | STARTER |

### Largest negative M9.1c adjustments

| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |
|---|---|---|---:|---:|---:|---|
| Nick Westbrook-Ikhine | WR | IND | -16.7 | -2.64 | 0.47 | COMMITTEE_FRINGE |
| Jack Bech | WR | LV | -16.1 | -1.22 | 0.57 | DEPTH |
| Blake Corum | RB | LAR | -14 | -0.7 | 0.57 | STARTER |
| Durham Smythe | TE | BAL | -13.3 | -7.74 | 0.58 | COMMITTEE_FRINGE |
| Kenneth Walker | RB | KC | -12.3 | -3.69 | 0.54 | CLEAR_STARTER |
| Jahan Dotson | WR | ATL | -12.3 | -4.86 | 0.51 | STARTER |
| Malik Willis | QB | MIA | -12 | -2.48 | 0.53 | CLEAR_STARTER |
| Derrick Henry | RB | BAL | -11.8 | -0.89 | 0.6 | CLEAR_STARTER |
| Saquon Barkley | RB | PHI | -11.8 | -1 | 0.6 | CLEAR_STARTER |
| Marquez Valdes-Scantling | WR | DAL | -11.6 | -0.59 | 0.48 | COMMITTEE_FRINGE |
