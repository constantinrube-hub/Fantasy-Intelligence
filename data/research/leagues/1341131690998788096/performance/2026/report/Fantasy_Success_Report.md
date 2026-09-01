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
| QB | Diagnostic model | 77 | 51 | 117.9 | 117.9 | -0.00 | 0.778 | 30.6 | 114.5 | 36.4% | 47 |
| RB | Diagnostic model | 135 | 87 | 84.6 | 84.6 | -0.00 | 0.868 | 9.5 | 53.4 | 42.2% | 70 |
| WR | Validated preseason model | 214 | 128 | 85.7 | 85.7 | 0.00 | 0.910 | 10.2 | 54.2 | 43.9% | 111 |
| TE | Validated preseason model | 123 | 78 | 61.2 | 61.2 | 0.00 | 0.911 | 3.6 | 38.1 | 46.3% | 61 |

## Position-level predictive evidence

### QB

**Preseason evidence:** Diagnostic model; mean historical improvement -0.9%; 95% CI -3.7% to +1.8%.

**M7 driver evidence:** recent QB rushing role (opportunity), recent QB rushing role (rushing_leverage), recent opportunity-based expected production (regression), recent QB pass-attempt role (opportunity), recent snap share (opportunity), recent actual-vs-expected production gap (regression)

**M8 matchup evidence:** public_pass_rush_matchup [diagnostic_only], public_defensive_synergy_matchup [diagnostic_only], public_coverage_matchup [diagnostic_only]

### RB

**Preseason evidence:** Diagnostic model; mean historical improvement +3.4%; 95% CI -3.1% to +8.1%.

**M7 driver evidence:** recent opportunity-based expected production (regression), recent offensive snap share (opportunity), recent carry share (opportunity), recent target share (receiving_role), recent target share (opportunity), backfield competition (competition)

**M8 matchup evidence:** insufficient

### WR

**Preseason evidence:** Validated preseason model; mean historical improvement +5.6%; 95% CI +2.8% to +9.9%.

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
| Josh Allen | 351.5 | 295.4 | -56.1 | -16.0% | 1 | 1 | 0 | — | 254.2 | 295.0 | 336.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-TD production, prior rushing-yard production. |
| Drake Maye | 309.8 | 264.5 | -45.3 | -14.6% | 2 | 4 | -2 | — | 224.7 | 263.7 | 305.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Lamar Jackson | 318.0 | 212.5 | -105.5 | -33.2% | 3 | 13 | -10 | — | 172.0 | 212.4 | 252.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior rushing-yard production. |
| Joe Burrow | 296.1 | 181.4 | -114.7 | -38.7% | 4 | 26 | -22 | — | 141.4 | 180.8 | 222.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Jayden Daniels | 299.7 | 219.2 | -80.5 | -26.9% | 5 | 11 | -6 | — | 179.0 | 218.6 | 259.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior-season fantasy production, recent QB rushing role. |
| Caleb Williams | 289.3 | 184.5 | -104.9 | -36.2% | 6 | 22 | -16 | — | 144.4 | 184.2 | 224.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Jalen Hurts | 302.5 | 234.2 | -68.3 | -22.6% | 7 | 9 | -2 | — | 194.2 | 233.9 | 274.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, prior rushing-TD production. |
| Justin Herbert | 285.5 | 203.9 | -81.5 | -28.6% | 8 | 15 | -7 | — | 163.6 | 203.4 | 244.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Jaxson Dart | 284.5 | 186.8 | -97.7 | -34.3% | 9 | 21 | -12 | — | 146.7 | 186.5 | 227.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Bo Nix | 283.7 | 200.4 | -83.3 | -29.4% | 10 | 18 | -8 | — | 160.5 | 200.1 | 241.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, recent opportunity-based expected production. |
| Patrick Mahomes | 274.7 | 253.1 | -21.6 | -7.9% | 11 | 7 | 4 | — | 213.5 | 252.6 | 293.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| Trevor Lawrence | 291.4 | 229.8 | -61.7 | -21.2% | 12 | 10 | 2 | — | 189.0 | 228.8 | 271.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, recent opportunity-based expected production. |
| Dak Prescott | 290.9 | 235.7 | -55.2 | -19.0% | 13 | 8 | 5 | — | 195.5 | 235.2 | 276.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, pfr times sacked, recent goal-line carry share. |
| Brock Purdy | 290.2 | 257.2 | -33.0 | -11.4% | 14 | 6 | 8 | — | 216.8 | 257.0 | 297.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, prior passing-TD production. |
| Fernando Mendoza | 201.2 | 201.2 | 0.0 | +0.0% | 15 | 17 | -2 | — | 163.3 | 200.3 | 239.4 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Baker Mayfield | 261.9 | 189.3 | -72.6 | -27.7% | 16 | 20 | -4 | — | 149.8 | 188.5 | 230.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, recent role-change signal. |
| Matthew Stafford | 280.2 | 280.2 | 0.0 | +0.0% | 17 | 2 | 15 | — | 240.4 | 279.8 | 320.4 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jordan Love | 268.5 | 168.9 | -99.6 | -37.1% | 18 | 27 | -9 | — | 129.1 | 168.8 | 209.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent actual-vs-expected production gap, pfr times sacked. |
| Jared Goff | 273.5 | 182.5 | -90.9 | -33.3% | 19 | 24 | -5 | — | 142.6 | 182.1 | 222.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, prior rushing-yard production. |
| C.J. Stroud | 235.8 | 146.0 | -89.8 | -38.1% | 20 | 34 | -14 | — | 107.1 | 145.0 | 185.4 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Cam Ward | 214.8 | 114.8 | -100.0 | -46.6% | 21 | 40 | -19 | — | 77.2 | 114.1 | 153.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Tyler Shough | 258.9 | 215.5 | -43.5 | -16.8% | 22 | 12 | 10 | — | 175.7 | 215.5 | 254.9 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, pfr times sacked, recent actual-vs-expected production gap. |
| Kyler Murray | 273.1 | 273.1 | 0.0 | +0.0% | 23 | 3 | 20 | — | 234.1 | 272.3 | 313.1 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Sam Darnold | 250.7 | 153.2 | -97.5 | -38.9% | 24 | 30 | -6 | — | 113.9 | 152.9 | 192.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, pfr times sacked, prior-season fantasy production. |

