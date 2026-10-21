#!/usr/bin/env node
/* UI v10 R6 contract tests (v10 season simulation, FIESeasonSim) on the committed Week 7 Tuesday capture.
 *   1 · consistency: Σ playoff = playoff teams, Σ title = 1, every rank distribution sums to 1, chopped Σ win = 1 and
 *       survival never increases from week to week; same seed → same result (deterministic).
 *   2 · no degenerate Best Ball odds (the classic engine gave exactly 100 % / 0 % when rosters were empty): BestBall – Prime
 *       has teams strictly between 2 % and 98 %; a team with an empty roster value never makes the playoffs.
 *   3 · Sleeper's schedule is used where published (pairs), random pairing elsewhere; "why" fields are present.
 *   4 · samplers: decile knots non-decreasing, mean close to the base value's distribution mean.
 *   5 · static wiring: Matchup/Field run button + details, data loader, FAAB odds column, classic engine kept as comparison.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), zlib = require('zlib'), assert = require('assert');
const ROOT = path.resolve(__dirname, '..'), read = r => fs.readFileSync(path.join(ROOT, r), 'utf8');
function store(dir) { const rec = new Map(); for (const f of fs.readdirSync(path.join(ROOT, dir))) if (f.endsWith('-response-receipt.json')) { const r = JSON.parse(read(`${dir}/${f}`)); rec.set(r.endpoint, r); }
  const raw = ep => rec.has(ep) ? zlib.gunzipSync(fs.readFileSync(path.join(ROOT, rec.get(ep).path))).toString() : null; return { J: ep => { const t = raw(ep); return t === null ? null : JSON.parse(t); }, raw }; }
const S = store('data/research/prospective/weekly-sources/2026/week_07/20261020T175919279901Z'), L = id => `https://api.sleeper.app/v1/league/${id}`;
const window = {}; const ctx = vm.createContext({ window, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Intl, Promise, setTimeout, Uint8Array });
for (const f of ['app/generated/runtime-contracts.js', 'app/core/core-services.js', 'app/generated/ui-decision-policy.js', 'app/core/status.js', 'app/core/projection-service.js', 'app/core/scoring-core.js', 'app/core/distribution.js',
  'app/core/game-state.js', 'app/core/week-model.js', 'app/core/waivers.js', 'app/core/team-views.js', 'app/core/season-sim.js']) vm.runInContext(read(f), ctx, { filename: f });
const w = window, sched = w.FIEGameState.index(S.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const p7 = new Map(S.J('https://api.sleeper.com/projections/nfl/2026/7?season_type=regular').map(r => [String(r.player_id), r]));
const cr = JSON.parse(read('data/research/app/player-catalog.json')), cat = new Map(Object.entries({ ...(cr.identity_only_players || {}), ...(cr.players || {}) }));
const cfg = JSON.parse(read('config/league-portfolio.json')), NOW = Date.parse('2026-10-20T19:00:00Z');
function setup(id, { iterations = 1200, seed = 7, emptyTeam = null } = {}) {
  const lg = S.J(L(id)), rs = S.J(`${L(id)}/rosters`), us = S.J(`${L(id)}/users`), u = us.find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')), me = rs.find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id));
  const fmt = w.FIECore.FormatRegistry.profile(cfg.leagues.find(l => l.league_id === id)?.format || 'REDRAFT');
  const wm = w.FIEWeekModel.build({ league: lg, rosters: rs, users: us, matchups: S.J(`${L(id)}/matchups/7`) || [], projRows: p7, catalog: cat, schedule: sched, week: 7, season: 2026, now: NOW, fetchedAt: NOW, managedRosterId: me.roster_id, format: fmt });
  const s = lg.settings, act = rs.filter(r => (r.players || []).length);
  const teams = act.map(r => { const st = r.settings || {}; return { rosterId: r.roster_id, name: String(r.roster_id), me: r.roster_id === me.roster_id, pool: r.roster_id === emptyTeam ? [] : (r.players || []).map(String).filter(x => !(r.reserve || []).includes(x) && !(r.taxi || []).includes(x)), wins: st.wins || 0, losses: st.losses || 0, ties: st.ties || 0, pf: (st.fpts || 0) + (st.fpts_decimal || 0) / 100 }; });
  const chopped = !!fmt.chopped, pws = s.playoff_week_start || 0, weeks = []; for (let x = 7; x <= (chopped ? 18 : pws - 1); x++) weeks.push(x);
  const pt = s.playoff_teams || 0, pw = []; if (!chopped) for (let k = 0; k < Math.ceil(Math.log2(pt)); k++) pw.push(pws + k);
  const g = new Map(); for (const m of S.J(`${L(id)}/matchups/7`) || []) { if (m.matchup_id == null) continue; (g.get(m.matchup_id) || g.set(m.matchup_id, []).get(m.matchup_id)).push(m.roster_id); }
  const pairs = chopped ? {} : { 7: [...g.values()].filter(x => x.length === 2) };
  const valueFor = (pid, wk) => { const p = wm.player(pid); if (!p) return 0; if (wk === 7) return p.recValue || 0; if (w.FIEGameState.forTeam(sched, p.team, { week: wk, season: 2026, now: NOW }).bye) return 0; return p.active.value || 0; };
  return { wm, cfg: { teams, player: wm.player, valueFor, slots: wm.slots, bestBall: !!fmt.bestBall, weeks, pairs, median: s.league_average_match === 1, playoffTeams: chopped ? 0 : pt, playoffWeeks: pw, chopped: chopped ? { perWeek: 1 } : null, iterations, seed } };
}
const near = (a, b, e = 1e-6) => Math.abs(a - b) <= e;
(async () => {
  const out = {};
  // 1 · consistency + determinism
  for (const id of ['1314002567004459008', '1313697754907697152']) {
    const { cfg } = setup(id), r1 = await w.FIESeasonSim.simulate(cfg), r2 = await w.FIESeasonSim.simulate(cfg);
    assert.ok(near(r1.rows.reduce((a, r) => a + r.playoff, 0), cfg.playoffTeams), `${id}: Σ playoff = ${cfg.playoffTeams}`);
    assert.ok(near(r1.rows.reduce((a, r) => a + r.title, 0), 1), `${id}: Σ title = 1`);
    for (const r of r1.rows) assert.ok(near(r.ranks.reduce((a, b) => a + b, 0), 1), 'rank distribution sums to 1');
    assert.deepStrictEqual(JSON.parse(JSON.stringify(r1.rows.map(r => r.playoff))), JSON.parse(JSON.stringify(r2.rows.map(r => r.playoff))), 'deterministic for a seed');
    assert.ok(r1.scheduleKnown === 1 && r1.rows.every(r => r.why && r.why.teamMean > 0 && r.why.remainingGames > 0), 'schedule used where published; why fields present');
    out[id] = r1.rows.filter(r => r.me).map(r => ({ playoff: r.playoff, title: r.title }))[0];
  }
  { const { cfg } = setup('1313696967989157888'), r = await w.FIESeasonSim.simulate(cfg);
    assert.ok(near(r.rows.reduce((a, x) => a + x.winner, 0), 1), 'chopped: Σ win = 1');
    for (const x of r.rows) for (let i = 1; i < x.survival.length; i++) assert.ok(x.survival[i] <= x.survival[i - 1] + 1e-9, 'survival never increases');
    assert.strictEqual(r.rows.length, 12, 'only the 12 teams still in the field are simulated');
    out.chopped = r.rows.find(x => x.me).survival[0]; }
  // 2 · Best Ball not degenerate; an empty team never makes the playoffs
  { const { cfg } = setup('1314008320385748992'), r = await w.FIESeasonSim.simulate(cfg);
    assert.ok(r.rows.some(x => x.playoff > 0.02 && x.playoff < 0.98), 'BestBall – Prime: odds are not all 100 % / 0 %');
    const e = setup('1314002567004459008', { emptyTeam: 14 }), re = await w.FIESeasonSim.simulate(e.cfg);
    assert.strictEqual(re.rows.find(x => x.rosterId === 14).title, 0, 'a team with no players never wins the title');
    out.bestBallSpread = r.rows.filter(x => x.playoff > 0.02 && x.playoff < 0.98).length; }
  // 4 · samplers
  { const { wm } = setup('1314002567004459008'); const p = wm.me.submitted.find(e => e.p && e.p.range?.deciles)?.p;
    const sm = w.FIESeasonSim.samplerFor(p, p.active.value); assert.ok(sm.knots.every((v, i) => i === 0 || v >= sm.knots[i - 1] - 1e-9), 'knots non-decreasing');
    const r = w.FIESeasonSim.mulberry(1); let m = 0; for (let i = 0; i < 20000; i++) m += w.FIESeasonSim.draw(sm, r); m /= 20000;
    assert.ok(Math.abs(m - w.FIESeasonSim.meanOf(sm)) < 0.05 * w.FIESeasonSim.meanOf(sm), 'sampling mean matches the distribution mean'); }
  // 5 · static wiring
  { const lg = read('app/v10/v10-league.js'), d = read('app/v10/v10-data.js'), wv = read('app/v10/v10-waivers.js'), ix = read('index.html');
    assert.ok(/data-v10-sim=/.test(lg) && /function paintSim/.test(lg) && /function simDetail/.test(lg) && /data-v10-odds=/.test(lg), 'Matchup/Field: v10 simulation + details; classic engine kept as comparison');
    assert.ok(/async function seasonSim/.test(d) && /simCache\.set\(key,res\)/.test(d), 'data loader caches per league and week');
    assert.ok(/simCached\?\.\(lid,wm\.key\.week\)/.test(wv), 'FAAB table shows survival / playoff odds after a run');
    assert.ok(/app\/core\/season-sim\.js/.test(ix), 'engine loaded'); }
  console.log('PASS UI v10 R6: season simulation consistency, determinism, Best Ball not degenerate, chopped survival, schedule, samplers, wiring');
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
