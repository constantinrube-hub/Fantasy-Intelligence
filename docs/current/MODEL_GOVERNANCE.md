# Model Governance

## Principle

Research evidence and production permission are separate.

A feature or candidate model may be visible diagnostically without altering a live recommendation.

## Production layers

### Baseline/fallback

The currently governed production fallback remains available whenever research/model activation closes.

### Research M1-M6

League-specific artifacts are namespaced and validated against:

- league identity;
- scoring signature;
- structural profile fingerprint;
- temporal/leakage rules;
- freshness;
- decision-specific promotion gates.

### V9 decision candidate

V9.1 is fail-closed through `config/model-config.json`.

`FIEModelV9.buildDraftValueRows()` returns production rows only when the generated configuration is promoted.

`buildDiagnosticRows()` may still be used for Lab/player-report evaluation.

## Current-player feature permission

A research current feature may alter a production decision only if all required conditions are true:

```text
leakage safe
+ player activation eligible
+ league M6 governance runtime enabled
+ global browser governance allow
+ domain-specific eligibility
```

Otherwise it is explanation/diagnostic evidence only.

## Readiness vocabulary

Use these terms consistently:

- `RESEARCH_ARTIFACT_READY`
- `RUNTIME_FALLBACK_ONLY`
- `RUNTIME_RESEARCH_ACTIVE`
- `DEPLOYABLE_SOURCE`
- final browser-preview PASS

Do not use a generic READY label for all of them.
