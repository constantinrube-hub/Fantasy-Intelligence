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
  const context = {
    state: {rosters, league: {league_id: '123456789', settings: {waiver_budget: 100}}, leagueRules: {chopped: {eliminatedPerPeriod: 1}}},
    window: {}, rosterPoolFor: id => [{id, power: id}], playerDistribution: p => ({mu: p.power}),
    teamModelFromPool: pool => ({mu: pool.reduce((n, p) => n + p.power, 0)}),
    sampleTeam: model => model.mu, rngFor: () => () => 0.5, finite: x => Number.isFinite(x) ? x : null,
    clampV: (x, min, max) => Math.max(min, Math.min(max, x))
  };
  vm.createContext(context);
  vm.runInContext(body + '\nthis.simulateChopped=simulateChopped;', context);
  const result = context.simulateChopped(4);
  assert.equal(result.rows.length, 3);
  assert.equal(result.rows.reduce((sum, row) => sum + row.winner, 0), 1);
  assert.equal(result.rows.reduce((sum, row) => sum + row.survival[0], 0), 2);
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

(async () => {
  await portfolioCardUsesControllerContext();
  choppedSimulationCompletes();
  researchNamespaceFollowsLoadedLeague();
  console.log('PASS preview recovery: card context, Chopped paths, research namespace');
})().catch(error => {console.error(error); process.exitCode = 1;});
