/* Tranche 1: six-format runtime characterization.
 * Default baseline mode PASSES only if the audited hybrid divergences are reproduced.
 * --mode target flips those same assertions to the intended post-fix contract.
 */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const HY='CHOPPED_BESTBALL';

function browserContext(){
  const listeners={};
  const ctx={
    console,window:null,state:{league:null,rosters:[],users:[],savedLeagues:[]},PLAYERS:[],
    localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},
    document:{readyState:'complete',getElementById:()=>null,querySelector:()=>null,addEventListener:()=>{}},
    performance:{now:()=>0},PerformanceObserver:undefined,
    AbortController,DOMException,CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}},
    setTimeout,clearTimeout,setInterval,clearInterval,Promise,Date,Number,String,Math,Object,Array,Set,Map,JSON,
    fetch:async()=>{throw new Error('network not used');}
  };
  ctx.window=ctx;ctx.location={href:'https://example.test/',origin:'https://example.test'};
  ctx.addEventListener=(n,f)=>(listeners[n]??=[]).push(f);ctx.dispatchEvent=e=>{for(const f of listeners[e.type]||[])f(e);return true;};
  ctx.FIEPortfolioConfig={entryFor:()=>null,config:{sleeper_username:'fixture'}};
  ctx.__format='REDRAFT';ctx.activeFormatKey=()=>ctx.__format;
  vm.createContext(ctx);
  for(const file of [
    'app/generated/runtime-contracts.js',
    'app/core/core-services.js',
    'app/runtime-foundation.js',
    'app/league-context.js',
    'app/core/draft-value-service.js',
    'app/core/value-calibration-guard.js'
  ]) vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
  return ctx;
}
function close(a,b,eps=1e-9){return Math.abs(Number(a)-Number(b))<=eps;}
const ctx=browserContext();
const fixture={league_id:'hybrid',name:'Hybrid fixture',type:'redraft',settings:{type:3,best_ball:1},total_rosters:12,roster_positions:['QB','RB','WR','TE','FLEX','BN'],scoring_settings:{pass_td:4,rec:1}};
const resolved=ctx.FIELeagueProfileResolver.resolve(fixture,HY);

ctx.state.league=fixture;ctx.__format=HY;
const lc=ctx.FIELeagueContext.build(fixture);

ctx.FIEProjectionResolver={
  week:p=>({value:p.weeklyProjection}),
  range:p=>({low:p.weeklyFloor,high:p.weeklyCeiling})
};
const players=[
  {sleeperId:'a',name:'A',position:'QB',team:'A',leagueEligible:true,engineSeasonProjection:320,projectedVOR:80,weeklyProjection:20,weeklyFloor:8,weeklyCeiling:32,currentOpportunity:80},
  {sleeperId:'b',name:'B',position:'RB',team:'B',leagueEligible:true,engineSeasonProjection:260,projectedVOR:55,weeklyProjection:16,weeklyFloor:7,weeklyCeiling:28,currentOpportunity:75},
  {sleeperId:'c',name:'C',position:'WR',team:'C',leagueEligible:true,engineSeasonProjection:250,projectedVOR:48,weeklyProjection:15,weeklyFloor:5,weeklyCeiling:30,currentOpportunity:70},
  {sleeperId:'d',name:'D',position:'TE',team:'D',leagueEligible:true,engineSeasonProjection:190,projectedVOR:28,weeklyProjection:11,weeklyFloor:4,weeklyCeiling:20,currentOpportunity:65}
];
ctx.PLAYERS=players;
const red=ctx.FIEDraftBaseValueService.compute(players,'REDRAFT');
const hyb=ctx.FIEDraftBaseValueService.compute(players,HY);
const redBy=new Map(red.map(x=>[x.id,x])),hybBy=new Map(hyb.map(x=>[x.id,x]));
const draftSameAsRed=players.every(p=>close(redBy.get(p.sleeperId).baseValue,hybBy.get(p.sleeperId).baseValue)&&redBy.get(p.sleeperId).architecture===hybBy.get(p.sleeperId).architecture);

const calWeight=ctx.FIECrossPositionCalibration.WEIGHT[HY];
const sample={__fie_mean:10,__fie_floor:2,__fie_ceiling:20,__fie_utility:14,__fie_vor:5};
const coreHybrid=ctx.FIECore.LineupOptimizer.objectiveForFormat(HY)(sample);
const coreBB=ctx.FIECore.LineupOptimizer.objectiveForFormat('REDRAFT_BESTBALL')(sample);
const coreChopped=ctx.FIECore.LineupOptimizer.objectiveForFormat('CHOPPED')(sample);

