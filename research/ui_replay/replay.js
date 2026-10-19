/* FIE UI replay server and provider router.
 *
 * - Serves a built `dist/` directory over HTTP (same layout as Cloudflare Pages).
 * - Answers `/api/*` (Pages Functions) and direct Sleeper calls from an immutable
 *   capture via Playwright routing. Unknown external requests are aborted and
 *   recorded, so a test can assert it did not depend on the live internet.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const http = require('http');
const { CaptureStore } = require('./fixtures');

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json', '.csv': 'text/csv', '.svg': 'image/svg+xml', '.png': 'image/png', '.md': 'text/markdown; charset=utf-8',
  '.gz': 'application/gzip', '.txt': 'text/plain; charset=utf-8' };

function serveDist(root) {
  const base = path.resolve(root);
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let pathname;
      try { pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname); } catch { res.writeHead(400).end(); return; }
      const file = path.resolve(base, '.' + (pathname.endsWith('/') ? pathname + 'index.html' : pathname));
      if (!file.startsWith(base + path.sep) && file !== base) { res.writeHead(403).end(); return; }
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404).end(); return; }
        res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
        res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve({ server, origin: `http://127.0.0.1:${server.address().port}` }));
  });
}

const NFLVERSE = {
  players: 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',
  schedule: 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',
  weekly: 'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv',
  snaps: 'https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2026.csv'
};

class ProviderRouter {
  constructor(scenario) {
    this.scenario = scenario;
    this.store = new CaptureStore(scenario.capture, { seasonMarketFile: scenario.seasonMarket, fallbacks: scenario.fallbackCaptures || [] });
    this.unmatched = new Set();
    this.served = 0;
  }
  json(value) { return { body: Buffer.from(JSON.stringify(value)), contentType: 'application/json' }; }
  sleeperLeague(pathname) {
    const ov = this.scenario.overrides || {};
    const m = pathname.match(/^\/v1\/league\/(\d+)(?:\/([a-z_]+))?(?:\/(\d+))?$/);
    if (!m) return null;
    const [, id, part, week] = m;
    const endpoint = `https://api.sleeper.app/v1/league/${id}${part ? '/' + part : ''}${week ? '/' + week : ''}`;
    if (!part && this.store.has(endpoint)) {
      const league = this.store.json(endpoint);
      return this.json(ov.league ? ov.league(league) : league);
    }
    if (this.store.has(endpoint)) {
      const value = this.store.json(endpoint);
      const r = ov[part] ? ov[part](value, { id, week, store: this.store }) : value;
      return this.json(r === undefined ? value : r);
    }
    // A scenario may model a provider payload the capture lacks (e.g. a scored past week).
    if (ov[part]) { const r = ov[part](null, { id, week, store: this.store }); if (r !== undefined && r !== null) return this.json(r); }
    // Weeks or league parts that the capture does not contain are empty, which is
    // Sleeper's own response for future/unknown periods.
    if (['matchups', 'transactions', 'drafts', 'traded_picks', 'winners_bracket', 'losers_bracket'].includes(part)) return this.json([]);
    return null;
  }
  resolve(url) {
    let u; try { u = new URL(url); } catch { return null; }
    if (u.pathname === '/api/health') return this.json({ ok: true, replay: true, capture: this.scenario.capture });
    if (u.pathname.startsWith('/api/data/')) {
      const parts = u.pathname.slice('/api/data/'.length).split('/').filter(Boolean);
      if (parts[0] === 'sleeper' && parts[1] === 'players') return this.store.raw('https://api.sleeper.app/v1/players/nfl');
      if (parts[0] === 'sleeper' && parts[1] === 'projections') {
        if (parts.length === 3) return this.store.seasonProjections();
        const key = `https://api.sleeper.com/projections/nfl/${parts[2]}/${parts[3]}?season_type=regular`;
        return this.store.raw(key) || this.store.frozenWeekProjections(parts[2], parts[3]) || this.json([]);
      }
      if (parts[0] === 'nflverse') {
        const legacy = /^(weekly|snaps)-20\d\d$/.exec(parts[1] || '');
        const key = legacy ? legacy[1] : parts[1];
        if (NFLVERSE[key] && this.store.has(NFLVERSE[key])) return this.store.raw(NFLVERSE[key]);
      }
      return null;
    }
    if (/(^|\.)sleeper\.(app|com)$/.test(u.hostname)) {
      if (u.pathname === '/v1/state/nfl') return this.json(this.scenario.nflState);
      if (u.pathname.startsWith('/v1/players/nfl')) return this.store.raw('https://api.sleeper.app/v1/players/nfl');
      const league = this.sleeperLeague(u.pathname);
      if (league) return league;
      const proj = u.pathname.match(/^\/projections\/nfl\/(\d{4})\/(\d+)$/);
      if (proj) return this.store.raw(`https://api.sleeper.com/projections/nfl/${proj[1]}/${proj[2]}?season_type=regular`) || this.json([]);
    }
    return null;
  }
  async install(context, origin) {
    await context.route('**/*', route => {
      const url = route.request().url();
      if (url.startsWith(origin + '/') && !url.startsWith(origin + '/api/')) return route.continue();
      const hit = this.resolve(url);
      if (hit) { this.served++; return route.fulfill({ status: 200, contentType: hit.contentType, body: hit.body, headers: { 'access-control-allow-origin': '*' } }); }
      this.unmatched.add(url.replace(/^https?:\/\/127\.0\.0\.1:\d+/, ''));
      return url.startsWith(origin + '/api/') ? route.fulfill({ status: 404, body: 'not in replay capture' }) : route.abort();
    });
  }
}

module.exports = { serveDist, ProviderRouter };
