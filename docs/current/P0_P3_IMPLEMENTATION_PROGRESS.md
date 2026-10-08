# P0–P3 implementation progress and next batches

Updated 8 October 2026. Authoritative scope: the user's filtered implementation plan of 7 October. M9 remains production champion. This is an implementation handoff, not a claim that P0–P3 are complete.

## Current boundary

The merged refresh → Window 1C → Window 1D chain is live-verified across all 23 leagues. The 8 October runs `37710615518` and `37710771825` verified the same input lineage, completed all workflow steps and published the four-checkpoint audit and seven-product coverage bundle. Offensive waiver eligible-row coverage remained zero; a successful job did not make those recommendations eligible.

The overnight batch adds operational reports, context integrity, independent projection evidence, a decision ledger, a declared P2 source inventory and bounded fixes to the existing draft worker. It is one coherent apply/push batch because report producers, their workflow wiring and their release registrations depend on one another. It does not contain a new football model, a new statistical method, a promotion or Sleeper execution.

## P0: operational continuity

| Work | State after this batch | Remaining acceptance work |
|---|---|---|
| Dynamic M10 fixture and rollover | Merged/live verified | Preserve through the next real rollover. |
| Ordered refresh/actions/waivers | Merged/live verified | Preserve all input/profile/source-dist guards. |
| Typed capabilities and lifecycle | Merged/live verified | Add explicit future lifecycle changes only from operator evidence. |
| M10/Sunday/PR2 deadline audit | Implemented and live verified | Observe due windows and terminal records; no retrospective reconstruction. |
| Availability/weather/trench audit | Merged/live verified | Merge and verify workflow summary; trench raw replay and weather accuracy remain separate. |
| Player performance | Merged/live verified; real Week 4 report | All 16 games/32 teams listed, 1,110 provider player-game rows; one unattributed row remains explicit. Official finality and snap/route coverage remain uncertified. |
| Exposure | Merged/live verified | Active owned/start exposure resolves 260 players; four league views retain unresolved-player gaps. The bundle binds immutable PR2 archives and displays existing direct-H2H contexts; new PR2 captures retain observed opponent starter IDs in the Sleeper namespace; canonical cross-league opponent aggregation and chopped-field exposure remain open. |
| Start/Sit and waivers | Existing owner outputs preserved | Full recommendation coverage depends on eligible projections/model evidence. |
| D/ST and kicker | Partial current owned/available boards | Validated multi-week hold/stream strategy remains absent; no new strategy is invented. |
| Post-week comparison | Stored PR2 source/scoring/evaluation replay adapter implemented | Real PR2 outcomes must accrue; paired FIE/Sleeper and M10 exact-scoring outcomes/comparisons remain required. |
| Seven-product contract | Explicit partial/not-due outputs | The adapter certifies zero complete products; full products need their own validators. |
| CI and deploy parity | Expanded focused tests/full closure gate | Post-merge workflow checks and browser smoke still required. |

### Next P0 batch

1. Observe the Thursday and Sunday prospective captures when due. Audit the original immutable evidence and exact league scope; record gaps with the original owner rather than constructing replacements.
2. Bind captured PR2 matchup evidence into portfolio exposure. Separate direct H2H from the chopped field; reuse the existing matchup/lineup owner.
3. Implement an approved real M10 outcome adapter: source identity, raw outcome hashes, complete exact-scoring fields and forecast-manifest lineage. The current synthetic outcome fixture is not a live outcome producer.
4. Add complete per-product validators only as each real report becomes complete. Do not promote a coverage index or a forecast board into a full report.
5. Verify one full post-merge weekly cycle, representative browser formats and mobile critical surfaces. P0 remains open until the real products and failure/no-op evidence satisfy its exit criteria.

## P1: projections and the decision core

