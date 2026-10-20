#!/usr/bin/env node
/* UI v10 R4 contract tests ("fix & tidy", 21 Oct 2026) — pure modules in a VM sandbox on the committed Week 7 capture
 * (20261020T175919279901Z, Tuesday evening) plus small synthetic fixtures. No network, no DOM.
 *   1 · R4.1 lineup changes per slot: a player is never shown at a slot he is not eligible for (Week 7 report:
 *       "Start Stevenson (RB) at WR for Boston"); moved starters are listed; the deltas add up to the gain.
 *   2 · R4.2 Best Ball bench: starters + bench + IR + taxi = roster, in every league of the capture.
 *   3 · R4.3 adds disabled (Sleeper settings.disable_adds = 1): no waiver rows, no to-do item; other leagues unaffected.
 *   4 · R4.4 results: eliminated / chopped / survived with ranks among teams that played; unscored weeks never "Chopped".
 *   5 · R4.5 classic simulation guards (static): scored weeks skipped, survival array, pool readiness, title columns.
 *   6 · R4.6 refresh cadence in policy (validated), R4.7 to-do columns, FAAB context, Team byes include this week.
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
const ctx = vm.createContext({ window, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Intl, Promise, setTimeout });
for (const f of ['app/generated/runtime-contracts.js', 'app/core/core-services.js', 'app/generated/ui-decision-policy.js', 'app/core/status.js', 'app/core/projection-service.js',
  'app/core/scoring-core.js', 'app/core/distribution.js', 'app/core/game-state.js', 'app/core/week-model.js', 'app/core/alerts.js',
  'app/core/waivers.js', 'app/core/team-views.js']) vm.runInContext(read(f), ctx, { filename: f });
const w = window;
const pmap = rows => new Map((rows || []).map(r => [String(r.player_id), r]));
const schedule = w.FIEGameState.index(W7.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const p7 = pmap(W7.J('https://api.sleeper.com/projections/nfl/2026/7?season_type=regular'));
const catRaw = JSON.parse(read('data/research/app/player-catalog.json')), catalog = new Map(Object.entries({ ...(catRaw.identity_only_players || {}), ...(catRaw.players || {}) }));
const cfg = JSON.parse(read('config/league-portfolio.json')), entryOf = id => cfg.leagues.find(l => String(l.league_id) === String(id)) || {};
function myRoster(S, id) { const u = (S.J(`${L(id)}/users`) || []).find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')); const r = u && S.J(`${L(id)}/rosters`).find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id)); return r ? r.roster_id : null; }
const TUE = Date.parse('2026-10-20T19:00:00Z');
const fmtOf = id => w.FIECore.FormatRegistry.profile(entryOf(id).format || 'REDRAFT');
function model(id, { now = TUE } = {}) {
  return w.FIEWeekModel.build({ league: W7.J(L(id)), rosters: W7.J(`${L(id)}/rosters`), users: W7.J(`${L(id)}/users`), matchups: W7.J(`${L(id)}/matchups/7`) || [], projRows: p7, catalog, schedule, week: 7, season: 2026, now, fetchedAt: now,
    managedRosterId: myRoster(W7, id), format: fmtOf(id) });
}
const ids = W7.ids().filter(id => myRoster(W7, id));
assert.ok(ids.length >= 20, `Week 7 capture has my rosters (${ids.length})`);
const results = {};

/* 1 · R4.1 lineup changes per slot — synthetic constellation of the Week 7 report */
{
  const T = 'AAA', O = 'BBB';
  const pl = { q: ['QB', { pass_yd: 400 }], a: ['RB', { rush_yd: 150 }], b: ['RB', { rush_yd: 140 }], w1: ['WR', { rec_yd: 130 }], boston: ['WR', { rec_yd: 113 }], te: ['TE', { rec_yd: 80 }],
    strange: ['TE', null], mcm: ['WR', { rec_yd: 120 }], metcalf: ['WR', { rec_yd: 125 }], stevenson: ['RB', { rush_yd: 114 }], goff: ['QB', { pass_yd: 300 }] };
  const cat = new Map(Object.entries(pl).map(([id, [pos]]) => [id, { full_name: id, position: pos, team: T }]));
  const proj = new Map(Object.entries(pl).filter(([, [, st]]) => st).map(([id, [pos, st]]) => [id, { player_id: id, team: T, stats: st, player: { position: pos, team: T } }]));
  const sched = w.FIEGameState.index([{ season: '2026', week: '7', game_type: 'REG', home_team: T, away_team: O, gameday: '2026-10-25', gametime: '13:00', result: '', home_score: '', away_score: '' }]);
  const starters = ['q', 'a', 'b', 'w1', 'boston', 'te', 'strange', 'mcm'], all = [...starters, 'metcalf', 'stevenson', 'goff'];
  const league = { league_id: 'SYN', name: 'synthetic', roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'FLEX', 'BN', 'BN', 'BN', 'BN'], scoring_settings: { pass_yd: 0.04, rush_yd: 0.1, rec_yd: 0.1 }, settings: {} };
  const wm = w.FIEWeekModel.build({ league, rosters: [{ roster_id: 1, owner_id: 'u', players: all, starters, reserve: [], taxi: [] }], users: [{ user_id: 'u', username: 'me' }],
    matchups: [{ roster_id: 1, matchup_id: 1, starters, players: all }], projRows: proj, catalog: cat, schedule: sched, week: 7, season: 2026, now: TUE, fetchedAt: TUE, managedRosterId: 1, format: w.FIECore.FormatRegistry.profile('REDRAFT') });
  const rec = wm.me.recommended, PR = w.FIECore.PositionRegistry;
  assert.ok(Math.abs(rec.gain - 12.6) < 0.01, `gain = Metcalf 12.5 + Stevenson 11.4 − Boston 11.3 − Strange 0 = 12.6 (got ${rec.gain})`);
  assert.strictEqual(rec.changes.length, 2, 'two players enter from the bench');
  for (const c of rec.changes) { const p = wm.player(c.inPid); assert.ok(PR.eligible(p.position, c.slot), `${p.name} (${p.position}) is never shown at ${c.slot}`); }
  const st = rec.changes.find(c => c.inPid === 'stevenson');
  assert.strictEqual(st.slot, 'FLEX', 'Stevenson (RB) enters at FLEX, not WR');
  assert.ok(['boston', 'strange'].includes(st.outPid), 'he displaces Boston or Strange');
  assert.ok(Math.abs(rec.changes.reduce((s, c) => s + c.delta, 0) - rec.gain) < 0.02, 'the deltas add up to the lineup gain (no full-value deltas)');
  for (const e of rec.starters) if (e.p) assert.ok(PR.eligible(e.p.position, e.slot), `recommended lineup: ${e.p.name} eligible at ${e.slot}`);
  assert.deepStrictEqual(new Set(rec.starters.filter(e => e.pid).map(e => e.pid)), new Set(['q', 'a', 'b', 'w1', 'te', 'mcm', 'metcalf', 'stevenson']), 'optimal set');
  // Same-named slots do not churn: W1 stays in his WR slot, Q at QB.
  assert.strictEqual(rec.starters[3].pid, 'w1', 'W1 keeps his WR slot');
  for (const m of rec.moves) assert.ok(['start', 'move', 'bench'].includes(m.kind), 'move kinds');
  assert.ok(rec.moves.filter(m => m.kind === 'bench').map(m => m.pid).sort().join() === 'boston,strange', 'Boston and Strange go to the bench');
  // Real leagues: no change anywhere names an ineligible slot, deltas add up.
  let checked = 0;
  for (const id of ids) { const m = model(id), r = m.me.recommended; for (const c of r.changes) { const p = m.player(c.inPid); if (c.slot) { assert.ok(PR.eligible(p.position, c.slot), `${id}: ${p.name} ${p.position} at ${c.slot}`); checked++; } }
    if (r.changes.length) assert.ok(Math.abs(r.changes.reduce((s, c) => s + c.delta, 0) - r.gain) < 0.05, `${id}: deltas add up to the gain`); }
  results.lineup = { gain: rec.gain, changes: rec.changes.map(c => `${c.inPid}@${c.slot}→${c.outPid}`), realChangesChecked: checked };
}