### RB Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Jahmyr Gibbs | 331.4 | 268.2 | -63.2 | -19.1% | 1 | 3 | -2 | — | 236.1 | 267.7 | 300.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Bijan Robinson | 324.9 | 286.5 | -38.4 | -11.8% | 2 | 2 | 0 | — | 254.2 | 286.1 | 319.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior rushing-yard production. |
| Ashton Jeanty | 233.9 | 206.2 | -27.7 | -11.9% | 3 | 12 | -9 | — | 174.7 | 206.2 | 237.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Jonathan Taylor | 272.3 | 264.9 | -7.4 | -2.7% | 4 | 4 | 0 | — | 233.3 | 264.8 | 295.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| De'Von Achane | 257.4 | 264.6 | 7.2 | +2.8% | 5 | 5 | 0 | — | 232.5 | 264.5 | 296.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Jeremiyah Love | 211.8 | 211.8 | 0.0 | +0.0% | 6 | 9 | -3 | — | 181.2 | 211.3 | 242.8 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Omarion Hampton | 242.9 | 196.9 | -46.0 | -18.9% | 7 | 17 | -10 | — | 165.9 | 196.8 | 228.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| James Cook | 260.8 | 237.3 | -23.5 | -9.0% | 8 | 7 | 1 | — | 205.7 | 237.1 | 269.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Christian McCaffrey | 291.0 | 308.3 | 17.3 | +5.9% | 9 | 1 | 8 | — | 276.5 | 307.9 | 340.2 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior reception volume, recent opportunity-based expected production. |
| Chase Brown | 255.2 | 228.5 | -26.7 | -10.5% | 10 | 8 | 2 | — | 197.0 | 228.3 | 259.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior reception volume. |
| Kenneth Walker III | 244.0 | 244.0 | 0.0 | +0.0% | 11 | 6 | 5 | — | 212.3 | 243.7 | 275.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Saquon Barkley | 246.7 | 199.7 | -47.0 | -19.1% | 12 | 15 | -3 | — | 168.0 | 199.8 | 231.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| TreVeyon Henderson | 171.0 | 156.7 | -14.3 | -8.4% | 13 | 28 | -15 | — | 126.7 | 155.9 | 187.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Breece Hall | 211.0 | 169.4 | -41.6 | -19.7% | 14 | 24 | -10 | — | 138.0 | 169.1 | 200.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Quinshon Judkins | 196.0 | 167.8 | -28.2 | -14.4% | 15 | 25 | -10 | — | 137.5 | 167.3 | 198.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Kyren Williams | 208.0 | 208.0 | 0.0 | +0.0% | 16 | 10 | 6 | — | 177.5 | 207.7 | 238.9 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Bucky Irving | 197.3 | 178.9 | -18.4 | -9.3% | 17 | 21 | -4 | — | 148.4 | 178.8 | 210.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Cam Skattebo | 201.2 | 199.7 | -1.5 | -0.8% | 18 | 16 | 2 | — | 168.9 | 199.1 | 231.1 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Derrick Henry | 246.9 | 202.0 | -44.9 | -18.2% | 19 | 14 | 5 | — | 170.6 | 202.0 | 233.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Javonte Williams | 212.0 | 183.3 | -28.7 | -13.5% | 20 | 19 | 1 | — | 152.8 | 182.9 | 214.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Jadarian Price | 170.0 | 170.0 | 0.0 | +0.0% | 21 | 23 | -2 | — | 140.6 | 169.4 | 199.9 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Josh Jacobs | 87.2 | 191.5 | 104.3 | +119.6% | 22 | 18 | 4 | — | 165.9 | 190.5 | 218.6 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Travis Etienne | 207.7 | 207.7 | 0.0 | +0.0% | 23 | 11 | 12 | — | 176.9 | 207.2 | 238.6 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Bhayshul Tuten | 174.8 | 63.9 | -110.9 | -63.5% | 24 | 67 | -43 | — | 34.0 | 63.6 | 93.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| D'Andre Swift | 208.0 | 180.6 | -27.4 | -13.2% | 25 | 20 | 5 | — | 150.1 | 180.4 | 212.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| David Montgomery | 206.1 | 206.1 | 0.0 | +0.0% | 26 | 13 | 13 | — | 175.5 | 205.6 | 237.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| RJ Harvey | 144.1 | 152.6 | 8.5 | +5.9% | 27 | 31 | -4 | — | 123.7 | 152.0 | 182.6 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Kyle Monangai | 154.6 | 103.2 | -51.4 | -33.2% | 28 | 50 | -22 | — | 74.5 | 102.6 | 132.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Jaylen Warren | 170.6 | 177.7 | 7.1 | +4.2% | 29 | 22 | 7 | — | 148.0 | 177.2 | 207.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Chuba Hubbard | 147.9 | 99.9 | -48.0 | -32.5% | 30 | 52 | -22 | — | 71.4 | 99.0 | 129.4 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Blake Corum | 135.3 | 135.3 | 0.0 | +0.0% | 31 | 38 | -7 | — | 106.3 | 134.8 | 164.2 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Rico Dowdle | 161.1 | 161.1 | 0.0 | +0.0% | 32 | 27 | 5 | — | 131.9 | 160.5 | 191.5 | Diagnostic model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jonathon Brooks | 154.9 | 154.9 | 0.0 | +0.0% | 33 | 29 | 4 | — | 126.0 | 154.4 | 184.5 | Diagnostic model | No diagnostic deviation: no usable prior-season FIE profile. |
| Rhamondre Stevenson | 169.0 | 151.4 | -17.6 | -10.4% | 34 | 33 | 1 | — | 121.6 | 150.8 | 181.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, prior receiving-yard production. |
| Jacory Croskey-Merritt | 127.9 | 95.8 | -32.1 | -25.1% | 35 | 55 | -20 | — | 67.9 | 95.0 | 124.3 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| J.K. Dobbins | 160.2 | 152.9 | -7.3 | -4.6% | 36 | 30 | 6 | — | 124.1 | 151.9 | 182.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior rushing-yard production, prior-season fantasy production, recent carry share. |

