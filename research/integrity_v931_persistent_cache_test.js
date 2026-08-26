/* V9.3.1 persistent shared-data cache integrity. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('app/core/data-client.js','utf8');
let fetches=0;
const stores=new Map();
const fakeCaches={
  async open(name){if(!stores.has(name))stores.set(name,new Map());const store=stores.get(name);return{
    async match(req){const r=store.get(req.url);return r?r.clone():undefined;},
    async put(req,res){store.set(req.url,res.clone());},
    async delete(req){return store.delete(req.url);}
  };},
  async delete(name){return stores.delete(name);}
};
const ctx={console,window:null,caches:fakeCaches,Request,Response,Headers,URL,AbortController,DOMException,Date,Math,Map,Set,Promise,setTimeout,clearTimeout,performance:{now:()=>Date.now()},location:{href:'https://example.test/',origin:'https://example.test'},fetch:async(url)=>{fetches++;return new Response(JSON.stringify({fetches,url:String(url)}),{status:200,headers:{'content-type':'application/json'}});}};
ctx.window=ctx;ctx.FIECore={Diagnostics:{capture(){}}};vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'data-client.js'});
(async()=>{
  const c=ctx.FIEDataClient;
  const first=await c.json('/api/data/nflverse/players',{ttlMs:60000});
  assert.strictEqual(fetches,1,'first stable shared-data request should hit network');
  c.clearMemory();
  const second=await c.json('/api/data/nflverse/players',{ttlMs:60000});
  assert.strictEqual(fetches,1,'second request after memory clear must come from persistent Cache Storage');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(second)),JSON.parse(JSON.stringify(first)));
  assert.ok(c.cacheStats().persistentHits>=1,'persistent hit must be observable in diagnostics');
  await c.json('https://api.sleeper.app/v1/league/123456',{ttlMs:60000});
  c.clearMemory();
  await c.json('https://api.sleeper.app/v1/league/123456',{ttlMs:60000});
  assert.strictEqual(fetches,3,'dynamic league endpoint should not be persisted by default');
  console.log('PASS V9.3.1 persistent cache: stable proxy data survives memory reset; dynamic league state stays network-fresh');
})().catch(e=>{console.error(e);process.exit(1);});
