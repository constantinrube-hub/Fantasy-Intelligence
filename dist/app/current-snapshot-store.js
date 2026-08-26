/* FIE 9.2.1 · shared current-snapshot storage hydrator.
   Keeps the logical milestone5_current contract stable while allowing source
   and dist artifacts to deduplicate invariant player data across leagues. */
(function(){
'use strict';
const FORMAT='fie-current-split-v1';
const cache=new Map();
function q(path,force){return `${path}${force?`${String(path).includes('?')?'&':'?'}t=${Date.now()}`:''}`;}
async function getJSON(path,{force=false,fetchResponse=null,sourceId='research-artifact'}={}){
  const key=String(path);if(!force&&cache.has(key))return cache.get(key);
  const loader=async()=>{const url=q(key,force),opts={cache:force?'no-store':'default',sourceId};const r=fetchResponse?await fetchResponse(url,opts):window.FIEDataClient?.response?await window.FIEDataClient.response(url,opts):await fetch(url,{cache:opts.cache});if(!r.ok)throw new Error(`HTTP ${r.status} loading ${key}`);return r.json();};
  const p=loader();cache.set(key,p);
  try{return await p;}catch(e){cache.delete(key);throw e;}
}
function pid(row){if(row?.sleeper_id!=null&&String(row.sleeper_id))return String(row.sleeper_id);if(row?.canonical_player_id!=null&&String(row.canonical_player_id))return `canonical:${row.canonical_player_id}`;return '';}
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
  for(const [id,b] of ordered){if(!id||!b||exclude.has(id))continue;const pair=Array.isArray(proj[id])?proj[id]:[0,0];players.push({...b,decision_weekly_projection:pair.length>0?pair[0]:0,sleeper_weekly_projection:pair.length>1?pair[1]:0});}
  const expected=Number(st.player_count);if(Number.isFinite(expected)&&expected!==players.length)throw new Error(`Current snapshot hydration mismatch: expected ${expected}, got ${players.length}`);
  const out={...raw,scoring_settings:overlay?.scoring_settings||{},players};delete out.storage;
  Object.defineProperty(out,'__storage',{value:st,enumerable:false});return out;
}
function clear(){cache.clear();}
window.FIECurrentSnapshotStore={FORMAT,load,clear};
})();
