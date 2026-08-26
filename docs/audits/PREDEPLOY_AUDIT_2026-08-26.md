# Fantasy Intelligence Engine
## Full Pre-Deployment Audit, Bug Register, Centralization Plan, and Codebase Excellence Standard
### Audit date: 2026-08-26
### Audited working tree: `FIE_work/Fantasy-Intelligence-main`

# Executive verdict

## Current deployment status: **NOT DEPLOYABLE**

The current version is materially stronger than the pre-Phase-1 codebase. It now has useful foundations for league switching, research feature lineage, 3RR, progressive Monte Carlo, V9 decision separation, position-aware scoring concepts, and namespaced M1–M6 research.

However, a full pre-deployment audit uncovered several **P0 correctness defects** and substantial architectural duplication that make the exact current working tree unsuitable for production.

The most important conclusion is:

> **Do not add D/ST runtime logic to the current architecture yet. First centralize the league profile, position/slot, scoring, replacement, lineup optimization, request/state, and valuation contracts. D/ST should then become an extension of those registries rather than another parallel scoring/model path.**

This is not a recommendation for a complete rewrite. The research pipeline and many newer modules should be retained. The correct approach is a **controlled consolidation and hardening release**.

---

# 1. Audit scope

The audit covered:

- `index.html`
- `app/`
- `research/`
- `functions/`
- `config/`
- `.github/workflows/`
- Cloudflare Pages configuration
- build/release manifests
- league profiles
- M1–M6 namespaced research artifacts
- current M5 snapshots
- governance artifacts for all 19 registered leagues
- scoring relevance logic
- Draft Assistant and V9 ranking logic
- Value Finder
- Monte Carlo Draft Strategist
- saved-league state
- season abstraction
- runtime caching
- source-health diagnostics
- test architecture
- deployment hygiene
- privacy/security exposure
- code duplication and monkey-patching

## Verification performed

The following were specifically checked:

- JavaScript syntax for the new `app/*.js` modules
- current build-manifest hash integrity
- production-readiness audit
- research/governance status across all 19 registered leagues
- current-snapshot size and duplication
- source-level integrity tests
- runtime VM tests already present in the repository
- league-switch race test
- Monte Carlo worker contract
- V9 decision model code paths
- scoring relevance implementation
- release output configuration

## Browser-test limitation

A true local Chromium/Playwright smoke run was attempted, but this environment blocks local/file browser navigation through administrator policy. Therefore:

> **A real served-build Playwright run against a Cloudflare preview deployment remains a mandatory external deployment gate.**

Static and VM/runtime tests are useful, but they cannot replace this final browser verification.

---

# 2. What is already strong

The audit is critical because the goal is release excellence, but significant work should be preserved.

## Research architecture

Positive findings:

- all 19 managed league namespaces are present;
- league profiles exist;
- M1–M6 bundles exist;
- current-snapshot artifacts exist;
- governance artifacts exist;
- namespaced research architecture is substantially better than the original global-only pipeline;
- temporal/bootstrap validation and fail-closed concepts are present;
- current-player feature lineage has been introduced;
- D/ST work can later reuse this research/governance architecture.

## Runtime foundations

Positive findings:

- Sleeper-native Chopped detection now considers `settings.type === 3`;
- 3RR has a canonical runtime service;
- a `LeagueController` with generation IDs and `AbortController` now exists;
- a dedicated V9 decision layer separates League Rank, Roster Value, and Draft Decision conceptually;
- Monte Carlo has been moved toward a worker model;
- Value Finder now caches more of its expensive work;
- `SeasonContext` exists;
- research feature usage is increasingly explicit and leakage-aware;
- a decision-specific validation framework has been created;
- many existing integrity/runtime tests pass.

## Release architecture

Positive findings:

- artifact hygiene checks exist;
- build-manifest hashing exists;
- source proxy has an allowlist;
- research governance is designed to fail closed;
- deployment can be made robust without replacing the entire system.

---

# 3. Immediate P0 deployment blockers

Every item in this section should be fixed before a production deployment.

---

## P0-01: Build manifest is stale

### Evidence

Running:

```bash
python research/integrity_build_manifest_test.py
```

currently fails with:

```text
AssertionError: stale manifest hash: app/runtime-foundation.js
```

### Risk

The exact release tree cannot be hash-verified.

### Required fix

- regenerate the build manifest only after every code/data change is complete;
- make manifest generation the final build step;
- immediately rerun manifest verification;
- prevent deployment if any listed hash differs.

### Deployment criterion

```text
integrity_build_manifest_test.py = PASS
```

---

## P0-02: V9 replacement comparator uses the wrong demand quantity

### Evidence

`app/decision-model-v9.js`, line 18:

```js
function positionReplacement(rows,pos,key){
    ...
    demand=Math.max(
        1,
        Math.ceil(Number((window.leaguePositionDemand||leaguePositionDemand)(pos))||1)
    );
    ...
}
```

V8.9's demand helper is based on **marginal per-team starter demand**, not the league-wide replacement cutoff required for cross-position replacement.

### Example

In an 18-team league with one required QB per team:

- personal/team starter demand is roughly 1 QB;
- league replacement demand should be roughly around QB18 plus any bench/scarcity allowance.

Using a demand near 1 makes the lower-tail comparator closer to QB1 than QB18.

### Affected models

- Chopped lower-tail surplus
- Best Ball ceiling surplus
- cross-position League Rank
- downstream Draft Decision

### Required fix

Create two explicitly different concepts:

```text
PersonalRosterDemand
LeagueReplacementDemand
```

Use a canonical `ReplacementService` for V9.

Prefer existing computed league replacement levels where available, for example:

```text
state.projectedReplacementLevels[position]
```

or rebuild them through one shared service.

### Mandatory regression tests

- 18 teams × 1 QB must never use QB1 as replacement;
- changing league size from 10 to 18 must move the cutoff materially;
- FLEX/SUPER_FLEX demand must affect relevant positions;
- a roster change must not alter League Rank's league-wide replacement cutoff.

---

## P0-03: Worker Monte Carlo can lose the user's existing roster

### Evidence

`simulationContext()` constructs:

- `pool`: available/draftable players
- `basePools`: already rostered players

But `monteCarloWorkerContext()` serializes:

```js
players: ctx.pool.map(...)
basePools: IDs only
```

The worker builds its `byId` map only from `ctx.players`.

Therefore rostered players that are not in the available draft pool cannot be reconstructed.

### Risk

The final simulated roster may effectively contain:

- newly drafted players,
- but not the user's existing owned players.

That invalidates final roster utility.

### Required fix

Serialize:

