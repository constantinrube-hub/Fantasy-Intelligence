const fs=require('fs'),vm=require('vm'),assert=require('assert');
const contracts=fs.readFileSync('app/generated/runtime-contracts.js','utf8'),core=fs.readFileSync('app/core/core-services.js','utf8'),client=fs.readFileSync('app/core/data-client.js','utf8'),code=fs.readFileSync('app/runtime-foundation.js','utf8');

class FakeResponse{
  constructor(data){this.data=data;this.ok=true;this.status=200;this.statusText='OK';this.headers={get:(k)=>String(k).toLowerCase()==='content-type'?'application/json':'0'};}
  async json(){return this.data;} async text(){return JSON.stringify(this.data);}
  clone(){return new FakeResponse(this.data);}
}
function delayResponse(ms,data,signal){
  return new Promise((resolve,reject)=>{
    if(signal?.aborted){const e=new Error('aborted');e.name='AbortError';reject(e);return;}
    const t=setTimeout(()=>resolve(new FakeResponse(data)),ms);
    signal?.addEventListener?.('abort',()=>{clearTimeout(t);const e=new Error('aborted');e.name='AbortError';reject(e);},{once:true});
  });
}
const listeners={};
const elements={
  leagueInput:{value:''},savedLeagueSelect:{value:''},savedLeagueFormat:{value:'AUTO'},loadBtn:{disabled:false,textContent:'Load league'},status:{textContent:''},availFilter:{value:''}
};
const state={savedLeagues:[],leagueRules:{},activeTab:'home',publicStatus:{},projectionStatus:{}};
const fakeFetch=(url,opts={})=>{
  const s=String(url),sig=opts.signal;
  if(s==='/api/data/sleeper/players')return delayResponse(1,{'p1':{player_id:'p1',position:'QB',team:'X'}},sig);
  const m=s.match(/\/league\/(\d+)(?:\/(rosters|users))?$/);
  if(m){const id=m[1],kind=m[2],ms=id==='111111'?40:2;
    if(kind==='rosters')return delayResponse(ms,[{roster_id:1,players:[]}],sig);
    if(kind==='users')return delayResponse(ms,[{user_id:'u'}],sig);
    return delayResponse(ms,{league_id:id,name:`League ${id}`,season:'2026',settings:{type:id==='111111'?0:3},roster_positions:['QB','RB','WR','TE','FLEX','BN'],scoring_settings:{pass_td:4,rec:1}},sig);
  }
  if(s.includes('/players/nfl/trending/'))return delayResponse(1,[],sig);
  throw new Error(`Unexpected fetch ${s}`);
};
const ctx={
  console,window:null,state,PLAYERS:[],fetch:fakeFetch,AbortController,performance:{now:()=>Date.now()},PerformanceObserver:undefined,DOMException,
  localStorage:{setItem(){},getItem(){return null;}},CustomEvent:class{constructor(type,o){this.type=type;this.detail=o?.detail;}},
  document:{readyState:'complete',getElementById:id=>elements[id]||null,querySelector:()=>null},
  setTimeout,clearTimeout,Promise,Date,Number,String,Math,Object,Array,Set,Map,JSON
};
ctx.window=ctx;ctx.location={href:'https://example.test/'};ctx.addEventListener=(t,f)=>(listeners[t]??=[]).push(f);ctx.dispatchEvent=e=>{for(const f of listeners[e.type]||[])f(e);};
ctx.defaultLeagueRules=()=>({format:'AUTO'});ctx.loadLeagueRulesFor=()=>{};ctx.buildPlayerUniverse=()=>{};ctx.populateFilters=()=>{};ctx.populateRosterPicker=()=>{};ctx.populateDraftControls=()=>{};ctx.assignScores=()=>{};ctx.updateKPIs=()=>{};ctx.renderSavedLeagueControlsV71=()=>{};ctx.render=()=>{};
vm.createContext(ctx);vm.runInContext(contracts,ctx,{filename:'runtime-contracts.js'});vm.runInContext(core,ctx,{filename:'core-services.js'});vm.runInContext(client,ctx,{filename:'data-client.js'});vm.runInContext(code,ctx,{filename:'runtime-foundation.js'});

(async()=>{
  const a=ctx.FIELeagueController.switchLeague('111111');
  await new Promise(r=>setTimeout(r,5));
  const b=ctx.FIELeagueController.switchLeague('222222');
  const [ra,rb]=await Promise.all([a,b]);
  assert.strictEqual(ra,null,'aborted first load must not commit');
  assert.strictEqual(rb.league_id,'222222');
  assert.strictEqual(state.league.league_id,'222222','late A response must not overwrite B');
  assert.strictEqual(ctx.FIELeagueController.activeLeagueId,'222222');
  assert.strictEqual(state.leagueRules.detectedFormat,'CHOPPED','second league must retain its structural format');
  assert.ok(ctx.FIELeagueController.generation>=2);
  console.log('PASS integrity_league_switch_runtime_test');
})().catch(e=>{console.error(e);process.exit(1);});
