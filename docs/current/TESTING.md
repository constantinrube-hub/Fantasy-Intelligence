# Testing

## Test tiers

### Repository lifecycle and release checks before merge

Every pull request runs `Validate FIE V9.3.2 Browser QA`, without a path filter.
Its fast `repository-lifecycle` job checks the full documentation/workflow tree
before the dependent deterministic release build. New files cannot silently
bypass the check. Review both jobs before merging; branch protection must require
them if GitHub should enforce this mechanically.

When adding, renaming, deleting or changing workflow triggers, update
`config/repository-lifecycle-contract.json` in the same PR. Scheduled workflows
must match `scheduled_workflows`, completion triggers must match
`completion_triggered_workflows`, and every `.yml`/`.yaml` workflow must have an
explicit classification. The registry is intentionally strict.

```powershell
python research/integrity_tranche5c_documentation_lifecycle.py --mode target
python research/integrity_repository_lifecycle_regression_test.py
python tools/release_build.py --mode personal
```

The regression suite mutates isolated copies to prove that an unregistered
schedule, a removed/renamed registration, an unclassified file, a changed
completion trigger and a missing canonical document are rejected. A workflow
and its correct new registration pass together. Refresh Current runs the same
lifecycle check immediately after checking out latest `main`, before dependency
installation or snapshot rebuilding, and retains the full final release gate.

### Fast source/runtime tests

Run on every code change. Important examples:

```bash
node research/integrity_runtime_foundation_test.js
node research/integrity_league_switch_runtime_test.js
node research/integrity_v9_model_runtime_test.js
node research/integrity_monte_carlo_worker_test.js
node research/integrity_value_finder_runtime_test.js
node research/integrity_top100_optimizer_runtime_test.js
python research/integrity_scoring_relevance_test.py
python research/integrity_decision_engines_test.py
python research/integrity_current_storage_test.py
python research/integrity_dist_hygiene_test.py
```

### Bounded release gate

The weekly pipeline independently refits frozen waiver artifacts and compares
the original diagnostics. Install `research/requirements-replay.txt` for this
replay: it retains the research dependencies and pins NumPy 2.3.5, pandas 2.2.3
and SciPy 1.17.0. CI uses that file for installation and its cache key, with the
existing single-threaded Sandybridge OpenBLAS path. Dependency-file changes
trigger weekly pipeline validation. The general research requirements remain
available for other workflows.

An open-ended numerical dependency upgrade can preserve predictions within
floating-point tolerance while changing the order of near-tied values and
therefore an exact rank diagnostic. Treat a replay failure as a failure; do not
restamp frozen research or relax tolerances to accommodate a new environment.
Validate an intentional numerical-stack upgrade separately against every frozen
unit before changing the replay pins.

```bash
python research/release_gate.py
```

This is designed to remain bounded. Long empirical research jobs should not make deployability ambiguous.

### Deep research tests

M2-M6 empirical/historical validation can be substantially slower. Run them when research inputs/model logic change and in research workflows.

## Browser replay suite (UI contract)

`research/ui_replay/` runs the real built application in headless Chromium against
**immutable, already-committed provider captures**, with a frozen browser clock. It is
the deterministic browser layer between VM tests and the manual preview pass.

```bash
python tools/release_build.py --mode personal          # builds dist/
node research/ui_replay/run.js --dist dist --suite classic --out ui-replay-output
node research/ui_replay/run.js --dist dist --suite v10 --out ui-replay-output
node research/ui_replay/run.js --only C-WEEK,C-BANNER  # selected checks
```

- Requires Node 22 and Playwright with Chromium (`npm install --no-save playwright && npx playwright install chromium`;
  set `FIE_UI_PLAYWRIGHT` to a Playwright module path if it is installed elsewhere).
- Fixtures (`research/ui_replay/fixtures.js`) read the receipts of
  `data/research/prospective/weekly-sources/2026/week_06/20261015T174631408136Z/`
  (Week 6, ~6.5 h before the first kickoff: 23 leagues' league/rosters/users/matchups/transactions,
  Sleeper players and Week 6 projections, nflverse players/schedule/weekly/snaps). Season projections are
  rebuilt from `data/research/market/sleeper/2026/season_market_2026-09-30.jsonl.gz`.
