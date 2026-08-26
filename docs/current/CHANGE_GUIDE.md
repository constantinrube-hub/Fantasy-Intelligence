# How to Change Fantasy Intelligence Safely

Use this document before adding or modifying a feature.

## Rule 1: identify the concept owner

Do not implement the same football concept in the feature module.

| Concept | Owner |
|---|---|
| Position aliases / slot eligibility | `config/contracts/runtime-contracts.json` |
| Scoring relevance | runtime contract + generated Python/JS |
| Player identity | `FIECore.PlayerIdentity` |
| League format | `FIELeagueProfileResolver` |
| League switching | `FIELeagueController` |
| Data requests | `FIEDataClient` |
| Draft sequence / 3RR | `FIEDraftSequence` |
| League demand / replacement | `FIECore.LeagueDemandService` / `ReplacementService` |
| Legal lineup | `FIECore.LineupOptimizer` |
| Roster marginal value | `FIECore.RosterValueService` |
| Production draft valuation source | `FIEDecisionService` |
| Current research features | `FIECurrentFeatures` |
| Production research activation | governance + model config |

## Rule 2: change source contracts, not generated files

If adding a roster slot or scoring family:

1. edit `config/contracts/runtime-contracts.json`;
2. run `python research/generate_runtime_contracts.py`;
3. run scoring/runtime integrity tests;
4. update documentation if semantics changed.

## Rule 3: never silently promote a candidate model

1. implement candidate logic;
2. create historical/forward decision validation;
3. generate model-config evidence;
4. promote only after the relevant domain gate passes;
5. keep fallback operational throughout.

## Rule 4: all new data requests use DataClient

Use:

```js
FIEDataClient.json(url, { sourceId: 'feature-name' })
```

Do not call raw `fetch()` from feature modules.

League-scoped requests automatically inherit the current abort scope.

## Rule 5: use canonical IDs

Never join players by display name in new code.

```js
const id = FIECore.PlayerIdentity.id(player);
```

## Rule 6: do not hand-code lineup eligibility

Use `PositionRegistry` and `LineupOptimizer`.

## Rule 7: no feature-specific replacement formula

Use `ReplacementService`.

## Rule 8: no new monkey-patch layer

Do not add:

```js
const OLD = window.someFunction;
window.someFunction = function(){ ... OLD(); ... };
```

Prefer:

- controller/service calls;
- explicit events/hooks;
- extending a canonical service.

Legacy wrappers still exist for compatibility, but 9.1 establishes a no-new-wrapper rule.

## Rule 9: add tests with the change

At minimum test:

- happy path;
- league-switch/stale state if asynchronous;
- one edge case;
- cross-position/slot behavior if football logic changed;
- fail-closed behavior if research/model logic changed.

## Rule 10: build output is generated

Never edit `dist/`.

After all source changes:

```bash
python research/generate_runtime_contracts.py
python research/generate_model_config.py
python research/generate_release_descriptor.py
python research/build_app_manifest.py
python tools/build_dist.py --mode personal
python research/release_gate.py
```

Then deploy the contents produced in `dist/` through the configured Cloudflare Pages build output.
