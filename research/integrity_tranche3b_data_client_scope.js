/* Tranche 3B preflight/target: scope-aware DataClient transport contract. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const code=fs.readFileSync('app/core/data-client.js','utf8');

const stores=new Map(),events=[];
const fakeCaches={
  async open(name){
    if(!stores.has(name))stores.set(name,new Map());
    const s=stores.get(name);
    return{
      async match(req){const r=s.get(req.url);return r?r.clone():undefined;},
      async put(req,res){s.set(req.url,res.clone());},
      async delete(req){return s.delete(req.url);}
    };
  },
  async delete(name){return stores.delete(name);}
};
const reply=o=>new Response(JSON.stringify(o),{status:200,headers:{'content-type':'application/json'}});
function delayed(ms,value,signal){
  return new Promise((resolve,reject)=>{
    if(signal?.aborted){const e=new Error('aborted');e.name='AbortError';return reject(e);}
    const t=setTimeout(()=>resolve(reply(value)),ms);
    signal?.addEventListener?.('abort',()=>{clearTimeout(t);const e=new Error('aborted');e.name='AbortError';reject(e);},{once:true});
  });
}
let fetchCount=0;
const fetch=async(url,opts={})=>{
  const s=String(url);
  if(s==='/scope-test'){fetchCount++;return delayed(35,{ok:true,fetch:fetchCount},opts.signal);}
  if(s.endsWith('/data/research/app/league-index.json'))return reply({schema:'fie-league-index-v1',leagues:[]});
  throw new Error(`unexpected fetch ${s}`);
};
const ctx={
  console,window:null,caches:fakeCaches,Request,Response,Headers,URL,AbortController,DOMException,
  Date,Math,Map,Set,WeakMap,Promise,setTimeout,clearTimeout,
  performance:{now:()=>Date.now()},location:{href:'https://example.test/',origin:'https://example.test'},
  fetch,navigator:{connection:{effectiveType:'4g',saveData:false}},
  document:{readyState:'loading',visibilityState:'visible',addEventListener(){}},
  CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}}
};
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=e=>{events.push(e);return true};
ctx.FIECore={Diagnostics:{capture(){}}};
vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'data-client.js'});

(async()=>{
  const c=ctx.FIEDataClient;

  // Same scope should retain useful request coalescing.
  const same=new AbortController();
  fetchCount=0;c.clearMemory();
  const sameA=c.json('/scope-test',{signal:same.signal,persist:false});
  const sameB=c.json('/scope-test',{signal:same.signal,persist:false});
  const sameVals=await Promise.all([sameA,sameB]);
  const sameScope={fetches:fetchCount,coalesced:c.cacheStats().coalesced,values:sameVals.map(x=>x.fetch)};
  if(mode==='target'){
    assert.strictEqual(sameScope.fetches,1,'same scope should still coalesce identical requests');
  }

  // Distinct scopes must not share an abortable in-flight promise.
  fetchCount=0;c.clearMemory();
  const a=new AbortController(),b=new AbortController();
  const pA=c.json('/scope-test',{signal:a.signal,persist:false});
  const pB=c.json('/scope-test',{signal:b.signal,persist:false});
  setTimeout(()=>a.abort(),5);
  const settled=await Promise.allSettled([pA,pB]);
  const crossScope={
    statuses:settled.map(x=>x.status),
    reasons:settled.map(x=>x.status==='rejected'?x.reason?.name:null),
    fetches:fetchCount,
    coalesced:c.cacheStats().coalesced
  };

  if(mode==='baseline'){
    assert.deepStrictEqual(crossScope.statuses,['rejected','rejected'],
      'baseline must reproduce cross-scope abort propagation');
    assert.strictEqual(crossScope.fetches,1,'baseline should reproduce URL-only coalescing');
    console.log('KNOWN_GAP_REPRODUCED DataClient coalesces distinct abort scopes by URL');
  }else if(mode==='target'){
    assert.deepStrictEqual(crossScope.statuses,['rejected','fulfilled'],
      'target must isolate distinct abort scopes');
    assert.strictEqual(crossScope.fetches,2,'target distinct scopes require independent in-flight requests');
    console.log('PASS Tranche 3B scope-aware DataClient coalescing contract');
  }else throw new Error(`unknown mode ${mode}`);

  console.log(JSON.stringify({mode,sameScope,crossScope}));
})().catch(e=>{console.error(e);process.exit(1);});
