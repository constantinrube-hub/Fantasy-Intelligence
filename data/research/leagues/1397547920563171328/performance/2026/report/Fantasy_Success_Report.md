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
| QB | Diagnostic model | 77 | 51 | 140.9 | 140.9 | -0.00 | 0.770 | 39.7 | 135.4 | 36.4% | 48 |
| RB | Diagnostic model | 135 | 87 | 84.6 | 84.6 | -0.00 | 0.868 | 9.6 | 53.3 | 42.2% | 70 |
| WR | Validated preseason model | 214 | 128 | 85.7 | 85.7 | -0.00 | 0.910 | 10.3 | 54.0 | 43.9% | 110 |
| TE | Validated preseason model | 123 | 78 | 61.2 | 61.2 | 0.00 | 0.911 | 3.6 | 38.2 | 45.5% | 61 |

## Position-level predictive evidence

### QB

**Preseason evidence:** Diagnostic model; mean historical improvement -0.5%; 95% CI -2.1% to +1.1%.

**M7 driver evidence:** recent QB rushing role (opportunity), recent QB rushing role (rushing_leverage), recent QB pass-attempt role (opportunity), recent opportunity-based expected production (regression), recent snap share (opportunity), recent actual-vs-expected production gap (regression)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_pass_rush_matchup [diagnostic_only], public_coverage_matchup [diagnostic_only]

### RB

**Preseason evidence:** Diagnostic model; mean historical improvement +3.5%; 95% CI -3.0% to +8.2%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent offensive snap share (opportunity), recent carry share (opportunity), recent target share (receiving_role), recent target share (opportunity), backfield competition (competition)

**M8 matchup evidence:** insufficient

### WR

