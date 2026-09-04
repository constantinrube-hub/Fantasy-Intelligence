# Tranche 5C Preflight — Documentation and Lifecycle Reconciliation

## Purpose

This characterization-only package freezes the current documentation and GitHub workflow lifecycle before consolidation. It changes no browser behavior, football calculation, research artifact, governance decision, or scheduled data operation.

## Current documentation state

The repository has a useful canonical core in `README.md`, `CHANGELOG.md`, and `docs/current/`. However, active guidance is mixed with numerous version-specific implementation notes, upload instructions, patch manifests, and release notes. Several version-specific files still live in the repository root or in `docs/current/`, so a reader cannot determine lifecycle state from location alone.

The audit also has no explicit Tranche 4 disposition. This is a traceability gap only; the preflight does not infer whether the number was reserved, absorbed, or intentionally omitted.

## Current workflow state

Scheduled current-season and market-capture workflows are operational responsibilities and must remain active. Completed controlled-tranche validators should retain their permanent checks but should not continue producing automatic branch noise after a successor tranche closes them. Older release and research workflows require classification before any trigger is changed or file is retired.

## Target boundary

The later target may establish one machine-readable lifecycle registry, reconcile the canonical documentation index, explicitly record Tranche 4's disposition, and classify workflows as active operational, active validation, manual historical validation, superseded, or archived.

No document or workflow is deleted in preflight. Any later retirement requires producer/consumer evidence, preservation of useful validation, and proof that scheduled operational behavior is unaffected.

## Preflight success condition

The dedicated workflow must reproduce the lifecycle gap, preserve Tranches 2A through 5B, retain all scheduled workflows, produce `DEPLOYABLE_SOURCE`, and create no runtime or generated drift.
