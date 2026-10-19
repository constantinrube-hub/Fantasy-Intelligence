#!/usr/bin/env node
/* UI v10 R3 contract tests — pure modules in a VM sandbox on committed captures (no network, no DOM).
 *   · WP3.7 waiver horizon with injured players: last-game carry-over (72 h guard), Sleeper decides returns in
 *     later weeks, IR-slot players rejoin the pool, injured starters are never suggested as drops, fill-in label
 *     with a causal check, "if he stays out" gain, long_term_zero override.
 *   · WP3.2/3.3 Players and Team (FIETeamViews): owners equal rosters, values equal the Lineup's, position ranks,
 *     depth = full re-optimisation, bye costs, real Sleeper slots, no season proxy for D/ST.
 *   · WP3.4 Trades (FIETrades): empty trade = 0, a trade and its reverse cancel exactly, receiving never lowers a
 *     lineup, locked players exclude this week, entry-class floor, roster-size drops.
 *   · WP3.1 Lab (FIELab): projection error on the scored Week 5 fixture (MAE/bias recomputed), unscored weeks are
 *     "not scored" and skipped by last-N, model-state source counts.
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
  'app/core/waivers.js', 'app/core/review.js', 'app/core/portfolio.js', 'app/core/team-views.js', 'app/core/trades.js', 'app/core/lab.js']) vm.runInContext(read(f), ctx, { filename: f });
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

/* 4 · Players and Team (WP3.2/3.3) on every captured league */
{
  let leagues = 0, players = 0, thin = 0;
  for (const id of ids) {
    const wm = model(W6, id), rosters = W6.J(`${L(id)}/rosters`), mine = rosters.find(r => r.roster_id === myRoster(W6, id));
    if (!(mine.players || []).length) continue; leagues++;
    const inp = { wm, rosters, projRows: p6, horizon: [{ week: 6, projRows: p6 }, { week: 7, projRows: p7 }], schedule, catalog, season: 2026, seasonRows: adp, adp };
    const pl = w.FIETeamViews.players(inp), rostered = new Map();
    for (const r of rosters) for (const k of ['players', 'reserve', 'taxi']) for (const x of r[k] || []) if (!rostered.has(String(x))) rostered.set(String(x), r.roster_id);
    for (const r of pl.rows) { players++;
      assert.strictEqual(r.fa, !rostered.has(r.pid), `${id} ${r.name}: free agent ⇔ on no roster`);
      if (!r.fa) assert.strictEqual(r.mine, rostered.get(r.pid) === mine.roster_id, `${id} ${r.name}: "yours" ⇔ on my roster`);
      const p = wm.player(r.pid); assert.ok(Math.abs((r.week ?? 0) - (p.status.unavailable ? 0 : (p.active.value ?? 0))) < 0.006, `${id} ${r.name}: this week's value equals the Lineup's`);
      assert.ok(Math.abs(r.next - r.values.reduce((a, v) => a + (v ?? 0), 0)) < 0.02, `${r.name}: horizon sum`); }
    const t = w.FIETeamViews.team(inp);
    for (const x of t.strength) assert.ok(x.rank >= 1 && x.rank <= x.of && x.points <= x.best + 1e-9, `${id} ${x.position}: rank ${x.rank}/${x.of}`);
    for (const d of t.depth) { if (d.recovered !== null) assert.ok(d.recovered >= 0 && d.recovered <= 1, `${d.name}: recovered share`);
      const c = wm.lineupContext(d.pid); if (c && c.role === 'starter') assert.ok(Math.abs(d.loss + c.delta) < 0.006, `${d.name}: loss = lineup context`); }
    for (const b of t.byes) assert.ok(b.cost >= -1e-9, `${id} W${b.week}: bye cost ≥ 0`);
    assert.strictEqual(t.roster.filter(r => !['BN', 'IR', 'TAXI'].includes(r.slot)).length, wm.me.submitted.filter(e => e.p).length, `${id}: starters keep their Sleeper slots`);
    assert.strictEqual(t.roster.filter(r => r.slot === 'IR').length, (mine.reserve || []).length, `${id}: IR slots`);
    assert.ok(t.roster.filter(r => r.position === 'DEF').every(r => r.ros === null), `${id}: no season-per-game proxy for D/ST (bucket scoring)`);
    for (const x of t.thin) for (const st of x.starters) assert.ok(Math.max(st.recovered, st.faRecovered) < t.thinAt, `${id} ${st.name}: thin = neither bench nor best free agent covers ${t.thinAt}`);
    for (const d of t.depth) if (d.recovered !== null && d.value >= 1 && Math.max(d.recovered, d.faRecovered) < t.thinAt) assert.ok(t.thin.some(x => x.position === d.position), `${id} ${d.name}: uncovered starter is flagged`);
    thin += t.thin.length;
  }
  assert.ok(leagues >= 15 && players > 3000, `players/team on ${leagues} leagues, ${players} player rows`);
  assert.strictEqual(w.FIE_UI_POLICY.team.thin_recovery, 0.25, 'thin threshold 25 % (decision 19 Oct)');
  assert.ok(thin / leagues < 0.5, `thin flags are rare: ${thin} in ${leagues} leagues`);
  results.team = `players/team on ${leagues} leagues (${players} rows, ${thin} thin positions)`;
}

