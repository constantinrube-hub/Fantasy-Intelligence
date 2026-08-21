# Fantasy Intelligence Engine V7 — Cloudflare Deployment Package

## What this package fixes

1. **CORS / upstream reliability**
   - Browser requests for nflverse release assets now go to same-origin `/api/data/...` Pages Functions.
   - The Function performs the upstream GitHub/Sleeper fetch server-side.
   - The proxy is allowlisted, not an arbitrary open proxy.

2. **Daily Sleeper player-pool cache**
   - `/api/data/sleeper/players` caches the large active NFL player map for 24 hours at the Cloudflare edge.
   - The browser no longer downloads it directly from Sleeper on every fresh page load.

3. **Projection proxy/cache**
   - Sleeper season projections: 1 hour edge TTL.
   - Sleeper weekly projections: 15 minute edge TTL.
   - This also isolates the app from browser CORS behavior on the separate `api.sleeper.com` projection host.

4. **nflverse caching**
   - Stable/historical datasets use long TTLs.
   - 2026 live datasets use shorter TTLs.

5. **Source observability**
   - V7 has a Deployment Source Health panel.
   - It displays source success/failure, HTTP status, cache HIT/MISS, upstream identity and request latency.

## Project layout

- `index.html` — deployable V7 app
- `functions/api/data/[[path]].js` — allowlisted proxy/cache
- `functions/api/health.js` — proxy health endpoint
- `_routes.json` — invokes Functions only for `/api/*`
- `wrangler.toml` — Pages configuration

## Deployment

Cloudflare Pages Functions need the `functions/` directory at the root of the Pages project.

### Recommended: Git integration
Commit this entire folder to a repository and connect that repository to Cloudflare Pages.

For a plain static project:
- Framework preset: None
- Build command: leave empty
- Build output directory: `.`
- Root directory: repository root

### Wrangler
From this directory:

```bash
npx wrangler pages deploy .
```

Use the Pages project name when prompted or supply it using Wrangler's project-name option.

## Important

Cloudflare's dashboard Direct Upload workflow does not support Pages Functions. Use Git integration or Wrangler for this package.

## Staging checks

After deployment:

1. Open `/api/health`.
2. Load the app and your Sleeper league.
3. Open **Deployment Source Health**.
4. Confirm:
   - Cloudflare data proxy: OK
   - Sleeper player universe: OK, then HIT on a repeat load
   - Sleeper projections: OK
   - nflverse players/contracts/stats/snaps/depth: OK
5. Reload. The player universe should report a cache HIT within the 24-hour TTL.
6. Run Draft, Waivers, Trades, Team Analysis and Start/Sit.
7. Check mobile Safari and browser console/network errors.

## Cache design

- Sleeper player universe: 24h
- Historical nflverse data: 24h where appropriate
- Schedule / historical production: 6h
- Current 2026 nflverse weekly/depth/snap/team data: 1h
- Sleeper season projections: 1h
- Sleeper weekly projections: 15m

The Function returns `X-FIE-Cache`, `X-FIE-Source`, and `X-FIE-Fetched-At` headers for the app's health panel.
