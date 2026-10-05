/* Read-only browser QA. Fixtures and blocked provider access are explicitly recorded. */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http'), assert = require('assert');
const { chromium } = require(process.env.FIE_UI_PLAYWRIGHT || 'playwright');
const baseline = path.resolve(process.argv[2]), candidate = path.resolve(process.argv[3]);
const output = path.resolve(process.env.FIE_UI_QA_OUTPUT || 'editorial-ui-qa');
fs.mkdirSync(output, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.csv': 'text/csv', '.svg': 'image/svg+xml' };
function serve(root) {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      const filename = path.resolve(root, '.' + (pathname.endsWith('/') ? pathname + 'index.html' : pathname));
      if (!filename.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
      fs.readFile(filename, (err, data) => {
        if (err) { res.writeHead(404).end(); return; }
        res.setHeader('Content-Type', types[path.extname(filename)] || 'application/octet-stream'); res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve({ server, url: `http://127.0.0.1:${server.address().port}` }));
  });
}
(async () => {
  const old = await serve(baseline), next = await serve(candidate);
  const browser = await chromium.launch({ headless: true });
  const results = { baselineCommit: '1272eed30faf9548c128677a2e45e99bafed819a', providerMode: 'External requests blocked identically; this is offline shell QA, not live-league validation.', samples: [] };
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 375, height: 812 }]) {
      for (const [name, source] of [['baseline', old], ['candidate', next]]) {
        const context = await browser.newContext({ viewport });
        await context.route('https://**/*', route => route.abort());
        const page = await context.newPage(), errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(source.url, { waitUntil: 'load' });
        await page.locator('#portfolioPanel.active').waitFor();
        await page.screenshot({ path: path.join(output, `${name}-${viewport.width}-first-screen.png`) });
        await page.screenshot({ path: path.join(output, `${name}-${viewport.width}.png`), fullPage: true });
        const measurement = await page.evaluate(() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
          firstContentTop: document.querySelector('#portfolioPanel')?.getBoundingClientRect().top,
          primarySections: document.querySelectorAll('#primaryNav .primary-tab').length
        }));
        results.samples.push({ name, viewport: viewport.width, ...measurement, errors });
        if (name === 'candidate') {
          assert.strictEqual(measurement.primarySections, 9, 'Eight original sections plus Reports must remain reachable');
          assert(measurement.documentWidth <= measurement.viewportWidth + 1, 'Candidate shell overflows viewport');
          assert(await page.locator('#savedLeagueSelect').isVisible(), 'League selector must stay visible');
          assert(await page.locator('#fieDataHealth').isVisible(), 'Scoring-health blockers must stay visible');
          assert.strictEqual(await page.locator('#fieLeagueManagement').getAttribute('open'), null);
          await page.getByRole('button', { name: 'Manage leagues', exact: true }).click();
          assert(await page.locator('#leagueInput').isVisible());
          await page.getByRole('button', { name: 'Manage leagues', exact: true }).click();
          await page.locator('#portfolioAddBtn').click();
          assert(await page.locator('#leagueInput').isVisible(), 'Portfolio setup shortcut must open its disclosure');
          await page.getByRole('button', { name: 'Manage leagues', exact: true }).click();
          await page.locator('#fieDataCoverage > summary').click();
          assert(await page.locator('#releaseMarkerV7').isVisible());
          await page.locator('#fieDataCoverage > summary').click();
          if (viewport.width < 760) await page.locator('#fieMobileNavigation').selectOption('players');
          else await page.locator('#primaryNav [data-section="players"]').click();
          await page.waitForURL('**/#view=all');
          if (viewport.width < 760) await page.locator('#fieMobileNavigation').selectOption('draft');
          else await page.locator('#primaryNav [data-section="draft"]').click();
          await page.waitForURL('**/#view=draft');
          await page.goBack(); await page.waitForURL('**/#view=all');
          await page.locator('#primaryNav [data-section="players"].active').waitFor({ state: 'attached' });
          assert.strictEqual(await page.evaluate(() => state.activeTab), 'all');
          await page.goForward(); await page.waitForURL('**/#view=draft');
          await page.locator('#primaryNav [data-section="draft"].active').waitFor({ state: 'attached' });
          await page.reload(); await page.waitForURL('**/#view=draft');
          await page.locator('#primaryNav [data-section="draft"].active').waitFor({ state: 'attached' });
          assert.strictEqual(await page.evaluate(() => state.activeTab), 'draft', 'Deep link must survive reload');
          await page.goto(`${source.url}/app/ui/editorial-review.html`);
          assert.strictEqual(await page.locator('.fie-expanded:visible').count(), 0);
          await page.getByRole('button', { name: 'Expand Alex Turner' }).click();
          assert.strictEqual(await page.locator('.fie-expanded:visible').count(), 1);
          await page.getByRole('button', { name: 'Expand Sam Jordan' }).click();
          assert.strictEqual(await page.locator('.fie-expanded:visible').count(), 1);
          const advanced = page.getByRole('button', { name: 'Advanced evidence for Alex Turner' });
          await advanced.click(); assert(await page.locator('dialog[open]').isVisible());
          await page.keyboard.press('Escape');
          assert.strictEqual(await page.locator('dialog[open]').count(), 0);
          assert(await advanced.evaluate(button => button === document.activeElement), 'Escape must restore trigger focus');
          assert.strictEqual(await page.locator('#waiverExample .fie-status').count(), 4);
          assert(await page.getByText('Exact-scoring evidence incomplete', { exact: true }).isVisible());
          await page.screenshot({ path: path.join(output, `disclosure-${viewport.width}.png`), fullPage: true });
        }
        await context.close();
      }
    }
    for (const sample of results.samples.filter(x => x.name === 'candidate')) {
      const oldSample = results.samples.find(x => x.name === 'baseline' && x.viewport === sample.viewport);
      assert(sample.firstContentTop < oldSample.firstContentTop, 'Editorial shell must place portfolio content earlier');
      assert.deepStrictEqual(sample.errors.filter(error => !oldSample.errors.includes(error)), [], 'Candidate introduced an uncaught browser error');
    }
    results.result = 'PASS';
    console.log(JSON.stringify(results, null, 2));
  } finally {
    fs.writeFileSync(path.join(output, 'comparison.json'), JSON.stringify(results, null, 2));
    await browser.close(); old.server.close(); next.server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
