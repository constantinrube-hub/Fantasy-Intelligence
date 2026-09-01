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
| TE | Validated preseason model | 123 | 78 | 84.9 | 84.9 | -0.00 | 0.914 | 6.7 | 53.0 | 45.5% | 63 |

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

**Preseason evidence:** Validated preseason model; mean historical improvement +5.9%; 95% CI +3.7% to +8.0%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent target share (opportunity), recent offensive snap share (opportunity), receiving competition (competition), number of receiving competitors (competition), recent red-zone target share (opportunity)

**M8 matchup evidence:** public_coverage_receiving_matchup [diagnostic_only], public_defensive_synergy_matchup [diagnostic_only], public_pressure_receiving_matchup [diagnostic_only]

## Requested Sleeper market universe

### QB Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Josh Allen | 415.5 | 341.6 | -73.9 | -17.8% | 1 | 1 | 0 | — | 291.7 | 341.1 | 391.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-TD production, recent goal-line carry share. |
| Drake Maye | 378.8 | 316.6 | -62.1 | -16.4% | 2 | 4 | -2 | — | 268.2 | 315.7 | 366.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Lamar Jackson | 380.0 | 255.2 | -124.8 | -32.8% | 3 | 13 | -10 | — | 206.1 | 255.1 | 304.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior passing-TD production. |
| Jayden Daniels | 350.7 | 258.7 | -92.0 | -26.2% | 4 | 12 | -8 | — | 210.1 | 257.9 | 307.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, recent QB rushing role, prior-season fantasy production. |
| Caleb Williams | 355.3 | 219.0 | -136.4 | -38.4% | 5 | 25 | -20 | — | 170.2 | 218.7 | 267.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Joe Burrow | 372.1 | 235.8 | -136.4 | -36.6% | 6 | 20 | -14 | — | 186.8 | 234.9 | 285.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Justin Herbert | 347.5 | 245.4 | -102.1 | -29.4% | 7 | 16 | -9 | — | 196.3 | 244.7 | 295.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Jalen Hurts | 352.5 | 283.3 | -69.3 | -19.7% | 8 | 7 | 1 | — | 235.0 | 282.8 | 331.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent goal-line carry share. |
| Jaxson Dart | 340.5 | 209.2 | -131.3 | -38.6% | 9 | 27 | -18 | — | 160.5 | 208.8 | 258.4 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Trevor Lawrence | 355.4 | 273.1 | -82.3 | -23.2% | 10 | 10 | 0 | — | 223.5 | 272.0 | 323.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Patrick Mahomes | 344.7 | 296.3 | -48.4 | -14.1% | 11 | 6 | 5 | — | 247.9 | 295.6 | 345.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, recent opportunity-based expected production. |
| Bo Nix | 347.7 | 237.9 | -109.8 | -31.6% | 12 | 19 | -7 | — | 189.4 | 237.6 | 287.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, recent opportunity-based expected production. |
| Brock Purdy | 363.2 | 323.5 | -39.7 | -10.9% | 13 | 3 | 10 | — | 274.2 | 323.3 | 372.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Dak Prescott | 365.9 | 281.7 | -84.2 | -23.0% | 14 | 8 | 6 | — | 232.7 | 281.3 | 331.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, recent goal-line carry share. |
| Jordan Love | 332.5 | 212.2 | -120.4 | -36.2% | 15 | 26 | -11 | — | 163.6 | 212.0 | 261.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Fernando Mendoza | 250.2 | 250.2 | 0.0 | +0.0% | 16 | 15 | 1 | — | 203.8 | 249.1 | 296.7 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jared Goff | 343.5 | 230.0 | -113.4 | -33.0% | 17 | 22 | -5 | — | 181.2 | 229.5 | 279.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent opportunity-based expected production. |
| Baker Mayfield | 326.9 | 233.8 | -93.0 | -28.5% | 18 | 21 | -3 | — | 185.6 | 232.9 | 283.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent role-change signal. |
| Cam Ward | 265.8 | 143.2 | -122.7 | -46.1% | 19 | 39 | -20 | — | 97.3 | 142.3 | 190.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Tyler Shough | 314.9 | 251.0 | -63.9 | -20.3% | 20 | 14 | 6 | — | 202.6 | 251.1 | 299.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, pfr times sacked, recent actual-vs-expected production gap. |
| Matthew Stafford | 280.2 | 280.2 | 0.0 | +0.0% | 21 | 9 | 12 | — | 233.3 | 279.5 | 328.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| C.J. Stroud | 291.8 | 181.0 | -110.8 | -38.0% | 22 | 34 | -12 | — | 133.5 | 179.7 | 228.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Kyler Murray | 327.1 | 327.1 | 0.0 | +0.0% | 23 | 2 | 21 | — | 279.8 | 326.1 | 375.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Sam Darnold | 314.7 | 197.2 | -117.5 | -37.3% | 24 | 28 | -4 | — | 149.3 | 197.0 | 245.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, pfr times sacked. |

