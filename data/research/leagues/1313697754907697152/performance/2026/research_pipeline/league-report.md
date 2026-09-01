# FIE League Research Report — ReDraft – Pro 🎯 XVI Football 

Season: **2026**  
League ID: `1313697754907697152`  
Format: **REDRAFT**  
Teams: **16**  
Roster: `QB, RB, RB, WR, WR, TE, FLEX, FLEX, DEF, BN, BN, BN, BN, BN, BN`  
ADP market: `adp_ppr`  
Pipeline: **complete_research_only**

## Model overview

| Position | Selected Model | Research Challenger | Validation Status | Exact Scoring | Key Reason |
|---|---|---|---|---|---|
| DST | FIE_DST_DEDICATED | — | PRODUCTION_EXISTING | True | existing_dedicated_specialist_engine |
| K | — | — | NOT_APPLICABLE | None | position_not_rosterable |
| QB | M9 | V9.7.5 | BLOCKED_STATISTICS | False | one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared |
| RB | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| TE | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |
| WR | M9 | V9.7.2 | BLOCKED_STATISTICS | True | one_or_more_head_to_head_or_noninferiority_gates_not_cleared |

## League/scoring overview

PPR: **PPR** (1 per reception)  
Pass TD: **4** · Pass INT: **-1**  
Fumble: **0** · Fumble lost: **-2**  
Superflex/2QB: **No** · D/ST: **Yes** · K: **No**

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
League replacement: **209.7**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Josh Allen | BUF | 299.9 | 258.9 | 340.7 | 90.2 | 21 | 1 | 0 | FAIR | M9 diagnostic |
| 2 | Kyler Murray | MIN | 283.1 | 244.3 | 323 | 73.3 | 161.6 | 19 | 17 | VALUE | M9 diagnostic |
| 3 | Matthew Stafford | LAR | 280.2 | 240.6 | 320.2 | 70.5 | 95.3 | 11 | 8 | VALUE | M9 diagnostic |
| 4 | Malik Willis | MIA | 270.1 | 230.8 | 310.8 | 60.4 | 208.4 | 25 | 21 | STRONG_VALUE | M9 diagnostic |
| 5 | Drake Maye | NE | 268.8 | 229.1 | 309.7 | 59.1 | 47.1 | 3 | -2 | FAIR | M9 diagnostic |
| 6 | Brock Purdy | SF | 267.6 | 227.3 | 308 | 57.9 | 123.3 | 15 | 9 | VALUE | M9 diagnostic |
| 7 | Patrick Mahomes | KC | 259.6 | 219.9 | 299.8 | 49.9 | 110 | 13 | 6 | FAIR | M9 diagnostic |
| 8 | Jalen Hurts | PHI | 241.6 | 201.6 | 281.6 | 31.8 | 60 | 5 | -3 | FAIR | M9 diagnostic |
| 9 | Dak Prescott | DAL | 239.8 | 199.6 | 280.5 | 30.1 | 77.5 | 8 | -1 | FAIR | M9 diagnostic |
| 10 | Trevor Lawrence | JAX | 233.6 | 193 | 274.8 | 23.9 | 100.7 | 12 | 2 | FAIR | M9 diagnostic |

