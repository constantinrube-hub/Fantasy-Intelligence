/* Fantasy Intelligence Engine V9.3.4A2 · league-switch performance hardening.
 * Goals:
 *  - make the core league workspace interactive before expensive scoring/enrichment
 *  - keep Draft initialization lazy unless Draft is actually visible
 *  - reduce the hot-path player universe to relevant current/rostered players
 *  - launch enhancements after first paint instead of inside the critical path
 *  - expose precise timings and a canonical progressive Public Enrichment counter
 */
(function(){
'use strict';
if(window.FIE934A2?.installed)return;

const VERSION='9.3.4A2';
const RELEASE='critical-path-defer-progressive-public-status';
const INSTALL_LIMIT=120;
let installAttempts=0;
let switchWrapped=false;
let universeWrapped=false;
let draftWrapped=false;
let fetchCsvWrapped=false;
let measuredWrapped=false;
let progressObserver=null;
let progressTimer=null;
let enhancedLeagueId='';
let draftTimer=null;
let inFastSwitch=false;

const diagnostics={
  coreSwitches:0,
  coreInteractiveMs:[],
  coreAssignDeferred:0,
  coreKpisDeferred:0,
  coreRendersDeferred:0,
  draftControlsDeferred:0,
  enhancementLaunches:0,
  leanUniverseBuilds:0,
  playerMapBefore:0,
  playerMapAfter:0,
  publicSourceSettles:0,
  publicSourceFailures:0,
  lastPublic:{leagueId:'',loaded:0,failed:0,settled:0,complete:false},
  timings:{},
  longFunctions:[]
};

const st=()=>window.state||(typeof state!=='undefined'?state:null);
const now=()=>typeof performance!=='undefined'&&performance.now?performance.now():Date.now();
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function activeLeagueId(){return String(st()?.league?.league_id||st()?.activeLeagueId||window.FIELeagueController?.activeLeagueId||'');}
function activeTab(){return String(st()?.activeTab||'').toLowerCase();}
function currentGeneration(){return Number(window.FIELeagueController?.generation||0);}
function sameContext(ctx){return String(ctx?.leagueId||'')===activeLeagueId()&&Number(ctx?.generation||0)===currentGeneration();}
function pushPerf(name,ms,meta={}){const val=Math.round(ms*10)/10;(diagnostics.timings[name]??=[]).push(val);if(diagnostics.timings[name].length>30)diagnostics.timings[name].shift();if(val>250)diagnostics.longFunctions.push({name,ms:val,at:Date.now(),...meta});if(diagnostics.longFunctions.length>80)diagnostics.longFunctions.splice(0,diagnostics.longFunctions.length-80);try{window.FIEPerformance?.push?.(`934a2:${name}`,val,meta);}catch{}}
function afterPaint(){return new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));}
function idle(timeout=700){return new Promise(resolve=>{const run=()=>requestAnimationFrame(resolve);if(typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout});else setTimeout(run,Math.min(120,timeout));});}
function diag(error,meta={}){try{window.FIECore?.Diagnostics?.capture?.(error,{domain:'v9.3.4a2',...meta});}catch{}}

function timedCall(name,fn,thisArg,args,meta={}){
  const t=now();let out;
  try{out=fn.apply(thisArg,args);}catch(e){pushPerf(name,now()-t,{...meta,error:true});throw e;}
  if(out&&typeof out.then==='function')return out.finally(()=>pushPerf(name,now()-t,meta));
  pushPerf(name,now()-t,meta);return out;
}

