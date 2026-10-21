#!/usr/bin/env node
/* UI v10 R5 contract tests ("decide better", 21 Oct 2026) — pure modules in a VM sandbox on committed captures.
 *   1 · R5.1 bid ranges (FIEBids): rank-matched winning bids as budget shares, own league weighs most, other leagues
 *       of the same type 0.15 / other types 0.05, fallbacks, cap at the remaining budget; backtest Weeks 3–6 on the
 *       auction-history capture: bidding the top of the range matched or beat the winner in ≥ 75 % of claims.
 *   2 · R5.2 waiver runs grouped by processing time; usual run time; "ran this week".
 *   3 · R5.3 exposure: started by me / vs me (H2H opponents) / chopped fields; snapshots keep rostered players only.
 *   4 · R5.5 opponent mode: optimal until Thursday 18:00 UTC before the week's first kickoff, as set after; optimal
 *       lineups are never below the lineup as set; the chopped cut line follows the mode.
 *   5 · R5.6 team strength top-N per position (user rules) and depth with bench / free agent separated.
 *   6 · R5.7 deciles by position × projection tier (Compare curve) without touching the win-estimate range.
 *   7 · static wiring: Overview week picker, Waivers bid column + runs, Lab forecasts week picker, Compare curve.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), zlib = require('zlib'), assert = require('assert');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8');
function store(dir) {
  const rec = new Map();
  for (const f of fs.readdirSync(path.join(ROOT, dir))) if (f.endsWith('-response-receipt.json')) { const r = JSON.parse(read(`${dir}/${f}`)); rec.set(r.endpoint, r); }
  const raw = ep => rec.has(ep) ? zlib.gunzipSync(fs.readFileSync(path.join(ROOT, rec.get(ep).path))).toString('utf8') : null;
  return { raw, J: ep => { const t = raw(ep); return t === null ? null : JSON.parse(t); }, ids: () => [...rec.keys()].map(e => (e.match(/league\/(\d+)$/) || [])[1]).filter(Boolean) };
}
const W7 = store('data/research/prospective/weekly-sources/2026/week_07/20261020T175919279901Z');
const L = id => `https://api.sleeper.app/v1/league/${id}`;
const window = { state: {} };
const ctx = vm.createContext({ window, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Intl });
for (const f of ['app/generated/runtime-contracts.js', 'app/core/core-services.js', 'app/generated/ui-decision-policy.js', 'app/core/status.js', 'app/core/projection-service.js',
  'app/core/scoring-core.js', 'app/core/distribution.js', 'app/core/game-state.js', 'app/core/week-model.js', 'app/core/alerts.js',
  'app/core/waivers.js', 'app/core/bids.js', 'app/core/portfolio.js', 'app/core/team-views.js']) vm.runInContext(read(f), ctx, { filename: f });
const w = window, B = w.FIEBids;
const pmap = rows => new Map((rows || []).map(r => [String(r.player_id), r]));
const schedule = w.FIEGameState.index(W7.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const p7 = pmap(W7.J('https://api.sleeper.com/projections/nfl/2026/7?season_type=regular'));
const catRaw = JSON.parse(read('data/research/app/player-catalog.json')), catalog = new Map(Object.entries({ ...(catRaw.identity_only_players || {}), ...(catRaw.players || {}) }));
const cfg = JSON.parse(read('config/league-portfolio.json')), entryOf = id => cfg.leagues.find(l => String(l.league_id) === String(id)) || {};
function myRoster(S, id) { const u = (S.J(`${L(id)}/users`) || []).find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')); const r = u && S.J(`${L(id)}/rosters`).find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id)); return r ? r.roster_id : null; }
const TUE = Date.parse('2026-10-20T19:00:00Z');
function model(id, { now = TUE } = {}) {
  return w.FIEWeekModel.build({ league: W7.J(L(id)), rosters: W7.J(`${L(id)}/rosters`), users: W7.J(`${L(id)}/users`), matchups: W7.J(`${L(id)}/matchups/7`) || [], projRows: p7, catalog, schedule, week: 7, season: 2026, now, fetchedAt: now,
    managedRosterId: myRoster(W7, id), format: w.FIECore.FormatRegistry.profile(entryOf(id).format || 'REDRAFT') });
}
const ids = W7.ids().filter(id => myRoster(W7, id));
const results = {};

/* 1 · bid ranges */
{
  const tx = (leg, pos, bids) => bids.map((b, i) => ({ type: 'waiver', status: 'complete', leg, settings: { waiver_bid: b }, adds: { [`${pos}${leg}${i}`]: 1 }, status_updated: 1e12 + leg * 1e8 + i }));
  const posOf = pid => pid.replace(/\d+$/, '');
  const own = B.claims({ leagueId: 'A', budget: 100, transactions: [...tx(4, 'WR', [40, 10, 2]), ...tx(5, 'WR', [30, 12]), ...tx(6, 'WR', [50, 5]), ...tx(6, 'RB', [20])], positionOf: posOf });
  assert.deepStrictEqual(JSON.parse(JSON.stringify(own.filter(c => c.week === 4).map(c => c.rank))), [1, 2, 3], 'ranks within week and position');
  assert.ok(own.every(c => Math.abs(c.pct - c.bid / 100) < 1e-9), 'bids as share of the budget');
  const other = B.claims({ leagueId: 'B', budget: 1000, transactions: tx(5, 'WR', [900]), positionOf: posOf });
  const e = B.estimate({ position: 'WR', rank: 1, week: 7, budget: 100, own, others: [{ claims: other, sameType: true }] });
  assert.ok(e && e.scope === 'position and rank' && e.nOwn === 3 && e.nOther === 1, 'rank-1 WR sample: 3 own + 1 other');
  assert.ok(e.high <= 50, `one $900/$1000 bid elsewhere (weight 0.15) does not dominate three own rank-1 bids (high ${e.high})`);
  const capped = B.estimate({ position: 'WR', rank: 1, week: 7, budget: 100, remaining: 20, own, others: [] });
  assert.ok(capped.high <= 20 && capped.capped, 'capped at the remaining budget');
  const fb = B.estimate({ position: 'TE', rank: 1, week: 7, budget: 100, own, others: [] });
  assert.ok(fb && fb.scope === 'rank (any position)', 'no TE claim → fallback to rank across positions');
  assert.strictEqual(B.estimate({ position: 'WR', rank: 1, week: 4, budget: 100, own, others: [] }), null, 'only claims of earlier weeks are used');
  const pol = JSON.parse(read('config/ui-decision-policy.json')).waivers.bids;
  assert.ok(pol.own === 1 && pol.same_type < pol.own && pol.other_type < pol.same_type, 'policy: own league weighs most');
  const bt = require('./v10_bid_backtest.js').run();
  for (const k of ['chopped', 'normal']) { assert.ok(bt.result[k].claims >= 100, `${k}: backtest sample`); assert.ok(bt.result[k].atOrBelowHigh >= 0.75, `${k}: top of the range ≥ winning bid in ≥ 75 % (${bt.result[k].atOrBelowHigh})`); }
  results.bids = { example: e, backtest: bt.result };
}