### RB

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **135**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Christian McCaffrey | SF | 308 | 276.2 | 339.9 | 173 | 5.4 | 3 | 2 | FAIR | M9 diagnostic |
| 2 | Bijan Robinson | ATL | 286.2 | 253.9 | 318.9 | 151.3 | 2.2 | 2 | 0 | FAIR | M9 diagnostic |
| 3 | Jahmyr Gibbs | DET | 268 | 235.9 | 300.6 | 133 | 1.9 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Jonathan Taylor | IND | 264.8 | 233.3 | 295.8 | 129.9 | 7.2 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | De'Von Achane | MIA | 264.6 | 232.5 | 296.3 | 129.6 | 13.1 | 7 | 2 | FAIR | M9 diagnostic |
| 6 | Kenneth Walker | KC | 244 | 212.3 | 275.9 | 109 | 19.9 | 11 | 5 | FAIR | M9 diagnostic |
| 7 | James Cook | BUF | 237.4 | 205.8 | 269.4 | 102.4 | 8.6 | 5 | -2 | FAIR | M9 diagnostic |
| 8 | Chase Brown | CIN | 228.6 | 197.1 | 259.9 | 93.6 | 16.7 | 10 | 2 | FAIR | M9 diagnostic |
| 9 | Jeremiyah Love | ARI | 211.8 | 181.2 | 242.8 | 76.8 | 26 | 13 | 4 | FAIR | M9 diagnostic |
| 10 | Kyren Williams | LAR | 208 | 177.5 | 238.9 | 73 | 28.5 | 14 | 4 | FAIR | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 72.7 | 44.3 | 20 | 9 | VALUE | M9 diagnostic |
| 12 | Ashton Jeanty | LV | 206.4 | 174.9 | 237.5 | 71.4 | 14.2 | 8 | -4 | FAIR | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 71.1 | 48.4 | 21 | 8 | VALUE | M9 diagnostic |
| 14 | Derrick Henry | BAL | 202 | 170.7 | 233.7 | 67.1 | 20 | 12 | -2 | FAIR | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.9 | 168.2 | 231.2 | 64.9 | 12.6 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 16 | Cam Skattebo | NYG | 199.6 | 168.8 | 231 | 64.6 | 42 | 18 | 2 | FAIR | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 61.9 | 15.3 | 9 | -8 | OVERPRICED | M9 diagnostic |
| 18 | Josh Jacobs | GB | 191.4 | 165.8 | 218.5 | 56.5 | 35.9 | 17 | -1 | FAIR | M9 diagnostic |
| 19 | Javonte Williams | DAL | 183.4 | 152.8 | 214.9 | 48.4 | 33.5 | 15 | -4 | FAIR | M9 diagnostic |
| 20 | D'Andre Swift | CHI | 180.6 | 150 | 212 | 45.6 | 52.6 | 22 | 2 | FAIR | M9 diagnostic |

### WR

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **132.5**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puka Nacua | LAR | 312.5 | 280.3 | 344.9 | 180 | 4.4 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | Jaxon Smith-Njigba | SEA | 295.4 | 263.5 | 327.8 | 162.9 | 6.2 | 3 | 1 | FAIR | M9 diagnostic |
| 3 | Ja'Marr Chase | CIN | 271.9 | 239.7 | 304 | 139.4 | 3.2 | 1 | -2 | FAIR | M9 diagnostic |
| 4 | Amon-Ra St. Brown | DET | 264.1 | 232.1 | 295.8 | 131.5 | 8.8 | 4 | 0 | FAIR | M9 diagnostic |
| 5 | Rashee Rice | KC | 250.6 | 219 | 282 | 118.1 | 29 | 12 | 7 | FAIR | M9 diagnostic |
| 6 | A.J. Brown | NE | 247.2 | 216 | 278.6 | 114.7 | 17.1 | 7 | 1 | FAIR | M9 diagnostic |
| 7 | Drake London | ATL | 228.2 | 196.6 | 260.2 | 95.7 | 17.7 | 8 | 1 | FAIR | M9 diagnostic |
| 8 | Chris Olave | NO | 225.7 | 194.7 | 257.2 | 93.2 | 30.1 | 13 | 5 | FAIR | M9 diagnostic |
| 9 | George Pickens | DAL | 224.5 | 193.2 | 256.6 | 92 | 22.1 | 9 | 0 | FAIR | M9 diagnostic |
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 89.7 | 62.4 | 27 | 17 | VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 88.5 | 44.7 | 20 | 9 | VALUE | M9 diagnostic |
| 12 | CeeDee Lamb | DAL | 218.8 | 187.1 | 250.4 | 86.3 | 10.4 | 5 | -7 | FAIR | M9 diagnostic |
| 13 | Zay Flowers | BAL | 212.5 | 180.6 | 244.2 | 80 | 41.8 | 19 | 6 | FAIR | M9 diagnostic |
| 14 | Nico Collins | HOU | 205.8 | 173.7 | 238 | 73.3 | 25.1 | 10 | -4 | FAIR | M9 diagnostic |
| 15 | Garrett Wilson | NYJ | 201.7 | 170.4 | 233 | 69.1 | 46.4 | 21 | 6 | FAIR | M9 diagnostic |
| 16 | Malik Nabers | NYG | 201.6 | 170.5 | 233 | 69.1 | 26.9 | 11 | -5 | FAIR | M9 diagnostic |
| 17 | Davante Adams | LAR | 192.5 | 162.3 | 223.5 | 60 | 50.1 | 22 | 5 | FAIR | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 188 | 157.7 | 218.7 | 55.5 | 80.6 | 35 | 17 | VALUE | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.8 | 151.2 | 214.8 | 50.2 | 11.3 | 6 | -13 | OVERPRICED | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.4 | 209.9 | 47.1 | 85.9 | 36 | 16 | VALUE | M9 diagnostic |