### WR Top 36

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Ja'Marr Chase | 311.1 | 271.8 | -39.3 | -12.6% | 1 | 3 | -2 | 285.8 | 239.8 | 271.5 | 303.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Puka Nacua | 312.5 | 312.5 | 0.0 | +0.0% | 2 | 1 | 1 | — | 280.3 | 312.2 | 344.9 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Jaxon Smith-Njigba | 284.6 | 295.4 | 10.8 | +3.8% | 3 | 2 | 1 | 309.5 | 263.5 | 295.2 | 327.9 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Amon-Ra St. Brown | 280.5 | 264.0 | -16.5 | -5.9% | 4 | 4 | 0 | 278.1 | 232.0 | 264.0 | 295.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Justin Jefferson | 250.4 | 182.5 | -67.9 | -27.1% | 5 | 20 | -15 | 196.6 | 151.9 | 182.2 | 213.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| CeeDee Lamb | 270.5 | 218.7 | -51.8 | -19.2% | 6 | 12 | -6 | 232.8 | 187.4 | 218.5 | 249.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Malik Nabers | 236.7 | 201.3 | -35.4 | -14.9% | 7 | 16 | -9 | 215.4 | 170.5 | 200.9 | 232.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Drake London | 250.2 | 228.0 | -22.2 | -8.9% | 8 | 7 | 1 | 242.1 | 196.5 | 227.6 | 259.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| George Pickens | 245.7 | 224.5 | -21.2 | -8.6% | 9 | 9 | 0 | 238.6 | 193.3 | 224.0 | 256.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tetairoa McMillan | 223.0 | 171.8 | -51.2 | -23.0% | 10 | 27 | -17 | 185.9 | 141.8 | 171.4 | 202.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | 224.0 | 164.3 | -59.7 | -26.7% | 11 | 35 | -24 | 178.4 | 134.4 | 163.4 | 194.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Nico Collins | 262.0 | 206.0 | -56.0 | -21.4% | 12 | 14 | -2 | 220.0 | 174.5 | 205.9 | 237.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chris Olave | 235.9 | 225.5 | -10.4 | -4.4% | 13 | 8 | 5 | 239.6 | 194.5 | 225.2 | 257.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Ladd McConkey | 228.2 | 153.3 | -74.9 | -32.8% | 14 | 43 | -29 | 167.4 | 123.2 | 152.7 | 183.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| A.J. Brown | 247.2 | 247.2 | 0.0 | +0.0% | 15 | 6 | 9 | — | 216.0 | 247.1 | 278.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Garrett Wilson | 224.9 | 201.5 | -23.4 | -10.4% | 16 | 15 | 1 | 215.6 | 170.4 | 201.1 | 232.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Rashee Rice | 229.3 | 250.7 | 21.4 | +9.3% | 17 | 5 | 12 | 264.7 | 218.4 | 250.7 | 282.3 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Carnell Tate | 177.3 | 177.3 | 0.0 | +0.0% | 18 | 23 | -5 | — | 147.7 | 176.7 | 208.2 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Zay Flowers | 228.2 | 212.7 | -15.5 | -6.8% | 19 | 13 | 6 | 226.7 | 180.8 | 212.7 | 244.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| DeVonta Smith | 229.2 | 166.6 | -62.6 | -27.3% | 20 | 32 | -12 | 180.6 | 136.9 | 165.8 | 197.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Luther Burden III | 209.0 | 125.8 | -83.2 | -39.8% | 21 | 57 | -36 | 139.8 | 96.6 | 125.3 | 155.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Rome Odunze | 207.9 | 166.1 | -41.8 | -20.1% | 22 | 33 | -11 | 180.1 | 136.1 | 165.4 | 196.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Tee Higgins | 224.4 | 175.6 | -48.8 | -21.8% | 23 | 24 | -1 | 189.6 | 145.6 | 175.3 | 206.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jaylen Waddle | 221.0 | 221.0 | 0.0 | +0.0% | 24 | 11 | 13 | — | 190.4 | 220.5 | 251.8 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Marvin Harrison Jr. | 186.2 | 151.6 | -34.6 | -18.6% | 25 | 45 | -20 | 165.6 | 122.3 | 151.1 | 181.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Brian Thomas Jr. | 195.4 | 139.6 | -55.8 | -28.5% | 26 | 47 | -21 | 153.7 | 110.4 | 138.8 | 169.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jameson Williams | 206.2 | 175.4 | -30.8 | -14.9% | 27 | 25 | 2 | 189.5 | 145.0 | 175.2 | 205.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jordyn Tyson | 111.0 | 111.0 | 0.0 | +0.0% | 28 | 64 | -36 | — | 83.2 | 110.3 | 139.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Makai Lemon | 168.5 | 168.5 | 0.0 | +0.0% | 29 | 31 | -2 | — | 139.0 | 167.9 | 198.7 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| DJ Moore | 179.0 | 179.0 | 0.0 | +0.0% | 30 | 22 | 8 | — | 149.2 | 178.4 | 209.3 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| KC Concepcion | 156.4 | 156.4 | 0.0 | +0.0% | 31 | 41 | -10 | — | 126.8 | 155.4 | 186.6 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Christian Watson | 207.6 | 174.6 | -33.0 | -15.9% | 32 | 26 | 6 | 188.7 | 144.0 | 174.2 | 205.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Terry McLaurin | 213.8 | 158.5 | -55.3 | -25.9% | 33 | 38 | -5 | 172.5 | 128.1 | 157.8 | 189.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Davante Adams | 192.5 | 192.5 | 0.0 | +0.0% | 34 | 17 | 17 | — | 162.3 | 192.0 | 223.5 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Michael Wilson | 166.0 | 179.7 | 13.7 | +8.3% | 35 | 21 | 14 | 193.8 | 148.7 | 179.2 | 210.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Parker Washington | 212.4 | 151.7 | -60.7 | -28.6% | 36 | 44 | -8 | 165.8 | 121.2 | 151.6 | 181.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |

### TE Top 24

| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Brock Bowers | 253.5 | 183.4 | -70.1 | -27.7% | 1 | 4 | -3 | 202.0 | 157.3 | 183.4 | 209.6 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Trey McBride | 234.9 | 234.8 | -0.1 | -0.0% | 2 | 1 | 1 | 253.4 | 209.2 | 234.7 | 261.0 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Colston Loveland | 215.4 | 127.2 | -88.2 | -41.0% | 3 | 20 | -17 | 145.8 | 102.8 | 127.1 | 151.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tyler Warren | 201.1 | 164.9 | -36.2 | -18.0% | 4 | 7 | -3 | 183.5 | 140.1 | 164.8 | 189.9 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Sam LaPorta | 196.5 | 158.1 | -38.4 | -19.5% | 5 | 8 | -3 | 176.7 | 133.3 | 157.9 | 183.1 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Harold Fannin Jr. | 180.4 | 172.7 | -7.7 | -4.2% | 6 | 5 | 1 | 191.3 | 147.4 | 172.6 | 198.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Tucker Kraft | 174.4 | 171.4 | -3.0 | -1.7% | 7 | 6 | 1 | 190.0 | 146.2 | 171.2 | 196.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Kyle Pitts | 171.6 | 187.1 | 15.5 | +9.0% | 8 | 3 | 5 | 205.7 | 161.8 | 186.9 | 212.5 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Dalton Kincaid | 163.6 | 110.9 | -52.7 | -32.2% | 9 | 24 | -15 | 129.5 | 87.2 | 110.4 | 134.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Kenyon Sadiq | 100.2 | 100.2 | 0.0 | +0.0% | 10 | 33 | -23 | — | 77.5 | 99.7 | 123.9 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Oronde Gadsden II | 141.8 | 127.6 | -14.2 | -10.0% | 11 | 19 | -8 | 146.2 | 103.6 | 127.1 | 152.3 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |
| Jake Ferguson | 159.8 | 139.2 | -20.6 | -12.9% | 12 | 15 | -3 | 157.8 | 114.8 | 138.7 | 164.4 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior reception volume. |
| Isaiah Likely | 157.3 | 157.3 | 0.0 | +0.0% | 13 | 9 | 4 | — | 132.8 | 157.0 | 182.1 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| George Kittle | 169.3 | 193.9 | 24.6 | +14.5% | 14 | 2 | 12 | 212.5 | 168.5 | 193.7 | 219.0 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Brenton Strange | 161.0 | 122.7 | -38.3 | -23.8% | 15 | 21 | -6 | 141.3 | 98.2 | 122.2 | 147.5 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Eli Stowers | 81.4 | 81.4 | 0.0 | +0.0% | 16 | 37 | -21 | — | 59.5 | 80.8 | 104.3 | Validated preseason model | No diagnostic deviation: no usable prior-season FIE profile. |
| Travis Kelce | 171.4 | 152.4 | -19.0 | -11.1% | 17 | 11 | 6 | 171.0 | 127.6 | 152.0 | 177.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| AJ Barner | 142.4 | 109.8 | -32.6 | -22.9% | 18 | 26 | -8 | 128.4 | 85.8 | 109.4 | 134.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Mark Andrews | 162.5 | 106.0 | -56.5 | -34.8% | 19 | 29 | -10 | 124.6 | 82.3 | 105.6 | 129.7 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior rushing-yard production. |
| Dallas Goedert | 136.0 | 146.3 | 10.3 | +7.6% | 20 | 13 | 7 | 164.9 | 121.9 | 146.1 | 170.8 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, recent role-change signal. |
| T.J. Hockenson | 155.0 | 109.4 | -45.6 | -29.4% | 21 | 28 | -7 | 128.0 | 85.6 | 108.7 | 134.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| Juwan Johnson | 140.9 | 146.5 | 5.6 | +4.0% | 22 | 12 | 10 | 165.1 | 121.8 | 146.2 | 171.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Chig Okonkwo | 144.1 | 144.1 | 0.0 | +0.0% | 23 | 14 | 9 | — | 120.2 | 143.7 | 168.6 | Validated preseason model | No diagnostic deviation: team transfer makes prior-team role profile non-portable. |
| Hunter Henry | 153.5 | 138.9 | -14.6 | -9.5% | 24 | 16 | 8 | 157.5 | 114.2 | 138.7 | 164.0 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, recent target share. |

