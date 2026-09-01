# FIE League Research Report — Stoned Lack Dynasty 30

Season: **2026**  
League ID: `1335691030116184065`  
Format: **DYNASTY**  
Teams: **12**  
Roster: `QB, RB, RB, WR, WR, TE, FLEX, FLEX, FLEX, K, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_dynasty_ppr`  
Pipeline: **complete_research_only**

## Model overview

| Position | Selected Model | Research Challenger | Validation Status | Exact Scoring | Key Reason |
|---|---|---|---|---|---|
| DST | — | — | NOT_APPLICABLE | None | position_not_rosterable |
| K | FIE_KICKER_DEDICATED | — | PRODUCTION_EXISTING | True | existing_dedicated_specialist_engine |
| QB | M9 | V9.7.5 | BLOCKED_STATISTICS | False | one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared |
| RB | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| TE | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| WR | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |

## League/scoring overview

PPR: **PPR** (1 per reception)  
Pass TD: **4** · Pass INT: **-2**  
Fumble: **0** · Fumble lost: **-2**  
Superflex/2QB: **No** · D/ST: **No** · K: **Yes**

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
League replacement: **215.4**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 295.3 | 254.2 | 336.3 | 79.9 | 8.1 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 64.8 | 132.9 | 17 | 15 | VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 57.6 | 196.4 | 23 | 20 | STRONG_VALUE | M9 diagnostic |
| 4 | Drake Maye | NE | 264.5 | 224.7 | 305.6 | 49.1 | 23.4 | 2 | -2 | FAIR | M9 diagnostic |
| 5 | Malik Willis | MIA | 261.1 | 221.9 | 301.9 | 45.7 | 230.6 | 26 | 21 | STRONG_VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 257.2 | 216.8 | 297.6 | 41.7 | 110.4 | 14 | 8 | VALUE | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 253.1 | 213.4 | 293.3 | 37.6 | 86.1 | 11 | 4 | FAIR | M9 diagnostic |
| 8 | Dak Prescott | DAL | 235.6 | 195.5 | 276.4 | 20.2 | 104 | 13 | 5 | FAIR | M9 diagnostic |
| 9 | Jalen Hurts | PHI | 234.2 | 194.2 | 274.3 | 18.7 | 61.2 | 7 | -2 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 229.8 | 189 | 271 | 14.3 | 94.4 | 12 | 2 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **145.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308 | 276.3 | 339.9 | 162.5 | 20.1 | 9 | 8 | VALUE | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.3 | 253.9 | 318.9 | 140.8 | 2.4 | 2 | 0 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268 | 236 | 300.6 | 122.5 | 1.3 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 264.9 | 233.3 | 295.8 | 119.4 | 12.7 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 264.6 | 232.5 | 296.3 | 119.1 | 14.4 | 5 | 0 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.3 | 275.9 | 98.5 | 26.1 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 237.4 | 205.8 | 269.4 | 91.9 | 17.4 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 228.6 | 197.1 | 259.9 | 83.1 | 22.5 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 181.2 | 242.8 | 66.3 | 15.4 | 6 | -3 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.5 | 238.9 | 62.5 | 42 | 16 | 6 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 62.2 | 59.4 | 23 | 12 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174.9 | 237.5 | 60.9 | 7.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 60.6 | 70.7 | 26 | 13 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202 | 170.7 | 233.7 | 56.5 | 46.5 | 19 | 5 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.8 | 168.2 | 231.2 | 54.3 | 28.8 | 12 | -3 | FAIR | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 199.6 | 168.9 | 231 | 54.1 | 44.1 | 18 | 2 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 51.3 | 16.8 | 7 | -10 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 191.4 | 165.8 | 218.5 | 45.9 | 57.4 | 22 | 4 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 183.4 | 152.8 | 214.9 | 37.9 | 51.1 | 20 | 1 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.6 | 150 | 212 | 35.1 | 69.4 | 25 | 5 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **148.4**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280.3 | 344.9 | 164.1 | 4.8 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 295.4 | 263.5 | 327.8 | 147.1 | 5.4 | 3 | 1 | FAIR | M9 diagnostic |
| 3 | Ja'Marr Chase | CIN | 271.9 | 239.7 | 304 | 123.5 | 3.1 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Amon-Ra St. Brown | DET | 264.1 | 232.1 | 295.8 | 115.7 | 6.5 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | Rashee Rice | KC | 250.6 | 219 | 282 | 102.2 | 38.5 | 17 | 12 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 98.8 | 34.1 | 15 | 9 | VALUE | M9 diagnostic |
| 7 | Drake London | ATL | 228.2 | 196.6 | 260.2 | 79.9 | 19.5 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chris Olave | NO | 225.3 | 194.3 | 256.9 | 77 | 30.7 | 13 | 5 | FAIR | M9 diagnostic |
| 9 | George Pickens | DAL | 224.5 | 193.2 | 256.6 | 76.2 | 21.4 | 9 | 0 | FAIR | M9 diagnostic |
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 73.8 | 89.8 | 40 | 30 | STRONG_VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 72.6 | 58.6 | 24 | 13 | VALUE | M9 diagnostic |
| 12 | CeeDee Lamb | DAL | 218.8 | 187.1 | 250.4 | 70.5 | 10.8 | 6 | -6 | FAIR | M9 diagnostic |
| 13 | Zay Flowers | BAL | 212.5 | 180.6 | 244.2 | 64.2 | 47.9 | 19 | 6 | FAIR | M9 diagnostic |
| 14 | Nico Collins | HOU | 205.8 | 173.8 | 238 | 57.5 | 26.8 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Garrett Wilson | NYJ | 201.7 | 170.4 | 233 | 53.3 | 35.4 | 16 | 1 | FAIR | M9 diagnostic |
| 16 | Malik Nabers | NYG | 201.6 | 170.5 | 233 | 53.3 | 11.9 | 7 | -9 | OVERPRICED | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 44.1 | 78.9 | 34 | 17 | VALUE | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 188 | 157.7 | 218.7 | 39.7 | 109.9 | 47 | 29 | STRONG_VALUE | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.7 | 151.2 | 214.8 | 34.4 | 8.4 | 5 | -14 | OVERPRICED | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.5 | 209.9 | 31.3 | 79.6 | 35 | 15 | VALUE | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **144.1**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 234.9 | 209.4 | 260.9 | 90.8 | 17.3 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | George Kittle | SF | 193.8 | 168.9 | 218.5 | 49.7 | 103.9 | 14 | 12 | VALUE | M9 diagnostic |
| 3 | Kyle Pitts | ATL | 187 | 162.3 | 212.1 | 42.9 | 66.1 | 8 | 5 | FAIR | M9 diagnostic |
| 4 | Brock Bowers | LV | 183.4 | 156.9 | 209.9 | 39.3 | 13 | 1 | -3 | FAIR | M9 diagnostic |
| 5 | Harold Fannin | CLE | 172.7 | 147.4 | 198 | 28.6 | 55.6 | 6 | 1 | FAIR | M9 diagnostic |
| 6 | Tucker Kraft | GB | 171.2 | 146.2 | 196.3 | 27.1 | 60.2 | 7 | 1 | FAIR | M9 diagnostic |
| 7 | Tyler Warren | IND | 165.1 | 139.9 | 190.2 | 21 | 35.8 | 4 | -3 | FAIR | M9 diagnostic |
| 8 | Sam LaPorta | DET | 158 | 133 | 183.2 | 13.9 | 53.9 | 5 | -3 | FAIR | M9 diagnostic |
| 9 | Isaiah Likely | NYG | 157.3 | 132.8 | 182.1 | 13.2 | 97.2 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Dalton Schultz | HOU | 154.1 | 129.8 | 178.5 | 10 | 218.8 | 28 | 18 | STRONG_VALUE | M9 diagnostic |