### TE

Selected model: **M9**  
Research challenger: **V9.7.2**  
Status: **BLOCKED_STATISTICS**  
Exact scoring: **True**  
Reason: one_or_more_head_to_head_or_noninferiority_gates_not_cleared  
League replacement: **140.2**

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trey McBride | ARI | 282.5 | 253.3 | 312.4 | 142.3 | 24.3 | 2 | 1 | FAIR | M9 diagnostic |
| 2 | George Kittle | SF | 232 | 203.5 | 260.3 | 91.8 | 83.2 | 9 | 7 | FAIR | M9 diagnostic |
| 3 | Kyle Pitts | ATL | 225.1 | 196.6 | 253.8 | 84.9 | 68.6 | 7 | 4 | FAIR | M9 diagnostic |
| 4 | Brock Bowers | LV | 218.3 | 187.9 | 248.7 | 78.1 | 23.2 | 1 | -3 | FAIR | M9 diagnostic |
| 5 | Harold Fannin | CLE | 208.1 | 179.1 | 237.1 | 67.9 | 70.6 | 8 | 3 | FAIR | M9 diagnostic |
| 6 | Tucker Kraft | GB | 200.7 | 172 | 229.5 | 60.5 | 62.8 | 6 | 0 | FAIR | M9 diagnostic |
| 7 | Tyler Warren | IND | 197 | 168.2 | 225.8 | 56.8 | 49.7 | 4 | -3 | FAIR | M9 diagnostic |
| 8 | Isaiah Likely | NYG | 188.3 | 160.2 | 216.8 | 48.1 | 107.6 | 13 | 5 | FAIR | M9 diagnostic |
| 9 | Sam LaPorta | DET | 188.2 | 159.6 | 217.1 | 48 | 58.8 | 5 | -4 | FAIR | M9 diagnostic |
| 10 | Dalton Schultz | HOU | 185.1 | 157.1 | 213.3 | 44.9 | 188.8 | 23 | 13 | VALUE | M9 diagnostic |

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

## Top-100 ADP positive outliers

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Mike Evans | SF | 222.2 | 191.2 | 254 | 89.7 | 62.4 | 27 | 17 | VALUE | M9 diagnostic |
| 18 | Courtland Sutton | DEN | 188 | 157.7 | 218.7 | 55.5 | 80.6 | 35 | 17 | VALUE | M9 diagnostic |
| 20 | Michael Wilson | ARI | 179.6 | 149.4 | 209.9 | 47.1 | 85.9 | 36 | 16 | VALUE | M9 diagnostic |
| 11 | Jaylen Waddle | DEN | 221 | 190.4 | 251.8 | 88.5 | 44.7 | 20 | 9 | VALUE | M9 diagnostic |
| 11 | Travis Etienne | NO | 207.7 | 176.9 | 238.6 | 72.7 | 44.3 | 20 | 9 | VALUE | M9 diagnostic |
| 13 | David Montgomery | HOU | 206.1 | 175.5 | 237.5 | 71.1 | 48.4 | 21 | 8 | VALUE | M9 diagnostic |
| 3 | Matthew Stafford | LAR | 280.2 | 240.6 | 320.2 | 70.5 | 95.3 | 11 | 8 | VALUE | M9 diagnostic |

