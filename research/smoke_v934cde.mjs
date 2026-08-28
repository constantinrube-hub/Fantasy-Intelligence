import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const ROOT = new URL('../', import.meta.url);
globalThis.window = globalThis;
globalThis.CustomEvent = class CustomEvent { constructor(type, init={}){ this.type=type; this.detail=init.detail; } };
const listeners = new Map();
window.addEventListener = (type, fn)=>{ if(!listeners.has(type)) listeners.set(type,[]); listeners.get(type).push(fn); };
window.dispatchEvent = (evt)=>{ for(const fn of listeners.get(evt.type)||[]) fn(evt); return true; };
window.FIEPerformance = { push(){} };
window.FIECore = { Diagnostics:{capture(){} } };
window.FIELeagueController = { generation:1 };
window.render = ()=>{};
const nullEl = null;
globalThis.document = {
  getElementById(){ return nullEl; },
  querySelector(){ return null; },
  querySelectorAll(){ return []; },
  addEventListener(){},
  createElement(){ return {dataset:{},style:{},prepend(){},querySelector(){return null;},querySelectorAll(){return[];},set textContent(v){this._text=v;},get textContent(){return this._text||'';}}; },
  head:{appendChild(){}}, documentElement:{appendChild(){}}, readyState:'complete'
};
window.state = {league:null, rosters:[], selectedRoster:'1', selectedRosterId:'999'};
window.PLAYERS = [];
globalThis.PLAYERS = window.PLAYERS;

function load(rel){ const code=fs.readFileSync(new URL(rel, ROOT),'utf8'); vm.runInThisContext(code,{filename:rel}); }

// C: load without a live league to avoid any network work.
load('app/v9.3.4c-weekly-context.js');
assert.equal(window.FIE934C.VERSION,'9.3.4C');
assert.equal(window.FIE934C.selectedRosterId(),'1');
window.state.league={league_id:'L',total_rosters:2,roster_positions:['QB','RB','WR','FLEX','SUPER_FLEX','BN']};
window.state.rosters=[
 {roster_id:1,players:['q1','q2','r1','r2','w1','t1'],starters:[]},
 {roster_id:2,players:['q3','q4','r1','r2','w1','t1'],starters:[]}
];
window.PLAYERS=[
 {sleeperId:'q1',name:'QB1',position:'QB',weeklyProjection:25,modelScore:95,leagueEligible:true},
 {sleeperId:'q2',name:'QB2',position:'QB',weeklyProjection:22,modelScore:90,leagueEligible:true},
 {sleeperId:'q3',name:'QB3',position:'QB',weeklyProjection:21,modelScore:89,leagueEligible:true},
 {sleeperId:'q4',name:'QB4',position:'QB',weeklyProjection:20,modelScore:87,leagueEligible:true},
 {sleeperId:'r1',name:'RB1',position:'RB',weeklyProjection:18,modelScore:88,leagueEligible:true},
 {sleeperId:'r2',name:'RB2',position:'RB',weeklyProjection:14,modelScore:75,leagueEligible:true},
 {sleeperId:'w1',name:'WR1',position:'WR',weeklyProjection:17,modelScore:84,leagueEligible:true},
 {sleeperId:'t1',name:'TE1',position:'TE',weeklyProjection:13,modelScore:72,leagueEligible:true},
];
globalThis.PLAYERS=window.PLAYERS;
const lineup=window.FIE934C.projectedLineup(window.state.rosters[0],1);
assert.equal(lineup.requiredSlots,5);
assert.equal(lineup.filledSlots,5);
assert(lineup.lineup.some(x=>x.slot==='SUPER_FLEX'&&x.position==='QB'));
const wp=window.FIE934C.normalWinProbability(110,100,15,15);
assert(wp>.5&&wp<1);
assert.equal(window.FIE934C.eligible('TE','WRRB_FLEX'),false);
assert.equal(window.FIE934C.eligible('EDGE','DL'),true);
assert.equal(window.FIE934C.eligible('S','DB'),true);
let matchupFetches=0;window.FIEDataClient={response:async()=>{matchupFetches++;return{ok:true,status:200,json:async()=>[{roster_id:1,matchup_id:77},{roster_id:2,matchup_id:77}]};}};
const quick=await window.FIE934C.get({week:1,rosterId:'1',force:true});
assert.equal(quick.opponentRosterId,'2');
assert.equal(quick.fullSimulationRequired,false);
assert.equal(matchupFetches,1);
assert(quick.myMean!==null&&quick.oppMean!==null&&quick.winProbability!==null);

