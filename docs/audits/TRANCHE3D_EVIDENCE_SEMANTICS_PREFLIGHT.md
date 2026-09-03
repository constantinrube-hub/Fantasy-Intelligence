# Tranche 3D Preflight — Evidence Semantics

## Purpose

This is the characterization-only preflight for **C10-009 EVIDENCE_SEMANTICS**.

It is intentionally combined with the exact generated synchronization emitted by
the successful Tranche 3C target run at commit
`406608787b5930e510730fbb2ab5bfba0a089ae8`.

No football-model, ranking, confidence, uncertainty, fallback, specialist, ADP,
league-profile, governance, or identity behavior is changed by this package.

## Tranche 3C closure carried in this package

Exact generated files from successful run `33781298841`, artifact `9903687758`:

- `config/build-manifest.json`
- `config/release-gate.json`
- `dist/config/build-manifest.json`

The 3C target run already proved:

- canonical PlayerIdentity ownership
- offense / IDP / D/ST / K crosswalk and ambiguity handling
- fail-closed ambiguous current-feature joins
- browser/Python current-snapshot identity parity
- Value Finder identity joins without display-name fallback
- D/ST and kicker integrity
- preservation of Tranches 2A–2C, 3A and 3B
- `DEPLOYABLE_SOURCE`

## C10-009 audited baseline

The repository already contains several good semantics:

- unavailable projection data is distinct from a real numeric zero
- verified byes may resolve to a true zero
- source and confidence labels exist
- calibrated empirical intervals are distinguishable from heuristic ranges in
  the canonical projection resolver
- D/ST and kicker surfaces label baseline/future estimates
- current-feature lineage carries its own freshness information

The remaining audited problem is **semantic fragmentation**.

Examples characterized by this preflight:

1. `app/core/projection-service.js` can fall back from a season projection to a
   weekly estimate using `seasonV / 17`, but there is no shared typed uncertainty
   classification propagated across every surface.
2. Projection, current-feature, current-snapshot, D/ST and kicker freshness /
   provenance are represented with different local fields and labels.
3. D/ST and kicker maintain local source/range/estimate semantics rather than
   consuming one canonical EvidenceStatus object.
4. Generic words such as `confidence`, `status`, `source` and `estimate` do not
   by themselves constitute the shared typed evidence contract required by
   C10-009.

Expected preflight marker:

`KNOWN_GAP_REPRODUCED evidence semantics are fragmented across projection and specialist surfaces`

## Frozen target for the later 3D implementation

The target implementation will introduce one typed evidence-status model that
can carry, without collapsing meanings:

- source
- as-of / freshness
- confidence
- reason
- fallback reason
- availability
- bye state
- uncertainty kind: calibrated / heuristic / exact / unavailable
- league-local provenance

It must preserve:

- league-specific decisions
- ADP outside the football model
- fail-closed research governance
- real-zero versus unavailable/null semantics
- verified-bye versus unknown-schedule semantics
- C10-007 canonical PlayerIdentity
- C10-006 scope-safe transport
- C10-004 replacement/scarcity/VOR ownership

## Scope boundary

This preflight does **not**:

- add or change model inputs
- alter rankings
- alter projection values
- recalibrate intervals
- change D/ST or kicker scores
- change ADP handling
- change research promotion gates
- resolve the separate unified research-stage provenance gap
- delete or archive any file
