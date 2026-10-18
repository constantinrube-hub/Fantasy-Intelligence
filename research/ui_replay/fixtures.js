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
  /**
   * fallbacks: further capture directories consulted (in order) for endpoints the primary capture
   * lacks — e.g. last week's transactions with processed FAAB bids. The primary always wins.
   */
  constructor(captureDir, { seasonMarketFile = null, fallbacks = [] } = {}) {
    this.captureDir = captureDir;
    this.index = loadCapture(captureDir);
    for (const fb of fallbacks) for (const [k, v] of loadCapture(fb)) if (!this.index.has(k)) this.index.set(k, v);
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

/**
 * Frozen Thursday Sleeper weekly projections (data/research/market/sleeper/<season>/week_NN.jsonl.gz,
 * written by the weekly market-benchmark workflow) in the /projections/nfl/<season>/<week> shape, joined
 * to the captured player DB for metadata. Serves past weeks that a weekly-source capture lacks.
 */
CaptureStore.prototype.frozenWeekProjections = function (season, week) {
  const key = `${season}:${week}`;
  this._frozen = this._frozen || new Map();
  if (this._frozen.has(key)) return this._frozen.get(key);
  const rel = `data/research/market/sleeper/${season}/week_${String(week).padStart(2, '0')}.jsonl.gz`;
  let out = null;
  if (fs.existsSync(path.join(REPO, rel))) {
    const players = this.json('https://api.sleeper.app/v1/players/nfl') || {};
    const rows = readGz(rel).toString('utf8').split('\n').filter(Boolean).map(line => {
      const r = JSON.parse(line), p = players[r.sleeper_id] || {};
      return { status: null, stats: r.stats || {}, category: 'proj', week: Number(week), season: String(season), season_type: 'regular', sport: 'nfl',
        player_id: r.sleeper_id, team: p.team ?? null,
        player: { first_name: p.first_name ?? null, last_name: p.last_name ?? null, position: p.position ?? r.position_model ?? null, team: p.team ?? null, injury_status: null } };
    });
    out = { body: Buffer.from(JSON.stringify(rows)), contentType: 'application/json' };
  }
  this._frozen.set(key, out);
  return out;
};

function parseCsv(text) {
  const rows = [];let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; continue; }
    if (c === '"') q = true; else if (c === ',') { row.push(cell); cell = ''; } else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; } else if (c !== '\r') cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows;
  return body.filter(r => r.length === head.length).map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

/**
 * TEST FIXTURE (not provider data): fantasy points of one completed week rebuilt from the captured
 * nflverse weekly player stats — skill players use nflverse `fantasy_points_ppr`, kickers a standard
 * table (FG 0–39 = 3, 40–49 = 4, 50+ = 5, PAT 1, misses −1); team D/ST scores 0 (no team stats in the
 * capture). Joined to Sleeper IDs through the captured dynastyprocess ID map. Used to give a replay
 * scenario a scored past week until WP-T2 captures real post-week matchups.
 */
CaptureStore.prototype.nflverseWeekPoints = function (week) {
  this._pts = this._pts || new Map();
  if (this._pts.has(week)) return this._pts.get(week);
  const stats = this.raw('https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv');
  const ids = this.raw('https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv');
  const out = new Map();
  if (stats && ids) {
    const gsis = new Map(parseCsv(ids.body.toString('utf8')).filter(r => r.gsis_id && r.sleeper_id && r.sleeper_id !== 'NA').map(r => [r.gsis_id, r.sleeper_id]));
    const n = v => Number(v) || 0;
    for (const r of parseCsv(stats.body.toString('utf8'))) {
      if (Number(r.week) !== Number(week) || r.season_type !== 'REG') continue;
      const sid = gsis.get(r.player_id); if (!sid) continue;
      const k = r.position === 'K'
        ? 3 * (n(r.fg_made_0_19) + n(r.fg_made_20_29) + n(r.fg_made_30_39)) + 4 * n(r.fg_made_40_49) + 5 * (n(r.fg_made_50_59) + n(r.fg_made_60_)) + n(r.pat_made) - n(r.fg_missed) - n(r.pat_missed)
        : n(r.fantasy_points_ppr);
      out.set(String(sid), Math.round(k * 100) / 100);
    }
  }
  this._pts.set(week, out);
  return out;
};

module.exports = { REPO, CaptureStore, loadCapture, readGz, parseCsv };