```text
allPlayers = union(
    available draft pool,
    every player in every base roster
)
```

Each record should contain:

```text
id
position
mean/floor/ceiling/VOR/utility
draftAvailable: true/false
```

The worker's `available` set must contain only `draftAvailable === true`.

### Mandatory regression test

For a fixture roster with N existing players:

```text
serialized base roster count = N
worker reconstructed base roster count = N
every base roster ID resolves
```

---

## P0-04: Monte Carlo bench utility double-counts starters

### Evidence

`app/draft-monte-carlo-worker.js`, `rosterUtility()`:

- calculates exact starter lineup value;
- then calculates `benchBonus` from the top VOR values in the **entire** player pool.

The starter IDs are not removed first.

### Risk

A player may count:

1. as a starter;
2. again in the bench bonus.

### Required fix

`lineupValue()` or a new `optimizeLineup()` must return:

```text
total
assignment
selectedPlayerIds
unassignedPlayerIds
```

Bench value must use only `unassignedPlayerIds`.

### Mandatory test

No player ID may contribute to both:

```text
starterTotal
benchBonus
```

---

## P0-05: Saved-league format mutation bug still exists through wrapper order

### Evidence

The V7.1 handler correctly checks whether the selected saved league equals the active league before mutating active `leagueRules`.

But `bindV82()` later wraps that handler:

```js
quick.onchange=function(){
    old?.();
    state.leagueRules.format=quick.value;
    ...
}
```

This write is unconditional.

### Risk

While League A is active:

1. select saved League B;
2. alter B's saved format;
3. V7.1 correctly updates B's saved record only;
4. V8.2 then writes the control value into active League A.

This can reintroduce the exact wrong-league state problem identified earlier.

### Required fix

Delete wrapper-based format handling.

Create one command:

```js
SavedLeagueController.updateFormat(savedLeagueId, format)
```

It may update active runtime state only when:

```text
savedLeagueId === activeLeagueId
```

### Mandatory race/state tests

- editing B never changes A;
- loading B after editing B uses B's value;
- returning to A restores A's value;
- format changes during loading cannot mutate the wrong generation.

---

## P0-06: League-state reset is incomplete

### Evidence

`resetLeagueVolatileState()` currently resets several major slices, but does not fully clear all league-bound state.

Potential stale slices include:

- `publicStatus`
- `publicErrors`
- `projectionStatus`
- `replacementLevels`
- `projectedReplacementLevels`
- `selectedRoster`
- `weekly`
- `calibration`
- `featureLearning`
- `matchDiagnostics`
- other simulation/lineup-specific state

### Risk

League B may temporarily or permanently use League A's:

- replacement levels,
- weekly data,
- projection status,
- selected roster,
- calibration state,
- matchup diagnostics.

### Required fix

Create a typed/schematized initial state per slice:

```text
LeagueState
PlayerDataState
ProjectionState
WeeklyState
DraftState
ResearchState
DiagnosticsState
```

Reset every league-scoped slice atomically.

### Mandatory test

After switching leagues, before background loading finishes:

```text
no field marked league-scoped may contain prior league ID/data
```

---

## P0-07: Async cancellation does not cover all league-dependent requests

### Evidence

The new `LeagueController` aborts critical requests, but legacy functions still issue direct requests and mutate global state.

Examples include:

- public enrichment;
- projections;
- weekly data;
- draft history;
- transactions;
- weather;
- odds;
- archived draft intelligence.

`loadLeagueTransactions()` can create approximately:

```text
3 seasons × 19 transaction rounds = 57 requests
```

through a single `Promise.allSettled()` fanout.

### Risk

Old League A requests can finish after League B becomes active and mutate shared state.

### Required fix

Introduce a single `RequestManager` / `DataClient`.

Every league-dependent operation receives:

```text
scope
leagueId
generation
AbortSignal
timeout
cache policy
source ID
```

Before committing a result:

```text
requestScope.isCurrent() === true
```

### Additional fix

Limit transaction-history concurrency, for example 4–6 requests.

---

## P0-08: League profile fingerprint includes volatile Sleeper settings

### Evidence

`research/league_profile.py` fingerprints the full:

```python
"settings": settings
```

inside the league contract.

Five current governance releases fail `current_profile_live_match`.

The observed differences include volatile values such as:

```text
daily_waivers_last_ran
```

Chopped leagues can also expose season-progress fields such as:

```text
leg
last_chopped_leg
```

### Risk

A league can become research-incompatible because Sleeper updates operational state that does not alter fantasy valuation rules.

### Required fix

Create a canonical `StructuralLeagueContract`.

Fingerprint only valuation-relevant stable settings, for example:

- format/type;
- best-ball flag;
- scoring;
- roster positions;
- total roster count;
- structurally relevant draft/roster settings;
- research cohort constraints.

Store the complete Sleeper settings separately for diagnostics.

### Migration

After changing the contract:

- rebuild all league profiles;
- regenerate dependent fingerprints;
- rebuild governance;
- verify no purely operational field can invalidate the model.

---

## P0-09: Position-aware scoring relevance is still materially incorrect

### Evidence

`research/scoring_relevance.py` currently includes:

```python
OFFENSE_PREFIXES=('pass_','rush_','rec_',...)
```

which makes any passing rule relevant to QB/RB/WR/TE.

It also currently defines:

```python
IDP_PREFIXES=('tkl_','qb_hit','pass_def')
```

while the browser-side classifier contains additional IDP patterns.

Unknown scoring rules intentionally remain relevant to all positions.

### Specific risks

1. pass-only scoring can become relevant to RB/WR/TE;
2. `idp_*` keys may be treated as unknown;
3. unknown D/ST keys can contaminate offensive scoring coverage;
4. individual special-teams return scoring and team-D/ST return scoring require different relevance;
5. Python and JavaScript classification can disagree.

### Confirmed practical effect

Current position support across the managed league profiles remains too conservative to produce exact support for many core offensive positions.

### Required fix

Create **one canonical scoring registry**, not two manually maintained classifiers.

Each Sleeper scoring key/family needs metadata:

```text
canonical_rule
Sleeper aliases
affected fantasy positions
team-DST vs individual
source field(s)
linear/nonlinear
weekly replay support
season expectation support
implementation status
```

Generate:

- Python registry;
- browser registry;
- documentation table;
- tests

from the same source definition.

### Important core mapping audit

Core offensive rules such as interceptions and fumbles must map to actual source columns correctly before any K/DST/D/ST expansion.

---

## P0-10: Production readiness incorrectly reports READY while all research runtime releases are disabled

### Evidence

There are 19 namespaced governance files.

Current count:

