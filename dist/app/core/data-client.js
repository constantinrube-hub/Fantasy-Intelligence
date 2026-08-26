/* FIE centralized fetch/request layer, V9.3.1.
 * Memory cache + in-flight coalescing remain the hot path. Stable shared NFL
 * proxy payloads also use Cache Storage so a full browser refresh or league
 * switch does not force another download/parse cycle.
 */
(function(){
'use strict';
const D=()=>window.FIECore?.Diagnostics;
const memory=new Map(),inflight=new Map();
const stats={hits:0,misses:0,coalesced:0,stores:0,persistentHits:0,persistentMisses:0,persistentStores:0,persistentErrors:0};
const PERSISTENT_CACHE='fie-data-v931';
function ttlFor(url){const u=String(url||'');if(/sleeper\/players/.test(u))return 6*3600e3;if(/nflverse\/(players|contracts)/.test(u))return 12*3600e3;if(/nflverse\/(stats|snaps|weekly|schedule|depth|team)/.test(u))return 6*3600e3;if(/projection/i.test(u))return 5*60e3;if(/research|milestone|current/i.test(u))return 10*60e3;return 60e3;}
function cacheable(opts){return String(opts?.method||'GET').toUpperCase()==='GET'&&opts?.cache!=='no-store'&&opts?.dedupe!==false;}
function keyFor(kind,url){return `${kind}:${String(url)}`;}
function absolute(url){try{return new URL(String(url),window.location?.href||'https://fie.local/').href;}catch{return String(url||'');}}
function persistable(url,opts={}){if(opts.persist===false||opts.cache==='no-store'||String(opts.method||'GET').toUpperCase()!=='GET')return false;if(opts.persist===true)return true;const u=absolute(url);return /\/api\/data\/(?:nflverse\/|sleeper\/players(?:$|[/?])|sleeper\/projections\/)/i.test(u);}
function fnv(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}
function persistentRequest(kind,url){const origin=window.location?.origin||'https://fie.local',abs=absolute(url);return new Request(`${origin}/__fie_cache__/v931/${kind}/${fnv(abs)}`,{method:'GET'});}
async function persistentGet(kind,url,ttl){if(!('caches'in window)||typeof Response==='undefined'||typeof Request==='undefined')return null;const abs=absolute(url);try{const c=await caches.open(PERSISTENT_CACHE),req=persistentRequest(kind,url),hit=await c.match(req);if(!hit){stats.persistentMisses++;return null;}const stored=Number(hit.headers.get('x-fie-cache-at')||0),source=hit.headers.get('x-fie-cache-url')||'';if(source!==abs||!stored||Date.now()-stored>=ttl){stats.persistentMisses++;await c.delete(req).catch(()=>{});return null;}const value=kind==='json'?await hit.json():await hit.text();stats.persistentHits++;return{at:stored,value};}catch(e){stats.persistentErrors++;D()?.capture?.(e,{domain:'persistent-cache-read',url:abs});return null;}}
async function persistentSet(kind,url,value){if(!('caches'in window)||typeof Response==='undefined'||typeof Request==='undefined')return;const abs=absolute(url);try{const body=kind==='json'?JSON.stringify(value):String(value??''),headers={'content-type':kind==='json'?'application/json; charset=utf-8':'text/plain; charset=utf-8','x-fie-cache-at':String(Date.now()),'x-fie-cache-url':abs,'x-fie-cache-kind':kind};const c=await caches.open(PERSISTENT_CACHE);await c.put(persistentRequest(kind,url),new Response(body,{status:200,headers}));stats.persistentStores++;}catch(e){stats.persistentErrors++;D()?.capture?.(e,{domain:'persistent-cache-write',url:abs});}}

function redacted(url){return D()?.redact?.(url)||String(url||'');}
function mergeSignals(a,b){if(!a)return b;if(!b)return a;const c=new AbortController(),stop=()=>c.abort();if(a.aborted||b.aborted)c.abort();else{a.addEventListener('abort',stop,{once:true});b.addEventListener('abort',stop,{once:true});}return c.signal;}
const Client={
  version:'9.3.1-data-client',defaultTimeoutMs:12000,scopeSignal:null,
  setScope(signal){this.scopeSignal=signal||null;},

  async request(url,{signal=this.scopeSignal,timeoutMs=this.defaultTimeoutMs,cache='default',method='GET',headers={},expect='auto',sourceId=null,maxBytes=20*1024*1024}={}){const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(new DOMException('Timeout','AbortError')),timeoutMs),combined=mergeSignals(signal,ctl.signal),started=performance.now();try{const r=await fetch(url,{signal:combined,cache,method,headers});const len=Number(r.headers.get('content-length')||0);if(len&&len>maxBytes)throw new Error(`Response too large (${len} bytes)`);if(!r.ok)throw new Error(`HTTP ${r.status} ${r.statusText}`);window.FIEPerformance?.push?.(`fetch:${sourceId||new URL(String(url),location.href).pathname}`,performance.now()-started,{status:r.status});if(expect==='response')return r;const ct=String(r.headers.get('content-type')||'').toLowerCase();if(expect==='json'||(expect==='auto'&&ct.includes('json')))return r.json();if(expect==='text'||expect==='auto')return r.text();return r;}catch(e){if(e?.name!=='AbortError')D()?.capture?.(e,{domain:'fetch',sourceId,url:redacted(url)});throw e;}finally{clearTimeout(timer);}},
  async _cached(kind,url,opts={}){if(!cacheable(opts))return this.request(url,{...opts,expect:kind});const key=keyFor(kind,url),now=Date.now(),hit=memory.get(key),ttl=Number.isFinite(Number(opts.ttlMs))?Number(opts.ttlMs):ttlFor(url);if(hit&&now-hit.at<ttl){stats.hits++;return hit.value;}if(inflight.has(key)){stats.coalesced++;return inflight.get(key);}stats.misses++;const promise=(async()=>{if(persistable(url,opts)){const disk=await persistentGet(kind,url,ttl);if(disk){memory.set(key,disk);return disk.value;}}const value=await this.request(url,{...opts,expect:kind});const row={at:Date.now(),value};memory.set(key,row);stats.stores++;if(persistable(url,opts))await persistentSet(kind,url,value);return value;})().finally(()=>inflight.delete(key));inflight.set(key,promise);return promise;},
  json(url,opts={}){return this._cached('json',url,opts);},
  text(url,opts={}){return this._cached('text',url,opts);},

  response(url,opts={}){return this.request(url,{...opts,expect:'response'});},
  sanitizeUrl:redacted,
  cacheStats(){return {...stats,inflightHits:stats.coalesced,entries:memory.size,memoryEntries:memory.size,inflight:inflight.size,persistentCache:PERSISTENT_CACHE};},
  clearMemory(){memory.clear();inflight.clear();},
  async clearPersistent(){if('caches'in window)try{return await caches.delete(PERSISTENT_CACHE);}catch{return false;}return false;}
};
window.FIEDataClient=Client;
})();
