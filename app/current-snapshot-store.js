/* FIE 9.3.4C-E · shared current-snapshot storage hydrator.
 * V9.3.3A fixes missing projection semantics: absent overlays remain null,
 * never synthetic zeroes. V9.3.3C also rejects degenerate shared D/ST/K
 * uncertainty templates so they cannot be presented as empirical P10/P90.
 */
(function(){
'use strict';
const VERSION='9.3.4C-E';
const FORMAT='fie-current-split-v1';
const cache=new Map();
function q(path,force){return `${path}${force?`${String(path).includes('?')?'&':'?'}t=${Date.now()}`:''}`;}
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
async function getJSON(path,{force=false,fetchResponse=null,sourceId='research-artifact'}={}){
  const key=String(path);if(!force&&cache.has(key))return cache.get(key);
  const loader=async()=>{const url=q(key,force),opts={cache:force?'no-store':'default',sourceId};const r=fetchResponse?await fetchResponse(url,opts):window.FIEDataClient?.response?await window.FIEDataClient.response(url,opts):await fetch(url,{cache:opts.cache});if(!r.ok)throw new Error(`HTTP ${r.status} loading ${key}`);return r.json();};
  const p=loader();cache.set(key,p);
  try{return await p;}catch(e){cache.delete(key);throw e;}
}
function pid(row){const canonical=window.FIECore?.PlayerIdentity?.governedId?.(row);if(canonical)return String(canonical);if(row?.sleeper_id!=null&&String(row.sleeper_id))return String(row.sleeper_id);if(row?.canonical_player_id!=null&&String(row.canonical_player_id))return `canonical:${row.canonical_player_id}`;return '';}
function positionModel(row){return String(row?.position_model||row?.position||'').toUpperCase().replace('DST','DEF');}
function sanitizeUncertainty(players){
  for(const pos of ['DEF','K']){
    const rows=(players||[]).filter(r=>positionModel(r)===pos);
    const usable=rows.filter(r=>finite(r?.p10)!==null&&finite(r?.p90)!==null&&finite(r.p90)>=finite(r.p10));
    if(usable.length<6)continue;
    const counts=new Map();
    for(const r of usable){const sig=`${finite(r.p10)}|${finite(r.p90)}`;counts.set(sig,(counts.get(sig)||0)+1);}
    const threshold=Math.max(6,Math.ceil(usable.length*.35));
    const suspicious=new Set([...counts].filter(([,n])=>n>=threshold).map(([sig])=>sig));
    if(!suspicious.size)continue;
    for(const r of rows){const lo=finite(r?.p10),hi=finite(r?.p90);if(lo===null||hi===null)continue;const sig=`${lo}|${hi}`;if(!suspicious.has(sig))continue;r.p10=null;r.p90=null;r.uncertainty_sanitized=true;r.uncertainty_reason='degenerate shared interval rejected by V9.3.3C';}
  }
  return players;
}
async function load(path,{force=false,fetchResponse=null,sourceId='research-artifact'}={}){
  const raw=await getJSON(path,{force,fetchResponse,sourceId});const st=raw?.storage||{};
  if(st.format!==FORMAT)return raw;
  if(!st.player_base||!st.scoring_overlay)throw new Error('Split current snapshot is missing shared references');
  const [base,overlay]=await Promise.all([
    getJSON(st.player_base,{force,fetchResponse,sourceId}),
    getJSON(st.scoring_overlay,{force,fetchResponse,sourceId})
  ]);
  if(String(overlay?.scoring_signature||'')!==String(raw?.scoring_signature||''))throw new Error('Current scoring overlay mismatch');
  const include=Array.isArray(st.included_player_ids)?st.included_player_ids.map(String):null;
  const exclude=new Set((st.excluded_player_ids||[]).map(String));const proj=overlay?.projections||{};const players=[];
  const baseRows=base?.players||[],baseMap=include?new Map(baseRows.map(b=>[pid(b),b])):null,ordered=include?include.map(id=>[id,baseMap.get(id)]):baseRows.map(b=>[pid(b),b]);
  for(const [id,b] of ordered){
    if(!id||!b||exclude.has(id))continue;
    const pair=Array.isArray(proj[id])?proj[id]:null;
    const decision=pair&&pair.length>0?finite(pair[0]):null;
    const sleeper=pair&&pair.length>1?finite(pair[1]):null;
    players.push({...b,decision_weekly_projection:decision,sleeper_weekly_projection:sleeper});
  }
  sanitizeUncertainty(players);
  const expected=Number(st.player_count);if(Number.isFinite(expected)&&expected!==players.length)throw new Error(`Current snapshot hydration mismatch: expected ${expected}, got ${players.length}`);
  const out={...raw,scoring_settings:overlay?.scoring_settings||{},players};delete out.storage;
  Object.defineProperty(out,'__storage',{value:st,enumerable:false});return out;
}
function clear(){cache.clear();}
window.FIECurrentSnapshotStore={VERSION,FORMAT,load,clear,sanitizeUncertainty};

/* Keep the stable V9.3.4A-B -> A2 -> A3 performance baseline, then
 * layer the roadmap modules C, D and E in order. No generated application
 * shell edit is required. */
function bootE(){
  if(document.querySelector('script[data-fie934e-runtime]'))return;
  const e=document.createElement('script');e.src='app/v9.3.4e-return-scoring.js?v=9.3.4E';e.async=false;e.dataset.fie934eRuntime='1';
  e.onerror=()=>console.error('FIE V9.3.4E return scoring module failed to load');
  (document.head||document.documentElement).appendChild(e);
}
function bootD(){
  const existing=document.querySelector('script[data-fie934d-runtime]');
  if(existing){if(window.FIE934D?.installed)bootE();else existing.addEventListener('load',bootE,{once:true});return;}
  const d=document.createElement('script');d.src='app/v9.3.4d-starter-economics.js?v=9.3.4D';d.async=false;d.dataset.fie934dRuntime='1';
  d.onload=bootE;d.onerror=()=>console.error('FIE V9.3.4D starter economics module failed to load');
  (document.head||document.documentElement).appendChild(d);
}
function bootC(){
  const existing=document.querySelector('script[data-fie934c-runtime]');
  if(existing){if(window.FIE934C?.installed)bootD();else existing.addEventListener('load',bootD,{once:true});return;}
  const c=document.createElement('script');c.src='app/v9.3.4c-weekly-context.js?v=9.3.4C';c.async=false;c.dataset.fie934cRuntime='1';
  c.onload=bootD;c.onerror=()=>console.error('FIE V9.3.4C weekly context module failed to load');
  (document.head||document.documentElement).appendChild(c);
}
function bootA3(){
  const existing=document.querySelector('script[data-fie934a3-runtime]');
  if(existing){if(window.FIE934A3?.installed)bootC();else existing.addEventListener('load',bootC,{once:true});return;}
  const b=document.createElement('script');b.src='app/v9.3.4a3-score-performance.js?v=9.3.4A3';b.async=false;b.dataset.fie934a3Runtime='1';
  b.onload=bootC;b.onerror=()=>console.error('FIE V9.3.4A3 scoring hotfix failed to load');
  (document.head||document.documentElement).appendChild(b);
}
function bootA2(){
  const existing=document.querySelector('script[data-fie934a2-runtime]');
  if(existing){if(window.FIE934A2?.installed)bootA3();else existing.addEventListener('load',bootA3,{once:true});return;}
  const a=document.createElement('script');a.src='app/v9.3.4a2-performance-hotfix.js?v=9.3.4A2';a.async=false;a.dataset.fie934a2Runtime='1';
  a.onload=bootA3;a.onerror=()=>console.error('FIE V9.3.4A2 performance hotfix failed to load');
  (document.head||document.documentElement).appendChild(a);
}
function boot934(){
  const existing=document.querySelector('script[data-fie933-runtime]');
  if(existing){if(window.FIE934AB?.installed)bootA2();else existing.addEventListener('load',bootA2,{once:true});return;}
  const s=document.createElement('script');s.src='app/v9.3.3-runtime-integrity.js?v=9.3.4';s.async=false;s.dataset.fie933Runtime='1';
  s.onload=bootA2;s.onerror=()=>console.error('FIE V9.3.4 runtime integrity module failed to load');
  (document.head||document.documentElement).appendChild(s);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot934,{once:true});else setTimeout(boot934,0);
})();
