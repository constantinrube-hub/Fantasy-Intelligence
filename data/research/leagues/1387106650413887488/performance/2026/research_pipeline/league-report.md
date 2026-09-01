# FIE League Research Report — German Football League

Season: **2026**  
League ID: `1387106650413887488`  
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
Pass TD: **4** · Pass INT: **-2**  
Fumble: **0** · Fumble lost: **-2**  
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
League replacement: **215.4**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 295.3 | 254.2 | 336.3 | 79.9 | 21 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 64.8 | 95.3 | 11 | 9 | VALUE | M9 diagnostic |
| 3 | Kyler Murray | MIN | 273.1 | 234.1 | 313.1 | 57.6 | 161.6 | 19 | 16 | VALUE | M9 diagnostic |
| 4 | Drake Maye | NE | 264.5 | 224.7 | 305.6 | 49.1 | 47.1 | 3 | -1 | FAIR | M9 diagnostic |
| 5 | Malik Willis | MIA | 261.1 | 221.9 | 301.9 | 45.7 | 208.4 | 25 | 20 | STRONG_VALUE | M9 diagnostic |
| 6 | Brock Purdy | SF | 257.2 | 216.8 | 297.6 | 41.7 | 123.3 | 15 | 9 | VALUE | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 253.1 | 213.4 | 293.3 | 37.6 | 110 | 13 | 6 | FAIR | M9 diagnostic |
| 8 | Dak Prescott | DAL | 235.6 | 195.5 | 276.4 | 20.2 | 77.5 | 8 | 0 | FAIR | M9 diagnostic |
| 9 | Jalen Hurts | PHI | 234.2 | 194.2 | 274.3 | 18.7 | 60 | 5 | -4 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 229.8 | 189 | 271 | 14.3 | 100.7 | 12 | 2 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **169.4**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308 | 276.3 | 339.9 | 138.6 | 5.4 | 3 | 2 | FAIR | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.3 | 253.9 | 318.9 | 116.9 | 2.2 | 2 | 0 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268 | 236 | 300.6 | 98.6 | 1.9 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 264.9 | 233.3 | 295.8 | 95.5 | 7.2 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 264.6 | 232.5 | 296.3 | 95.2 | 13.1 | 7 | 2 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.3 | 275.9 | 74.6 | 19.9 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 237.4 | 205.8 | 269.4 | 68 | 8.6 | 5 | -2 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 228.6 | 197.1 | 259.9 | 59.2 | 16.7 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 181.2 | 242.8 | 42.4 | 26 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.5 | 238.9 | 38.6 | 28.5 | 14 | 4 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 38.3 | 44.3 | 20 | 9 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174.9 | 237.5 | 37 | 14.2 | 8 | -4 | FAIR | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 36.7 | 48.4 | 21 | 8 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202 | 170.7 | 233.7 | 32.6 | 20 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.8 | 168.2 | 231.2 | 30.4 | 12.6 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 199.6 | 168.9 | 231 | 30.2 | 42 | 18 | 2 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 27.4 | 15.3 | 9 | -8 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 191.4 | 165.8 | 218.5 | 22 | 35.9 | 17 | -1 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 183.4 | 152.8 | 214.9 | 14 | 33.5 | 15 | -4 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.6 | 150 | 212 | 11.2 | 52.6 | 22 | 2 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **170.9**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280.3 | 344.9 | 141.6 | 4.4 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 309.4 | 277.5 | 341.9 | 138.5 | 6.2 | 3 | 1 | FAIR | M9 production |
| 3 | Ja'Marr Chase | CIN | 285.9 | 253.9 | 317.9 | 115 | 3.2 | 1 | -2 | FAIR | M9 production |
| 4 | Amon-Ra St. Brown | DET | 278 | 246 | 309.7 | 107.1 | 8.8 | 4 | 0 | FAIR | M9 production |
| 5 | Rashee Rice | KC | 264.6 | 232.3 | 296.2 | 93.7 | 29 | 12 | 7 | FAIR | M9 production |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 76.3 | 17.1 | 7 | 1 | FAIR | M9 diagnostic |
| 7 | Drake London | ATL | 242.2 | 210.7 | 274.1 | 71.3 | 17.7 | 8 | 1 | FAIR | M9 production |
| 8 | Chris Olave | NO | 239.3 | 208.3 | 270.9 | 68.4 | 30.1 | 13 | 5 | FAIR | M9 production |
| 9 | George Pickens | DAL | 238.5 | 207.3 | 270.5 | 67.6 | 22.1 | 9 | 0 | FAIR | M9 production |
| 10 | CeeDee Lamb | DAL | 232.8 | 201.5 | 264 | 61.9 | 10.4 | 5 | -5 | FAIR | M9 production |
| 11 | Zay Flowers | BAL | 226.5 | 194.6 | 258.2 | 55.6 | 41.8 | 19 | 8 | VALUE | M9 production |
| 12 | Mike Evans | SF | 222.2 | 191.2 | 254 | 51.3 | 62.4 | 27 | 15 | VALUE | M9 diagnostic |
| 13 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 50.1 | 44.7 | 20 | 7 | FAIR | M9 diagnostic |
| 14 | Nico Collins | HOU | 219.8 | 188.3 | 251.5 | 48.9 | 25.1 | 10 | -4 | FAIR | M9 production |
| 15 | Garrett Wilson | NYJ | 215.6 | 184.5 | 246.8 | 44.7 | 46.4 | 21 | 6 | FAIR | M9 production |
| 16 | Malik Nabers | NYG | 215.6 | 184.7 | 246.7 | 44.7 | 26.9 | 11 | -5 | FAIR | M9 production |
| 17 | Courtland Sutton | DEN | 202 | 171.1 | 233.2 | 31.1 | 80.6 | 35 | 18 | STRONG_VALUE | M9 production |
| 18 | Justin Jefferson | MIN | 196.7 | 166.1 | 228.1 | 25.8 | 11.3 | 6 | -12 | OVERPRICED | M9 production |
| 19 | Michael Wilson | ARI | 193.6 | 162.6 | 224.5 | 22.7 | 85.9 | 36 | 17 | VALUE | M9 production |
| 20 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 21.6 | 50.1 | 22 | 2 | FAIR | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **164.8**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 253.4 | 227.9 | 279.6 | 88.6 | 24.3 | 2 | 1 | FAIR | M9 production |
| 2 | George Kittle | SF | 212.4 | 187 | 237.5 | 47.6 | 83.2 | 9 | 7 | FAIR | M9 production |
| 3 | Kyle Pitts | ATL | 205.6 | 180.2 | 231 | 40.8 | 68.6 | 7 | 4 | FAIR | M9 production |
| 4 | Brock Bowers | LV | 201.9 | 175.8 | 228.1 | 37.1 | 23.2 | 1 | -3 | FAIR | M9 production |
| 5 | Harold Fannin | CLE | 191.3 | 166 | 216.7 | 26.5 | 70.6 | 8 | 3 | FAIR | M9 production |
| 6 | Tucker Kraft | GB | 189.8 | 164.6 | 215.1 | 24.9 | 62.8 | 6 | 0 | FAIR | M9 production |
| 7 | Tyler Warren | IND | 183.7 | 158.8 | 208.6 | 18.8 | 49.7 | 4 | -3 | FAIR | M9 production |
| 8 | Sam LaPorta | DET | 176.6 | 151.8 | 201.5 | 11.8 | 58.8 | 5 | -3 | FAIR | M9 production |
| 9 | Dalton Schultz | HOU | 172.7 | 147.9 | 197.5 | 7.8 | 188.8 | 23 | 14 | VALUE | M9 production |
| 10 | Travis Kelce | KC | 171.1 | 146.3 | 195.9 | 6.3 | 89.1 | 11 | 1 | FAIR | M9 production |