- Scenarios (`scenarios.js`): `w6-pregame` (Thu 18:00 UTC), `w6-after-tnf` (Sat 12:00 UTC),
  `live-week-ahead` (provider one week ahead of the bundled snapshot). Overrides may change provider
  payloads only; tests never assign application state (`integrity_ui_replay_no_injection_test.js`).
- Requests not covered by the capture are aborted and listed in the report (`unmatched`).
- Output: `report.json` plus screenshots in the output folder (git-ignored).

| Check | Contract |
|---|---|
| C-LOAD | reference leagues load; Weekly/Waivers render with no page error |
| C-WEEK | live Sleeper week wins over the snapshot week; notice shown |
| C-WAIVER | no CLAIM for Doubtful/Out/IR/…; status column; unavailable adds below CLAIMs |
| C-DRAFT | no draft-preparation task for in-season leagues |
| C-BANNER | submitted starter who cannot play → red Weekly alert |
| C-NOBYE | a Rams starter (nflverse `LA` / Sleeper `LAR`) is not reported as a bye |
| C-OVERLAY | Weekly keeps Sleeper week projections after the live roster overlay (4 timings sampled) |
| C-IRSTART | the Weekly lineup never starts a reserve (IR) or taxi player |
| C-OUTSTART | the Weekly lineup never starts a player who cannot play (Out/IR/PUP/SUS/NA; Doubtful = Out) |
| C-REFRESH | "Refresh weekly context" runs without a page error |
| V-OVERVIEW | (v10) every league listed; urgent tasks per league; no in-season draft task; no Best Ball lineup task |
| V-CONSISTENCY | (v10) Overview row = League Home = Lineup = Matchup; best lineup = classic optimum |
| V-LINEUP | (v10) suggestion with tier, Questionable caveat + fallback, Sleeper link; Expand/Advanced layering |
| V-AFTER-TNF | (v10) locked players marked and never part of a suggestion |
| V-CHOPPED | (v10) only active teams, verified eliminations, cut margin, no H2H estimate |
| V-SWITCH | (v10) A → B → A shows the visible league; `?ui=classic` restores classic |
| V-BRIDGE | (v10) Trades/Draft/Lab (and the old Waivers route) open classic for the same league; pill returns |
| V-WAIVERS | (v10, Tuesday scenario) best adds by lineup gain with legal drop, ≤ 3 per position, no CLAIM/bid in Basic, market + budgets |
| V-REVIEW | (v10) Week 5 review: submitted ≤ hindsight, projection-best ≤ hindsight |
| V-WEEKPICK | (v10) past → review, future → projections, live → normal lineup |
| V-READER | (v10) reader from a name, pin two, compare with lineup impact |
| V-FEED | (v10) second visit lists status changes; My players counts |

The v10 checks open `/?ui=v10#…`; run them with `--suite v10`. Scenario `w7-tuesday` (R2) uses the Sunday
Week 7 capture with Thursday's Week 6 capture as fallback (processed FAAB claims), the frozen Thursday projections
for past weeks (`data/research/market/sleeper/2026/week_NN.jsonl.gz`), and a **test fixture** for a scored Week 5
(lineups from the Tuesday-after-Week-5 capture, points rebuilt from real nflverse stats, D/ST = 0) until WP-T2
captures post-week matchups. Pure-module contracts of the v10 core run without a
browser: `node research/integrity_v10_core_test.js` (release gate).

## Mandatory preview browser test

Static/VM testing cannot prove real browser behavior.

After building `dist/`, deploy a Cloudflare preview and verify:

1. cold open;
2. warm cached open;
3. load Redraft;
4. load Chopped;
5. rapid A → B → A switch;
6. edit saved B while A remains active;
7. Draft Assistant;
8. 3RR sequence;
9. Value Finder;
10. Monte Carlo run and cancellation;
11. player drawer keyboard access;
12. Lab states;
13. mobile viewport;
14. switch between two leagues with different scoring and verify M5/D/ST/Kicker rows hydrate correctly from shared current storage.

This preview pass is the final production gate.
