# Tranche 7C-R8 — Corrected Lock and Operational Runner Design

## Sol decision

The green Tranche 7C-R7 artifact is preserved as evidence that real public-core data can build portable M9, M10-Linear, and M10-HGB point-model specifications. It is not eligible for activation or installation at the canonical 2026 season-lock path. Review found three contract gaps: training and inference do not share one feature owner, the team budget can follow a player across a team change, and the lock omits the residual distribution and provenance hashes required by the approved rollout design.

R8 therefore begins with a corrective lock target. Terra must not copy, stage, or schedule the R7 artifact. A corrected lock receives a new schema and hash and is first-written only after its controlled target is green and its artifact is independently verified. R7 remains closed validation history; this decision does not rewrite its artifact.

The rollout remains research-only. M9 remains champion. This design does not authorize 6F, shadow use, app or runtime integration, rank or recommendation changes, model selection, or production activation.

## R8A: shared time-safe feature owner

Create one repository module that is called by both historical training-row construction and prospective inference-row construction. It owns the three locked numeric features and emits an explicit row-identity manifest.

- `player_prior4_volume` and `player_prior4_efficiency` use the player's last four completed regular-season games before the target kickoff, with a minimum of two observations. Player history may cross a season or team change.
- `team_prior4_budget` is computed from team-game totals, grouped and rolled by canonical team rather than player. It uses the team's last four completed regular-season games before the target kickoff, with a minimum of two observations. The target row joins the budget for its target-week team, so an old team's budget can never follow a transferred player.
- The historical and prospective entry points must produce identical feature values for an identical as-of row. A frozen parity fixture must include a cross-season row, a team change, a negative yardage label, null features, and fewer-than-two-history cases.
- `season`, `week`, target kickoff, canonical player ID, position, team, and opponent remain identity or reconciliation fields. Team and opponent identifiers are never numeric predictors.
- Target-week outcomes, post-cutoff status, projections, ADP, market data, ranks, roster demand, replacement economics, and app recommendations are forbidden.

The input schema must retain deterministic row keys and the target-week team. Count labels remain finite and non-negative. Negative finite yardage labels are preserved. Null labels remain null and are excluded only for their target.

## R8A: residual-distribution contract

The corrected lock must support honest P10/P25/P50/P75/P90 forecasts without pretending that independently shifted raw components form a joint game simulation.

For every position and candidate, construct out-of-sample residual vectors from the same declared historical outer folds and the same shared eligible rows. A residual vector is the actual raw component vector minus the reconciled point-prediction vector for one row. Store the canonical residual sample table and its manifest hash in the lock; do not store only five independently estimated component quantiles.

At weekly scoring time, apply each frozen same-position, same-candidate residual vector to the player's reconciled point vector, then apply target-domain floors and within-player structural constraints (`completions <= attempts`, `receptions <= targets`). Score every resulting sample with the exact captured league profile and take empirical P10/P25/P50/P75/P90. The raw forecast row's default quantiles use the same process with the repository default-PPR scorer. These are player-level marginal score distributions, not coherent cross-player or team-level simulations; they must be labelled accordingly and cannot be combined as if they were joint samples.

Team-budget reconciliation applies to the point forecast across the full shared weekly universe before residual replay. Event and availability probabilities remain null with typed blockers. Chopped decisions may use the exact per-profile P10 marginal already required by the decision contract; no probability may be inferred from the quantiles.

## R8A: corrected season-lock schema and provenance

Use a new `fie-m10-prospective-season-lock-v2` schema. In addition to portable model specifications and their parameter hashes, it must contain or bind all of the following:

- training matrix and deterministic row-identity manifest hashes;
- feature-contract and target-contract hashes;
- source payload paths, releases when exposed, and hashes;
- dependency-lock hash;
- scorer hash;
- hashes for the shared feature builder, trainer, portable inference, reconciliation, and residual-calibration code;
- candidate configuration and rollout-design hashes;
- residual sample and residual manifest hashes; and
- explicit research-only governance, M9 champion, 2019–2025 training target seasons, and forbidden 2026 outcomes.