```text
runtime_enabled = true: 0
runtime_enabled = false: 19
```

Reasons:

```text
eligible_players: 14
current_profile_live_match + eligible_players: 5
```

Yet:

```bash
python research/production_readiness.py --strict
```

reports repository status:

```text
READY
```

because it primarily validates artifact existence/namespace/profile consistency, not live runtime activation.

### Risk

“READY” has two incompatible meanings:

1. repository artifacts exist;
2. research runtime is actually authorized.

### Required fix

Use explicit statuses:

```text
REPOSITORY_READY
RUNTIME_FALLBACK_ONLY
RUNTIME_RESEARCH_ACTIVE
DEPLOYABLE
```

A deployment can legitimately be `RUNTIME_FALLBACK_ONLY`, but this must be explicit.

### Release tooling

Create one `release_gate.py` that owns the final deploy decision.

---

## P0-11: V9 production decision weights are hard-coded without governed promotion

### Evidence

Examples in `app/decision-model-v9.js`:

```text
Chopped:
0.55 VOR-related + 0.45 floor-surplus

Best Ball:
0.55 VOR-related + 0.45 ceiling-surplus

Dynasty:
0.55 VOR percentile + 0.45 dynasty percentile

Draft Decision:
0.65 League + 0.25 Roster + 0.10 Timing
```

A decision-validation framework exists, but these exact live weights are not currently enabled through an empirical promotion artifact.

### Risk

The UI can make calibrated-looking recommendations from candidate coefficients.

### Required fix

Before deployment choose one of two safe approaches:

### Option A, recommended initially

V9 remains **Beta/Diagnostic**.

Production decisions use the last governed fallback until V9 coefficients clear decision-specific validation.

### Option B

Generate a governed model-config artifact:

```text
model_version
coefficients
training window
validation window
metrics
confidence intervals
promotion result
activation scope
```

Client code may consume coefficients only if the artifact is activated.

### Rule

Hard-coded candidate weights must not masquerade as empirically promoted production coefficients.

---

## P0-12: V9 Roster Value is not an exact lineup marginal

### Evidence

`rosterGainApprox()` compares the candidate primarily with same-position roster players and per-position demand.

It does not perform exact FLEX/SUPER_FLEX lineup displacement.

### Risk

The UI calls the result roster marginal value, but the calculation is only an approximation.

### Required fix

Use the canonical lineup optimizer:

```text
RosterValue(player)
=
OptimalRosterUtility(roster + player)
-
OptimalRosterUtility(roster)
```

For acquisition constraints:

```text
max over legal drop candidates
```

This can be cached and applied only to the shortlist for performance.

### Temporary fallback

Until exact marginal value is active, label it:

```text
Same-position roster approximation
```

not “marginal roster utility”.

---

## P0-13: Value Finder can bypass the intended M6 governance boundary for opportunity residuals

### Evidence

Value Finder's current-feature opportunity adjustment checks leakage-safe lineage, but the activation path does not consistently require all of:

```text
player activation eligibility
league governance allow
M6 runtime activation
```

### Risk

A research feature can influence Value Finder even when the research governance layer says the model is closed.

### Required fix

A research feature may alter production decisions only when:

```text
feature.leakageSafe
AND feature.validation_status == promoted
AND player.activationEligible
AND leagueGovernance.runtime_enabled
AND domain gate permits the decision
```

Otherwise it is diagnostic/explainability only.

---

## P0-14: Draft Assistant and Value Finder still use competing valuation kernels

### Evidence

The V9 Draft Assistant uses `FIEModelV9`.

Value Finder still contains its own V8.9/M5 weighted scoring logic and heuristics.

### Risk

The same player can be:

- highly preferred by Draft Assistant;
- weakly valued by Value Finder;

for architectural rather than strategic reasons.

### Required fix

Centralize:

```text
LeagueValueService
RosterValueService
DraftTimingService
DecisionService
```

Value Finder should consume these and add only its distinct job:

```text
market inefficiency
target band
sleepers/value classification
```

It should not independently recreate the full football valuation model.

---

## P0-15: Cloudflare Pages is configured to deploy the entire repository root

### Evidence

`wrangler.toml`:

```toml
pages_build_output_dir = "."
```

Current repository size is approximately:

```text
224 MiB
```

Research data alone dominates the tree.

### Potentially published content includes

- full research data;
- Python research source;
- old docs;
- backup files;
- cached bytecode;
- managed league config;
- artifacts not needed by the client.

### Required fix

Build a clean:

```text
dist/
```

Deployment should contain only:

- HTML shell;
- CSS;
- production JS;
- Cloudflare functions as required;
- compact public runtime data;
- explicit public configuration;
- release/version metadata.

Set:

```toml
pages_build_output_dir = "dist"
```

### Release test

Fail if `dist/` contains files outside an allowlist.

---

## P0-16: Backup and generated temporary files remain in the release tree

### Examples

```text
index.pre_phase1_7.html
app/decision-engines.pre_phase1_7.js
app/value-finder.pre_phase1_7.js
app/portfolio-home.pre_phase1_7.js
research/league_profile.pre_phase1_7.py
research/build_current_snapshot.pre_phase1_7.py
research/__pycache__/*.pyc
```

### Required fix

- move historical backups outside production source;
- expand `.gitignore`;
- add a release hygiene rule forbidding:
  - `*.pre_*`
  - `*.bak`
  - `__pycache__`
  - `*.pyc`
  - temporary manifests.

---

## P0-17: Personal portfolio metadata would be statically published

### Evidence

`config/league-portfolio.json` contains:

- a Sleeper username;
- 19 league IDs.

Because the current Pages output is repository root, this file is public if the site is public.

### Required product decision

If this is a private personal application:

- protect deployment with Cloudflare Access or equivalent.

If this is intended as a public/general product:

- remove personal account/config data from public static files;
- use localStorage/private config/KV/authenticated storage;
- ship an empty/default portfolio configuration.

---

## P0-18: Odds API key can enter runtime diagnostics through full URLs

### Evidence

`loadOdds()` constructs a URL containing:

```text
apiKey=<user key>
```

`fetchJSON()` records source health using the full URL.

`recordSourceHealthV7()` stores:

```js
const key=String(url);
FIE_SOURCE_HEALTH[key] = ...
```

The UI label hides the raw URL, but the full URL can remain in global runtime state/devtools.

### Required fix

Create a central URL redactor.

Never log/store diagnostic query parameters named:

```text
key
apiKey
token
secret
authorization
```

Prefer a server-side proxy/secret if the product later manages its own odds credential.

---

## P0-19: Release/version identity is inconsistent

### Current examples

