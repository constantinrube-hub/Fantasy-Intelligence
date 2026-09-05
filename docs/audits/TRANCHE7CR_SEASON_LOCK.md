# Tranche 7C-R1 — Portable 2026 Season Lock

This bounded Terra implementation is the first step of the user-authorized 7C-R rollout design. It creates an offline, first-write immutable 2026 research season lock from an explicit historical training matrix. It does not request providers, schedule a job, write prospective evidence, alter the app, alter runtime behavior, activate a model, or authorize 6F.

The lock admits only 2019–2025 outcome targets. It exports M9 (Ridge alpha 10), M10-Linear (Ridge alpha 6), and the locked two-member M10-HGB ladder for QB/RB/WR/TE. The final HGB candidate is selected using the 2025 inner holdout and then refit through 2025. Count-target Poisson use remains guarded by a positive eligible target sum.

Model parameters are canonical JSON only. Ridge uses ordered median/imputer/scaler/coefficient data; HGB uses the repository-owned `fie-hgb-tree-v1` numeric-tree format, including its loss inverse-link (`exp` for Poisson and identity otherwise). No pickle is emitted or read. The validator checks lock and parameter hashes, immutable first-write behavior, governance flags, and portable HGB probe equality against the exported scikit-learn predictions to `1e-10`.

The controlled target is `config/tranche7cr-season-lock-target.json` and its temporary push validator is `.github/workflows/validate-fie-tranche7cr-season-lock.yml`. Its sole release gate remains the canonical personal build. Closure will return the validator to manual-only and record the resulting artifact before the next separately bounded source-bundle increment.