/* 2 · R4.2 Best Ball bench is complete */
{
  let bb = 0;
  for (const id of ids) {
    const m = model(id), r = W7.J(`${L(id)}/rosters`).find(x => Number(x.roster_id) === Number(myRoster(W7, id))), mm = (W7.J(`${L(id)}/matchups/7`) || []).find(x => Number(x.roster_id) === Number(r.roster_id));
    const all = new Set((mm?.players || r.players || []).map(String)); if (!all.size) continue;
    const shown = new Set([...m.me.submitted.filter(e => e.pid).map(e => e.pid), ...m.me.bench.map(p => p.pid), ...m.me.reserve.map(p => p.pid), ...m.me.taxi.map(p => p.pid)]);
    for (const pid of all) assert.ok(shown.has(pid) || !m.player(pid), `${entryOf(id).name || id}: ${m.player(pid)?.name || pid} appears in lineup, bench, IR or taxi`);
    if (m.format.bestBall) { bb++; const inLine = new Set(m.me.submitted.filter(e => e.pid).map(e => e.pid)); assert.ok(m.me.bench.every(p => !inLine.has(p.pid)), 'bench never repeats a lineup player'); }
  }
  const among = model('1402643913583398912');
  assert.ok(among.me.bench.some(p => /Kincaid/.test(p.name)), 'Among Us Guillotine 3: Dalton Kincaid (BUF bye) is on the bench');
  results.bench = { bestBallLeagues: bb, amongUsBench: among.me.bench.length };
}

