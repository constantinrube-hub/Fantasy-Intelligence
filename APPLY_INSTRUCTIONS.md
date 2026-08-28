# Apply V9.3.4A3

Base checked: `0daf3525074eef1c9075cef4019dcdcec64fa5cb`.

Copy the repository-path files from this package into the same paths on `main`:

- replace `app/current-snapshot-store.js`
- replace `app/v9.3.4a2-performance-hotfix.js`
- add `app/v9.3.4a3-score-performance.js`
- add `functions/api/data/nflverse/contracts.js`
- add `research/integrity_v934a3_test.py`
- add `.github/workflows/validate-fie-v934a3.yml`
- optionally add `docs/current/V9.3.4A3-SCORE-FIX.md`

Then run:

1. **Validate FIE V9.3.4A3**
2. **Refresh FIE current season**
3. Existing broader validation workflow
4. Wait for Cloudflare Pages deployment and hard-refresh the browser

Browser check after Genesis and Chopped enrichment:

```js
FIE934A3.report()
```

The combined A2 diagnostic also contains the A3 report:

```js
FIE934A2.report()
```

Verify `diagnostics.lastTotalMs`, `diagnostics.fallbacks === 0`, and that Public Data reaches `4/4` without a contracts 404.
