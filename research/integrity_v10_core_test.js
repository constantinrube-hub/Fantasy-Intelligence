#!/usr/bin/env node
/* UI v10 R1 core contract tests — pure modules in a VM sandbox on the committed Week 6
 * pre-kickoff capture. Covers scoring parity with the classic scorer, distribution parity with the
 * classic engine, DST-correct kickoffs, WeekModel lineup/lock/chopped/best-ball behaviour, the
 * Doubtful policy, recommendation tiers and cross-league alert grouping. No network, no DOM. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), zlib = require('zlib'), assert = require('assert');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const CAPTURE = 'data/research/prospective/weekly-sources/2026/week_06/20261015T174631408136Z';
const receipts = new Map();
for (const f of fs.readdirSync(path.join(ROOT, CAPTURE))) if (f.endsWith('-response-receipt.json')) { const r = JSON.parse(read(`${CAPTURE}/${f}`)); receipts.set(r.endpoint, r); }
const raw = ep => zlib.gunzipSync(fs.readFileSync(path.join(ROOT, receipts.get(ep).path))).toString('utf8');
const J = ep => JSON.parse(raw(ep));
const L = id => `https://api.sleeper.app/v1/league/${id}`;

function sandbox() {
  const window = { state: {} };
  const ctx = vm.createContext({ window, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Intl });
  for (const f of ['app/generated/runtime-contracts.js', 'app/core/core-services.js', 'app/generated/ui-decision-policy.js', 'app/core/status.js',
    'app/core/scoring-core.js', 'app/core/distribution.js', 'app/core/game-state.js', 'app/core/week-model.js', 'app/core/alerts.js']) vm.runInContext(read(f), ctx, { filename: f });
  return window;
}
const w = sandbox();
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

/* 1 · Scoring parity with the scorer classic actually uses: index.html › scoreSleeperProjectionStatsV89
 *     (V8.9 rebinds window.scoreSleeperProjectionStats onto it). Every projection row × 5 leagues. */
{
  const html = read('index.html'), a = html.indexOf('const PUBLIC_ALIASES='), b0 = html.indexOf('function scoreSleeperProjectionStatsV89(', a);
  assert.ok(a > 0 && b0 > a, 'classic V8.9 scoring compiler located');
  const b = html.indexOf('\n}\n', b0) + 2;
  const classic = vm.createContext({ state: { league: null }, window: { FIERuntimeContracts: w.FIERuntimeContracts }, Number, Object, String, RegExp, Set, Math });
  vm.runInContext(`function getSetting(keys,d){for(const k of keys){const v=Number(state.league?.scoring_settings?.[k]);if(Number.isFinite(v))return v;}return d;}
function leaguePPR(){return getSetting(['rec'],0);}function activeSeason(){return 2026;}
${html.slice(a, b)}
this.classicScore=scoreSleeperProjectionStatsV89;`, classic);
  const rows = J('https://api.sleeper.com/projections/nfl/2026/6?season_type=regular');
  let compared = 0, defDiff = 0;
  for (const id of ['1313697754907697152', '1316165875291668480', '1343914986388353024', '1331042152091766784', '1313696967989157888']) {
    const league = J(L(id)); classic.state.league = league;
    for (const r of rows) {
      const pos = String(r.player?.position || '').toUpperCase(), p = { position: pos };
      const x = classic.classicScore(r.stats, p), y = w.FIEScoringCore.score(r.stats, league.scoring_settings, pos);
      assert.ok(x === y || (x !== null && y !== null && Math.abs(x - y) < 1e-9), `scoring parity ${id} ${r.player_id} ${pos}: ${x} vs ${y}`);
      compared++;
    }
  }
  /* The naive Σ stat×weight would score player return yards for a team DEF (JAX +0.63): must not. */
  const jax = rows.find(r => r.player_id === 'JAX'), lg = J(L('1313697754907697152')).scoring_settings;
  near(w.FIEScoringCore.score(jax.stats, lg, 'DEF'), 8.04, 0.005, 'JAX DEF without pr_yd');
  var SCORING_COMPARED = compared;
}
/* 2 · Distribution parity with app/decision-engines.js › playerDistribution */
{
  const src = read('app/decision-engines.js'), i = src.indexOf('function playerDistribution('), j = src.indexOf('\n}\n', i) + 2;
  const eng = vm.createContext({ Math, Number, weeklyLineupValue: p => p.mu, window: {} });
  vm.runInContext(`function finite(v){const n=Number(v);return v===null||v===undefined||v===''||!Number.isFinite(n)?null:n;}function clampV(x,a,b){return Math.max(a,Math.min(b,x));}\n${src.slice(i, j)}`, eng);
  for (const [mu, lo, hi] of [[12, 9.36, 14.64], [0, 0, 0], [25, null, null], [3.2, 2.5, 3.9], [40, 10, 70]]) {
    const a = vm.runInContext('playerDistribution', eng)({ mu, weeklyFloor: lo, weeklyCeiling: hi }), b = w.FIEDistribution.player({ mu, low: lo, high: hi });
    near(a.sd, b.sd, 1e-12, `sd parity ${mu}`); near(a.mu, b.mu, 1e-12, `mu parity ${mu}`);
  }
  near(w.FIEDistribution.winProbability({ mu: 100, sd: 10 }, { mu: 100, sd: 10 }), 0.5, 1e-9, 'even matchup');
  assert.ok(w.FIEDistribution.winProbability({ mu: 110, sd: 10 }, { mu: 100, sd: 10 }) > 0.7, 'favourite');
}
/* 3 · Kickoff conversion is DST-correct */
assert.strictEqual(w.FIEGameState.easternToUtc('2026-10-15', '20:15'), Date.UTC(2026, 9, 16, 0, 15), 'EDT');
assert.strictEqual(w.FIEGameState.easternToUtc('2026-11-08', '13:00'), Date.UTC(2026, 10, 8, 18, 0), 'EST');
const schedule = w.FIEGameState.index(raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const tnf = [...schedule.games.values()].filter(g => g.season === 2026 && g.week === 6).sort((a, b) => a.kickoff - b.kickoff)[0];
assert.strictEqual(tnf.kickoff, Date.UTC(2026, 9, 16, 0, 15), 'Week 6 TNF kickoff');

/* WeekModel inputs from the capture */
const proj = new Map(J('https://api.sleeper.com/projections/nfl/2026/6?season_type=regular').map(r => [String(r.player_id), r]));
const catalogRaw = JSON.parse(read('data/research/app/player-catalog.json'));
const catalog = new Map(Object.entries({ ...(catalogRaw.identity_only_players || {}), ...(catalogRaw.players || {}) }));
const fetchedAt = Date.parse('2026-10-15T17:46:31Z');
function myRoster(id) { const users = J(`${L(id)}/users`), rosters = J(`${L(id)}/rosters`); const u = users.find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')); return rosters.find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id)).roster_id; }
function model(id, { now = Date.parse('2026-10-15T18:00:00Z'), format = 'REDRAFT', tweak = null } = {}) {
  const rows = tweak ? new Map([...proj].map(([k, v]) => [k, tweak(k, v)])) : proj;
  return w.FIEWeekModel.build({ league: J(L(id)), rosters: J(`${L(id)}/rosters`), users: J(`${L(id)}/users`), matchups: J(`${L(id)}/matchups/6`),
    projRows: rows, catalog, schedule, week: 6, season: 2026, now, fetchedAt, managedRosterId: myRoster(id), format: w.FIECore.FormatRegistry.profile(format) });
}
/* 4 · ReDraft – Pro pregame: optimizer total equals the classic optimal lineup (84.32) */
const redraft = model('1313697754907697152');
assert.strictEqual(redraft.slots.length, 9);
near(redraft.me.recommended.optimizedTotal, 84.32, 0.05, 'optimal lineup total vs classic 84.32');
assert.ok(redraft.me.submitted.every(e => e.p), 'submitted lineup complete');
assert.ok(redraft.opponent && redraft.winEstimate && redraft.winEstimate.calibrated === true && redraft.winEstimate.dot === null, 'H2H opponent and calibrated win estimate (WP-V1 on: no amber dot)');
assert.ok(redraft.me.recommended.gain >= 0 && Math.abs(redraft.me.recommended.gain - (redraft.me.recommended.optimizedTotal - redraft.me.recommended.submittedTotal)) < 0.02, 'gain = full re-optimisation delta');
for (const c of redraft.me.recommended.changes) assert.ok(w.FIECore.PositionRegistry.eligible(redraft.player(c.inPid).position, c.slot), 'changes are slot-legal');
/* 4b · Questionable swap-in gets a fallback (Lamar Q → Bryce Young if ruled out) */
{ const fb = (redraft.me.recommended.fallbacks || [])[0];
  assert.ok(fb && redraft.player(fb.forPid).status.monitor && fb.pid && redraft.player(fb.pid).position === 'QB' && fb.gain >= 0, 'Questionable fallback present'); }
/* 5 · After TNF: locked players never move; TNF players are final or live */
const afterTnf = model('1313697754907697152', { now: Date.parse('2026-10-17T12:00:00Z') });
for (const c of afterTnf.me.recommended.changes) { assert.ok(!afterTnf.player(c.inPid).game.locked, 'no locked player swapped in'); if (c.outPid) assert.ok(!afterTnf.player(c.outPid).game.locked, 'no locked player swapped out'); }
const tnfTeams = new Set([tnf.home, tnf.away]);
for (const e of afterTnf.me.submitted) if (e.p && tnfTeams.has(e.p.team)) assert.ok(e.p.game.locked, 'TNF starter locked');
/* 6 · Chopped – Drive: verified active field */
const chop = model('1313696967989157888', { format: 'CHOPPED' });
assert.strictEqual(chop.field.activeCount, 13); assert.strictEqual(chop.field.eliminatedCount, 5); assert.strictEqual(chop.field.verified, true);
assert.ok(chop.field.myRank >= 1 && chop.field.myRank <= 13 && chop.opponent === null && chop.winEstimate === null, 'chopped has field, no H2H');
/* 7 · Best Ball: automatic lineup, no lineup tasks */
const bb = model('1314007486205804544', { format: 'REDRAFT_BESTBALL' });
assert.strictEqual(bb.me.recommended.tier, 'none');
assert.ok(w.FIEAlerts.forLeague(bb, { leagueName: 'BB' }).every(a => a.code === 'DATA_ISSUE'), 'no Best Ball lineup tasks');
/* 8 · Submitted starters who cannot play (IDP Dynasty 39 at capture: Goff/Van Ginkel/Battle BYE, Hockenson Out) */
const idp = model('1331042152091766784', { format: 'DYNASTY' });
const idpAlerts = w.FIEAlerts.forLeague(idp, { leagueName: 'IDP 39' });
for (const name of ['Jared Goff', 'T.J. Hockenson']) assert.ok(idpAlerts.some(a => a.code === 'STARTER_UNAVAILABLE' && a.playerName === name && a.tier === 'urgent'), `${name} urgent`);
/* 9 · Doubtful = out (tie-break only), replacement suggested, inactives time */
const victim = redraft.me.submitted.find(e => e.p && e.p.active.value > 5 && !e.p.status.code).pid;
const dbt = model('1313697754907697152', { tweak: (k, v) => k === victim ? { ...v, player: { ...v.player, injury_status: 'Doubtful' } } : v });
const dp = dbt.player(victim);
assert.strictEqual(dp.status.code, 'Doubtful'); near(dp.recValue, dp.active.value * 0.01, 1e-9, 'Doubtful tie-break');
const da = w.FIEAlerts.forLeague(dbt, { leagueName: 'R' }).find(a => a.code === 'STARTER_DOUBTFUL');
assert.ok(da && da.tier === 'urgent' && da.inactivesAt === dp.game.kickoff - 90 * 60000, 'Doubtful alert with inactives time');
assert.ok(dbt.me.recommended.changes.some(c => c.outPid === victim), 'Doubtful starter is replaced');
/* 10 · Thresholds (user decision D5) */
for (const [g, t] of [[3, 'urgent'], [2.99, 'recommended'], [1, 'recommended'], [0.5, 'close'], [0.25, 'close'], [0.2, 'none']]) assert.strictEqual(w.FIEWeekModel.tierFor(g), t, `tier ${g}`);
/* 11 · Cross-league grouping */
const a1 = { code: 'STARTER_UNAVAILABLE', tier: 'urgent', playerId: '1', playerName: 'X', status: 'Out', dedupKey: 'player:1:Out', leagueName: 'A', priority: 'HIGH', lockAt: 5 };
const merged = w.FIEAlerts.portfolio([[a1], [{ ...a1, leagueName: 'B' }], [{ code: 'EMPTY_SLOT', tier: 'urgent', dedupKey: 'c:empty', leagueName: 'C', lockAt: 1 }]]);
assert.strictEqual(merged.length, 2); assert.ok(merged.find(x => x.grouped && x.grouped.length === 2), 'one grouped line per player');
assert.strictEqual(merged[0].code, 'EMPTY_SLOT', 'earlier lock first within a tier');
/* 11b · WeekModel never takes byes from classic state: even a resolver that calls everyone a bye changes nothing;
 *       Matthew Stafford (LAR, nflverse "LA") starts in Genesis Dynasty and plays ARI in Week 6. */
{
  w.FIEProjectionResolver = { isVerifiedBye: () => true };
  const gen = model('1316165875291668480', { format: 'DYNASTY' });
  delete w.FIEProjectionResolver;
  const staff = gen.me.submitted.find(e => e.p && e.p.name === 'Matthew Stafford');
  assert.ok(staff && staff.p.status.code !== 'BYE' && !staff.p.game.bye && staff.p.game.opp === 'ARI', `Stafford not a bye: ${staff && JSON.stringify(staff.p.status)}`);
}
/* 12 · Queue: one action row per league, monitor grouped per player, empty-slot fill not listed twice */
{
  const empty = model('1313697754907697152', { tweak: null });
  const forced = { ...empty, me: { ...empty.me, submitted: empty.me.submitted.map((e, i) => i === 3 ? { slot: e.slot, pid: null, p: null } : e),
    recommended: { ...empty.me.recommended, tier: 'urgent', changes: [{ slot: empty.me.submitted[3].slot, inPid: empty.me.bench[0].pid, outPid: null, delta: 5 }] } } };
  const al = w.FIEAlerts.forLeague(forced, { leagueName: 'E' });
  assert.ok(al.some(a => a.code === 'EMPTY_SLOT' && /Start /.test(a.detail)), 'empty-slot alert names the fill');
  assert.ok(!al.some(a => /over empty slot/.test(a.title || '')), 'empty-slot fill not repeated as a swap');
  const idpA = w.FIEAlerts.forLeague(idp, { leagueId: 'idp', leagueName: 'IDP 39' }), rdA = w.FIEAlerts.forLeague(redraft, { leagueId: 'rd', leagueName: 'ReDraft' });
  const q = w.FIEAlerts.queue([idpA, rdA, [{ code: 'MONITOR_Q', tier: 'monitor', playerId: '9', playerName: 'Q', dedupKey: 'player:9:Q', leagueName: 'X' }], [{ code: 'MONITOR_Q', tier: 'monitor', playerId: '9', playerName: 'Q', dedupKey: 'player:9:Q', leagueName: 'Y' }]]);
  assert.strictEqual(q.actions.filter(t => t.leagueId === 'idp').length, 1, 'one action row for the IDP league');
  const it = q.actions.find(t => t.leagueId === 'idp');
  assert.ok(it.tier === 'urgent' && /can't play/.test(it.title) && it.items.some(a => /Hockenson/.test(a.title)), 'IDP row summarises and lists the items');
  assert.ok(q.monitor.some(m => m.grouped && m.grouped.length === 2), 'Questionable grouped per player across leagues');
  for (const a of idpA.filter(a => a.code === 'STARTER_UNAVAILABLE')) assert.ok(Number.isFinite(a.lockAt), `bye/out alert has a lock time (${a.playerName})`);
}
console.log(`UI v10 core: PASS (scoring parity ${SCORING_COMPARED} rows on 5 leagues, ReDraft optimal ${redraft.me.recommended.optimizedTotal}, tier ${redraft.me.recommended.tier} +${redraft.me.recommended.gain}, chopped rank ${chop.field.myRank}/${chop.field.activeCount} margin ${chop.field.marginToCut})`);