## Top-100 ADP negative outliers / fades

| Rank | Player | Team | Projection | P10 | P90 | VORP | ADP | Market Pos Rank | Rank Edge | Value | Projection Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 59 | Bhayshul Tuten | JAX | 63.9 | 34 | 93.9 | -71.1 | 61.6 | 25 | -34 | STRONG_FADE | M9 diagnostic |
| 57 | Luther Burden | CHI | 125.3 | 93.9 | 156.8 | -7.2 | 53.7 | 23 | -34 | STRONG_FADE | M9 diagnostic |
| 42 | Ladd McConkey | LAC | 153.3 | 122 | 184.4 | 20.8 | 37.7 | 16 | -26 | STRONG_FADE | M9 diagnostic |
| 62 | Jordyn Tyson | NO | 111 | 83.2 | 139.3 | -21.5 | 98 | 39 | -23 | STRONG_FADE | M9 diagnostic |
| 49 | Chuba Hubbard | CAR | 99.8 | 71.3 | 129.3 | -35.2 | 78.1 | 28 | -21 | STRONG_FADE | M9 diagnostic |
| 21 | Joe Burrow | CIN | 188.1 | 148 | 229 | -21.6 | 51.4 | 4 | -17 | OVERPRICED | M9 diagnostic |
| 31 | DeVonta Smith | PHI | 166.7 | 136.2 | 197.9 | 34.2 | 32.1 | 14 | -17 | OVERPRICED | M9 diagnostic |
| 23 | Caleb Williams | CHI | 186.7 | 146.7 | 226.3 | -23 | 71 | 7 | -16 | OVERPRICED | M9 diagnostic |
| 26 | Dalton Kincaid | BUF | 129.6 | 101.3 | 158.1 | -10.6 | 87.7 | 10 | -16 | OVERPRICED | M9 diagnostic |
| 54 | Chris Godwin | TB | 127.1 | 97.2 | 157.5 | -5.4 | 93.1 | 38 | -16 | OVERPRICED | M9 diagnostic |
| 34 | Emeka Egbuka | TB | 164.7 | 133.9 | 196.3 | 32.2 | 39 | 18 | -16 | OVERPRICED | M9 diagnostic |
| 18 | Colston Loveland | CHI | 152.2 | 123.1 | 181.6 | 12 | 40.5 | 3 | -15 | OVERPRICED | M9 diagnostic |
| 46 | Brian Thomas | JAX | 139.8 | 109.1 | 170.8 | 7.2 | 74.6 | 32 | -14 | OVERPRICED | M9 diagnostic |
| 38 | Terry McLaurin | WAS | 158.4 | 127.2 | 189.9 | 25.9 | 56.2 | 25 | -13 | OVERPRICED | M9 diagnostic |
| 19 | Justin Jefferson | MIN | 182.8 | 151.2 | 214.8 | 50.2 | 11.3 | 6 | -13 | OVERPRICED | M9 diagnostic |
| 22 | Jaxson Dart | NYG | 187.9 | 147.7 | 228.3 | -21.8 | 94.5 | 10 | -12 | OVERPRICED | M9 diagnostic |
| 43 | Parker Washington | JAX | 153.2 | 121.7 | 184 | 20.7 | 73.8 | 31 | -12 | OVERPRICED | M9 diagnostic |
| 13 | Lamar Jackson | BAL | 218.4 | 178 | 258.5 | 8.6 | 31.2 | 2 | -11 | OVERPRICED | M9 diagnostic |
| 44 | Marvin Harrison | ARI | 151.6 | 121.6 | 182.6 | 19.1 | 76.6 | 34 | -10 | OVERPRICED | M9 diagnostic |
| 26 | Tetairoa McMillan | CAR | 171.8 | 141.1 | 202.9 | 39.3 | 38.3 | 17 | -9 | OVERPRICED | M9 diagnostic |
| 24 | Tee Higgins | CIN | 175.4 | 144.5 | 206.4 | 42.9 | 35.2 | 15 | -9 | OVERPRICED | M9 diagnostic |
| 15 | Saquon Barkley | PHI | 199.9 | 168.2 | 231.2 | 64.9 | 12.6 | 6 | -9 | OVERPRICED | M9 diagnostic |
| 24 | Breece Hall | NYJ | 169.4 | 138 | 200.8 | 34.4 | 34.1 | 16 | -8 | OVERPRICED | M9 diagnostic |
| 17 | Omarion Hampton | LAC | 196.8 | 165.8 | 228 | 61.9 | 15.3 | 9 | -8 | OVERPRICED | M9 diagnostic |