const wctx={console,postMessage:()=>{},setTimeout,clearTimeout,Math,Number,String,Array,Set,Map,JSON};
vm.createContext(wctx);vm.runInContext(fs.readFileSync('app/draft-monte-carlo-worker.js','utf8'),wctx,{filename:'draft-monte-carlo-worker.js'});
assert.strictEqual(typeof wctx.rosterUtility,'function','worker rosterUtility not reachable for characterization');
const wp={id:'p',position:'QB',mean:10,floor:2,ceiling:20,utility:14,vor:0};
function wutil(format){return wctx.rosterUtility([wp],{format,rosterPositions:['QB'],slotEligibility:{QB:['QB']}}).starterTotal;}
const workerHybrid=wutil(HY),workerBB=wutil('REDRAFT_BESTBALL'),workerChopped=wutil('CHOPPED');

const v9=fs.readFileSync('app/decision-model-v9.js','utf8');
assert.ok(v9.includes("fmt==='CHOPPED_BESTBALL'"),'V9 diagnostic hybrid branch unexpectedly absent');
assert.ok(v9.includes('lower_tail_surplus')&&v9.includes('spike_surplus'),'V9 diagnostic hybrid ingredients unexpectedly absent');

const result={
  mode,
  runtimeResolver:resolved,
  leagueContext:{format:lc.format,isBestBall:lc.isBestBall,isChopped:lc.isChopped,isDynasty:lc.isDynasty},
  draftBase:{sameAsRedraft:draftSameAsRed,architecture:hyb[0]?.architecture},
  calibration:{hybridWeight:calWeight??null},
  coreObjective:{hybrid:coreHybrid,bestball:coreBB,chopped:coreChopped},
  workerObjective:{hybrid:workerHybrid,bestball:workerBB,chopped:workerChopped},
  v9DiagnosticExplicitHybrid:true
};

if(mode==='baseline'){
  assert.strictEqual(resolved.format,'CHOPPED','baseline must reproduce runtime-foundation hybrid collapse');
  assert.strictEqual(lc.format,HY);
  assert.strictEqual(lc.isBestBall,true);
  assert.strictEqual(lc.isChopped,false,'baseline must reproduce LeagueContext chopped-capability loss');
  assert.strictEqual(draftSameAsRed,true,'baseline must reproduce DraftBase hybrid->Redraft/default valuation');
  assert.strictEqual(calWeight,undefined,'baseline must reproduce missing hybrid calibration weight');
  assert.ok(close(coreHybrid,coreBB)&&!close(coreHybrid,coreChopped),'baseline Core hybrid must reproduce generic Best Ball objective');
  assert.ok(close(workerHybrid,workerBB)&&!close(workerHybrid,workerChopped),'baseline worker hybrid must reproduce generic Best Ball objective');
  console.log('KNOWN_GAP_REPRODUCED six-format hybrid runtime divergence');
}else if(mode==='target'){
  assert.strictEqual(resolved.format,HY,'target: runtime resolver must preserve explicit hybrid');
  assert.strictEqual(lc.isBestBall,true);
  assert.strictEqual(lc.isChopped,true,'target: hybrid must expose chopped capability');
  assert.strictEqual(draftSameAsRed,false,'target: DraftBase hybrid must not fall through to Redraft');
  assert.ok(String(hyb[0]?.architecture||'').includes('hybrid'),'target: DraftBase must identify its explicit hybrid architecture');
  assert.strictEqual(Number(calWeight),8,'target: hybrid calibration keeps the parent-format scarcity weight');
  const expectedHybrid=.50*sample.__fie_mean+.225*sample.__fie_floor+.275*sample.__fie_ceiling;
  assert.ok(close(coreHybrid,expectedHybrid),'target: Core hybrid must equal the governed 50/50 Chopped + Redraft Best Ball production blend');
  assert.ok(close(workerHybrid,expectedHybrid),'target: worker hybrid must equal the governed Core hybrid production blend');
  assert.ok(!close(coreHybrid,coreBB)&&!close(coreHybrid,coreChopped),'target: Core hybrid objective must be explicit, not generic BB or Chopped');
  assert.ok(!close(workerHybrid,workerBB)&&!close(workerHybrid,workerChopped),'target: worker hybrid objective must be explicit, not generic BB or Chopped');
}else throw new Error(`unknown mode ${mode}`);
console.log(JSON.stringify(result));