### RB Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bijan Robinson | 324.9 | 286.1 | -38.8 | -11.9% | 1 | 2 | -1 | — | 253.8 | 285.8 | 318.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior rushing-yard production. |
| Jahmyr Gibbs | 331.4 | 267.9 | -63.5 | -19.2% | 2 | 3 | -1 | — | 235.8 | 267.4 | 300.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Ashton Jeanty | 233.9 | 206.3 | -27.6 | -11.8% | 3 | 12 | -9 | — | 174.8 | 206.3 | 237.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Jeremiyah Love | 211.8 | 211.8 | 0.0 | +0.0% | 4 | 9 | -5 | — | 181.2 | 211.3 | 242.8 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Omarion Hampton | 242.9 | 196.8 | -46.1 | -19.0% | 5 | 17 | -12 | — | 165.7 | 196.6 | 228.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| De'Von Achane | 257.4 | 264.8 | 7.4 | +2.9% | 6 | 4 | 2 | — | 232.6 | 264.7 | 296.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Jonathan Taylor | 272.3 | 264.6 | -7.7 | -2.8% | 7 | 5 | 2 | — | 233.0 | 264.5 | 295.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| James Cook | 260.8 | 237.4 | -23.4 | -9.0% | 8 | 7 | 1 | — | 205.8 | 237.2 | 269.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Christian McCaffrey | 291.0 | 308.0 | 17.0 | +5.8% | 9 | 1 | 8 | — | 276.2 | 307.7 | 339.9 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, recent opportunity-based expected production. |
| Chase Brown | 255.2 | 228.8 | -26.4 | -10.3% | 10 | 8 | 2 | — | 197.3 | 228.7 | 260.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Kenneth Walker III | 244.0 | 244.0 | 0.0 | +0.0% | 11 | 6 | 5 | — | 212.3 | 243.7 | 275.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Saquon Barkley | 246.7 | 199.8 | -46.9 | -19.0% | 12 | 15 | -3 | — | 168.1 | 199.8 | 231.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| TreVeyon Henderson | 171.0 | 156.8 | -14.2 | -8.3% | 13 | 28 | -15 | — | 126.8 | 156.0 | 188.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Breece Hall | 211.0 | 169.9 | -41.1 | -19.5% | 14 | 24 | -10 | — | 138.5 | 169.6 | 201.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Quinshon Judkins | 196.0 | 167.8 | -28.2 | -14.4% | 15 | 25 | -10 | — | 137.4 | 167.3 | 198.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Kyren Williams | 208.0 | 208.0 | 0.0 | +0.0% | 16 | 10 | 6 | — | 177.5 | 207.7 | 238.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Bucky Irving | 197.3 | 178.6 | -18.7 | -9.5% | 17 | 21 | -4 | — | 148.1 | 178.5 | 209.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Cam Skattebo | 201.2 | 199.5 | -1.7 | -0.8% | 18 | 16 | 2 | — | 168.7 | 198.9 | 231.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Derrick Henry | 246.9 | 202.1 | -44.8 | -18.1% | 19 | 14 | 5 | — | 170.8 | 202.2 | 233.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Javonte Williams | 212.0 | 183.3 | -28.7 | -13.5% | 20 | 19 | 1 | — | 152.7 | 182.9 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Jadarian Price | 170.0 | 170.0 | 0.0 | +0.0% | 21 | 23 | -2 | — | 140.6 | 169.4 | 199.9 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Travis Etienne | 207.7 | 207.7 | 0.0 | +0.0% | 22 | 11 | 11 | — | 176.9 | 207.2 | 238.7 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Josh Jacobs | 87.2 | 191.3 | 104.1 | +119.4% | 23 | 18 | 5 | — | 165.7 | 190.3 | 218.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Bhayshul Tuten | 174.8 | 63.8 | -111.0 | -63.5% | 24 | 67 | -43 | — | 34.0 | 63.5 | 93.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| D'Andre Swift | 208.0 | 180.6 | -27.4 | -13.2% | 25 | 20 | 5 | — | 150.1 | 180.4 | 212.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| David Montgomery | 206.1 | 206.1 | 0.0 | +0.0% | 26 | 13 | 13 | — | 175.5 | 205.6 | 237.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| RJ Harvey | 144.1 | 152.7 | 8.6 | +6.0% | 27 | 31 | -4 | — | 123.7 | 152.1 | 182.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Kyle Monangai | 154.6 | 102.9 | -51.7 | -33.5% | 28 | 50 | -22 | — | 74.1 | 102.3 | 132.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Jaylen Warren | 170.6 | 177.9 | 7.3 | +4.3% | 29 | 22 | 7 | — | 148.1 | 177.4 | 208.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Blake Corum | 135.3 | 135.3 | 0.0 | +0.0% | 30 | 38 | -8 | — | 106.3 | 134.8 | 164.3 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jonathon Brooks | 154.9 | 154.9 | 0.0 | +0.0% | 31 | 29 | 2 | — | 126.0 | 154.4 | 184.5 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Chuba Hubbard | 147.9 | 99.8 | -48.1 | -32.6% | 32 | 52 | -20 | — | 71.3 | 98.9 | 129.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Rico Dowdle | 161.1 | 161.1 | 0.0 | +0.0% | 33 | 27 | 6 | — | 131.9 | 160.5 | 191.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rhamondre Stevenson | 169.0 | 151.4 | -17.6 | -10.4% | 34 | 33 | 1 | — | 121.6 | 150.8 | 181.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior receiving-yard production. |
| Jacory Croskey-Merritt | 127.9 | 96.0 | -31.9 | -24.9% | 35 | 55 | -20 | — | 68.0 | 95.2 | 124.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| Jonah Coleman | 63.9 | 63.9 | 0.0 | +0.0% | 36 | 66 | -30 | — | 40.3 | 62.5 | 89.4 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |

