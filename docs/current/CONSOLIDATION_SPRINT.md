# 9.1 Consolidation Sprint

## Why this sprint exists

The pre-deployment audit found that research quality had outgrown application architecture. The goal of 9.1 is to remove deployment blockers, centralize shared contracts and create a clean foundation before D/ST is integrated.

## Step 1: canonical football contracts

Implemented a generated source of truth for:

- position aliases;
- roster-slot eligibility;
- starter versus bench/reserve slots;
- scoring-rule families;
- known weekly supported scoring rules;
- nonlinear season-rule identification.

Python and browser code now consume generated forms of the same contract.

## Step 2: core services

Added exact/common services for:

- canonical player IDs;
- Hungarian exact lineup assignment;
- league-wide starter demand;
- replacement cutoffs;
- exact roster marginal utility;
- context fingerprints;
- runtime diagnostics.

This fixes the previous ambiguity between personal starter demand and league replacement demand.

## Step 3: league state and requests

League switching now uses:

- `AbortController`;
- generation IDs;
- league IDs;
- full volatile-state reset;
- a centralized DataClient scope.

Legacy asynchronous requests that use the centralized `fetchJSON`/`fetchCSV` compatibility layer inherit the active league abort signal.

Transaction-history fanout is bounded to six concurrent requests and verifies the league before committing results.

## Step 4: saved league + format correctness

Inactive saved-league edits no longer mutate the active league. Native Chopped detection uses Sleeper structure before name heuristics. Draft sequence uses one 3RR-aware service.

## Step 5: structural profile identity

All 19 league profiles were migrated from full-settings fingerprints to structural-v2 contracts.

Operational fields such as waiver-run timestamps or Chopped progress can no longer invalidate research identity.

## Step 6: V9 fail-closed model

V9 diagnostics use:

- league-wide replacement;
- exact roster marginal utility;
- separate League Rank, Roster Value and Draft Decision concepts.

But production activation is controlled by `config/model-config.json`. Candidate coefficients are not silently promoted.

## Step 7: Value Finder centralization

Value Finder:

- uses canonical context fingerprints;
- uses dynamic positions from the roster registry;
- consumes the canonical production Draft rows through `FIEDecisionService`;
- permits current research opportunity features to affect decisions only after leakage, player, M6 and domain gates pass.

## Step 8: Monte Carlo correction

Fixed:

- lost pre-existing roster players;
- starter/bench double counting;
- divergent slot eligibility;
- candidate-specific random worlds;
- slow cancellation;
- synchronous no-Worker freeze fallback.

The worker now receives all owned + available players, marks which are draftable, reconstructs base rosters exactly, uses common random scenarios, and runs progressive sub-batches.

## Step 9: release semantics

Repository readiness and model-runtime activation are now separate concepts.

Current expected state before V9 empirical promotion:

```text
RESEARCH_ARTIFACT_READY
RUNTIME_FALLBACK_ONLY
```

That is a valid safe deployment state.

## Step 10: deployment isolation

Cloudflare now deploys `dist/`, not repository root.

The build excludes:

- Python source;
- docs;
- backup files;
- caches;
- unrelated research intermediates.

Current snapshots are compacted to league-relevant position-model families during the build.

## Step 11: documentation cleanup

Root documentation was reduced to:

- `README.md`
- `CHANGELOG.md`

Living documentation is under `docs/current/`; historical files are under `docs/archive/`.

## Step 12: release gate

The bounded release gate verifies source integrity, research readiness, worker/runtime contracts, Value Finder and deployment hygiene.

A browser preview smoke test remains an explicit final deployment gate because static/VM tests cannot prove DOM/browser integration.