function rosteredIds(){
  const ids=new Set();
  for(const r of st()?.rosters||[]){for(const key of ['players','starters','reserve','taxi'])for(const id of r?.[key]||[])if(id&&String(id)!=='0')ids.add(String(id));}
  return ids;
}
function wantedPositions(){
  const raw=new Set((st()?.league?.roster_positions||[]).map(x=>String(x||'').toUpperCase()));
  const out=new Set(),has=(x)=>raw.has(x);
  if(has('QB')||has('SUPER_FLEX')||has('OP'))out.add('QB');
  if(has('RB')||has('FLEX')||has('WRRB_FLEX')||has('RB_WR'))out.add('RB');
  if(has('WR')||has('FLEX')||has('WRRB_FLEX')||has('REC_FLEX')||has('RB_WR')||has('WR_TE'))out.add('WR');
  if(has('TE')||has('FLEX')||has('REC_FLEX')||has('WR_TE'))out.add('TE');
  if(has('K'))out.add('K');
  if(has('DL')||has('IDP_FLEX')){out.add('DL');out.add('DE');out.add('DT');}
  if(has('LB')||has('IDP_FLEX'))out.add('LB');
  if(has('DB')||has('IDP_FLEX')){out.add('DB');out.add('CB');out.add('S');}
  if(!out.size){for(const p of ['QB','RB','WR','TE','K'])out.add(p);}
  return out;
}
function metaPositions(meta){
  const arr=[];for(const p of meta?.fantasy_positions||[])arr.push(String(p||'').toUpperCase());if(meta?.position)arr.push(String(meta.position).toUpperCase());return arr;
}
function keepCurrentMeta(meta,wanted){
  const pos=metaPositions(meta);if(!pos.some(p=>wanted.has(p)))return false;
  const team=String(meta?.team||'').trim();const status=String(meta?.status||'').toLowerCase();const injury=String(meta?.injury_status||'').toLowerCase();const rank=finite(meta?.search_rank);
  if(status==='active'&&team)return true;
  if(team&&injury&&injury!=='healthy')return true;
  if(team&&rank!==null&&rank<=1200)return true;
  if(rank!==null&&rank<=500)return true;
  return false;
}
function leanPlayerMap(full){
  const wanted=wantedPositions(),forced=rosteredIds(),out={};
  for(const [id,meta] of Object.entries(full||{}))if(forced.has(String(id))||keepCurrentMeta(meta,wanted))out[id]=meta;
  diagnostics.playerMapBefore=Object.keys(full||{}).length;diagnostics.playerMapAfter=Object.keys(out).length;return out;
}

function installLeanUniverse(){
  if(universeWrapped)return true;const original=window.buildPlayerUniverse;if(typeof original!=='function')return false;
  window.buildPlayerUniverse=function(){
    const state=st(),full=state?.playerMap;if(!state||!full||typeof full!=='object')return timedCall('buildPlayerUniverse',original,this,arguments,{leagueId:activeLeagueId()});
    const lean=leanPlayerMap(full);state.playerMap=lean;diagnostics.leanUniverseBuilds++;const t=now();let out;
    const restore=()=>{state.playerMap=full;pushPerf('buildPlayerUniverse',now()-t,{leagueId:activeLeagueId(),before:diagnostics.playerMapBefore,after:diagnostics.playerMapAfter});};
    try{out=original.apply(this,arguments);}catch(e){restore();throw e;}
    if(out&&typeof out.then==='function')return out.finally(restore);restore();return out;
  };
  window.buildPlayerUniverse.__fie934a2Lean=true;window.buildPlayerUniverse.__original=original;universeWrapped=true;return true;
}

function isDraftVisible(){return /draft/.test(activeTab());}
function installLazyDraft(){
  if(draftWrapped)return true;const original=window.populateDraftControls;if(typeof original!=='function')return false;
  const wrapped=function(){if(!isDraftVisible()){diagnostics.draftControlsDeferred++;return null;}return timedCall('populateDraftControls',original,this,arguments,{leagueId:activeLeagueId()});};
  wrapped.__fie934a2Lazy=true;wrapped.__original=original;window.populateDraftControls=wrapped;draftWrapped=true;
  const ensure=()=>{clearTimeout(draftTimer);draftTimer=setTimeout(()=>{if(!isDraftVisible())return;try{original.call(window);}catch(e){diag(e,{feature:'lazy-draft-controls'});}},30);};
  document.addEventListener('click',e=>{const el=e.target?.closest?.('button,a,[data-tab],[data-route],[role="tab"]');if(!el)return;const sig=[el.id,el.dataset?.tab,el.dataset?.route,el.getAttribute?.('href'),el.textContent].filter(Boolean).join(' ').toLowerCase();if(sig.includes('draft'))setTimeout(ensure,0);},true);
  window.addEventListener('fie:league-loaded',e=>{if(e?.detail?.stage==='core'&&isDraftVisible())ensure();});return true;
}

function wrapMeasuredGlobal(key,name){
  const original=window[key];if(typeof original!=='function'||original.__fie934a2Measured)return;
  const wrapped=function(){return timedCall(name,original,this,arguments,{leagueId:activeLeagueId()});};wrapped.__fie934a2Measured=true;wrapped.__original=original;window[key]=wrapped;
}
function installMeasurements(){
  if(measuredWrapped)return true;
  for(const [key,name] of [['populateFilters','populateFilters'],['populateRosterPicker','populateRosterPicker'],['assignScores','assignScores'],['updateKPIs','updateKPIs'],['render','render']])wrapMeasuredGlobal(key,name);
  measuredWrapped=true;return true;
}

