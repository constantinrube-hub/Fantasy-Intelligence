# Tranche 3C — C10-007 Canonical Player Identity

Validated preflight: `23063ab350ee82ce04272933060ce1ac4551fbe9`, run `33777550987`, artifact `9902218284`.

## Problem corrected

The browser had multiple identity owners. Core omitted `sleeper_id`, current research preferred it, current storage had its own precedence, Value Finder could fall back to normalized names, and specialist current joins used local maps. That allowed one source row to resolve differently depending on the consumer.

## Canonical owner

`FIECore.PlayerIdentity` now owns browser player/entity identity.

### Compatibility ID

`PlayerIdentity.id(subject)` preserves stable browser IDs and may synthesize `synthetic:<position>:<team>:<name>` only when no stable ID exists. This is retained for non-governed lineup/bookkeeping compatibility.

### Governed ID

`PlayerIdentity.governedId(subject)` never synthesizes identity. It accepts stable runtime aliases and explicit crosswalk identifiers only.

Recognized runtime aliases:

- `sleeperId`
- `sleeper_id`
- `player_id`
- `playerId`
- `id`

Governed crosswalk identifiers:

- `canonical_player_id`
- `internal_id`
- `gsis_id`
- `pfr_id`
- `fantasypros_id`

Sleeper identity wins over legacy aliases when both are present.

## Resolution contract

`PlayerIdentity.resolve()` returns exactly one of:

- `resolved`
- `unavailable`
- `ambiguous`

Conflicting stable aliases resolve to `ambiguous`. A duplicate display-name collision resolves to `ambiguous`, but names are not used to pick a player. A single display-name match without stable identity remains `unavailable`.

D/ST receives a team-defense entity alias so a governed `DST:<TEAM>` canonical research row can resolve to the live Sleeper D/ST entity without generic display-name matching.

## Governed consumers

### Current player features

Research rows resolve against the live player pool through `FIECore.PlayerIdentity`. Rows with unavailable or ambiguous identity do not attach. Multiple research rows resolving to the same live player also fail closed instead of last-write-wins.

Current feature lineage now records:

- `identityResolved`
- `identityStatus`
- `identitySource`
- `canonicalId`

Research influence additionally requires `identityResolved === true` along with the existing leakage, player activation and M6 governance gates.

### Current snapshot store

Browser storage IDs use `PlayerIdentity.governedId()` first. The Python shared-current storage helper mirrors the governed namespace rules and never accepts display names or synthetic name-position identity.

### Value Finder

The governed M5 current join uses `PlayerIdentity.resolve()`. The normalized-name fallback is removed from the research/current join. Human-facing display/search helpers remain outside the governed join contract.

### D/ST and kicker

Current research rows are indexed/resolved through `PlayerIdentity`; D/ST team-entity resolution is handled by Core rather than a separate local team/name identity owner.

## Permanent tests

The release gate now requires:

1. canonical identity ownership/source contract;
2. offense fixture;
3. IDP fixture;
4. D/ST entity fixture;
5. kicker fixture;
6. explicit canonical/GSIS crosswalk fixtures;
7. conflicting-alias ambiguity;
8. duplicate-name ambiguity without guessing;
9. display-name-only unavailable state;
10. canonical-only current-feature attachment;
11. duplicate governed current rows fail closed;
12. governed current-snapshot storage IDs.

## Preserved boundaries

No change to replacement/scarcity/VOR economics, DataClient transport, league isolation, ADP/model separation, statistical thresholds or research promotion gates. C10-009 and C10-005 remain frozen.