/* 5 · Trades (WP3.4) */
{
  const hz = [{ week: 6, projRows: p6 }, { week: 7, projRows: p7 }];
  const ev = (id, wm, rosters, partner, send, receive, extra = {}) => w.FIETrades.evaluate({ wm, rosters, partnerRosterId: partner, send, receive, horizon: hz, schedule, catalog, season: 2026, seasonRows: adp, adp,
    constraints: entryOf(id).research_constraints || [], rosterPositions: W6.J(L(id)).roster_positions, now: T6, ...extra });
  let checked = 0;
  for (const id of ids) {
    const wm = model(W6, id), rosters = W6.J(`${L(id)}/rosters`), me = rosters.find(r => r.roster_id === myRoster(W6, id));
    if (!(me.players || []).length) continue;
    const other = rosters.find(r => r.roster_id !== me.roster_id && (r.players || []).length); if (!other) continue;
    const zero = ev(id, wm, rosters, other.roster_id, [], []);
    assert.ok([...zero.me.delta, ...zero.partner.delta].every(d => d === null || Math.abs(d) < 1e-9) && zero.me.rateDelta === 0, `${id}: empty trade changes nothing`);
    // my best active starter for their best active non-starter-of-mine player
    const actMe = (me.players || []).map(String).filter(x => !(me.reserve || []).map(String).includes(x) && !(me.taxi || []).map(String).includes(x));
    const actThem = (other.players || []).map(String).filter(x => !(other.reserve || []).map(String).includes(x) && !(other.taxi || []).map(String).includes(x));
    const best = ids2 => ids2.map(x => wm.player(x)).filter(p => p && p.position !== 'DEF').sort((a, b) => (b.recValue || 0) - (a.recValue || 0))[0];
    const a = best(actMe), b = best(actThem); if (!a || !b) continue;
    const t = ev(id, wm, rosters, other.roster_id, [a.pid], [b.pid]);
    // Reverse on the post-trade rosters cancels exactly
    const post = JSON.parse(JSON.stringify(rosters)), pm = post.find(r => r.roster_id === me.roster_id), po = post.find(r => r.roster_id === other.roster_id);
    pm.players = pm.players.filter(x => String(x) !== a.pid).concat(b.pid); po.players = po.players.filter(x => String(x) !== b.pid).concat(a.pid);
    const r = ev(id, wm, post, other.roster_id, [b.pid], [a.pid]);
    t.me.delta.forEach((d, k) => { if (d !== null) assert.ok(Math.abs(d + r.me.delta[k]) < 0.011 && Math.abs(t.partner.delta[k] + r.partner.delta[k]) < 0.011, `${id}: trade + reverse = 0 (W${hz[k].week})`); });
    assert.ok(Math.abs(t.me.rateDelta + r.me.rateDelta) < 0.011, `${id}: season-rate reverse`);
    // Receiving only never lowers my lineup; sending only never lowers theirs
    const recv = ev(id, wm, rosters, other.roster_id, [], [b.pid]); assert.ok(recv.me.delta.every(d => d === null || d >= -1e-9) && recv.partner.delta.every(d => d === null || d <= 1e-9), `${id}: receiving only`);
    if (recv.roster.limit !== null && actMe.length >= recv.roster.limit) assert.ok(recv.roster.meDrops >= 1, `${id}: a full roster must drop for a 0-for-1`);
    checked++;
  }
  assert.ok(checked >= 15, `trades checked on ${checked} leagues`);
  // Locked players: after TNF (Sat 17 Oct) a trade involving a Thursday player does not count Week 6.
  const sat = Date.parse('2026-10-17T12:00:00Z');let lockedSeen = null;
  for (const id of ids) { const wm = model(W6, id, { now: sat }), rosters = W6.J(`${L(id)}/rosters`), me = rosters.find(r => r.roster_id === myRoster(W6, id));
    const lockedPid = (me.players || []).map(String).find(x => wm.player(x)?.game?.locked); if (!lockedPid) continue;
    const other = rosters.find(r => r.roster_id !== me.roster_id && (r.players || []).length); const t = w.FIETrades.evaluate({ wm, rosters, partnerRosterId: other.roster_id, send: [lockedPid], receive: [], horizon: hz, schedule, catalog, season: 2026, seasonRows: adp, adp, now: sat });
    assert.ok(t.counted[0] === false && t.me.delta[0] === null && t.locked.length === 1 && t.counted[1] === true, 'a locked traded player excludes this week only'); lockedSeen = wm.player(lockedPid).name; break; }
  assert.ok(lockedSeen, 'some league has a player locked after TNF');
  // Entry-class floor (Genesis NFL GM League: 2025+ only) — a veteran received is flagged.
  const g = '1342896584593018880', gw = model(W6, g), gr = W6.J(`${L(g)}/rosters`), gme = gr.find(r => r.roster_id === myRoster(W6, g)), go = gr.find(r => r.roster_id !== gme.roster_id && (r.players || []).length);
  const vet = [...p6.keys()].find(pid => { const c = catalog.get(pid); return c && Number(c.years_exp) >= 3 && gw.player(pid)?.position === 'QB'; });
  const gt = w.FIETrades.evaluate({ wm: gw, rosters: gr, partnerRosterId: go.roster_id, send: [], receive: [vet], horizon: hz, schedule, catalog, season: 2026, constraints: entryOf(g).research_constraints || [], now: T6 });
  assert.ok(gt.issues.some(x => /entry class/.test(x)), 'entry-class floor flagged');
  results.trades = `trades on ${checked} leagues (reverse = 0, receive-only ≥ 0, lock: ${lockedSeen}, entry floor)`;
}

