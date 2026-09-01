/* Tranche 1: Core <-> A3 <-> D starter-demand/replacement characterization. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const league={league_id:'parity',total_rosters:2,roster_positions:['QB','RB','WR','TE','FLEX','SUPER_FLEX','BN'],settings:{teams:2}};
const make=(pos,n,start,step)=>Array.from({length:n},(_,i)=>({sleeperId:`${pos}${i+1}`,name:`${pos}${i+1}`,position:pos,team:'T',leagueEligible:true,availability:'FA',engineSeasonProjection:start-i*step,weeklyProjection:(start-i*step)/17,modelScore:90-i*2,projectedVOR:0}));
const players=[...make('QB',7,340,25),...make('RB',10,300,16),...make('WR',10,295,15),...make('TE',8,240,14)];
const listeners={};
const state={league,rosters:[{roster_id:1},{roster_id:2}],replacement:{ownershipInfluence:0,benchInfluence:0},projectionStatus:{season:true},weekly:{week:1,weekly2025:[],weekly2026:[],snaps2026:[],team2025:[],team2026:[]},validation:{snapshots:{}},featureLearning:{byPosition:{},matchupByPosition:{}},weights:{fa:0},trending:{},modelHealth:{}};
const ctx={console,window:null,state,PLAYERS:players,performance:{now:()=>0},document:{getElementById:()=>null},
  setTimeout:()=>0,clearTimeout:()=>{},requestIdleCallback:undefined,Date,Math,Number,String,Object,Array,Set,Map,JSON,Promise,
  CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}}
};
ctx.window=ctx;ctx.addEventListener=(n,f)=>(listeners[n]??=[]).push(f);ctx.dispatchEvent=()=>true;
ctx.FIE934A2={installed:true,report:()=>({})};ctx.FIE89={playerDecisionValue:p=>p.modelScore||0,marketEdgeValue:()=>null};
ctx.weightedModel=p=>p.modelScore||0;ctx.scoringFit=()=>50;ctx.replacementScoreFor=()=>({level:null,advantage:null,score:null,adjustment:0});ctx.optimizeLineup=()=>{};
ctx.renderReplacementSummary=()=>{};ctx.renderHealthDiagnostics=()=>{};ctx.loadValidationSnapshots=()=>{};
vm.createContext(ctx);
for(const file of ['app/generated/runtime-contracts.js','app/core/core-services.js','app/v9.3.4a3-score-performance.js','app/v9.3.4d-starter-economics.js'])
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});

assert.ok(ctx.FIE934A3?.installed,'A3 not installed for characterization');
assert.ok(ctx.FIE934D?.installed,'D not installed for characterization');
const core=ctx.FIECore.LeagueDemandService.starterDemand({league,players,valueFn:p=>p.engineSeasonProjection});
const a3=ctx.FIE934A3.computeMarginalDemand();
const d=ctx.FIE934D.computeDemand(players,league,state.rosters);
const positions=['QB','RB','WR','TE'];
const demand=[];
for(const pos of positions){
  const c=Number(core.perTeam[pos]||0),a=Number(a3[pos]||0),x=Number(d.perTeamDemand[pos]||0);
  demand.push({position:pos,core:c,a3:a,d:x});
  assert.ok(Math.abs(c-a)<1e-9,`${pos}: Core/A3 starter demand diverged`);
  assert.ok(Math.abs(c-x)<1e-9,`${pos}: Core/D starter demand diverged`);
}

ctx.computeReplacementLevels();
ctx.computeProjectedReplacementLevels();
const econ=ctx.FIE934D.computeEconomics(players,league,state.rosters);
const replacementRows=[];
for(const pos of positions){
  const cp=ctx.FIECore.ReplacementService.profile(pos,{league,players,state,valueFn:p=>p.engineSeasonProjection});
  const a=state.projectedReplacementLevels[pos];
  const dr=econ.replacementByPosition[pos];
  if(!a||!dr)continue;
  const relation={position:pos,coreCutoff:cp.cutoff,a3ProjectedCutoff:a.cutoff,dReplacementRank:dr.replacementRank,
    dHasStructuralCutoff:Object.prototype.hasOwnProperty.call(dr,'structuralCutoff')||Object.prototype.hasOwnProperty.call(dr,'sourceCutoff')};
  replacementRows.push(relation);
  assert.strictEqual(a.cutoff,cp.cutoff,`${pos}: baseline Core/A3 projected cutoff must agree under zero ownership/bench influence`);
}
const conventionMismatches=replacementRows.filter(x=>x.dReplacementRank!==x.coreCutoff);
if(mode==='baseline'){
  assert.ok(conventionMismatches.length>0,'baseline must reproduce D separate replacement-rank convention');
  assert.ok(conventionMismatches.every(x=>x.dReplacementRank===x.coreCutoff+1),`unexpected D replacement relation ${JSON.stringify(conventionMismatches)}`);
  console.log('KNOWN_GAP_REPRODUCED D replacement frontier is recomputed as first non-starter rather than carrying canonical cutoff provenance');
}else if(mode==='target'){
  for(const x of replacementRows)assert.ok(x.dHasStructuralCutoff,`${x.position}: target D economics must expose/consume canonical structural cutoff provenance`);
}else throw new Error(`unknown mode ${mode}`);
console.log(JSON.stringify({mode,demand,replacementRows,conventionMismatches}));
