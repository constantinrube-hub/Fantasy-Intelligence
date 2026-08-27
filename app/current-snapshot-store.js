/* FIE 9.3.3A-C · shared current-snapshot storage hydrator.
 * V9.3.3A fixes missing projection semantics: absent overlays remain null,
 * never synthetic zeroes. V9.3.3C also rejects degenerate shared D/ST/K
 * uncertainty templates so they cannot be presented as empirical P10/P90.
 */
(function(){
'use strict';
const VERSION='9.3.3A-C';
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
function pid(row){if(row?.sleeper_id!=null&&String(row.sleeper_id))return String(row.sleeper_id);if(row?.canonical_player_id!=null&&String(row.canonical_player_id))return `canonical:${row.canonical_player_id}`;return '';}
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

/* Load the V9.3.3A-C compatibility/runtime patch without editing the very large
 * generated application shell. Static scripts have completed by DOMContentLoaded,
 * so this module can safely wrap final renderers and services afterwards. */
function boot933(){
  if(document.querySelector('script[data-fie933-runtime]'))return;
  const s=document.createElement('script');s.src='app/v9.3.3-runtime-integrity.js?v=9.3.3';s.async=false;s.dataset.fie933Runtime='1';
  s.onerror=()=>console.error('FIE V9.3.3 runtime integrity module failed to load');
  (document.head||document.documentElement).appendChild(s);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot933,{once:true});else setTimeout(boot933,0);
})();
