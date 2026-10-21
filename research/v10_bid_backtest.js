#!/usr/bin/env node
/* UI v10 R5.1 · backtest of the waiver bid ranges (FIEBids) on the repo's auction-history capture.
 *
 * For every completed priced claim in weeks --from..--to of every FAAB league, the range is estimated exactly as the
 * app would have shown it before that week's run: only claims of earlier weeks (own league + other leagues with the
 * policy weights), the claim's position and its rank among that week's winning claims at the position.
 * Reported per league type: share of winning bids inside [low, high], share ≤ high ("bidding the top of the range
 * would have matched or beaten the winner"), median overshoot of high over the winning bid (budget share).
 * Caveat: the rank of a historical claim is the rank among WINNING bids, the app ranks candidates by lineup gain — the
 * match is an assumption, which is why the backtest exists.
 *   node research/v10_bid_backtest.js [--from 3 --to 6] [--json]
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), zlib = require('zlib');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const FROM = Number(arg('--from', 3)), TO = Number(arg('--to', 6)), OWN_ONLY = process.argv.includes('--own-only');
const AUCTION = 'data/research/prospective/auction-history/2026/target_week_07/20261020T175951784034Z/auction-history.json';
const PROFILES = 'data/research/prospective/weekly-sources/2026/week_07/20261020T175919279901Z';
function run() {
  const window = {};
  const ctx = vm.createContext({ window, Math, Number, String, Object, Array, Map, Set, JSON, Date });
  vm.runInContext(read('app/generated/ui-decision-policy.js'), ctx); vm.runInContext(read('app/core/bids.js'), ctx);
  const B = window.FIEBids;
  const cat = JSON.parse(read('data/research/app/player-catalog.json')), catalog = { ...(cat.identity_only_players || {}), ...(cat.players || {}) };
  const posOf = pid => (catalog[pid]?.position) || (/^[A-Z]{2,3}$/.test(pid) ? 'DEF' : '?');
  const leagues = new Map();
  for (const f of fs.readdirSync(path.join(ROOT, PROFILES))) if (/^\d+-profile-response-receipt\.json$/.test(f)) {
    const r = JSON.parse(read(`${PROFILES}/${f}`)), lg = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(ROOT, r.path))).toString());
    if (Number(lg.settings?.waiver_type) === 2 && Number(lg.settings?.disable_adds) !== 1) leagues.set(String(lg.league_id), { budget: Number(lg.settings.waiver_budget), chopped: Number(lg.settings?.type) === 3, name: lg.name });
  }
  const obs = JSON.parse(read(AUCTION)).observations || [], seen = new Set(), tx = new Map();
  for (const o of obs) { const t = o.raw_transaction; if (!t || seen.has(t.transaction_id)) continue; seen.add(t.transaction_id); const id = String(o.league_id); (tx.get(id) || tx.set(id, []).get(id)).push(t); }
  const book = new Map([...leagues].map(([id, l]) => [id, B.claims({ leagueId: id, budget: l.budget, transactions: tx.get(id) || [], positionOf: posOf })]));
  const out = { chopped: { n: 0, inside: 0, belowHigh: 0, over: [] }, normal: { n: 0, inside: 0, belowHigh: 0, over: [] } };
  for (const [id, l] of leagues) {
    const own = book.get(id), others = [...leagues].filter(([o]) => o !== id).map(([o, ol]) => ({ claims: book.get(o), sameType: ol.chopped === l.chopped }));
    for (const c of own) { if (c.week < FROM || c.week > TO) continue;
      const e = B.estimate({ position: c.pos, rank: c.rank, week: c.week, budget: l.budget, own, others: OWN_ONLY ? [] : others }); if (!e) continue;
      const k = l.chopped ? 'chopped' : 'normal', s = out[k]; s.n++; if (c.bid >= e.low && c.bid <= e.high) s.inside++; if (c.bid <= e.high) s.belowHigh++; s.over.push((e.high - c.bid) / l.budget); }
  }
  const med = xs => { const a = xs.slice().sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };
  const res = {}; for (const [k, s] of Object.entries(out)) res[k] = { claims: s.n, insideRange: s.n ? +(s.inside / s.n).toFixed(3) : null, atOrBelowHigh: s.n ? +(s.belowHigh / s.n).toFixed(3) : null, medianHighMinusWinnerShare: s.over.length ? +med(s.over).toFixed(4) : null };
  return { weeks: [FROM, TO], leagues: leagues.size, result: res };
}
if (require.main === module) { const r = run(); console.log(process.argv.includes('--json') ? JSON.stringify(r) : JSON.stringify(r, null, 1)); }
module.exports = { run };