function publicKey(url){const s=String(url||'').toLowerCase();if(s.includes('nflverse/players'))return'players';if(s.includes('nflverse/contracts'))return'contracts';if(s.includes('nflverse/stats-regpost'))return'stats';if(s.includes('nflverse/snaps-'))return'snaps';return null;}
const publicCycle={leagueId:'',started:0,settled:new Set(),failed:new Set()};
function resetPublicCycle(id=activeLeagueId()){publicCycle.leagueId=String(id||'');publicCycle.started=Date.now();publicCycle.settled=new Set();publicCycle.failed=new Set();enhancedLeagueId='';updatePublicDiagnostic(false);repairProgressDom();}
function updatePublicDiagnostic(complete=String(enhancedLeagueId)===activeLeagueId()){
  const status=st()?.publicStatus||{},keys=['players','contracts','stats','snaps'],loaded=keys.filter(k=>status[k]===true).length,failed=publicCycle.failed.size,settled=publicCycle.settled.size;
  diagnostics.lastPublic={leagueId:activeLeagueId(),loaded,failed,settled,complete:!!complete};return diagnostics.lastPublic;
}
function progressLabel(){const p=updatePublicDiagnostic();return p.complete?`${p.loaded}/4 available · complete`:`${p.loaded}/4 available${p.failed?` · ${p.failed} unavailable`:''} · loading`;}
function repairProgressDom(){
  if(typeof document==='undefined'||!document.body)return;const summary=progressLabel(),count=`${diagnostics.lastPublic.loaded}/4`;
  const els=document.querySelectorAll('body *');
  for(const el of els){if(el.childElementCount>6)continue;const txt=String(el.textContent||'').trim();if(!/public enrichment/i.test(txt))continue;
    if(/\b[0-4]\s*\/\s*4\b/.test(txt)&&el.childElementCount===0){el.textContent=txt.replace(/\b[0-4]\s*\/\s*4\b/,count);el.title=summary;el.setAttribute('aria-label',summary);continue;}
    const leaves=el.querySelectorAll('*');let fixed=false;for(const leaf of leaves){if(leaf.childElementCount)continue;const t=String(leaf.textContent||'').trim();if(/^\s*[0-4]\s*\/\s*4\s*$/.test(t)){leaf.textContent=count;leaf.title=summary;fixed=true;}}
    if(!fixed){let badge=el.querySelector('[data-fie934a2-public]');if(!badge){badge=document.createElement('span');badge.dataset.fie934a2Public='1';badge.style.marginLeft='6px';badge.style.opacity='.78';el.appendChild(badge);}badge.textContent=count;badge.title=summary;}
  }
}
function installProgressObserver(){
  // Progress is repaired only at meaningful state transitions (source settle,
  // league change, first paint, enhanced publish). A body-wide MutationObserver
  // would itself add avoidable work during large table renders.
  return true;
}

function installFetchCsvProgress(){
  if(fetchCsvWrapped)return true;const original=window.fetchCSV;if(typeof original!=='function')return false;
  window.fetchCSV=async function(url){const key=publicKey(url);if(!key)return original.apply(this,arguments);const ctx={leagueId:activeLeagueId(),generation:currentGeneration()};if(publicCycle.leagueId!==ctx.leagueId)resetPublicCycle(ctx.leagueId);try{const result=await original.apply(this,arguments);if(sameContext(ctx)){const state=st();state.publicStatus=state.publicStatus||{};state.publicStatus[key]=true;publicCycle.settled.add(key);publicCycle.failed.delete(key);diagnostics.publicSourceSettles++;repairProgressDom();}return result;}catch(e){if(sameContext(ctx)){const state=st();state.publicStatus=state.publicStatus||{};state.publicStatus[key]=false;publicCycle.settled.add(key);publicCycle.failed.add(key);diagnostics.publicSourceFailures++;repairProgressDom();}throw e;}};
  window.fetchCSV.__fie934a2Progress=true;window.fetchCSV.__original=original;fetchCsvWrapped=true;return true;
}

