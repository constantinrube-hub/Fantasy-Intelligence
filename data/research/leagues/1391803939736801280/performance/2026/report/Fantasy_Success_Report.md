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
| QB | Diagnostic model | 77 | 0 | 122.2 | 122.2 | 0.00 | 1.000 | 0.0 | 0.0 | 100.0% | 0 |
| RB | Diagnostic model | 134 | 85 | 85.6 | 85.6 | 0.00 | 0.867 | 9.0 | 51.9 | 43.3% | 67 |
| WR | Validated preseason model | 215 | 126 | 85.7 | 85.7 | 0.00 | 0.914 | 9.2 | 53.5 | 45.6% | 104 |
| TE | Validated preseason model | 127 | 77 | 59.8 | 59.8 | -0.00 | 0.926 | 2.9 | 36.2 | 47.2% | 57 |

## Position-level predictive evidence

### QB

**Preseason evidence:** Diagnostic model; mean historical improvement -0.6%; 95% CI -2.2% to +2.3%.

**M7 driver evidence:** recent QB rushing role (opportunity), recent QB rushing role (rushing_leverage), recent opportunity-based expected production (regression), recent QB pass-attempt role (opportunity), recent snap share (opportunity), recent actual-vs-expected production gap (regression)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_pass_rush_matchup [diagnostic_only], public_coverage_matchup [diagnostic_only]

### RB

**Preseason evidence:** Diagnostic model; mean historical improvement +3.5%; 95% CI -3.0% to +8.2%.

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
| Josh Allen | 361.5 | 361.5 | 0.0 | +0.0% | 1 | 1 | 0 | — | 321.2 | 361.0 | 403.3 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Lamar Jackson | 326.0 | 326.0 | 0.0 | +0.0% | 2 | 2 | 0 | — | 285.3 | 326.0 | 367.1 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Drake Maye | 320.8 | 320.8 | 0.0 | +0.0% | 3 | 3 | 0 | — | 279.4 | 320.4 | 361.7 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Joe Burrow | 306.1 | 306.1 | 0.0 | +0.0% | 4 | 6 | -2 | — | 265.7 | 305.8 | 347.1 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Jalen Hurts | 310.5 | 310.5 | 0.0 | +0.0% | 5 | 4 | 1 | — | 269.9 | 309.9 | 352.0 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Jayden Daniels | 308.7 | 308.7 | 0.0 | +0.0% | 6 | 5 | 1 | — | 268.2 | 308.3 | 349.3 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Caleb Williams | 299.3 | 299.3 | 0.0 | +0.0% | 7 | 10 | -3 | — | 259.8 | 298.9 | 339.1 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Dak Prescott | 303.9 | 303.9 | 0.0 | +0.0% | 8 | 7 | 1 | — | 263.9 | 303.2 | 345.1 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Justin Herbert | 295.5 | 295.5 | 0.0 | +0.0% | 9 | 13 | -4 | — | 254.5 | 294.8 | 336.8 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Jaxson Dart | 296.5 | 296.5 | 0.0 | +0.0% | 10 | 11 | -1 | — | 257.0 | 296.2 | 336.6 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Matthew Stafford | 280.2 | 280.2 | 0.0 | +0.0% | 11 | 17 | -6 | — | 239.9 | 279.6 | 322.0 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Trevor Lawrence | 303.4 | 303.4 | 0.0 | +0.0% | 12 | 8 | 4 | — | 263.0 | 303.0 | 344.0 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Patrick Mahomes | 286.7 | 286.7 | 0.0 | +0.0% | 13 | 14 | -1 | — | 246.5 | 286.0 | 327.7 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Bo Nix | 295.7 | 295.7 | 0.0 | +0.0% | 14 | 12 | 2 | — | 255.0 | 295.5 | 337.0 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Brock Purdy | 303.2 | 303.2 | 0.0 | +0.0% | 15 | 9 | 6 | — | 262.5 | 302.7 | 344.9 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Jared Goff | 283.5 | 283.5 | 0.0 | +0.0% | 16 | 15 | 1 | — | 243.7 | 282.8 | 323.5 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Baker Mayfield | 274.9 | 274.9 | 0.0 | +0.0% | 17 | 19 | -2 | — | 235.4 | 274.5 | 314.9 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Jordan Love | 278.5 | 278.5 | 0.0 | +0.0% | 18 | 18 | 0 | — | 238.7 | 278.1 | 318.5 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Kyler Murray | 283.1 | 283.1 | 0.0 | +0.0% | 19 | 16 | 3 | — | 243.6 | 282.1 | 323.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Sam Darnold | 262.7 | 262.7 | 0.0 | +0.0% | 20 | 22 | -2 | — | 222.6 | 262.3 | 303.4 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Fernando Mendoza | 212.2 | 212.2 | 0.0 | +0.0% | 21 | 28 | -7 | — | 174.7 | 211.3 | 251.1 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Tyler Shough | 270.9 | 270.9 | 0.0 | +0.0% | 22 | 20 | 2 | — | 231.0 | 270.4 | 310.9 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |
| Malik Willis | 270.1 | 270.1 | 0.0 | +0.0% | 23 | 21 | 2 | — | 229.5 | 269.7 | 310.8 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| C.J. Stroud | 247.8 | 247.8 | 0.0 | +0.0% | 24 | 23 | 1 | — | 208.8 | 247.0 | 287.7 | Diagnostic model | No diagnostic deviation: the FIE shadow model does not cover every active core league-scoring component (pass_int). |

