/* Tranche 1: execute all real enabled profiles through browser format/capability owners. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const registry=JSON.parse(fs.readFileSync('data/research/leagues/registry.json','utf8')).leagues;
const enabled=Object.entries(registry).filter(([,x])=>x&&x.enabled===true);
const listeners={};
const ctx={console,window:null,state:{league:null,rosters:[],users:[],savedLeagues:[]},PLAYERS:[],
  localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},
  document:{readyState:'complete',getElementById:()=>null,querySelector:()=>null,addEventListener:()=>{}},
  performance:{now:()=>0},PerformanceObserver:undefined,AbortController,DOMException,
  CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}},
  setTimeout,clearTimeout,Promise,Date,Number,String,Math,Object,Array,Set,Map,JSON,
  fetch:async()=>{throw new Error('network not used');}
};
ctx.window=ctx;ctx.location={href:'https://example.test/',origin:'https://example.test'};
ctx.addEventListener=(n,f)=>(listeners[n]??=[]).push(f);ctx.dispatchEvent=()=>true;
ctx.FIEPortfolioConfig={entryFor:id=>registry[String(id)]||null,config:{sleeper_username:'fixture'}};
ctx.__expected='REDRAFT';ctx.activeFormatKey=()=>ctx.__expected;
vm.createContext(ctx);
for(const file of ['app/generated/runtime-contracts.js','app/core/core-services.js','app/runtime-foundation.js','app/league-context.js'])
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});

const rows=[],resolverMismatches=[],capabilityMismatches=[],unknownSlots=[];
for(const [lid,meta] of enabled){
  const p=JSON.parse(fs.readFileSync(meta.profile_path,'utf8')),fmt=String(meta.format||p.format||'').toUpperCase();
  const league={
    league_id:lid,name:p.league_name||meta.league_name||lid,type:p.type||'redraft',
    settings:p.settings||{},total_rosters:Number(p.total_rosters||p.settings?.num_teams||0),
    roster_positions:p.roster_positions||[],scoring_settings:p.scoring_settings||{}
  };
  ctx.state.league=league;ctx.state.rosters=Array.from({length:league.total_rosters},(_,i)=>({roster_id:i+1}));ctx.__expected=fmt;
  const rr=ctx.FIELeagueProfileResolver.resolveFor(league,lid),lc=ctx.FIELeagueContext.build(league);
  const slots=league.roster_positions.map(x=>String(x).toUpperCase());
  const unk=slots.filter(s=>!ctx.FIECore.PositionRegistry.slot(s));
  if(unk.length)unknownSlots.push({leagueId:lid,format:fmt,slots:[...new Set(unk)]});
  const expected={
    format:fmt,teamCount:league.total_rosters,isDynasty:fmt.includes('DYNASTY'),
    isBestBall:fmt.includes('BESTBALL'),isChopped:fmt.includes('CHOPPED'),
    hasK:slots.includes('K'),hasDST:slots.includes('DEF')||slots.includes('DST'),
    hasSuperflex:slots.includes('SUPER_FLEX')||slots.includes('SF')||slots.filter(x=>x==='QB').length>=2
  };
  if(rr.format!==fmt)resolverMismatches.push({leagueId:lid,expected:fmt,actual:rr.format,source:rr.source});
  const caps=['format','teamCount','isDynasty','isBestBall','isChopped','hasK','hasDST','hasSuperflex'];
  for(const k of caps)if(lc[k]!==expected[k])capabilityMismatches.push({leagueId:lid,format:fmt,key:k,expected:expected[k],actual:lc[k]});
  rows.push({leagueId:lid,leagueName:meta.league_name,format:fmt,resolvedFormat:rr.format,teamCount:lc.teamCount,isDynasty:lc.isDynasty,isBestBall:lc.isBestBall,isChopped:lc.isChopped,hasK:lc.hasK,hasDST:lc.hasDST,hasSuperflex:lc.hasSuperflex});
}
assert.strictEqual(enabled.length,22,'enabled portfolio count drifted from Tranche 0');
assert.deepStrictEqual([...new Set(rows.map(x=>x.format))].sort(),['CHOPPED','CHOPPED_BESTBALL','DYNASTY','DYNASTY_BESTBALL','REDRAFT','REDRAFT_BESTBALL'].sort());
assert.strictEqual(unknownSlots.length,0,`real profiles contain runtime-contract unknown slots: ${JSON.stringify(unknownSlots)}`);
if(mode==='baseline'){
  assert.deepStrictEqual(resolverMismatches.map(x=>x.format||x.expected),['CHOPPED_BESTBALL'],'baseline should have exactly the known hybrid resolver mismatch');
  const capKeys=capabilityMismatches.map(x=>`${x.format}:${x.key}`);
  assert.deepStrictEqual(capKeys,['CHOPPED_BESTBALL:isChopped'],'baseline should have exactly the known hybrid chopped-capability mismatch');
  console.log('KNOWN_GAP_REPRODUCED all-22 runtime semantic matrix: hybrid-only mismatch');
}else if(mode==='target'){
  assert.strictEqual(resolverMismatches.length,0,JSON.stringify(resolverMismatches));
  assert.strictEqual(capabilityMismatches.length,0,JSON.stringify(capabilityMismatches));
}else throw new Error(`unknown mode ${mode}`);
console.log(JSON.stringify({mode,enabled:enabled.length,formatCounts:Object.fromEntries([...new Set(rows.map(x=>x.format))].map(f=>[f,rows.filter(x=>x.format===f).length])),resolverMismatches,capabilityMismatches,rows}));
