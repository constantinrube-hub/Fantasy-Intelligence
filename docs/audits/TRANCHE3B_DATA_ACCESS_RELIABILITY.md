# Tranche 3B — Data Access Reliability (C10-006)

Preflight target: `c96cbb4fb6df5f3383de5d4aa818817d9d84c3c3`
Preflight run: `33643778396`

## Proven baseline gaps

The preflight reproduced three controlled findings while keeping Tranche 3A closed:

1. DataClient in-flight coalescing was keyed only by request kind + URL.
2. Two callers with different AbortSignals could therefore share one promise, so aborting caller A rejected caller B.
3. ResearchReportService still owned a primary raw `fetch()` route instead of the canonical browser transport.

The existing delayed league A→B live-overlay abort guard passed and is preserved.

## Target implementation

### Scope-safe in-flight identity

`FIEDataClient` now keys in-flight cached requests by:

`request kind + URL + AbortSignal identity`

Consequences:

- identical requests in the same scope still coalesce;
- identical URLs in different scopes use separate in-flight requests;
- aborting one scope cannot reject a distinct scope;
- an already-aborted scope fails before snapshot/cache/network delivery;
- URL-only memory and persistent caches remain shared because completed payload identity is still URL-based.

### Canonical ResearchReportService transport

`FIEResearchReportService` now routes its JSON reads through `FIEDataClient.json` with:

- `cache: no-store`
- `persist: false`
- `sourceId: research-report`

This preserves the service's own league-scoped promise cache and network-fresh behavior while removing its independent raw browser transport.

## Explicitly unchanged

- league fast-switch snapshot architecture;
- live-overlay mutation and abort guard;
- persistent stable NFL proxy cache;
- current snapshot fallbacks;
- D/ST and kicker fallbacks;
- weekly-context fallback paths;
- football projections, replacement/scarcity/VOR and rankings;
- ADP boundary;
- research/statistical promotion gates;
- C10-007, C10-009 and C10-005.

## Required validation

The target workflow must prove:

- all Tranche 3A targets remain green;
- same-scope requests still coalesce;
- cross-scope requests no longer share abort propagation;
- league live-overlay race guard remains green;
- persistent cache behavior remains green;
- league fast-switch behavior remains green;
- ResearchReportService has no raw `fetch()`;
- direct-fetch allowlist target passes;
- later research-stage identity gap remains frozen;
- release gate remains `DEPLOYABLE_SOURCE`.
