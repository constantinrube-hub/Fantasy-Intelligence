/* FIE UI replay fixtures.
 *
 * Serves immutable, already-committed provider captures to the browser so the
 * real application can be exercised deterministically. Nothing here creates new
 * research evidence or alters a capture: every payload is read from the receipt
 * files written by the weekly-source capture workflow.
 *
 * Capture layout (written by the existing workflow):
 *   data/research/prospective/weekly-sources/<season>/week_NN/<stamp>/*-response-receipt.json
 *   each receipt: { endpoint, kind: 'json'|'csv', path: <repo-relative .gz>, ... }
 */
'use strict';
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const REPO = path.resolve(__dirname, '..', '..');

function readGz(rel) {
  return zlib.gunzipSync(fs.readFileSync(path.join(REPO, rel)));
}

/** Map provider endpoint URL -> { path, kind } from one capture directory. */
function loadCapture(captureDir) {
  const dir = path.join(REPO, captureDir);
  if (!fs.existsSync(dir)) throw new Error(`capture directory missing: ${captureDir}`);
  const map = new Map();
  for (const name of fs.readdirSync(dir)) {
    if (!name.endsWith('-response-receipt.json')) continue;
    const receipt = JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
    if (receipt.endpoint && receipt.path) map.set(receipt.endpoint, { path: receipt.path, kind: receipt.kind || 'json' });
  }
  if (!map.size) throw new Error(`no response receipts in ${captureDir}`);
  return map;
}

class CaptureStore {
  constructor(captureDir, { seasonMarketFile = null } = {}) {
    this.captureDir = captureDir;
    this.index = loadCapture(captureDir);
    this.cache = new Map();
    this.seasonMarketFile = seasonMarketFile;
    this._season = null;
  }
  has(endpoint) { return this.index.has(endpoint); }
  raw(endpoint) {
    const entry = this.index.get(endpoint);
    if (!entry) return null;
    if (!this.cache.has(endpoint)) this.cache.set(endpoint, readGz(entry.path));
    return { body: this.cache.get(endpoint), contentType: entry.kind === 'csv' ? 'text/csv; charset=utf-8' : 'application/json' };
  }
  json(endpoint) {
    const r = this.raw(endpoint);
    return r ? JSON.parse(r.body.toString('utf8')) : null;
  }
  /**
   * Season projections in Sleeper's /projections/nfl/<season> shape, rebuilt from
   * the committed season-market capture (stats + ADP) joined to the captured
   * Sleeper player DB for player metadata. Used only because the weekly-source
   * capture does not include the season endpoint.
   */
  seasonProjections() {
    if (this._season) return this._season;
    if (!this.seasonMarketFile) return (this._season = { body: Buffer.from('[]'), contentType: 'application/json' });
    const players = this.json('https://api.sleeper.app/v1/players/nfl') || {};
    const lines = readGz(this.seasonMarketFile).toString('utf8').split('\n').filter(Boolean);
    const rows = lines.map(line => {
      const r = JSON.parse(line), p = players[r.sleeper_id] || {};
      return {
        status: null, stats: r.stats || {}, category: 'proj', week: null, season: String(r.season),
        season_type: 'regular', sport: 'nfl', player_id: r.sleeper_id, team: p.team ?? null,
        player: { fantasy_positions: p.fantasy_positions ?? null, first_name: p.first_name ?? null, last_name: p.last_name ?? null,
          position: p.position ?? null, team: p.team ?? null, years_exp: p.years_exp ?? null, injury_status: p.injury_status ?? null, metadata: p.metadata ?? null }
      };
    });
    return (this._season = { body: Buffer.from(JSON.stringify(rows)), contentType: 'application/json' });
  }
}

module.exports = { REPO, CaptureStore, loadCapture, readGz };
