# Tranche 7C — Audit-Branch Operational Prospective Collection

## Boundary

Tranche 7C connects the closed 7B ledger to an explicit time-safe input bundle on the audit branch. It does not request provider data, enable a schedule, construct a forecast from a current endpoint, modify the app, select a model, create a 6F shadow namespace, or alter M9 production behavior.

The source input bundle is required to contain three independently hashed records captured no later than the weekly cutoff: paired candidate forecast rows, a profile snapshot, and research-only decision inputs. A missing bundle blocks the run; it is never replaced with current data or a reconstructed historical prediction.

## Operational adapter

`research/m10_prospective_operational_capture.py` validates the bundle, requires a zero-to-18-hour first-kickoff lead time, checks all locked M9/M10-Linear/M10-HGB QB/RB/WR/TE pairs, then writes the established first-write ledger. Its non-fixture validator rejects synthetic 7B payloads.

Every real profile must match the current enabled registry exactly by league ID, scoring signature, and profile fingerprint. The adapter invokes the existing canonical football scorer for each candidate row and profile, rather than a default-PPR fallback. Its decision input requires the same legal choice set for every compared candidate. Outcomes are separate, append-only revision-1 inputs and cannot exist without the immutable forecast.

The target fixture exercises this adapter without a network request. It is engineering validation only, not prospective football evidence. The absent current-week bundle on this audit branch is an explicit operational block, not permission to make a late capture.

## Lifecycle

The controlled 7C target validates the no-network fixture, canonical scorer import, input hashing, profile replay, decision trace, outcome separation, and all closed 6B–7B contracts before its single release gate. It does not create or change any operational scheduler.

After artifact verification, the controlled validator returns to manual-only. A later 7C rollout decision is required before a default-branch schedule can write real evidence; that rollout remains separate from any model or promotion decision.
