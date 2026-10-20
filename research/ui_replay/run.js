#!/usr/bin/env node
/* FIE UI replay runner.
 *
 *   node research/ui_replay/run.js [--dist dist] [--suite classic|v10|all] [--only ID[,ID]] [--out ui-replay-output]
 *
 * Runs the real application (built dist/) against immutable provider captures
 * with a frozen browser clock. Tests interact through the DOM only. Reading
 * `window.state` is allowed for diagnostics; assigning to it is forbidden and
 * checked by research/integrity_ui_replay_no_injection_test.js.
 *
 * Exit code: 0 when every selected check passes, 1 otherwise.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.FIE_UI_PLAYWRIGHT || 'playwright');
const { serveDist, ProviderRouter } = require('./replay');
const { SCENARIOS, REFERENCE_LEAGUES: L } = require('./scenarios');

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : dflt; };
const DIST = path.resolve(opt('dist', 'dist'));
const OUT = path.resolve(opt('out', 'ui-replay-output'));
const SUITE = opt('suite', 'all');
const ONLY = (opt('only', '') || '').split(',').filter(Boolean);
fs.mkdirSync(OUT, { recursive: true });

const IGNORED_CONSOLE = [/Failed to load resource/i, /net::ERR_FAILED/i, /ERR_ABORTED/i];

// Classic checks open the classic UI explicitly, so they keep testing classic after default_ui switches to v10 (S7).
async function openApp(browser, origin, scenarioId, { width = 1440, height = 1000, path: urlPath = '/?ui=classic' } = {}) {
  const scenario = SCENARIOS[scenarioId];
  const router = new ProviderRouter(scenario);
  const context = await browser.newContext({ viewport: { width, height }, timezoneId: 'Europe/Berlin' });
  await router.install(context, origin);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${String(e.message || e).slice(0, 300)}`));
  page.on('console', m => { if (m.type() === 'error' && !IGNORED_CONSOLE.some(r => r.test(m.text()))) errors.push(`console: ${m.text().slice(0, 300)}`); });
  await page.clock.install({ time: new Date(scenario.clock) });
  await page.goto(origin + urlPath, { waitUntil: 'load' });
  await page.waitForSelector('#savedLeagueSelect option', { state: 'attached', timeout: 20000 });
  await page.waitForTimeout(1500);
  return { context, page, errors, router, scenario };
}

async function loadLeague(page, leagueId) {
  await page.selectOption('#savedLeagueSelect', leagueId);
  await page.click('#loadSavedLeagueBtn');
  await page.waitForFunction(id => window.state?.league?.league_id === id && window.state?.matched === true, leagueId, { timeout: 60000 });
  await page.waitForTimeout(4000); // live overlay + enrichment settle
}

async function nav(page, section, tab) {
  await page.locator(`#primaryNav [data-section="${section}"]`).first().click();
  await page.waitForTimeout(1200);
  if (tab) { await page.locator(`#subnav .tab[data-tab="${tab}"]`).first().click(); await page.waitForTimeout(2500); }
}

async function tableRows(page, scopeSelector) {
  return page.evaluate(sel => {
    const root = document.querySelector(sel); if (!root) return { headers: [], rows: [] };
    const table = [...root.querySelectorAll('table')].find(t => t.offsetParent !== null) || root.querySelector('table');
    if (!table) return { headers: [], rows: [] };
    const headers = [...table.querySelectorAll('thead th')].map(th => th.innerText.trim().toUpperCase());
    const rows = [...table.querySelectorAll('tbody tr')].map(tr => [...tr.children].map(td => td.innerText.trim()));
    return { headers, rows };
  }, scopeSelector);
}

const CHECKS = [];
const check = (id, suite, title, fn) => CHECKS.push({ id, suite, title, fn });

/* ------------------------------ classic suite ------------------------------ */

check('C-LOAD', 'classic', 'A-27: reference leagues load; Weekly and Waivers render without page errors', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    for (const id of [L.redraft, L.dynastySF, L.chopped, L.bestBall]) {
      await loadLeague(app.page, id);
      await nav(app.page, 'weekly', 'startsit');
      await nav(app.page, 'market', 'waivers');
    }
    return { pass: app.errors.length === 0, detail: { errors: app.errors.slice(0, 10), unmatched: [...app.router.unmatched].slice(0, 10) } };
  } finally { await app.context.close(); }
});

check('C-WEEK', 'classic', 'A-01: the live Sleeper week wins over an older bundled research snapshot', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'live-week-ahead');
  try {
    await loadLeague(app.page, L.redraft);
    await app.page.waitForTimeout(3000);
    await nav(app.page, 'weekly', 'startsit');
    const selected = await app.page.$eval('#weekSelect', el => el.value);
    const notice = await app.page.locator('#fieWeekSourceNotice').count() ? await app.page.locator('#fieWeekSourceNotice').innerText() : '';
    await app.page.screenshot({ path: path.join(OUT, 'C-WEEK.png'), fullPage: false });
    return { pass: selected === '7' && /Week 6/.test(notice), detail: { selectedWeek: selected, notice } };
  } finally { await app.context.close(); }
});

