# FIE V8.7-M5: Steps 24–27

Milestone 5 is the decision-integration layer built on M1–M4.

## Included

- `index.html`: V8.7-M5 app with `Lab → M5 Decisions` and fail-closed runtime integration.
- `research/fie_m5.py`: Steps 24–27 historical decision-policy research.
- `research/validate_m5_bundle.py`: schema and activation guardrails.
- `research/integrity_m5_test.py`: deterministic format-policy integrity checks.
- `data/research/milestone5.json`: deliberately inactive placeholder until empirical M1→M5 research is run.
- `data/research/current/milestone5_current.json`: deliberately inactive current-season placeholder; automatic generation belongs to Step 29.
- updated manual research workflow capable of rebuilding Milestones 1–5.
- inherited M1–M4 research code, bundles/placeholders and documentation.

## Decision behavior

M5 never replaces the existing live path globally.

The browser first calculates V8.2.2 as before. M5 then evaluates separate gates for:

- Weekly mean projection,
- Weekly risk bands,
- Draft policy,
- Waiver policy,
- active league-format transform.

Only the component whose gate passes can be overwritten. Everything else retains the previously calculated V8.2.2 value.

## Why the current snapshot is empty

Steps 24–27 define and validate the decision policies. Roadmap Step 29 is responsible for automatically creating current-season player inputs from live data and the validated model specifications. Keeping the M5 current snapshot inactive prevents a research milestone from pretending it already has a production-grade current data pipeline.

## Next roadmap block

Steps 28–30:

- advanced second-wave research,
- current-season automation,
- permanent model governance/versioning/rollback.

Detailed deployment instructions are intentionally deferred until those steps are complete.
