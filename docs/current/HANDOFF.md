# FIE 9.1 Consolidation Handoff

## Status

Source release gate: **DEPLOYABLE_SOURCE**  
Research state: **RESEARCH_ARTIFACT_READY / RUNTIME_FALLBACK_ONLY**  
Required before production promotion: **served-browser preview smoke test**

`RUNTIME_FALLBACK_ONLY` is deliberate. V9 candidate logic remains fail-closed until an empirically promoted model configuration authorizes it.

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
| Change production decision source | `app/core/decision-service.js` + governed model config |
| Add current research feature | Python research pipeline → `CurrentPlayerFeatures` bridge |
| Promote new model coefficients | research validation → `config/model-config.json`, never client hard-code alone |
| Add D/ST | follow `docs/current/DST_INTEGRATION_GUIDE.md` |

## Rules that should not be broken

1. Do not add a second position map.
2. Do not add a second scoring-relevance map.
3. Do not add a feature-specific replacement formula.
4. Do not join new player data by display name.
5. Do not add raw `fetch()` in feature modules.
6. Do not add another `window.someFunction = wrapper(oldFunction)` patch layer.
7. Do not let candidate research/model code alter production recommendations without governance.
8. Do not deploy the repository root.
9. Regenerate the final manifest after the last source/config change.
10. Run the served-browser preview check before production.

## Recommended post-upload verification

After pushing the repository:

1. Confirm Cloudflare is building/serving `dist/`.
2. Open the preview URL before production.
3. Load one Redraft league.
4. Load one Chopped league.
5. Switch Redraft → Chopped → Redraft quickly.
6. Verify saved-league format labels do not bleed between leagues.
7. Open Draft Assistant.
8. Open Value Finder and change filters repeatedly.
9. Run Monte Carlo, cancel it, then run it again.
10. Verify a 3RR draft's next-pick sequence.
11. Open a player report.
12. Open Lab and confirm research status is described as loaded/fallback rather than unavailable.
13. Check mobile layout.
14. Confirm `/api/health` and one proxy-backed data request work.

## D/ST handoff

The D/ST research project can now be integrated without inventing new infrastructure. Add team-DST entities and scoring/data features to the canonical registries and projection layer, then let the existing replacement/lineup/decision services consume them.