- Cloudflare project name includes `v7`;
- health endpoint reports `V8.9-RTS`;
- proxy User-Agent contains V8.9;
- client state contains V8.9 labels;
- build manifest identifies V9 components;
- Value Finder has another composite version.

### Risk

Debugging a deployed bug cannot reliably answer:

> “Which exact release generated this behavior?”

### Required fix

Generate one canonical release descriptor:

```json
{
  "release": "9.x.x",
  "commit": "...",
  "built_at": "...",
  "runtime": "...",
  "research_schema": "...",
  "model_config": "...",
  "data_snapshot": "..."
}
```

All client/functions/health/build-manifest UI should consume it.

---

## P0-20: Real-browser release verification is not currently demonstrated

### Evidence

The source and VM test suite is substantial, but true local Chromium execution could not be performed in this audit environment because administrator policy blocks local/file navigation.

### Required fix

Run Playwright against a real preview deployment.

### Mandatory scenarios

- cold launch;
- warm cached launch;
- Redraft load;
- Chopped load;
- Dynasty load;
- Best Ball;
- Superflex;
- custom cohort/Genesis;
- rapid A → B → A switching;
- format editing of B while A is active;
- 3RR draft;
- Value Finder open/filter;
- Monte Carlo run/cancel;
- switch league while MC runs;
- Draft Player Report;
- Lab states;
- Start/Sit;
- mobile viewport.

No production deployment before this gate passes.

---

# 4. High-priority P1 improvements required for a “commitment to excellence” release

These are not all single-line bugs, but they should be part of the pre-deployment overhaul rather than deferred indefinitely.

---

# 4.1 Centralize position and roster-slot definitions

## Current problem

Position eligibility is duplicated across:

- main app;
- V8.9;
- V9;
- Monte Carlo worker;
- scoring relevance;
- research;
- Value Finder.

The Monte Carlo worker currently supports a smaller slot set than the main app.

For example, its `SLOT` map does not fully mirror all:

- DE;
- DT;
- CB;
- S;
- P;
- OL;
- T;
- G;
- C

semantics.

`RESERVE` handling also differs from bench/exclusion rules.

## Required architecture

Create one canonical `PositionRegistry` / `RosterSlotRegistry`.

It should define:

```text
slot
eligible model positions
starter/bench/reserve classification
replacement family
scoring family
fantasy group
```

Generate JS worker and Python representations from the same registry.

## D/ST relevance

This is a **prerequisite for D/ST implementation**.

D/ST should add/extend:

```text
DEF/DST slot
team-defense entity type
replacement group
scoring-family support
```

without creating a separate code path.

---

# 4.2 Centralize lineup optimization

## Current problem

Several functions optimize or approximate roster value differently.

## Required service

Create:

```text
LineupOptimizer
```

Input:

```text
players
roster slots
value key/objective
eligibility registry
```

Output:

```text
starterTotal
assignment
selectedPlayerIds
benchPlayerIds
unfilledSlots
method
```

Use it for:

- team analysis;
- roster marginal value;
- Monte Carlo;
- trade analysis;
- Start/Sit;
- Chopped downside utility;
- Best Ball spike utility.

No separate lineup algorithm per feature.

---

# 4.3 Centralize league-wide replacement

## Current problem

“Demand” currently refers to several different things:

- personal starter demand;
- league-wide replacement;
- flex demand;
- roster scarcity;
- Monte Carlo need.

## Required services

```text
LeagueDemandService
ReplacementService
```

Explicit outputs:

```text
perTeamStarterDemand[position]
leagueStarterDemand[position]
benchDemand[position]
replacementRank[position]
replacementPlayerId[position]
replacementPoints[position]
```

Replacement values should be independently testable.

---

# 4.4 Centralize scoring rule interpretation

This is one of the most important pre-D/ST tasks.

## Create one `ScoringRuleRegistry`

Each rule:

```text
Sleeper key
canonical name
affected position/entity families
source field
weekly exact support
season exact support
nonlinear flag
special-teams ownership
implemented status
```

### Generate

- JS runtime table;
- Python table;
- Data Quality matrix;
- tests.

### Unknown rules

Unknown scoring must remain fail-closed, but only for the correct potentially affected entity family.

---

# 4.5 Centralize player identity

## Current problem

Some runtime paths still fall back to player name.

Example in V9:

```js
sleeperId || name
```

Monte Carlo manager player biases also use names.

## Required rule

Canonical IDs only.

Priority:

```text
Sleeper player ID
source-specific canonical ID
synthetic namespaced ID for non-Sleeper entity
```

Names are display text, not a join key.

## Migration

Legacy stored manager/player biases may match names only as a migration fallback, then persist the resolved canonical ID.

---

# 4.6 Centralize data fetching

## Current state

There are still numerous direct `fetch()` paths across the runtime.

The active source currently contains roughly:

```text
18 direct fetch() occurrences
```

### Required `DataClient`

Capabilities:

- source ID;
- request type;
- timeout;
- AbortSignal composition;
- generation/scope;
- rate/concurrency limit;
- retry policy;
- CacheStorage/local cache policy;
- sanitized diagnostics;
- content-type validation;
- response-size guard;
- schema validation;
- stale-response protection.

No feature module should call raw `fetch()` except the DataClient/proxy layer.

---

# 4.7 Centralize state

## Current problem

The app currently has multiple effective sources of truth:

- global `state`;
- global `PLAYERS`;
- DOM inputs;
- localStorage;
- module caches;
- research globals.

### Required store slices

```text
session
league
leagueProfile
playerData
scoring
projection
weekly
draft
research
portfolio
ui
diagnostics
```

State should be mutated through actions/controller functions.

### Rule

DOM controls render state.

DOM values should not silently become production model state.

---

# 4.8 Centralize cache fingerprints

## Current problem

Different modules create ad-hoc cache keys.

Value Finder contains at least one suspicious key component where a boolean projection status is accessed as if it had an `updatedAt` field.

Monte Carlo's key does not encode every model/scoring/data dependency.

## Required `ContextFingerprint`

Include:

```text
league ID
structural profile fingerprint
scoring signature
roster state hash
draft-picks hash
projection dataset version
research snapshot version
model config version
season/week
feature snapshot version
```

All model caches use this one fingerprint contract.

---

# 4.9 Consolidate V9/VF/MC decision math

## Target architecture

```text
ProjectionDistribution
        ↓
LeagueValueService
        ↓
RosterValueService
        ↓
DraftTimingService
        ↓
DecisionService
        ↓
Draft Assistant / Value Finder / Monte Carlo / Trade
```

### Feature-specific responsibilities