/* 3 · R4.3 adds disabled */
{
  const disabled = ids.filter(id => Number(W7.J(L(id)).settings?.disable_adds) === 1);
  assert.deepStrictEqual(disabled.sort(), ['1314007486205804544', '1314008320385748992', '1332838151168724992'], 'BestBall – Pro, BestBall – Prime, Stoned Lack Bestball Dynasty 4');
  for (const id of ids) {
    const m = model(id);
    const wv = w.FIEWaivers.build({ wm: m, league: W7.J(L(id)), rosters: W7.J(`${L(id)}/rosters`), managedRosterId: myRoster(W7, id), horizon: [{ week: 7, projRows: p7 }], schedule, season: 2026, now: TUE, catalog, adp: new Map(), seasonRows: new Map(), constraints: entryOf(id).research_constraints || [] });
    const al = w.FIEAlerts.forLeague(m, { leagueId: id, leagueName: id, waivers: wv });
    if (disabled.includes(id)) { assert.ok(wv.addsDisabled && !wv.rows.length && /disabled/.test(wv.issues[0]), `${id}: no waiver rows`); assert.ok(!al.some(a => a.code === 'WAIVER_ADD'), `${id}: no waiver to-do`); }
    else assert.ok(!wv.addsDisabled, `${id}: adds allowed`);
  }
  results.addsDisabled = disabled.length;
}

