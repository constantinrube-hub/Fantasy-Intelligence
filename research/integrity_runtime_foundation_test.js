const fs=require('fs'),vm=require('vm');
const contracts=fs.readFileSync('app/generated/runtime-contracts.js','utf8'),core=fs.readFileSync('app/core/core-services.js','utf8'),code=fs.readFileSync('app/runtime-foundation.js','utf8');
const listeners={};
const ctx={console,setTimeout,clearTimeout,Date,Math,JSON,Promise,AbortController,CustomEvent:function(type,opts){this.type=type;this.detail=opts?.detail;},performance:{now:()=>0},fetch:async()=>{throw new Error('not used')},caches:undefined,
  state:{league:null,savedLeagues:[],rosters:[],users:[]},localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},FIE:{},FIE89:{scoringAudit:()=>({unsupported:['fgm_60p','pts_allow_0']})},
  document:{readyState:'complete',getElementById:()=>null,querySelector:()=>null},
  addEventListener:(n,f)=>{(listeners[n]??=[]).push(f)},dispatchEvent:()=>{},
};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(contracts,ctx,{filename:'runtime-contracts.js'});vm.runInContext(core,ctx,{filename:'core-services.js'});vm.runInContext(code,ctx,{filename:'runtime-foundation.js'});
let r=ctx.FIELeagueProfileResolver.resolve({name:'Anything',settings:{type:3}},'AUTO');
if(r.format!=='CHOPPED'||r.source!=='sleeper_settings_type_3')throw new Error('native chopped type not authoritative');
r=ctx.FIELeagueProfileResolver.resolve({name:'Chopped',settings:{type:3}},{formatOverride:'REDRAFT'});
if(r.format!=='REDRAFT'||r.source!=='explicit_override')throw new Error('explicit override precedence failed');
const seq=ctx.FIEDraftSequence.sequence({type:'snake',settings:{teams:4,rounds:5,reversal_round:3}});
const rounds=n=>seq.filter(x=>x.round===n).map(x=>x.slot).join(',');
if(rounds(1)!=='1,2,3,4'||rounds(2)!=='4,3,2,1'||rounds(3)!=='4,3,2,1'||rounds(4)!=='1,2,3,4'||rounds(5)!=='4,3,2,1')throw new Error('3RR sequence incorrect');
ctx.state.league={roster_positions:['QB','RB','WR','TE','FLEX'],scoring_settings:{pass_td:4,fgm_60p:3,pts_allow_0:10}};
const a=ctx.FIEScoringSupport.audit({unsupported:['fgm_60p','pts_allow_0']});
if(a.coverage!==1||a.unsupported.length||a.ignoredIrrelevant.length!==2)throw new Error('position-relevant scoring filter failed');
ctx.state.league={roster_positions:['QB','K','DEF'],scoring_settings:{pass_td:4,fgm_60p:3,pts_allow_0:10}};
const b=ctx.FIEScoringSupport.audit({unsupported:['fgm_60p','pts_allow_0']});
if(b.unsupported.length!==2||b.coverage>=1)throw new Error('relevant K/DST unsupported rules were incorrectly ignored');
console.log('OK: V9 runtime foundation format, explicit precedence, 3RR, and scoring relevance');