### WR Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 311.1 | 271.8 | -39.3 | -12.6% | 1 | 3 | -2 | 285.8 | 239.8 | 271.5 | 303.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Puka Nacua | 312.5 | 312.5 | 0.0 | +0.0% | 2 | 1 | 1 | — | 280.3 | 312.2 | 344.9 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jaxon Smith-Njigba | 284.6 | 295.4 | 10.8 | +3.8% | 3 | 2 | 1 | 309.4 | 263.4 | 295.1 | 327.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Amon-Ra St. Brown | 280.5 | 264.0 | -16.5 | -5.9% | 4 | 4 | 0 | 278.0 | 232.0 | 264.1 | 295.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Justin Jefferson | 250.4 | 182.7 | -67.7 | -27.0% | 5 | 20 | -15 | 196.6 | 152.1 | 182.4 | 214.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Malik Nabers | 236.7 | 201.6 | -35.1 | -14.8% | 6 | 16 | -10 | 215.6 | 170.8 | 201.2 | 232.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| CeeDee Lamb | 270.5 | 218.8 | -51.7 | -19.1% | 7 | 12 | -5 | 232.7 | 187.4 | 218.6 | 250.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Drake London | 250.2 | 228.2 | -22.0 | -8.8% | 8 | 7 | 1 | 242.1 | 196.6 | 227.8 | 260.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | 223.0 | 171.8 | -51.2 | -22.9% | 9 | 27 | -18 | 185.8 | 141.8 | 171.4 | 202.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| George Pickens | 245.7 | 224.5 | -21.2 | -8.6% | 10 | 9 | 1 | 238.4 | 193.2 | 223.9 | 256.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | 224.0 | 164.7 | -59.3 | -26.5% | 11 | 35 | -24 | 178.6 | 134.7 | 163.8 | 195.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Nico Collins | 262.0 | 205.8 | -56.2 | -21.4% | 12 | 14 | -2 | 219.8 | 174.3 | 205.7 | 237.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chris Olave | 235.9 | 225.7 | -10.2 | -4.3% | 13 | 8 | 5 | 239.6 | 194.6 | 225.4 | 257.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Ladd McConkey | 228.2 | 153.3 | -74.9 | -32.8% | 14 | 43 | -29 | 167.3 | 123.2 | 152.7 | 183.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Garrett Wilson | 224.9 | 201.7 | -23.2 | -10.3% | 15 | 15 | 0 | 215.7 | 170.6 | 201.3 | 232.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Carnell Tate | 177.3 | 177.3 | 0.0 | +0.0% | 16 | 23 | -7 | — | 147.7 | 176.7 | 208.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| A.J. Brown | 247.2 | 247.2 | 0.0 | +0.0% | 17 | 6 | 11 | — | 216.0 | 247.1 | 278.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rashee Rice | 229.3 | 250.5 | 21.2 | +9.3% | 18 | 5 | 13 | 264.5 | 218.2 | 250.5 | 282.1 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Luther Burden III | 209.0 | 125.3 | -83.7 | -40.0% | 19 | 58 | -39 | 139.3 | 96.2 | 124.9 | 155.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Zay Flowers | 228.2 | 212.5 | -15.7 | -6.9% | 20 | 13 | 7 | 226.5 | 180.6 | 212.5 | 244.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Rome Odunze | 207.9 | 166.2 | -41.7 | -20.1% | 21 | 33 | -12 | 180.2 | 136.2 | 165.6 | 196.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DeVonta Smith | 229.2 | 166.7 | -62.5 | -27.3% | 22 | 32 | -10 | 180.7 | 137.0 | 165.9 | 197.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tee Higgins | 224.4 | 175.4 | -49.0 | -21.8% | 23 | 25 | -2 | 189.4 | 145.5 | 175.2 | 205.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Marvin Harrison Jr. | 186.2 | 151.6 | -34.6 | -18.6% | 24 | 45 | -21 | 165.6 | 122.3 | 151.1 | 182.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jordyn Tyson | 111.0 | 111.0 | 0.0 | +0.0% | 25 | 64 | -39 | — | 83.2 | 110.3 | 139.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jaylen Waddle | 221.0 | 221.0 | 0.0 | +0.0% | 26 | 11 | 15 | — | 190.4 | 220.5 | 251.8 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Brian Thomas Jr. | 195.4 | 139.7 | -55.7 | -28.5% | 27 | 47 | -20 | 153.7 | 110.5 | 139.0 | 170.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Makai Lemon | 168.5 | 168.5 | 0.0 | +0.0% | 28 | 31 | -3 | — | 138.9 | 167.9 | 198.7 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Jameson Williams | 206.2 | 175.4 | -30.8 | -14.9% | 29 | 24 | 5 | 189.4 | 145.0 | 175.3 | 205.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DJ Moore | 179.0 | 179.0 | 0.0 | +0.0% | 30 | 22 | 8 | — | 149.1 | 178.4 | 209.3 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| KC Concepcion | 156.4 | 156.4 | 0.0 | +0.0% | 31 | 41 | -10 | — | 126.7 | 155.4 | 186.7 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Christian Watson | 207.6 | 174.7 | -32.9 | -15.8% | 32 | 26 | 6 | 188.7 | 144.1 | 174.3 | 206.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | 213.8 | 158.4 | -55.4 | -25.9% | 33 | 39 | -6 | 172.3 | 128.0 | 157.7 | 189.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Parker Washington | 212.4 | 153.2 | -59.2 | -27.9% | 34 | 44 | -10 | 167.2 | 122.6 | 153.1 | 183.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Michael Wilson | 166.0 | 179.7 | 13.7 | +8.2% | 35 | 21 | 14 | 193.6 | 148.7 | 179.2 | 210.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Davante Adams | 192.5 | 192.5 | 0.0 | +0.0% | 36 | 17 | 19 | — | 162.3 | 192.0 | 223.5 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |

### TE Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Brock Bowers | 355.5 | 253.2 | -102.3 | -28.8% | 1 | 4 | -3 | 280.1 | 219.3 | 253.3 | 287.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Trey McBride | 330.9 | 329.9 | -1.0 | -0.3% | 2 | 1 | 1 | 356.8 | 296.7 | 329.8 | 363.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Colston Loveland | 299.4 | 177.3 | -122.1 | -40.8% | 3 | 19 | -16 | 204.1 | 145.6 | 177.2 | 209.5 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Tyler Warren | 284.1 | 228.7 | -55.4 | -19.5% | 4 | 7 | -3 | 255.5 | 196.2 | 228.6 | 261.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Harold Fannin Jr. | 254.4 | 243.5 | -10.9 | -4.3% | 5 | 5 | 0 | 270.3 | 210.5 | 243.5 | 276.6 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, recent opportunity-based expected production. |
| Tucker Kraft | 241.4 | 230.3 | -11.1 | -4.6% | 6 | 6 | 0 | 257.1 | 197.6 | 230.1 | 263.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Sam LaPorta | 272.5 | 218.4 | -54.1 | -19.8% | 7 | 9 | -2 | 245.3 | 186.1 | 218.2 | 250.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Kyle Pitts | 237.6 | 263.3 | 25.7 | +10.8% | 8 | 3 | 5 | 290.2 | 230.4 | 263.1 | 296.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Kenyon Sadiq | 140.2 | 140.2 | 0.0 | +0.0% | 9 | 32 | -23 | — | 110.6 | 139.7 | 171.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Dalton Kincaid | 229.6 | 148.4 | -81.2 | -35.4% | 10 | 28 | -18 | 175.2 | 117.5 | 147.8 | 179.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Oronde Gadsden II | 197.8 | 173.8 | -24.0 | -12.2% | 11 | 20 | -9 | 200.6 | 142.4 | 173.1 | 206.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Isaiah Likely | 219.3 | 219.3 | 0.0 | +0.0% | 12 | 8 | 4 | — | 187.4 | 219.0 | 251.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jake Ferguson | 229.8 | 195.6 | -34.2 | -14.9% | 13 | 15 | -2 | 222.5 | 163.7 | 195.1 | 228.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior reception volume. |
| George Kittle | 231.3 | 270.2 | 38.9 | +16.8% | 14 | 2 | 12 | 297.1 | 237.3 | 270.0 | 302.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Brenton Strange | 224.0 | 170.7 | -53.3 | -23.8% | 15 | 21 | -6 | 197.6 | 138.8 | 170.1 | 203.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Eli Stowers | 112.4 | 112.4 | 0.0 | +0.0% | 16 | 38 | -22 | — | 83.6 | 111.7 | 142.4 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Travis Kelce | 241.4 | 212.8 | -28.6 | -11.9% | 17 | 11 | 6 | 239.6 | 180.4 | 212.3 | 245.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| AJ Barner | 200.4 | 151.9 | -48.5 | -24.2% | 18 | 25 | -7 | 178.8 | 120.5 | 151.4 | 183.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Mark Andrews | 222.5 | 146.9 | -75.6 | -34.0% | 19 | 30 | -11 | 173.8 | 115.7 | 146.5 | 177.8 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior reception volume. |
| Dallas Goedert | 189.0 | 202.2 | 13.2 | +7.0% | 20 | 14 | 6 | 229.0 | 170.4 | 202.0 | 234.2 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, recent role-change signal. |
| Chig Okonkwo | 205.1 | 205.1 | 0.0 | +0.0% | 21 | 12 | 9 | — | 173.7 | 204.6 | 237.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Juwan Johnson | 196.9 | 204.1 | 7.2 | +3.6% | 22 | 13 | 9 | 230.9 | 171.9 | 203.7 | 236.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| T.J. Hockenson | 221.0 | 155.8 | -65.2 | -29.5% | 23 | 24 | -1 | 182.6 | 124.5 | 155.0 | 188.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior reception volume. |
| Gunnar Helm | 187.3 | 125.7 | -61.6 | -32.9% | 24 | 35 | -11 | 152.6 | 95.7 | 125.1 | 156.3 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, recent red-zone target share, recent opportunity-based expected production. |

