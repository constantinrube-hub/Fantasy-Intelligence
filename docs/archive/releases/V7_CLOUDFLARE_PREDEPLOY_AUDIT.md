# V7 Cloudflare Pre-Deployment Audit

## Static result: PASS

- Duplicate HTML IDs: none
- Direct nflverse GitHub URLs remaining in browser app: 0
- Direct `api.sleeper.com/projections` URLs remaining: no
- Direct uncached Sleeper player-universe call remaining: no
- Pages Function data route: present
- Pages Function health route: present
- `_routes.json`: present
- Source-health UI: present
- App SHA-256: `49ff3f1ae3fd0fa5f166282f6cef1435c82d11c7548f39111d53c58552817468`

## Live checks still required
- Actual Cloudflare Pages Function deployment
- Upstream responses through Cloudflare
- Cache HIT after repeated request
- Actual Sleeper league load
- Mobile Safari runtime/layout
- Console/network error review
