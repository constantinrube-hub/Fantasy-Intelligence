#!/usr/bin/env node
/* UI v10 R2 contract tests — pure modules in a VM sandbox on committed captures (no network, no DOM).
 *   · Waivers (WP2.4): exact pruning vs exhaustive search on every captured league; free-agent pool
 *     never contains rostered players; drops legal (active roster, not locked, not protected); league
 *     roster rules (entry-class floor, legacy cap); eliminated teams; FAAB market from real claims.
 *   · Review (WP2.3): hindsight ≥ submitted and ≥ projection-best on a scored Week 5 fixture; Best Ball.
 *   · Portfolio (WP2.5): my-players counts equal roster contents (A-26); changes feed detects status
 *     changes and my transactions after the previous visit only.
 *   · Lineup context (WP2.1), WAIVER_ADD alert (Best Ball keeps waiver tasks), team-code aliases.
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
const W6 = store('data/research/prospective/weekly-sources/2026/week_06/20261015T174631408136Z');
const W7 = store('data/research/prospective/weekly-sources/2026/week_07/20261018T093323977084Z');
const L = id => `https://api.sleeper.app/v1/league/${id}`;
const window = { state: {} };
const ctx = vm.createContext({ window, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Intl });
for (const f of ['app/generated/runtime-contracts.js', 'app/core/core-services.js', 'app/generated/ui-decision-policy.js', 'app/core/status.js', 'app/core/projection-service.js',
  'app/core/scoring-core.js', 'app/core/distribution.js', 'app/core/game-state.js', 'app/core/week-model.js', 'app/core/alerts.js',
  'app/core/waivers.js', 'app/core/review.js', 'app/core/portfolio.js']) vm.runInContext(read(f), ctx, { filename: f });
const w = window;
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);
const pmap = rows => new Map((rows || []).map(r => [String(r.player_id), r]));
const schedule = w.FIEGameState.index(W6.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const p6 = pmap(W6.J('https://api.sleeper.com/projections/nfl/2026/6?season_type=regular')), p7 = pmap(W7.J('https://api.sleeper.com/projections/nfl/2026/7?season_type=regular'));
const catRaw = JSON.parse(read('data/research/app/player-catalog.json')), catalog = new Map(Object.entries({ ...(catRaw.identity_only_players || {}), ...(catRaw.players || {}) }));
const cfg = JSON.parse(read('config/league-portfolio.json')), entryOf = id => cfg.leagues.find(l => String(l.league_id) === String(id)) || {};
const adp = new Map(zlib.gunzipSync(fs.readFileSync(path.join(ROOT, 'data/research/market/sleeper/2026/season_market_2026-09-30.jsonl.gz'))).toString().split('\n').filter(Boolean).map(JSON.parse)
  .map(r => [String(r.sleeper_id), { dynasty: r.adp?.adp_dynasty_ppr, dynasty2qb: r.adp?.adp_dynasty_2qb, redraft: r.adp?.adp_ppr, stats: r.stats }]));
function myRoster(S, id) { const u = S.J(`${L(id)}/users`).find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')); const r = u && S.J(`${L(id)}/rosters`).find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id)); return r ? r.roster_id : null; }
function model(S, id, { week = 6, projRows = p6, now = Date.parse('2026-10-15T18:00:00Z'), matchups = null } = {}) {
  return w.FIEWeekModel.build({ league: S.J(L(id)), rosters: S.J(`${L(id)}/rosters`), users: S.J(`${L(id)}/users`), matchups: matchups || S.J(`${L(id)}/matchups/${week}`) || [], projRows, catalog, schedule, week, season: 2026, now, fetchedAt: now,
    managedRosterId: myRoster(S, id), format: w.FIECore.FormatRegistry.profile(entryOf(id).format || 'REDRAFT') });
}
function waivers(S, id, wm, extra = {}) {
  return w.FIEWaivers.build({ wm, league: S.J(L(id)), rosters: S.J(`${L(id)}/rosters`), managedRosterId: myRoster(S, id), horizon: [{ week: 6, projRows: p6 }, { week: 7, projRows: p7 }], schedule, season: 2026, now: Date.parse('2026-10-15T18:00:00Z'),
    catalog, adp, seasonRows: adp, constraints: entryOf(id).research_constraints || [], ...extra });
}
const ids = W6.ids().filter(id => myRoster(W6, id));
let leaguesChecked = 0, rowsChecked = 0;

/* 1 · Waivers on every captured league: exact pruning, FA pool, legal drops, rules */
for (const id of ids) {
  const wm = model(W6, id), r = waivers(W6, id, wm), x = waivers(W6, id, wm, { exhaustive: true });
  const rosters = W6.J(`${L(id)}/rosters`), rostered = new Set(rosters.flatMap(q => [...(q.players || []), ...(q.reserve || []), ...(q.taxi || [])]).map(String));
  const mine = rosters.find(q => q.roster_id === myRoster(W6, id)), reserve = new Set([...(mine.reserve || []), ...(mine.taxi || [])].map(String));
  if (!(mine.players || []).length) { assert.ok(r.eliminated && r.rows.length === 0, `${id}: eliminated team gets no adds`); leaguesChecked++; continue; }
  const ex = new Map([...x.rows, ...x.watch].map(q => [q.pid, q]));
  for (const q of [...r.rows, ...r.watch]) {
    rowsChecked++;
    // Pruned rows are exactly "no improvement possible" (reported 0); exhaustive may quantify a loss when a drop is forced.
    const e = ex.get(q.pid), pos = v => Math.max(0, v ?? 0); assert.ok(e && Math.abs(pos(e.gainHorizon) - pos(q.gainHorizon)) < 1e-6 && pos(e.gainWeek) === pos(q.gainWeek), `${id} ${q.name}: pruned gain equals exhaustive`);
    assert.ok(!rostered.has(q.pid), `${id} ${q.name}: free agent is not rostered`);
    if (q.gainHorizon < -1e-9) assert.ok(q.drop && r.freeSpots === 0, `${id} ${q.name}: a negative gain only comes from a forced drop`);
    if (q.drop) { assert.ok((mine.players || []).map(String).includes(q.drop.pid) && !reserve.has(q.drop.pid), `${id}: drop ${q.drop.name} is an active-roster player`);
      assert.ok(!wm.player(q.drop.pid).game.locked, `${id}: drop ${q.drop.name} is not locked`);
      assert.ok(!r.protectedDrops.some(p => p.pid === q.drop.pid), `${id}: drop ${q.drop.name} is not dynasty-protected`); }
    if (q.status?.unavailable && q.status.code !== 'BYE') assert.ok(r.watch.includes(q), `${id} ${q.name}: unavailable players are watch rows, never adds`);
    if (q.tier === 'recommended') assert.ok(q.gainWeek >= 1 || q.gainHorizon >= 3, `${id} ${q.name}: tier follows policy thresholds`);
  }
  const floor = (entryOf(id).research_constraints || []).find(c => c.type === 'nfl_entry_cohort_floor');
  if (floor) for (const q of r.rows) assert.ok(q.entry !== null && q.entry >= floor.minimum_entry_season, `${id} ${q.name}: entry class ${q.entry} ≥ ${floor.minimum_entry_season}`);
  leaguesChecked++;
}
assert.ok(leaguesChecked >= 20 && rowsChecked > 500, `waivers covered ${leaguesChecked} leagues / ${rowsChecked} rows`);
/* 1b · Rules: Genesis Dynasty legacy cap forces a legacy drop for legacy adds; dynasty ADP protection */
{
  const id = '1316165875291668480', wm = model(W6, id), r = waivers(W6, id, wm);
  assert.ok(r.rules.some(t => /Legacy players/.test(t)), 'legacy-cap rule reported');
  assert.ok(r.protectedDrops.some(p => p.name === "Ja'Marr Chase"), 'Chase is protected from drop suggestions (dynasty ADP)');
  for (const q of r.rows) if (q.rule && q.drop) assert.ok((catalog.get(q.drop.pid)?.years_exp ?? 99) >= 2026 - 2024, `${q.name}: legacy add drops a legacy player`);
}
/* 1c · Locks: after TNF nobody whose game started is added for this week or dropped */
{
  const id = '1313697754907697152', now = Date.parse('2026-10-17T12:00:00Z'), wm = model(W6, id, { now });
  const r = w.FIEWaivers.build({ wm, league: W6.J(L(id)), rosters: W6.J(`${L(id)}/rosters`), managedRosterId: myRoster(W6, id), horizon: [{ week: 6, projRows: p6 }], schedule, season: 2026, now, catalog });
  for (const q of r.rows) { if (wm.player(q.pid).game.locked) assert.strictEqual(q.gainWeek, 0, `${q.name}: locked add has no gain this week`); if (q.drop) assert.ok(!wm.player(q.drop.pid).game.locked, `${q.drop.name}: locked players are never dropped`); }
}
/* 1d · Unpublished horizon weeks are reported, not counted */
{
  const id = '1313697754907697152', wm = model(W6, id), r = waivers(W6, id, wm, { horizon: [{ week: 6, projRows: p6 }, { week: 7, projRows: p7 }, { week: 8, projRows: new Map() }] });
  assert.strictEqual(r.weeksAvailable, 2); assert.ok(r.rows.every(q => q.gains[2] === null), 'no gain counted for an unpublished week');
  const top = r.rows[0]; assert.ok(top && top.replaces[1] && top.replaces[1][0].name, 'gain explains whom it replaces');
}
/* 2 · FAAB market from real Week 6 claims (ReDraft – Pro: $100 budget) */
{
  const id = '1313697754907697152', wm = model(W6, id);
  const m = w.FIEWaivers.market({ league: W6.J(L(id)), rosters: W6.J(`${L(id)}/rosters`), users: W6.J(`${L(id)}/users`), transactions: W6.J(`${L(id)}/transactions/6`), positionOf: pid => wm.player(pid)?.position, nameOf: pid => wm.player(pid)?.name, managedRosterId: myRoster(W6, id) });
  assert.ok(m.faab && m.budget === 100 && m.mine.remaining === 66, 'budget and remaining from roster settings');
  assert.strictEqual(m.byPosition.RB.n, 4); near(m.byPosition.RB.median, 5.5, 1e-9, 'RB median winning bid');
  assert.ok(m.lastRun.length >= 3 && m.lastRun.every(t => t.adds.length), 'last waiver run listed');
}
/* 3 · Review on the scored Week 5 fixture (nflverse stats) with frozen Thursday projections */
{
  const { week5Matchups } = require('./ui_replay/scenarios'), { CaptureStore } = require('./ui_replay/fixtures');
  const fz = new CaptureStore('data/research/prospective/weekly-sources/2026/week_07/20261018T093323977084Z').frozenWeekProjections(2026, 5);
  const p5 = pmap(JSON.parse(fz.body.toString('utf8')));
  for (const id of ['1313697754907697152', '1316165875291668480', '1314007486205804544']) {
    const mm = week5Matchups(id), wm = model(W7, id, { week: 5, projRows: p5, now: Date.parse('2026-10-20T08:00:00Z'), matchups: mm }), rv = w.FIEReview.build({ wm, matchups: mm });
    assert.ok(rv.available, `${id}: review available`);
    assert.ok(rv.hindsight.points + 1e-9 >= rv.submitted.points && rv.hindsight.points + 1e-9 >= rv.projectionBest.points, `${id}: hindsight is the upper bound`);
    near(rv.leftOnBench, rv.hindsight.points - rv.submitted.points, 0.011, `${id}: left on bench`);
    if (wm.format.bestBall) assert.strictEqual(rv.submitted.points, rv.hindsight.points, 'Best Ball submitted = hindsight');
  }
  assert.ok(!w.FIEReview.build({ wm: model(W6, '1313697754907697152'), matchups: W6.J(`${L('1313697754907697152')}/matchups/6`) }).available, 'unscored week → not available');
}
/* 4 · Portfolio: my players equal roster contents (A-26); changes feed */
{
  const results = ['1313697754907697152', '1316165875291668480', '1313696967989157888'].map(id => ({ wm: model(W6, id) }));
  const mp = w.FIEPortfolioViews.myPlayers(results);
  const expectStarts = results.reduce((s, r) => s + r.wm.me.submitted.filter(e => e.p).length, 0);
  assert.strictEqual(mp.startSlots, expectStarts, 'starting slots = filled submitted starters');
  const expectRostered = results.reduce((s, r) => s + new Set([...r.wm.me.submitted.filter(e => e.p).map(e => e.pid), ...r.wm.me.bench.map(p => p.pid), ...r.wm.me.reserve.map(p => p.pid), ...r.wm.me.taxi.map(p => p.pid)]).size, 0);
  assert.strictEqual(mp.rows.reduce((s, x) => s + x.rostered, 0), expectRostered, 'rostered memberships = roster contents');
  const snap = w.FIEPortfolioViews.snapshot(results, 1000), anyPid = mp.rows.find(x => x.starts > 0).pid;
  const prev = { ...snap, at: 1000, statuses: { ...snap.statuses, [anyPid]: 'Out' } };
  const tx = { '1313697754907697152': [{ type: 'waiver', status: 'complete', roster_ids: [results[0].wm.key.rosterId], adds: { '9999': results[0].wm.key.rosterId }, drops: null, settings: { waiver_bid: 7 }, status_updated: 2000 },
    { type: 'waiver', status: 'complete', roster_ids: [results[0].wm.key.rosterId], adds: { '9998': results[0].wm.key.rosterId }, status_updated: 500 }] };
  const f = w.FIEPortfolioViews.changes(prev, results, tx, { names: { 9999: 'Test Add' } });
  assert.ok(f.items.some(i => i.kind === 'status' && i.pid === anyPid && i.from === 'Out'), 'status change detected');
  assert.ok(f.items.some(i => i.kind === 'tx' && /Waiver won: Test Add \(\$7\)/.test(i.text)), 'my processed claim since last visit');
  assert.ok(!f.items.some(i => /9998/.test(i.text)), 'transactions before the last visit are not repeated');
  assert.ok(w.FIEPortfolioViews.changes(null, results, {}).firstVisit, 'first visit has no feed');
  const byeP = mp.rows.find(x => x.status?.code === 'BYE');
  if (byeP) assert.ok(!w.FIEPortfolioViews.changes({ ...snap, statuses: { ...snap.statuses, [byeP.pid]: null } }, results, {}).items.some(i => i.pid === byeP.pid), 'a bye week is not a status change');
}
/* 5 · Lineup context, WAIVER_ADD alert, Best Ball keeps waiver tasks only */
{
  const id = '1313697754907697152', wm = model(W6, id), sub = wm.me.submitted.find(e => e.p && e.p.recValue > 5);
  const c = wm.lineupContext(sub.pid); assert.ok(c && (c.role === 'starter' ? c.delta <= 0 : true), 'lineup context for a starter is a cost');
  const r = waivers(W6, id, wm), a = w.FIEAlerts.forLeague(wm, { leagueId: id, leagueName: 'R', waivers: r });
  assert.ok(a.some(x => x.code === 'WAIVER_ADD' && x.tier === 'recommended' && x.route === 'waivers'), 'WAIVER_ADD is Recommended and routes to Waivers');
  const bid = '1314007486205804544', bwm = model(W6, bid), br = waivers(W6, bid, bwm), ba = w.FIEAlerts.forLeague(bwm, { leagueName: 'BB', waivers: br });
  assert.ok(ba.every(x => ['WAIVER_ADD', 'DATA_ISSUE', 'CHOP_RISK'].includes(x.code)), 'Best Ball: no lineup tasks, waiver adds allowed');
}
/* 6 · Team-code aliases (R0 WP0.7 class of bug): every alias resolves to the same game */
{
  const g = (t) => w.FIEGameState.forTeam(schedule, t, { week: 6, season: 2026, now: Date.parse('2026-10-15T18:00:00Z') });
  for (const [a, b] of [['LA', 'LAR'], ['JAC', 'JAX'], ['WSH', 'WAS'], ['OAK', 'LV'], ['SD', 'LAC']]) { const x = g(a), y = g(b); assert.ok(x.kickoff === y.kickoff && x.bye === y.bye && x.opp === y.opp, `${a} = ${b}`); }
  window.state.weekly = { schedule: w.FIEGameState.parseCsv(W6.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv')) };
  for (const [a, b] of [['LA', 'LAR'], ['JAC', 'JAX'], ['WSH', 'WAS'], ['OAK', 'LV'], ['SD', 'LAC']]) assert.strictEqual(w.FIEProjectionResolver.isVerifiedBye({ team: a }, 6, 2026), w.FIEProjectionResolver.isVerifiedBye({ team: b }, 6, 2026), `resolver ${a} = ${b}`);
  assert.strictEqual(w.FIEProjectionResolver.isVerifiedBye({ team: 'LAR' }, 6, 2026), false, 'Rams play in Week 6');
}
/* 7 · WP-V1 switch: calibrated is the shipped default (signed off 19 Oct, R3 WP3.0); rule of thumb → ±22 % ranges and a more extreme win estimate */
{
  const id = '1313697754907697152', cal = model(W6, id), pol = JSON.parse(JSON.stringify(w.FIE_UI_POLICY));
  assert.strictEqual(pol.variance.mode, 'calibrated', 'WP-V1 signed off: calibrated by default');
  pol.variance.mode = 'rule_of_thumb';
  const base = w.FIEWeekModel.build({ league: W6.J(L(id)), rosters: W6.J(`${L(id)}/rosters`), users: W6.J(`${L(id)}/users`), matchups: W6.J(`${L(id)}/matchups/6`), projRows: p6, catalog, schedule, week: 6, season: 2026,
    now: Date.parse('2026-10-15T18:00:00Z'), fetchedAt: Date.parse('2026-10-15T18:00:00Z'), managedRosterId: myRoster(W6, id), format: w.FIECore.FormatRegistry.profile('REDRAFT'), policy: pol });
  assert.ok(cal.winEstimate.calibrated && cal.winEstimate.dot === null && base.winEstimate.dot === 'amber', 'amber "uncalibrated" dot only in rule-of-thumb mode');
  const wr = cal.me.submitted.find(e => e.p && e.p.position === 'WR' && e.p.active.value > 3).p;
  assert.ok(wr.range.calibrated && wr.range.label === 'P10–P90' && Math.abs(wr.range.high - wr.active.value * 1.91) < 1e-9, 'WR P10–P90 from calibration');
  const dst = cal.me.submitted.find(e => e.p && e.p.position === 'DEF').p;
  assert.ok(!dst.range.calibrated, 'D/ST keeps the rule of thumb (no calibration data)');
  assert.ok(Math.abs(cal.winEstimate.value - 0.5) < Math.abs(base.winEstimate.value - 0.5), `calibrated estimate less extreme: ${cal.winEstimate.value} vs ${base.winEstimate.value}`);
  assert.strictEqual(base.me.recommended.optimizedTotal, cal.me.recommended.optimizedTotal, 'calibration never changes lineup recommendations (means unchanged)');
}
console.log(`UI v10 R2: PASS (waivers ${leaguesChecked} leagues / ${rowsChecked} rows exact, market, review, portfolio, context, alerts, aliases)`);
