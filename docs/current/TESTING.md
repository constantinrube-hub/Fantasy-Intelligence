# Testing

## Test tiers

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

```bash
python research/release_gate.py
```

This is designed to remain bounded. Long empirical research jobs should not make deployability ambiguous.

### Deep research tests

M2-M6 empirical/historical validation can be substantially slower. Run them when research inputs/model logic change and in research workflows.

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
