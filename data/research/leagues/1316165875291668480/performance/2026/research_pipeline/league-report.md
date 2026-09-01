# FIE League Research Report — Genesis Dynasty - sixteen now & for the future

Season: **2026**  
League ID: `1316165875291668480`  
Format: **DYNASTY**  
Teams: **16**  
Roster: `QB, RB, WR, WR, TE, FLEX, FLEX, WRRB_FLEX, REC_FLEX, SUPER_FLEX, K, DEF, BN, BN, BN, BN, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_dynasty_2qb`  
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

Bonuses: `{"bonus_pass_yd_300": 2.0, "bonus_pass_yd_400": 1.0, "bonus_rec_te": 0.5, "bonus_rec_yd_100": 2.0, "bonus_rush_yd_100": 2.0}`

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
League replacement: **150.8**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 295.9 | 253.1 | 338.5 | 145.1 | 1.7 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 238.8 | 322.1 | 129.4 | 86.9 | 21 | 19 | STRONG_VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 232.5 | 314.7 | 122.3 | 93.3 | 23 | 20 | STRONG_VALUE | M9 diagnostic |
| 4 | Drake Maye | NE | 262.7 | 221.1 | 305.4 | 111.9 | 5.7 | 2 | -2 | FAIR | M9 diagnostic |
| 5 | Malik Willis | MIA | 261.1 | 220.2 | 303.6 | 110.3 | 115.4 | 26 | 21 | STRONG_VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 256.8 | 214.7 | 298.9 | 106 | 47.7 | 13 | 7 | FAIR | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 250.6 | 209.5 | 292.6 | 99.9 | 37.2 | 11 | 4 | FAIR | M9 diagnostic |
| 8 | Dak Prescott | DAL | 237 | 195.1 | 279.4 | 86.2 | 51 | 14 | 6 | FAIR | M9 diagnostic |
| 9 | Jalen Hurts | PHI | 232.1 | 190.5 | 273.8 | 81.3 | 26.7 | 8 | -1 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 227.5 | 185.1 | 270.4 | 76.7 | 35.4 | 10 | 0 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **128.1**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308.8 | 275.8 | 341.9 | 180.7 | 31 | 9 | 8 | VALUE | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 288 | 254.5 | 321.8 | 159.9 | 2.7 | 1 | -1 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 267.7 | 234.5 | 301.5 | 139.6 | 3.2 | 2 | -1 | FAIR | M9 diagnostic |
| 4 | De'Von Achane | MIA | 265.4 | 232.2 | 298.2 | 137.3 | 21.3 | 6 | 2 | FAIR | M9 diagnostic |
| 5 | Jonathan Taylor | IND | 264.1 | 231.4 | 296.1 | 136 | 22.2 | 7 | 2 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 211.1 | 277 | 115.9 | 35.5 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 240.8 | 208.1 | 274 | 112.7 | 23.9 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 229.2 | 196.6 | 261.7 | 101.1 | 33.5 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 180.2 | 243.8 | 83.7 | 17.3 | 4 | -5 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 176.5 | 240 | 79.9 | 53.4 | 16 | 6 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 175.7 | 239.7 | 79.6 | 71.1 | 22 | 11 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174 | 238.7 | 78.3 | 12.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 174.4 | 238.7 | 78 | 85.1 | 26 | 13 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 205 | 172.6 | 237.8 | 76.9 | 62.1 | 19 | 5 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 200.5 | 167.8 | 233.1 | 72.4 | 41.8 | 12 | -3 | FAIR | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 197.5 | 165.7 | 230 | 69.4 | 57.9 | 18 | 2 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.3 | 164.3 | 228.7 | 68.2 | 20.9 | 5 | -12 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 189 | 162.4 | 217 | 60.9 | 73.5 | 23 | 5 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 182.1 | 150.4 | 214.7 | 54 | 62.6 | 20 | 1 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.3 | 148.8 | 212.9 | 52.2 | 80.9 | 25 | 5 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **125.8**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 279.1 | 346.2 | 186.7 | 6.1 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 297.9 | 264.7 | 331.6 | 172.1 | 7.2 | 3 | 1 | FAIR | M9 diagnostic |
| 3 | Ja'Marr Chase | CIN | 273.5 | 240 | 307 | 147.7 | 4 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Amon-Ra St. Brown | DET | 264.2 | 230.9 | 297.2 | 138.4 | 8.6 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | Rashee Rice | KC | 249 | 216.3 | 281.7 | 123.2 | 50.6 | 18 | 13 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 214.9 | 279.8 | 121.4 | 48.8 | 17 | 11 | VALUE | M9 diagnostic |
| 7 | Drake London | ATL | 230.5 | 197.6 | 263.7 | 104.6 | 24.7 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | George Pickens | DAL | 225.4 | 192.8 | 258.7 | 99.5 | 30.4 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Chris Olave | NO | 225 | 192.8 | 257.8 | 99.2 | 40.8 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Mike Evans | SF | 222.2 | 190 | 255.3 | 96.4 | 106.9 | 40 | 30 | STRONG_VALUE | M9 diagnostic |
| 11 | CeeDee Lamb | DAL | 221.2 | 188.1 | 253.9 | 95.3 | 17.7 | 7 | -4 | FAIR | M9 diagnostic |
| 12 | Jaylen Waddle | DEN | 221 | 189.1 | 252.9 | 95.2 | 70.6 | 26 | 14 | VALUE | M9 diagnostic |
| 13 | Zay Flowers | BAL | 212.5 | 179.3 | 245.4 | 86.6 | 55.7 | 20 | 7 | FAIR | M9 diagnostic |
| 14 | Nico Collins | HOU | 206.1 | 172.8 | 239.5 | 80.3 | 34.1 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Malik Nabers | NYG | 202.3 | 169.9 | 234.9 | 76.5 | 16.5 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 16 | Garrett Wilson | NYJ | 199.7 | 167.2 | 232.3 | 73.9 | 44.5 | 15 | -1 | FAIR | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 161.1 | 224.7 | 66.7 | 96.5 | 36 | 19 | STRONG_VALUE | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 187.1 | 155.6 | 218.9 | 61.3 | 127.1 | 49 | 31 | STRONG_VALUE | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.6 | 149.7 | 215.9 | 56.8 | 14.3 | 5 | -14 | OVERPRICED | M9 diagnostic |
| 20 | Michael Wilson | ARI | 180.2 | 148.9 | 211.6 | 54.3 | 94.9 | 35 | 15 | VALUE | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **125.8**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 283.3 | 253.6 | 313.6 | 157.5 | 19.5 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | George Kittle | SF | 233 | 204.1 | 261.7 | 107.2 | 114.5 | 14 | 12 | VALUE | M9 diagnostic |
| 3 | Kyle Pitts | ATL | 226.2 | 197.3 | 255.3 | 100.4 | 74.4 | 8 | 5 | FAIR | M9 diagnostic |
| 4 | Brock Bowers | LV | 219.5 | 188.7 | 250.3 | 93.7 | 11.5 | 1 | -3 | FAIR | M9 diagnostic |
| 5 | Harold Fannin | CLE | 208.2 | 178.8 | 237.6 | 82.4 | 56.3 | 5 | 0 | FAIR | M9 diagnostic |
| 6 | Tucker Kraft | GB | 203.4 | 174.3 | 232.6 | 77.6 | 61.4 | 6 | 0 | FAIR | M9 diagnostic |
| 7 | Tyler Warren | IND | 195.6 | 166.3 | 224.8 | 69.8 | 38.3 | 4 | -3 | FAIR | M9 diagnostic |
| 8 | Sam LaPorta | DET | 188.8 | 159.8 | 218.2 | 63 | 64 | 7 | -1 | FAIR | M9 diagnostic |
| 9 | Isaiah Likely | NYG | 188.3 | 159.8 | 217.2 | 62.5 | 104.7 | 12 | 3 | FAIR | M9 diagnostic |
| 10 | Dalton Schultz | HOU | 185.2 | 156.8 | 213.7 | 59.4 | 195.1 | 27 | 17 | VALUE | M9 diagnostic |