| Work | Implemented now | Next step / required evidence |
|---|---|---|
| Independent projections | Stored FIE mean, baseline mean, delta, intervals, components, gating and null semantics | Add the same object to the app's agreed UI hierarchy; bind model/version where the current owner does not declare them. |
| Exact managed lineups | Existing approved PR2 owner retained | Capture lock/matchup scope, then run its real outcome evaluator. Floor/ceiling modes require complete interval evidence. |
| Decision ledger | Durable source-bound IDs and unchanged owner advice | Store separately captured actions/outcomes; retain unknown adoption/quality where timing or evidence is absent. |
| Explainability | Existing owner rationale/confidence preserved | Add approved drivers, alternatives and sensitivity from the same stored decision; no invented drivers. |
| Projection evaluation | Existing owner paths retained | Real paired prospective outcomes, declared metrics/slices and stable out-of-sample comparison. |
| Offensive waivers | Existing diagnostics and gates retained | Resolve exact source compatibility, retrain/revalidate the approved waiver-v2 target, then populate eligible forecast rows. Fixing an output label cannot manufacture model eligibility. |
| Chopped survival and FAAB | Not implemented by this batch | Required statistical/waiver-economics design handoff, full-field distributions, calibrated survival and observed auction evidence. |
| Promotion | Unchanged and blocked where evidence is absent | Predeclared incremental value, stability, decision impact and explicit governed promotion. |

### P1 implementation sequence

1. Bind versioned FIE forecast identity without replacing the independently displayed external baseline.
2. Finish the existing waiver-v2 source/scoring compatibility work under its approved contract. Keep missing attribution null and forecast/ranking/recommendation gates independent.
3. Produce real prospective eligible-row coverage and report it by position/profile; do not activate a model from the overnight source inventory.
4. Build automatic paired evaluation and decision regret from immutable forecast/lineup captures and exact outcomes.
5. Complete the Chopped design before implementation: full field, elimination threshold, calibrated survival, bid-clearing curves and FAAB opportunity cost. Never borrow a direct H2H opponent model.
6. Wire the same ledger/projection objects into Basic → Expanded → Advanced. Browser computation must not create a competing decision owner.

P1 exit remains independent FIE evidence, real automatic evaluation, stored/evaluated lineup and waiver decisions, survival-aware Chopped guidance and consistent explanations. This batch provides plumbing, not that exit.

## P2: context and research

`config/roadmap-research-registry.json` declares all nine P2 workstreams and their evidence/design prerequisites. `research/roadmap_research_inventory.py` hashes available owner modules. This is a source inventory, not research-completeness scoring or a statistical validation result. `config/weekly-usage-dictionary.json` documents supported provider fields and missing snaps/routes/alignment.

| Order | Workstream | Existing starting point | Required next implementation/result |
|---|---|---|---|
| 1 | Usage/opportunity | New raw player-performance owner | Canonical weekly table, explicit crosswalks, source-bound snaps/routes if obtainable. |
| 2 | Team opportunity | Existing trench/context owners | Approved coherent pace/pass-rate/EPA/usage priors; trench proxies remain research-only. |
| 3 | Red zone | Source feasibility/design still needed | Trips, conversion, player opportunities; no unvalidated TD correction. |
| 4 | Weather/rest | Existing prospective captures and context foundation | Realized validation dataset, approved incremental out-of-sample tests and stability. |
| 5 | Field position | Roadmap hypothesis only | Drive-start reasons, yard-line contract, descriptive outcomes and approved conditional analysis. |
| 6 | Role change | Usage history prerequisite | Approved persistence/minimum-opportunity/uncertainty rules and prospective evidence. |
| 7 | D/ST strategy | Existing D/ST forecast owner | Frozen preseason ranking, prospective availability and exact-scoring strategy comparison. |
| 8 | Kicker strategy | Existing kicker forecast owner | Immutable baseline, hold/stream comparison and evidence for added complexity. |
| 9 | Lab results/promotion | Existing Lab/runtime governance | Record historical and prospective results, negative findings, incremental value and decisions. |

Each result batch must preserve RAW → NORMALIZED → DERIVED → FORECAST → DECISION → OUTCOME → EVALUATION lineage. No P2 hypothesis enters production automatically. P2 is not complete until the formal results exist; neither module presence nor a declared `FEASIBLE` stage proves a predictive feature.

