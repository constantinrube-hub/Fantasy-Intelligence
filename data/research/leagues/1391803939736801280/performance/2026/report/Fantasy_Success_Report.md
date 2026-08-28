# FIE Fantasy Success, M7-M9 Season Report

## Executive summary

This report separates **Sleeper market consensus**, a **market-anchored FIE diagnostic view**, and a **production-eligible independent FIE projection**. Diagnostic disagreement is not evidence that Sleeper is wrong. The diagnostic view uses FIE's own league-scored player allocation signal and anchors it to Sleeper's **total** position-level market projection, so its average projection matches the market average without depending on completeness of Sleeper's raw-stat component feed.

- Production-validated preseason positions: WR, TE
- Diagnostic-only preseason positions: QB, RB
- M7 validated weekly driver families: 0
- M8 validated matchup families: 0
- M9 weekly returner candidates: none

## Market agreement by position

| Pos | Evidence | Players | Shadow coverage | Avg Sleeper | Avg FIE diagnostic | Mean Δ | Rank corr. | Median |Δ pts| | P90 |Δ pts| | Within ±5% | >10% |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QB | Diagnostic model | 77 | 51 | 122.2 | 122.2 | -0.00 | 0.778 | 28.9 | 116.1 | 35.1% | 47 |
| RB | Diagnostic model | 134 | 85 | 85.6 | 85.6 | 0.00 | 0.867 | 9.0 | 51.9 | 43.3% | 67 |
| WR | Validated preseason model | 215 | 126 | 85.7 | 85.7 | -0.00 | 0.914 | 9.5 | 53.5 | 45.6% | 105 |
| TE | Validated preseason model | 127 | 77 | 59.8 | 59.8 | 0.00 | 0.926 | 2.8 | 36.3 | 47.2% | 58 |

## Position-level predictive evidence

### QB

**Preseason evidence:** Diagnostic model; mean historical improvement -1.0%; 95% CI -3.3% to +1.6%.

**M7 driver evidence:** recent QB rushing role (opportunity), recent QB rushing role (rushing_leverage), recent opportunity-based expected production (regression), recent QB pass-attempt role (opportunity), recent snap share (opportunity), recent actual-vs-expected production gap (regression)

**M8 matchup evidence:** public_pass_rush_matchup [diagnostic_only], public_defensive_synergy_matchup [diagnostic_only], public_coverage_matchup [diagnostic_only]

### RB

**Preseason evidence:** Diagnostic model; mean historical improvement +3.5%; 95% CI -3.0% to +8.3%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent offensive snap share (opportunity), recent carry share (opportunity), recent target share (receiving_role), recent target share (opportunity), backfield competition (competition)

**M8 matchup evidence:** insufficient

### WR