### K

Selected model: **FIE_KICKER_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cameron Dicker | LAC | 8.2 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | Harrison Mevis | LAR | 8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | Jake Bates | DET | 7.9 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | Tyler Loop | BAL | 7.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | Brandon Aubrey | DAL | 7.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | Jason Myers | SEA | 7.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | Evan McPherson | CIN | 7.6 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | Ka'imi Fairbairn | HOU | 7.6 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | Will Reichard | MIN | 7.4 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | Cam Little | JAX | 7.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 73.8 | 89.8 | 40 | 30 | STRONG_VALUE | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 44.1 | 78.9 | 34 | 17 | VALUE | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.5 | 209.9 | 31.3 | 79.6 | 35 | 15 | VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 72.6 | 58.6 | 24 | 13 | VALUE | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 60.6 | 70.7 | 26 | 13 | VALUE | M9 diagnostic |
| 5 | Rashee Rice | KC | 250.6 | 219 | 282 | 102.2 | 38.5 | 17 | 12 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 62.2 | 59.4 | 23 | 12 | VALUE | M9 diagnostic |
| 29 | DK Metcalf | PIT | 169.4 | 139.3 | 200.8 | 21.1 | 93.1 | 41 | 12 | VALUE | M9 diagnostic |
| 28 | Wan'Dale Robinson | TEN | 170.7 | 140.7 | 201 | 22.3 | 88.4 | 39 | 11 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 98.8 | 34.1 | 15 | 9 | VALUE | M9 diagnostic |
| 21 | DJ Moore | BUF | 179 | 149.2 | 209.3 | 30.6 | 72 | 30 | 9 | VALUE | M9 diagnostic |
| 1 | Christian McCaffrey | SF | 308 | 276.3 | 339.9 | 162.5 | 20.1 | 9 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 60 | Bhayshul Tuten | JAX | 63.9 | 34 | 93.9 | -81.6 | 68.8 | 24 | -36 | STRONG_FADE | M9 diagnostic |
| 57 | Luther Burden | CHI | 125.4 | 93.9 | 156.8 | -23 | 49.2 | 21 | -36 | STRONG_FADE | M9 diagnostic |
| 62 | Jordyn Tyson | NO | 111 | 83.2 | 139.3 | -37.4 | 65.1 | 28 | -34 | STRONG_FADE | M9 diagnostic |
| 42 | Ladd McConkey | LAC | 153.3 | 122 | 184.4 | 5 | 31.1 | 14 | -28 | STRONG_FADE | M9 diagnostic |
| 34 | Emeka Egbuka | TB | 164.7 | 133.9 | 196.3 | 16.3 | 25.6 | 11 | -23 | STRONG_FADE | M9 diagnostic |
| 31 | Kenyon Sadiq | NYJ | 100.2 | 77.5 | 123.9 | -43.9 | 91.7 | 10 | -21 | STRONG_FADE | M9 diagnostic |
| 25 | Joe Burrow | CIN | 181.4 | 141.4 | 222.6 | -34 | 41.1 | 4 | -21 | STRONG_FADE | M9 diagnostic |
| 46 | Brian Thomas | JAX | 139.8 | 109.1 | 170.9 | -8.6 | 62.6 | 26 | -20 | STRONG_FADE | M9 diagnostic |
| 44 | Marvin Harrison | ARI | 151.6 | 121.6 | 182.6 | 3.3 | 62.4 | 25 | -19 | STRONG_FADE | M9 diagnostic |
| 48 | Chuba Hubbard | CAR | 99.8 | 71.3 | 129.3 | -45.7 | 89.8 | 30 | -18 | STRONG_FADE | M9 diagnostic |
| 46 | Kyle Monangai | CHI | 103.1 | 74.4 | 132.3 | -42.4 | 82.2 | 28 | -18 | STRONG_FADE | M9 diagnostic |
| 19 | Colston Loveland | CHI | 127.1 | 101.9 | 152.7 | -17 | 29.9 | 3 | -16 | OVERPRICED | M9 diagnostic |
| 26 | Tetairoa McMillan | CAR | 171.8 | 141.1 | 202.9 | 23.5 | 24.6 | 10 | -16 | OVERPRICED | M9 diagnostic |
| 21 | Caleb Williams | CHI | 184.4 | 144.4 | 224 | -31 | 52 | 6 | -15 | OVERPRICED | M9 diagnostic |
| 28 | TreVeyon Henderson | NE | 156.7 | 126.8 | 187.9 | 11.2 | 33.8 | 13 | -15 | OVERPRICED | M9 diagnostic |
| 23 | Dalton Kincaid | BUF | 110.8 | 86.2 | 135.6 | -33.3 | 85.6 | 9 | -14 | OVERPRICED | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.7 | 151.2 | 214.8 | 34.4 | 8.4 | 5 | -14 | OVERPRICED | M9 diagnostic |
| 55 | Omar Cooper | NYJ | 127.1 | 98.5 | 156.2 | -21.3 | 98.1 | 42 | -13 | OVERPRICED | M9 diagnostic |
| 50 | Jordan Addison | MIN | 131.1 | 100.8 | 161.6 | -17.2 | 83.2 | 37 | -13 | OVERPRICED | M9 diagnostic |
| 20 | Jaxson Dart | NYG | 186.8 | 146.7 | 227.3 | -28.6 | 74.5 | 9 | -11 | OVERPRICED | M9 diagnostic |
| 31 | DeVonta Smith | PHI | 166.7 | 136.3 | 197.9 | 18.4 | 48.7 | 20 | -11 | OVERPRICED | M9 diagnostic |
| 13 | Lamar Jackson | BAL | 212.4 | 171.9 | 252.7 | -3 | 32.9 | 3 | -10 | OVERPRICED | M9 diagnostic |
| 32 | Rome Odunze | CHI | 166.2 | 135.7 | 197.4 | 17.9 | 50.7 | 22 | -10 | OVERPRICED | M9 diagnostic |
| 25 | Quinshon Judkins | CLE | 168 | 137.6 | 199 | 22.5 | 40.7 | 15 | -10 | OVERPRICED | M9 diagnostic |
| 24 | Breece Hall | NYJ | 169.4 | 138 | 200.8 | 23.9 | 37.7 | 14 | -10 | OVERPRICED | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 51.3 | 16.8 | 7 | -10 | OVERPRICED | M9 diagnostic |
| 40 | KC Concepcion | CLE | 156.4 | 126.8 | 186.7 | 8 | 75.7 | 31 | -9 | OVERPRICED | M9 diagnostic |
| 16 | Malik Nabers | NYG | 201.6 | 170.5 | 233 | 53.3 | 11.9 | 7 | -9 | OVERPRICED | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174.9 | 237.5 | 60.9 | 7.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 18 | Bo Nix | DEN | 200.3 | 160.5 | 241 | -15.1 | 80.2 | 10 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 230.6 | Malik Willis | MIA | 5 | 26 | 21 | 261.1 | 45.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 196.4 | Kyler Murray | MIN | 3 | 23 | 20 | 273.1 | 57.6 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 132.9 | Matthew Stafford | LAR | 2 | 17 | 15 | 280.2 | 64.8 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 159.9 | Tyler Shough | NO | 12 | 22 | 10 | 215.4 | 0 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 110.4 | Brock Purdy | SF | 6 | 14 | 8 | 257.2 | 41.7 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 221.6 | MarShawn Lloyd | GB | 34 | 64 | 30 | 149 | 3.5 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 152.8 | Aaron Jones | MIN | 36 | 49 | 13 | 145.5 | 0 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 119.4 | Tony Pollard | TEN | 26 | 38 | 12 | 167 | 21.5 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 143.5 | Tyrone Tracy | NYG | 35 | 46 | 11 | 147.6 | 2.1 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 122.5 | Kenny Gainwell | TB | 32 | 41 | 9 | 152.3 | 6.8 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 109.9 | Courtland Sutton | DEN | 18 | 47 | 29 | 188 | 39.7 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 154.2 | Deebo Samuel | SF | 41 | 63 | 22 | 155.7 | 7.3 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 134.5 | Jakobi Meyers | JAX | 35 | 55 | 20 | 162.2 | 13.9 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 143.7 | Stefon Diggs | WAS | 39 | 59 | 20 | 157.3 | 8.9 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 106.8 | Michael Pittman | PIT | 27 | 45 | 18 | 170.9 | 22.5 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 125.9 | Romeo Doubs | NE | 36 | 51 | 15 | 161.2 | 12.8 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 107.9 | Quentin Johnston | LAC | 33 | 46 | 13 | 165.3 | 17 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 137.2 | Khalil Shakir | BUF | 45 | 56 | 11 | 148.4 | 0 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 218.8 | Dalton Schultz | HOU | 10 | 28 | 18 | 154.1 | 10 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 103.9 | George Kittle | SF | 2 | 14 | 12 | 193.8 | 49.7 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 165.3 | Juwan Johnson | NO | 12 | 22 | 10 | 146.5 | 2.4 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 169.6 | Chig Okonkwo | WAS | 14 | 23 | 9 | 144.1 | 0 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

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