Draft Assistant:
- present current decision.

Value Finder:
- find market inefficiency.

Monte Carlo:
- simulate future draft states.

Trade:
- compare roster utility.

They should not each own independent player-value models.

---

# 4.10 Make research promotion the only production-model gate

## Current problem

Browser-local calibration/feature-learning still exists alongside the more rigorous Python research governance.

## Required policy

Production model selection happens in the research pipeline.

Browser:

- reads promoted parameters;
- applies them;
- displays provenance.

Browser-local experimentation may exist only under:

```text
Lab / Experimental
```

and cannot alter production recommendations unless explicitly enabled.

---

# 5. Monte Carlo overhaul

Monte Carlo is strategically valuable, but it needs several additional correctness improvements before release.

---

## MC-01: Use canonical roster-slot registry

Worker and main runtime must consume identical eligibility logic.

---

## MC-02: Remove duplicated starters from bench bonus

Covered under P0-04.

---

## MC-03: Preserve existing rosters

Covered under P0-03.

---

## MC-04: Use canonical demand

The worker currently has its own `demandFor()` heuristic.

It should consume the same demand/replacement contract as the main app.

---

## MC-05: Common random numbers across candidates

Current RNG seed includes candidate ID.

That means candidate A and candidate B are evaluated under different random draft worlds.

For cleaner candidate comparison:

```text
seed = release/league/draft/simulation index
```

Use the same underlying random scenario for all candidate alternatives.

This reduces simulation comparison noise.

---

## MC-06: Cancellation granularity

The worker's `cancel` message cannot interrupt the middle of a long synchronous batch until the worker event loop can process the cancel message.

### Fix

Use smaller sub-batches, for example:

```text
8 or 16 simulations
```

Post progress after each.

The main process can also terminate the worker immediately when a league/draft switch occurs.

---

## MC-07: Main-thread fallback

If Web Workers are unavailable, the current fallback should not run a large synchronous simulation that freezes the browser.

### Preferred behavior

- small cooperative/chunked fallback;
- or show:
  `Deep simulation unavailable in this browser`.

Never sacrifice responsiveness.

---

## MC-08: Cache fingerprint

Monte Carlo cache must include full model/context fingerprint, not only league/draft/roster/pick state.

---

## MC-09: Manager bias by canonical ID

Stored player tendencies should use player ID, not display name.

---

## MC-10: Worker/main parity test

On a deterministic fixture:

```text
worker lineup utility == canonical main LineupOptimizer utility
```

within defined numerical tolerance.

---

# 6. Value Finder overhaul

---

## VF-01: Use canonical V9 valuation services

Value Finder should not maintain a parallel player-value engine.

---

## VF-02: Fix cache versioning

Use explicit projection/research dataset versions.

Do not infer freshness from loosely structured status objects.

---

## VF-03: Dynamic position registry

Current hard-coded position lists should be replaced with the canonical registry.

This is necessary before D/ST.

---

## VF-04: Eliminate name-based M5 joins

Use canonical player IDs.

---

## VF-05: Govern current opportunity usage

Research opportunity signals remain diagnostic unless all promotion gates pass.

---

## VF-06: Structured errors

Value Finder currently contains broad catch-and-continue patterns.

Expected optional failures may degrade gracefully.

Unexpected calculation failures must enter a diagnostics/error buffer.

---

## VF-07: Heuristic labelling

Snap-path scores, ADP bands, and unvalidated policy thresholds should be labelled:

```text
heuristic/proxy
```

until validated.

Do not make proxy outputs look empirical.

---

# 7. Research/governance overhaul

---

## RG-01: Structural profile fingerprint

Covered under P0-08.

---

## RG-02: Scoring registry

Covered under P0-09.

---

## RG-03: Runtime status semantics

Covered under P0-10.

---

## RG-04: Current-feature provenance completeness

Every exposed feature family should contain:

```text
source
as_of
sample size
leakage status
validation status
activation state
gate reason
```

Do not mark a PFF/TFG/environment value “active” merely because a value exists.

---

## RG-05: Preseason current-feature status

When there are no completed regular-season rolling features, the UI should say:

```text
No completed regular-season rolling opportunity features are available yet.
Preseason fallback remains active.
```

not a generic missing/unavailable message.

---

## RG-06: Decision-specific promotion

The new validation framework should be connected to actual model-config artifacts for:

- Draft
- Start/Sit
- Waiver
- Chopped
- Best Ball
- Dynasty.

A model may be promoted in one domain and remain fallback in another.

---

## RG-07: Reproducible dependencies

Python requirements currently use loose lower bounds.

Before a production research release:

- create a locked/constraints dependency set;
- record Python version;
- record library versions in build provenance;
- update dependencies intentionally.

---

## RG-08: Artifact schemas

Add JSON Schema or equivalent validation for:

- league profile;
- M1;
- M2;
- M3;
- M4;
- M5;
- M6;
- current snapshot;
- governance;
- portfolio config;
- model config;
- build manifest.

---

## RG-09: Artifact provenance

Every production research artifact should identify:

```text
schema version
producer version/hash
source dataset versions
structural league fingerprint
scoring signature
generated_at
```

---

# 8. Data payload and performance overhaul

This should be completed before deployment because load time was already a user-visible problem.

---

## DATA-01: Current snapshots are extremely duplicated

There are currently:

```text
19 current M5 snapshots
147.44 MiB total
approximately 7.76 MiB each
```

They largely repeat the same player universe.

### Preferred architecture

```text
GlobalCurrentPlayerFeatures
+
LeagueSpecificOverlay
```

Global:

- player identity;
- public projection;
- opportunity features;
- talent/context features.

League overlay:

- league scoring;
- replacement;
- rank;
- governance;
- league eligibility.

---

## DATA-02: Do not ship irrelevant positions in every league snapshot

An offense-only league does not need thousands of irrelevant defensive/OL records in a league-specific runtime payload.

Filter to:

- league-relevant entities;
- or store the global universe once.

---

## DATA-03: Full historical research should not ship to normal browser runtime

Full M1–M6 artifacts are useful for research and Lab.

Normal UI should consume compact runtime summaries.

Keep full historical bundles outside `dist/` unless a user explicitly requests/downloads them.

---

## DATA-04: Lazy-load Lab

Research diagnostics should load when:

- Lab opens;
- a detailed player report explicitly needs lineage.

They should not delay the league shell.

---

## DATA-05: Parsing

Large JSON parsing can itself block the UI.

After compacting artifacts, if any payload remains large:

- parse in a worker;
- or stream/split by position/domain.

---

## DATA-06: Player-map cache governance

CacheStorage currently uses a stale-while-revalidate style flow.

