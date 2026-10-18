#!/usr/bin/env node
/* R0 contract tests for app/core/status.js (UI contract §5.4) and the R0 wiring.
 * Runs the real browser modules in a VM sandbox; no network, no DOM. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const ROOT = path.resolve(__dirname, '..');
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8');

function sandbox({ week = 6, season = 2026, byeTeams = [] } = {}) {
  const window = { state: { weekly: { week }, league: { season, settings: {} }, rosters: [], selectedRoster: 1 } };
  window.currentWeek = () => week;
  window.FIECore = { SeasonResolver: { resolve: () => season } };
  window.FIEProjectionResolver = { isVerifiedBye: (p) => byeTeams.includes(p.team) };
  window.formatProfile = () => ({ dynasty: false });
  const ctx = vm.createContext({ window, Date, Math, Number, String, Object, Array, Map, Set, JSON });
  vm.runInContext(read('app/generated/ui-decision-policy.js'), ctx);
  vm.runInContext(read('app/core/status.js'), ctx);
  return window;
}

const now = Date.now();
let w = sandbox();
const S = w.FIEStatus;
assert.ok(S && w.FIE_UI_POLICY, 'status service and policy loaded');

// Source precedence: fresh feed for the bound week beats the 24 h player DB.
assert.strictEqual(S.resolve({ injuryStatus: 'Questionable', weeklyStatusFeed: { status: 'Doubtful', week: 6, season: 2026, at: now } }).code, 'Doubtful');
assert.strictEqual(S.resolve({ injuryStatus: 'Questionable', weeklyStatusFeed: { status: null, week: 6, season: 2026, at: now } }).code, null, 'feed "no designation" clears an old DB status');
assert.strictEqual(S.resolve({ injuryStatus: 'Out', weeklyStatusFeed: { status: 'Questionable', week: 5, season: 2026, at: now } }).code, 'Out', 'feed for another week is ignored');
assert.strictEqual(S.resolve({ injuryStatus: 'Out', weeklyStatusFeed: { status: null, week: 6, season: 2026, at: now - 13 * 3600e3 } }).code, 'Out', 'stale feed (> 12 h) falls back to DB');
assert.strictEqual(S.resolve({ injuryStatus: 'Q' }).source, 'player-db');

// BYE from the verified schedule.
w = sandbox({ byeTeams: ['DET'] });
assert.strictEqual(w.FIEStatus.resolve({ team: 'DET' }).code, 'BYE');
assert.strictEqual(w.FIEStatus.resolve({ team: 'DET' }).unavailable, true);

// Policy: Doubtful treated as out with a tie-break; Questionable unchanged (user decisions D6, F4).
assert.strictEqual(S.recommendationValue({ injuryStatus: 'Doubtful' }, 12), 12 * w.FIE_UI_POLICY.status.doubtful_tiebreak_factor);
assert.strictEqual(S.recommendationValue({ injuryStatus: 'Out' }, 12), 0);
assert.strictEqual(S.recommendationValue({ injuryStatus: 'Questionable' }, 12), 12);
assert.strictEqual(S.resolve({ injuryStatus: 'Questionable' }).monitor, true);
assert.strictEqual(S.recommendationValue({ injuryStatus: null }, null), null, 'missing projection stays missing');

// Reserve eligibility follows Sleeper league settings.
assert.strictEqual(S.irEligible('IR', {}), true);
assert.strictEqual(S.irEligible('Out', { reserve_allow_out: 1 }), true);
assert.strictEqual(S.irEligible('Out', {}), false);
assert.strictEqual(S.freeReserveSlots({ reserve: ['1', '2'] }, { reserve_slots: 3 }), 1);

// Waiver add policy: never CLAIM an unavailable player; dynasty may STASH into a free legal IR slot.
const league = { settings: { reserve_slots: 3 } };
assert.deepStrictEqual(S.addPolicy({ injuryStatus: 'IR' }, { rosterId: 1, league, rosters: [{ roster_id: 1, reserve: ['a', 'b', 'c'] }], dynasty: false }).action, 'WATCH');
assert.strictEqual(S.addPolicy({ injuryStatus: 'IR' }, { rosterId: 1, league, rosters: [{ roster_id: 1, reserve: ['a'] }], dynasty: true }).action, 'STASH');
assert.strictEqual(S.addPolicy({ injuryStatus: 'IR' }, { rosterId: 1, league, rosters: [{ roster_id: 1, reserve: ['a'] }], dynasty: true }).allowClaim, false);
assert.strictEqual(S.addPolicy({ injuryStatus: null }, { rosterId: 1, league, rosters: [], dynasty: false }).allowClaim, true);
assert.strictEqual(sandbox({ byeTeams: ['MIA'] }).FIEStatus.addPolicy({ team: 'MIA' }, { rosterId: 1, league, rosters: [], dynasty: false }).allowClaim, true, 'a bye week does not block a rest-of-season add');

// R0 wiring (static): the fixes stay connected.
const runtime = read('app/v9.3.3-runtime-integrity.js'), index = read('index.html'), ui = read('app/decision-ui.js'), engines = read('app/decision-engines.js');
assert.ok(runtime.includes('scheduleLiveOverlay(id);'), 'WP0.1b live overlay scheduled after core load');
assert.ok(runtime.includes('syncLiveLeagueWeek(previousLeg)'), 'WP0.1 live week re-sync wired into applyLiveOverlay');
assert.ok(runtime.includes('p.weeklyStatusFeed='), 'N1 projection-feed status recorded');
assert.ok(index.includes('window.syncSeasonSelectV89?.();') && index.includes('window.syncSeasonSelectV89=syncSeasonSelectV89;'), 'WP0.4 weekly refresh no longer throws');
assert.ok(/<script src="app\/core\/status\.js"><\/script>/.test(index) && /<script src="app\/generated\/ui-decision-policy\.js"><\/script>/.test(index) && /<script src="app\/weekly-alerts\.js"><\/script>/.test(index), 'R0 scripts loaded');
assert.ok(index.indexOf('app/generated/ui-decision-policy.js') < index.indexOf('app/core/status.js'), 'policy loads before status service');
assert.ok(ui.includes('window.FIEStatus?.addPolicy?.(p,{rosterId:rid})') && (ui.match(/key:'status',label:'Status',value:x=>x\.status\?\.code/g) || []).length === 3, 'WP0.2 waiver action and status column in all formats');
assert.ok(engines.includes("allowClaim!==false"), 'WP0.2 Home/portfolio callouts skip unavailable adds');
console.log('UI status policy + R0 wiring: PASS');