### RB Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jahmyr Gibbs | 331.4 | 268.5 | -62.9 | -19.0% | 1 | 3 | -2 | — | 236.2 | 268.6 | 299.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Bijan Robinson | 324.9 | 286.8 | -38.1 | -11.7% | 2 | 2 | 0 | — | 255.2 | 286.7 | 318.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior rushing-yard production. |
| Christian McCaffrey | 291.0 | 308.5 | 17.5 | +6.0% | 3 | 1 | 2 | — | 277.0 | 308.2 | 340.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, recent opportunity-based expected production. |
| Jonathan Taylor | 272.3 | 265.4 | -6.9 | -2.5% | 4 | 4 | 0 | — | 233.9 | 265.4 | 297.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| James Cook | 260.8 | 238.0 | -22.8 | -8.8% | 5 | 7 | -2 | — | 206.6 | 237.7 | 269.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| De'Von Achane | 257.4 | 265.2 | 7.8 | +3.0% | 6 | 5 | 1 | — | 233.3 | 265.3 | 296.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Saquon Barkley | 246.7 | 200.4 | -46.3 | -18.8% | 7 | 15 | -8 | — | 169.9 | 200.1 | 231.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Ashton Jeanty | 233.9 | 207.0 | -26.9 | -11.5% | 8 | 12 | -4 | — | 176.4 | 206.4 | 238.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Omarion Hampton | 242.9 | 197.4 | -45.5 | -18.7% | 9 | 17 | -8 | — | 166.2 | 197.3 | 228.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Chase Brown | 255.2 | 229.2 | -26.0 | -10.2% | 10 | 8 | 2 | — | 198.4 | 228.7 | 260.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Kenneth Walker III | 244.0 | 244.0 | 0.0 | +0.0% | 11 | 6 | 5 | — | 212.4 | 243.7 | 275.4 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Derrick Henry | 246.9 | 202.6 | -44.3 | -17.9% | 12 | 14 | -2 | — | 171.6 | 202.5 | 233.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Jeremiyah Love | 211.8 | 211.8 | 0.0 | +0.0% | 13 | 9 | 4 | — | 180.9 | 211.4 | 243.4 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Kyren Williams | 208.0 | 208.0 | 0.0 | +0.0% | 14 | 10 | 4 | — | 177.6 | 207.5 | 239.0 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Josh Jacobs | 202.6 | 192.0 | -10.6 | -5.2% | 15 | 18 | -3 | — | 161.4 | 191.2 | 223.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Breece Hall | 211.0 | 170.0 | -41.0 | -19.4% | 16 | 24 | -8 | — | 139.4 | 169.8 | 200.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Javonte Williams | 207.3 | 184.0 | -23.3 | -11.2% | 17 | 19 | -2 | — | 153.6 | 183.6 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bucky Irving | 197.3 | 179.4 | -17.9 | -9.1% | 18 | 21 | -3 | — | 148.9 | 178.9 | 210.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Cam Skattebo | 201.2 | 200.1 | -1.1 | -0.5% | 19 | 16 | 3 | — | 170.1 | 199.7 | 231.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Travis Etienne | 207.7 | 207.7 | 0.0 | +0.0% | 20 | 11 | 9 | — | 176.9 | 207.2 | 238.7 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| David Montgomery | 206.1 | 206.1 | 0.0 | +0.0% | 21 | 13 | 8 | — | 175.2 | 205.8 | 237.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Quinshon Judkins | 196.0 | 168.6 | -27.4 | -14.0% | 22 | 25 | -3 | — | 138.4 | 168.3 | 199.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| TreVeyon Henderson | 171.0 | 157.3 | -13.7 | -8.0% | 23 | 28 | -5 | — | 127.3 | 156.8 | 188.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| D'Andre Swift | 208.0 | 181.1 | -26.9 | -12.9% | 24 | 20 | 4 | — | 149.8 | 180.3 | 212.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bhayshul Tuten | 174.8 | 64.4 | -110.4 | -63.1% | 25 | 66 | -41 | — | 34.5 | 63.9 | 95.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Jadarian Price | 170.0 | 170.0 | 0.0 | +0.0% | 26 | 23 | 3 | — | 140.8 | 169.3 | 200.6 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jaylen Warren | 170.6 | 178.3 | 7.7 | +4.5% | 27 | 22 | 5 | — | 148.2 | 178.0 | 208.2 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Chuba Hubbard | 147.9 | 100.3 | -47.6 | -32.2% | 28 | 51 | -23 | — | 71.0 | 99.4 | 130.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| RJ Harvey | 144.1 | 153.3 | 9.2 | +6.4% | 29 | 31 | -2 | — | 124.4 | 152.6 | 182.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Rhamondre Stevenson | 169.0 | 151.9 | -17.1 | -10.1% | 30 | 33 | -3 | — | 122.1 | 151.3 | 182.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior receiving-yard production. |
| Tony Pollard | 160.1 | 167.6 | 7.5 | +4.7% | 31 | 26 | 5 | — | 138.3 | 167.2 | 198.0 | Diagnostic model | FIE diagnostic is higher; main model signals: recent carry share, prior-season fantasy production, prior rushing-yard production. |
| Rico Dowdle | 161.1 | 161.1 | 0.0 | +0.0% | 32 | 27 | 5 | — | 131.3 | 160.3 | 191.4 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| J.K. Dobbins | 160.2 | 153.5 | -6.7 | -4.2% | 33 | 30 | 3 | — | 123.9 | 153.1 | 183.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior-season fantasy production, recent carry share. |
| Kyle Monangai | 154.6 | 103.7 | -50.9 | -32.9% | 34 | 49 | -15 | — | 74.4 | 102.9 | 134.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Blake Corum | 135.3 | 135.3 | 0.0 | +0.0% | 35 | 38 | -3 | — | 106.6 | 134.8 | 164.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jonathon Brooks | 154.9 | 154.9 | 0.0 | +0.0% | 36 | 29 | 7 | — | 126.5 | 154.3 | 184.1 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |

### WR Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 311.1 | 272.5 | -38.6 | -12.4% | 1 | 3 | -2 | 285.8 | 240.8 | 272.0 | 304.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Puka Nacua | 312.5 | 312.5 | 0.0 | +0.0% | 2 | 1 | 1 | — | 280.0 | 312.5 | 344.7 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jaxon Smith-Njigba | 284.6 | 296.0 | 11.4 | +4.0% | 3 | 2 | 1 | 309.4 | 264.6 | 295.8 | 328.0 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Amon-Ra St. Brown | 280.5 | 264.7 | -15.8 | -5.6% | 4 | 4 | 0 | 278.0 | 232.9 | 264.3 | 297.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| CeeDee Lamb | 270.5 | 219.4 | -51.1 | -18.9% | 5 | 12 | -7 | 232.8 | 188.3 | 218.9 | 251.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Justin Jefferson | 250.4 | 183.4 | -67.0 | -26.8% | 6 | 20 | -14 | 196.7 | 153.0 | 183.0 | 214.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Drake London | 250.2 | 228.8 | -21.4 | -8.5% | 7 | 7 | 0 | 242.2 | 198.0 | 228.2 | 260.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| A.J. Brown | 247.2 | 247.2 | 0.0 | +0.0% | 8 | 6 | 2 | — | 216.4 | 246.7 | 278.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| George Pickens | 245.7 | 225.1 | -20.6 | -8.4% | 9 | 9 | 0 | 238.5 | 194.1 | 224.8 | 256.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Nico Collins | 262.0 | 206.4 | -55.6 | -21.2% | 10 | 14 | -4 | 219.8 | 175.0 | 206.1 | 237.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Malik Nabers | 236.7 | 202.2 | -34.5 | -14.6% | 11 | 16 | -5 | 215.6 | 171.6 | 201.8 | 233.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Rashee Rice | 229.3 | 251.2 | 21.9 | +9.6% | 12 | 5 | 7 | 264.6 | 218.9 | 251.2 | 282.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chris Olave | 235.9 | 226.7 | -9.2 | -3.9% | 13 | 8 | 5 | 240.1 | 195.3 | 226.6 | 258.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | 224.4 | 176.0 | -48.4 | -21.6% | 14 | 25 | -11 | 189.3 | 145.5 | 175.7 | 207.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| DeVonta Smith | 229.2 | 167.3 | -61.9 | -27.0% | 15 | 32 | -17 | 180.7 | 137.4 | 166.8 | 198.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | 223.0 | 172.5 | -50.5 | -22.7% | 16 | 27 | -11 | 185.8 | 142.3 | 172.0 | 202.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Ladd McConkey | 228.2 | 154.0 | -74.2 | -32.5% | 17 | 43 | -26 | 167.3 | 124.5 | 153.3 | 184.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | 224.0 | 165.3 | -58.7 | -26.2% | 18 | 35 | -17 | 178.7 | 135.2 | 164.9 | 195.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Zay Flowers | 228.2 | 213.1 | -15.1 | -6.6% | 19 | 13 | 6 | 226.5 | 181.4 | 213.0 | 244.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Garrett Wilson | 224.9 | 202.3 | -22.6 | -10.1% | 20 | 15 | 5 | 215.6 | 171.5 | 201.7 | 233.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Jaylen Waddle | 221.0 | 221.0 | 0.0 | +0.0% | 21 | 11 | 10 | — | 190.0 | 220.8 | 252.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Davante Adams | 192.5 | 192.5 | 0.0 | +0.0% | 22 | 17 | 5 | — | 161.4 | 192.2 | 223.9 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Luther Burden III | 209.0 | 125.9 | -83.1 | -39.7% | 23 | 58 | -35 | 139.3 | 97.5 | 125.1 | 155.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Terry McLaurin | 213.8 | 159.0 | -54.8 | -25.6% | 24 | 39 | -15 | 172.3 | 128.8 | 158.3 | 189.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DJ Moore | 179.0 | 179.0 | 0.0 | +0.0% | 25 | 22 | 3 | — | 149.3 | 178.5 | 209.8 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jameson Williams | 206.2 | 176.0 | -30.2 | -14.6% | 26 | 24 | 2 | 189.4 | 145.3 | 175.4 | 207.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mike Evans | 222.2 | 222.2 | 0.0 | +0.0% | 27 | 10 | 17 | — | 191.0 | 221.7 | 253.4 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rome Odunze | 207.9 | 166.9 | -41.0 | -19.7% | 28 | 33 | -5 | 180.2 | 136.6 | 166.2 | 197.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Carnell Tate | 177.3 | 177.3 | 0.0 | +0.0% | 29 | 23 | 6 | — | 147.3 | 176.9 | 208.4 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Christian Watson | 207.6 | 175.3 | -32.3 | -15.6% | 30 | 26 | 4 | 188.6 | 144.5 | 174.7 | 206.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Brian Thomas Jr. | 195.4 | 140.4 | -55.0 | -28.2% | 31 | 47 | -16 | 153.7 | 111.0 | 140.0 | 170.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DK Metcalf | 183.3 | 170.0 | -13.3 | -7.2% | 32 | 30 | 2 | 183.4 | 139.8 | 169.4 | 201.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Marvin Harrison Jr. | 186.2 | 152.2 | -34.0 | -18.2% | 33 | 45 | -12 | 165.6 | 122.4 | 151.7 | 182.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Parker Washington | 212.4 | 153.8 | -58.6 | -27.6% | 34 | 44 | -10 | 167.2 | 124.2 | 153.3 | 184.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Courtland Sutton | 174.3 | 188.7 | 14.4 | +8.2% | 35 | 18 | 17 | 202.0 | 158.4 | 188.4 | 219.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Michael Wilson | 166.0 | 180.2 | 14.2 | +8.6% | 36 | 21 | 15 | 193.6 | 149.3 | 179.8 | 211.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |

