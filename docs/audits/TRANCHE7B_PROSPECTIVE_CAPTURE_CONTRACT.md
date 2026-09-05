# Tranche 7B — Deterministic Prospective-Capture Contract

## Boundary

This Terra tranche implements the 7A storage and validation contract with synthetic, no-network fixtures only. It creates no scheduled workflow, provider request, live prediction, app artifact, runtime writer, ranking change, recommendation change, model selection, shadow integration, or production activation. M9 remains the production model.

The active target contract is `config/tranche7b-prospective-capture-contract-preflight.json`. Its source design is fixed at `3314828cc0020c4528f6b9b7d8828c6bebd48bb8`.

## Implemented contract

- `research/m10_prospective_capture_contract.py` owns deterministic gzip JSONL ledgers and their shared validation rules.
- `research/build_m10_prospective_capture.py` permits `--fixture` only. Any attempted non-fixture invocation stops with the explicit 7C boundary.
- `research/validate_m10_prospective_capture.py` requires exactly one immutable capture or typed missed-capture record per week.
- `research/integrity_m10_prospective_capture_test.py` verifies first-write idempotence, paired M9/M10-Linear/M10-HGB rows, late-window rejection, missed-window preservation, and separate append-only synthetic outcomes.

The fixture has QB/RB/WR/TE rows for all three locked candidates, two synthetic scoring profiles, and research-only decision traces. It proves serialization and preservation behavior; it is not football evidence and is not representative of the 22 enabled leagues.

## Data invariants

Forecasts, scoring replay, decision traces, and outcomes have separate namespaces. A forecast contains no realized outcome fields. Outcomes require an existing forecast and append under an explicit revision directory. A missed capture and a forecast are mutually exclusive for the same season and week.

The capture manifest requires a verified zero-to-18-hour lead time, schedule hash, source/model hashes, all positions, all candidates, and disabled production/shadow flags. The validator rejects a missing candidate row, unpaired row set, profile identity omission, or drift from the immutable ledger hashes.

## Validation lifecycle

The controlled 7B workflow runs focused fixture and integrity checks, preserves 6B–6E closures, then performs its single release gate. Its generated synchronization must remain limited to `config/build-manifest.json`, `config/release-gate.json`, and `dist/config/build-manifest.json`.

The target validated successfully at `0b120fd652a142372a221240381acfa47c40a238` in GitHub Actions run `33960545413` (50 seconds, `DEPLOYABLE_SOURCE`). Its release artifact SHA-256 is `eb2c764ed9f11244ae14b08d67b904fbbd2f20f6258aa3975d0e1be06c211af4`; the verified fixture capture manifest SHA-256 is `67b52ebfd86770ccbebf873c3919eb84addf5f91e8b09a6f7b047ba2142762a2b`. Generated synchronization is limited to `config/build-manifest.json`, `config/release-gate.json`, and `dist/config/build-manifest.json`.

The workflow has returned to manual-only. Only then may 7C connect this contract to real time-safe inputs; recurring scheduled rollout remains a separate explicit boundary.
