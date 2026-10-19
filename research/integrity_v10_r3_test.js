#!/usr/bin/env node
/* UI v10 R3 contract tests — pure modules in a VM sandbox on committed captures (no network, no DOM).
 *   · WP3.7 waiver horizon with injured players: last-game carry-over (72 h guard), Sleeper decides returns in
 *     later weeks, IR-slot players rejoin the pool, injured starters are never suggested as drops, fill-in label
 *     with a causal check, "if he stays out" gain, long_term_zero override.
 * Later R3 work packages append their sections below.
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
const pmap = rows => new Map((rows || []).map(r => [String(r.player_id), r]));
const schedule = w.FIEGameState.index(W6.raw('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'));
const p6 = pmap(W6.J('https://api.sleeper.com/projections/nfl/2026/6?season_type=regular')), p7 = pmap(W7.J('https://api.sleeper.com/projections/nfl/2026/7?season_type=regular'));
const catRaw = JSON.parse(read('data/research/app/player-catalog.json')), catalog = new Map(Object.entries({ ...(catRaw.identity_only_players || {}), ...(catRaw.players || {}) }));
const cfg = JSON.parse(read('config/league-portfolio.json')), entryOf = id => cfg.leagues.find(l => String(l.league_id) === String(id)) || {};
const adp = new Map(zlib.gunzipSync(fs.readFileSync(path.join(ROOT, 'data/research/market/sleeper/2026/season_market_2026-09-30.jsonl.gz'))).toString().split('\n').filter(Boolean).map(JSON.parse)
  .map(r => [String(r.sleeper_id), { dynasty: r.adp?.adp_dynasty_ppr, dynasty2qb: r.adp?.adp_dynasty_2qb, redraft: r.adp?.adp_ppr, stats: r.stats }]));
function myRoster(S, id) { const u = (S.J(`${L(id)}/users`) || []).find(x => [x.username, x.display_name].some(v => String(v || '').toLowerCase() === 'c0nstant1n')); const r = u && S.J(`${L(id)}/rosters`).find(r => r.owner_id === u.user_id || (r.co_owners || []).includes(u.user_id)); return r ? r.roster_id : null; }
const T6 = Date.parse('2026-10-15T18:00:00Z');
function model(S, id, { week = 6, projRows = p6, now = T6, policy } = {}) {
  return w.FIEWeekModel.build({ league: S.J(L(id)), rosters: S.J(`${L(id)}/rosters`), users: S.J(`${L(id)}/users`), matchups: S.J(`${L(id)}/matchups/${week}`) || [], projRows, catalog, schedule, week, season: 2026, now, fetchedAt: now,
    managedRosterId: myRoster(S, id), format: w.FIECore.FormatRegistry.profile(entryOf(id).format || 'REDRAFT'), ...(policy ? { policy } : {}) });
}
function waivers(S, id, wm, extra = {}) {
  return w.FIEWaivers.build({ wm, league: S.J(L(id)), rosters: S.J(`${L(id)}/rosters`), managedRosterId: myRoster(S, id), horizon: [{ week: 6, projRows: wm.__p6 || p6 }, { week: 7, projRows: p7 }], schedule, season: 2026, now: T6,
    catalog, adp, seasonRows: adp, constraints: entryOf(id).research_constraints || [], ...extra });
}
const clone = x => JSON.parse(JSON.stringify(x));
const ids = W6.ids().filter(id => myRoster(W6, id));
const results = {};

/* 1 · Last-game carry-over (WeekModel): Out/Doubtful + positive Sleeper projection for the modelled week = previous game's tag */
{
  // In the game week itself Sleeper projects 0 for every Out/Doubtful player → never carried over (W6 Thursday capture).
  let carried = 0, outs = 0;
  for (const id of ids) { const wm = model(W6, id); for (const e of [...wm.me.submitted, ...wm.me.bench.map(p => ({ p }))]) { const s = e.p?.status; if (!s) continue; if (s.carriedOver) carried++; if (s.code === 'Out' || s.code === 'Doubtful') outs++; } }
  assert.strictEqual(carried, 0, 'game week: no Out/Doubtful designation is treated as last week\'s');
  assert.ok(outs > 0, 'the game-week capture has Out/Doubtful players on my rosters');
  // Week 7 model on Tuesday 20 Oct with the capture taken during Week 6: Sunday's tags carry over where Sleeper already projects Week 7.
  const tue = Date.parse('2026-10-20T08:00:00Z');
  let found = null;
  for (const id of W7.ids().filter(x => myRoster(W7, x))) {
    const wm = model(W7, id, { week: 7, projRows: p7, now: tue });
    for (const e of [...wm.me.submitted, ...wm.me.bench.map(p => ({ p }))]) if (e.p?.status?.carriedOver) { found = { id, p: e.p }; break; }
    if (found) break;
  }
  assert.ok(found, 'Week 7 on Tuesday: at least one carried-over Out/Doubtful player on my rosters');
  assert.ok(!found.p.status.unavailable && found.p.status.monitor && found.p.recValue === found.p.active.value && found.p.active.value > 0, `${found.p.name}: monitored at full value`);
  assert.ok(/·prev$/.test(found.p.status.short) && /last game/.test(found.p.status.label), 'chip and label say "last game"');
  // 72 h guard: the same player inside the designation window (≤ 72 h before his kickoff) is treated as out again.
  const late = found.p.game.kickoff - 48 * 3600e3;
  const wmLate = model(W7, found.id, { week: 7, projRows: p7, now: late }), pl = wmLate.player(found.p.pid);
  assert.ok(pl.status.unavailable && !pl.status.carriedOver && pl.recValue < pl.active.value, `${found.p.name}: 48 h before kickoff the tag is current again`);
  results.carry = `${found.p.name} (${found.p.status.code}) carried over Tue, current again 48 h before kickoff`;
}