// D: universal slot economics, with SF increasing QB demand and player fields attached.
window.FIE934A3={installed:true};
window.FIE89={playerDecisionValue:p=>Number(p.modelScore)||0,marketEdgeValue:()=>0};
load('app/v9.3.4d-starter-economics.js');
assert.equal(window.FIE934D.VERSION,'9.3.4D');
const dctx=window.FIE934D.compute({rerank:true,render:false});
assert(dctx);
assert.equal(dctx.effectiveDemand.QB,4);
const oneQb=window.FIE934D.computeDemand(window.PLAYERS,{league_id:'L1',total_rosters:2,roster_positions:['QB','RB','WR','FLEX','BN']},window.state.rosters);
assert.equal(oneQb.effectiveDemand.QB,2);
assert.equal(dctx.perTeamDemand.QB,2);
assert.equal(oneQb.perTeamDemand.QB,1);
assert(window.PLAYERS.every(p=>p.starterEconomics));
assert(window.PLAYERS.some(p=>p.starterEconomics.starterProbability>0));
assert.equal(window.FIE934D.slotEligible('TE','WRRB_FLEX'),false);
assert.equal(window.FIE934D.slotEligible('QB','SUPER_FLEX'),true);
assert.equal(window.FIE934D.slotEligible('EDGE','IDP_FLEX'),true);
assert.equal(window.FIE934D.slotEligible('FS','DB'),true);

// E: verified return keys + counterfactual legacy completion.
window.state.league.scoring_settings={kr_yd:.1,pr_yd:.05,kr_td:6,st_td:6,def_st_td:6};
window.scorePublicStats=(row)=>Number(row.base_points||0); // deliberately excludes returns
load('app/v9.3.4e-return-scoring.js');
assert.equal(window.FIE934E.VERSION,'9.3.4E');
const row={base_points:10,kickoff_return_yards:100,punt_return_yards:20,kickoff_return_tds:1};
const ret=window.FIE934E.scoreReturnRow(row);
assert.equal(ret.points,17);
assert.equal(ret.weights.kr_td_source,'kr_td');
assert.equal(window.FIE934E.completionDecision(50,33,17).mode,'already-complete');
assert.equal(window.FIE934E.completionDecision(50,33,17).added,0);
assert.equal(window.FIE934E.completionDecision(33,33,17).result,50);
assert.equal(window.FIE934E.completionDecision(43,33,17).mode,'partial-completed');
assert.equal(window.FIE934E.completionDecision(43,33,17).result,50);
const completed=window.scorePublicStats(row,window.PLAYERS[0]);
assert.equal(completed,27);
assert.equal(window.PLAYERS[0].returnScoring.completionMode,'missing-completed');
const aggregate=window.FIE934E.scoreReturnRow({special_teams_tds:2},{st_td:6});
assert.equal(aggregate.points,12);
assert.equal(aggregate.aggregateTdMode,'safe-equal-weight aggregate');
const noProj={};window.FIE934E.auditPlayerProjection(noProj);assert.equal(noProj.returnProjectionPoints,null);

console.log('V9.3.4C-E smoke: PASS', {
  lineup: lineup.lineup.map(x=>`${x.slot}:${x.position}`),
  winProbability: Math.round(wp*1000)/1000,
  qbDemand: dctx.effectiveDemand.QB,
  returnPoints: ret.points,
  completedPublicPoints: completed
});
process.exit(0);