/* 4 · R4.4 results — v10-data results() on synthetic chopped matchups (VM with a stub data client) */
{
  const urls = new Map();
  const dctx = vm.createContext({ window: { FIE_UI_POLICY: w.FIE_UI_POLICY, FIEPortfolioConfig: { config: { sleeper_username: 'c0nstant1n' } },
    FIEDataClient: { json: async url => { if (!urls.has(url)) throw new Error('no fixture ' + url); return JSON.parse(JSON.stringify(urls.get(url))); }, text: async () => '' } }, console, Math, Number, String, Object, Array, Map, Set, JSON, Date, Promise, setTimeout, URLSearchParams });
  vm.runInContext(read('app/v10/v10-data.js'), dctx, { filename: 'app/v10/v10-data.js' });
  const D = dctx.window.FIEV10Data, base = 'https://api.sleeper.app/v1/league/X';
  const users = [{ user_id: 'me', username: 'C0nstant1n' }, { user_id: 'b' }, { user_id: 'c' }, { user_id: 'd' }];
  const set = (myPlayersNow, rows) => { urls.clear(); urls.set(`${base}/users`, users);
    urls.set(`${base}/rosters`, [{ roster_id: 1, owner_id: 'me', players: myPlayersNow }, { roster_id: 2, owner_id: 'b', players: ['x'] }, { roster_id: 3, owner_id: 'c', players: ['y'] }, { roster_id: 4, owner_id: 'd', players: [] }]);
    urls.set(`${base}/matchups/6`, rows); };
  const run = () => D.results({ id: 'X' }, 6);
  return (async () => {
    // eliminated before Week 6: my row is empty
    set([], [{ roster_id: 1, players: [], points: 0 }, { roster_id: 2, players: ['x'], points: 100 }, { roster_id: 3, players: ['y'], points: 90 }, { roster_id: 4, players: [], points: 0 }]);
    let r = await run(); assert.ok(r.eliminated && r.rank === null && r.teams === 2, 'eliminated before the week: no rank, 2 teams played');
    // survived: 2nd of 3 that played (an earlier-eliminated team does not count)
    set(['p'], [{ roster_id: 1, players: ['p'], points: 95 }, { roster_id: 2, players: ['x'], points: 100 }, { roster_id: 3, players: ['y'], points: 90 }, { roster_id: 4, players: [], points: 0 }]);
    r = await run(); assert.ok(!r.eliminated && r.rank === 2 && r.teams === 3 && !r.lowest, 'survived: 2/3');
    // chopped this week: lowest of those who played
    set([], [{ roster_id: 1, players: ['p'], points: 80 }, { roster_id: 2, players: ['x'], points: 100 }, { roster_id: 3, players: ['y'], points: 90 }, { roster_id: 4, players: [], points: 0 }]);
    r = await run(); assert.ok(!r.eliminated && r.rank === 3 && r.lowest, 'chopped: 3/3, lowest');
    // unscored week (all zero): never "chopped"
    set(['p'], [{ roster_id: 1, players: ['p'], points: 0 }, { roster_id: 2, players: ['x'], points: 0 }, { roster_id: 3, players: ['y'], points: 0 }]);
    r = await run(); assert.ok(!r.lowest, 'unscored week: not chopped');
    results.results = 'ok';
  })().then(rest);
}

