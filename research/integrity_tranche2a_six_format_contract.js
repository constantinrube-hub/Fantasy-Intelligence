/* Permanent Tranche 2A six-format capability + production-semantics contract. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const EXPECTED={
  REDRAFT:{dynasty:false,bestBall:false,chopped:false},
  DYNASTY:{dynasty:true,bestBall:false,chopped:false},
  CHOPPED:{dynasty:false,bestBall:false,chopped:true},
  REDRAFT_BESTBALL:{dynasty:false,bestBall:true,chopped:false},
  DYNASTY_BESTBALL:{dynasty:true,bestBall:true,chopped:false},
  CHOPPED_BESTBALL:{dynasty:false,bestBall:true,chopped:true}
};
const contract=JSON.parse(fs.readFileSync('config/contracts/runtime-contracts.json','utf8'));
assert.deepStrictEqual(Object.keys(contract.league_formats||{}).sort(),Object.keys(EXPECTED).sort(),'runtime contract must own exactly the six supported league formats');
for(const [fmt,e] of Object.entries(EXPECTED)){
  const p=contract.league_formats[fmt];assert.ok(p,fmt);assert.strictEqual(p.dynasty,e.dynasty,`${fmt} dynasty`);assert.strictEqual(p.best_ball,e.bestBall,`${fmt} best_ball`);assert.strictEqual(p.chopped,e.chopped,`${fmt} chopped`);assert.ok(String(p.label||'').trim(),`${fmt} label`);
}

const ctx={console,window:null,state:{league:null,rosters:[],leagueRules:{format:'REDRAFT'}},PLAYERS:[],document:{readyState:'loading',addEventListener(){},getElementById(){return null;}},localStorage:{getItem(){return null;},setItem(){},removeItem(){}},performance:{now:()=>0},PerformanceObserver:undefined,AbortController,DOMException,CustomEvent:class{},setTimeout,clearTimeout,setInterval,clearInterval,Promise,Date,Number,String,Math,Object,Array,Set,Map,JSON};
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=()=>true;ctx.FIEPortfolioConfig={entryFor:()=>null,config:{sleeper_username:'fixture'}};
vm.createContext(ctx);
for(const f of ['app/generated/runtime-contracts.js','app/core/core-services.js'])vm.runInContext(fs.readFileSync(f,'utf8'),ctx,{filename:f});
for(const [fmt,e] of Object.entries(EXPECTED)){
  const p=ctx.FIECore.FormatRegistry.profile(fmt);assert.strictEqual(p.key,fmt);assert.strictEqual(p.dynasty,e.dynasty);assert.strictEqual(p.bestBall,e.bestBall);assert.strictEqual(p.chopped,e.chopped);
}
const sample={__fie_mean:10,__fie_floor:2,__fie_ceiling:20,__fie_utility:14,__fie_vor:0};
const objectiveExpected={REDRAFT:10,DYNASTY:14,CHOPPED:6.4,REDRAFT_BESTBALL:15.5,DYNASTY_BESTBALL:15.5,CHOPPED_BESTBALL:10.95};
for(const [fmt,v] of Object.entries(objectiveExpected))assert.ok(Math.abs(ctx.FIECore.LineupOptimizer.objectiveForFormat(fmt)(sample)-v)<1e-9,`${fmt} Core objective drift`);

// DraftBase five-format numerics are frozen from the Tranche-1 preflight fixture.
// Only the sixth format is allowed to move from its accidental Redraft fallback.
ctx.state.league={league_id:'fixture',total_rosters:12,roster_positions:['QB','RB','WR','TE','FLEX','BN']};ctx.state.rosters=[];
ctx.FIEProjectionResolver={week:p=>({value:p.weeklyProjection}),range:p=>({low:p.weeklyFloor,high:p.weeklyCeiling})};
vm.runInContext(fs.readFileSync('app/core/draft-value-service.js','utf8'),ctx,{filename:'app/core/draft-value-service.js'});
const draftPlayers=[
{sleeperId:'a',name:'A',position:'QB',team:'A',leagueEligible:true,engineSeasonProjection:320,projectedVOR:80,weeklyProjection:20,weeklyFloor:8,weeklyCeiling:32,currentOpportunity:80},
{sleeperId:'b',name:'B',position:'RB',team:'B',leagueEligible:true,engineSeasonProjection:260,projectedVOR:55,weeklyProjection:16,weeklyFloor:7,weeklyCeiling:28,currentOpportunity:75},
{sleeperId:'c',name:'C',position:'WR',team:'C',leagueEligible:true,engineSeasonProjection:250,projectedVOR:48,weeklyProjection:15,weeklyFloor:5,weeklyCeiling:30,currentOpportunity:70},
{sleeperId:'d',name:'D',position:'TE',team:'D',leagueEligible:true,engineSeasonProjection:190,projectedVOR:28,weeklyProjection:11,weeklyFloor:4,weeklyCeiling:20,currentOpportunity:65}
];
const draftExpected={
REDRAFT:[87.95,62.95000000000001,37.95,12.95],
DYNASTY:[90.3,63.63333333333334,36.96666666666667,10.3],
CHOPPED:[92.24,64.24,36.24,8.24],
REDRAFT_BESTBALL:[82.90666666666668,56.90666666666666,52.906666666666666,8.24],
DYNASTY_BESTBALL:[87.04333333333334,60.04333333333335,47.04333333333334,6.71],
CHOPPED_BESTBALL:[87.57333333333334,60.57333333333334,44.57333333333334,8.24]
};
for(const [fmt,vals] of Object.entries(draftExpected)){
  const rows=ctx.FIEDraftBaseValueService.compute(draftPlayers,fmt).sort((a,b)=>a.id.localeCompare(b.id));
  rows.forEach((r,i)=>assert.ok(Math.abs(r.baseValue-vals[i])<1e-9,`${fmt} DraftBase fixture drift for ${r.id}`));
  if(fmt==='CHOPPED_BESTBALL')assert.ok(rows.every(r=>r.architecture.includes('hybrid')),'hybrid DraftBase architecture label missing');
}

// Legacy shell remains active. Execute just the V8.2 league-engine layer and
// require it to surface the canonical capabilities for all six formats.
const html=fs.readFileSync('index.html','utf8'),m=html.match(/<script id="v82LeagueEngineLayer">([\s\S]*?)<\/script>/);assert.ok(m,'V8.2 league engine script not found');
const shellStart=m[1].indexOf("const EXPERIENCE_KEYS"),shellEnd=m[1].indexOf("function canonicalExperienceKey");assert.ok(shellStart>=0&&shellEnd>shellStart,'legacy format slice not found');
ctx.state.leagueRules={format:'REDRAFT',detectedFormat:'REDRAFT',allowedExperience:['R'],maxByExperience:{},chopped:{}};ctx.state.activeTab='home';ctx.FIE={};
vm.runInContext(m[1].slice(shellStart,shellEnd),ctx,{filename:'index.html#v82LeagueEngineLayer-format-slice'});
for(const [fmt,e] of Object.entries(EXPECTED)){
  ctx.state.leagueRules.format=fmt;const p=vm.runInContext('formatProfile()',ctx);assert.strictEqual(p.dynasty,e.dynasty,`${fmt} shell dynasty`);assert.strictEqual(p.bestBall,e.bestBall,`${fmt} shell bestBall`);assert.strictEqual(p.chopped,e.chopped,`${fmt} shell chopped`);
}

// Main-thread Monte Carlo serialization must carry weekly floor and ceiling for
// the hybrid before the pure worker ever sees a player record.
ctx.state.league={league_id:'hybrid',roster_positions:['QB']};ctx.FIELeagueProfileResolver={resolve:()=>({format:'CHOPPED_BESTBALL'})};ctx.activeFormatKey=()=> 'CHOPPED_BESTBALL';ctx.document.querySelectorAll=()=>[];ctx.document.createElement=()=>({});
vm.runInContext(fs.readFileSync('app/decision-engines.js','utf8'),ctx,{filename:'app/decision-engines.js'});
const ip={sleeperId:'x',name:'X',position:'QB',team:'T',engineSeasonProjection:340,weeklyProjection:20,weeklyFloor:8,weeklyCeiling:32,projectedVOR:40};
const irec=ctx.FIEDecisionEngines.__formatInternals.workerPlayerRecord(ip,{marketOf:()=>10,decisionMap:new Map([['x',50]])});
assert.strictEqual(irec.mean,20,'hybrid worker serializer mean must be weekly');assert.strictEqual(irec.floor,8,'hybrid worker serializer must carry weekly floor');assert.strictEqual(irec.ceiling,32,'hybrid worker serializer must carry weekly ceiling');

// D/ST specialist uses the equal blend of its pre-existing Chopped and Best
// Ball production scores, with no research-challenger activation.
ctx.document.getElementById=()=>null;ctx.__format='CHOPPED_BESTBALL';ctx.activeFormatKey=()=>ctx.__format;vm.runInContext(fs.readFileSync('app/dst-intelligence.js','utf8'),ctx,{filename:'app/dst-intelligence.js'});
const dstExpected={REDRAFT:10,DYNASTY:10,CHOPPED:6.64,REDRAFT_BESTBALL:14.5,DYNASTY_BESTBALL:14.5,CHOPPED_BESTBALL:10.57};
for(const [fmt,v] of Object.entries(dstExpected)){ctx.__format=fmt;const got=ctx.FIEDST.decisionScore({mean:10,low:2,high:20});assert.ok(Math.abs(got-v)<1e-9,`${fmt} D/ST score drift: ${got} != ${v}`);}

// Worker must preserve the same five pre-existing numerical objectives and use
// the explicit hybrid blend for the sixth.
const wctx={console,postMessage(){},setTimeout,clearTimeout,Math,Number,String,Array,Set,Map,JSON};vm.createContext(wctx);vm.runInContext(fs.readFileSync('app/draft-monte-carlo-worker.js','utf8'),wctx);
const wp={id:'p',position:'QB',mean:10,floor:2,ceiling:20,utility:14,vor:0};
for(const [fmt,v] of Object.entries(objectiveExpected)){
  const got=wctx.rosterUtility([wp],{format:fmt,formatCapabilities:ctx.FIECore.FormatRegistry.profile(fmt),rosterPositions:['QB'],slotEligibility:{QB:['QB']}}).starterTotal;
  assert.ok(Math.abs(got-v)<1e-9,`${fmt} worker objective drift: ${got} != ${v}`);
}
console.log('PASS six-format generated capability contract, Core, legacy shell and Monte Carlo objectives');
