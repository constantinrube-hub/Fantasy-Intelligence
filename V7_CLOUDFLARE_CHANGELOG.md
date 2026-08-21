# V7 Cloudflare Infrastructure Changelog

- Replaced direct browser nflverse GitHub release fetches with same-origin `/api/data/nflverse/*` routes.
- Replaced direct Sleeper projection fetches with `/api/data/sleeper/projections/*`.
- Replaced direct active-player-universe request with `/api/data/sleeper/players`.
- Added 24-hour edge caching for Sleeper player universe.
- Added differentiated cache TTLs for projections and nflverse datasets.
- Added allowlisted Pages Function to prevent arbitrary proxy abuse.
- Added `/api/health`.
- Added response metadata headers:
  - `X-FIE-Cache`
  - `X-FIE-Source`
  - `X-FIE-Fetched-At`
- Instrumented `fetchCSV()` and `fetchJSON()` to record source health.
- Added Deployment Source Health UI.
- Added `_routes.json` limiting Functions invocation to `/api/*`.
- Added Wrangler configuration and deployment README.