## Largest model-market disagreements

These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 24 | 67 | -43 | 174.8 | 63.8 | -111.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 19 | 58 | -39 | 209.0 | 125.3 | -83.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 14 | 43 | -29 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 11 | 35 | -24 | 224.0 | 164.7 | -59.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Kyle Monangai | RB | 28 | 50 | -22 | 154.6 | 102.9 | -51.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Marvin Harrison Jr. | WR | 24 | 45 | -21 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Caleb Williams | QB | 5 | 25 | -20 | 355.3 | 219.0 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Cam Ward | QB | 19 | 39 | -20 | 265.8 | 143.2 | -122.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Jacory Croskey-Merritt | RB | 35 | 55 | -20 | 127.9 | 96.0 | -31.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| Chuba Hubbard | RB | 32 | 52 | -20 | 147.9 | 99.8 | -48.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Brian Thomas Jr. | WR | 27 | 47 | -20 | 195.4 | 139.7 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jaxson Dart | QB | 9 | 27 | -18 | 340.5 | 209.2 | -131.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Tetairoa McMillan | WR | 9 | 27 | -18 | 223.0 | 171.8 | -51.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Dalton Kincaid | TE | 10 | 28 | -18 | 229.6 | 148.4 | -81.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Colston Loveland | TE | 3 | 19 | -16 | 299.4 | 177.3 | -122.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Justin Jefferson | WR | 5 | 20 | -15 | 250.4 | 182.7 | -67.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| TreVeyon Henderson | RB | 13 | 28 | -15 | 171.0 | 156.8 | -14.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Michael Wilson | WR | 35 | 21 | 14 | 166.0 | 179.7 | 13.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Joe Burrow | QB | 6 | 20 | -14 | 372.1 | 235.8 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Rashee Rice | WR | 18 | 5 | 13 | 229.3 | 250.5 | 21.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| C.J. Stroud | QB | 22 | 34 | -12 | 291.8 | 181.0 | -110.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Omarion Hampton | RB | 5 | 17 | -12 | 242.9 | 196.8 | -46.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Rome Odunze | WR | 21 | 33 | -12 | 207.9 | 166.2 | -41.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| George Kittle | TE | 14 | 2 | 12 | 231.3 | 270.2 | 38.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Gunnar Helm | TE | 24 | 35 | -11 | 187.3 | 125.7 | -61.6 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, recent red-zone target share, recent opportunity-based expected production. |
| Jordan Love | QB | 15 | 26 | -11 | 332.5 | 212.2 | -120.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Mark Andrews | TE | 19 | 30 | -11 | 222.5 | 146.9 | -75.6 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior reception volume. |
| Lamar Jackson | QB | 3 | 13 | -10 | 380.0 | 255.2 | -124.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior passing-TD production. |
| Quinshon Judkins | RB | 15 | 25 | -10 | 196.0 | 167.8 | -28.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Malik Nabers | WR | 6 | 16 | -10 | 236.7 | 201.6 | -35.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |

## Diagnostic sleeper candidates outside market cutoffs

These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Josh Johnson | QB | 165 | 46 | 119 | 11.3 | 89.0 | 77.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Jimmy Garoppolo | QB | 114 | 55 | 59 | 12.3 | 36.7 | 24.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Clayton Tune | QB | 116 | 75 | 41 | 12.4 | 2.9 | -9.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent snap share. |
| Davis Mills | QB | 63 | 38 | 25 | 12.0 | 146.8 | 134.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior passing-TD production. |
| Spencer Rattler | QB | 60 | 36 | 24 | 12.7 | 155.5 | 142.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Jaleel McLaughlin | RB | 243 | 80 | 163 | 7.5 | 40.9 | 33.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Antonio Gibson | RB | 219 | 93 | 126 | 3.9 | 29.6 | 25.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, number of backfield competitors, prior reception volume. |
| Kareem Hunt | RB | 151 | 49 | 102 | 24.2 | 105.1 | 80.9 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, recent role-change signal, prior-season fantasy production. |
| Craig Reynolds | RB | 228 | 133 | 95 | 4.4 | -20.1 | -24.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Raheem Mostert | RB | 193 | 102 | 91 | 12.5 | 19.9 | 7.4 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Roschon Johnson | RB | 221 | 130 | 91 | 7.6 | -19.3 | -26.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Cam Akers | RB | 190 | 122 | 68 | 5.1 | 2.9 | -2.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Jacardia Wright | RB | 144 | 92 | 52 | 4.3 | 29.9 | 25.6 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, prior receiving-yard production. |
| Clyde Edwards-Helaire | RB | 126 | 88 | 38 | 0.8 | 32.4 | 31.6 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior receiving-yard production. |
| Ty Johnson | RB | 99 | 63 | 36 | 55.8 | 68.5 | 12.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior rushing-yard production, prior-season fantasy production, recent carry share. |
| Jahdae Walker | WR | 411 | 137 | 274 | 25.9 | 49.8 | 23.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Josh Palmer | WR | 390 | 117 | 273 | 32.6 | 60.8 | 28.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tyler Lockett | WR | 384 | 121 | 263 | 28.3 | 58.9 | 30.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Isaiah Williams | WR | 387 | 135 | 252 | 31.3 | 50.0 | 18.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Darius Cooper | WR | 380 | 147 | 233 | 6.7 | 39.7 | 33.0 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Curtis Samuel | WR | 385 | 154 | 231 | 5.3 | 37.0 | 31.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Ben Skowronek | WR | 413 | 188 | 225 | 0.6 | 12.5 | 11.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Cody White | WR | 364 | 178 | 186 | 8.5 | 23.1 | 14.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Gage Larvadain | WR | 369 | 183 | 186 | 1.9 | 17.5 | 15.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jake Bobo | WR | 358 | 191 | 167 | 4.2 | 10.1 | 5.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tanner Hudson | TE | 173 | 54 | 119 | 5.8 | 67.5 | 61.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, recent offensive snap share, prior receiving-yard production. |
| Shane Zylstra | TE | 136 | 48 | 88 | 2.3 | 80.3 | 78.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior reception volume, number of receiving competitors. |
| Adam Trautman | TE | 146 | 58 | 88 | 38.8 | 61.8 | 23.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Luke Farrell | TE | 169 | 95 | 74 | 10.1 | 29.1 | 19.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Jeremy Ruckert | TE | 131 | 69 | 62 | 9.3 | 49.2 | 39.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent role-change signal, prior-season fantasy production, prior receiving-yard production. |