## Positive sleepers with ADP >100

### QB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 208.4 | Malik Willis | MIA | 4 | 25 | 21 | 270.1 | 60.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 161.6 | Kyler Murray | MIN | 2 | 19 | 17 | 283.1 | 73.3 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 187.3 | Tyler Shough | NO | 12 | 22 | 10 | 222.4 | 12.7 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 123.3 | Brock Purdy | SF | 6 | 15 | 9 | 267.6 | 57.9 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### RB

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 231.6 | James Conner | ARI | 39 | 67 | 28 | 135 | 0 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 173 | Tyrone Tracy | NYG | 35 | 51 | 16 | 147.6 | 12.6 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 157.8 | MarShawn Lloyd | GB | 34 | 45 | 11 | 149 | 14 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 166.3 | Alvin Kamara | NO | 37 | 48 | 11 | 139.9 | 5 | 64 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### WR

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 241.8 | Troy Franklin | DEN | 48 | 96 | 48 | 132.9 | 0.4 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 119 | Wan'Dale Robinson | TEN | 28 | 47 | 19 | 170.7 | 38.2 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 132.9 | Romeo Doubs | NE | 36 | 52 | 16 | 161.2 | 28.7 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 105.9 | Michael Pittman | PIT | 27 | 42 | 15 | 170.9 | 38.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 122.8 | Jakobi Meyers | JAX | 35 | 49 | 14 | 162.2 | 29.7 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 114.8 | Quentin Johnston | LAC | 33 | 46 | 13 | 165.3 | 32.8 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 172.4 | Denzel Boston | CLE | 47 | 59 | 12 | 134.7 | 2.2 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 130.1 | Deebo Samuel | SF | 41 | 51 | 10 | 155.7 | 23.2 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 143.4 | Khalil Shakir | BUF | 45 | 55 | 10 | 148.3 | 15.8 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 121.8 | KC Concepcion | CLE | 40 | 48 | 8 | 156.4 | 23.9 | 62 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

### TE

| ADP | Player | Team | FIE Rank | Market Pos Rank | Edge | Projection | VORP | Confidence | Why |
|---|---|---|---|---|---|---|---|---|---|
| 188.8 | Dalton Schultz | HOU | 10 | 23 | 13 | 185.1 | 44.9 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 232.2 | Theo Johnson | NYG | 17 | 29 | 12 | 153.7 | 13.5 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 192.2 | Chig Okonkwo | WAS | 13 | 24 | 11 | 174.6 | 34.4 | 55 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 182 | Juwan Johnson | NO | 12 | 22 | 10 | 175.3 | 35.1 | 66 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |
| 233.1 | Cade Otton | TB | 21 | 30 | 9 | 140.2 | 0 | 65 | Positive value over this league's replacement level, FIE positional rank is materially ahead of market, M9 remains the selected governed model, Matched to the current Sleeper player/team, League FLEX demand is included in replacement value |

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
