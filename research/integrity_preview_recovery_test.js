const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const read = path => fs.readFileSync(path, 'utf8');

async function portfolioCardUsesControllerContext() {
  const source = read('app/portfolio-home.js');
  const body = source.slice(source.indexOf('async function openLeague('), source.indexOf('\nfunction bind(){'));
  let captured = 0;
  const elements = Object.fromEntries(['leagueInput', 'savedLeagueSelect', 'savedLeagueFormat', 'status'].map(id => [id, {value: '', textContent: ''}]));
  const state = {activeTab: '', league: null};
  const controller = {
    async switchLeague(id, options) {
      assert.equal(this, controller, 'the league loader must retain its controller context');
      assert.equal(options.route, 'weekly');
      state.league = {league_id: id};
      return state.league;
    }
  };
  const context = {state, window: {FIELeagueController: controller}, document: {getElementById: id => elements[id]},
    savedLeagues: () => [{id: '123456789', name: 'Fixture', formatOverride: 'REDRAFT'}],
    leavePortfolio() {}, captureCurrentLeague() {captured++;}, BASE_RENDER() {}, BASE_LOAD: null, console: {error() {}}};
  vm.createContext(context);
  vm.runInContext(body + '\nthis.openLeague=openLeague;', context);
  await context.openLeague('123456789', 'weekly');
  assert.equal(captured, 1);
  assert.equal(state.league.league_id, '123456789');
  controller.switchLeague = async () => null;
  await context.openLeague('123456789', 'weekly');
  assert.equal(captured, 1, 'failed loads must not cache a stale league');
  assert.match(elements.status.textContent, /did not complete/);
}

function choppedSimulationCompletes() {
  const source = read('app/decision-engines.js');
  const body = source.slice(source.indexOf('function choppedBudgetMap()'), source.indexOf('\nasync function runLeagueSimulation('));
  const rosters = [1, 2, 3].map(roster_id => ({roster_id, settings: {waiver_budget_used: 100}}));
  let modelsBuilt = 0;
  const context = {
    state: {rosters, league: {league_id: '123456789', settings: {waiver_budget: 100}}, leagueRules: {chopped: {eliminatedPerPeriod: 1}}},
    window: {}, rosterPoolFor: id => [{id, power: id}], playerDistribution: p => ({mu: p.power}),
    teamModelFromPool: pool => {modelsBuilt++; return {mu: pool.reduce((n, p) => n + p.power, 0)};},
    playerId: p => String(p.id),
    sampleTeam: model => model.mu, rngFor: () => () => 0.5, finite: x => Number.isFinite(x) ? x : null,
    clampV: (x, min, max) => Math.max(min, Math.min(max, x))
  };
  vm.createContext(context);
  vm.runInContext(body + '\nthis.simulateChopped=simulateChopped;', context);
  const result = context.simulateChopped(4);
  assert.equal(result.rows.length, 3);
  assert.equal(result.rows.reduce((sum, row) => sum + row.winner, 0), 1);
  assert.equal(result.rows.reduce((sum, row) => sum + row.survival[0], 0), 2);
  assert.equal(modelsBuilt, 3, 'repeated Chopped paths must reuse identical roster models');
}