## Diagnostic fades / market-higher disagreements

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 24 | 67 | -43 | 174.8 | 63.8 | -111.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 19 | 58 | -39 | 209.0 | 125.3 | -83.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 14 | 43 | -29 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 11 | 35 | -24 | 224.0 | 164.7 | -59.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Kyle Monangai | RB | 28 | 50 | -22 | 154.6 | 102.9 | -51.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Marvin Harrison Jr. | WR | 24 | 45 | -21 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Caleb Williams | QB | 5 | 25 | -20 | 355.3 | 219.0 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Cam Ward | QB | 19 | 39 | -20 | 265.8 | 143.2 | -122.7 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Brian Thomas Jr. | WR | 27 | 47 | -20 | 195.4 | 139.7 | -55.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Chuba Hubbard | RB | 32 | 52 | -20 | 147.9 | 99.8 | -48.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Jacory Croskey-Merritt | RB | 35 | 55 | -20 | 127.9 | 96.0 | -31.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| Jaxson Dart | QB | 9 | 27 | -18 | 340.5 | 209.2 | -131.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, prior-season fantasy production, prior rushing-yard production. |
| Dalton Kincaid | TE | 10 | 28 | -18 | 229.6 | 148.4 | -81.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Tetairoa McMillan | WR | 9 | 27 | -18 | 223.0 | 171.8 | -51.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Colston Loveland | TE | 3 | 19 | -16 | 299.4 | 177.3 | -122.1 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Justin Jefferson | WR | 5 | 20 | -15 | 250.4 | 182.7 | -67.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| TreVeyon Henderson | RB | 13 | 28 | -15 | 171.0 | 156.8 | -14.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Joe Burrow | QB | 6 | 20 | -14 | 372.1 | 235.8 | -136.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| C.J. Stroud | QB | 22 | 34 | -12 | 291.8 | 181.0 | -110.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Omarion Hampton | RB | 5 | 17 | -12 | 242.9 | 196.8 | -46.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |

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