### DST

Selected model: **FIE_DST_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LV D/ST | LV | 43.6 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | TEN D/ST | TEN | 43 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | NYJ D/ST | NYJ | 37.9 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | MIA D/ST | MIA | 37.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | LAC D/ST | LAC | 35.4 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | PIT D/ST | PIT | 33.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | JAX D/ST | JAX | 33.4 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | DAL D/ST | DAL | 31.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | DET D/ST | DET | 31.4 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | CIN D/ST | CIN | 31.1 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

### K

Selected model: **FIE_KICKER_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cameron Dicker | LAC | 9.1 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | Harrison Mevis | LAR | 8.9 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | Jake Bates | DET | 8.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | Tyler Loop | BAL | 8.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | Jason Myers | SEA | 8.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | Brandon Aubrey | DAL | 8.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | Evan McPherson | CIN | 8.6 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | Ka'imi Fairbairn | HOU | 8.5 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | Will Reichard | MIN | 8.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | Cam Little | JAX | 8.2 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Kyler Murray | MIN | 273.1 | 232.5 | 314.7 | 122.3 | 93.3 | 23 | 20 | STRONG_VALUE | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 238.8 | 322.1 | 129.4 | 86.9 | 21 | 19 | STRONG_VALUE | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 161.1 | 224.7 | 66.7 | 96.5 | 36 | 19 | STRONG_VALUE | M9 diagnostic |
| 20 | Michael Wilson | ARI | 180.2 | 148.9 | 211.6 | 54.3 | 94.9 | 35 | 15 | VALUE | M9 diagnostic |
| 12 | Jaylen Waddle | DEN | 221 | 189.1 | 252.9 | 95.2 | 70.6 | 26 | 14 | VALUE | M9 diagnostic |
| 5 | Rashee Rice | KC | 249 | 216.3 | 281.7 | 123.2 | 50.6 | 18 | 13 | VALUE | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 174.4 | 238.7 | 78 | 85.1 | 26 | 13 | VALUE | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 214.9 | 279.8 | 121.4 | 48.8 | 17 | 11 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 175.7 | 239.7 | 79.6 | 71.1 | 22 | 11 | VALUE | M9 diagnostic |
| 11 | Tyler Shough | NO | 218.3 | 176.9 | 259.4 | 67.5 | 83.4 | 20 | 9 | VALUE | M9 diagnostic |
| 21 | DJ Moore | BUF | 179 | 148.1 | 210.5 | 53.2 | 80.6 | 30 | 9 | VALUE | M9 diagnostic |
| 1 | Christian McCaffrey | SF | 308.8 | 275.8 | 341.9 | 180.7 | 31 | 9 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 62 | Bhayshul Tuten | JAX | 63.3 | 32.4 | 94.4 | -64.8 | 79.1 | 24 | -38 | STRONG_FADE | M9 diagnostic |
| 56 | Luther Burden | CHI | 125.8 | 93.2 | 158.5 | 0 | 52.8 | 19 | -37 | STRONG_FADE | M9 diagnostic |
| 61 | Jordyn Tyson | NO | 111 | 82.2 | 140.4 | -14.8 | 69.5 | 25 | -36 | STRONG_FADE | M9 diagnostic |
| 42 | Ladd McConkey | LAC | 153.4 | 120.7 | 185.6 | 27.6 | 42.1 | 14 | -28 | STRONG_FADE | M9 diagnostic |
| 31 | Kenyon Sadiq | NYJ | 120.2 | 93.7 | 147.9 | -5.6 | 89.3 | 9 | -22 | STRONG_FADE | M9 diagnostic |
| 33 | Emeka Egbuka | TB | 164.9 | 133 | 197.8 | 39.1 | 32.8 | 11 | -22 | STRONG_FADE | M9 diagnostic |
| 39 | Cam Ward | TEN | 112.7 | 73.4 | 152.9 | -38.1 | 82.7 | 19 | -20 | STRONG_FADE | M9 diagnostic |
| 44 | Marvin Harrison | ARI | 150 | 118.9 | 182.2 | 24.2 | 68.3 | 24 | -20 | STRONG_FADE | M9 diagnostic |
| 46 | Brian Thomas | JAX | 138.6 | 106.9 | 170.9 | 12.8 | 71.7 | 27 | -19 | STRONG_FADE | M9 diagnostic |
| 46 | Kyle Monangai | CHI | 102.9 | 73.2 | 133.1 | -25.2 | 98.6 | 28 | -18 | STRONG_FADE | M9 diagnostic |
| 24 | Joe Burrow | CIN | 182.2 | 140.6 | 225.1 | 31.5 | 15.1 | 6 | -18 | STRONG_FADE | M9 diagnostic |
| 22 | Caleb Williams | CHI | 182.5 | 140.7 | 223.7 | 31.7 | 13.7 | 5 | -17 | OVERPRICED | M9 diagnostic |
| 26 | Tetairoa McMillan | CAR | 171.7 | 139.8 | 204.1 | 45.9 | 29.6 | 9 | -17 | OVERPRICED | M9 diagnostic |
| 26 | Dalton Kincaid | BUF | 130.6 | 101.9 | 159.5 | 4.8 | 98.4 | 10 | -16 | OVERPRICED | M9 diagnostic |
| 18 | Colston Loveland | CHI | 152.6 | 123.1 | 182.4 | 26.8 | 28.2 | 3 | -15 | OVERPRICED | M9 diagnostic |
| 28 | TreVeyon Henderson | NE | 156.9 | 126 | 189.1 | 28.8 | 43.8 | 13 | -15 | OVERPRICED | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.6 | 149.7 | 215.9 | 56.8 | 14.3 | 5 | -14 | OVERPRICED | M9 diagnostic |
| 27 | Jordan Love | GB | 167.5 | 126 | 209.3 | 16.7 | 58.4 | 15 | -12 | OVERPRICED | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.3 | 164.3 | 228.7 | 68.2 | 20.9 | 5 | -12 | OVERPRICED | M9 diagnostic |
| 33 | C.J. Stroud | HOU | 144.4 | 103.8 | 185.3 | -6.4 | 91.7 | 22 | -11 | OVERPRICED | M9 diagnostic |
| 48 | Jordan Addison | MIN | 132.1 | 100.5 | 163.7 | 6.3 | 97.7 | 37 | -11 | OVERPRICED | M9 diagnostic |
| 20 | Jaxson Dart | NYG | 185.8 | 144 | 227.9 | 35 | 27 | 9 | -11 | OVERPRICED | M9 diagnostic |
| 26 | Quinshon Judkins | CLE | 166.6 | 135.3 | 198.7 | 38.5 | 49.5 | 15 | -11 | OVERPRICED | M9 diagnostic |
| 32 | DeVonta Smith | PHI | 166.3 | 134.6 | 198.8 | 40.5 | 60.7 | 22 | -10 | OVERPRICED | M9 diagnostic |
| 31 | Rome Odunze | CHI | 166.4 | 134.7 | 198.8 | 40.6 | 59.6 | 21 | -10 | OVERPRICED | M9 diagnostic |
| 13 | Lamar Jackson | BAL | 210.9 | 168.8 | 252.9 | 60.1 | 8.2 | 3 | -10 | OVERPRICED | M9 diagnostic |
| 43 | Parker Washington | JAX | 152.9 | 120.2 | 185 | 27.1 | 92.4 | 34 | -9 | OVERPRICED | M9 diagnostic |
| 40 | KC Concepcion | CLE | 156.4 | 125.7 | 187.8 | 30.6 | 84.6 | 31 | -9 | OVERPRICED | M9 diagnostic |
| 23 | Breece Hall | NYJ | 170.2 | 137.8 | 202.7 | 42.1 | 46.1 | 14 | -9 | OVERPRICED | M9 diagnostic |
| 15 | Malik Nabers | NYG | 202.3 | 169.9 | 234.9 | 76.5 | 16.5 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174 | 238.7 | 78.3 | 12.8 | 3 | -9 | OVERPRICED | M9 diagnostic |
| 19 | Oronde Gadsden | LAC | 150.6 | 122.8 | 179.4 | 24.8 | 100 | 11 | -8 | OVERPRICED | M9 diagnostic |
| 15 | Justin Herbert | LAC | 206.8 | 164.7 | 249.4 | 56 | 25.8 | 7 | -8 | OVERPRICED | M9 diagnostic |
| 12 | Jayden Daniels | WAS | 218 | 176.2 | 260.2 | 67.3 | 10.6 | 4 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 340.3 | Marcus Mariota | WAS | 28 | 52 | 24 | 154.6 | 3.9 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 318 | Jameis Winston | NYG | 26 | 48 | 22 | 170.5 | 19.7 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 115.4 | Malik Willis | MIA | 5 | 26 | 21 | 261.1 | 110.3 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 184.2 | Geno Smith | NYJ | 14 | 33 | 19 | 208.5 | 57.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 206.6 | J.J. McCarthy | MIN | 25 | 37 | 12 | 181.4 | 30.6 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 120.3 | Daniel Jones | IND | 16 | 27 | 11 | 202.8 | 52 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 253.2 | James Conner | ARI | 39 | 72 | 33 | 133.8 | 5.7 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 217.6 | MarShawn Lloyd | GB | 34 | 64 | 30 | 149 | 20.9 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 203.5 | Alvin Kamara | NO | 37 | 58 | 21 | 139.1 | 11 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 176.1 | Aaron Jones | MIN | 36 | 52 | 16 | 144.5 | 16.4 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 134.7 | Tony Pollard | TEN | 25 | 39 | 14 | 168.8 | 40.7 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 155.1 | Tyrone Tracy | NYG | 35 | 46 | 11 | 147.2 | 19.1 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 139.7 | Kenny Gainwell | TB | 31 | 41 | 10 | 152.3 | 24.2 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 170.5 | Chris Rodriguez | JAX | 40 | 49 | 9 | 132.5 | 4.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 127.1 | Courtland Sutton | DEN | 18 | 49 | 31 | 187.1 | 61.3 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 209.1 | Troy Franklin | DEN | 49 | 80 | 31 | 131.8 | 6 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 106.9 | Mike Evans | SF | 10 | 40 | 30 | 222.2 | 96.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 210 | Tre Tucker | LV | 53 | 81 | 28 | 128.4 | 2.5 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 158.1 | Stefon Diggs | WAS | 38 | 61 | 23 | 157.3 | 31.5 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 166 | Deebo Samuel | SF | 41 | 64 | 23 | 155.7 | 29.9 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 123.8 | Michael Pittman | PIT | 27 | 47 | 20 | 170.9 | 45.1 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 148.1 | Jakobi Meyers | JAX | 36 | 55 | 19 | 160.4 | 34.6 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 188.2 | Jalen Nailor | LV | 51 | 70 | 19 | 130.6 | 4.8 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 141.5 | Romeo Doubs | NE | 35 | 52 | 17 | 161.2 | 35.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 107.1 | Wan'Dale Robinson | TEN | 28 | 41 | 13 | 170.7 | 44.9 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 149.1 | Khalil Shakir | BUF | 45 | 56 | 11 | 147.7 | 21.9 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 103.8 | DK Metcalf | PIT | 29 | 39 | 10 | 169.4 | 43.6 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 116.1 | Quentin Johnston | LAC | 34 | 44 | 10 | 164.8 | 38.9 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 304.4 | Darren Waller | CAR | 21 | 45 | 24 | 146.1 | 20.3 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 251.4 | Theo Johnson | NYG | 17 | 38 | 21 | 153.1 | 27.3 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 195.1 | Dalton Schultz | HOU | 10 | 27 | 17 | 185.2 | 59.4 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 114.5 | George Kittle | SF | 2 | 14 | 12 | 233 | 107.2 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 244.1 | Jake Tonges | SF | 25 | 37 | 12 | 130.6 | 4.8 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 159 | Juwan Johnson | NO | 12 | 22 | 10 | 175.3 | 49.5 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |
| 181.1 | Hunter Henry | NE | 16 | 26 | 10 | 164.8 | 39 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, League Superflex/QB scarcity is included |

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
