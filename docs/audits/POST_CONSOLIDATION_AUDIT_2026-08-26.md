# FIE 9.1 Post-Consolidation Audit

## Verdict

The consolidation source tree passes the bounded release gate and the broader fast integrity/runtime suite. It is suitable for a **preview deployment**. A real served-browser smoke test remains the final gate before production because this audit environment cannot verify the fully rendered Cloudflare preview in Chromium.

## Resolved deployment blockers

- stale build manifest: resolved through deterministic release build and final hash regeneration;
- wrong league-wide replacement comparator in V9: resolved through canonical `ReplacementService`;
- Monte Carlo loss of pre-existing rostered players: resolved;
- Monte Carlo starter/bench double counting: resolved;
- saved-league inactive-format mutation path: guarded by league identity and canonical switch controller;
- incomplete request race protection: centralized league abort scope added to compatibility data path;
- volatile Sleeper profile fingerprint: migrated to structural-v2 across 19 managed league namespaces;
- position/scoring semantics: centralized into generated runtime contracts;
- false generic READY semantics: repository and runtime activation statuses are now distinct;
- unpromoted V9 coefficients: fail-closed through generated model configuration and `FIEDecisionService`;
- approximate V9 roster marginal: canonical exact legal-lineup marginal available;
- Value Finder production model divergence: production Draft rows now come through `FIEDecisionService`;
- Value Finder research-feature governance bypass: production influence requires governance/activation;
- Cloudflare repository-root deployment: replaced with generated `dist/`;
- backup/cache release contamination: removed and release hygiene tested;
- secret-like URL diagnostics: centralized URL redaction in DataClient/Diagnostics;
- inconsistent release identity: canonical 9.1 release descriptor generated into client/functions/config;
- release workflow human-error risk: `tools/release_build.py` now owns build ordering;
- runtime compaction bug discovered during final handoff (`eligible` vs `positions`): fixed and covered by stronger dist integrity assertions.

## Validation results

### Bounded release gate

Status: **DEPLOYABLE_SOURCE**

The gate verifies:

- production/research artifact readiness;
- build manifest hashes;
- runtime foundations;
- league-switch race behavior;
- V9 fail-closed behavior;
- canonical DecisionService;
- structural profiles;
- release versions;
- dist hygiene and position-aware compaction;
- Monte Carlo worker invariants;
- decision engine integration;
- V8.9 integrity;
- M5/M6 integrity;
- scoring relevance;
- Value Finder and Top-100 runtime behavior;
- source artifact hygiene.

### Broader fast suite

All fast Python and Node integrity tests were run, excluding the deliberately long empirical M4 test. Every executed test passed. JavaScript syntax checking for `app/` and `functions/` passed.

### Not represented by DEPLOYABLE_SOURCE

A preview browser test is still required to prove:

- DOM binding behavior in the actual built site;
- Cloudflare Functions/proxy routing;
- browser Worker behavior;
- CacheStorage behavior;
- mobile rendering;
- network/CORS behavior from the deployed origin.

## Current runtime model state

The research artifacts are complete enough for the repository contract, but production research overlays remain fail-closed for the managed portfolio. This is expected and safer than silently promoting candidate V9 logic.

Safe state:

```text
RESEARCH_ARTIFACT_READY
RUNTIME_FALLBACK_ONLY
DEPLOYABLE_SOURCE
```

## Remaining architectural debt, non-blocking for preview

### 1. `index.html` remains a legacy monolith

It is still roughly 1.37 MB and contains historical definitions/wrappers of critical UI functions. The final effective league-loading path is canonicalized by the 9.1 runtime foundation, but source readability is still below the long-term target.

Commitment going forward:

- no new monkey-patch layers;
- extract legacy sections only behind stable service interfaces;
- do not combine D/ST integration with a risky wholesale UI rewrite.

### 2. Inline handlers remain

There are still legacy inline click handlers and many `innerHTML` render paths. Existing content generally escapes external text, but a future UI modernization should replace these with component/event helpers and enable a tighter CSP without `'unsafe-inline'`.

### 3. Research runtime payload is still larger than the ideal architecture

The corrected personal `dist/` is about 70 MiB. This is much safer than publishing the full source/research repository, but the long-term target remains:

```text
one global current-player feature snapshot
+
small league-specific policy/scoring overlays
```

rather than repeated league current snapshots.

### 4. Full empirical M4 validation is deliberately outside the fast release gate

Deep empirical validation should remain a separate research-tier CI job with its own timeout/status rather than making app deployability ambiguous.

### 5. Production V9 promotion is not yet earned

The candidate architecture exists; model promotion remains a research task. Do not confuse the 9.1 code release with evidence that V9 beats the governed fallback or Sleeper.

## D/ST readiness

The foundation is ready for D/ST integration because D/ST can now reuse:

- canonical position/slot registry;
- canonical scoring registry;
- league demand/replacement;
- exact lineup optimizer;
- roster marginal value;
- production decision gateway;
- research/governance contracts.

The D/ST project should add its domain-specific data/projection research, not another parallel application architecture.