Add:

```text
schema version
stored_at
max age
release/data version
```

A stale cached player map should not live indefinitely without visibility.

---

# 9. Code centralization and monolith removal

This is the biggest maintainability project.

---

# 9.1 Current problem: critical functions are defined/wrapped repeatedly

Examples from `index.html` and app modules:

### `loadLeague`

Multiple generations remain in the page:

- original base implementation;
- V7 wrapper;
- V8.2 replacement;
- V8.9 wrapper;
- runtime-foundation final reassignment.

### `renderDraftAssistant`

Multiple generations/wrappers exist:

- base;
- V7.1;
- V8.2;
- M5;
- Value Finder;
- decision engine.

### `render`

Also wrapped repeatedly.

### Consequence

Behavior depends on:

- script execution order;
- which function was captured before another wrapper;
- whether an old reference is later called by a newer wrapper.

This is exactly how the saved-format bug survived the new state controller.

---

# 9.2 Centralization rule

Critical global actions may be defined **once**.

Examples:

```text
AppController.loadLeague
DraftController.renderAssistant
AppRenderer.render
ModelService.assignScores
```

No later module may monkey-patch them.

---

# 9.3 Add a duplicate-definition integrity test

Fail CI if critical symbols are:

- redefined;
- reassigned;
- wrapped.

Allow extension only through explicit hooks/events/interfaces.

---

# 9.4 Decompose `index.html`

Current file size is approximately:

```text
1.37 MB
```

It should become primarily:

- semantic HTML shell;
- stylesheet references;
- module bootstrap.

Suggested structure:

```text
app/
  bootstrap.js
  state/
  controllers/
  services/
  model/
  views/
  components/
  diagnostics/
  workers/
```

---

# 9.5 Remove inline event handlers

The active tree still contains around:

```text
21 inline onclick= occurrences
```

Replace them with:

- `addEventListener`;
- event delegation;
- controller-bound actions.

Benefits:

- cleaner lifecycle;
- easier testing;
- CSP support;
- no hidden global dependency.

---

# 9.6 Audit HTML rendering

The active app contains roughly:

```text
75 .innerHTML writes
```

Not all are unsafe because the app often uses escaping.

Still:

- centralize `escapeHTML`;
- prefer DOM-building helpers for complex content;
- explicitly review all externally sourced league/player/user text.

---

# 9.7 Replace broad silent catches

The active tree contains many:

```text
catch {}
```

patterns.

Optional features may fail softly, but unexpected errors should be visible in diagnostics.

Create:

```text
Diagnostics.capture(error, context)
```

with:

- redaction;
- ring buffer;
- timestamp;
- active release;
- league ID;
- feature domain.

---

# 10. Season and rollover hardening

---

## SEASON-01: Fix `portfolio-config.js` SeasonContext call

Current code:

```js
num(window.FIESeasonContext?.active)
```

If `active` is a function, this passes the function object to `Number()`.

Use:

```js
window.FIESeasonContext?.active?.()
```

---

## SEASON-02: Behavioral season logic must use SeasonContext

Gradually replace legacy semantic fields such as:

```text
weekly2026
team2026
snaps2026
```

with:

```text
weeklyCurrent
teamCurrent
snapsCurrent
```

Do not mechanically replace historical/provenance uses of `2026`.

---

## SEASON-03: Rollover tests

Fixtures should validate:

- late December;
- January playoffs/offseason;
- February;
- preseason;
- new Sleeper league season;
- previous league chain.

---

# 11. Security, privacy, and robustness

---

## SEC-01: Build `dist/`

Covered under P0-15.

---

## SEC-02: Add security headers

Once inline scripts/event handlers are reduced, add Cloudflare `_headers` such as:

```text
X-Content-Type-Options: nosniff
Referrer-Policy
Permissions-Policy
Content-Security-Policy
frame-ancestors
```

Exact CSP should be built around the actual external data requirements.

---

## SEC-03: Redact secrets from diagnostics

Covered under P0-18.

---

## SEC-04: Harden proxy upstream calls

Add:

- upstream timeout;
- AbortController;
- allowed content types;
- maximum response size where practical;
- sanitized error messages;
- consistent release User-Agent.

The existing allowlist should remain.

---

## SEC-05: Public/private deployment decision

If this is a personal multi-league command center, consider Cloudflare Access.

If it becomes public, remove personal config from static assets.

---

# 12. Accessibility and UI quality

A commitment-to-excellence release should include basic accessibility rather than deferring it indefinitely.

---

## A11Y-01: Clickable table rows

Add:

```text
tabindex=0
Enter/Space activation
visible focus
```

---

## A11Y-02: Player drawer/dialog

Use:

```text
role="dialog"
aria-modal="true"
```

Add:

- focus trap;
- close with Escape;
- return focus to originating row.

---

## A11Y-03: Sortable tables

Use real buttons or keyboard-accessible headers.

Expose:

```text
aria-sort
```

---

## A11Y-04: Loading and status

Use appropriate:

```text
aria-live
```

for asynchronous league/data status.

---

## A11Y-05: Do not rely on color alone

Positive/negative/warning signals need text/icons in addition to color.

---

# 13. Test architecture overhaul

The current test suite is broad, but it needs a clearer release hierarchy.

---

## 13.1 Split test tiers

### Unit

Fast, seconds.

Examples:

- scoring registry;
- position registry;
- replacement service;
- identity;
- SeasonContext;
- lineup optimizer.

### Release

Bounded, minutes.

Examples:

- all fast integrity tests;
- build manifest;
- profiles;
- runtime source contracts;
- worker/main parity;
- payload limits;
- version consistency.

### Research

Deep empirical jobs.

Examples:

- long M4 validation;
- historical bootstrap experiments;
- model retraining.

Do not let one deep empirical script make the deployability check ambiguous.

---

## 13.2 Add explicit timeouts

Each test owns a time budget.

Failure types should distinguish:

```text
FAIL
TIMEOUT
SKIP
NOT_APPLICABLE
```

---

## 13.3 Add true browser Playwright tests

Already covered under P0-20.

---

# 14. Mandatory new invariants

The following should be machine-tested before production.

## League/state

- old league async results cannot mutate current league;
- selected saved league and active league are separate;
- editing saved B cannot modify active A;
- all league-scoped state resets.

## Replacement/model

- replacement cutoff scales with number of teams;
- League Rank is independent of the user's roster;
- Roster Value changes with roster composition;
- FLEX/SF displacement is legal and exact.

## Lineup

- a player starts at most once;
- bench excludes starters;
- all assignments obey one slot registry;
- incomplete lineups report unfilled slots.

