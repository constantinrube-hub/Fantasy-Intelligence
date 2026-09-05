/* Tranche 3A: Core/A3/D replacement parity across every enabled league profile. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
const registry=JSON.parse(fs.readFileSync(path.join(ROOT,'data/research/leagues/registry.json'),'utf8'));
const entries=Object.entries(registry.leagues||{}).filter(([,x])=>x&&x.enabled===true);
assert.strictEqual(entries.length,22,'expected 22 enabled leagues');

const POSITIONS=['QB','RB','WR','TE','K','DEF','DL','LB','DB','P','OL'];
const formatCounts={};
const results=[];
function makePlayers(){
  const out=[];
  for(const [pi,pos] of POSITIONS.entries()){
    const n=80,base=500-pi*12;
    for(let i=0;i<n;i++)out.push({sleeperId:`${pos}${i+1}`,name:`${pos}${i+1}`,position:pos,team:'T',leagueEligible:true,availability:'FA',engineSeasonProjection:base-i*2,sleeperSeasonProjection:base-i*2,weeklyProjection:(base-i*2)/17,modelScore:98-i*.7,projectedVOR:0});
  }
  return out;
}
for(const [leagueId,meta] of entries){
  const profile=JSON.parse(fs.readFileSync(path.join(ROOT,meta.profile_path),'utf8'));
  formatCounts[profile.format]=(formatCounts[profile.format]||0)+1;
  const players=makePlayers(),state={league:profile,rosters:Array.from({length:Number(profile.total_rosters)||1},(_,i)=>({roster_id:i+1})),replacement:{ownershipInfluence:100,benchInfluence:0},projectionStatus:{season:true},weekly:{week:1,weekly2025:[],weekly2026:[],snaps2026:[],team2025:[],team2026:[]},validation:{snapshots:{}},featureLearning:{byPosition:{},matchupByPosition:{}},weights:{fa:0},trending:{},modelHealth:{}};
  const ctx={console,window:null,state,PLAYERS:players,performance:{now:()=>0},document:{getElementById:()=>null},setTimeout:()=>0,clearTimeout:()=>{},requestIdleCallback:undefined,Date,Math,Number,String,Object,Array,Set,Map,JSON,Promise,CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}}};
  ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=()=>true;ctx.FIE934A2={installed:true,report:()=>({})};ctx.FIE89={playerDecisionValue:p=>p.modelScore||0,marketEdgeValue:()=>null};ctx.weightedModel=p=>p.modelScore||0;ctx.scoringFit=()=>50;ctx.replacementScoreFor=()=>({level:null,advantage:null,score:null,adjustment:0});ctx.optimizeLineup=()=>{};ctx.renderReplacementSummary=()=>{};ctx.renderHealthDiagnostics=()=>{};ctx.loadValidationSnapshots=()=>{};
  vm.createContext(ctx);
  for(const file of ['app/generated/runtime-contracts.js','app/core/core-services.js','app/v9.3.4a3-score-performance.js','app/v9.3.4d-starter-economics.js'])vm.runInContext(fs.readFileSync(path.join(ROOT,file),'utf8'),ctx,{filename:file});
  ctx.computeReplacementLevels();ctx.computeProjectedReplacementLevels();
  const econ=ctx.FIE934D.computeEconomics(players,profile,state.rosters);
  const demand=ctx.FIECore.LeagueDemandService.starterDemand({league:profile,players,valueFn:ctx.FIECore.LeagueDemandService.defaultValue});
  const checked=[];
  for(const pos of POSITIONS){
    if(Number(demand.leagueStarterDemand[pos]||0)<=0)continue;
    const c=ctx.FIECore.ReplacementService.profile(pos,{league:profile,players,state,valueFn:ctx.FIECore.LeagueDemandService.defaultValue}),a=state.projectedReplacementLevels[pos],d=econ.replacementByPosition[pos];
    assert.ok(a,`${leagueId}/${pos}: A3 projected replacement missing`);
    assert.ok(d,`${leagueId}/${pos}: D replacement missing`);
    assert.strictEqual(a.cutoff,c.cutoff,`${leagueId}/${pos}: Core/A3 cutoff mismatch`);
    assert.strictEqual(d.replacementRank,c.cutoff,`${leagueId}/${pos}: Core/D cutoff mismatch`);
    assert.strictEqual(d.structuralCutoff,c.cutoff,`${leagueId}/${pos}: D structural cutoff mismatch`);
    assert.strictEqual(d.source,'FIECore.ReplacementService',`${leagueId}/${pos}: D source mismatch`);
    assert.strictEqual(c.ownershipAffectsCutoff,false,`${leagueId}/${pos}: ownership feedback enabled`);
    checked.push(pos);
  }
  assert.ok(checked.length>0,`${leagueId}: no starter positions checked`);
  results.push({leagueId,format:profile.format,teams:profile.total_rosters,checked});
}
assert.deepStrictEqual(formatCounts,{DYNASTY:7,CHOPPED:5,REDRAFT:4,REDRAFT_BESTBALL:2,DYNASTY_BESTBALL:3,CHOPPED_BESTBALL:1});
console.log(JSON.stringify({enabled:entries.length,formatCounts,results}));
console.log('PASS Tranche 3A Core/A3/D replacement parity across all 22 enabled league profiles');
