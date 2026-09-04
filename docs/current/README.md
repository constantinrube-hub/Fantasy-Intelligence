# Current Documentation

This directory contains the current operational and architectural documentation for Fantasy Intelligence. When a version-specific note conflicts with a topic guide below, the topic guide is authoritative.

## Canonical guides

- [`../../README.md`](../../README.md) — repository entry point and quick start
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — chronological change history
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — runtime ownership and service boundaries
- [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) — generated, research, and runtime data contracts
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — current build and Cloudflare deployment procedure
- [`MODEL_GOVERNANCE.md`](MODEL_GOVERNANCE.md) — promotion and fail-closed behavior
- [`TESTING.md`](TESTING.md) — validation tiers and release gates
- [`SECURITY.md`](SECURITY.md) — security and privacy posture
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — release operator checklist

## Historical references

Files in this directory whose names begin with a version number document specific implementation or repair events. They remain useful evidence, but they are not current operating instructions. Root-level patch, upload, apply, and versioned release-note files have the same historical status pending the later evidence-backed archive cleanup.

Repository-wide lifecycle rules are machine-readable in [`../../config/repository-lifecycle-contract.json`](../../config/repository-lifecycle-contract.json).
