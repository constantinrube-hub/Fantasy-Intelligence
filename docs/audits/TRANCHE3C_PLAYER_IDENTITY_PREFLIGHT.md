# Combined Tranche 3B Final Sync + Tranche 3C Player Identity Preflight

Validated Tranche 3B target:

- commit `96a3f6200cdefd521b18265b705a10d2885bf896`
- workflow run `33645046578`
- target artifact `9852443209`
- release gate `DEPLOYABLE_SOURCE`
- final build-manifest SHA256 `c2a9a48e817e2955832f07b30a869dcfcd5eb0be0caf1dfb5ef659282fd75373`

## Combined transition

This package synchronizes the exact two build manifests emitted by the successful
Tranche 3B target run and then starts a characterization-only Tranche 3C /
C10-007 preflight.

No player-identity production behavior changes in this package.

## Formal Tranche 3B closure

The Tranche 3C workflow first re-runs the preserved 2A/2B/2C/3A contracts and the
Tranche 3B target contracts:

- scope-aware DataClient coalescing;
- no cross-scope abort propagation;
- ResearchReportService through `FIEDataClient.json`;
- persistent cache behavior;
- fast league switching;
- canonical release build.

It then requires:

- `STATUS: DEPLOYABLE_SOURCE`
- zero tracked/generated/runtime drift.

Only after `PASS Tranche 3B final generated tree fully synchronized` may the
workflow characterize Tranche 3C.

## Audited C10-007 gap

Runtime identity is currently fragmented:

- Core `playerId()` recognizes one alias set and can synthesize
  `syn:team:position:name`.
- Core `PlayerIdentity.byId()` uses a narrower alias set.
- current-player-features prefers `sleeper_id`.
- current-snapshot-store uses more than one local precedence.
- Value Finder can fall back from Sleeper ID to normalized display name.

That makes identity ownership non-canonical and creates collision/ambiguity risk
when research or cross-source archives expand.

## Frozen Tranche 3C target

The subsequent implementation must establish one canonical
`FIECore.PlayerIdentity` path with:

1. stable runtime aliases:
   `sleeperId`, `sleeper_id`, `player_id`, `playerId`, `id`;
2. governed crosswalk fields:
   Sleeper, GSIS, PFR, FantasyPros and internal ID;
3. explicit `resolved`, `unavailable`, and `ambiguous` outcomes;
4. deterministic ambiguity for duplicate-name collisions;
5. no silent synthetic name-position ID as governed research identity;
6. no display-name fallback for governed current-feature activation;
7. fail-closed research activation when mapping is incomplete;
8. canonical consumers in current-player-features, current-snapshot-store and
   Value Finder;
9. offense, IDP, D/ST and kicker fixtures;
10. a canonical-only current-feature fixture.

This does **not** mean all display-name helpers must disappear. Human-facing
search/display may retain name helpers; governed identity joins may not silently
promote them to canonical identity.

## Preserved boundaries

- ADP remains outside football/player-quality modeling.
- league-specific decisions remain independent.
- cross-league validation pooling remains disabled.
- statistical and research-promotion thresholds remain fail-closed.
- Tranche 3A economics remains unchanged.
- Tranche 3B transport remains unchanged.
- C10-009 evidence/uncertainty remains frozen.
- C10-005 research producer typing remains frozen.

## Preflight result expected

The current source should deliberately produce:

`KNOWN_GAP_REPRODUCED player identity is fragmented across stable IDs, synthetic IDs and display-name fallback`

The workflow then captures the exact identity-related source bytes and requires
no runtime/generated drift.