### DST

Selected model: **FIE_DST_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | JAX D/ST | JAX | 9.4 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | PIT D/ST | PIT | 8.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | LAC D/ST | LAC | 8.6 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | LAR D/ST | LAR | 8.5 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | LV D/ST | LV | 8.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | TEN D/ST | TEN | 8.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | SEA D/ST | SEA | 8.1 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | PHI D/ST | PHI | 8.1 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | BAL D/ST | BAL | 7.9 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | DET D/ST | DET | 7.8 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

### K

Selected model: **FIE_KICKER_DEDICATED**  
Research challenger: **—**  
Status: **PRODUCTION_EXISTING**  
Exact scoring: **True**  
Reason: existing_dedicated_specialist_engine  
League replacement: **—**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cameron Dicker | LAC | 7.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 2 | Harrison Mevis | LAR | 7.7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 3 | Jake Bates | DET | 7.5 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 4 | Tyler Loop | BAL | 7.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 5 | Brandon Aubrey | DAL | 7.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 6 | Jason Myers | SEA | 7.3 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 7 | Evan McPherson | CIN | 7.2 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 8 | Ka'imi Fairbairn | HOU | 7.1 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 9 | Will Reichard | MIN | 7 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |
| 10 | Cam Little | JAX | 6.9 | — | — | — | — | — | — | CURRENT_SPECIALIST | Weekly specialist |

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 17 | Courtland Sutton | DEN | 202 | 171.1 | 233.2 | 31.1 | 80.6 | 35 | 18 | STRONG_VALUE | M9 production |
| 19 | Michael Wilson | ARI | 193.6 | 162.6 | 224.5 | 22.7 | 85.9 | 36 | 17 | VALUE | M9 production |
| 12 | Mike Evans | SF | 222.2 | 191.2 | 254 | 51.3 | 62.4 | 27 | 15 | VALUE | M9 diagnostic |
| 2 | Matthew Stafford | LAR | 280.2 | 240.4 | 320.4 | 64.8 | 95.3 | 11 | 9 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 38.3 | 44.3 | 20 | 9 | VALUE | M9 diagnostic |
| 11 | Zay Flowers | BAL | 226.5 | 194.6 | 258.2 | 55.6 | 41.8 | 19 | 8 | VALUE | M9 production |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 36.7 | 48.4 | 21 | 8 | VALUE | M9 diagnostic |
| 25 | DK Metcalf | PIT | 183.4 | 153.2 | 214.8 | 12.5 | 75.9 | 33 | 8 | VALUE | M9 production |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 59 | Bhayshul Tuten | JAX | 63.9 | 34 | 93.9 | -105.5 | 61.6 | 25 | -34 | STRONG_FADE | M9 diagnostic |
| 71 | Jordyn Tyson | NO | 111 | 83.2 | 139.3 | -59.9 | 98 | 39 | -32 | STRONG_FADE | M9 diagnostic |
| 54 | Luther Burden | CHI | 139.3 | 110.2 | 169.2 | -31.6 | 53.7 | 23 | -31 | STRONG_FADE | M9 production |
| 38 | Ladd McConkey | LAC | 167.3 | 137.2 | 197.3 | -3.6 | 37.7 | 16 | -22 | STRONG_FADE | M9 production |
| 49 | Chuba Hubbard | CAR | 99.8 | 71.3 | 129.3 | -69.6 | 78.1 | 28 | -21 | STRONG_FADE | M9 diagnostic |
| 24 | Joe Burrow | CIN | 181.4 | 141.4 | 222.6 | -34 | 51.4 | 4 | -20 | STRONG_FADE | M9 diagnostic |
| 18 | Colston Loveland | CHI | 145.7 | 121.4 | 170.5 | -19.1 | 40.5 | 3 | -15 | OVERPRICED | M9 production |
| 52 | Chris Godwin | TB | 141.1 | 112.2 | 170.7 | -29.8 | 93.1 | 38 | -14 | OVERPRICED | M9 production |
| 46 | Brian Thomas | JAX | 153.7 | 124.5 | 184.1 | -17.2 | 74.6 | 32 | -14 | OVERPRICED | M9 production |
| 20 | Caleb Williams | CHI | 184.4 | 144.4 | 224 | -31 | 71 | 7 | -13 | OVERPRICED | M9 diagnostic |
| 22 | Dalton Kincaid | BUF | 129.4 | 105.8 | 153.5 | -35.4 | 87.7 | 10 | -12 | OVERPRICED | M9 production |
| 30 | Emeka Egbuka | TB | 178.7 | 148.7 | 209.3 | 7.8 | 39 | 18 | -12 | OVERPRICED | M9 production |
| 26 | DeVonta Smith | PHI | 180.7 | 151 | 211.2 | 9.8 | 32.1 | 14 | -12 | OVERPRICED | M9 production |
| 18 | Justin Jefferson | MIN | 196.7 | 166.1 | 228.1 | 25.8 | 11.3 | 6 | -12 | OVERPRICED | M9 production |
| 13 | Lamar Jackson | BAL | 212.4 | 171.9 | 252.7 | -3 | 31.2 | 2 | -11 | OVERPRICED | M9 diagnostic |
| 19 | Jaxson Dart | NYG | 186.8 | 146.7 | 227.3 | -28.6 | 94.5 | 10 | -9 | OVERPRICED | M9 diagnostic |
| 34 | Terry McLaurin | WAS | 172.4 | 142 | 203.1 | 1.5 | 56.2 | 25 | -9 | OVERPRICED | M9 production |
| 15 | Saquon Barkley | PHI | 199.8 | 168.2 | 231.2 | 30.4 | 12.6 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 39 | Parker Washington | JAX | 167.2 | 136.6 | 197.3 | -3.7 | 73.8 | 31 | -8 | OVERPRICED | M9 production |
| 24 | Breece Hall | NYJ | 169.4 | 138 | 200.8 | 0 | 34.1 | 16 | -8 | OVERPRICED | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 27.4 | 15.3 | 9 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 208.4 | Malik Willis | MIA | 5 | 25 | 20 | 261.1 | 45.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 161.6 | Kyler Murray | MIN | 3 | 19 | 16 | 273.1 | 57.6 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |
| 187.3 | Tyler Shough | NO | 12 | 22 | 10 | 215.4 | 0 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 123.3 | Brock Purdy | SF | 6 | 15 | 9 | 257.2 | 41.7 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 114.8 | Quentin Johnston | LAC | 28 | 46 | 18 | 179.3 | 8.4 | 93 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 122.8 | Jakobi Meyers | JAX | 32 | 49 | 17 | 176.2 | 5.3 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 188.8 | Dalton Schultz | HOU | 9 | 23 | 14 | 172.7 | 7.8 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |
| 182 | Juwan Johnson | NO | 11 | 22 | 11 | 165.1 | 0.3 | 94 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value, ADP has improved over the last 7 days |

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
| Jaxon Smith-Njigba | WR | SEA | 24.3 | 0.88 | 0.44 | CLEAR_STARTER |
| Keenan Allen | WR | IND | 20.4 | 1.7 | 0.55 | COMMITTEE_FRINGE |
| Jakobi Meyers | WR | JAX | 19.9 | 1.84 | 0.35 | COMMITTEE_FRINGE |
| Jauan Jennings | WR | MIN | 19.3 | 1.63 | 0.56 | COMMITTEE_FRINGE |
| Mack Hollins | WR | NE | 17.6 | 1.73 | 0.62 | DEPTH |
| Deebo Samuel | WR | SF | 16.4 | 1.54 | 0.51 | STARTER |
| Marquise Brown | WR | PHI | 16.3 | 1.39 | 0.54 | DEPTH |
| Trey McBride | TE | ARI | 16.3 | 2.37 | 0.25 | CLEAR_STARTER |
| Quentin Johnston | WR | LAC | 16 | 1.77 | 0.5 | STARTER |