## P3: simulation, opponents and draft

The existing remaining-draft Monte Carlo worker has been hardened: strict null/zero handling, missing-material-input and duplicate-ID rejection, reproducible seeded tests, bounded batches, immediate run-bound errors, stale-job isolation and cancellation/timeout/load/clone cleanup. It still simulates the existing remaining-draft utility model. This is not a calibrated weekly NFL score simulator and must not be relabelled as one.

### Next P3 batches

1. Complete the approved design for calibrated weekly outcome distributions and empirical dependence. Block weekly win/survival claims when calibration or correlations are missing; do not invent Gaussian noise to fill the gap.
2. Reuse canonical slot assignment for score aggregation. Add direct H2H and chopped full-field simulation as distinct outputs with profile/season/week/source bindings and reproducible seeds.
3. Capture opponent submitted lineups and game-time evidence. Treat likely-lineup scenarios as scenarios; do not claim another manager's intentions.
4. Produce exposure/overlap/leverage and late-game path-to-win explanations from those same distribution and matchup objects.
5. Add the approved distributions to pre/live/post-draft analysis and future-board scenarios. Preserve 3RR, roster reconstruction, scoring isolation and cancellation.
6. Run format-specific and seeded/calibration/coverage tests, then one deterministic release closure, browser smoke and post-merge verification.

P3 exit requires calibrated reproducible correlated score distributions powering opponent/Chopped/draft decisions. The worker lifecycle fix is a bounded prerequisite, not phase completion.

## Batching and routing

The current combined branch should be applied to fresh main with the source-only helper, rebuilt and pushed once. No generated snapshots from the overnight environment should replace tomorrow's current snapshots. After merge, manually dispatch Window 1C and inspect its 1D follow-up: context states, performance replay/no-op, independent portfolio surface, partial/not-due product rows and durable ledger records.

Future model/result batches should be one coherent phase tranche each: a documented design, implementation, targeted checks and one full closure gate. Live evidence accrual and promotion cannot be compressed into an overnight code change.

The repository's `docs/audits/CODEX_MODEL_ROUTING.md` requires a clean handoff before new football-model architecture, statistical methodology, research-completeness scoring, cross-model reasoning or waiver-economics design. That boundary applies to the remaining new Chopped, P2 experiment and calibrated P3 designs. Existing approved owners were reused in this batch; no such new model design or promotion was performed.

P4 remains deferred. Standalone Vegas, college/college-to-NFL, IDP expansion and broad scoring-hardening workstreams remain outside the selected scope. Targeted compatibility fixes for the included pipeline remain allowed.

## 8 October daytime continuity batch

Runs 37773966120 and 37774336604 completed successfully. M10 Week 5 is CAPTURED_VALIDATED and the checkpoint audit is ON_TRACK. Current roster views in that 1D invocation rejected all 23 stale cores under their established six-hour freshness limit; pipeline success did not certify exposure availability. Refresh Currentseason, then Window 1C and its automatic Window 1D follow-up, is the recovery path. Tonight's PR2 evidence remains a separate real checkpoint.

The continuity batch adds explicit stale ages/limits/recovery instructions and read-only postgame PR2 revision replay through the existing source adapter, scoring owner and evaluator. It preserves blocked revisions, partial-product states and model authority. No real outcome is invented, no freshness threshold is relaxed, and no new evaluation method is introduced.

### Seven-product readiness diagnostics

The report bundle now records product-specific source coverage and blocking reasons without changing its seven incomplete product states. Week 4 player performance identifies 16 games, 32 team entries, 1,110 player-game rows, the single unattributed source row, uncertified official finality and missing snap/route source. Week 5 exposure separately reports captured H2H starters and blocked Chopped field scope. Waiver, lineups, D/ST, kicker and postweek outputs expose their own evidence counts and remaining certification gaps. This is P0 observability; the real product validators and prospective Week 5 captures remain outstanding.