## Largest model-market disagreements

These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 24 | 67 | -43 | 174.8 | 63.9 | -110.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 21 | 57 | -36 | 209.0 | 125.8 | -83.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 14 | 43 | -29 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 11 | 35 | -24 | 224.0 | 164.3 | -59.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Chuba Hubbard | RB | 30 | 52 | -22 | 147.9 | 99.9 | -48.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Kyle Monangai | RB | 28 | 50 | -22 | 154.6 | 103.2 | -51.4 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Joe Burrow | QB | 4 | 26 | -22 | 296.1 | 181.4 | -114.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Brian Thomas Jr. | WR | 26 | 47 | -21 | 195.4 | 139.6 | -55.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jacory Croskey-Merritt | RB | 35 | 55 | -20 | 127.9 | 95.8 | -32.1 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| Marvin Harrison Jr. | WR | 25 | 45 | -20 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Cam Ward | QB | 21 | 40 | -19 | 214.8 | 114.8 | -100.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.2 | -88.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tetairoa McMillan | WR | 10 | 27 | -17 | 223.0 | 171.8 | -51.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Caleb Williams | QB | 6 | 22 | -16 | 289.3 | 184.5 | -104.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 110.9 | -52.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| TreVeyon Henderson | RB | 13 | 28 | -15 | 171.0 | 156.7 | -14.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Justin Jefferson | WR | 5 | 20 | -15 | 250.4 | 182.5 | -67.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| C.J. Stroud | QB | 20 | 34 | -14 | 235.8 | 146.0 | -89.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Michael Wilson | WR | 35 | 21 | 14 | 166.0 | 179.7 | 13.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Rashee Rice | WR | 17 | 5 | 12 | 229.3 | 250.7 | 21.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jaxson Dart | QB | 9 | 21 | -12 | 284.5 | 186.8 | -97.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| George Kittle | TE | 14 | 2 | 12 | 169.3 | 193.9 | 24.6 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior-season fantasy production, prior receiving-yard production. |
| DeVonta Smith | WR | 20 | 32 | -12 | 229.2 | 166.6 | -62.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Rome Odunze | WR | 22 | 33 | -11 | 207.9 | 166.1 | -41.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Omarion Hampton | RB | 7 | 17 | -10 | 242.9 | 196.9 | -46.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Juwan Johnson | TE | 22 | 12 | 10 | 140.9 | 146.5 | 5.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Lamar Jackson | QB | 3 | 13 | -10 | 318.0 | 212.5 | -105.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent role-change signal, prior rushing-yard production. |
| Tyler Shough | QB | 22 | 12 | 10 | 258.9 | 215.5 | -43.5 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, pfr times sacked, recent actual-vs-expected production gap. |
| Quinshon Judkins | RB | 15 | 25 | -10 | 196.0 | 167.8 | -28.2 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| Breece Hall | RB | 14 | 24 | -10 | 211.0 | 169.4 | -41.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |

## Diagnostic sleeper candidates outside market cutoffs

These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Joe Flacco | QB | 189 | 39 | 150 | 28.7 | 124.7 | 95.9 | Diagnostic model | FIE diagnostic is higher; main model signals: pfr times sacked, recent pressure rate, recent opportunity-based expected production. |
| Jameis Winston | QB | 177 | 28 | 149 | 12.9 | 166.0 | 153.1 | Diagnostic model | FIE diagnostic is higher; main model signals: recent actual-vs-expected production gap, recent goal-line carry share, recent pressure rate. |
| Carson Wentz | QB | 156 | 19 | 137 | 12.4 | 196.0 | 183.5 | Diagnostic model | FIE diagnostic is higher; main model signals: recent goal-line carry share, pfr times sacked, prior-season fantasy production. |
| Davis Mills | QB | 174 | 38 | 136 | 12.0 | 126.3 | 114.3 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent pressure rate. |
| Joe Milton III | QB | 181 | 45 | 136 | 12.4 | 89.2 | 76.8 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent pressure rate. |
| Jawhar Jordan | RB | 267 | 47 | 220 | 27.0 | 110.0 | 83.0 | Diagnostic model | FIE diagnostic is higher; main model signals: prior rushing-yard production, recent carry share, recent opportunity-based expected production. |
| Devin Singletary | RB | 251 | 56 | 195 | 30.6 | 86.1 | 55.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, prior reception volume. |
| Chris Brooks | RB | 260 | 106 | 154 | 56.3 | 10.8 | -45.5 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Raheem Mostert | RB | 255 | 102 | 153 | 12.5 | 20.0 | 7.5 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent carry share, prior rushing-yard production. |
| George Holani | RB | 263 | 125 | 138 | 25.2 | -1.4 | -26.6 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent opportunity-based expected production. |
| Austin Ekeler | RB | 190 | 53 | 137 | 9.3 | 97.3 | 88.0 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, prior-season fantasy production, prior rushing-yard production. |
| Zavier Scott | RB | 181 | 86 | 95 | 5.6 | 36.3 | 30.7 | Diagnostic model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Will Shipley | RB | 198 | 103 | 95 | 33.8 | 17.1 | -16.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Audric Estimé | RB | 137 | 43 | 94 | 22.6 | 123.0 | 100.4 | Diagnostic model | FIE diagnostic is higher; main model signals: number of backfield competitors, prior-season fantasy production, prior reception volume. |
| Roschon Johnson | RB | 224 | 130 | 94 | 7.6 | -19.2 | -26.8 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| Darius Slayton | WR | 408 | 69 | 339 | 76.3 | 108.0 | 31.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent drop rate, prior receiving-yard production, recent target share. |
| Theo Wease Jr. | WR | 404 | 68 | 336 | 8.9 | 108.3 | 99.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| Mack Hollins | WR | 388 | 60 | 328 | 57.6 | 118.0 | 60.4 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| KaVontae Turpin | WR | 385 | 101 | 284 | 71.5 | 73.3 | 1.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, recent target share, prior receiving-yard production. |
| Josh Palmer | WR | 398 | 116 | 282 | 32.6 | 61.0 | 28.4 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Roman Wilson | WR | 397 | 127 | 270 | 26.8 | 56.6 | 29.8 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Isaiah Williams | WR | 405 | 137 | 268 | 31.3 | 49.8 | 18.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Tyrell Shavers | WR | 393 | 129 | 264 | 4.0 | 54.7 | 50.7 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jahdae Walker | WR | 393 | 135 | 258 | 25.9 | 50.4 | 24.5 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Jimmy Horn Jr. | WR | 378 | 146 | 232 | 30.2 | 41.4 | 11.2 | Validated preseason model | FIE diagnostic is higher; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Dawson Knox | TE | 165 | 30 | 135 | 76.4 | 104.3 | 27.9 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, recent role-change signal, recent opportunity-based expected production. |
| Brock Wright | TE | 153 | 42 | 111 | 27.3 | 64.9 | 37.6 | Validated preseason model | FIE diagnostic is higher; main model signals: prior receiving-yard production, number of receiving competitors, recent role-change signal. |
| Grant Calcaterra | TE | 123 | 59 | 64 | 25.6 | 43.2 | 17.6 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, number of receiving competitors. |
| Josh Oliver | TE | 113 | 50 | 63 | 31.4 | 53.9 | 22.5 | Validated preseason model | FIE diagnostic is higher; main model signals: recent role-change signal, prior receiving-yard production, number of receiving competitors. |
| Cameron Latu | TE | 170 | 111 | 59 | 4.0 | 4.7 | 0.7 | Validated preseason model | FIE diagnostic is higher; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |

## Diagnostic fades / market-higher disagreements

| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Bhayshul Tuten | RB | 24 | 67 | -43 | 174.8 | 63.9 | -110.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent opportunity-based expected production, recent carry share. |
| Luther Burden III | WR | 21 | 57 | -36 | 209.0 | 125.8 | -83.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, recent target share, prior-season fantasy production. |
| Ladd McConkey | WR | 14 | 43 | -29 | 228.2 | 153.3 | -74.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Emeka Egbuka | WR | 11 | 35 | -24 | 224.0 | 164.3 | -59.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Joe Burrow | QB | 4 | 26 | -22 | 296.1 | 181.4 | -114.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior passing-TD production, recent actual-vs-expected production gap. |
| Kyle Monangai | RB | 28 | 50 | -22 | 154.6 | 103.2 | -51.4 | Diagnostic model | FIE diagnostic is lower; main model signals: recent opportunity-based expected production, prior rushing-yard production, recent role-change signal. |
| Chuba Hubbard | RB | 30 | 52 | -22 | 147.9 | 99.9 | -48.0 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior reception volume, recent offensive snap share. |
| Brian Thomas Jr. | WR | 26 | 47 | -21 | 195.4 | 139.6 | -55.8 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Marvin Harrison Jr. | WR | 25 | 45 | -20 | 186.2 | 151.6 | -34.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Jacory Croskey-Merritt | RB | 35 | 55 | -20 | 127.9 | 95.8 | -32.1 | Diagnostic model | FIE diagnostic is lower; main model signals: recent carry share, prior rushing-yard production, prior reception volume. |
| Cam Ward | QB | 21 | 40 | -19 | 214.8 | 114.8 | -100.0 | Diagnostic model | FIE diagnostic is lower; main model signals: recent pressure rate, prior-season fantasy production, recent actual-vs-expected production gap. |
| Colston Loveland | TE | 3 | 20 | -17 | 215.4 | 127.2 | -88.2 | Validated preseason model | FIE diagnostic is lower; main model signals: recent target share, prior receiving-yard production, prior-season fantasy production. |
| Tetairoa McMillan | WR | 10 | 27 | -17 | 223.0 | 171.8 | -51.2 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |
| Caleb Williams | QB | 6 | 22 | -16 | 289.3 | 184.5 | -104.9 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent pressure rate, pfr times sacked. |
| Justin Jefferson | WR | 5 | 20 | -15 | 250.4 | 182.5 | -67.9 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, recent target share. |
| Dalton Kincaid | TE | 9 | 24 | -15 | 163.6 | 110.9 | -52.7 | Validated preseason model | FIE diagnostic is lower; main model signals: prior receiving-yard production, prior-season fantasy production, prior reception volume. |
| TreVeyon Henderson | RB | 13 | 28 | -15 | 171.0 | 156.7 | -14.3 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior rushing-yard production, recent carry share. |
| C.J. Stroud | QB | 20 | 34 | -14 | 235.8 | 146.0 | -89.8 | Diagnostic model | FIE diagnostic is lower; main model signals: recent goal-line carry share, recent pressure rate, recent role-change signal. |
| Jaxson Dart | QB | 9 | 21 | -12 | 284.5 | 186.8 | -97.7 | Diagnostic model | FIE diagnostic is lower; main model signals: prior-season fantasy production, recent goal-line carry share, prior rushing-yard production. |
| DeVonta Smith | WR | 20 | 32 | -12 | 229.2 | 166.6 | -62.6 | Validated preseason model | FIE diagnostic is lower; main model signals: prior-season fantasy production, prior receiving-yard production, prior reception volume. |

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