### Largest negative M9.1c adjustments

| Player | Pos | Team | M9.1c Δ vs Sleeper | Signal z | Reliability | Cohort |
|---|---|---|---:|---:|---:|---|
| Nick Westbrook-Ikhine | WR | IND | -16.7 | -2.62 | 0.47 | COMMITTEE_FRINGE |
| Jack Bech | WR | LV | -16.1 | -1.18 | 0.57 | DEPTH |
| Blake Corum | RB | LAR | -14 | -0.7 | 0.57 | STARTER |
| Jahan Dotson | WR | ATL | -12.3 | -4.91 | 0.51 | STARTER |
| Kenneth Walker | RB | KC | -12.3 | -3.7 | 0.53 | CLEAR_STARTER |
| Malik Willis | QB | MIA | -12 | -2.79 | 0.53 | CLEAR_STARTER |
| Derrick Henry | RB | BAL | -11.8 | -0.9 | 0.6 | CLEAR_STARTER |
| Saquon Barkley | RB | PHI | -11.8 | -1 | 0.6 | CLEAR_STARTER |
| Marquez Valdes-Scantling | WR | DAL | -11.6 | -0.59 | 0.48 | COMMITTEE_FRINGE |
| Gunnar Helm | TE | TEN | -11 | -1.58 | 0.54 | CLEAR_STARTER |
