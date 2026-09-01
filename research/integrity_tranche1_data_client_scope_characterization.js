/* Tranche 1: DataClient scope/inflight and delayed live-overlay characterization. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const code=fs.readFileSync('app/core/data-client.js','utf8');
const stores=new Map(),events=[];
const fakeCaches={async open(name){if(!stores.has(name))stores.set(name,new Map());const s=stores.get(name);return{async match(req){const r=s.get(req.url);return r?r.clone():undefined;},async put(req,res){s.set(req.url,res.clone());},async delete(req){return s.delete(req.url);}};},async delete(name){return stores.delete(name);}};
const reply=o=>new Response(JSON.stringify(o),{status:200,headers:{'content-type':'application/json'}});
function delayed(ms,value,signal){
  return new Promise((resolve,reject)=>{
    if(signal?.aborted){const e=new Error('aborted');e.name='AbortError';return reject(e);}
    const t=setTimeout(()=>resolve(reply(value)),ms);
    signal?.addEventListener?.('abort',()=>{clearTimeout(t);const e=new Error('aborted');e.name='AbortError';reject(e);},{once:true});
  });
}
let scopeFetches=0;
const A='111111111111',B='222222222222';
const fetch=async(url,opts={})=>{
  const s=String(url),sig=opts.signal;
  if(s.endsWith('/data/research/app/league-index.json'))return reply({schema:'fie-league-index-v1',leagues:[{league_id:A,priority:'HIGH'},{league_id:B,priority:'HIGH'}]});
  for(const id of [A,B])if(s.includes(`/data/research/leagues/${id}/app/core.json`))return reply({schema:'fie-league-core-v1',league_id:id,sleeper:{league:{league_id:id,name:`Snapshot-${id}`},rosters:[{roster_id:1,players:['old']}],users:[{user_id:'u'}]}});
  if(s==='/scope-test'){scopeFetches++;return delayed(40,{ok:true,fetch:scopeFetches},sig);}
  if(s===`https://api.sleeper.app/v1/league/${A}`)return delayed(50,{league_id:A,name:'Live-A'},sig);
  if(s===`https://api.sleeper.app/v1/league/${B}`)return delayed(5,{league_id:B,name:'Live-B'},sig);
  if(/\/rosters$/.test(s))return delayed(5,[{roster_id:1,players:['live']}],sig);
  if(/\/users$/.test(s))return delayed(5,[{user_id:'u',display_name:'live'}],sig);
  throw new Error(`unexpected fetch ${s}`);
};
const ctx={console,window:null,caches:fakeCaches,Request,Response,Headers,URL,AbortController,DOMException,Date,Math,Map,Set,Promise,setTimeout,clearTimeout,performance:{now:()=>Date.now()},location:{href:'https://example.test/',origin:'https://example.test'},fetch,navigator:{connection:{effectiveType:'4g',saveData:false}},document:{readyState:'loading',visibilityState:'visible',addEventListener(){}},CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}}};
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=e=>{events.push(e);return true};ctx.FIECore={Diagnostics:{capture(){}}};
vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'data-client.js'});

(async()=>{
  const c=ctx.FIEDataClient;
  // Known gap: same URL request is coalesced without scope identity.
  const ctlA=new AbortController(),ctlB=new AbortController();
  const pA=c.json('/scope-test',{signal:ctlA.signal,persist:false});
  const pB=c.json('/scope-test',{signal:ctlB.signal,persist:false});
  setTimeout(()=>ctlA.abort(),5);
  const settled=await Promise.allSettled([pA,pB]);
  const scopeResult={statuses:settled.map(x=>x.status),reasons:settled.map(x=>x.status==='rejected'?x.reason?.name:null),scopeFetches,coalesced:c.cacheStats().coalesced};
  if(mode==='baseline'){
    assert.deepStrictEqual(scopeResult.statuses,['rejected','rejected'],'baseline must reproduce shared aborted in-flight promise');
    assert.ok(scopeResult.coalesced>=1,'baseline must show URL-only coalescing');
  }else if(mode==='target'){
    assert.strictEqual(scopeResult.statuses[1],'fulfilled','target second scope must not inherit first scope abort');
  }else throw new Error(`unknown mode ${mode}`);

  // Positive race guard: delayed snapshot live overlay for A must not mutate after A scope abort; B may update.
  c.clearMemory();await c.prefetchLeagueSnapshots();
  const oa=new AbortController(),ob=new AbortController();
  const a=await c.json(`https://api.sleeper.app/v1/league/${A}`,{signal:oa.signal});
  assert.strictEqual(a.name,`Snapshot-${A}`);
  oa.abort();
  const b=await c.json(`https://api.sleeper.app/v1/league/${B}`,{signal:ob.signal});
  assert.strictEqual(b.name,`Snapshot-${B}`);
  await new Promise(r=>setTimeout(r,80));
  assert.strictEqual(a.name,`Snapshot-${A}`,'aborted A live overlay must not mutate snapshot after switch');
  assert.strictEqual(b.name,'Live-B','active B live overlay should update');
  const bEvents=events.filter(e=>e.type==='fie:league-live-update'&&e.detail?.leagueId===B);
  const lateAEvents=events.filter(e=>e.type==='fie:league-live-update'&&e.detail?.leagueId===A&&e.detail?.value?.name==='Live-A');
  assert.ok(bEvents.length>=1,'B live update event missing');
  assert.strictEqual(lateAEvents.length,0,'aborted A emitted a late live update');
  console.log(mode==='baseline'?'KNOWN_GAP_REPRODUCED URL-only in-flight coalescing is scope-unsafe; live-overlay abort guard itself passes':'PASS target scope-safe DataClient');
  console.log(JSON.stringify({mode,scopeResult,liveOverlay:{a:a.name,b:b.name,bEvents:bEvents.length,lateAEvents:lateAEvents.length}}));
})().catch(e=>{console.error(e);process.exit(1);});
