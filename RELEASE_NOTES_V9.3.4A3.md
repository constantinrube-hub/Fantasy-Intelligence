# V9.3.4A3

Measured hotfix based on V9.3.4A2 browser profiling.

- Core league shell already validated at 236 ms Genesis / 338 ms Chopped.
- Removes repeated O(N² log N)-style scoring work from the atomic publish.
- Caches universal starter-slot economics once per scoring cycle.
- Single-sort decision ranking and projection ranking.
- Shared weekly-context caches and position-level risk quantiles.
- Defers retrospective feature training out of score publication.
- Restores free-agent D/ST to A2 lean universes when the league starts DEF/DST.
- Repairs nflverse contracts 404 through server-side gzip decompression.
