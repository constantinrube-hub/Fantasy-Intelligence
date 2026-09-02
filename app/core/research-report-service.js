/* FIE unified per-league research report service.
 * Lazy, league-namespaced context only. Never computes or overrides a rank.
 */
(function(){
'use strict';
const VERSION='1.1-data-client-transport';
let cache={leagueId:null,core:null,docs:new Map()};
function leagueId(){return String(window.FIELeagueContext?.current?.()?.leagueId||window.state?.league?.league_id||'').trim();}
function reset(){cache={leagueId:null,core:null,docs:new Map()};}
function ensureLeague(id){const now=leagueId();if(!id||!now||String(id)!==String(now))throw new Error(`FIE research league boundary mismatch: expected ${now||'none'}, got ${id||'none'}`);}
async function jsonFetch(path){const client=window.FIEDataClient;if(!client?.json)throw new Error('FIEDataClient unavailable for research report transport');return client.json(path,{cache:'no-store',persist:false,sourceId:'research-report'});}
async function core(){const id=leagueId();if(!id)throw new Error('No active league');if(cache.leagueId!==id)reset();cache.leagueId=id;if(!cache.core){cache.core=jsonFetch(`data/research/leagues/${encodeURIComponent(id)}/app/core.json`).then(x=>{ensureLeague(x?.league_id);return x;});}return cache.core;}
function validatePath(id,path){const p=String(path||'');if(!p.includes(`/leagues/${id}/performance/`)||!p.includes('/research_pipeline/'))throw new Error(`Cross-league/invalid FIE research path: ${p}`);return p;}
async function doc(key){const id=leagueId();const c=await core();const path=validatePath(id,c?.research?.[key]);const ck=`${id}:${key}:${path}`;if(!cache.docs.has(ck))cache.docs.set(ck,jsonFetch(path).then(x=>{const payloadId=String(x?.league_id||x?.league?.id||'');if(payloadId)ensureLeague(payloadId);return x;}));return cache.docs.get(ck);}
async function readiness(){return doc('readiness');}
async function rankings(){return doc('rankings');}
async function reportSummary(){return doc('report_summary');}
async function positionModel(position){const r=await readiness();return r?.positions?.[String(position||'').toUpperCase()]||null;}
async function top(position){const r=await reportSummary();return r?.top?.[String(position||'').toUpperCase()]||[];}
async function top100Outliers(){const r=await reportSummary();return r?.outliers_top100||{positive:[],negative:[]};}
async function sleepers(position){const r=await reportSummary();return r?.sleepers_gt100?.[String(position||'').toUpperCase()]||[];}
window.addEventListener?.('fie:league-changing',reset);
window.addEventListener?.('fie:league-loaded',e=>{if(!e?.detail?.stage||e.detail.stage==='core')reset();});
window.FIEResearchReportService={VERSION,readiness,rankings,reportSummary,positionModel,top,top100Outliers,sleepers,invalidate:reset};
})();