/* 2 · Later weeks: Sleeper decides; players in an IR slot rejoin the pool; injured starters are never drops */
{
  let back = 0, reserveBack = 0, protectedInjured = 0, rows = 0;
  for (const id of ids) {
    const wm = model(W6, id), r = waivers(W6, id, wm); if (r.eliminated) continue;
    for (const x of r.returning || []) {
      if (x.week) { back++; assert.ok((p7.get(x.pid) && w.FIEScoringCore.score(p7.get(x.pid).stats || {}, W6.J(L(id)).scoring_settings, wm.player(x.pid).position) > 0), `${x.name}: counted back only when Sleeper projects him`); }
      if (x.week && x.inReserve) reserveBack++;
    }
    const inj = new Set(r.protectedDrops.filter(p => p.reason === 'injured').map(p => p.pid)); protectedInjured += inj.size;
    for (const q of [...r.rows, ...r.watch]) { rows++; if (q.drop) assert.ok(!inj.has(q.drop.pid), `${id}: ${q.drop.name} is an injured starter and never the suggested drop`);
      if (q.drop) { const s = wm.player(q.drop.pid).status; assert.ok(!(s.unavailable && s.code !== 'BYE' && inj.has(q.drop.pid)), 'no injured starter dropped'); } }
  }
  assert.ok(back >= 3 && reserveBack >= 1 && protectedInjured >= 3, `returns observed (${back}, IR slot ${reserveBack}), injured starters protected (${protectedInjured})`);
  // Genesis NFL GM League: Omar Cooper sits in the IR slot and Sleeper projects him in Week 7 → the Week 7 baseline counts him.
  const g = '1342896584593018880', wm = model(W6, g), r = waivers(W6, g, wm), oc = (r.returning || []).find(x => x.pid === '13276');
  assert.ok(oc && oc.inReserve && oc.week === 7, 'Omar Cooper (IR slot) is back in Week 7 per Sleeper');
  const pol = clone(w.FIE_UI_POLICY); pol.waivers.long_term_zero = ['IR'];
  const forced = waivers(W6, g, wm, { policy: pol });
  assert.ok(r.baseline[1].total > forced.baseline[1].total, `IR player counted in W7 (${r.baseline[1].total}) vs long_term_zero override (${forced.baseline[1].total})`);
  results.returns = `${back} returns (${reserveBack} from IR slots), ${protectedInjured} injured starters protected, ${rows} rows`;
}

