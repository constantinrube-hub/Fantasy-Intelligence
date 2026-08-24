# Fantasy Intelligence Engine V8.9-RTS

V8.9-RTS is the ready-to-deploy integrity release built from the V8.8-M6 repository.

## What changed

The release focuses on making displayed numbers mean what they claim to mean:

- explicit league-scoring coverage instead of silent partial scoring,
- rollover-safe current/prior season data routing,
- one replacement-rank convention with lineup-derived FLEX/Superflex/IDP demand,
- chronological out-of-time calibration and feature gates,
- empirical residual uncertainty before heuristic fallback bands,
- nonlinear market-value edge,
- empirical saved-draft survival frequencies when sufficiently sampled,
- probabilistic future-pick slot priors instead of using the current rookie class,
- format-specific Redraft/Dynasty/Best Ball/Chopped roster utility,
- stronger temporal block-bootstrap promotion rules,
- and independent browser SHA-256 verification of governed research artifacts.

## Important fail-closed behavior

The repository's checked-in empirical milestones are still `pipeline_ready_not_run`. V8.9 therefore deploys on the corrected fallback engine and **does not fabricate a green research state**.

The M5/M6 layer can activate only after the repository workflows generate complete compatible artifacts and the current-season snapshot passes governance.

## Files to deploy

Deploy the whole repository tree, not only `index.html`. See `DEPLOYMENT_GUIDE_V8_9_RTS.md`.

## Validation

See `V8_9_RTS_IMPLEMENTATION_AUDIT.md` and `V8_9_RTS_CHANGELOG.md` for the full implementation and test record.