/* 2 · runs and schedule */
{
  const t = (at, st = 'complete') => ({ type: 'waiver', status: st, status_updated: at, settings: { waiver_bid: 1 }, adds: { x: 1 } });
  const H = 3600e3, base = Date.parse('2026-10-21T16:00:00Z');
  const rs = B.runs({ transactions: [t(base), t(base + 60e3), t(base + 120e3, 'failed'), t(base + 30 * H)], since: base - 1 });
  assert.strictEqual(rs.length, 2, 'two runs (gap > 1 h)'); assert.strictEqual(rs[0].items.length, 3, 'main run first');
  const sc = B.schedule({ transactions: [t(base), t(base + 7 * 24 * H), t(base + 14 * 24 * H + 60e3)], since: base + 10 * 24 * H });
  assert.ok(sc.usual.weekday === 3 && sc.usual.hourUtc === 16 && sc.ranThisWeek, 'usual run Wednesday 16 UTC; ran after `since`');
  const nx = B.nextRun(sc.usual, Date.parse('2026-10-20T19:00:00Z'));
  assert.strictEqual(new Date(nx).toISOString(), '2026-10-21T16:00:00.000Z', 'next run after Tuesday evening = Wednesday 16:00 UTC');
  results.runs = 'ok';
}

/* 3 · exposure */
{
  const res = ids.map(id => ({ wm: model(id), entry: { id } }));
  const mp = w.FIEPortfolioViews.myPlayers(res);
  assert.ok(mp.vsSlots > 0, 'opponents start players against me');
  const h2h = res.filter(r => r.wm.opponent).length, oppStarts = res.reduce((s, r) => s + (r.wm.opponent ? r.wm.opponent.starters.filter(e => e.p).length : 0), 0);
  assert.strictEqual(mp.vsSlots, oppStarts, `vs counts = opponents' submitted starters in ${h2h} H2H leagues`);
  assert.ok(mp.rows.some(r => r.fieldStarts > 0), 'chopped fields counted for listed players');
  assert.ok(mp.rows.every(r => r.net === r.starts - r.vs), 'net = by me − vs me');
  const snap = w.FIEPortfolioViews.snapshot(res);
  assert.ok(Object.keys(snap.statuses).every(pid => mp.rows.find(r => r.pid === pid)?.rostered > 0), 'status snapshot keeps rostered players only');
  results.exposure = { players: mp.players, vsSlots: mp.vsSlots, vsOnly: mp.rows.filter(r => !r.rostered).length };
}