check('C-WAIVER', 'classic', 'A-24: unavailable players are never CLAIM without a legal IR slot; status column present', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.redraft);
    await nav(app.page, 'market', 'waivers');
    const t = await tableRows(app.page, '#mainArea');
    const iAdd = t.headers.indexOf('ADD'), iAct = t.headers.indexOf('ACTION'), iStatus = t.headers.indexOf('STATUS');
    const bad = [];
    for (const r of t.rows) {
      const name = (r[iAdd] || '').split('\n')[0], action = (r[iAct] || '').trim(), status = iStatus >= 0 ? (r[iStatus] || '') : '';
      if (/^(De'Von Achane|Michael Pittman)$/.test(name) && action === 'CLAIM') bad.push({ name, action, status });
      if (action === 'CLAIM' && /\b(IR|Out|Doubtful|Suspended|PUP|NA)\b/i.test(status)) bad.push({ name, action, status });
    }
    const firstBlocked = t.rows.findIndex(r => /\b(IR|Out|Doubtful|Suspended|PUP|NA)\b/.test(iStatus >= 0 ? (r[iStatus] || '') : ''));
    const lastClaim = t.rows.map(r => (r[iAct] || '').trim()).lastIndexOf('CLAIM');
    if (firstBlocked >= 0 && lastClaim > firstBlocked) bad.push({ ordering: `unavailable row ${firstBlocked + 1} above CLAIM row ${lastClaim + 1}` });
    await app.page.screenshot({ path: path.join(OUT, 'C-WAIVER.png'), fullPage: false });
    const firstClaim = t.rows.find(r => (r[iAct] || '').trim() === 'CLAIM');
    return { pass: iStatus >= 0 && bad.length === 0, detail: { headers: t.headers, violations: bad, firstClaim: firstClaim ? firstClaim[iAdd]?.split('\n')[0] : null } };
  } finally { await app.context.close(); }
});

check('C-DRAFT', 'classic', 'A-15: in-season leagues never show a draft-preparation task in All Leagues', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.dynastySF);
    await app.page.locator('#portfolioHomeBtn').click();
    await app.page.waitForTimeout(5000);
    const text = await app.page.locator('#portfolioPanel, main').first().innerText();
    const hits = (text.match(/Prepare draft|Draft prep|draft preparation/gi) || []).length;
    return { pass: hits === 0, detail: { draftTaskMentions: hits } };
  } finally { await app.context.close(); }
});

check('C-BANNER', 'classic', 'WP0.5: a submitted starter who cannot play (D/O/IR/BYE) raises a visible Weekly alert', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.idpDynasty);
    await nav(app.page, 'weekly', 'startsit');
    await app.page.waitForTimeout(4000);
    const has = await app.page.locator('#fieStarterAlert:visible').count();
    const text = has ? await app.page.locator('#fieStarterAlert').innerText() : '';
    await app.page.screenshot({ path: path.join(OUT, 'C-BANNER.png'), fullPage: false });
    return { pass: has > 0 && /can.t play/i.test(text) && /Hockenson/.test(text), detail: { text } };
  } finally { await app.context.close(); }
});