function installFastSwitch(){
  if(switchWrapped)return true;const ctl=window.FIELeagueController;if(!ctl||typeof ctl.switchLeague!=='function'||typeof ctl.loadEnhancements!=='function')return false;
  const originalSwitch=ctl.switchLeague,realEnhancements=ctl.loadEnhancements;
  ctl.switchLeague=async function(){
    if(inFastSwitch)return originalSwitch.apply(this,arguments);inFastSwitch=true;diagnostics.coreSwitches++;const started=now();const args=arguments,requestedRoute=String(args?.[1]?.route||activeTab()).toLowerCase();let pendingScope=null,result=null;
    const savedLoad=this.loadEnhancements,savedAssign=window.assignScores,savedKpis=window.updateKPIs,savedRender=window.render,savedDraft=window.populateDraftControls;
    this.loadEnhancements=function(scope){pendingScope=scope;return Promise.resolve(null);};
    if(typeof savedAssign==='function')window.assignScores=function(){diagnostics.coreAssignDeferred++;return null;};
    if(typeof savedKpis==='function')window.updateKPIs=function(){diagnostics.coreKpisDeferred++;return null;};
    if(typeof savedRender==='function')window.render=function(){diagnostics.coreRendersDeferred++;return null;};
    if(typeof savedDraft==='function'&&!requestedRoute.includes('draft'))window.populateDraftControls=function(){diagnostics.draftControlsDeferred++;return null;};
    try{result=await originalSwitch.apply(this,args);}finally{this.loadEnhancements=savedLoad;window.assignScores=savedAssign;window.updateKPIs=savedKpis;window.render=savedRender;window.populateDraftControls=savedDraft;inFastSwitch=false;}
    if(!result)return result;
    const ctx={leagueId:activeLeagueId(),generation:currentGeneration()};resetPublicCycle(ctx.leagueId);
    await afterPaint();if(!sameContext(ctx))return result;
    try{savedRender?.();}catch(e){diag(e,{feature:'first-interactive-render',leagueId:ctx.leagueId});}
    const interactive=now()-started;diagnostics.coreInteractiveMs.push(Math.round(interactive*10)/10);if(diagnostics.coreInteractiveMs.length>30)diagnostics.coreInteractiveMs.shift();pushPerf('core-interactive',interactive,{leagueId:ctx.leagueId});
    const status=document.getElementById('status');if(status)status.textContent=`Loaded ${st()?.league?.name||ctx.leagueId}. Core workspace ready; rankings and enrichment are updating in the background.`;
    window.dispatchEvent(new CustomEvent('fie:core-interactive',{detail:{leagueId:ctx.leagueId,generation:ctx.generation,ms:Math.round(interactive)}}));
    if(pendingScope){
      const self=this;setTimeout(async()=>{await idle(900);if(!sameContext(ctx)||!pendingScope?.isCurrent?.())return;diagnostics.enhancementLaunches++;try{self.background=realEnhancements.call(self,pendingScope);await self.background;}catch(e){if(e?.name!=='AbortError')diag(e,{feature:'deferred-enhancements',leagueId:ctx.leagueId});}},0);
    }
    return result;
  };
  ctl.switchLeague.__fie934a2Fast=true;ctl.switchLeague.__original=originalSwitch;ctl.__fie934a2RealEnhancements=realEnhancements;switchWrapped=true;return true;
}

window.addEventListener('fie:league-changing',e=>resetPublicCycle(String(e?.detail?.leagueId||'')));
window.addEventListener('fie:league-loaded',e=>{const id=String(e?.detail?.leagueId||'');if(e?.detail?.stage==='enhanced'&&id===activeLeagueId()){enhancedLeagueId=id;updatePublicDiagnostic(true);repairProgressDom();}});

function report(){
  const perf=window.FIEPerformance?.snapshot?.()||null;return{version:VERSION,release:RELEASE,leagueId:activeLeagueId(),generation:currentGeneration(),diagnostics,performance:perf};
}
function install(){
  installAttempts++;const baseReady=!!window.FIE934AB?.installed;
  if(baseReady){installLeanUniverse();installLazyDraft();installMeasurements();installFetchCsvProgress();installFastSwitch();installProgressObserver();repairProgressDom();}
  const complete=baseReady&&universeWrapped&&draftWrapped&&fetchCsvWrapped&&switchWrapped;
  if(!complete&&installAttempts<INSTALL_LIMIT)setTimeout(install,100);else if(!complete)console.warn('FIE V9.3.4A2 installed partially; inspect FIE934A2.report().');
}

window.FIE934A2={installed:true,VERSION,RELEASE,diagnostics,report,repairProgressDom,leanPlayerMap};
install();
})();
