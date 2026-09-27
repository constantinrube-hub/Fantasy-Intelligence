'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const runtime = fs.readFileSync('app/v9.3.3-runtime-integrity.js', 'utf8');
const shell = fs.readFileSync('index.html', 'utf8');

function currentWeekDefaultsToSleeperLeg() {
  const start = runtime.indexOf('const stateObj=');
  const end = runtime.indexOf('\nfunction currentContext()', start);
  const select = {value: '1'};
  const state = {league: {settings: {leg: 3}}, weekly: {week: 1}};
  const context = {
    window: {state, FIECore: {}}, state,
    document: {getElementById: id => id === 'weekSelect' ? select : null},
    Date, Number, Math
  };
  vm.createContext(context);
  vm.runInContext(runtime.slice(start, end) + '\nthis.authoritativeLeagueWeek=authoritativeLeagueWeek;this.syncAuthoritativeLeagueWeek=syncAuthoritativeLeagueWeek;', context);
  assert.equal(context.authoritativeLeagueWeek(), 3);
  assert.equal(context.syncAuthoritativeLeagueWeek(), 3);
  assert.equal(state.weekly.week, 3);
  assert.equal(select.value, '3');

  state.league.settings.leg = 0;
  select.value = '7';
  state.weekly.week = 7;
  assert.equal(context.authoritativeLeagueWeek(), null, 'invalid/offseason legs must not fabricate a current week');
  assert.equal(context.syncAuthoritativeLeagueWeek(), 7, 'invalid/offseason legs retain the explicit selected week');
}

async function hydrationInvalidatesAStartedSimulation() {
  const start = runtime.indexOf('function refreshStartedLeagueSimulation()');
  const end = runtime.indexOf('\n\n/* ----------------------- B', start);
  let cancelled = null, reruns = 0;
  const engine = {
    leagueSim: {loading: false, data: {current: {myMean: 0, oppMean: 0}}, leagueId: '123', week: 3},
    cancelLeagueSimulation: reason => {cancelled = reason;},
    runLeagueSimulation: () => {reruns++;}
  };
  const state = {activeTab: 'matchupsim'};
  const context = {
    window: {FIEDecisionEngines: engine},
    stateObj: () => state,
    defaultSim: (id, week) => ({loading: false, error: null, data: null, leagueId: id, week}),
    leagueId: () => '123', activeWeek: () => 3,
    diag: error => {throw error;}, setTimeout
  };
  vm.createContext(context);
  vm.runInContext(runtime.slice(start, end) + '\nthis.refreshStartedLeagueSimulation=refreshStartedLeagueSimulation;', context);
  assert.equal(context.refreshStartedLeagueSimulation(), true);
  await new Promise(resolve => setTimeout(resolve, 5));
  assert.match(cancelled, /hydration completed/);
  assert.equal(engine.leagueSim.data, null);
  assert.equal(engine.leagueSim.week, 3);
  assert.equal(reruns, 1, 'a visible, already-started simulation must rerun after final hydration');

  engine.leagueSim = {loading: false, data: null, progress: {status: 'cancelled'}};
  assert.equal(context.refreshStartedLeagueSimulation(), false, 'user cancellation must remain respected');
}

function m6ShowsTheActualClientBlocker() {
  const start = shell.indexOf('function m6RuntimeReason(');
  const end = shell.indexOf('\nasync function loadM6(', start);
  const mandatory = ['global_operator_auto','operator_auto','league_id_match','profile_fingerprint_match','current_profile_live_match','format_match','artifact_scope_match','current_storage_integrity','m4_complete','m5_complete','m6_complete','current_complete','current_producer','current_contract','scoring_signature_match','fresh_snapshot','target_week_leakage_guard','eligible_players'];
  const checks = Object.fromEntries(mandatory.map(key => [key, true]));
  const state = {league: {league_id: '123'}};
  const governance = {active_build: 'V8.8-M6', runtime_enabled: true, runtime_allow_m5: true, operator_mode: 'AUTO', schema_version: 2, league_id: '123', league_format: 'REDRAFT', checks, current_snapshot: {season: 2026, week: 3, max_age_hours: 18}};
  const context = {
    window: {FIE89_HASH_VERIFIED: false, FIE89_HASH_STATUS: {reason: 'artifact hash mismatch: milestone4'}, activeFormatKey: () => 'REDRAFT'},
    state, m6Gov: governance, m6Bundle: {league_id: '123', profile_fingerprint: 'fp'},
    activeSeason: () => 2026, currentWeek: () => 3, m6Fresh: () => false
  };
  governance.profile_fingerprint = 'fp';
  vm.createContext(context);
  vm.runInContext(shell.slice(start, end) + '\nthis.m6RuntimeReason=m6RuntimeReason;', context);
  assert.equal(context.m6RuntimeReason(governance), 'artifact hash mismatch: milestone4');
  context.window.FIE89_HASH_VERIFIED = true;
  assert.match(context.m6RuntimeReason(governance), /18h freshness limit/);
  context.m6Fresh = () => true;
  assert.equal(context.m6RuntimeReason(governance), 'all client/runtime promotion checks passed');
}

(async () => {
  currentWeekDefaultsToSleeperLeg();
  await hydrationInvalidatesAStartedSimulation();
  m6ShowsTheActualClientBlocker();
  for (const name of ['dst-intelligence.js', 'kicker-intelligence.js']) {
    const text = fs.readFileSync(`app/${name}`, 'utf8');
    assert.match(text, /fie:league-changing[^\n]+selectedWeek=null/, `${name} must reset its per-league week selection`);
  }
  console.log('PASS current-week defaults, hydration simulation refresh, M6 blocker semantics, and D/ST/K switch reset');
})().catch(error => {console.error(error); process.exitCode = 1;});