check('C-NOBYE', 'classic', 'WP0.7: a Rams starter is not reported as a bye (nflverse "LA" = Sleeper "LAR")', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.dynastySF); // Genesis Dynasty: Matthew Stafford (LAR) is a submitted starter, Rams play ARI in Week 6
    await nav(app.page, 'weekly', 'startsit');
    await app.page.waitForTimeout(4000);
    const has = await app.page.locator('#fieStarterAlert:visible').count();
    const text = has ? await app.page.locator('#fieStarterAlert').innerText() : '';
    return { pass: !/Stafford/.test(text) && app.errors.length === 0, detail: { alert: text || '(none)', errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('C-OVERLAY', 'classic', 'WP0.8: after the live roster overlay rebuilds players, Weekly still uses the Sleeper week projections (race sampled at 4 timings)', async ({ browser, origin }) => {
  // The overlay rebuild and the week fast path race; before WP0.8 about half of all loads ended on legacy
  // values. Sample several delays between league load and opening Weekly; every one must be right.
  // 158.5 = the optimal Week 6 lineup on Sleeper projections for this immutable capture (fresh load, and the v10 optimum).
  const runs = [];
  for (const delay of [0, 1500, 5000, 7000]) {
    const app = await openApp(browser, origin, 'w6-pregame');
    try {
      await app.page.selectOption('#savedLeagueSelect', L.dynasty30);
      await app.page.click('#loadSavedLeagueBtn');
      await app.page.waitForFunction(id => window.state?.league?.league_id === id && window.state?.matched === true, L.dynasty30, { timeout: 60000 });
      await app.page.waitForTimeout(delay);
      await nav(app.page, 'weekly', 'startsit');
      await app.page.waitForTimeout(6000);
      const t = await app.page.locator('#mainArea').innerText();
      runs.push({ delay, total: Number(((t.match(/Your projected total\s*\n?\s*([\d.,]+)/) || [])[1] || '').replace(',', '.')), errors: app.errors.slice(0, 3) });
    } finally { await app.context.close(); }
  }
  return { pass: runs.every(r => Math.abs(r.total - 158.5) <= 0.05 && !r.errors.length), detail: { expected: 158.5, runs } };
});

check('C-IRSTART', 'classic', 'WP0.9: the Weekly lineup never starts a player in a reserve (IR) or taxi slot', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.dynastyPrime); // Jalen Coker: healthy, projected 12.7, but in an IR slot in the live roster
    await nav(app.page, 'weekly', 'startsit');
    await app.page.waitForTimeout(4000);
    const r = await app.page.evaluate(() => {
      const st = window.state, rid = Number(st.selectedRoster), ro = (st.rosters || []).find(x => Number(x.roster_id) === rid); // read-only
      const out = new Set([...(ro?.reserve || []), ...(ro?.taxi || [])].map(String));
      const names = new Map((window.PLAYERS || []).filter(p => out.has(String(p.sleeperId))).map(p => [p.name, String(p.sleeperId)]));
      const rows = [...document.querySelectorAll('#mainArea table tbody tr')].map(tr => [...tr.children].map(td => td.innerText.split('\n')[0].trim()));
      return { reserveOrTaxi: [...names.keys()], started: rows.filter(x => x[0] && x[0] !== 'BENCH' && names.has(x[1])).map(x => `${x[0]} ${x[1]}`) };
    });
    return { pass: r.reserveOrTaxi.length > 0 && r.started.length === 0 && app.errors.length === 0, detail: { ...r, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('C-OUTSTART', 'classic', 'WP0.10: the Weekly lineup never starts a player who cannot play (Out/IR/PUP/SUS/NA, Doubtful = Out)', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.genesisGM); // Marques Sigle (DB): Out, Sleeper still projects 11.0 → was START on main
    await nav(app.page, 'weekly', 'startsit');
    await app.page.waitForTimeout(4000);
    const r = await app.page.evaluate(() => {
      const st = window.state, rid = Number(st.selectedRoster), ro = (st.rosters || []).find(x => Number(x.roster_id) === rid); // read-only
      const off = new Set([...(ro?.reserve || []), ...(ro?.taxi || [])].map(String)), ids = new Set((ro?.players || []).map(String));
      const cant = new Map((window.PLAYERS || []).filter(p => ids.has(String(p.sleeperId)) && !off.has(String(p.sleeperId)) && window.FIEStatus?.resolve?.(p)?.unavailable === true && Number(p.sleeperWeeklyProjection) > 0)
        .map(p => [p.name, window.FIEStatus.resolve(p).code]));
      const rows = [...document.querySelectorAll('#mainArea table tbody tr')].map(tr => [...tr.children].map(td => td.innerText.split('\n')[0].trim()));
      const total = (document.querySelector('#fie93WeeklyPanel')?.innerText.match(/Your projected total\s*\n?\s*([\d.,]+)/) || [])[1] || null;
      return { cannotPlay: [...cant].map(([n, c]) => `${n} (${c})`), started: rows.filter(x => x[0] && x[0] !== 'BENCH' && cant.has(x[1])).map(x => `${x[0]} ${x[1]}`), total };
    });
    return { pass: r.cannotPlay.length > 0 && r.started.length === 0 && app.errors.length === 0, detail: { ...r, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('C-REFRESH', 'classic', 'WP0.4: "Refresh weekly context" runs without a page error and keeps the lineup', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame');
  try {
    await loadLeague(app.page, L.redraft);
    await nav(app.page, 'weekly', 'startsit');
    await app.page.locator('#weeklyLoadBtn').click();
    await app.page.waitForTimeout(8000);
    const rows = (await tableRows(app.page, '#mainArea')).rows.length;
    const errs = app.errors.filter(e => /syncSeasonSelectV89|ReferenceError/.test(e));
    return { pass: errs.length === 0 && rows > 0, detail: { errors: app.errors.slice(0, 5), lineupRows: rows } };
  } finally { await app.context.close(); }
});


/* -------------------------------- v10 suite --------------------------------- */
const V10 = (hash = '#/overview') => `/?ui=v10${hash}`;
async function overviewReady(page) {
  await page.waitForSelector('#fieV10 .v10-overview', { timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector('#fieV10 .v10-lrow.v10-loading') && document.querySelectorAll('#fieV10 .v10-lrow').length > 0, null, { timeout: 120000 });
  await page.waitForTimeout(800);
}
async function leagueReady(page, id, tab) {
  await page.evaluate(h => { location.hash = h; }, `#/league/${id}/${tab}`);
  await page.waitForFunction(([id]) => !!document.querySelector(`#fieV10 .v10-league[data-v10-league="${id}"] .v10-lhdr`), [id], { timeout: 60000 });
  await page.waitForTimeout(500);
}
const text = (page, sel) => page.locator(sel).first().innerText().catch(() => '');

check('V-OVERVIEW', 'v10', 'A-15/A-16/§4.1: Overview lists every league, queues urgent tasks across leagues, no in-season draft task, no Best Ball lineup task (waiver tasks allowed)', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10() });
  try {
    await overviewReady(app.page);
    const info = await app.page.evaluate(() => {
      const q = [...document.querySelectorAll('#fieV10 .v10-q > summary')].map(s => s.innerText.replace(/\s+/g, ' '));
      const idp = document.querySelector('#fieV10 details[data-k="t:1331042152091766784"]');
      const idpTask = idp ? { summary: idp.querySelector('summary').innerText.replace(/\s+/g, ' '), items: idp.querySelector('.v10-xbody').textContent.replace(/\s+/g, ' ') } : null;
      const rows = [...document.querySelectorAll('#fieV10 .v10-lrow')].map(r => ({ k: r.dataset.k || '', tasks: r.querySelector('.v10-l-tasks')?.innerText.trim() || '', name: r.querySelector('.v10-l-name')?.innerText.trim() || '',
        task: (document.querySelector(`#fieV10 details[data-k="t:${(r.dataset.k || '').slice(2)}"] > summary`)?.innerText || '').replace(/\s+/g, ' ') }));
      return { head: document.querySelector('#fieV10 .v10-ov-head')?.innerText || '', q, idpTask, rows, bodyV10: document.body.classList.contains('fie-v10'), classicHidden: getComputedStyle(document.querySelector('.shell')).display === 'none' };
    });
    await app.page.screenshot({ path: path.join(OUT, 'V-OVERVIEW.png'), fullPage: true });
    const urgentIdp = !!info.idpTask && /Urgent/.test(info.idpTask.summary) && /can't play/.test(info.idpTask.summary) && /Hockenson/.test(info.idpTask.items) && /Goff/.test(info.idpTask.items);
    const draft = info.q.filter(t => /Draft (in progress|not held)/.test(t));
    const bb = info.rows.filter(r => /Best Ball|Dynasty BB/.test(r.name) && !/Chopped/.test(r.name));
    // R2: Best Ball leagues may carry waiver tasks, never lineup tasks.
    const bbTasks = bb.filter(r => /can't play|better lineup|empty starter|close call/.test(r.task));
    const pass = info.bodyV10 && info.classicHidden && /Week 6/.test(info.head) && info.rows.length === 23 && urgentIdp && draft.length === 0 && bbTasks.length === 0 && app.errors.length === 0;
    return { pass, detail: { head: info.head, leagues: info.rows.length, queueRows: info.q.length, queue: info.q.slice(0, 30), idpTask: info.idpTask, draft, bestBallWithTasks: bbTasks, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-CONSISTENCY', 'v10', 'A-03: the Overview row, League Home, Lineup and Matchup show the same numbers; best lineup equals classic optimum', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10() });
  try {
    await overviewReady(app.page);
    const ov = await text(app.page, `#fieV10 .v10-lrow[data-k="l:${L.redraft}"] .v10-l-match`);
    await leagueReady(app.page, L.redraft, 'lineup');
    const lineupTotal = await text(app.page, '#fieV10 .v10-total b');
    const recBox = await text(app.page, '#fieV10 .v10-rec-h');
    await app.page.screenshot({ path: path.join(OUT, 'V-LINEUP.png'), fullPage: true });
    await leagueReady(app.page, L.redraft, 'matchup');
    const bigs = await app.page.$$eval('#fieV10 .v10-h2h .v10-big', els => els.map(e => e.innerText.trim()));
    await leagueReady(app.page, L.redraft, 'home');
    const homeLine = await text(app.page, '#fieV10 .v10-grid2 p');
    const nums = s => (String(s).match(/\d+\.\d/g) || []);
    const [ovMe, ovOpp] = nums(ov), best = (recBox.match(/→\s*(\d+\.\d)/) || [])[1];
    const pass = !!ovMe && ovMe === lineupTotal.trim() && ovMe === bigs[0] && ovOpp === bigs[2] && nums(homeLine)[0] === ovMe && nums(homeLine)[1] === ovOpp && best === '84.3';
    return { pass, detail: { overview: ov, lineupTotal, matchup: bigs, home: homeLine, recBox, classicOptimum: '84.3' } };
  } finally { await app.context.close(); }
});

check('V-LINEUP', 'v10', '§4.2: pregame suggestion with tier, Questionable caveat, Doubtful-as-out, Sleeper link; expand shows source and the calibrated P10–P90 range (WP-V1 on)', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10(`#/league/${L.redraft}/lineup`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-lhdr', { timeout: 60000 });
    const rec = await text(app.page, '#fieV10 .v10-rec');
    const first = app.page.locator('#fieV10 .v10-prow > summary').first();
    await first.click();
    const body = await text(app.page, '#fieV10 .v10-prow[open] .v10-xbody');
    const adv = await app.page.locator('#fieV10 .v10-prow[open] .v10-adv').count();
    const advOpenBefore = await app.page.locator('#fieV10 .v10-prow[open] .v10-adv[open]').count();
    const link = await app.page.locator('#fieV10 a[href*="sleeper.com/leagues/"]').count();
    const pass = /Lamar Jackson/.test(rec) && /Questionable/.test(rec) && /(Urgent|Recommended)/.test(rec) && /P10–P90/.test(body) && /calibrated, n=/.test(body) && !/Typical range/.test(body) && /Source/.test(body) && adv === 1 && advOpenBefore === 0 && link > 0;
    return { pass, detail: { rec: rec.slice(0, 400), expand: body.slice(0, 300), advancedInsideExpand: adv, advancedOpenByDefault: advOpenBefore } };
  } finally { await app.context.close(); }
});

check('V-AFTER-TNF', 'v10', '§5.3: after Thursday night, locked players are marked and never part of a suggested change', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-after-tnf', { path: V10(`#/league/${L.redraft}/lineup`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-lhdr', { timeout: 60000 });
    const rows = await app.page.$$eval('#fieV10 .v10-prow > summary', els => els.map(e => ({ t: e.innerText.replace(/\s+/g, ' '), cls: e.parentElement.className })));
    const locked = rows.filter(r => /🔒|Final/.test(r.t));
    const lockedChanged = locked.filter(r => /v10-in|v10-out/.test(r.cls));
    return { pass: lockedChanged.length === 0 && app.errors.length === 0, detail: { lockedRows: locked.map(r => r.t.slice(0, 80)), lockedChanged } };
  } finally { await app.context.close(); }
});

check('V-CHOPPED', 'v10', '§4.3: Chopped field shows only active teams, eliminations verified, cut margin, no head-to-head win estimate', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10(`#/league/${L.chopped}/matchup`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-lhdr', { timeout: 60000 });
    const head = await text(app.page, '#fieV10 .v10-card h2');
    const fieldRows = await app.page.$$eval('#fieV10 .v10-card:first-of-type table tbody tr', r => r.length).catch(() => 0);
    const h2h = await app.page.locator('#fieV10 .v10-h2h').count();
    await app.page.screenshot({ path: path.join(OUT, 'V-CHOPPED.png'), fullPage: true });
    return { pass: /13 active · 5 chopped/.test(head) && fieldRows === 13 && h2h === 0, detail: { head, fieldRows, h2h } };
  } finally { await app.context.close(); }
});

check('V-SWITCH', 'v10', 'A-06: fast league switching A → B → A shows the visible league only; ?ui=classic restores the classic UI', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10(`#/league/${L.redraft}/home`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-lhdr', { timeout: 60000 });
    for (const id of [L.dynastySF, L.redraft, L.chopped, L.redraft]) await app.page.evaluate(h => { location.hash = h; }, `#/league/${id}/home`);
    await app.page.waitForTimeout(6000);
    const shown = await app.page.$eval('#fieV10 .v10-league', el => el.dataset.v10League).catch(() => null);
    const sel = await app.page.$eval('#v10LeagueSelect', el => el.value);
    await app.page.goto(origin + '/?ui=classic', { waitUntil: 'load' });
    await app.page.waitForTimeout(1500);
    const classic = await app.page.evaluate(() => !document.body.classList.contains('fie-v10') && !document.getElementById('fieV10'));
    return { pass: shown === L.redraft && sel === L.redraft && classic && app.errors.length === 0, detail: { shown, sel, classicRestored: classic, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-BRIDGE', 'v10', '§2: routes not rebuilt in R1 open the classic view for the same league and tab; the pill returns to v10', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10(`#/classic/${L.redraft}/waivers`) });
  try {
    await app.page.waitForFunction(id => window.state?.league?.league_id === id && window.state?.activeTab === 'waivers', L.redraft, { timeout: 90000 });
    const visible = await app.page.evaluate(() => getComputedStyle(document.querySelector('.shell')).display !== 'none' && !!document.querySelector('#fieV10Back:not([hidden])'));
    await app.page.locator('#fieV10Back').click();
    await overviewReady(app.page);
    const back = await app.page.evaluate(() => document.body.classList.contains('fie-v10'));
    return { pass: visible && back, detail: { classicVisible: visible, backToV10: back, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

/* ------------------------------ v10 R2 checks ------------------------------- */
check('V-WAIVERS', 'v10', 'A-24/A-25/§5.12: Waivers rank free agents by lineup gain with a legal drop; no CLAIM or bid in Basic; market + budgets present', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/waivers`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-wrow', { timeout: 90000 });
    const info = await app.page.evaluate(() => {
      const rows = [...document.querySelectorAll('#fieV10 .v10-wrow > summary')].map(s => s.innerText.replace(/\s+/g, ' '));
      const cards = [...document.querySelectorAll('#fieV10 .v10-card')].map(c => (c.querySelector('summary,h2')?.innerText || '').replace(/\s+/g, ' '));
      return { rows, cards, perPos: [...document.querySelectorAll('#fieV10 .v10-wrow .v10-w-name .v10-muted')].map(x => x.innerText.split(' · ')[0]) };
    });
    await app.page.locator('#fieV10 .v10-wrow > summary').first().click();
    const expand = await text(app.page, '#fieV10 .v10-wrow[open] .v10-xbody');
    await app.page.screenshot({ path: path.join(OUT, 'V-WAIVERS.png'), fullPage: true });
    const counts = info.perPos.reduce((m, p) => (m[p] = (m[p] || 0) + 1, m), {});
    const noClaim = info.rows.every(r => !/\bCLAIM\b|\$\d/.test(r));
    const pass = info.rows.length > 0 && noClaim && Object.values(counts).every(n => n <= 3) && /Replaces/.test(expand) && /budget/i.test(expand)
      && info.cards.some(c => /Last waiver run/.test(c)) && info.cards.some(c => /FAAB budgets/.test(c)) && app.errors.length === 0;
    return { pass, detail: { rows: info.rows.slice(0, 6), perPosition: counts, cards: info.cards, expand: expand.slice(0, 400), errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-SPECIAL', 'v10', 'WP3.5: Lineup shows a Kicker and a D/ST board (yours + best free agents, next weeks); gains equal the Waivers engine', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.dynastySF}/lineup`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-specboard', { timeout: 90000 });
    const cards = await app.page.$$eval('#fieV10 .v10-specboard > summary', xs => xs.map(x => x.innerText.replace(/\s+/g, ' ')));
    for (const s of await app.page.locator('#fieV10 .v10-specboard:not([open]) > summary').all()) await s.click();
    const tables = await app.page.$$eval('#fieV10 .v10-specboard table', ts => ts.map(t => ({ head: [...t.querySelectorAll('th')].map(x => x.innerText.trim()),
      rows: [...t.querySelectorAll('tbody tr')].map(tr => [...tr.children].map(td => td.innerText.replace(/\s+/g, ' ').trim())) })));
    // Same engine, same numbers: recompute the waiver rows in-page (read-only call of the app's own data layer).
    const engine = await app.page.evaluate(async id => { const e = (await window.FIEV10Data.leagues()).find(x => String(x.id) === id); const r = (await window.FIEV10Data.waivers(e, {})).result;
      return r.rows.filter(x => ['K', 'DEF'].includes(x.position) && !x.pruned).map(x => ({ name: x.name, pos: x.position, gh: x.gainHorizon })); }, L.dynastySF);
    await app.page.screenshot({ path: path.join(OUT, 'V-SPECIAL.png'), fullPage: true });
    const fa = tables.flatMap(t => t.rows.filter(r => /free agent/.test(r[0])).map(r => ({ name: r[0].replace(/\s*free agent.*$/, '').replace(/\s+(Q|O|D|IR|BYE)(·prev)?$/, '').trim(), gh: r[r.length - 2] })));
    const num = s => Number(String(s).replace('+', '').replace('−', '-').replace(',', '.'));
    const consistent = fa.length > 0 && fa.every(f => { const e = engine.find(x => f.name.startsWith(x.name)); return e && Math.abs(Math.max(0, e.gh) - Math.max(0, num(f.gh))) < 0.051; });
    const pass = cards.length === 2 && cards.some(c => /^Kicker/.test(c)) && cards.some(c => /^D\/ST/.test(c)) && tables.every(t => t.rows.some(r => /yours/.test(r[0])))
      && tables.every(t => t.head.filter(h => /^W\d+$/.test(h)).length >= 1) && consistent && !cards.some(c => /\b(PAY|WAIT|STREAM)\b/.test(c)) && app.errors.length === 0;
    return { pass, detail: { cards, tables: tables.map(t => ({ head: t.head, rows: t.rows.slice(0, 4) })), fa: fa.slice(0, 6), engine: engine.slice(0, 6), errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-PLAYERS', 'v10', 'WP3.2: Players tab — visible filters work (position, owner, horizon, search), defaults reset on league change, rows expand', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/players`) });
  try {
    const p = app.page; await p.waitForSelector('#fieV10 .v10-plrow', { timeout: 90000 });
    const rows = () => p.$$eval('#fieV10 .v10-plrow > summary', xs => xs.map(x => x.innerText.replace(/\s+/g, ' ')));
    const all = await rows();
    await p.selectOption('#fieV10 select[data-v10-pf="pos"]', 'RB'); const rb = await rows();
    await p.selectOption('#fieV10 select[data-v10-pf="own"]', 'FA'); const rbFa = await rows();
    await p.fill('#fieV10 input[data-v10-pf="q"]', 'zzzz-nobody'); const none = await p.locator('#fieV10 .v10-plrow').count();
    await p.fill('#fieV10 input[data-v10-pf="q"]', '');
    await p.locator('#fieV10 .v10-plrow > summary').first().click(); const expand = await text(p, '#fieV10 .v10-plrow[open] .v10-xbody');
    await p.screenshot({ path: path.join(OUT, 'V-PLAYERS.png'), fullPage: false });
    await p.evaluate(id => { location.hash = `#/league/${id}/players`; }, L.dynastySF); await p.waitForFunction(id => document.querySelector(`#fieV10 [data-v10-league="${id}"] .v10-plrow`), L.dynastySF, { timeout: 90000 });
    const reset = await p.$eval('#fieV10 select[data-v10-pf="pos"]', e => e.value) === 'ALL' && await p.$eval('#fieV10 select[data-v10-pf="own"]', e => e.value) === 'ALL';
    const pass = all.length === 50 && rb.length > 0 && rb.every(r => /\bRB · /.test(r)) && rbFa.length > 0 && rbFa.every(r => /free agent/.test(r) && /\bRB · /.test(r)) && none === 0
      && /Source|Projection|range/i.test(expand) && reset && app.errors.length === 0;
    return { pass, detail: { first: all.slice(0, 3), rb: rb.slice(0, 2), rbFa: rbFa.slice(0, 2), none, expand: expand.slice(0, 200), reset, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-TEAM', 'v10', 'WP3.3: Team tab — position strength with ranks, depth/thin, byes, roster with real Sleeper slots', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/team`) });
  try {
    const p = app.page; await p.waitForSelector('#fieV10 .v10-card h2', { timeout: 90000 }); await p.waitForFunction(() => /Roster/.test(document.querySelector('#fieV10Main')?.innerText || ''), null, { timeout: 90000 });
    const h2 = await p.$$eval('#fieV10 .v10-card h2', xs => xs.map(x => x.innerText.split('\n')[0]));
    const tables = await p.$$eval('#fieV10 .v10-card table', ts => ts.map(t => [...t.querySelectorAll('tbody tr')].map(tr => [...tr.children].map(td => td.innerText.trim()))));
    const strength = tables[0] || [], roster = tables[tables.length - 1] || [];
    const slots = roster.map(r => r[0]);
    await p.screenshot({ path: path.join(OUT, 'V-TEAM.png'), fullPage: true });
    const pass = ['Team strength', 'Depth', 'Byes', 'Roster'].every(x => h2.some(h => h.startsWith(x))) && strength.length >= 4 && strength.every(r => /^\d+\/\d+$/.test(r[2]))
      && slots.includes('QB') && slots.includes('BN') && slots.some(s => s === 'FLEX') && app.errors.length === 0;
    return { pass, detail: { h2, strength, rosterSlots: slots, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-TRADES', 'v10', 'WP3.4: Trades tab — tick players on both sides, effect on both lineups per week and at season rates; Draft link only with an open Sleeper draft (R4.3)', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/trades`) });
  try {
    const p = app.page; await p.waitForSelector('#fieV10 input[data-v10-tr="send"]', { timeout: 90000 });
    const before = await text(p, '#fieV10 #v10TrResult');
    await p.locator('#fieV10 input[data-v10-tr="send"]').first().check(); await p.locator('#fieV10 input[data-v10-tr="receive"]').first().check();
    await p.waitForFunction(() => /Season rate/.test(document.querySelector('#fieV10 #v10TrResult')?.innerText || ''), null, { timeout: 30000 });
    const res = await p.$$eval('#fieV10 #v10TrResult table.v10-table tbody tr', trs => trs.map(t => [...t.children].map(c => c.innerText.replace(/\s+/g, ' ').trim())));
    const verdict = await text(p, '#fieV10 #v10TrResult > p');
    await p.screenshot({ path: path.join(OUT, 'V-TRADES.png'), fullPage: true });
    const navRedraft = await p.$$eval('#fieV10 nav.v10-tabs a', xs => xs.map(x => x.innerText.trim()));
    await p.evaluate(id => { location.hash = `#/league/${id}/home`; }, L.dynastySF); await p.waitForFunction(id => document.querySelector(`#fieV10 [data-v10-league="${id}"] .v10-lhdr`), L.dynastySF, { timeout: 90000 });
    const navDynasty = await p.$$eval('#fieV10 nav.v10-tabs a', xs => xs.map(x => x.innerText.trim()));
    const pass = /Tick players/.test(before) && res.length >= 3 && res.some(r => /^W\d+$/.test(r[0]) && /→/.test(r[1]) && /→/.test(r[2])) && res.some(r => /Season rate/.test(r[0]))
      && /helps|costs|neutral/.test(verdict) && navRedraft.includes('Trades') && !navRedraft.some(x => /^Draft/.test(x)) && !navDynasty.some(x => /^Draft/.test(x)) && app.errors.length === 0; // R4.3: Draft link only with an open Sleeper draft — the capture has none (drafts = [])
    return { pass, detail: { res, verdict: verdict.slice(0, 300), navRedraft, navDynasty, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-LAB', 'v10', 'WP3.1: Research Lab — model state for every league, projection accuracy on a scored week, forecasts, rankings with the research board, documents; display only', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10('#/lab/state') });
  try {
    const p = app.page, go = async (h, re) => { await p.evaluate(x => { location.hash = x; }, h); await p.waitForFunction(r => new RegExp(r).test(document.querySelector('#fieV10Main')?.innerText || '') && !document.querySelector('#fieV10Main .v10-loading'), re, { timeout: 120000 }); return p.locator('#fieV10Main').innerText(); };
    await p.waitForFunction(() => /Research pipeline/.test(document.querySelector('#fieV10Main')?.innerText || '') && !document.querySelector('#fieV10Main .v10-loading'), null, { timeout: 180000 });
    const state = await p.locator('#fieV10Main').innerText(), leaguesRows = await p.locator('#fieV10Main table').first().locator('tbody tr').count();
    const navLab = await p.locator('#fieV10 .v10-bar [data-nav="lab"].active').count();
    const ev = await go(`#/lab/eval?league=${L.redraft}&week=5`, 'Mean abs\\. error');
    const evRows = await p.$$eval('#fieV10Main table.v10-table tbody tr', trs => trs.map(t => [...t.children].map(c => c.innerText.trim())));
    await p.screenshot({ path: path.join(OUT, 'V-LAB-eval.png'), fullPage: true });
    const fc = await go(`#/lab/forecasts?league=${L.redraft}`, 'Forecasts, Week');
    const games = await p.locator('#fieV10Main .v10-labgame').count();
    const rk = await go(`#/lab/rankings?league=${L.redraft}&pos=WR`, 'Season p50');
    const rkRows = await p.$$eval('#fieV10Main table.v10-table tbody tr', trs => trs.map(t => [...t.children].map(c => c.innerText.trim())));
    const dc = await go(`#/lab/docs?league=${L.redraft}`, 'Documents');
    const pass = /Sleeper-only mode|governed FIE projection/.test(state) && leaguesRows >= 20 && /Production model/.test(state) && navLab === 1
      && evRows.some(r => r[0] === 'All' && Number(r[1]) > 20 && Number(String(r[2]).replace(',', '.')) > 0) && games > 3 && /Last 4/.test(fc)
      && rkRows.length >= 20 && rkRows.filter(r => /\d/.test(r[4])).length >= 10 && /research/.test(rk) && (dc.match(/JSON ↗/g) || []).length >= 3 && app.errors.length === 0;
    return { pass, detail: { leaguesRows, navLab, eval: evRows.slice(-3), games, rankings: rkRows.slice(0, 3), docs: dc.slice(0, 300), errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-REVIEW', 'v10', 'A-23/§5.13: a past week shows submitted vs projection-best vs hindsight-best on actual points', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/lineup?week=5`) });
  try {
    await app.page.waitForSelector('#fieV10 .v10-review', { timeout: 90000 });
    const rows = await app.page.$$eval('#fieV10 .v10-review tbody tr', trs => trs.map(t => [...t.children].map(c => c.innerText.trim())));
    const sel = await app.page.$eval('#fieV10 select[data-v10-week]', e => e.value);
    const num = s => Number(String(s).replace(',', '.'));
    const [sub, projBest, hind] = rows.map(r => num(r[1]));
    await app.page.screenshot({ path: path.join(OUT, 'V-REVIEW.png'), fullPage: true });
    const pass = rows.length === 3 && hind >= sub && hind >= projBest && sel === '5' && app.errors.length === 0;
    return { pass, detail: { rows, weekSelected: sel, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-WEEKPICK', 'v10', 'R2: the week picker moves between live, past (review) and future weeks without stale content', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w7-tuesday', { path: V10(`#/league/${L.redraft}/lineup`) });
  try {
    await app.page.waitForSelector('#fieV10 select[data-v10-week]', { timeout: 90000 });
    const states = [];
    for (const wk of ['5', '8', '7']) {
      await app.page.selectOption('#fieV10 select[data-v10-week]', wk);
      await app.page.waitForFunction(w => document.querySelector('#fieV10 .v10-league')?.dataset.v10Week === w, wk, { timeout: 60000 });
      await app.page.waitForTimeout(600);
      states.push({ wk, review: await app.page.locator('#fieV10 .v10-review').count(), future: /in the future/.test(await text(app.page, '#fieV10 .v10-league')), hash: await app.page.evaluate(() => location.hash) });
    }
    const pass = states[0].review === 1 && states[1].future && states[1].review === 0 && states[2].review === 0 && !/week=/.test(states[2].hash) && app.errors.length === 0;
    return { pass, detail: { states, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-READER', 'v10', 'A-22/WP2.2: one player reader from any name; pin up to 3; compare shows the pinned players with lineup impact', async ({ browser, origin }) => {
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10(`#/league/${L.redraft}/lineup`) });
  try {
    await app.page.waitForSelector('#fieV10 a.v10-plink', { timeout: 90000 });
    await app.page.locator('#fieV10 a.v10-plink').nth(0).click();
    await app.page.waitForSelector('#fieV10Reader:not([hidden]) [data-v10-pin]', { timeout: 30000 });
    const first = await text(app.page, '#fieV10Reader');
    await app.page.locator('#fieV10Reader [data-v10-pin]').click();
    await app.page.locator('#fieV10Reader [data-v10-close]').first().click();
    await app.page.locator('#fieV10 a.v10-plink').nth(12).click();
    await app.page.waitForSelector('#fieV10Reader:not([hidden]) [data-v10-pin]', { timeout: 30000 });
    await app.page.locator('#fieV10Reader [data-v10-pin]').click();
    await app.page.locator('#fieV10Tray [data-v10-compare]').click();
    await app.page.waitForSelector('#fieV10Reader .v10-cmp', { timeout: 30000 });
    const cols = await app.page.$$eval('#fieV10Reader .v10-cmp thead th', t => t.length - 1);
    const impact = await app.page.$$eval('#fieV10Reader .v10-cmp tbody tr', trs => trs.map(t => t.innerText).find(x => /Your lineup/.test(x)) || '');
    await app.page.screenshot({ path: path.join(OUT, 'V-READER.png'), fullPage: false });
    const pass = /In ReDraft/.test(first) && /Details/.test(first) && cols === 2 && /best lineup|If you add|acquired/.test(impact) && app.errors.length === 0;
    return { pass, detail: { first: first.slice(0, 300), cols, impact: impact.slice(0, 300), errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

check('V-FEED', 'v10', 'A-26/WP2.5: second visit shows status changes since the first; My players counts are listed', async ({ browser, origin }) => {
  // Visit 1 on the Thursday Week 6 capture, visit 2 (same browser profile) on the Sunday Week 7 capture.
  const app = await openApp(browser, origin, 'w6-pregame', { path: V10() });
  try {
    await overviewReady(app.page);
    const firstFeed = await text(app.page, '#fieV10 #v10Feed');
    await app.context.unroute('**/*');
    const r2 = new ProviderRouter(SCENARIOS['w7-tuesday']); await r2.install(app.context, origin);
    const page2 = await app.context.newPage(); page2.on('pageerror', e => app.errors.push(`pageerror: ${String(e.message || e).slice(0, 300)}`));
    await page2.clock.install({ time: new Date(SCENARIOS['w7-tuesday'].clock) });
    await page2.goto(origin + V10(), { waitUntil: 'load' });
    await overviewReady(page2);
    const feed = await text(page2, '#fieV10 #v10Feed'), mp = await text(page2, '#fieV10 .v10-mphead');
    const mpHead = await page2.$$eval('#fieV10 .v10-card h2', hs => hs.map(h => h.innerText).find(t => /My players/.test(t)) || '');
    await page2.screenshot({ path: path.join(OUT, 'V-FEED.png'), fullPage: true });
    const items = (feed.match(/→/g) || []).length;
    const pass = /First visit/.test(firstFeed) && items > 0 && /\d+ players · \d+ starting slots/.test(mpHead) && /Starts/.test(mp) && app.errors.length === 0;
    return { pass, detail: { firstFeed: firstFeed.slice(0, 160), feed: feed.slice(0, 600), statusChanges: items, myPlayers: mpHead, errors: app.errors.slice(0, 5) } };
  } finally { await app.context.close(); }
});

/* ---------------------------------- main ----------------------------------- */
(async () => {
  if (!fs.existsSync(path.join(DIST, 'index.html'))) { console.error(`dist not found: ${DIST}`); process.exit(2); }
  const { server, origin } = await serveDist(DIST);
  const browser = await chromium.launch({ headless: true });
  const selected = CHECKS.filter(c => (SUITE === 'all' || c.suite === SUITE) && (!ONLY.length || ONLY.includes(c.id)));
  const results = [];
  try {
    for (const c of selected) {
      const t0 = Date.now();
      let r;
      try { r = await c.fn({ browser, origin }); } catch (e) { r = { pass: false, detail: { exception: String(e && e.stack || e).slice(0, 800) } }; }
      results.push({ id: c.id, suite: c.suite, title: c.title, pass: !!r.pass, seconds: Math.round((Date.now() - t0) / 100) / 10, detail: r.detail });
      console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${c.id}  ${c.title}`);
      if (!r.pass) console.log('      ' + JSON.stringify(r.detail).slice(0, 600));
    }
  } finally { await browser.close(); server.close(); }
  const report = { generated_at: new Date().toISOString(), dist: path.relative(process.cwd(), DIST) || '.', suite: SUITE, passed: results.filter(r => r.pass).length, total: results.length, results };
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log(`${report.passed}/${report.total} checks passed · report: ${path.join(OUT, 'report.json')}`);
  process.exit(report.passed === report.total ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