The validator must recompute every reachable hash, reject undeclared code or source drift, replay portable inference against independent probes within `1e-10`, validate residual row/fold identity, and prove that no 2026 outcome appears. Activation guard logic must accept only the corrected v2 lock for the 2026 operational path.

## R8B: governed weekly producer

Only after the corrected lock is green and installed by exact first-write may Terra implement the operational producer. The producer—not an external caller—must create the three inputs consumed by the closed 7C capture adapter.

Its scheduled path is:

`verified schedule + immutable public-core responses + governed identity + captured league/profile/roster state`

`→ shared as-of feature builder → frozen v2 inference for all three candidates`

`→ shared team-budget reconciliation → residual replay and exact profile scoring`

`→ immutable forecast, scoring-replay, and legal-choice decision records`

Every HTTP response used by the producer is written to a temporary source envelope before transformation with URL or source identity, observation time, provider revision/ETag/Last-Modified when exposed, and SHA-256. The final bundle commits those response hashes. Provider projection values are never read into the candidate matrix.

The candidate universe is shared across candidates. A player is eligible only with an unambiguous canonical identity, a scheduled QB/RB/WR/TE position, and enough information for the common feature builder and all portable candidates. Exclusions are typed and symmetric. A league decision trace is blocked if its captured legal roster cannot be mapped completely enough to construct every legal starting choice; it is never silently computed from a reduced easy subset. Raw forecast capture may still succeed when a league-specific decision is explicitly blocked.

The time policy remains unchanged: before the 18-hour window is a no-write success; inside the window, incomplete required football sources are retryable failures; after kickoff, the first verified attempt writes one permanent typed miss when no forecast won the first-write race. Forecasts are never reconstructed later.

## R8C: default-branch workflow

After R8A and R8B targeted contracts pass, add one operational workflow and one separate audit-branch controlled validator.

- The operational workflow is defined on the default branch, supports dispatch plus a three-hour schedule during January and September–December, and writes only when `github.ref == refs/heads/main`.
- It has `contents: write`, non-cancelling concurrency, and no deployment step.
- The runner builds and validates outputs outside tracked paths first. It then copies only first-write research records under `data/research/prospective/m10`.
- Before commit and again after fetch/rebase, it validates the exact changed-path allowlist. `app`, `functions`, `dist`, production config, ranks, recommendations, and current league snapshots are forbidden.
- A no-op creates no commit. A push race never force-pushes: the loser fetches/rebases once, validates an identical winning first-write when present, and otherwise fails closed.
- Outcome ingestion remains model-independent and append-only. A corrected provider payload creates a higher revision with parent and source-diff hashes; forecasts and prior revisions are immutable.
- The audit workflow uses no-network fixtures or explicitly bounded historical downloads, has read-only repository permission, writes only artifacts, and cannot activate the operational path.

## Validation order and clean boundaries

1. **R8A corrected-lock preflight:** shared feature parity, cross-team budget reset, residual methodology, provenance schema, and v1 rejection by the activation guard.
2. **R8A real-lock target:** build the v2 artifact from completed 2019–2025 evidence; targeted tests only during implementation.
3. Verify the artifact externally, then first-write the exact verified lock bytes to `data/research/prospective/m10/season-locks/2026/season-lock.json` in a separate closure commit.
4. **R8B producer target:** deterministic no-network weekly producer, all-profile replay, decision blockers, timing, and first-write behavior.
5. **R8C workflow target:** default-branch schedule, write/race/path controls, outcome revisions, and operational dry run.
6. Run one full personal release gate only when the combined R8 controlled target closes. If the previously recorded 22-profile production-governance hash drift recurs, report it as a separate pre-existing blocker; do not rewrite production snapshots in this tranche.

Each subtarget closes and returns its workflow to manual-only before proceeding. Merge of the fully green, closed R8 rollout to `main` remains the already authorized activation event. Until then no real prospective evidence may be written.

## Terra implementation boundary

Terra High is authorized to implement R8A only at the next step. It must preserve the R7 artifact, introduce the shared feature owner and v2 lock as additive research code, and use focused tests. It must stop for artifact verification after the real v2 lock target. R8B and R8C remain ordered follow-ons; neither permits app/runtime changes or M10 activation.
