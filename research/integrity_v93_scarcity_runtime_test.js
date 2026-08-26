/* V9.3 starter-slot scarcity / league-context runtime integrity. */
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
global.window={}; global.document={getElementById:()=>null}; global.CustomEvent=function(){};
window.addEventListener=()=>{}; window.dispatchEvent=()=>{};
for(const rel of ['app/generated/runtime-contracts.js','app/core/core-services.js']){
  vm.runInThisContext(fs.readFileSync(path.join(ROOT,rel),'utf8'),{filename:rel});
}
const {LeagueDemandService,ReplacementService,LineupOptimizer}=window.FIECore;
function rows(pos,n,base){return Array.from({length:n},(_,i)=>({id:`${pos}${i+1}`,position:pos,value:base-i}));}
const players=[...rows('QB',40,120),...rows('RB',80,100),...rows('WR',100,100),...rows('TE',40,75)];
const valueFn=p=>p.value;
const oneQB={total_rosters:12,roster_positions:['QB','RB','RB','WR','WR','TE','FLEX','BN','BN']};
const superflex={total_rosters:12,roster_positions:['QB','RB','RB','WR','WR','TE','FLEX','SUPER_FLEX','BN']};
const a=LeagueDemandService.starterDemand({league:oneQB,players,valueFn});
const b=LeagueDemandService.starterDemand({league:superflex,players,valueFn});
if(!(b.leagueStarterDemand.QB>a.leagueStarterDemand.QB))throw new Error(`Superflex must increase exact QB starter demand: 1QB=${a.leagueStarterDemand.QB}, SF=${b.leagueStarterDemand.QB}`);
const ca=ReplacementService.cutoff('QB',{league:oneQB,players,state:{replacement:{benchInfluence:0}},valueFn});
const cb=ReplacementService.cutoff('QB',{league:superflex,players,state:{replacement:{benchInfluence:0}},valueFn});
if(!(cb>ca))throw new Error(`Superflex must deepen QB replacement cutoff: 1QB=${ca}, SF=${cb}`);
const pool=[{id:'q',position:'QB',value:20},{id:'r',position:'RB',value:10},{id:'w',position:'WR',value:9},{id:'t',position:'TE',value:8}];
const opt=LineupOptimizer.optimize(pool,['QB','RB','WR','TE'],valueFn);
if(opt.unfilledSlots.length||opt.assignment.length!==4)throw new Error('Exact legal lineup optimizer failed canonical starter-slot assignment');
console.log(`V9.3 scarcity runtime integrity OK: QB demand ${a.leagueStarterDemand.QB}->${b.leagueStarterDemand.QB}, replacement cutoff ${ca}->${cb}`);