function rest() {
/* 5 · R4.5 classic simulation guards (static: the classic engine needs the full DOM app) */
{
  const de = read('app/decision-engines.js'), lg = read('app/v10/v10-league.js');
  assert.ok(/lastScored=Number\(state\.league\?\.settings\?\.last_scored_leg\)\|\|0/.test(de) && /for\(let w=Math\.max\(start,lastScored\+1\);w<=end;w\+\+\)/.test(de), 'classic season simulation skips weeks Sleeper has scored');
  assert.ok(/function choppedSimulationContext[^]*?const ids=\(state\.rosters\|\|\[\]\)\.filter\(r=>\(r\.players\|\|\[\]\)\.length>0\)/.test(de), 'classic chopped simulation only contains teams still in the field');
  assert.ok(/async function poolsReady/.test(lg) && /await poolsReady\(\)/.test(lg), 'v10 waits until the classic engine has players on every active roster');
  assert.ok(/Array\.isArray\(r\.survival\)\?r\.survival\[0\]/.test(lg), 'chopped survival array → this week');
  assert.ok(/a team has no players in the simulation/.test(lg), 'empty team models are an error, never odds');
  assert.ok(/data-odds2=/.test(lg) && /Title<\/th>/.test(lg) && /Win league<\/th>/.test(lg), 'title / win-league columns');
  assert.ok(/oddsCache\.set\(`\$\{id\}:\$\{week\}`/.test(lg) && /oddsCache\.get\(`\$\{id\}:\$\{wm\.key\.week\}`\)/.test(lg), 'results cached per league and week and repainted');
  results.sim = 'ok';
}

/* 6 · R4.6 / R4.7 */
{
  const pol = JSON.parse(read('config/ui-decision-policy.json')).refresh_seconds;
  assert.deepStrictEqual(pol, { live: 120, idle: 900, offseason: 21600 }, 'refresh cadence in policy');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(w.FIE_UI_POLICY.refresh_seconds)), pol, 'generated policy matches config');
  const sh = read('app/v10/v10-shell.js');
  assert.ok(/async function cadence/.test(sh) && /setTimeout\(\(\)=>\{if\(document\.visibilityState==='visible'/.test(sh) && !/setInterval\(\(\)=>\{if\(document\.visibilityState/.test(sh), 'cadence-driven refresh replaces the fixed 2-minute interval');
  // To-do columns: every action and monitor row has an issue and an action.
  const per = ids.map(id => { const m = model(id); return w.FIEAlerts.forLeague(m, { leagueId: id, leagueName: entryOf(id).name || id }); });
  const q = w.FIEAlerts.queue(per);
  assert.ok(q.actions.length > 0 && q.actions.every(a => a.issue && a.action !== undefined), 'league tasks carry issue + action');
  for (const a of q.actions) if (a.items.some(x => ['SWAP', 'SWAP_URGENT', 'STARTER_UNAVAILABLE', 'EMPTY_SLOT'].includes(x.code))) assert.ok(a.action.length > 0, `${a.leagueName}: lineup task has an action`);
  assert.ok(q.monitor.every(a => a.issue && a.action !== undefined), 'monitor rows carry issue + action');
  const ov = read('app/v10/v10-overview.js');
  assert.ok(/<span>League<\/span><span>Issue<\/span><span>Proposed action<\/span><span>Locks in<\/span>/.test(ov), 'one header row for the to-do grid');
  assert.ok(/\$\{wk\?`Week \$\{k\.esc\(wk\)\}`:'This week'\}/.test(ov), 'Leagues table says "Week N"');
  // FAAB context
  const id = '1313696967989157888', m = model(id);
  const mk = w.FIEWaivers.market({ league: W7.J(L(id)), rosters: W7.J(`${L(id)}/rosters`), users: W7.J(`${L(id)}/users`), transactions: W7.J(`${L(id)}/transactions/7`) || [], positionOf: pid => m.player(pid)?.position, nameOf: pid => m.player(pid)?.name || pid, managedRosterId: myRoster(W7, id),
    lastWeek: { week: 6, matchups: [{ roster_id: 1, players: ['a'], points: 120 }, { roster_id: 2, players: ['b'], points: 140 }] } });
  const act = mk.budgets.filter(b => b.active);
  assert.ok(act.every(b => b.avgPoints > 0), 'avg points per week for every active team');
  assert.strictEqual(mk.budgets.find(b => b.rosterId === 2).lastWeekRank, 1, 'last week rank among teams that played');
  assert.ok(!/Winning bids by position/.test(read('app/v10/v10-waivers.js')) && !/<th class="v10-num">Spent<\/th>/.test(read('app/v10/v10-waivers.js')), 'median table and Spent column removed');
  // Team byes include the current week
  const teamIn = { wm: m, rosters: W7.J(`${L(id)}/rosters`), horizon: [{ week: 7, projRows: p7 }, { week: 8, projRows: new Map() }], schedule, catalog, season: 2026, seasonRows: new Map(), adp: new Map(), projRows: p7 };
  const t = w.FIETeamViews.team(teamIn);
  assert.strictEqual(t.byes[0].week, 7, 'Byes start with this week'); assert.ok(t.byes[0].current, 'marked as this week');
  const jaxBye = t.byes[0].players.some(p => /Strange/.test(p.name));
  assert.ok(jaxBye, 'Chopped – Drive: Brenton Strange (JAX) on bye in Week 7');
  assert.ok(t.byes[0].cost >= 0, 'bye cost is non-negative');
  results.ui = { monitorRows: q.monitor.length, actionRows: q.actions.length, byesW7: t.byes[0].players.map(p => p.name), byeCostW7: t.byes[0].cost };
}
console.log('PASS UI v10 R4: lineup changes per slot, Best Ball bench complete, adds disabled, chopped results, simulation guards, refresh cadence, to-do columns, FAAB context, byes this week');
console.log(JSON.stringify(results));
}
