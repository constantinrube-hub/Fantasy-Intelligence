/* FIE centralized fetch/request layer. */
(function(){
'use strict';
const D=()=>window.FIECore?.Diagnostics;
const memory=new Map(),inflight=new Map();
const stats={hits:0,misses:0,coalesced:0,stores:0};
function ttlFor(url){const u=String(url||'');if(/sleeper\/players/.test(u))return 6*3600e3;if(/nflverse\/(players|contracts)/.test(u))return 12*3600e3;if(/nflverse\/(stats|snaps|weekly)/.test(u))return 6*3600e3;if(/projection/i.test(u))return 5*60e3;if(/research|milestone|current/i.test(u))return 10*60e3;return 60e3;}
function cacheable(opts){return String(opts?.method||'GET').toUpperCase()==='GET'&&opts?.cache!=='no-store'&&opts?.dedupe!==false;}
function keyFor(kind,url){return `${kind}:${String(url)}`;}

function redacted(url){return D()?.redact?.(url)||String(url||'');}
function mergeSignals(a,b){if(!a)return b;if(!b)return a;const c=new AbortController(),stop=()=>c.abort();if(a.aborted||b.aborted)c.abort();else{a.addEventListener('abort',stop,{once:true});b.addEventListener('abort',stop,{once:true});}return c.signal;}
const Client={
  version:'9.3-data-client',defaultTimeoutMs:12000,scopeSignal:null,
  setScope(signal){this.scopeSignal=signal||null;},

  async request(url,{signal=this.scopeSignal,timeoutMs=this.defaultTimeoutMs,cache='default',method='GET',headers={},expect='auto',sourceId=null,maxBytes=20*1024*1024}={}){const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(new DOMException('Timeout','AbortError')),timeoutMs),combined=mergeSignals(signal,ctl.signal),started=performance.now();try{const r=await fetch(url,{signal:combined,cache,method,headers});const len=Number(r.headers.get('content-length')||0);if(len&&len>maxBytes)throw new Error(`Response too large (${len} bytes)`);if(!r.ok)throw new Error(`HTTP ${r.status} ${r.statusText}`);window.FIEPerformance?.push?.(`fetch:${sourceId||new URL(String(url),location.href).pathname}`,performance.now()-started,{status:r.status});if(expect==='response')return r;const ct=String(r.headers.get('content-type')||'').toLowerCase();if(expect==='json'||(expect==='auto'&&ct.includes('json')))return r.json();if(expect==='text'||expect==='auto')return r.text();return r;}catch(e){if(e?.name!=='AbortError')D()?.capture?.(e,{domain:'fetch',sourceId,url:redacted(url)});throw e;}finally{clearTimeout(timer);}},
  async _cached(kind,url,opts={}){if(!cacheable(opts))return this.request(url,{...opts,expect:kind});const key=keyFor(kind,url),now=Date.now(),hit=memory.get(key),ttl=Number.isFinite(Number(opts.ttlMs))?Number(opts.ttlMs):ttlFor(url);if(hit&&now-hit.at<ttl){stats.hits++;return hit.value;}if(inflight.has(key)){stats.coalesced++;return inflight.get(key);}stats.misses++;const promise=this.request(url,{...opts,expect:kind}).then(value=>{memory.set(key,{at:Date.now(),value});stats.stores++;return value;}).finally(()=>inflight.delete(key));inflight.set(key,promise);return promise;},
  json(url,opts={}){return this._cached('json',url,opts);},
  text(url,opts={}){return this._cached('text',url,opts);},

  response(url,opts={}){return this.request(url,{...opts,expect:'response'});},
  sanitizeUrl:redacted,
  cacheStats(){return {...stats,inflightHits:stats.coalesced,entries:memory.size,memoryEntries:memory.size,inflight:inflight.size};},
  clearMemory(){memory.clear();inflight.clear();}
};
window.FIEDataClient=Client;
})();
