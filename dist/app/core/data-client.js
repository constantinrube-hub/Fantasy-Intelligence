/* FIE centralized fetch/request layer. */
(function(){
'use strict';
const D=()=>window.FIECore?.Diagnostics;
function redacted(url){return D()?.redact?.(url)||String(url||'');}
function mergeSignals(a,b){if(!a)return b;if(!b)return a;const c=new AbortController(),stop=()=>c.abort();if(a.aborted||b.aborted)c.abort();else{a.addEventListener('abort',stop,{once:true});b.addEventListener('abort',stop,{once:true});}return c.signal;}
const Client={
  version:'9.1-data-client',defaultTimeoutMs:12000,scopeSignal:null,
  setScope(signal){this.scopeSignal=signal||null;},

  async request(url,{signal=this.scopeSignal,timeoutMs=this.defaultTimeoutMs,cache='default',method='GET',headers={},expect='auto',sourceId=null,maxBytes=20*1024*1024}={}){const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(new DOMException('Timeout','AbortError')),timeoutMs),combined=mergeSignals(signal,ctl.signal),started=performance.now();try{const r=await fetch(url,{signal:combined,cache,method,headers});const len=Number(r.headers.get('content-length')||0);if(len&&len>maxBytes)throw new Error(`Response too large (${len} bytes)`);if(!r.ok)throw new Error(`HTTP ${r.status} ${r.statusText}`);window.FIEPerformance?.push?.(`fetch:${sourceId||new URL(String(url),location.href).pathname}`,performance.now()-started,{status:r.status});if(expect==='response')return r;const ct=String(r.headers.get('content-type')||'').toLowerCase();if(expect==='json'||(expect==='auto'&&ct.includes('json')))return r.json();if(expect==='text'||expect==='auto')return r.text();return r;}catch(e){if(e?.name!=='AbortError')D()?.capture?.(e,{domain:'fetch',sourceId,url:redacted(url)});throw e;}finally{clearTimeout(timer);}},
  json(url,opts={}){return this.request(url,{...opts,expect:'json'});},
  text(url,opts={}){return this.request(url,{...opts,expect:'text'});},
  response(url,opts={}){return this.request(url,{...opts,expect:'response'});},
  sanitizeUrl:redacted
};
window.FIEDataClient=Client;
})();
