# Fantasy Intelligence Audit Instructions

Read [`docs/audits/AUDIT_CURRENT_STATE.md`](docs/audits/AUDIT_CURRENT_STATE.md) first. Treat completed tranche contracts as established facts; do not rediscover or re-audit closed architecture unless a preservation test fails or the current task changes that ownership boundary.

Use [`docs/audits/CODEX_MODEL_ROUTING.md`](docs/audits/CODEX_MODEL_ROUTING.md) at every new tranche boundary. Prefer targeted tests during implementation, one deterministic release gate at tranche closure, and detailed CI-log inspection only after failure.

Do not delete, archive, relocate, or retire a file or workflow solely because it appears old. Preserve the frozen PRE-audit baseline and all fail-closed, league-specific, canonical-identity, source/dist, and governance contracts.