### TE Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Trey McBride | 234.9 | 235.4 | 0.5 | +0.2% | 1 | 1 | 0 | 253.3 | 209.3 | 234.9 | 261.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Brock Bowers | 253.5 | 183.8 | -69.7 | -27.5% | 2 | 4 | -2 | 201.7 | 158.9 | 183.5 | 209.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Colston Loveland | 215.4 | 127.7 | -87.7 | -40.7% | 3 | 20 | -17 | 145.6 | 103.6 | 127.2 | 152.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tyler Warren | 201.1 | 165.9 | -35.2 | -17.5% | 4 | 7 | -3 | 183.9 | 141.1 | 165.6 | 191.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Sam LaPorta | 196.5 | 158.4 | -38.1 | -19.4% | 5 | 8 | -3 | 176.3 | 133.6 | 158.2 | 183.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Tucker Kraft | 174.4 | 171.4 | -3.0 | -1.7% | 6 | 6 | 0 | 189.3 | 146.1 | 171.0 | 197.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Harold Fannin Jr. | 180.4 | 173.3 | -7.1 | -4.0% | 7 | 5 | 2 | 191.2 | 148.0 | 173.1 | 198.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Kyle Pitts | 171.6 | 187.5 | 15.9 | +9.3% | 8 | 3 | 5 | 205.5 | 162.3 | 187.5 | 212.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Dalton Kincaid | 163.6 | 111.3 | -52.3 | -31.9% | 9 | 24 | -15 | 129.3 | 87.7 | 110.8 | 135.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| George Kittle | 169.3 | 194.2 | 24.9 | +14.7% | 10 | 2 | 8 | 212.2 | 168.9 | 194.0 | 219.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Travis Kelce | 171.4 | 153.3 | -18.1 | -10.6% | 11 | 11 | 0 | 171.3 | 128.4 | 153.2 | 178.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Jake Ferguson | 159.8 | 139.9 | -19.9 | -12.4% | 12 | 15 | -3 | 157.9 | 115.0 | 139.7 | 165.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior reception volume. |
| Isaiah Likely | 157.3 | 157.3 | 0.0 | +0.0% | 13 | 9 | 4 | — | 132.9 | 156.9 | 181.7 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Dallas Goedert | 136.0 | 146.7 | 10.7 | +7.9% | 14 | 13 | 1 | 164.7 | 121.7 | 146.5 | 171.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, recent role-change signal. |
| Oronde Gadsden II | 141.8 | 128.2 | -13.6 | -9.6% | 15 | 19 | -4 | 146.2 | 104.0 | 128.1 | 152.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Mark Andrews | 162.5 | 106.8 | -55.7 | -34.2% | 16 | 29 | -13 | 124.8 | 83.1 | 106.5 | 131.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Hunter Henry | 153.5 | 139.3 | -14.2 | -9.3% | 17 | 16 | 1 | 157.2 | 114.6 | 138.8 | 164.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Brenton Strange | 161.0 | 123.3 | -37.7 | -23.4% | 18 | 21 | -3 | 141.3 | 99.0 | 123.1 | 147.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Kenyon Sadiq | 100.2 | 100.2 | 0.0 | +0.0% | 19 | 33 | -14 | — | 77.7 | 99.6 | 123.4 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| T.J. Hockenson | 155.0 | 110.0 | -45.0 | -29.0% | 20 | 28 | -8 | 127.9 | 86.4 | 109.6 | 134.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| AJ Barner | 142.4 | 110.3 | -32.1 | -22.6% | 21 | 27 | -6 | 128.2 | 86.6 | 110.2 | 134.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Chig Okonkwo | 144.1 | 144.1 | 0.0 | +0.0% | 22 | 14 | 8 | — | 120.3 | 143.9 | 168.4 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Juwan Johnson | 140.9 | 147.1 | 6.2 | +4.4% | 23 | 12 | 11 | 165.0 | 122.3 | 146.8 | 172.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Dalton Schultz | 150.9 | 154.7 | 3.8 | +2.5% | 24 | 10 | 14 | 172.6 | 130.0 | 154.4 | 179.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Largest model-market disagreements

