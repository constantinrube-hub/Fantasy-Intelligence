# Architecture

## Objective

Fantasy Intelligence Engine should have **one source of truth for every football concept and every runtime state transition**. Feature modules consume shared services rather than recreating scoring, eligibility, replacement, lineup or player-value logic.

## Runtime flow

```text
Sleeper / nflverse / public sources
              |
          DataClient
              |
      LeagueController + state
              |
 +------------+-------------+
 |            |             |
League     Position/     ScoringRule
Profile    Slot Registry Registry
 |            |             |
 +------------+-------------+
              |
    LeagueDemand / Replacement
              |
       Projection Distribution
              |
        League Value
              |
        LineupOptimizer
              |
         Roster Value
              |
        Draft Timing
              |
        DecisionService
       /       |       \
Draft      Value      Monte
Assistant  Finder     Carlo
```

## Canonical contracts

### Runtime contracts

Source: `config/contracts/runtime-contracts.json`

Generated outputs:

- `app/generated/runtime-contracts.js`
- `research/generated_runtime_contracts.py`

Never edit generated copies directly. Change the JSON source, then run:

```bash
python research/generate_runtime_contracts.py
```

### Core services

`app/core/core-services.js` owns:

- `PositionRegistry`
- `PlayerIdentity`
- `LineupOptimizer`
- `LeagueDemandService`
- `ReplacementService`
- `RosterValueService`
- `ContextFingerprint`
- `Diagnostics`

### Data access

`app/core/data-client.js` is the browser data gateway. New feature code should not call `fetch()` directly.

### Decision source

`app/core/decision-service.js` chooses the production valuation source.

- promoted V9 if governance explicitly allows it;
- governed V8.9 fallback otherwise.

Value Finder and Monte Carlo consume this gateway rather than choosing an independent model.

## League state

`app/runtime-foundation.js` owns the authoritative league-change lifecycle.

A league switch:

1. aborts the previous request scope;
2. increments the generation;
3. resets every league-scoped state slice;
4. loads critical Sleeper data;
5. commits only if generation/league ID are still current;
6. renders the core shell;
7. loads enrichment/research progressively.

Direct feature code must not create its own competing league-switch lifecycle.

## Research architecture

Research remains namespaced, while large current-season payloads are shared by content hash:

```text
data/research/leagues/<league_id>/
  profile.json
  milestone1.json
  ...
  milestone6.json
  current/milestone5_current.json   # lightweight league manifest
  governance/active_release.json

data/research/shared/current/
  player_base.<hash>.json
  scoring/<scoring_signature>.<hash>.json
```

`app/current-snapshot-store.js` hydrates the manifest + shared artifacts back into the unchanged logical M5 current contract. This keeps league scoring exact without repeating the invariant player payload for every league. `tools/build_dist.py` performs a second portfolio-wide runtime compaction so Cloudflare ships only rows needed by at least one managed league. See `CURRENT_SNAPSHOT_STORAGE.md`.

The profile uses a **structural-v2** fingerprint. Volatile Sleeper operational fields are retained for diagnostics but do not define model identity.

## Legacy shell

`index.html` still contains legacy-compatible V7/V8 logic. Consolidation modules are authoritative for the highest-risk shared contracts. New work must move logic outward into `app/` rather than add another version wrapper inside `index.html`.

The long-term direction is gradual extraction, not a blind rewrite.
