# FIE 9.3.4C Controlled-Implementation Handoff

## Status

Source release gate: **DEPLOYABLE_SOURCE**  
Production decision authority: **FIEDecisionService@9.3.2**  
Candidate decision coefficients: **FAIL-CLOSED / NOT PROMOTED**  
Current-feature activation: **league-scoped M6 + lineage governance**  
Required before production deployment: **served-browser preview smoke test**

These are separate concepts. The production app does not fall back to V8.9 merely because candidate coefficients are unpromoted. The canonical V9 decision route remains active, while candidate promotion stays fail-closed. A league may independently allow governed current features only when its M6/lineage gates pass. `FIE_DRAFT_V71` is compatibility fallback only if canonical V9 rows are unavailable.

## The one command to build a release

```bash
python tools/release_build.py --mode personal
```

This regenerates contracts/configuration, creates the source hash manifest, rebuilds `dist/`, and runs the bounded release gate.

Do not hand-edit `dist/`.

## What to upload

### GitHub + Cloudflare Pages

Upload/commit the **full repository**. Cloudflare serves `dist/` because `wrangler.toml` specifies:

```toml
pages_build_output_dir = "dist"
```

Keep `functions/` in the repository because the Pages API proxy is deployed from there.

### Manual static upload

Upload only the contents of `dist/`. This does **not** by itself deploy the Pages Functions proxy, so GitHub/Pages integration is preferred for the full app.

## Where to change things

| Change | Canonical owner |
|---|---|
| Add/change position aliases | `config/contracts/runtime-contracts.json` |
| Add/change roster slot eligibility | `config/contracts/runtime-contracts.json` |
| Add scoring rule support | `config/contracts/runtime-contracts.json` + source-field implementation |
| Change league-format resolution | `app/runtime-foundation.js` / `FIELeagueProfileResolver` |
| Change league loading/state | `app/runtime-foundation.js` / `FIELeagueController` |
| Add HTTP/API source | `app/core/data-client.js` and Cloudflare proxy allowlist if needed |
| Change lineup legality | `app/core/core-services.js` / `LineupOptimizer` |
| Change replacement logic | `app/core/core-services.js` / `ReplacementService` |
| Change roster marginal value | `app/core/core-services.js` / `RosterValueService` |
| Change production decision authority | `app/core/decision-service.js` + `config/model-config.json` |
| Change candidate decision coefficients/promotion | research validation → `config/model-config.json` |
| Add governed current research feature | Python research pipeline → `CurrentPlayerFeatures` bridge + league-scoped M6/lineage governance |
| Change current snapshot storage | `research/current_snapshot_storage.py`, `research/deduplicate_current_snapshots.py`, `app/current-snapshot-store.js` |
| Add D/ST | follow `docs/current/DST_INTEGRATION_GUIDE.md` |

## Rules that should not be broken

1. Do not add a second position map.
2. Do not add a second scoring-relevance map.
3. Do not add a feature-specific replacement formula.
4. Do not join new player data by display name.
5. Do not add raw `fetch()` in feature modules.
6. Do not add another `window.someFunction = wrapper(oldFunction)` patch layer.
7. Do not let candidate decision coefficients alter production recommendations without their promotion gate.
8. Do not let current research features bypass league-scoped lineage/M6 governance.
9. Do not deploy the repository root.
10. If current snapshots changed, run `python research/deduplicate_current_snapshots.py` before governance/release build.
11. Regenerate the final manifest after the last source/config change.
12. Run the served-browser preview check before production.

## Recommended post-upload verification

After pushing the repository:

1. Confirm Cloudflare is building/serving `dist/`.
2. Open the preview URL before production.
3. Load one Redraft league.
4. Load one Chopped league.
5. Load the Chopped + Best Ball hybrid league.
6. Switch formats quickly and verify no league-state bleed.
7. Open Draft Assistant and confirm the production authority status is coherent.
8. Open Value Finder and change filters repeatedly.
9. Run Monte Carlo, cancel it, then run it again.
10. Verify a 3RR draft's next-pick sequence.
11. Open a player report.
12. Open Research/Lab and verify research-only evidence is labelled separately from production authority.
13. Check mobile layout and primary Decision/Action visibility.
14. Confirm `/api/health` and one proxy-backed data request work.

## Documentation scope

This handoff reflects the production-authority and release-identity contract after Tranche 2C. Broader historical-document cleanup remains a later controlled documentation tranche.