**Preseason evidence:** Validated preseason model; mean historical improvement +5.7%; 95% CI +3.1% to +10.1%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent target share (opportunity), recent offensive snap share (opportunity), receiving competition (competition), number of receiving competitors (competition), recent red-zone target share (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

### TE

**Preseason evidence:** Validated preseason model; mean historical improvement +6.6%; 95% CI +4.5% to +8.6%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent target share (opportunity), recent offensive snap share (opportunity), receiving competition (competition), number of receiving competitors (competition), recent red-zone target share (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

## Requested Sleeper market universe

### QB Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Josh Allen | 361.5 | 299.6 | -61.9 | -17.1% | 1 | 1 | 0 | — | 259.6 | 299.1 | 341.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-TD production, recent goal-line carry share. |
| Lamar Jackson | 326.0 | 218.1 | -107.9 | -33.1% | 2 | 14 | -12 | — | 177.6 | 218.1 | 259.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior rushing-yard production. |
| Drake Maye | 320.8 | 268.6 | -52.2 | -16.3% | 3 | 5 | -2 | — | 227.5 | 268.2 | 309.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Joe Burrow | 306.1 | 187.8 | -118.3 | -38.6% | 4 | 23 | -19 | — | 147.6 | 187.5 | 228.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Jalen Hurts | 310.5 | 241.3 | -69.2 | -22.3% | 5 | 8 | -3 | — | 200.9 | 240.7 | 282.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, prior rushing-TD production. |
| Jayden Daniels | 308.7 | 225.6 | -83.1 | -26.9% | 6 | 11 | -5 | — | 185.3 | 225.2 | 266.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, recent QB rushing role, prior-season fantasy production. |
| Caleb Williams | 299.3 | 186.5 | -112.8 | -37.7% | 7 | 25 | -18 | — | 147.2 | 186.1 | 226.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Dak Prescott | 303.9 | 239.6 | -64.3 | -21.2% | 8 | 9 | -1 | — | 199.8 | 238.9 | 280.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, recent goal-line carry share. |
| Justin Herbert | 295.5 | 209.5 | -86.0 | -29.1% | 9 | 16 | -7 | — | 168.7 | 208.8 | 250.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Jaxson Dart | 296.5 | 187.7 | -108.9 | -36.7% | 10 | 24 | -14 | — | 148.3 | 187.4 | 227.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Matthew Stafford | 280.2 | 280.2 | 0.0 | +0.0% | 11 | 3 | 8 | — | 240.1 | 279.6 | 321.8 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Trevor Lawrence | 303.4 | 233.4 | -70.0 | -23.1% | 12 | 10 | 2 | — | 193.2 | 233.0 | 273.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Patrick Mahomes | 286.7 | 259.3 | -27.3 | -9.5% | 13 | 7 | 6 | — | 219.3 | 258.6 | 300.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Bo Nix | 295.7 | 206.9 | -88.8 | -30.0% | 14 | 18 | -4 | — | 166.4 | 206.6 | 247.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, recent opportunity-based expected production. |
| Brock Purdy | 303.2 | 267.4 | -35.8 | -11.8% | 15 | 6 | 9 | — | 226.9 | 266.8 | 308.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent actual-vs-expected production gap, prior-season fantasy production, prior passing-TD production. |
| Jared Goff | 283.5 | 186.1 | -97.4 | -34.4% | 16 | 26 | -10 | — | 146.4 | 185.4 | 225.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, prior passing-yard production. |
| Baker Mayfield | 274.9 | 196.9 | -78.0 | -28.4% | 17 | 20 | -3 | — | 157.6 | 196.5 | 236.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent role-change signal. |
| Jordan Love | 278.5 | 175.0 | -103.5 | -37.2% | 18 | 27 | -9 | — | 135.4 | 174.6 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, pfr times sacked. |
| Kyler Murray | 283.1 | 283.1 | 0.0 | +0.0% | 19 | 2 | 17 | — | 243.7 | 282.2 | 323.7 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Sam Darnold | 262.7 | 163.8 | -99.0 | -37.7% | 20 | 30 | -10 | — | 123.8 | 163.3 | 204.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior passing-yard production, prior-season fantasy production. |
| Fernando Mendoza | 212.2 | 212.2 | 0.0 | +0.0% | 21 | 15 | 6 | — | 174.9 | 211.3 | 250.9 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Tyler Shough | 270.9 | 222.2 | -48.8 | -18.0% | 22 | 13 | 9 | — | 182.5 | 221.7 | 262.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, pfr times sacked, recent actual-vs-expected production gap. |
| Malik Willis | 270.1 | 270.1 | 0.0 | +0.0% | 23 | 4 | 19 | — | 229.7 | 269.7 | 310.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| C.J. Stroud | 247.8 | 152.4 | -95.5 | -38.5% | 24 | 34 | -10 | — | 113.5 | 151.6 | 192.1 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |

### RB Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jahmyr Gibbs | 331.4 | 268.5 | -62.9 | -19.0% | 1 | 3 | -2 | — | 236.3 | 268.7 | 299.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Bijan Robinson | 324.9 | 286.8 | -38.1 | -11.7% | 2 | 2 | 0 | — | 255.2 | 286.7 | 318.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior rushing-yard production. |
| Christian McCaffrey | 291.0 | 308.6 | 17.6 | +6.0% | 3 | 1 | 2 | — | 277.0 | 308.2 | 340.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, recent opportunity-based expected production. |
| Jonathan Taylor | 272.3 | 265.4 | -6.9 | -2.5% | 4 | 4 | 0 | — | 233.9 | 265.4 | 297.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| James Cook | 260.8 | 238.0 | -22.8 | -8.8% | 5 | 7 | -2 | — | 206.6 | 237.7 | 269.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| De'Von Achane | 257.4 | 265.2 | 7.8 | +3.0% | 6 | 5 | 1 | — | 233.3 | 265.3 | 296.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Saquon Barkley | 246.7 | 200.4 | -46.3 | -18.8% | 7 | 15 | -8 | — | 169.9 | 200.1 | 231.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Ashton Jeanty | 233.9 | 207.0 | -26.9 | -11.5% | 8 | 12 | -4 | — | 176.3 | 206.4 | 238.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Omarion Hampton | 242.9 | 197.4 | -45.5 | -18.7% | 9 | 17 | -8 | — | 166.2 | 197.3 | 228.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Chase Brown | 255.2 | 229.2 | -26.0 | -10.2% | 10 | 8 | 2 | — | 198.4 | 228.7 | 260.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Kenneth Walker III | 244.0 | 244.0 | 0.0 | +0.0% | 11 | 6 | 5 | — | 212.4 | 243.7 | 275.4 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Derrick Henry | 246.9 | 202.6 | -44.3 | -17.9% | 12 | 14 | -2 | — | 171.6 | 202.5 | 233.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Jeremiyah Love | 211.8 | 211.8 | 0.0 | +0.0% | 13 | 9 | 4 | — | 180.9 | 211.4 | 243.4 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Kyren Williams | 208.0 | 208.0 | 0.0 | +0.0% | 14 | 10 | 4 | — | 177.6 | 207.5 | 239.0 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Josh Jacobs | 202.6 | 192.0 | -10.6 | -5.2% | 15 | 18 | -3 | — | 161.4 | 191.3 | 223.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Breece Hall | 211.0 | 170.0 | -41.0 | -19.4% | 16 | 24 | -8 | — | 139.4 | 169.8 | 200.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Javonte Williams | 207.3 | 184.0 | -23.3 | -11.2% | 17 | 19 | -2 | — | 153.6 | 183.6 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bucky Irving | 197.3 | 179.4 | -17.9 | -9.1% | 18 | 21 | -3 | — | 148.9 | 179.0 | 210.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Cam Skattebo | 201.2 | 200.2 | -1.0 | -0.5% | 19 | 16 | 3 | — | 170.1 | 199.7 | 231.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Travis Etienne | 207.7 | 207.7 | 0.0 | +0.0% | 20 | 11 | 9 | — | 176.9 | 207.2 | 238.7 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| David Montgomery | 206.1 | 206.1 | 0.0 | +0.0% | 21 | 13 | 8 | — | 175.2 | 205.8 | 237.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Quinshon Judkins | 196.0 | 168.6 | -27.4 | -14.0% | 22 | 25 | -3 | — | 138.4 | 168.3 | 199.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| TreVeyon Henderson | 171.0 | 157.3 | -13.7 | -8.0% | 23 | 28 | -5 | — | 127.3 | 156.8 | 188.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| D'Andre Swift | 208.0 | 181.1 | -26.9 | -12.9% | 24 | 20 | 4 | — | 149.8 | 180.4 | 212.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bhayshul Tuten | 174.8 | 64.4 | -110.4 | -63.1% | 25 | 66 | -41 | — | 34.5 | 63.9 | 95.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Jadarian Price | 170.0 | 170.0 | 0.0 | +0.0% | 26 | 23 | 3 | — | 140.8 | 169.3 | 200.6 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jaylen Warren | 170.6 | 178.3 | 7.7 | +4.5% | 27 | 22 | 5 | — | 148.2 | 178.0 | 208.2 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Chuba Hubbard | 147.9 | 100.4 | -47.5 | -32.1% | 28 | 51 | -23 | — | 71.0 | 99.4 | 130.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| RJ Harvey | 144.1 | 153.3 | 9.2 | +6.4% | 29 | 31 | -2 | — | 124.4 | 152.6 | 182.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Rhamondre Stevenson | 169.0 | 151.9 | -17.1 | -10.1% | 30 | 33 | -3 | — | 122.1 | 151.3 | 182.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior receiving-yard production. |
| Tony Pollard | 160.1 | 167.6 | 7.5 | +4.7% | 31 | 26 | 5 | — | 138.2 | 167.2 | 197.9 | Diagnostic model | FIE diagnostic is higher; main model signals: recent carry share, prior-season fantasy production, prior rushing-yard production. |
| Rico Dowdle | 161.1 | 161.1 | 0.0 | +0.0% | 32 | 27 | 5 | — | 131.3 | 160.3 | 191.4 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| J.K. Dobbins | 160.2 | 153.5 | -6.7 | -4.2% | 33 | 30 | 3 | — | 123.9 | 153.1 | 183.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior-season fantasy production, recent carry share. |
| Kyle Monangai | 154.6 | 103.7 | -50.9 | -32.9% | 34 | 49 | -15 | — | 74.4 | 102.9 | 134.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Blake Corum | 135.3 | 135.3 | 0.0 | +0.0% | 35 | 38 | -3 | — | 106.6 | 134.8 | 164.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jonathon Brooks | 154.9 | 154.9 | 0.0 | +0.0% | 36 | 29 | 7 | — | 126.5 | 154.3 | 184.1 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |

### WR Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 311.1 | 272.5 | -38.6 | -12.4% | 1 | 3 | -2 | 285.9 | 240.8 | 272.0 | 304.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Puka Nacua | 312.5 | 312.5 | 0.0 | +0.0% | 2 | 1 | 1 | — | 280.0 | 312.5 | 344.7 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jaxon Smith-Njigba | 284.6 | 296.1 | 11.5 | +4.0% | 3 | 2 | 1 | 309.4 | 264.6 | 295.9 | 328.0 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Amon-Ra St. Brown | 280.5 | 264.7 | -15.8 | -5.6% | 4 | 4 | 0 | 278.0 | 232.9 | 264.3 | 297.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| CeeDee Lamb | 270.5 | 219.5 | -51.0 | -18.9% | 5 | 12 | -7 | 232.8 | 188.3 | 218.9 | 251.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Justin Jefferson | 250.4 | 183.4 | -67.0 | -26.8% | 6 | 20 | -14 | 196.7 | 152.9 | 183.0 | 214.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Drake London | 250.2 | 228.8 | -21.4 | -8.5% | 7 | 7 | 0 | 242.2 | 198.0 | 228.2 | 260.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| A.J. Brown | 247.2 | 247.2 | 0.0 | +0.0% | 8 | 6 | 2 | — | 216.4 | 246.7 | 278.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| George Pickens | 245.7 | 225.1 | -20.6 | -8.4% | 9 | 9 | 0 | 238.5 | 194.1 | 224.8 | 256.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Nico Collins | 262.0 | 206.4 | -55.6 | -21.2% | 10 | 14 | -4 | 219.8 | 175.0 | 206.1 | 237.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Malik Nabers | 236.7 | 202.2 | -34.5 | -14.6% | 11 | 16 | -5 | 215.6 | 171.6 | 201.8 | 233.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Rashee Rice | 229.3 | 251.2 | 21.9 | +9.6% | 12 | 5 | 7 | 264.6 | 218.9 | 251.2 | 282.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chris Olave | 235.9 | 226.3 | -9.6 | -4.1% | 13 | 8 | 5 | 239.7 | 194.9 | 226.2 | 258.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | 224.4 | 176.0 | -48.4 | -21.6% | 14 | 25 | -11 | 189.3 | 145.6 | 175.7 | 207.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| DeVonta Smith | 229.2 | 167.4 | -61.8 | -27.0% | 15 | 32 | -17 | 180.7 | 137.4 | 166.8 | 198.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | 223.0 | 172.5 | -50.5 | -22.7% | 16 | 27 | -11 | 185.8 | 142.3 | 172.0 | 202.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Ladd McConkey | 228.2 | 154.0 | -74.2 | -32.5% | 17 | 43 | -26 | 167.3 | 124.5 | 153.3 | 184.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | 224.0 | 165.3 | -58.7 | -26.2% | 18 | 35 | -17 | 178.7 | 135.2 | 164.9 | 195.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Zay Flowers | 228.2 | 213.1 | -15.1 | -6.6% | 19 | 13 | 6 | 226.5 | 181.4 | 213.1 | 244.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Garrett Wilson | 224.9 | 202.3 | -22.6 | -10.1% | 20 | 15 | 5 | 215.6 | 171.5 | 201.7 | 233.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Jaylen Waddle | 221.0 | 221.0 | 0.0 | +0.0% | 21 | 11 | 10 | — | 190.0 | 220.8 | 252.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Davante Adams | 192.5 | 192.5 | 0.0 | +0.0% | 22 | 17 | 5 | — | 161.4 | 192.2 | 223.9 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Luther Burden III | 209.0 | 126.0 | -83.0 | -39.7% | 23 | 58 | -35 | 139.3 | 97.5 | 125.1 | 155.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Terry McLaurin | 213.8 | 159.0 | -54.8 | -25.6% | 24 | 39 | -15 | 172.4 | 128.8 | 158.4 | 189.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DJ Moore | 179.0 | 179.0 | 0.0 | +0.0% | 25 | 22 | 3 | — | 149.3 | 178.5 | 209.8 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jameson Williams | 206.2 | 176.0 | -30.2 | -14.6% | 26 | 24 | 2 | 189.4 | 145.3 | 175.4 | 207.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mike Evans | 222.2 | 222.2 | 0.0 | +0.0% | 27 | 10 | 17 | — | 191.0 | 221.7 | 253.4 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rome Odunze | 207.9 | 166.9 | -41.0 | -19.7% | 28 | 33 | -5 | 180.2 | 136.6 | 166.2 | 197.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Carnell Tate | 177.3 | 177.3 | 0.0 | +0.0% | 29 | 23 | 6 | — | 147.3 | 176.9 | 208.4 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Christian Watson | 207.6 | 175.3 | -32.3 | -15.6% | 30 | 26 | 4 | 188.7 | 144.5 | 174.7 | 206.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Brian Thomas Jr. | 195.4 | 140.4 | -55.0 | -28.2% | 31 | 47 | -16 | 153.7 | 111.0 | 140.0 | 170.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DK Metcalf | 183.3 | 170.0 | -13.3 | -7.2% | 32 | 30 | 2 | 183.4 | 139.9 | 169.4 | 201.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Marvin Harrison Jr. | 186.2 | 152.2 | -34.0 | -18.2% | 33 | 45 | -12 | 165.6 | 122.4 | 151.7 | 182.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Parker Washington | 212.4 | 153.9 | -58.5 | -27.6% | 34 | 44 | -10 | 167.2 | 124.2 | 153.3 | 184.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Courtland Sutton | 174.3 | 188.7 | 14.4 | +8.2% | 35 | 18 | 17 | 202.0 | 158.4 | 188.4 | 219.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Michael Wilson | 166.0 | 180.3 | 14.3 | +8.6% | 36 | 21 | 15 | 193.6 | 149.3 | 179.8 | 211.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |

### TE Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Trey McBride | 234.9 | 235.4 | 0.5 | +0.2% | 1 | 1 | 0 | 253.4 | 209.4 | 235.0 | 261.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Brock Bowers | 253.5 | 183.9 | -69.6 | -27.5% | 2 | 4 | -2 | 201.8 | 159.0 | 183.6 | 209.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Colston Loveland | 215.4 | 127.7 | -87.7 | -40.7% | 3 | 20 | -17 | 145.7 | 103.7 | 127.2 | 152.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tyler Warren | 201.1 | 165.8 | -35.3 | -17.6% | 4 | 7 | -3 | 183.8 | 141.0 | 165.5 | 191.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Sam LaPorta | 196.5 | 158.5 | -38.0 | -19.3% | 5 | 8 | -3 | 176.5 | 133.7 | 158.3 | 183.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Tucker Kraft | 174.4 | 171.6 | -2.8 | -1.6% | 6 | 6 | 0 | 189.5 | 146.3 | 171.2 | 197.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Harold Fannin Jr. | 180.4 | 173.3 | -7.1 | -3.9% | 7 | 5 | 2 | 191.3 | 148.1 | 173.1 | 198.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Kyle Pitts | 171.6 | 187.5 | 15.9 | +9.3% | 8 | 3 | 5 | 205.5 | 162.3 | 187.6 | 212.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Dalton Kincaid | 163.6 | 111.4 | -52.2 | -31.9% | 9 | 24 | -15 | 129.4 | 87.7 | 110.9 | 135.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| George Kittle | 169.3 | 194.3 | 25.0 | +14.8% | 10 | 2 | 8 | 212.3 | 169.0 | 194.1 | 219.5 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Travis Kelce | 171.4 | 153.2 | -18.2 | -10.6% | 11 | 11 | 0 | 171.2 | 128.4 | 153.1 | 178.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Jake Ferguson | 159.8 | 139.9 | -19.9 | -12.5% | 12 | 15 | -3 | 157.9 | 115.0 | 139.7 | 165.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior reception volume. |
| Isaiah Likely | 157.3 | 157.3 | 0.0 | +0.0% | 13 | 9 | 4 | — | 132.9 | 156.9 | 181.7 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Dallas Goedert | 136.0 | 146.8 | 10.8 | +7.9% | 14 | 13 | 1 | 164.7 | 121.8 | 146.6 | 171.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, recent role-change signal. |
| Oronde Gadsden II | 141.8 | 128.2 | -13.6 | -9.6% | 15 | 19 | -4 | 146.2 | 103.9 | 128.1 | 152.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Mark Andrews | 162.5 | 106.8 | -55.7 | -34.3% | 16 | 29 | -13 | 124.8 | 83.0 | 106.4 | 131.4 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Hunter Henry | 153.5 | 139.3 | -14.2 | -9.2% | 17 | 16 | 1 | 157.3 | 114.6 | 138.8 | 164.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Brenton Strange | 161.0 | 123.3 | -37.7 | -23.4% | 18 | 21 | -3 | 141.3 | 99.0 | 123.1 | 147.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Kenyon Sadiq | 100.2 | 100.2 | 0.0 | +0.0% | 19 | 33 | -14 | — | 77.7 | 99.6 | 123.4 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| T.J. Hockenson | 155.0 | 110.0 | -45.0 | -29.1% | 20 | 28 | -8 | 127.9 | 86.4 | 109.6 | 134.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| AJ Barner | 142.4 | 110.3 | -32.1 | -22.5% | 21 | 27 | -6 | 128.3 | 86.7 | 110.3 | 134.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Chig Okonkwo | 144.1 | 144.1 | 0.0 | +0.0% | 22 | 14 | 8 | — | 120.4 | 143.9 | 168.4 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Juwan Johnson | 140.9 | 147.1 | 6.2 | +4.4% | 23 | 12 | 11 | 165.1 | 122.3 | 146.8 | 172.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Dalton Schultz | 150.9 | 154.7 | 3.8 | +2.5% | 24 | 10 | 14 | 172.7 | 130.0 | 154.5 | 179.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Largest model-market disagreements

These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 66 | -41 | 174.8 | 64.4 | -110.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 126.0 | -83.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 17 | 43 | -26 | 228.2 | 154.0 | -74.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 51 | -23 | 147.9 | 100.4 | -47.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Joe Burrow | QB | 4 | 23 | -19 | 306.1 | 187.8 | -118.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Caleb Williams | QB | 7 | 25 | -18 | 299.3 | 186.5 | -112.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Courtland Sutton | WR | 35 | 18 | 17 | 174.3 | 188.7 | 14.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.7 | -87.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| DeVonta Smith | WR | 15 | 32 | -17 | 229.2 | 167.4 | -61.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 165.3 | -58.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brian Thomas Jr. | WR | 31 | 47 | -16 | 195.4 | 140.4 | -55.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 111.4 | -52.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Terry McLaurin | WR | 24 | 39 | -15 | 213.8 | 159.0 | -54.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Michael Wilson | WR | 36 | 21 | 15 | 166.0 | 180.3 | 14.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Kyle Monangai | RB | 34 | 49 | -15 | 154.6 | 103.7 | -50.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 183.4 | -67.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jaxson Dart | QB | 10 | 24 | -14 | 296.5 | 187.7 | -108.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Dalton Schultz | TE | 24 | 10 | 14 | 150.9 | 154.7 | 3.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Mark Andrews | TE | 16 | 29 | -13 | 162.5 | 106.8 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Lamar Jackson | QB | 2 | 14 | -12 | 326.0 | 218.1 | -107.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior rushing-yard production. |
| Marvin Harrison Jr. | WR | 33 | 45 | -12 | 186.2 | 152.2 | -34.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tee Higgins | WR | 14 | 25 | -11 | 224.4 | 176.0 | -48.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Juwan Johnson | TE | 23 | 12 | 11 | 140.9 | 147.1 | 6.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Tetairoa McMillan | WR | 16 | 27 | -11 | 223.0 | 172.5 | -50.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Parker Washington | WR | 34 | 44 | -10 | 212.4 | 153.9 | -58.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jared Goff | QB | 16 | 26 | -10 | 283.5 | 186.1 | -97.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, prior passing-yard production. |
| C.J. Stroud | QB | 24 | 34 | -10 | 247.8 | 152.4 | -95.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Sam Darnold | QB | 20 | 30 | -10 | 262.7 | 163.8 | -99.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior passing-yard production, prior-season fantasy production. |
| Brock Purdy | QB | 15 | 6 | 9 | 303.2 | 267.4 | -35.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent actual-vs-expected production gap, prior-season fantasy production, prior passing-TD production. |
| Jordan Love | QB | 18 | 27 | -9 | 278.5 | 175.0 | -103.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, pfr times sacked. |

## Diagnostic sleeper candidates outside market cutoffs

These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jimmy Garoppolo | QB | 181 | 56 | 125 | 12.3 | 28.3 | 16.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-yard production. |
| Nick Mullens | QB | 132 | 59 | 73 | 12.0 | 24.3 | 12.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-yard production. |
| Jacoby Brissett | QB | 34 | 22 | 12 | 160.0 | 188.9 | 28.9 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior passing-TD production, pfr times sacked. |
| Daniel Jones | QB | 25 | 17 | 8 | 223.5 | 208.3 | -15.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, prior rushing-TD production. |
| J.J. McCarthy | QB | 26 | 21 | 5 | 13.6 | 192.9 | 179.3 | Diagnostic model | FIE diagnostic is higher; main model signals: pfr times sacked, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Zavier Scott | RB | 338 | 86 | 252 | 5.6 | 36.7 | 31.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Elijah Mitchell | RB | 336 | 114 | 222 | 9.3 | 5.7 | -3.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Jacardia Wright | RB | 300 | 91 | 209 | 4.3 | 30.5 | 26.2 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, prior receiving-yard production. |
| Kalel Mullings | RB | 329 | 134 | 195 | 5.6 | -19.7 | -25.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Cam Akers | RB | 263 | 124 | 139 | 5.1 | 0.0 | -5.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| James Conner | RB | 69 | 37 | 32 | 57.2 | 135.5 | 78.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Audric Estimé | RB | 70 | 42 | 28 | 22.6 | 123.7 | 101.1 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, prior-season fantasy production, prior reception volume. |
| Kimani Vidal | RB | 71 | 44 | 27 | 60.0 | 115.1 | 55.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior rushing-yard production, recent opportunity-based expected production, prior-season fantasy production. |
| Jaylen Wright | RB | 77 | 58 | 19 | 44.1 | 78.2 | 34.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, number of backfield competitors, recent goal-line carry share. |
| Tyrone Tracy Jr. | RB | 48 | 34 | 14 | 111.3 | 148.1 | 36.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Allen Lazard | WR | 609 | 156 | 453 | 6.4 | 32.5 | 26.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Bo Melton | WR | 610 | 176 | 434 | 9.8 | 23.6 | 13.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Curtis Samuel | WR | 587 | 154 | 433 | 5.3 | 37.6 | 32.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jalen Brooks | WR | 595 | 166 | 429 | 6.5 | 28.1 | 21.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tai Felton | WR | 601 | 199 | 402 | 29.2 | 6.0 | -23.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Xavier Restrepo | WR | 524 | 124 | 400 | 4.8 | 57.6 | 52.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cedric Tillman | WR | 499 | 114 | 385 | 6.6 | 62.4 | 55.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Ben Skowronek | WR | 501 | 187 | 314 | 0.6 | 13.1 | 12.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tyrell Shavers | WR | 439 | 129 | 310 | 4.0 | 55.1 | 51.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cody White | WR | 483 | 175 | 308 | 8.5 | 23.7 | 15.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brock Wright | TE | 280 | 42 | 238 | 27.3 | 65.6 | 38.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, number of receiving competitors, recent role-change signal. |
| Josh Whyle | TE | 290 | 66 | 224 | 6.2 | 37.4 | 31.2 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, number of receiving competitors, prior receiving-yard production. |
| Grant Calcaterra | TE | 275 | 59 | 216 | 25.6 | 43.9 | 18.3 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, number of receiving competitors. |
| Adam Trautman | TE | 271 | 56 | 215 | 27.8 | 45.2 | 17.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Cameron Latu | TE | 248 | 113 | 135 | 4.0 | 5.3 | 1.3 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Diagnostic fades / market-higher disagreements

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 66 | -41 | 174.8 | 64.4 | -110.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 126.0 | -83.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 17 | 43 | -26 | 228.2 | 154.0 | -74.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 51 | -23 | 147.9 | 100.4 | -47.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Joe Burrow | QB | 4 | 23 | -19 | 306.1 | 187.8 | -118.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Caleb Williams | QB | 7 | 25 | -18 | 299.3 | 186.5 | -112.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.7 | -87.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| DeVonta Smith | WR | 15 | 32 | -17 | 229.2 | 167.4 | -61.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 165.3 | -58.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brian Thomas Jr. | WR | 31 | 47 | -16 | 195.4 | 140.4 | -55.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | WR | 24 | 39 | -15 | 213.8 | 159.0 | -54.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 111.4 | -52.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Kyle Monangai | RB | 34 | 49 | -15 | 154.6 | 103.7 | -50.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Jaxson Dart | QB | 10 | 24 | -14 | 296.5 | 187.7 | -108.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 183.4 | -67.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mark Andrews | TE | 16 | 29 | -13 | 162.5 | 106.8 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Lamar Jackson | QB | 2 | 14 | -12 | 326.0 | 218.1 | -107.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior rushing-yard production. |
| Marvin Harrison Jr. | WR | 33 | 45 | -12 | 186.2 | 152.2 | -34.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tetairoa McMillan | WR | 16 | 27 | -11 | 223.0 | 172.5 | -50.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | WR | 14 | 25 | -11 | 224.4 | 176.0 | -48.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |

## Diagnostic market-anchor audit

Production projections still require exact replay of every relevant nonzero scoring component. Diagnostics are different: FIE builds a player-allocation signal from the league-scoring components its shadow model supports, then recenters that signal to Sleeper **total** points within the eligible position cohort. Sleeper raw-stat component availability is not a diagnostic gate.

| Pos | Comparable players | Market-anchored partials | Mean FIE scoring coverage | Unsupported FIE auxiliary keys observed |
|---|---:|---:|---:|---|
| QB | 51 | 0 | 100.0% | none |
| RB | 85 | 0 | 100.0% | none |
| WR | 126 | 0 | 100.0% | none |
| TE | 77 | 0 | 100.0% | none |

## Interpretation rules

- The FIE diagnostic view is centered within each eligible position cohort, while ineligible rows remain at Sleeper. Therefore the full-position average diagnostic projection equals Sleeper by construction.
- A diagnostic deviation answers **where FIE allocates value differently**, not which model is better.
- Production eligibility is separate. Only positions in the validated production model registry may replace market/fallback values in runtime consumers.
- Missing profiles and team changes remain hard diagnostic guardrails. Exact scoring replay remains mandatory for production projections.
- Diagnostics do not require Sleeper raw-stat components. FIE supplies the allocation signal; Sleeper supplies the total position-level market anchor. Unsupported auxiliary FIE outcomes are disclosed and excluded from that diagnostic signal.
- P10/P50/P90 retain empirically calibrated historical OOS spread and are recentered on the diagnostic mean.
- M7/M8 diagnostic feature evidence can explain football mechanisms but does not stack onto projections unless its own sequential activation gate validates.
- Return production affects fantasy values only when the league scores it and the corresponding M9 return target independently validates.