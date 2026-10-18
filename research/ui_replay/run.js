#!/usr/bin/env node
/* FIE UI replay runner.
 *
 *   node research/ui_replay/run.js [--dist dist] [--suite classic|all] [--only ID[,ID]] [--out ui-replay-output]
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

async function openApp(browser, origin, scenarioId, { width = 1440, height = 1000 } = {}) {
  const scenario = SCENARIOS[scenarioId];
  const router = new ProviderRouter(scenario);
  const context = await browser.newContext({ viewport: { width, height }, timezoneId: 'Europe/Berlin' });
  await router.install(context, origin);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${String(e.message || e).slice(0, 300)}`));
  page.on('console', m => { if (m.type() === 'error' && !IGNORED_CONSOLE.some(r => r.test(m.text()))) errors.push(`console: ${m.text().slice(0, 300)}`); });
  await page.clock.install({ time: new Date(scenario.clock) });
  await page.goto(origin + '/', { waitUntil: 'load' });
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
