# Current Repo + V8.9-VF2 Merge

## Exact base
This release was built on the user-uploaded repository:
- source archive: Fantasy-Intelligence-main (4).zip
- source SHA256: 19461567630a7729656bdbd7e9d091f9645500a45e685d339558cf5c86f2d2f7

## Verification of the current base
Compared with the earlier V8.9-RTS repository retained in the working session:
- application/research code outside data/: no differences;
- current league research/governance artifacts in data/: 38 differing files;
- those current data artifacts were preserved unchanged in the merged full release.

The uploaded repository does not contain an explicit V8.9.1 release marker. This merge therefore treats the uploaded archive itself, rather than a version label, as the authoritative current base.

## Added on top of the current base
- Draft → Value Finder.
- ADP 100–200 value-sleeper discovery.
- ADP 200+ snap-path-first deep-sleeper discovery.
- Top 100 Pick Optimizer.
- eligible-pool Sleeper market ranks, including Genesis hard eligibility.
- M5 preseason policy scoring independent of the M6 live activation gate.
- target windows and WATCH / WAIT / TARGET / TAKE NOW states.
- Top-100 value capture, reach cost, tier/replacement cost, opponent-adjusted survival, wait cost and 3-pick path proxy.
- Draft Assistant Value Finder / Target Plan integration.

## Governance
M6 production governance is unchanged and is not force-enabled.

## Tests
Passed:
1. integrity_v89_test.py
2. integrity_draft_rank_sort_test.py
3. integrity_multileague_test.py
4. integrity_decision_engines_test.py
5. integrity_m5_test.py
6. integrity_m6_test.py
7. integrity_custom_league_rules_test.py
8. integrity_portfolio_home_test.py
9. integrity_bulk_onboarding_test.py
10. integrity_value_finder_test.py
11. integrity_value_finder_runtime_test.js
12. integrity_top100_optimizer_runtime_test.js

Also passed:
- all external app JavaScript syntax checks;
- all six inline index.html script syntax checks;
- duplicate DOM id scan;
- Value Finder wiring checks.