## Monte Carlo

- base roster is reconstructed exactly;
- available pool excludes rostered players;
- common random scenario is used for candidate comparisons;
- worker and main utility agree;
- cancellation works within bounded latency.

## Scoring

- Python and JS rule relevance are generated from one registry;
- unknown rules fail conservatively;
- irrelevant K/DST rules do not disable offense;
- individual-return rules are not mistaken for team-DST rules;
- scoring signature changes when actual scoring changes.

## Profiles

- volatile Sleeper operational settings do not change structural fingerprint;
- scoring/roster/format changes do change it.

## Security/release

- no secrets in diagnostics;
- no backup/cache files in dist;
- no personal config in public dist unless explicitly allowed;
- all release versions agree;
- manifest hashes match.

---

# 15. League fixture matrix

Before deployment, maintain representative fixtures for:

1. 12-team 1QB Redraft
2. 18-team Chopped 1QB
3. Superflex
4. TE premium
5. Best Ball
6. Dynasty
7. IDP
8. Kicker
9. custom cohort/Genesis
10. future D/ST

The D/ST fixture can be activated after the separate D/ST research work, but the registry architecture must exist before that integration.

---

# 16. Documentation overhaul

The root currently contains many version-specific readmes, changelogs, manifests, and milestone documents.

Archive historical documents under:

```text
docs/archive/
```

Maintain only a small canonical active set:

```text
README.md
ARCHITECTURE.md
DEPLOYMENT.md
MODEL_GOVERNANCE.md
DATA_CONTRACTS.md
TESTING.md
SECURITY.md
CHANGELOG.md
RELEASE_CHECKLIST.md
```

After the D/ST project:

```text
DST_MODEL.md
```

## Documentation rules

- one current deployment guide;
- one current architecture source of truth;
- versioned change log;
- no stale statements such as “Sleeper has no native Chopped type”;
- diagrams for data flow and model flow;
- explicit fail-closed behavior.

---

# 17. CI/CD excellence

---

## CI-01: Linting/formatting

Add:

### JavaScript
- ESLint
- formatter

### Python
- Ruff
- Black or equivalent
- optional type checking for critical contracts

---

## CI-02: Prevent architecture regression

Add checks for:

- raw `fetch()` outside DataClient;
- duplicate critical global definitions;
- inline event handlers;
- backup files;
- stale version strings;
- forbidden secret parameters;
- oversized bundles;
- missing schema versions.

---

## CI-03: Generated artifacts should not be partially committed

Research/build workflow should:

1. generate all outputs;
2. validate all outputs;
3. generate release manifest;
4. only then commit/publish.

Prefer a branch/PR or dedicated generated-artifact commit rather than committing partially validated outputs directly to the main production branch.

---

# 18. Release architecture

Create:

```text
src/
research/
config-private-or-dev/
data-full-research/
dist/
```

## `dist/` should be generated

It should not be the repository root.

### Suggested public contents

```text
index.html
assets/*.css
assets/*.js
workers/*.js
data/runtime/*
config/public/*
release.json
```

Full research bundles remain outside the public runtime package unless intentionally exposed.

---

# 19. Optimal central architecture before D/ST

This is the most important architectural commitment.

D/ST should integrate into these existing contracts, not create new parallel logic.

```text
                         ┌────────────────────┐
                         │   Sleeper / Data    │
                         └─────────┬──────────┘
                                   │
                            ┌──────▼──────┐
                            │ DataClient  │
                            └──────┬──────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Canonical State    │
                         │ + Request Scopes   │
                         └─────────┬─────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │                           │                           │
┌──────▼──────┐          ┌─────────▼────────┐        ┌────────▼────────┐
│LeagueProfile│          │Position/Slot      │        │ScoringRule      │
│Resolver     │          │Registry           │        │Registry         │
└──────┬──────┘          └─────────┬────────┘        └────────┬────────┘
       │                           │                           │
       └───────────────────┬───────┴──────────────┬────────────┘
                           │                      │
                  ┌────────▼────────┐    ┌────────▼────────┐
                  │Replacement      │    │Projection       │
                  │Service          │    │Distribution     │
                  └────────┬────────┘    └────────┬────────┘
                           │                      │
                           └──────────┬───────────┘
                                      │
                            ┌─────────▼─────────┐
                            │ LeagueValue       │
                            └─────────┬─────────┘
                                      │
                            ┌─────────▼─────────┐
                            │ LineupOptimizer   │
                            │ + RosterValue     │
                            └─────────┬─────────┘
                                      │
                            ┌─────────▼─────────┐
                            │ DraftTiming       │
                            └─────────┬─────────┘
                                      │
                            ┌─────────▼─────────┐
                            │ DecisionService   │
                            └──────┬─────┬──────┘
                                   │     │
                          Draft Assistant
                          Value Finder
                          Monte Carlo
                          Trade/Start-Sit
```

## D/ST later adds

- team-DST entity type;
- DEF/DST roster-slot support;
- D/ST scoring families;
- D/ST projection distribution;
- replacement levels;
- D/ST-specific feature families.

Everything downstream then works through the same generic interfaces.

---

# 20. Exact implementation order

I recommend this order.

---

## Workstream 1: Freeze current baseline

- snapshot rankings;
- snapshot Draft Assistant;
- snapshot Value Finder;
- record league fixtures;
- preserve a tagged archive of this RC.

---

## Workstream 2: Central registries

Implement first:

1. `PositionRegistry`
2. `RosterSlotRegistry`
3. `ScoringRuleRegistry`
4. `PlayerIdentity`
5. `SeasonContext`

Generate Python/JS forms from the same canonical definitions where possible.

---

## Workstream 3: League/state/request consolidation

- `StructuralLeagueContract`
- `LeagueProfileResolver`
- `LeagueController`
- full state reset
- `DataClient`
- request scopes/generations
- saved-league controller
- remove old format wrappers

---

## Workstream 4: Replacement and lineup correctness

- `LeagueDemandService`
- `ReplacementService`
- exact `LineupOptimizer`
- starter IDs/bench IDs
- FLEX/SF support
- roster marginal value

Fix P0-02 and P0-12 here.

---

## Workstream 5: Monte Carlo correctness

- serialize union of available + owned players
- eliminate starter/bench double count
- canonical slot/demand
- common random numbers
- sub-batches/cancel
- canonical IDs
- exact worker/main parity test

---

## Workstream 6: Unify Draft Assistant and Value Finder

- one LeagueValue
- one RosterValue
- one DraftTiming
- Value Finder becomes market/opportunity finder
- no duplicate policy model

---

## Workstream 7: Research/governance contracts

