# Tranche 7C-R1 — Portable 2026 Season Lock

This bounded Terra implementation is the first step of the user-authorized 7C-R rollout design. It creates an offline, first-write immutable 2026 research season lock from an explicit historical training matrix. It does not request providers, schedule a job, write prospective evidence, alter the app, alter runtime behavior, activate a model, or authorize 6F.

The lock admits only 2019–2025 outcome targets. It exports M9 (Ridge alpha 10), M10-Linear (Ridge alpha 6), and the locked two-member M10-HGB ladder for QB/RB/WR/TE. The final HGB candidate is selected using the 2025 inner holdout and then refit through 2025. Count-target Poisson use remains guarded by a positive eligible target sum.

Model parameters are canonical JSON only. Ridge uses ordered median/imputer/scaler/coefficient data; HGB uses the repository-owned `fie-hgb-tree-v1` numeric-tree format, including its loss inverse-link (`exp` for Poisson and identity otherwise). No pickle is emitted or read. The validator checks lock and parameter hashes, immutable first-write behavior, governance flags, and portable HGB probe equality against the exported scikit-learn predictions to `1e-10`.

The controlled target passed at `8d34c04c6f768f12abe3bd128c0ab68c06f4bc18` in GitHub Actions run `33964009179` (1m 4s), with `DEPLOYABLE_SOURCE`. Its verified archive SHA-256 is `da28b8c410be591fb1e1a318d2ce82c08569b570a76623c9561fcf2162509e86`; the generated synchronization was restricted to the established three files. The temporary push validator is now manual-only. The next source-bundle component remains separately bounded.