**Preseason evidence:** Validated preseason model; mean historical improvement +5.7%; 95% CI +3.1% to +10.0%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent target share (opportunity), recent offensive snap share (opportunity), receiving competition (competition), number of receiving competitors (competition), recent red-zone target share (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

### TE

**Preseason evidence:** Validated preseason model; mean historical improvement +6.6%; 95% CI +4.5% to +8.7%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent target share (opportunity), recent offensive snap share (opportunity), receiving competition (competition), number of receiving competitors (competition), recent red-zone target share (opportunity)

**M8 matchup evidence:** public_defensive_synergy_matchup [diagnostic_only], public_coverage_receiving_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

## Requested Sleeper market universe

### QB Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Josh Allen | 415.5 | 341.6 | -73.9 | -17.8% | 1 | 1 | 0 | — | 291.7 | 341.1 | 391.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-TD production, recent goal-line carry share. |
| Lamar Jackson | 380.0 | 255.2 | -124.8 | -32.8% | 2 | 13 | -11 | — | 206.1 | 255.1 | 304.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior passing-TD production. |
| Drake Maye | 378.8 | 316.6 | -62.1 | -16.4% | 3 | 4 | -1 | — | 268.2 | 315.7 | 366.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Joe Burrow | 372.1 | 235.8 | -136.4 | -36.6% | 4 | 20 | -16 | — | 186.8 | 234.9 | 285.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Jalen Hurts | 352.5 | 283.3 | -69.3 | -19.7% | 5 | 7 | -2 | — | 235.0 | 282.8 | 331.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent goal-line carry share. |
| Jayden Daniels | 350.7 | 258.7 | -92.0 | -26.2% | 6 | 12 | -6 | — | 210.1 | 257.9 | 307.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, recent QB rushing role, prior-season fantasy production. |
| Caleb Williams | 355.3 | 219.0 | -136.4 | -38.4% | 7 | 25 | -18 | — | 170.2 | 218.7 | 267.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Dak Prescott | 365.9 | 281.7 | -84.2 | -23.0% | 8 | 8 | 0 | — | 232.7 | 281.3 | 331.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, recent goal-line carry share. |
| Justin Herbert | 347.5 | 245.4 | -102.1 | -29.4% | 9 | 16 | -7 | — | 196.3 | 244.7 | 295.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Jaxson Dart | 340.5 | 209.2 | -131.3 | -38.6% | 10 | 27 | -17 | — | 160.5 | 208.8 | 258.4 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Matthew Stafford | 280.2 | 280.2 | 0.0 | +0.0% | 11 | 9 | 2 | — | 233.3 | 279.5 | 328.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Trevor Lawrence | 355.4 | 273.1 | -82.3 | -23.2% | 12 | 10 | 2 | — | 223.5 | 272.0 | 323.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Patrick Mahomes | 344.7 | 296.3 | -48.4 | -14.1% | 13 | 6 | 7 | — | 247.9 | 295.6 | 345.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, recent opportunity-based expected production. |
| Bo Nix | 347.7 | 237.9 | -109.8 | -31.6% | 14 | 19 | -5 | — | 189.4 | 237.6 | 287.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, recent opportunity-based expected production. |
| Brock Purdy | 363.2 | 323.5 | -39.7 | -10.9% | 15 | 3 | 12 | — | 274.2 | 323.3 | 372.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Jared Goff | 343.5 | 230.0 | -113.4 | -33.0% | 16 | 22 | -6 | — | 181.2 | 229.5 | 279.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent opportunity-based expected production. |
| Baker Mayfield | 326.9 | 233.8 | -93.0 | -28.5% | 17 | 21 | -4 | — | 185.6 | 232.9 | 283.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent role-change signal. |
| Jordan Love | 332.5 | 212.2 | -120.4 | -36.2% | 18 | 26 | -8 | — | 163.6 | 212.0 | 261.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Kyler Murray | 327.1 | 327.1 | 0.0 | +0.0% | 19 | 2 | 17 | — | 279.8 | 326.1 | 375.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Sam Darnold | 314.7 | 197.2 | -117.5 | -37.3% | 20 | 28 | -8 | — | 149.3 | 197.0 | 245.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, pfr times sacked. |
| Fernando Mendoza | 250.2 | 250.2 | 0.0 | +0.0% | 21 | 15 | 6 | — | 203.8 | 249.1 | 296.7 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Tyler Shough | 314.9 | 251.0 | -63.9 | -20.3% | 22 | 14 | 8 | — | 202.6 | 251.1 | 299.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, pfr times sacked, recent actual-vs-expected production gap. |
| Daniel Jones | 261.5 | 244.5 | -17.1 | -6.5% | 23 | 17 | 6 | — | 198.1 | 243.8 | 292.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, prior rushing-TD production. |
| C.J. Stroud | 291.8 | 181.0 | -110.8 | -38.0% | 24 | 34 | -10 | — | 133.5 | 179.7 | 228.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |

### RB Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jahmyr Gibbs | 331.4 | 267.9 | -63.5 | -19.2% | 1 | 3 | -2 | — | 235.8 | 267.4 | 300.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Bijan Robinson | 324.9 | 286.1 | -38.8 | -11.9% | 2 | 2 | 0 | — | 253.8 | 285.8 | 318.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior rushing-yard production. |
| Christian McCaffrey | 291.0 | 308.0 | 17.0 | +5.8% | 3 | 1 | 2 | — | 276.2 | 307.7 | 339.9 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, recent opportunity-based expected production. |
| Jonathan Taylor | 272.3 | 264.6 | -7.7 | -2.8% | 4 | 5 | -1 | — | 233.0 | 264.5 | 295.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| James Cook | 260.8 | 237.4 | -23.4 | -9.0% | 5 | 7 | -2 | — | 205.8 | 237.2 | 269.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Saquon Barkley | 246.7 | 199.8 | -46.9 | -19.0% | 6 | 15 | -9 | — | 168.1 | 199.8 | 231.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| De'Von Achane | 257.4 | 264.8 | 7.4 | +2.9% | 7 | 4 | 3 | — | 232.6 | 264.7 | 296.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Ashton Jeanty | 233.9 | 206.3 | -27.6 | -11.8% | 8 | 12 | -4 | — | 174.8 | 206.3 | 237.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Omarion Hampton | 242.9 | 196.8 | -46.1 | -19.0% | 9 | 17 | -8 | — | 165.7 | 196.6 | 228.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Chase Brown | 255.2 | 228.8 | -26.4 | -10.3% | 10 | 8 | 2 | — | 197.3 | 228.7 | 260.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Kenneth Walker III | 244.0 | 244.0 | 0.0 | +0.0% | 11 | 6 | 5 | — | 212.3 | 243.7 | 275.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Derrick Henry | 246.9 | 202.1 | -44.8 | -18.1% | 12 | 14 | -2 | — | 170.8 | 202.2 | 233.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Jeremiyah Love | 211.8 | 211.8 | 0.0 | +0.0% | 13 | 9 | 4 | — | 181.2 | 211.3 | 242.8 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Kyren Williams | 208.0 | 208.0 | 0.0 | +0.0% | 14 | 10 | 4 | — | 177.5 | 207.7 | 238.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Javonte Williams | 212.0 | 183.3 | -28.7 | -13.5% | 15 | 19 | -4 | — | 152.7 | 182.9 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Breece Hall | 211.0 | 169.9 | -41.1 | -19.5% | 16 | 24 | -8 | — | 138.5 | 169.6 | 201.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Josh Jacobs | 87.2 | 191.3 | 104.1 | +119.4% | 17 | 18 | -1 | — | 165.7 | 190.3 | 218.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Cam Skattebo | 201.2 | 199.5 | -1.7 | -0.8% | 18 | 16 | 2 | — | 168.7 | 198.9 | 231.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Bucky Irving | 197.3 | 178.6 | -18.7 | -9.5% | 19 | 21 | -2 | — | 148.1 | 178.5 | 209.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Travis Etienne | 207.7 | 207.7 | 0.0 | +0.0% | 20 | 11 | 9 | — | 176.9 | 207.2 | 238.7 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| David Montgomery | 206.1 | 206.1 | 0.0 | +0.0% | 21 | 13 | 8 | — | 175.5 | 205.6 | 237.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| D'Andre Swift | 208.0 | 180.6 | -27.4 | -13.2% | 22 | 20 | 2 | — | 150.1 | 180.4 | 212.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Quinshon Judkins | 196.0 | 167.8 | -28.2 | -14.4% | 23 | 25 | -2 | — | 137.4 | 167.3 | 198.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| TreVeyon Henderson | 171.0 | 156.8 | -14.2 | -8.3% | 24 | 28 | -4 | — | 126.8 | 156.0 | 188.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bhayshul Tuten | 174.8 | 63.8 | -111.0 | -63.5% | 25 | 67 | -42 | — | 34.0 | 63.5 | 93.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Jadarian Price | 170.0 | 170.0 | 0.0 | +0.0% | 26 | 23 | 3 | — | 140.6 | 169.4 | 199.9 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jaylen Warren | 170.6 | 177.9 | 7.3 | +4.3% | 27 | 22 | 5 | — | 148.1 | 177.4 | 208.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Chuba Hubbard | 147.9 | 99.8 | -48.1 | -32.6% | 28 | 52 | -24 | — | 71.3 | 98.9 | 129.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| RJ Harvey | 144.1 | 152.7 | 8.6 | +6.0% | 29 | 31 | -2 | — | 123.7 | 152.1 | 182.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Rhamondre Stevenson | 169.0 | 151.4 | -17.6 | -10.4% | 30 | 33 | -3 | — | 121.6 | 150.8 | 181.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior receiving-yard production. |
| Tony Pollard | 160.1 | 167.1 | 7.0 | +4.4% | 31 | 26 | 5 | — | 138.0 | 166.4 | 197.1 | Diagnostic model | FIE diagnostic is higher; main model signals: recent carry share, prior-season fantasy production, prior rushing-yard production. |
| Rico Dowdle | 161.1 | 161.1 | 0.0 | +0.0% | 32 | 27 | 5 | — | 131.9 | 160.5 | 191.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| J.K. Dobbins | 160.2 | 152.8 | -7.4 | -4.6% | 33 | 30 | 3 | — | 123.9 | 151.7 | 182.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior-season fantasy production, recent carry share. |
| Kyle Monangai | 154.6 | 102.9 | -51.7 | -33.5% | 34 | 50 | -16 | — | 74.1 | 102.3 | 132.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Blake Corum | 135.3 | 135.3 | 0.0 | +0.0% | 35 | 38 | -3 | — | 106.3 | 134.8 | 164.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jonathon Brooks | 154.9 | 154.9 | 0.0 | +0.0% | 36 | 29 | 7 | — | 126.0 | 154.4 | 184.5 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |

### WR Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 311.1 | 271.8 | -39.3 | -12.6% | 1 | 3 | -2 | 285.8 | 239.8 | 271.5 | 303.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Puka Nacua | 312.5 | 312.5 | 0.0 | +0.0% | 2 | 1 | 1 | — | 280.3 | 312.2 | 344.9 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jaxon Smith-Njigba | 284.6 | 295.4 | 10.8 | +3.8% | 3 | 2 | 1 | 309.4 | 263.4 | 295.1 | 327.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Amon-Ra St. Brown | 280.5 | 264.0 | -16.5 | -5.9% | 4 | 4 | 0 | 278.0 | 232.0 | 264.1 | 295.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| CeeDee Lamb | 270.5 | 218.8 | -51.7 | -19.1% | 5 | 12 | -7 | 232.7 | 187.4 | 218.6 | 250.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Justin Jefferson | 250.4 | 182.7 | -67.7 | -27.0% | 6 | 20 | -14 | 196.6 | 152.1 | 182.4 | 214.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| A.J. Brown | 247.2 | 247.2 | 0.0 | +0.0% | 7 | 6 | 1 | — | 216.0 | 247.1 | 278.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Drake London | 250.2 | 228.2 | -22.0 | -8.8% | 8 | 7 | 1 | 242.1 | 196.6 | 227.8 | 260.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| George Pickens | 245.7 | 224.5 | -21.2 | -8.6% | 9 | 9 | 0 | 238.4 | 193.2 | 223.9 | 256.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Nico Collins | 262.0 | 205.8 | -56.2 | -21.4% | 10 | 14 | -4 | 219.8 | 174.3 | 205.7 | 237.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Malik Nabers | 236.7 | 201.6 | -35.1 | -14.8% | 11 | 16 | -5 | 215.6 | 170.8 | 201.2 | 232.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Rashee Rice | 229.3 | 250.5 | 21.2 | +9.3% | 12 | 5 | 7 | 264.5 | 218.2 | 250.5 | 282.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chris Olave | 235.9 | 225.7 | -10.2 | -4.3% | 13 | 8 | 5 | 239.6 | 194.6 | 225.4 | 257.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| DeVonta Smith | 229.2 | 166.7 | -62.5 | -27.3% | 14 | 32 | -18 | 180.7 | 137.0 | 165.9 | 197.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | 224.4 | 175.4 | -49.0 | -21.8% | 15 | 25 | -10 | 189.4 | 145.5 | 175.2 | 205.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Ladd McConkey | 228.2 | 153.3 | -74.9 | -32.8% | 16 | 43 | -27 | 167.3 | 123.2 | 152.7 | 183.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | 223.0 | 171.8 | -51.2 | -22.9% | 17 | 27 | -10 | 185.8 | 141.8 | 171.4 | 202.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | 224.0 | 164.7 | -59.3 | -26.5% | 18 | 35 | -17 | 178.6 | 134.7 | 163.8 | 195.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Zay Flowers | 228.2 | 212.5 | -15.7 | -6.9% | 19 | 13 | 6 | 226.5 | 180.6 | 212.5 | 244.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jaylen Waddle | 221.0 | 221.0 | 0.0 | +0.0% | 20 | 11 | 9 | — | 190.4 | 220.5 | 251.8 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Garrett Wilson | 224.9 | 201.7 | -23.2 | -10.3% | 21 | 15 | 6 | 215.7 | 170.6 | 201.3 | 232.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Davante Adams | 192.5 | 192.5 | 0.0 | +0.0% | 22 | 17 | 5 | — | 162.3 | 192.0 | 223.5 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Luther Burden III | 209.0 | 125.3 | -83.7 | -40.0% | 23 | 58 | -35 | 139.3 | 96.2 | 124.9 | 155.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| DJ Moore | 179.0 | 179.0 | 0.0 | +0.0% | 24 | 22 | 2 | — | 149.1 | 178.4 | 209.3 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Terry McLaurin | 213.8 | 158.4 | -55.4 | -25.9% | 25 | 39 | -14 | 172.3 | 128.0 | 157.7 | 189.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jameson Williams | 206.2 | 175.4 | -30.8 | -14.9% | 26 | 24 | 2 | 189.4 | 145.0 | 175.3 | 205.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mike Evans | 222.2 | 222.2 | 0.0 | +0.0% | 27 | 10 | 17 | — | 191.2 | 221.9 | 254.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rome Odunze | 207.9 | 166.2 | -41.7 | -20.1% | 28 | 33 | -5 | 180.2 | 136.2 | 165.6 | 196.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Carnell Tate | 177.3 | 177.3 | 0.0 | +0.0% | 29 | 23 | 6 | — | 147.7 | 176.7 | 208.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Christian Watson | 207.6 | 174.7 | -32.9 | -15.8% | 30 | 26 | 4 | 188.7 | 144.1 | 174.3 | 206.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Parker Washington | 212.4 | 153.2 | -59.2 | -27.9% | 31 | 44 | -13 | 167.2 | 122.6 | 153.1 | 183.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Brian Thomas Jr. | 195.4 | 139.7 | -55.7 | -28.5% | 32 | 47 | -15 | 153.7 | 110.5 | 139.0 | 170.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DK Metcalf | 183.3 | 169.4 | -13.9 | -7.6% | 33 | 30 | 3 | 183.4 | 139.3 | 168.8 | 200.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Marvin Harrison Jr. | 186.2 | 151.6 | -34.6 | -18.6% | 34 | 45 | -11 | 165.6 | 122.3 | 151.1 | 182.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Courtland Sutton | 174.3 | 188.0 | 13.7 | +7.9% | 35 | 18 | 17 | 202.0 | 157.1 | 188.0 | 219.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Michael Wilson | 166.0 | 179.7 | 13.7 | +8.2% | 36 | 21 | 15 | 193.6 | 148.7 | 179.2 | 210.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |

### TE Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Brock Bowers | 253.5 | 183.3 | -70.2 | -27.7% | 1 | 4 | -3 | 201.8 | 157.1 | 183.3 | 209.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Trey McBride | 234.9 | 234.7 | -0.2 | -0.1% | 2 | 1 | 1 | 253.3 | 209.1 | 234.6 | 260.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Colston Loveland | 215.4 | 127.1 | -88.3 | -41.0% | 3 | 20 | -17 | 145.7 | 102.7 | 127.0 | 151.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tyler Warren | 201.1 | 165.1 | -36.0 | -17.9% | 4 | 7 | -3 | 183.7 | 140.2 | 165.0 | 190.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Sam LaPorta | 196.5 | 157.9 | -38.6 | -19.6% | 5 | 8 | -3 | 176.5 | 133.1 | 157.7 | 182.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Tucker Kraft | 174.4 | 171.0 | -3.4 | -2.0% | 6 | 6 | 0 | 189.6 | 145.8 | 170.8 | 196.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Kyle Pitts | 171.6 | 187.1 | 15.5 | +9.0% | 7 | 3 | 4 | 205.7 | 161.7 | 186.9 | 212.5 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Harold Fannin Jr. | 180.4 | 172.7 | -7.7 | -4.3% | 8 | 5 | 3 | 191.3 | 147.4 | 172.6 | 198.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| George Kittle | 169.3 | 193.8 | 24.5 | +14.5% | 9 | 2 | 7 | 212.4 | 168.4 | 193.5 | 218.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Dalton Kincaid | 163.6 | 110.8 | -52.8 | -32.3% | 10 | 24 | -14 | 129.4 | 87.1 | 110.3 | 134.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Travis Kelce | 171.4 | 152.5 | -18.9 | -11.0% | 11 | 11 | 0 | 171.1 | 127.7 | 152.1 | 177.4 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Jake Ferguson | 159.8 | 139.3 | -20.5 | -12.8% | 12 | 15 | -3 | 157.9 | 114.9 | 138.8 | 164.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior reception volume. |
| Isaiah Likely | 157.3 | 157.3 | 0.0 | +0.0% | 13 | 9 | 4 | — | 132.8 | 157.0 | 182.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Dallas Goedert | 136.0 | 146.2 | 10.2 | +7.5% | 14 | 13 | 1 | 164.8 | 121.8 | 146.0 | 170.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, recent role-change signal. |
| Mark Andrews | 162.5 | 106.2 | -56.3 | -34.7% | 15 | 29 | -14 | 124.7 | 82.4 | 105.7 | 129.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Oronde Gadsden II | 141.8 | 127.6 | -14.2 | -10.0% | 16 | 19 | -3 | 146.2 | 103.5 | 127.1 | 152.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Hunter Henry | 153.5 | 138.7 | -14.8 | -9.6% | 17 | 16 | 1 | 157.3 | 114.0 | 138.5 | 163.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Brenton Strange | 161.0 | 122.7 | -38.3 | -23.8% | 18 | 21 | -3 | 141.3 | 98.2 | 122.2 | 147.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| T.J. Hockenson | 155.0 | 109.5 | -45.5 | -29.4% | 19 | 28 | -9 | 128.0 | 85.7 | 108.7 | 134.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Kenyon Sadiq | 100.2 | 100.2 | 0.0 | +0.0% | 20 | 33 | -13 | — | 77.5 | 99.7 | 123.9 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| AJ Barner | 142.4 | 109.7 | -32.7 | -23.0% | 21 | 27 | -6 | 128.3 | 85.6 | 109.3 | 134.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Juwan Johnson | 140.9 | 146.5 | 5.6 | +4.0% | 22 | 12 | 10 | 165.1 | 121.8 | 146.2 | 171.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Dalton Schultz | 150.9 | 154.1 | 3.2 | +2.1% | 23 | 10 | 13 | 172.7 | 129.3 | 153.6 | 179.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Chig Okonkwo | 144.1 | 144.1 | 0.0 | +0.0% | 24 | 14 | 10 | — | 120.1 | 143.7 | 168.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |

## Largest model-market disagreements

These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 67 | -42 | 174.8 | 63.8 | -111.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 125.3 | -83.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 16 | 43 | -27 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 52 | -24 | 147.9 | 99.8 | -48.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Caleb Williams | QB | 7 | 25 | -18 | 355.3 | 219.0 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| DeVonta Smith | WR | 14 | 32 | -18 | 229.2 | 166.7 | -62.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 164.7 | -59.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.1 | -88.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Courtland Sutton | WR | 35 | 18 | 17 | 174.3 | 188.0 | 13.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jaxson Dart | QB | 10 | 27 | -17 | 340.5 | 209.2 | -131.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Joe Burrow | QB | 4 | 20 | -16 | 372.1 | 235.8 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Kyle Monangai | RB | 34 | 50 | -16 | 154.6 | 102.9 | -51.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Michael Wilson | WR | 36 | 21 | 15 | 166.0 | 179.7 | 13.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Brian Thomas Jr. | WR | 32 | 47 | -15 | 195.4 | 139.7 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | WR | 25 | 39 | -14 | 213.8 | 158.4 | -55.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mark Andrews | TE | 15 | 29 | -14 | 162.5 | 106.2 | -56.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 182.7 | -67.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 10 | 24 | -14 | 163.6 | 110.8 | -52.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Parker Washington | WR | 31 | 44 | -13 | 212.4 | 153.2 | -59.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Schultz | TE | 23 | 10 | 13 | 150.9 | 154.1 | 3.2 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Brock Purdy | QB | 15 | 3 | 12 | 363.2 | 323.5 | -39.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Marvin Harrison Jr. | WR | 34 | 45 | -11 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Lamar Jackson | QB | 2 | 13 | -11 | 380.0 | 255.2 | -124.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior passing-TD production. |
| Tee Higgins | WR | 15 | 25 | -10 | 224.4 | 175.4 | -49.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | WR | 17 | 27 | -10 | 223.0 | 171.8 | -51.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| C.J. Stroud | QB | 24 | 34 | -10 | 291.8 | 181.0 | -110.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Juwan Johnson | TE | 22 | 12 | 10 | 140.9 | 146.5 | 5.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Saquon Barkley | RB | 6 | 15 | -9 | 246.7 | 199.8 | -46.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| T.J. Hockenson | TE | 19 | 28 | -9 | 155.0 | 109.5 | -45.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Omarion Hampton | RB | 9 | 17 | -8 | 242.9 | 196.8 | -46.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |

## Diagnostic sleeper candidates outside market cutoffs

These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jimmy Garoppolo | QB | 192 | 55 | 137 | 12.3 | 36.7 | 24.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Nick Mullens | QB | 132 | 57 | 75 | 12.0 | 29.3 | 17.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Josh Johnson | QB | 77 | 46 | 31 | 11.3 | 89.0 | 77.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Jacoby Brissett | QB | 36 | 23 | 13 | 190.0 | 229.3 | 39.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior passing-TD production, recent opportunity-based expected production. |
| J.J. McCarthy | QB | 26 | 24 | 2 | 13.6 | 225.5 | 211.9 | Diagnostic model | FIE diagnostic is higher; main model signals: pfr times sacked, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Zavier Scott | RB | 404 | 86 | 318 | 5.6 | 36.1 | 30.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Elijah Mitchell | RB | 402 | 115 | 287 | 9.3 | 5.1 | -4.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Jacardia Wright | RB | 362 | 92 | 270 | 4.3 | 29.9 | 25.6 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, prior receiving-yard production. |
| Kalel Mullings | RB | 394 | 135 | 259 | 5.6 | -20.3 | -25.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Hunter Luepke | RB | 338 | 100 | 238 | 9.0 | 21.3 | 12.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Cam Akers | RB | 312 | 122 | 190 | 5.1 | 2.9 | -2.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Craig Reynolds | RB | 297 | 133 | 164 | 4.4 | -20.1 | -24.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| James Conner | RB | 68 | 39 | 29 | 57.2 | 134.9 | 77.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Audric Estimé | RB | 71 | 43 | 28 | 22.6 | 123.2 | 100.6 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, prior-season fantasy production, prior reception volume. |
| Kimani Vidal | RB | 72 | 45 | 27 | 60.0 | 114.4 | 54.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior rushing-yard production, recent opportunity-based expected production, prior-season fantasy production. |
| Allen Lazard | WR | 723 | 158 | 565 | 6.4 | 31.9 | 25.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Bo Melton | WR | 724 | 179 | 545 | 9.8 | 23.1 | 13.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Curtis Samuel | WR | 694 | 154 | 540 | 5.3 | 37.0 | 31.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jalen Brooks | WR | 704 | 169 | 535 | 6.5 | 27.4 | 20.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tai Felton | WR | 711 | 199 | 512 | 29.2 | 5.4 | -23.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Xavier Restrepo | WR | 622 | 125 | 497 | 4.8 | 57.0 | 52.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cedric Tillman | WR | 589 | 113 | 476 | 6.6 | 61.7 | 55.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Ben Skowronek | WR | 591 | 188 | 403 | 0.6 | 12.5 | 11.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cody White | WR | 571 | 178 | 393 | 8.5 | 23.1 | 14.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tyrell Shavers | WR | 516 | 129 | 387 | 4.0 | 54.5 | 50.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Brock Wright | TE | 344 | 42 | 302 | 27.3 | 65.0 | 37.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, number of receiving competitors, recent role-change signal. |
| Josh Whyle | TE | 355 | 66 | 289 | 13.8 | 36.8 | 23.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, number of receiving competitors, prior receiving-yard production. |
| Grant Calcaterra | TE | 339 | 59 | 280 | 25.6 | 43.3 | 17.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, number of receiving competitors. |
| Adam Trautman | TE | 331 | 56 | 275 | 27.8 | 44.5 | 16.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Cameron Latu | TE | 310 | 111 | 199 | 4.0 | 4.7 | 0.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Diagnostic fades / market-higher disagreements

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 25 | 67 | -42 | 174.8 | 63.8 | -111.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 23 | 58 | -35 | 209.0 | 125.3 | -83.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 16 | 43 | -27 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 28 | 52 | -24 | 147.9 | 99.8 | -48.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Caleb Williams | QB | 7 | 25 | -18 | 355.3 | 219.0 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| DeVonta Smith | WR | 14 | 32 | -18 | 229.2 | 166.7 | -62.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jaxson Dart | QB | 10 | 27 | -17 | 340.5 | 209.2 | -131.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.1 | -88.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Emeka Egbuka | WR | 18 | 35 | -17 | 224.0 | 164.7 | -59.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Joe Burrow | QB | 4 | 20 | -16 | 372.1 | 235.8 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Kyle Monangai | RB | 34 | 50 | -16 | 154.6 | 102.9 | -51.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Brian Thomas Jr. | WR | 32 | 47 | -15 | 195.4 | 139.7 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Justin Jefferson | WR | 6 | 20 | -14 | 250.4 | 182.7 | -67.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Mark Andrews | TE | 15 | 29 | -14 | 162.5 | 106.2 | -56.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Terry McLaurin | WR | 25 | 39 | -14 | 213.8 | 158.4 | -55.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 10 | 24 | -14 | 163.6 | 110.8 | -52.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Parker Washington | WR | 31 | 44 | -13 | 212.4 | 153.2 | -59.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Lamar Jackson | QB | 2 | 13 | -11 | 380.0 | 255.2 | -124.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior passing-TD production. |
| Marvin Harrison Jr. | WR | 34 | 45 | -11 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| C.J. Stroud | QB | 24 | 34 | -10 | 291.8 | 181.0 | -110.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |

## Diagnostic market-anchor audit

Production projections still require exact replay of every relevant nonzero scoring component. Diagnostics are different: FIE builds a player-allocation signal from the league-scoring components its shadow model supports, then recenters that signal to Sleeper **total** points within the eligible position cohort. Sleeper raw-stat component availability is not a diagnostic gate.

| Pos | Comparable players | Market-anchored partials | Mean FIE scoring coverage | Unsupported FIE auxiliary keys observed |
|---|---:|---:|---:|---|
| QB | 51 | 0 | 100.0% | none |
| RB | 87 | 0 | 100.0% | none |
| WR | 128 | 0 | 100.0% | none |
| TE | 78 | 0 | 100.0% | none |

## Interpretation rules

- The FIE diagnostic view is centered within each eligible position cohort, while ineligible rows remain at Sleeper. Therefore the full-position average diagnostic projection equals Sleeper by construction.
- A diagnostic deviation answers **where FIE allocates value differently**, not which model is better.
- Production eligibility is separate. Only positions in the validated production model registry may replace market/fallback values in runtime consumers.
- Missing profiles and team changes remain hard diagnostic guardrails. Exact scoring replay remains mandatory for production projections.
- Diagnostics do not require Sleeper raw-stat components. FIE supplies the allocation signal; Sleeper supplies the total position-level market anchor. Unsupported auxiliary FIE outcomes are disclosed and excluded from that diagnostic signal.
- P10/P50/P90 retain empirically calibrated historical OOS spread and are recentered on the diagnostic mean.
- M7/M8 diagnostic feature evidence can explain football mechanisms but does not stack onto projections unless its own sequential activation gate validates.
- Return production affects fantasy values only when the league scores it and the corresponding M9 return target independently validates.