/* 3 · Fill-in: my top healthy RB/WR ruled Out for Week 6 (as Sleeper does it: tag Out, projection removed), back in Week 7 */
{
  let leagues = 0, fills = [], inflated = 0;
  for (const id of ids) {
    const base = model(W6, id); if (!base.me.submitted.length || base.format.bestBall) continue;
    const st = base.me.submitted.filter(e => e.p && ['RB', 'WR'].includes(e.p.position) && !e.p.status.code && e.p.active.value > 6 && p7.get(e.p.pid)).sort((a, b) => b.p.active.value - a.p.active.value)[0];
    if (!st) continue; const star = st.p;
    const q6 = new Map(p6); const row = clone(p6.get(star.pid)); row.player.injury_status = 'Out'; row.stats = {}; q6.set(star.pid, row);
    const wm = model(W6, id, { projRows: q6 }); wm.__p6 = q6;
    assert.ok(wm.player(star.pid).status.unavailable && !wm.player(star.pid).status.carriedOver, `${star.name}: Out in his game week`);
    const r = waivers(W6, id, wm); if (r.eliminated) continue; leagues++;
    const me = (r.returning || []).find(x => x.pid === star.pid);
    if (!me || me.week !== 7) continue; // Sleeper does not have him in the W7 best lineup → nothing to fill
    assert.ok(r.protectedDrops.some(p => p.pid === star.pid && p.reason === 'injured') || !r.rows.some(x => x.drop?.pid === star.pid), `${star.name} is never suggested as the drop`);
    for (const x of r.rows.filter(x => x.fillIn)) {
      assert.ok(x.gains[0] >= 0.25 && x.gains[1] <= 0.25 && x.fillIn.gainIfOut - x.gains[1] >= 0.5, `${x.name}: gain W6 ${x.gains[0]}, W7 ${x.gains[1]}, if out ${x.fillIn.gainIfOut}`);
      assert.ok(x.ifOut && x.ifOut.gainHorizon >= x.gainHorizon + 0.5 - 1e-9, `${x.name}: "if he stays out" ${x.ifOut?.gainHorizon} ≥ ${x.gainHorizon} + 0.5`);
      assert.ok(x.position !== 'DEF' && x.position !== 'K', `${x.name}: a D/ST or kicker is never a fill-in for a skill player`);
      if (x.fillIn.pid === star.pid) fills.push(`${x.name} (${entryOf(id).name || id}) +${x.gainHorizon}, if ${star.name} stays out +${x.ifOut.gainHorizon}`);
    }
    // R2 behaviour for comparison: zeroing him in every week over-rates the best fill-in.
    const f = r.rows.find(x => x.fillIn?.pid === star.pid);
    if (f) { const pol = clone(w.FIE_UI_POLICY); pol.waivers.long_term_zero = ['Out']; const old = waivers(W6, id, wm, { policy: pol }).rows.find(x => x.pid === f.pid);
      assert.ok(old && old.gainHorizon >= f.gainHorizon + 0.5, `R2-style zeroing inflates ${f.name}: ${old?.gainHorizon} vs ${f.gainHorizon}`); inflated++; }
  }
  assert.ok(leagues >= 5 && fills.length >= 1 && inflated >= 1, `fill-ins found (${fills.length}) in ${leagues} constructed leagues`);
  results.fillIn = `${fills.length} fill-ins in ${leagues} leagues, e.g. ${fills[0]}`;
}

console.log(`UI v10 R3: PASS (${Object.values(results).join(' · ')})`);