These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 66 | -41 | 174.8 | 64.4 | -110.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 125.9 | -83.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 17 | 43 | -26 | 228.2 | 154.0 | -74.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 51 | -23 | 147.9 | 100.3 | -47.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.7 | -87.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 165.3 | -58.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Courtland Sutton | WR | 35 | 18 | 17 | 174.3 | 188.7 | 14.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DeVonta Smith | WR | 15 | 32 | -17 | 229.2 | 167.3 | -61.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brian Thomas Jr. | WR | 31 | 47 | -16 | 195.4 | 140.4 | -55.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Kyle Monangai | RB | 34 | 49 | -15 | 154.6 | 103.7 | -50.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 111.3 | -52.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Michael Wilson | WR | 36 | 21 | 15 | 166.0 | 180.2 | 14.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | WR | 24 | 39 | -15 | 213.8 | 159.0 | -54.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Schultz | TE | 24 | 10 | 14 | 150.9 | 154.7 | 3.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 183.4 | -67.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mark Andrews | TE | 16 | 29 | -13 | 162.5 | 106.8 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Marvin Harrison Jr. | WR | 33 | 45 | -12 | 186.2 | 152.2 | -34.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tetairoa McMillan | WR | 16 | 27 | -11 | 223.0 | 172.5 | -50.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Juwan Johnson | TE | 23 | 12 | 11 | 140.9 | 147.1 | 6.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Tee Higgins | WR | 14 | 25 | -11 | 224.4 | 176.0 | -48.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Parker Washington | WR | 34 | 44 | -10 | 212.4 | 153.8 | -58.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Breece Hall | RB | 16 | 24 | -8 | 211.0 | 170.0 | -41.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Omarion Hampton | RB | 9 | 17 | -8 | 242.9 | 197.4 | -45.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| T.J. Hockenson | TE | 20 | 28 | -8 | 155.0 | 110.0 | -45.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| George Kittle | TE | 10 | 2 | 8 | 169.3 | 194.2 | 24.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Saquon Barkley | RB | 7 | 15 | -8 | 246.7 | 200.4 | -46.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Rashee Rice | WR | 12 | 5 | 7 | 229.3 | 251.2 | 21.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| CeeDee Lamb | WR | 5 | 12 | -7 | 270.5 | 219.4 | -51.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Zay Flowers | WR | 19 | 13 | 6 | 228.2 | 213.1 | -15.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| AJ Barner | TE | 21 | 27 | -6 | 142.4 | 110.3 | -32.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |

## Diagnostic sleeper candidates outside market cutoffs

These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Zavier Scott | RB | 338 | 86 | 252 | 5.6 | 36.7 | 31.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Elijah Mitchell | RB | 336 | 114 | 222 | 9.3 | 5.8 | -3.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Jacardia Wright | RB | 300 | 91 | 209 | 4.3 | 30.6 | 26.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, prior receiving-yard production. |
| Kalel Mullings | RB | 329 | 134 | 195 | 5.6 | -19.7 | -25.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Cam Akers | RB | 263 | 124 | 139 | 5.1 | 0.0 | -5.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| James Conner | RB | 69 | 37 | 32 | 57.2 | 135.5 | 78.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Audric Estimé | RB | 70 | 42 | 28 | 22.6 | 123.7 | 101.1 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, prior-season fantasy production, prior reception volume. |
| Kimani Vidal | RB | 71 | 44 | 27 | 60.0 | 115.1 | 55.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior rushing-yard production, recent opportunity-based expected production, prior-season fantasy production. |
| Jaylen Wright | RB | 77 | 58 | 19 | 44.1 | 78.2 | 34.1 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, number of backfield competitors, recent goal-line carry share. |
| Tyrone Tracy Jr. | RB | 48 | 34 | 14 | 111.3 | 148.2 | 36.9 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Allen Lazard | WR | 609 | 156 | 453 | 6.4 | 32.5 | 26.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Bo Melton | WR | 610 | 176 | 434 | 9.8 | 23.6 | 13.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Curtis Samuel | WR | 587 | 154 | 433 | 5.3 | 37.6 | 32.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jalen Brooks | WR | 595 | 166 | 429 | 6.5 | 28.0 | 21.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tai Felton | WR | 601 | 199 | 402 | 29.2 | 6.0 | -23.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Xavier Restrepo | WR | 524 | 124 | 400 | 4.8 | 57.6 | 52.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cedric Tillman | WR | 499 | 114 | 385 | 6.6 | 62.3 | 55.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Ben Skowronek | WR | 501 | 187 | 314 | 0.6 | 13.1 | 12.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tyrell Shavers | WR | 439 | 129 | 310 | 4.0 | 55.0 | 51.0 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cody White | WR | 483 | 175 | 308 | 8.5 | 23.6 | 15.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brock Wright | TE | 280 | 42 | 238 | 27.3 | 65.7 | 38.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, number of receiving competitors, recent role-change signal. |
| Josh Whyle | TE | 290 | 66 | 224 | 6.2 | 37.4 | 31.2 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, number of receiving competitors, prior receiving-yard production. |
| Grant Calcaterra | TE | 275 | 59 | 216 | 25.6 | 43.9 | 18.3 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, number of receiving competitors. |
| Adam Trautman | TE | 271 | 56 | 215 | 27.8 | 45.2 | 17.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Cameron Latu | TE | 248 | 113 | 135 | 4.0 | 5.4 | 1.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Diagnostic fades / market-higher disagreements

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 66 | -41 | 174.8 | 64.4 | -110.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 125.9 | -83.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 17 | 43 | -26 | 228.2 | 154.0 | -74.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 51 | -23 | 147.9 | 100.3 | -47.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.7 | -87.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| DeVonta Smith | WR | 15 | 32 | -17 | 229.2 | 167.3 | -61.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 165.3 | -58.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brian Thomas Jr. | WR | 31 | 47 | -16 | 195.4 | 140.4 | -55.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | WR | 24 | 39 | -15 | 213.8 | 159.0 | -54.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 111.3 | -52.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Kyle Monangai | RB | 34 | 49 | -15 | 154.6 | 103.7 | -50.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 183.4 | -67.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mark Andrews | TE | 16 | 29 | -13 | 162.5 | 106.8 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Marvin Harrison Jr. | WR | 33 | 45 | -12 | 186.2 | 152.2 | -34.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tetairoa McMillan | WR | 16 | 27 | -11 | 223.0 | 172.5 | -50.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | WR | 14 | 25 | -11 | 224.4 | 176.0 | -48.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Parker Washington | WR | 34 | 44 | -10 | 212.4 | 153.8 | -58.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Saquon Barkley | RB | 7 | 15 | -8 | 246.7 | 200.4 | -46.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Omarion Hampton | RB | 9 | 17 | -8 | 242.9 | 197.4 | -45.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| T.J. Hockenson | TE | 20 | 28 | -8 | 155.0 | 110.0 | -45.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |

## Diagnostic market-anchor audit

Production projections still require exact replay of every relevant nonzero scoring component. Diagnostics are different: FIE builds a player-allocation signal from the league-scoring components its shadow model supports, then recenters that signal to Sleeper **total** points within the eligible position cohort. Sleeper raw-stat component availability is not a diagnostic gate.

| Pos | Comparable players | Market-anchored partials | Mean FIE scoring coverage | Unsupported FIE auxiliary keys observed |
|---|---:|---:|---:|---|
| QB | 0 | 0 | —% | none |
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