/* 4 · opponent mode */
{
  const any = ids.find(id => model(id).opponent);
  const m = model(any);
  assert.strictEqual(new Date(m.opponentMode.cutoff).toISOString(), '2026-10-22T18:00:00.000Z', 'cutoff Thursday 18:00 UTC before TNF (Fri 00:15 UTC)');
  assert.strictEqual(m.opponentMode.mode, 'optimal', 'Tuesday: optimal');
  assert.strictEqual(model(any, { now: Date.parse('2026-10-22T18:30:00Z') }).opponentMode.mode, 'asSet', 'after the cutoff: as set');
  let h2h = 0, fields = 0;
  for (const id of ids) { const x = model(id);
    if (x.opponent) { h2h++; assert.ok(x.opponent.optimal.totals.projected >= x.opponent.totals.projected - 0.01, `${id}: optimal ≥ as set`); assert.strictEqual(x.winEstimate.value, x.winEstimate.vsOptimal, `${id}: Tuesday win estimate uses the optimal opponent`); }
    if (x.field && !x.field.meEliminated) { fields++; for (const r of x.field.rows) assert.ok(r.optimal >= r.asSet - 0.01, `${id}: field optimal ≥ as set`); assert.strictEqual(x.field.marginToCut, x.field.optimal.marginToCut, 'cut line follows the mode'); } }
  assert.ok(h2h > 5 && fields > 3, 'checked H2H leagues and chopped fields');
  results.opponents = { h2h, fields };
}

/* 5 · team strength and depth */
{
  const C = w.FIETeamViews.strengthCounts;
  assert.deepStrictEqual(JSON.parse(JSON.stringify(C(['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'FLEX']))), { QB: 2, RB: 4, WR: 4, TE: 2 }, '2 RB / 2 WR / 1 TE / 2 FLEX → 4 / 4 / 2');
  assert.strictEqual(C(['TE', 'FLEX', 'FLEX', 'FLEX']).TE, 3, '1 TE + 3 FLEX → 3 TEs (half the FLEX slots, rounded up)');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(C(['DL', 'DL', 'LB', 'LB', 'DB', 'DB', 'IDP_FLEX', 'IDP_FLEX']))), { DL: 3, LB: 4, DB: 3 }, 'IDP: slots + 1, LB + 2, IDP_FLEX ignored');
  assert.strictEqual(C(['QB', 'SUPER_FLEX']).QB, 3, 'Superflex counts as a QB slot, + 1');
  const id = '1313696967989157888', wm = model(id);
  const t = w.FIETeamViews.team({ wm, rosters: W7.J(`${L(id)}/rosters`), horizon: [{ week: 7, projRows: p7 }], schedule, catalog, season: 2026, seasonRows: new Map(), adp: new Map(), projRows: p7 });
  assert.ok(t.strength.every(s => s.count === t.strengthCounts[s.position]), 'strength rows carry their N');
  assert.ok(t.depth.length && t.depth.every(d => 'bench' in d && 'worstStarter' in d), 'depth rows carry bench / worst starter');
  results.team = { counts: t.strengthCounts };
}

/* 6 · deciles */
{
  const m = model('1313696967989157888'), pol = w.FIE_UI_POLICY.variance.calibration;
  let n = 0;
  for (const e of m.me.submitted) { const p = e.p; if (!p?.range?.deciles) continue; n++;
    const q = p.range.deciles.q; assert.strictEqual(q.length, 9, 'P10..P90'); assert.ok(q.every((v, i) => i === 0 || v >= q[i - 1] - 1e-9), 'non-decreasing');
    assert.strictEqual(p.range.deciles.source, 'position × projection tier', 'source labelled');
    const c = pol.positions[p.position]; if (c) assert.ok(Math.abs(p.range.low - Math.max(0, p.active.value * c.p10)) < 1e-6, 'win-estimate range unchanged (position P10)'); }
  assert.ok(n >= 4, 'starters have deciles');
  assert.strictEqual(pol.player_level, false, 'player-level switch off until per-player spreads exist');
  results.deciles = n;
}

/* 7 · static wiring */
{
  const ov = read('app/v10/v10-overview.js'), wv = read('app/v10/v10-waivers.js'), lab = read('app/v10/v10-lab.js'), rd = read('app/v10/v10-reader.js'), sh = read('app/v10/v10-shell.js');
  assert.ok(/data-v10-ovweek/.test(ov) && /function pastTable/.test(ov) && /function futureTable/.test(ov) && /\{view:'overview',week\}/.test(sh), 'Overview week picker');
  assert.ok(!/resultsSection\(resultsRows\)\}<\/div>/.test(ov), 'no separate Latest results card');
  assert.ok(/<span class="v10-num">Bid<\/span>/.test(wv) && /This week's waiver runs/.test(wv), 'Waivers: bid column and this week\'s runs');
  assert.ok(/Bid \$\$\{e\.low\}–\$\{e\.high\} on/.test(ov), 'Overview to-do: "Bid $a–b on X"');
  assert.ok(/data-v10-lab-fweek/.test(lab), 'Lab forecasts week picker');
  assert.ok(/function curve\(ps\)/.test(rd) && /function statTable\(ps,wm\)/.test(rd), 'Compare: outcome curve and stat breakdown');
  assert.ok(/Started vs me/.test(ov) && /Chopped fields/.test(ov), 'Exposure columns');
  results.static = 'ok';
}
console.log('PASS UI v10 R5: bid ranges (backtest), waiver runs, exposure, opponent mode, team strength top-N, depth, deciles, wiring');
console.log(JSON.stringify(results));