async function choppedBestBallWorkIsBoundedAndCancellable() {
  const source = read('app/decision-engines.js');
  const body = source.slice(source.indexOf('function choppedBudgetMap()'), source.indexOf('\nasync function runLeagueSimulation('));
  const rosters = Array.from({length: 18}, (_, i) => ({roster_id: i + 1, settings: {waiver_budget_used: 0}}));
  const pools = Object.fromEntries(rosters.map(({roster_id}) => [roster_id, Array.from({length: 6}, (_, j) => ({
    id: `${roster_id}-${j}`, position: ['QB', 'RB', 'WR', 'TE', 'RB', 'WR'][j], power: 8 + roster_id * .2 + j,
    weeklyProjection: 8 + roster_id * .2 + j
  }))]));
  let modelsBuilt = 0;
  const context = {
    state: {rosters, league: {league_id: 'hybrid-fixture', settings: {waiver_budget: 100}}, leagueRules: {chopped: {eliminatedPerPeriod: 1}}},
    window: {
      formatProfile: () => ({chopped: true, bestBall: true}),
      optimizePoolByValue: (pool, valueFn) => ({starterTotal: [...pool].map(valueFn).sort((a, b) => b - a).slice(0, 4).reduce((a, b) => a + b, 0)})
    },
    rosterPoolFor: id => pools[id], playerDistribution: p => ({mu: p.power, sd: 1, empirical: [p.power - .5, p.power, p.power + .5]}),
    teamModelFromPool: pool => {modelsBuilt++; const mu = [...pool].sort((a, b) => b.power - a.power).slice(0, 4).reduce((n, p) => n + p.power, 0); return {mu, sd: 2, empirical: [mu - 1, mu, mu + 1]};},
    allTeamModels: initial => Object.fromEntries(rosters.map(({roster_id}) => [roster_id, context.teamModelFromPool(initial[roster_id])])),
    playerId: p => String(p.id),
    sampleTeam: (model, rng) => model.mu + (model.shift || 0) + rng() - .5,
    rngFor: seed => {let n = [...String(seed)].reduce((a, c) => (a * 33 + c.charCodeAt(0)) >>> 0, 5381); return () => ((n = (1664525 * n + 1013904223) >>> 0) / 4294967296);},
    finite: x => Number.isFinite(Number(x)) ? Number(x) : null,
    clampV: (x, min, max) => Math.max(min, Math.min(max, x)),
    setTimeout
  };
  vm.createContext(context);
  vm.runInContext(body + '\nthis.simulateChoppedProgressive=simulateChoppedProgressive;', context);

  const progress = [];
  const first = await context.simulateChoppedProgressive(450, null, {batchSize: 25, onProgress: done => progress.push(done)});
  assert.equal(first.compute.method, 'bounded_chopped_bestball_v1');
  assert.equal(first.rows.length, 18);
  assert.ok(Math.abs(first.rows.reduce((sum, row) => sum + row.winner, 0) - 1) < 1e-12);
  assert.equal(modelsBuilt, 18, 'hybrid paths must build each full Best Ball roster model once');
  assert.ok(first.compute.candidateCount <= 54, 'candidate table must be capped at three released players per roster');
  assert.ok(first.compute.marginalEvaluations <= 18 * 54, 'marginal work must be bounded by teams times candidates');
  assert.equal(progress.length, 18);
  assert.equal(progress.at(-1), 450);
  assert.ok(progress.every((done, i) => done === (i + 1) * 25));

  const second = await context.simulateChoppedProgressive(450, null, {batchSize: 17});
  assert.equal(JSON.stringify(second.rows), JSON.stringify(first.rows), 'batch boundaries must not change deterministic results');

  let cancel = false;
  await assert.rejects(
    context.simulateChoppedProgressive(450, null, {batchSize: 9, onProgress: () => {cancel = true;}, shouldCancel: () => cancel}),
    /cancelled/,
    'cooperative cancellation must stop before publishing a partial result'
  );
}

function researchNamespaceFollowsLoadedLeague() {
  const source = read('index.html');
  const start = source.indexOf('const FIE_RESEARCH_RUNTIME=');
  const end = source.indexOf('\nlet m1ResearchBundle=', start);
  const state = {league: null};
  const context = {state, window: {}};
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  assert.equal(context.window.FIE_RESEARCH_RUNTIME.activeLeagueId(), null);
  state.league = {league_id: '123456789'};
  assert.equal(context.window.FIE_RESEARCH_RUNTIME.path('milestone5.json'), 'data/research/leagues/123456789/milestone5.json');
  context.window.FIE_RESEARCH_RUNTIME.resetAll();
  assert.equal(context.window.FIE_RESEARCH_RUNTIME.token, 1);
}

function researchDeltaRenderingIsDefined() {
  const source = read('index.html');
  const start = source.indexOf('function m5Num(');
  const end = source.indexOf('function m5PositionFor(', start);
  const context = {};
  vm.createContext(context);
  vm.runInContext(source.slice(start, end) + '\nthis.deltaClass=m5DeltaClass;', context);
  assert.equal(context.deltaClass(0.12), 'm1-positive');
  assert.equal(context.deltaClass(-0.12), 'm1-negative');
  assert.equal(context.deltaClass(null), 'm1-muted');
}

(async () => {
  await portfolioCardUsesControllerContext();
  choppedSimulationCompletes();
  await choppedBestBallWorkIsBoundedAndCancellable();
  researchNamespaceFollowsLoadedLeague();
  researchDeltaRenderingIsDefined();
  console.log('PASS preview recovery: card context, bounded Chopped + Best Ball paths, cancellation, research namespace and M5 rendering');
})().catch(error => {console.error(error); process.exitCode = 1;});