- structural profile fingerprint
- unified scoring support
- rebuild 19 profiles/artifacts as required
- explicit runtime status
- connect decision-validation artifacts
- ensure opportunity features cannot bypass governance

---

## Workstream 8: Payload/runtime build

- global current feature snapshot
- league overlay
- compact research summaries
- lazy Lab
- clean `dist/`
- remove backups/pycache
- cache versioning

---

## Workstream 9: Security/privacy/accessibility

- secret URL redaction
- static config decision
- headers/CSP preparation
- proxy timeouts
- keyboard/dialog/table accessibility

---

## Workstream 10: Remove monolithic wrapper architecture

- extract remaining inline JS
- one definition per critical controller/service
- no monkey patches
- no model logic in DOM event handlers
- reduce inline `onclick`
- reduce unsafe rendering surfaces

This should be done incrementally behind the new stable services, not as a blind rewrite.

---

## Workstream 11: Release engineering

- version unification
- dependency locks
- fast/deep test tiers
- `release_gate.py`
- build manifest generated last
- preview deployment
- Playwright against preview

---

## Workstream 12: Production deployment

Only when every release gate below is green.

---

# 21. Deployment excellence checklist

The release is **ready to deploy** only when all applicable boxes are satisfied.

## Correctness

- [ ] Saved League B cannot mutate active League A.
- [ ] Rapid A → B → A switch passes under slow mocked network.
- [ ] Every league-scoped state slice resets.
- [ ] 3RR fixtures pass.
- [ ] V9 replacement cutoff uses league-wide demand.
- [ ] Roster Value uses exact legal lineup marginal utility.
- [ ] Monte Carlo preserves all existing rostered players.
- [ ] Monte Carlo bench excludes starters.
- [ ] Worker/main lineup utility parity passes.
- [ ] Draft Assistant and Value Finder share the same League/Roster value kernels.

## Scoring/governance

- [ ] Python and JS scoring relevance come from one registry.
- [ ] Core offensive scoring aliases are correctly mapped.
- [ ] Irrelevant K/DST scoring cannot disable offense.
- [ ] Individual return rules remain correctly relevant.
- [ ] Structural profile fingerprint ignores volatile operational settings.
- [ ] All 19 profiles rebuilt/validated under structural fingerprint.
- [ ] Runtime governance state is explicitly reported.
- [ ] V9 production weights are either promoted or clearly diagnostic/fallback.
- [ ] Value Finder cannot bypass M6/domain gates.

## Performance

- [ ] Warm saved-league shell target is met.
- [ ] Value Finder opens without long main-thread blocking.
- [ ] Monte Carlo first provisional result arrives progressively.
- [ ] Transaction history uses bounded concurrency.
- [ ] Research payload duplication materially reduced.
- [ ] Lab data is lazy-loaded.
- [ ] No repeated >200 ms main-thread tasks in normal interaction.

## Architecture

- [ ] One LeagueProfileResolver.
- [ ] One Position/Slot registry.
- [ ] One Scoring registry.
- [ ] One Replacement service.
- [ ] One Lineup optimizer.
- [ ] One PlayerIdentity service.
- [ ] One DataClient.
- [ ] One release version source.
- [ ] Critical global functions are not monkey-patched.
- [ ] Critical duplicate-definition CI test passes.

## Release/security

- [ ] `dist/` replaces root deployment.
- [ ] No `.pre_*` backups in `dist/`.
- [ ] No `__pycache__`/`.pyc` in `dist/`.
- [ ] No personal portfolio metadata is unintentionally public.
- [ ] No API key can enter diagnostics/logs.
- [ ] Security headers are configured.
- [ ] Proxy has upstream timeout and sanitized error handling.
- [ ] Version identity is consistent.
- [ ] Build manifest is current.
- [ ] Build-manifest integrity test passes.

## Testing

- [ ] Unit tier passes.
- [ ] Release tier passes within bounded time.
- [ ] Research tier has explicit status.
- [ ] Browser Playwright preview suite passes.
- [ ] Mobile viewport smoke passes.
- [ ] Season rollover fixtures pass.
- [ ] 19 managed league fixture/status checks pass.

## Documentation

- [ ] README is current.
- [ ] Architecture document is current.
- [ ] Deployment document is current.
- [ ] Model governance document is current.
- [ ] Data contracts are current.
- [ ] Testing guide is current.
- [ ] Security guide is current.
- [ ] Release checklist is current.
- [ ] Old version-specific docs are archived.

---

# 22. Recommended release quality levels

Do not use a single vague “READY” label.

## Level 1: Research artifact ready

All expected namespaced artifacts exist and validate.

## Level 2: Runtime fallback ready

App is technically deployable, but governed research overlays are inactive.

## Level 3: Runtime research active

At least the explicitly supported decision domains are empirically promoted and live.

## Level 4: Production deployable

All correctness, security, browser, payload, manifest, and release gates pass.

The current branch is closest to:

```text
Research artifact ready
+
partial runtime hardening
```

but it is **not Level 4**.

---

# 23. D/ST integration commitment

The separate D/ST analysis should be preserved and can continue conceptually, but runtime integration should begin only after these foundation components are centralized:

1. `PositionRegistry`
2. `RosterSlotRegistry`
3. `ScoringRuleRegistry`
4. `LeagueDemandService`
5. `ReplacementService`
6. `LineupOptimizer`
7. `ProjectionDistribution`
8. production model/governance contract

Then D/ST becomes clean:

```text
D/ST data
→ D/ST projection distribution
→ league scoring transform
→ league replacement
→ League Value
→ Roster Value
→ Draft/Start-Sit/Waiver decisions
```

This avoids repeating the current problem where K/DST/IDP/offense relevance logic exists in multiple inconsistent implementations.

---

# 24. Final recommendation

## Do not deploy this exact version.

The core project is worth hardening rather than replacing.

The highest-value action is now a **release-consolidation sprint**, not another analytics feature sprint.

The order should be:

```text
Correctness
→ central contracts
→ exact lineup/replacement
→ MC correctness
→ unified valuation
→ governance/scoring
→ payload/dist
→ security/accessibility
→ architecture cleanup
→ release gate
→ preview browser test
→ production
→ D/ST integration
```

A ready-to-deploy release should be defined by objective machine-verifiable gates, not by whether the newest feature appears to work manually.

The goal for the next version should be:

> **One source of truth for every football concept, one source of truth for every state transition, one source of truth for every production valuation, explicit governance for every empirical overlay, and a release package that can prove exactly what code and data it contains.**

That is the appropriate “commitment to excellence” standard for Fantasy Intelligence before D/ST is added.