/* 6 · Research Lab computations (WP3.1) */
{
  const { week5Matchups } = require('./ui_replay/scenarios'), { CaptureStore } = require('./ui_replay/fixtures');
  const p5 = pmap(JSON.parse(new CaptureStore('data/research/prospective/weekly-sources/2026/week_07/20261018T093323977084Z').frozenWeekProjections(2026, 5).body.toString('utf8')));
  const id = '1313697754907697152', league = W6.J(L(id)), wm = model(W6, id), mm5 = week5Matchups(id);
  const ev = w.FIELab.evaluate({ projRows: p5, matchups: mm5, scoring: league.scoring_settings, positionOf: pid => wm.player(pid)?.position, nameOf: pid => wm.player(pid)?.name || pid });
  assert.ok(ev.scored && ev.n >= 50, `Week 5 evaluated: ${ev.n} players`);
  // Recompute one position by hand
  const wr = []; for (const m of mm5) for (const pid of m.players || []) { const r = p5.get(String(pid)); if (!r || wm.player(pid)?.position !== 'WR') continue; const pr = w.FIEScoringCore.score(r.stats || {}, league.scoring_settings, 'WR'); if (pr === null || pr < 3) continue; wr.push(Number(m.players_points[pid]) - pr); }
  const row = ev.byPosition.find(x => x.position === 'WR'); assert.ok(row && row.n === wr.length && Math.abs(row.mae - wr.reduce((s2, e) => s2 + Math.abs(e), 0) / wr.length) < 0.006 && Math.abs(row.bias - wr.reduce((s2, e) => s2 + e, 0) / wr.length) < 0.006, `WR MAE/bias recomputed (n=${wr.length})`);
  assert.ok(ev.misses.length === 10 && Math.abs(ev.misses[0].error) >= Math.abs(ev.misses[9].error), 'misses sorted by size');
  const pre = w.FIELab.evaluate({ projRows: p6, matchups: W6.J(`${L(id)}/matchups/6`), scoring: league.scoring_settings, positionOf: pid => wm.player(pid)?.position, nameOf: pid => pid });
  assert.ok(pre.scored === false && pre.n === 0, 'a pregame payload is "not scored", never a 100 % miss');
  const l4 = w.FIELab.lastN({ weeks: [{ week: 5, matchups: mm5 }, { week: 6, matchups: W6.J(`${L(id)}/matchups/6`) }], n: 4 });
  assert.ok(l4.size > 50 && [...l4.values()].every(x => x.games === 1 && x.weeks[0] === 5), 'last-N skips the unscored week');
  const wms = ids.slice(0, 6).map(x => { const m = model(W6, x); m.entry = { name: x }; return m; });
  const ms = w.FIELab.modelState({ wms, readiness: new Map(), researchView: null });
  assert.ok(ms.length === 6 && ms.every(r => Object.values(r.counts).reduce((s2, c) => s2 + Object.values(c).reduce((a, b) => a + b, 0), 0) === r.players && r.governed === 0), 'model state counts every rostered player; no governed rows in the captures');
  results.lab = `lab: Week 5 ${ev.n} players, MAE ${ev.overall.mae}, bias ${ev.overall.bias}`;
}

console.log(`UI v10 R3: PASS (${Object.values(results).join(' · ')})`);
