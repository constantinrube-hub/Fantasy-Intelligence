/* Fantasy Intelligence Engine decision simulation layer.
 * Kept separate from index.html intentionally: this is the first production
 * step toward a modular frontend without rewriting the stable legacy runtime.
 */
(function(){
'use strict';

const Engine={version:'0.3.0',draftCache:new Map(),lastDraftRun:null,leagueSim:{loading:false,error:null,data:null,leagueId:null,week:null}};

function finite(x){const v=Number(x);return Number.isFinite(v)?v:null;}
function clampV(x,a,b){return Math.max(a,Math.min(b,x));}
function qtile(xs,q){const a=xs.filter(Number.isFinite).sort((x,y)=>x-y);if(!a.length)return null;const z=(a.length-1)*q,l=Math.floor(z),h=Math.ceil(z);return l===h?a[l]:a[l]*(h-z)+a[h]*(z-l);}
function meanV(xs){const a=xs.filter(Number.isFinite);return a.length?a.reduce((s,x)=>s+x,0)/a.length:null;}
function escV(s){return typeof esc==='function'?esc(s):String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
function fmtV(x,d=1){const v=finite(x);return v===null?'—':v.toFixed(d).replace(/\.0$/,'');}

function hashSeed(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
function rngFor(str){let a=hashSeed(str)||1;return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
function normal(rng){const u=Math.max(1e-12,rng()),v=Math.max(1e-12,rng());return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);}

function draftHelpers(){return window.FIE_DRAFT_V71||{};}
function currentDraft(){return state?.draftIntel?.draft||null;}
function currentPick(){return (state?.draftIntel?.picks||[]).length+1;}
function selectedRoster(){return Number(document.getElementById('draftRosterPicker')?.value||state?.selectedRoster)||null;}
function playerId(p){return String(window.FIECore?.PlayerIdentity?.id?.(p)||p?.sleeperId||p?.player_id||p?.playerId||'');}

function slotRosterMap(d){
  const out={};
  for(const [slot,rid] of Object.entries(d?.slot_to_roster_id||{}))out[Number(slot)]=Number(rid);
  if(typeof rosterDraftSlot==='function')for(const r of state.rosters||[]){const slot=rosterDraftSlot(d,r.roster_id);if(slot)out[Number(slot)]=Number(r.roster_id);}
  return out;
}

function posCount(pool,pos){return pool.reduce((n,p)=>n+(p.position===pos?1:0),0);}
function needAdjustment(pool,p,round){
  let demand=1;
  try{demand=Math.max(.5,Number((window.leaguePositionDemand||leaguePositionDemand)(p.position))||1);}catch{}
  const have=posCount(pool,p.position),short=Math.max(0,Math.ceil(demand)-have),over=Math.max(0,have-Math.ceil(demand)-1);
  let a=short*(round<=6?8:5)-over*3;
  // QBs and TEs become much more urgent only when the league actually creates scarcity.
  if((p.position==='QB'||p.position==='TE')&&demand<1.25&&have>=1)a-=4;
  return clampV(a,-10,18);
}

function managerReach(model,rosterId,p){
  if(!model?.managers)return 0;
  const r=(state.rosters||[]).find(x=>Number(x.roster_id)===Number(rosterId));
  const uid=String(r?.owner_id||'');const m=model.managers[uid];if(!m)return 0;
  let vals=[];const pb=(m.posBias||[]).find(x=>x.pos===p.position&&x.n>=2);if(pb&&finite(pb.delta)!==null)vals.push(Number(pb.delta));
  const fav=(m.playerBias||[]).find(x=>String(x.name).toLowerCase()===String(p.name).toLowerCase()&&x.n>=2);if(fav&&finite(fav.delta)!==null)vals.push(Number(fav.delta));
  return vals.length?clampV(meanV(vals),-15,15):0;
}

function marketRankMap(rows,pool){
  const byId=new Map(rows.map(x=>[playerId(x.p),x]));
  const missing=[...pool].filter(p=>!byId.has(playerId(p))||finite(byId.get(playerId(p))?.market)===null)
    .sort((a,b)=>(finite(b.m5DraftUtility??b.seasonScore??b.targetScore)??0)-(finite(a.m5DraftUtility??a.seasonScore??a.targetScore)??0));
  const maxKnown=Math.max(currentPick(),...rows.map(x=>finite(x.market)||0),0);
  const fallback=new Map(missing.map((p,i)=>[playerId(p),maxKnown+i+12]));
  return p=>finite(byId.get(playerId(p))?.market)??fallback.get(playerId(p))??999;
}

function staticDecisionMap(rows,pool){
  const m=new Map(rows.map(x=>[playerId(x.p),finite(x.score)??50]));
  for(const p of pool)if(!m.has(playerId(p)))m.set(playerId(p),finite(p.m5DraftUtility??p.seasonScore??p.targetScore)??50);
  return m;
}

function rosterPools(){
  const h=draftHelpers(),out={};
  for(const r of state.rosters||[]){
    let p=[];try{p=h.draftRosterPool?h.draftRosterPool(r.roster_id):rosterPlayers(r.roster_id);}catch{p=[];}
    const seen=new Set();out[Number(r.roster_id)]=(p||[]).filter(x=>{const id=playerId(x);if(seen.has(id))return false;seen.add(id);return true;});
  }
  return out;
}

function bestFromShortlist(sorted,available,limit,scoreFn){
  let best=null,bestScore=-Infinity,n=0;
  for(const item of sorted){if(!available.has(item.id))continue;n++;const s=scoreFn(item.p,item);if(s>bestScore){bestScore=s;best=item;}if(n>=limit)break;}
  return best;
}

function simulateCandidate(candidate,context,simIndex){
  const {d,seq,slotRoster,pool,marketOf,decisionMap,history,rosterId,basePools,startPick,endPick}=context;
  const rng=rngFor(`${state.league?.league_id}|${d.draft_id}|${startPick}|${playerId(candidate)}|${simIndex}`);
  const available=new Set(pool.map(playerId));
  const rosters={};for(const [k,v] of Object.entries(basePools))rosters[k]=v.slice();
  const cid=playerId(candidate);if(!available.has(cid))return null;
  rosters[rosterId]=(rosters[rosterId]||[]).concat(candidate);available.delete(cid);

  const latent=pool.map(p=>{
    const market=marketOf(p),sigma=clampV(6+Math.max(0,market-startPick)*.035,6,18);
    return {p,id:playerId(p),market,latent:market+normal(rng)*sigma};
  }).sort((a,b)=>a.latent-b.latent);

  for(const pick of seq){
    if(pick.pickNo<=startPick||pick.pickNo>endPick)continue;
    const rid=slotRoster[pick.slot];if(!rid||!available.size)continue;
    const rp=rosters[rid]||(rosters[rid]=[]);
    let choice;
    if(Number(rid)===Number(rosterId)){
      choice=bestFromShortlist(latent,available,42,(p,item)=>{
        const decision=decisionMap.get(item.id)??50;
        return decision+needAdjustment(rp,p,pick.round)*1.4-(Math.max(0,item.market-pick.pickNo))*0.08;
      });
    }else{
      choice=bestFromShortlist(latent,available,28,(p,item)=>{
        const reach=managerReach(history,rid,p),need=needAdjustment(rp,p,pick.round);
        // Higher score = should be selected earlier. Latent market location is
        // the dominant term; manager history and roster need perturb it.
        return -item.latent+reach*.75+need*.65;
      });
    }
    if(!choice)continue;
    available.delete(choice.id);rp.push(choice.p);
  }

  const finalPool=rosters[rosterId]||[];
  let util=null,starter=null,method='';
  try{const u=(window.rosterUtilityFromPool||rosterUtilityFromPool)(finalPool);util=finite(u?.total);starter=finite(u?.starterTotal);method=String(u?.method||'');}catch{}
  if(util===null)util=finalPool.reduce((s,p)=>s+(finite(p.m5DraftUtility??p.seasonScore??p.targetScore)??0),0);
  return {utility:util,starter,method};
}

function simulationContext(rosterId){
  const h=draftHelpers(),d=currentDraft();if(!d)return null;
  const rows=window.FIEDecisionService?.draftRows?.(rosterId)||h.buildDraftValueRows?.(rosterId)||[],pool=draftCandidatePool(),startPick=currentPick();
  const next=nextPickForRoster(rosterId,startPick);
  if(!next||Number(next.pickNo)!==Number(startPick))return {onClock:false,rows,pool,startPick,next};
  const seq=draftPickSequence(d),slotRoster=slotRosterMap(d),basePools=rosterPools(),marketOf=marketRankMap(rows,pool),decisionMap=staticDecisionMap(rows,pool),history=h.archiveManagerModel?h.archiveManagerModel():{};
  const lastOwn=[...seq].reverse().find(x=>slotRoster[x.slot]===Number(rosterId)&&x.pickNo>=startPick);
  const endPick=lastOwn?.pickNo||seq[seq.length-1]?.pickNo||startPick;
  return {onClock:true,d,rows,pool,startPick,seq,slotRoster,basePools,marketOf,decisionMap,history,rosterId,endPick};
}

function runDraftMonteCarlo(rosterId,{simulations=160,candidates=8}={}){
  const ctx=simulationContext(rosterId);if(!ctx)return {error:'Draft state is unavailable.'};
  if(!ctx.onClock)return {error:`Roster is not on the clock. Next pick is #${ctx.next?.pickNo??'—'}.`,onClock:false};
  const cand=[...ctx.rows].sort((a,b)=>(finite(b.score)??0)-(finite(a.score)??0)).slice(0,candidates).map(x=>x.p);
  const results=[];
  for(const p of cand){
    const vals=[],starters=[];let method='';
    for(let i=0;i<simulations;i++){const r=simulateCandidate(p,ctx,i);if(!r)continue;vals.push(r.utility);if(r.starter!==null)starters.push(r.starter);if(r.method)method=r.method;}
    if(!vals.length)continue;
    results.push({p,n:vals.length,mean:meanV(vals),p10:qtile(vals,.10),p90:qtile(vals,.90),starterMean:meanV(starters),method});
  }
  results.sort((a,b)=>b.mean-a.mean);const best=results[0]?.mean??null;
  results.forEach((r,i)=>{r.rank=i+1;r.deltaToBest=best===null?null:r.mean-best;});
  const key=`${state.league?.league_id}|${ctx.d.draft_id}|${ctx.startPick}|${rosterId}`;
  const out={key,leagueId:String(state.league?.league_id||''),draftId:String(ctx.d.draft_id),pick:ctx.startPick,rosterId,simulations,candidates:results,generatedAt:new Date().toISOString(),method:'remaining-draft Monte Carlo with ADP uncertainty, opponent roster need, saved-manager positional reach tendencies, and format-specific final roster utility'};
  Engine.draftCache.set(key,out);Engine.lastDraftRun=out;return out;
}


function monteCarloFormat(){
  try{return String(window.FIELeagueProfileResolver?.resolve?.(state.league,{formatOverride:document.getElementById('savedLeagueFormat')?.value})?.format||window.activeFormatKey?.()||'REDRAFT');}catch{return 'REDRAFT';}
}
function workerPlayerRecord(p,ctx){
  const fmt=monteCarloFormat(),fp=window.FIECore?.FormatRegistry?.profile?.(fmt)||{chopped:fmt.includes('CHOPPED'),bestBall:fmt.includes('BESTBALL')},market=ctx.marketOf(p),decision=ctx.decisionMap.get(playerId(p))??50;
  let utility=null;try{utility=finite((window.playerDecisionValue||playerDecisionValue)(p));}catch{}
  const season=finite(p.engineSeasonProjection)??finite(p.sleeperSeasonProjection)??(finite(p.seasonScore)??0)*2.2;
  const weekly=finite(p.weeklyProjection)??finite(p.sleeperWeeklyProjection)??season/17;
  return {id:playerId(p),name:String(p.name||''),position:String(p.position||''),team:String(p.team||''),market:Number.isFinite(market)?market:999,decision:finite(decision)??50,mean:fp.chopped||fp.bestBall?weekly:season,floor:fp.chopped?(finite(p.weeklyFloor)??weekly):season,ceiling:fp.bestBall?(finite(p.weeklyCeiling)??weekly):season,vor:finite(p.projectedVOR)??0,utility:utility??season};
}
function monteCarloWorkerContext(ctx){
  const byRoster={},all=new Map();
  for(const p of ctx.pool||[])all.set(playerId(p),p);
  for(const [rid,pool] of Object.entries(ctx.basePools||{})){
    byRoster[rid]=(pool||[]).map(p=>{const id=playerId(p);if(id)all.set(id,p);return id;}).filter(Boolean);
  }
  const available=new Set((ctx.pool||[]).map(playerId));
  const owners={};for(const r of state.rosters||[])owners[Number(r.roster_id)]=String(r.owner_id||'');
  const rosterSlots=window.FIERuntimeContracts?.roster_slots||{};
  const players=[...all.values()].map(p=>({...workerPlayerRecord(p,ctx),draftAvailable:available.has(playerId(p))}));
  const fingerprint=window.FIECore?.ContextFingerprint?.current?.({draftId:String(ctx.d.draft_id),pick:Number(ctx.startPick),rosterId:Number(ctx.rosterId)})||`${state.league?.league_id}|${ctx.d.draft_id}|${ctx.startPick}`;
  const fmt=monteCarloFormat(),formatCapabilities=window.FIECore?.FormatRegistry?.profile?.(fmt)||{key:fmt,dynasty:fmt.includes('DYNASTY'),bestBall:fmt.includes('BESTBALL'),chopped:fmt.includes('CHOPPED')};
  return {seed:String(fingerprint),format:fmt,formatCapabilities,rosterPositions:[...(state.league?.roster_positions||[])],slotEligibility:Object.fromEntries(Object.entries(rosterSlots).map(([k,v])=>[k,[...(v?.positions||[])]])),players,basePools:byRoster,rosterOwner:owners,history:ctx.history||{},seq:ctx.seq.map(x=>({pickNo:Number(x.pickNo),round:Number(x.round),slot:Number(x.slot)})),slotRoster:{...ctx.slotRoster},rosterId:Number(ctx.rosterId),startPick:Number(ctx.startPick),endPick:Number(ctx.endPick)};
}
function cancelDraftMonteCarlo(reason='cancelled'){
  const job=Engine.draftJob;if(!job)return;job.cancelled=true;try{job.worker?.postMessage({type:'cancel',jobId:job.id});job.worker?.terminate();}catch{}Engine.draftJob=null;Engine.draftProgress={status:'cancelled',reason};
}
async function runDraftMonteCarloAsync(rosterId,{candidates=8,batches=[32,64,128]}={}){
  const ctx=simulationContext(rosterId);if(!ctx)return {error:'Draft state is unavailable.'};
  if(!ctx.onClock)return {error:`Roster is not on the clock. Next pick is #${ctx.next?.pickNo??'—'}.`,onClock:false};
  if(typeof Worker!=='function')return {error:'Deep draft simulation is unavailable because this browser does not support Web Workers.',workerUnavailable:true};
  cancelDraftMonteCarlo('superseded');
  const cand=[...ctx.rows].sort((a,b)=>(finite(b.score)??0)-(finite(a.score)??0)).slice(0,candidates).map(x=>x.p),ids=cand.map(playerId),byId=new Map(cand.map(p=>[playerId(p),p]));
  const jobId=`mc-${Date.now()}-${Math.random().toString(36).slice(2)}`,worker=new Worker('app/draft-monte-carlo-worker.js'),samples=new Map(ids.map(id=>[id,[]]));
  const job={id:jobId,worker,cancelled:false,leagueId:String(state.league?.league_id||''),draftId:String(ctx.d.draft_id),pick:ctx.startPick};Engine.draftJob=job;
  const context=monteCarloWorkerContext(ctx),targets=[...new Set((batches||[32,64,128]).map(Number).filter(x=>x>0))].sort((a,b)=>a-b);let done=0;
  const receiveBatch=(startIndex,count)=>new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('Monte Carlo worker timed out.')),60000);const listener=e=>{const m=e.data||{};if(m.jobId!==jobId||m.type!=='batch')return;worker.removeEventListener('message',listener);clearTimeout(timeout);resolve(m);};worker.addEventListener('message',listener);worker.postMessage({type:'run',jobId,startIndex,count,candidateIds:ids,context});});
  try{
    for(const target of targets){
      if(job.cancelled)throw new Error('cancelled');
      while(done<target){
        const count=Math.min(16,target-done);
        Engine.draftProgress={status:'running',done,target:targets.at(-1),leagueId:job.leagueId,draftId:job.draftId,pick:job.pick};draftPanel();
        const m=await receiveBatch(done,count);if(job.cancelled)throw new Error('cancelled');
        for(const r of m.results||[])samples.get(String(r.id))?.push(...(r.values||[]).map(Number).filter(Number.isFinite));
        done+=count;
      }
      const results=ids.map(id=>{const vals=samples.get(id)||[];return vals.length?{p:byId.get(id),n:vals.length,mean:meanV(vals),p10:qtile(vals,.10),p90:qtile(vals,.90),method:'Web Worker exact legal-lineup utility'}:null;}).filter(Boolean).sort((a,b)=>b.mean-a.mean);const best=results[0]?.mean??null;results.forEach((r,i)=>{r.rank=i+1;r.deltaToBest=best===null?null:r.mean-best;});const key=window.FIECore?.ContextFingerprint?.current?.({draftId:String(ctx.d.draft_id),pick:Number(ctx.startPick),rosterId:Number(rosterId),purpose:'monte-carlo'})||`${state.league?.league_id}|${ctx.d.draft_id}|${ctx.startPick}|${rosterId}`;const out={key,leagueId:job.leagueId,draftId:job.draftId,pick:ctx.startPick,rosterId,simulations:done,candidates:results,generatedAt:new Date().toISOString(),progressive:done<targets.at(-1),method:'progressive Web Worker remaining-draft Monte Carlo; exact legal lineup assignment; ADP uncertainty, roster need and saved manager tendencies'};Engine.draftCache.set(key,out);Engine.lastDraftRun=out;Engine.draftProgress={status:done<targets.at(-1)?'running':'complete',done,target:targets.at(-1),leagueId:job.leagueId,draftId:job.draftId,pick:job.pick};draftPanel();
    }
    return Engine.lastDraftRun;
  }finally{if(Engine.draftJob?.id===jobId){try{worker.terminate();}catch{}Engine.draftJob=null;}}
}
window.addEventListener?.('fie:league-changing',()=>cancelDraftMonteCarlo('league changed'));
window.addEventListener?.('fie:draft-updated',()=>cancelDraftMonteCarlo('draft changed'));

function draftPanel(){
  const host=document.getElementById('draftAssistantSummary');if(!host||!state.league||!state.draftIntel?.draft)return;
  let panel=document.getElementById('fieDraftMonteCarlo');if(!panel){panel=document.createElement('div');panel.id='fieDraftMonteCarlo';panel.className='card';panel.style.cssText='margin-top:14px;padding:14px';host.appendChild(panel);}
  const rosterId=selectedRoster(),pick=currentPick(),key=`${state.league?.league_id}|${state.draftIntel.draft.draft_id}|${pick}|${rosterId}`,cached=Engine.draftCache.get(key);
  const next=nextPickForRoster(rosterId,pick),onClock=next&&Number(next.pickNo)===pick;
  if(!cached){
    const prog=Engine.draftProgress?.status==='running'?`<div class="notice" style="margin-top:10px"><b>Simulating progressively:</b> ${Engine.draftProgress.done}/${Engine.draftProgress.target} paths per candidate complete. You can keep using the app while the worker runs.</div>`:'';
    panel.innerHTML=`<div class="eyebrow">Remaining-draft simulation</div><h3 style="margin:4px 0 6px">Monte Carlo Draft Strategist <span class="badge">Beta</span></h3><div class="subtitle">Evaluates a pick by the final roster it tends to produce, not only by the player's standalone rank. Simulations use Sleeper ADP uncertainty, roster needs, saved manager/position tendencies when available, and the active league-format utility.</div>${onClock?`${prog}<button id="runFieDraftMonteCarlo" class="btn primary" style="margin-top:10px">Simulate top choices</button>`:`<div class="notice" style="margin-top:10px">Your selected roster is not on the clock. Its next pick is #${next?.pickNo??'—'}. Choice simulation activates when that roster is on the clock.</div>`}`;
  }else{
    const rs=cached.candidates||[];
    panel.innerHTML=`<div class="eyebrow">Remaining-draft simulation</div><h3 style="margin:4px 0 6px">Monte Carlo Draft Strategist</h3><div class="subtitle">${cached.simulations} full remaining-draft simulations per candidate. Higher final roster utility is better. This is a simulation model, not yet a prospectively calibrated probability model.</div><div class="scroll" style="margin-top:10px"><table class="draft-assistant-table"><thead><tr><th>#</th><th>Pick now</th><th>Expected final roster</th><th>10–90% range</th><th>vs best</th><th>Interpretation</th></tr></thead><tbody>${rs.map(r=>`<tr><td><b>${r.rank}</b></td><td><b>${escV(r.p.name)}</b><br><span class="muted">${escV(r.p.position)} · ADP ${fmtV(r.p.marketADP)}</span></td><td><b>${fmtV(r.mean,2)}</b></td><td>${fmtV(r.p10,2)} – ${fmtV(r.p90,2)}</td><td class="${r.deltaToBest>=-.01?'positive':'negative'}">${r.deltaToBest>=-.01?'BEST':fmtV(r.deltaToBest,2)}</td><td>${r.rank===1?'<b>Best simulated roster path</b>':Math.abs(r.deltaToBest)<1?'Near-equivalent path':'Lower expected final roster utility'}</td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:10px"><b>Why this is different:</b> the existing Draft Assistant asks how good the player is now and how likely they are to survive. This layer additionally asks what your roster tends to look like after all later picks. Re-run after every pick because availability and roster needs change.</div><button id="runFieDraftMonteCarlo" class="btn" style="margin-top:10px">Re-run simulations</button>`;
  }
  const btn=document.getElementById('runFieDraftMonteCarlo');if(btn&&!btn.dataset.bound){btn.dataset.bound='1';btn.onclick=()=>{btn.disabled=true;btn.textContent='Starting worker…';runDraftMonteCarloAsync(rosterId).catch(err=>{if(String(err?.message)!=='cancelled'){console.error(err);Engine.draftProgress={status:'error',error:String(err?.message||err)};}draftPanel();});};}
}


// ---------------------------------------------------------------------------
// Action-first UX, FAAB context, bilateral trade fit and player explanations
// ---------------------------------------------------------------------------

function remainingFaab(rid){
  const cap=Number(state.league?.settings?.waiver_budget)||100;
  const r=(state.rosters||[]).find(x=>Number(x.roster_id)===Number(rid));
  return Math.max(0,cap-(Number(r?.settings?.waiver_budget_used)||0));
}
function weeksRemaining(){return Math.max(1,leagueRegularSeasonEnd()-activeWeek()+1);}
function swapFor(p,rid){
  try{if(typeof window.bestWaiverSwap==='function')return window.bestWaiverSwap(p,rid);}catch{}
  const pool=rosterPoolFor(rid);if(!pool.length)return null;let base;try{base=window.rosterUtilityFromPool(pool);}catch{return null;}
  let best=null;for(const drop of pool){let after;try{after=window.rosterUtilityFromPool(pool.filter(x=>x!==drop).concat(p));}catch{continue;}const gain=(finite(after?.total)??0)-(finite(base?.total)??0);if(!best||gain>best.gain)best={drop,gain,starterGain:(finite(after?.starterTotal)??0)-(finite(base?.starterTotal)??0),totalAfter:after?.total};}
  return best;
}
function allWinningBids(pos){
  const prof=Object.values(state.transactions?.profiles||{}),byPos=prof.flatMap(x=>(x.waiverBidsByPos?.[pos]||[])).map(Number).filter(Number.isFinite),all=prof.flatMap(x=>x.waiverBids||[]).map(Number).filter(Number.isFinite);
  return {sample:byPos.length>=6?byPos:all,positionN:byPos.length,allN:all.length,scope:byPos.length>=6?pos:'all positions'};
}
function winningBidContext(pos,bid){
  const x=allWinningBids(pos),a=[...x.sample].sort((a,b)=>a-b);if(!a.length)return {...x,q50:null,q75:null,q90:null,coverage:null};
  const coverage=a.filter(v=>v<=bid).length/a.length;
  return {...x,q50:qtile(a,.50),q75:qtile(a,.75),q90:qtile(a,.90),coverage};
}
function faabFor(p,swap,rankPct){
  try{if(typeof window.faabRecommendation==='function')return window.faabRecommendation(p,swap,rankPct);}catch{}
  const b=remainingFaab(selectedRoster());return {rec:Math.round(Math.min(b,b*.12)),low:Math.round(Math.min(b,b*.08)),high:Math.round(Math.min(b,b*.18)),history:0,base:null};
}
function strategicWaiverRows(rid,limit=6){
  let xs=(window.PLAYERS||PLAYERS||[]).filter(p=>p.availability==='FA'&&p.leagueEligible).sort((a,b)=>(finite(b.waiverScore)??0)-(finite(a.waiverScore)??0)).slice(0,45)
    .map(p=>({p,swap:swapFor(p,rid)})).filter(x=>x.swap).sort((a,b)=>b.swap.gain-a.swap.gain).slice(0,limit);
  xs.forEach((x,i)=>{x.faab=faabFor(x.p,x.swap,1-i/Math.max(10,xs.length));x.bid=winningBidContext(x.p.position,x.faab.rec);});return xs;
}
function faabPosture(x,rid){
  const rem=remainingFaab(rid),weekly=rem/weeksRemaining(),rec=Number(x.faab?.rec)||0;
  if(!x.bid.sample.length)return rec>weekly*2?'Aggressive, history thin':'Value-led, history thin';
  if(x.bid.q90!==null&&rec>=x.bid.q90)return 'Historically aggressive';
  if(x.bid.q75!==null&&rec>=x.bid.q75)return 'Above typical winner';
  if(x.bid.q50!==null&&rec>=x.bid.q50)return 'Near typical winner';
  return 'Conservative vs past winners';
}
function ensureWaiverStrategyPanel(){
  let p=document.getElementById('fieFaabStrategy');if(p)return p;p=document.createElement('div');p.id='fieFaabStrategy';p.className='card';p.style.cssText='padding:14px;margin-top:10px';const w=document.getElementById('waiverRecommendations');if(w)w.insertAdjacentElement('afterend',p);else document.querySelector('.table-card')?.insertAdjacentElement('beforebegin',p);return p;
}
function renderStrategicWaiverPanel(){
  const p=ensureWaiverStrategyPanel();if(state.activeTab!=='waivers'||!state.selectedRoster||!state.matched){p.classList.add('hidden');return;}p.classList.remove('hidden');const rid=Number(state.selectedRoster),rows=strategicWaiverRows(rid),rem=remainingFaab(rid),weekBank=rem/weeksRemaining();
  if(!rows.length){p.innerHTML='<div class="eyebrow">FAAB strategy</div><div class="notice">No roster-positive add/drop candidate is available.</div>';return;}
  p.innerHTML=`<div class="eyebrow">FAAB strategy</div><h3 style="margin:4px 0 6px">Winning-bid context, budget pressure & leverage <span class="badge">Beta</span></h3><div class="subtitle">Historical completed bids are used as <b>winning-threshold context</b>, not as a calibrated probability of winning a future claim. Remaining budget is ${fmtV(rem,0)}; equal-spend pace is ${fmtV(weekBank,1)} per remaining regular-season week.</div><div class="scroll" style="margin-top:10px"><table><thead><tr><th>Add</th><th>Drop</th><th>Roster gain</th><th>Rec bid</th><th>Past winner median</th><th>75th / 90th</th><th>Historical context</th></tr></thead><tbody>${rows.map(x=>`<tr><td><b>${escV(x.p.name)}</b><br><span class="muted">${escV(x.p.position)}</span></td><td>${escV(x.swap.drop?.name||'—')}</td><td class="${x.swap.gain>=0?'positive':'negative'}">${x.swap.gain>=0?'+':''}${fmtV(x.swap.gain,2)}</td><td><b>${fmtV(x.faab.rec,0)}</b><br><span class="muted">${fmtV(x.faab.low,0)}–${fmtV(x.faab.high,0)}</span></td><td>${fmtV(x.bid.q50,0)}</td><td>${fmtV(x.bid.q75,0)} / ${fmtV(x.bid.q90,0)}</td><td>${escV(faabPosture(x,rid))}<br><span class="muted">${x.bid.sample.length?`${x.bid.sample.length} ${escV(x.bid.scope)} winning bids · rec ≥ ${Math.round((x.bid.coverage||0)*100)}% of sample`:'No historical winning-bid sample'}</span></td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:10px"><b>Why no “72% chance to win”?</b> Sleeper transaction history reliably gives completed winning claims, but not a complete set of every losing private bid. The app therefore shows empirical winner thresholds and manager tendencies without inventing a calibrated auction probability.</div><button id="fieWaiverLeverageBtn" class="btn" style="margin-top:10px">Measure matchup / season leverage</button><div id="fieWaiverLeverageOut"></div>`;
  const btn=document.getElementById('fieWaiverLeverageBtn');if(btn)btn.onclick=()=>runWaiverLeverage(rid,rows.slice(0,3));
}
function modelWithPool(models,rid,pool){const x={...models};x[rid]=teamModelFromPool(pool);return x;}
async function runWaiverLeverage(rid,rows){
  const out=document.getElementById('fieWaiverLeverageOut');if(!out)return;out.innerHTML='<div class="notice" style="margin-top:10px">Running paired counterfactual simulations…</div>';
  if(!Engine.leagueSim.data)await runLeagueSimulation(true);const d=Engine.leagueSim.data;if(!d){out.innerHTML='<div class="notice">League simulation is unavailable, so only roster-utility gain can be shown.</div>';return;}
  const basePool=rosterPoolFor(rid),oppId=d.current?.opponentId,baseCurrent=d.current?.win??null,baseStrategic=(d.strategic?.rows||[]).find(x=>Number(x.rosterId)===Number(rid)),res=[];
  for(const x of rows){const afterPool=basePool.filter(p=>p!==x.swap.drop).concat(x.p),models=modelWithPool(d.models,rid,afterPool);let matchDelta=null;if(oppId&&models[oppId]){const m=matchupProbability(models[rid],models[oppId],`${state.league.league_id}|${activeWeek()}|waiver|${playerId(x.p)}`,2200);if(baseCurrent!==null)matchDelta=m.win-baseCurrent;}
    let objDelta=null,objLabel='';if(d.chopped){const pools=Object.fromEntries((state.rosters||[]).map(r=>[r.roster_id,r.roster_id===rid?afterPool:rosterPoolFor(r.roster_id)])),s=simulateChopped(220,pools),r=s.rows.find(z=>Number(z.rosterId)===rid);objDelta=r&&baseStrategic?r.winner-baseStrategic.winner:null;objLabel='league-win';}else{const s=simulateRedraftSeason(d.matchups,models,420),r=s.rows.find(z=>Number(z.rosterId)===rid);objDelta=r&&baseStrategic?r.playoff-baseStrategic.playoff:null;objLabel='playoff';}
    res.push({...x,matchDelta,objDelta,objLabel});
  }
  out.innerHTML=`<div class="scroll" style="margin-top:10px"><table><thead><tr><th>Move</th><th>Roster utility</th><th>This-week win probability</th><th>${d.chopped?'League-win':'Playoff'} probability</th><th>Decision</th></tr></thead><tbody>${res.map(x=>`<tr><td><b>${escV(x.p.name)}</b> for ${escV(x.swap.drop.name)}</td><td>+${fmtV(x.swap.gain,2)}</td><td>${x.matchDelta===null?'—':`${x.matchDelta>=0?'+':''}${fmtV(x.matchDelta*100,1)} pp`}</td><td>${x.objDelta===null?'—':`${x.objDelta>=0?'+':''}${fmtV(x.objDelta*100,1)} pp`}</td><td>${(x.matchDelta||0)>0.015||(x.objDelta||0)>0.01?'<b>Meaningful leverage</b>':'Marginal strategic change'}</td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:8px">Counterfactuals reuse the same current-strength league model. Probability deltas are simulation estimates, not yet prospectively calibrated transaction effects.</div>`;
}

function needFitFor(rosterId,players){
  let needs=[];try{needs=window.positionNeedsForRoster?.(rosterId)||[];}catch{}const map=Object.fromEntries(needs.map(x=>[x.pos,x.needScore]));const vals=(players||[]).map(p=>finite(map[p.position])).filter(x=>x!==null);return vals.length?meanV(vals):.5;
}
function selectedAssetsForTrade(){
  const a=Number(document.getElementById('tradeRosterA')?.value),b=Number(document.getElementById('tradeRosterB')?.value);let sendA=[],sendB=[],picksA=[],picksB=[];try{sendA=window.selectedTradePlayers?.('tradePlayersA')||[];sendB=window.selectedTradePlayers?.('tradePlayersB')||[];picksA=window.selectedTradePicks?.('tradePicksA')||[];picksB=window.selectedTradePicks?.('tradePicksB')||[];}catch{}
  return {a,b,sendA,sendB,picksA,picksB};
}
function counterpartyTradeFit(){
  const z=selectedAssetsForTrade();if(!z.a||!z.b)return null;const poolA=rosterPoolFor(z.a),poolB=rosterPoolFor(z.b),idsA=new Set(z.sendA.map(playerId)),idsB=new Set(z.sendB.map(playerId));let baseB,afterB;try{baseB=window.rosterUtilityFromPool(poolB);afterB=window.rosterUtilityFromPool(poolB.filter(p=>!idsB.has(playerId(p))).concat(z.sendA));}catch{return null;}
  const valA=z.sendA.reduce((n,p)=>n+(finite(window.tradeAssetValue?.(p))??releasedValue(p)),0)+z.picksA.reduce((n,p)=>n+(finite(window.pickValue?.(p))??0),0),valB=z.sendB.reduce((n,p)=>n+(finite(window.tradeAssetValue?.(p))??releasedValue(p)),0)+z.picksB.reduce((n,p)=>n+(finite(window.pickValue?.(p))??0),0);
  const delta=(finite(afterB?.total)??0)-(finite(baseB?.total)??0),scale=Math.max(1,Math.abs(finite(baseB?.total)??0)*.08),utility=Math.tanh(delta/scale),value=Math.tanh((valA-valB)/Math.max(5,(Math.abs(valA)+Math.abs(valB))*.25)),need=clampV((needFitFor(z.b,z.sendA)-.5)*2,-1,1),prof=state.transactions?.profiles?.[z.b]||{},activity=clampV((Number(prof.trades)||0)/8,0,1),prior=clampV((Number(prof.tradePartners?.[z.a])||0)/3,0,1),raw=.38*utility+.27*value+.18*need+.10*activity+.07*prior,score=Math.round(clampV(50+raw*42,5,95));
  return {...z,score,delta,valueSignal:value,needSignal:need,activity,prior,valA,valB};
}
function appendTradeCounterparty(){
  const out=document.getElementById('tradeResult'),x=counterpartyTradeFit();if(!out||!x)return;const names=leagueRosterNameMap(),cls=x.score>=65?'positive':x.score<40?'negative':'';out.insertAdjacentHTML('beforeend',`<div class="notice fie-trade-fit" style="margin-top:10px"><b>Counterparty fit score: <span class="${cls}">${x.score}/100</span></b> for ${escV(names[x.b]||`Roster ${x.b}`)}.<br>Roster-utility impact for them: <b>${x.delta>=0?'+':''}${fmtV(x.delta,2)}</b> · assets they receive vs send: ${fmtV(x.valA,1)} vs ${fmtV(x.valB,1)} · positional-need signal ${fmtV(x.needSignal,2)} · prior trade-activity signal ${fmtV(x.activity,2)}.${x.prior?` · prior direct-trade signal ${fmtV(x.prior,2)}`:''}<br><span class="muted"><b>Not an acceptance probability:</b> Sleeper exposes completed trades, not rejected private offers, so a calibrated P(accept) cannot be learned honestly yet. This score ranks how plausible the offer looks from the other roster's perspective.</span></div>`);
}

function playerDecisionSummary(p){
  const weeklyBase=finite(p.sleeperWeeklyProjection),weekly=finite(p.weeklyProjection),seasonBase=finite(p.sleeperSeasonProjection),season=finite(p.engineSeasonProjection),vor=finite(p.projectedVOR),edge=finite(p.marketEdge),rid=Number(state.selectedRoster),swap=p.availability==='FA'&&rid?swapFor(p,rid):null;let dv=null;try{dv=finite((window.playerDecisionValue||playerDecisionValue)(p));}catch{}
  const factors=[];if(finite(p.usageAdjustment)!==null)factors.push({k:'Usage',v:Number(p.usageAdjustment)*100});if(finite(p.matchupAdjustment)!==null)factors.push({k:'Matchup',v:Number(p.matchupAdjustment)*100});if(finite(p.projectionAdjustment)!==null)factors.push({k:'Season overlay',v:Number(p.projectionAdjustment)*100});
  return {weeklyBase,weekly,weeklyDelta:weekly!==null&&weeklyBase!==null?weekly-weeklyBase:null,seasonBase,season,seasonDelta:season!==null&&seasonBase!==null?season-seasonBase:null,vor,edge,swap,dv,factors};
}
function augmentDrawer(id){
  const body=document.getElementById('drawerBody'),players=(typeof PLAYERS!=='undefined'?PLAYERS:(window.PLAYERS||[])),p=players.find(x=>String(x.sleeperId||x.name)===String(id));if(!body||!p||body.querySelector('.fie-decision-summary'))return;
  const x=playerDecisionSummary(p),rid=Number(document.getElementById('draftRosterPicker')?.value||state.selectedRoster),draftRow=(window.FIEModelV9?.buildDiagnosticRows?.(rid)||window.FIEModelV9?.buildDraftValueRows?.(rid)||[]).find(r=>playerId(r.p)===playerId(p))||null,features=window.FIECurrentFeatures?.summary?.(p)||[],lineage=window.FIEModelV9?.featureLineage?.(p)||[],audit=window.FIEScoringSupport?.audit?.()||null,fmt=window.FIELeagueProfileResolver?.resolveFor?.(state.league)?.format||'REDRAFT';
  const floor=finite(p.weeklyFloor),mean=finite(p.weeklyProjection),ceil=finite(p.weeklyCeiling),mx=Math.max(1,ceil??mean??1),left=floor===null?0:clampV(floor/mx*100,0,100),mid=mean===null?50:clampV(mean/mx*100,0,100),right=ceil===null?100:clampV(ceil/mx*100,0,100);
  const why=draftRow?.why?.length?draftRow.why:[...x.factors.map(f=>`${f.k} ${f.v>=0?'+':''}${fmtV(f.v,1)}%`)];
  const d=document.createElement('div');d.className='fie-decision-summary';
  d.innerHTML=`<div class="eyebrow">League-specific player report</div><h3 style="margin:4px 0 8px">Why FIE ${draftRow?.valueEdge>0?'values':'evaluates'} ${escV(p.name)} ${draftRow?.valueEdge>0?'above':'versus'} the market</h3>
  <div class="fie-action-grid"><div class="fie-action-card"><span>Sleeper ADP</span><b>${draftRow?.market===null||draftRow?.market===undefined?'—':fmtV(draftRow.market,0)}</b><small>${draftRow?.marketSampleRank?`eligible market #${draftRow.marketSampleRank}`:'market baseline'}</small></div><div class="fie-action-card"><span>FIE League Rank</span><b>${draftRow?.leagueRank?`#${draftRow.leagueRank}`:'—'}</b><small>${draftRow?.valueEdge===null||draftRow?.valueEdge===undefined?'no comparable ADP':`${draftRow.valueEdge>=0?'+':''}${fmtV(draftRow.valueEdge,0)} ranks vs market`}</small></div><div class="fie-action-card"><span>Roster Value</span><b>${draftRow?.rosterMarginal===undefined?'—':`${draftRow.rosterMarginal>=0?'+':''}${fmtV(draftRow.rosterMarginal,2)}`}</b><small>marginal roster utility</small></div><div class="fie-action-card"><span>Draft Decision</span><b>${escV(draftRow?.recommendation||'—')}</b><small>${draftRow?.survive==null?'timing unavailable':`${draftRow.survive}% modeled survival to next own-pick window`}</small></div></div>
  <div class="fie-range"><div class="fie-range-label"><b>Weekly distribution</b><span>${floor===null?'—':fmtV(floor)} low · ${mean===null?'—':fmtV(mean)} mean · ${ceil===null?'—':fmtV(ceil)} high</span></div><div class="fie-range-track"><i style="left:${left}%;width:${Math.max(1,right-left)}%"></i><b style="left:${mid}%"></b></div></div>
  <div class="fie-report-grid"><section><b>Why FIE differs</b><ul>${why.length?why.slice(0,6).map(z=>`<li>${escV(z)}</li>`).join(''):'<li>No active league-specific divergence is available.</li>'}</ul></section><section><b>League effects</b><ul><li>${escV(fmt)} format</li><li>${draftRow?`${draftRow.leagueUtility>=0?'+':''}${fmtV(draftRow.leagueUtility,2)} ${escV(draftRow.leagueUtilityUnit)}`:'league utility unavailable'}</li><li>${audit?`${Math.round(audit.coverage*100)}% relevant scoring coverage${audit.ignoredIrrelevant?.length?`, ${audit.ignoredIrrelevant.length} irrelevant rules ignored`:''}`:'scoring audit unavailable'}</li></ul></section><section><b>Current opportunity evidence</b><ul>${features.length?features.slice(0,6).map(f=>`<li>${escV(f.text)}</li>`).join(''):'<li>No governed current-feature snapshot matched this player.</li>'}</ul></section><section><b>Signal lineage</b><div class="fie-lineage">${lineage.length?lineage.map(l=>`<span class="fie-lineage-chip ${l.active?'active':'diagnostic'}">${escV(l.family)} · ${l.active?'active':'diagnostic'}</span>`).join(''):'<span class="muted">No lineage metadata.</span>'}</div></section></div>
  <div class="fie-explain"><b>Roster counterfactual:</b> ${x.swap?`Adding ${escV(p.name)} would currently model ${x.swap.gain>=0?'+':''}${fmtV(x.swap.gain,2)} utility versus the best identified drop, ${escV(x.swap.drop.name)}.`:'No free-agent swap counterfactual is available for the selected roster.'}<br><b>Architecture:</b> League Rank is roster-independent; Roster Value measures team-specific marginal value; Draft Decision adds market timing. Research opportunity features are displayed separately so they are not silently counted as an additional independent signal when they already influence a governed projection.</div>`;
  body.insertAdjacentElement('afterbegin',d);
}

function commandCenterItems(rid=Number(state.selectedRoster)){
  if(!state.league||!rid)return [];
  const waiver=strategicWaiverRows(rid,1)[0],sim=Engine.leagueSim.data,current=sim?.current,strategic=(sim?.strategic?.rows||[]).find(x=>Number(x.rosterId)===Number(rid)),draft=Engine.lastDraftRun?.rosterId===Number(rid)?Engine.lastDraftRun:null;let partner=null;try{partner=(window.tradePartnerSuggestions?.(rid)||[])[0]||null;}catch{}
  const items=[];
  if(draft?.candidates?.[0])items.push({priority:100,route:'draftassistant',tag:'DRAFT',title:`Take ${draft.candidates[0].p.name}`,note:`Best simulated final-roster path at pick #${draft.pick}; ${draft.simulations} paths per candidate.`,metric:fmtV(draft.candidates[0].mean,2)});
  const injuryRisk=(window.PLAYERS||PLAYERS||[]).filter(p=>Number(p.ownerRosterId)===Number(rid)&&String(p.startDecision||'').startsWith('START')&&String(p.injuryStatus||'').trim()).sort((a,b)=>(finite(b.weeklyProjection)??0)-(finite(a.weeklyProjection)??0))[0];
  if(injuryRisk)items.push({priority:95,route:'startsit',tag:'LINEUP',title:`Monitor ${injuryRisk.name}`,note:`Currently in the modeled starting lineup with injury status ${injuryRisk.injuryStatus}. Re-check before lineup lock.`,metric:'Check'});
  if(waiver)items.push({priority:80,route:'waivers',tag:'WAIVER',title:`Add ${waiver.p.name}, drop ${waiver.swap.drop.name}`,note:`+${fmtV(waiver.swap.gain,2)} roster utility; FAAB rec ${waiver.faab.rec}, historical ${waiver.bid.scope} winner median ${fmtV(waiver.bid.q50,0)}.`,metric:`+${fmtV(waiver.swap.gain,2)}`});
  if(current)items.push({priority:90,route:'matchupsim',tag:'THIS WEEK',title:`${Math.round(current.win*100)}% win probability`,note:`${current.myName} ${fmtV(current.myMean)} vs ${current.oppName} ${fmtV(current.oppMean)}; median margin ${current.medianMargin>=0?'+':''}${fmtV(current.medianMargin)}.`,metric:`${Math.round(current.win*100)}%`});
  if(strategic)items.push({priority:60,route:'matchupsim',tag:sim?.chopped?'SURVIVAL':'SEASON',title:sim?.chopped?`${Math.round(strategic.winner*100)}% league-win simulation`:`${Math.round(strategic.playoff*100)}% playoff simulation`,note:sim?.chopped?`Current-strength chopped paths with direct elimination and released-player redistribution.`:`Expected rank ${fmtV(strategic.expectedRank,2)}; title probability ${Math.round(strategic.title*100)}%.`,metric:sim?.chopped?`${Math.round(strategic.winner*100)}%`:`${Math.round(strategic.playoff*100)}%`});
  if(partner)items.push({priority:40,route:'trades',tag:'TRADE',title:`Explore ${partner.name}`,note:`Best complementary roster fit from current position rooms${partner.prior?` and ${partner.prior} prior trade(s) with you`:''}.`,metric:`Fit ${fmtV(partner.score,0)}`});
  return items.sort((a,b)=>(b.priority||0)-(a.priority||0));
}
function portfolioSnapshot(rid=Number(state.selectedRoster)){
  if(!state.league||!rid)return null;let power=null,names={};try{power=window.teamPowerMetrics?.(rid)||null;names=window.rosterNameMap?.()||{};}catch{}
  const fp=window.formatProfile?.()||{},items=commandCenterItems(rid),viol=window.rosterRuleViolations?.(rid)||[];
  return {schemaVersion:1,leagueId:String(state.league.league_id||''),leagueName:String(state.league.name||state.league.league_id||'League'),season:Number(state.league.season)||null,format:String(fp.label||'League'),formatKey:String(window.activeFormatKey?.()||''),teams:Number(state.league.total_rosters||state.rosters?.length)||null,rosterId:Number(rid),rosterName:String(names[rid]||`Roster ${rid}`),powerRank:finite(power?.powerRank),contenderRank:finite(power?.ranks?.contender),weeklyRank:finite(power?.ranks?.weekly),depthRank:finite(power?.ranks?.depth),dynastyRank:finite(power?.ranks?.dynasty),items:items.slice(0,5),violations:viol.slice(0,4),generatedAt:new Date().toISOString()};
}
function renderCommandCenter(){
  const box=document.getElementById('homeSummary');if(!box||!state.league||!state.selectedRoster)return;let c=document.getElementById('fieDecisionCommandCenter');if(!c){c=document.createElement('div');c.id='fieDecisionCommandCenter';c.className='home-card full fie-command-center';box.querySelector('.home-grid')?.appendChild(c);}if(!c)return;const items=commandCenterItems(Number(state.selectedRoster)),sim=Engine.leagueSim.data;
  c.innerHTML=`<div class="hc-label">Fantasy Command Center</div><div class="hc-note">Action-first summary. Open the detailed module for assumptions, uncertainty and counterfactuals.</div><div class="fie-command-list">${items.length?items.slice(0,5).map(x=>`<div class="fie-command-item"><span class="fie-tag">${escV(x.tag)}</span><div><b>${escV(x.title)}</b><small>${escV(x.note)}</small></div><strong>${escV(x.metric)}</strong></div>`).join(''):'<div class="action-callout">Load draft, transaction and weekly context to populate prioritized decisions.</div>'}</div>${!sim?'<div class="fie-explain">Matchup/playoff probabilities appear here after the Matchup & Playoffs simulation has run.</div>':''}`;
  try{window.FIEPortfolio?.captureCurrentLeague?.(portfolioSnapshot(Number(state.selectedRoster)));}catch{}
}

function injectDecisionStyles(){if(document.getElementById('fieDecisionStyles'))return;const st=document.createElement('style');st.id='fieDecisionStyles';st.textContent=`
.fie-action-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:8px 0}.fie-action-card{border:1px solid var(--line);background:rgba(7,18,34,.7);border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:3px}.fie-action-card span,.fie-action-card small{color:var(--muted);font-size:11px}.fie-action-card b{font-size:19px}.fie-explain{margin-top:9px;border-left:3px solid #5086c8;background:rgba(32,67,110,.18);padding:9px 11px;border-radius:8px;font-size:12px;line-height:1.45}.fie-decision-summary{margin-bottom:12px}.fie-range{border:1px solid var(--line);border-radius:10px;padding:9px 10px;margin:9px 0;background:rgba(8,20,36,.65)}.fie-range-label{display:flex;justify-content:space-between;gap:8px;font-size:10px;color:var(--muted)}.fie-range-track{height:8px;border-radius:99px;background:#162a43;position:relative;margin-top:8px}.fie-range-track i{position:absolute;height:100%;border-radius:99px;background:rgba(96,165,250,.45)}.fie-range-track b{position:absolute;top:-3px;width:3px;height:14px;background:#dbeafe}.fie-report-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:9px 0}.fie-report-grid section{border:1px solid var(--line);border-radius:10px;padding:9px;background:rgba(8,20,36,.45);font-size:11px}.fie-report-grid ul{margin:6px 0 0;padding-left:17px}.fie-lineage{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}.fie-lineage-chip{font-size:8px;border:1px solid #31547a;border-radius:999px;padding:3px 6px}.fie-lineage-chip.active{color:#86efac;border-color:#236a4d}.fie-lineage-chip.diagnostic{color:#fde68a;border-color:#786522}.fie-command-center{margin-top:2px}.fie-command-list{display:grid;gap:8px;margin-top:10px}.fie-command-item{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;border:1px solid var(--line);border-radius:11px;padding:9px 10px;background:rgba(6,16,30,.52)}.fie-command-item small{display:block;color:var(--muted);margin-top:2px;line-height:1.35}.fie-command-item strong{font-size:16px;white-space:nowrap}.fie-tag{font-size:9px;font-weight:800;letter-spacing:.08em;padding:4px 6px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}
@media(max-width:760px){.fie-action-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.fie-command-item{grid-template-columns:auto 1fr}.fie-command-item strong{grid-column:2;font-size:14px}.fie-command-center{padding:12px!important}}
`;document.head.appendChild(st);}

// ---------------------------------------------------------------------------
// Weekly matchup + season / chopped simulation
// ---------------------------------------------------------------------------

function activeWeek(){try{return Number((window.currentWeek||currentWeek)())||1;}catch{return 1;}}
function leagueRosterNameMap(){try{return rosterNameMap();}catch{return Object.fromEntries((state.rosters||[]).map(r=>[r.roster_id,`Roster ${r.roster_id}`]));}}
function rosterPoolFor(rid){try{return rosterPlayers(rid)||[];}catch{return PLAYERS.filter(p=>Number(p.ownerRosterId)===Number(rid)&&p.leagueEligible);}}

function playerDistribution(p){
  const mu=finite((window.weeklyLineupValue||weeklyLineupValue)(p))??0;
  const lo=finite(p.weeklyFloor),hi=finite(p.weeklyCeiling);
  let sd=(lo!==null&&hi!==null&&hi>lo)?(hi-lo)/(2*1.28155):Math.max(1.8,Math.abs(mu)*.34);
  sd=clampV(sd,1.25,Math.max(3,Math.abs(mu)*.8+2));
  return {mu:Math.max(0,mu),sd};
}

function bestBallTeamModel(pool,samples=260){
  const distributions=pool.map(p=>({p,...playerDistribution(p)})),vals=[],rng=rngFor(`${state.league?.league_id}|bestball|${pool.map(playerId).sort().join(',')}`),opt=window.optimizePoolByValue||optimizePoolByValue;
  for(let i=0;i<samples;i++){
    const sampled=new Map(distributions.map(x=>[playerId(x.p),Math.max(0,x.mu+normal(rng)*x.sd)]));
    try{vals.push(Number(opt(pool,p=>sampled.get(playerId(p))??0).starterTotal)||0);}catch{vals.push([...sampled.values()].reduce((a,b)=>a+b,0));}
  }
  const mu=meanV(vals)??0,sd=Math.sqrt(meanV(vals.map(x=>(x-mu)**2))??1);
  return {pool,starters:[],parts:distributions,mu,sd:Math.max(1,sd),empirical:vals,method:`Best Ball sampled optimal lineup (${samples} paths)`};
}
function teamModelFromPool(pool){
  let fp={};try{fp=window.formatProfile?.()||{};}catch{}
  if(fp.bestBall)return bestBallTeamModel(pool);
  let line;
  try{line=(window.optimizePoolByValue||optimizePoolByValue)(pool,p=>playerDistribution(p).mu);}catch{line={starterTotal:pool.reduce((s,p)=>s+playerDistribution(p).mu,0),starters:pool.map(p=>({player:p}))};}
  const starters=(line.starters||[]).map(x=>x.player||x).filter(Boolean),parts=starters.map(p=>({p,...playerDistribution(p)}));
  const mu=parts.reduce((s,x)=>s+x.mu,0);
  const variance=parts.reduce((s,x)=>s+x.sd*x.sd,0);
  // A modest shared game/team shock captures some teammate correlation without
  // pretending we have a fully calibrated covariance matrix yet.
  const teams={};for(const x of parts){const t=String(x.p.team||'FA');(teams[t]??=[]).push(x);}
  let corrVar=0;for(const xs of Object.values(teams))if(xs.length>1)corrVar+=Math.pow(xs.reduce((s,x)=>s+x.sd*.12,0),2);
  return {pool,starters,parts,mu,sd:Math.sqrt(Math.max(1,variance+corrVar)),method:'fixed optimal projected lineup distribution'};
}

function allTeamModels(rosterPoolsOverride=null){
  const out={};for(const r of state.rosters||[]){const pool=rosterPoolsOverride?.[r.roster_id]||rosterPoolFor(r.roster_id);out[r.roster_id]=teamModelFromPool(pool);}return out;
}

function sampleTeam(model,rng){
  if(model?.empirical?.length)return model.empirical[Math.floor(rng()*model.empirical.length)]??model.mu;
  // Team-level normal approximation is much faster for season simulations;
  // lineup selection remains exact at the model-building stage.
  return Math.max(0,model.mu+normal(rng)*model.sd);
}


function currentMatchupPair(rows,rid){
  const mine=(rows||[]).find(x=>Number(x.roster_id)===Number(rid));if(!mine)return null;
  const opp=(rows||[]).find(x=>Number(x.matchup_id)===Number(mine.matchup_id)&&Number(x.roster_id)!==Number(rid));
  return opp?{mine,opp}:null;
}

function matchupProbability(a,b,seed,n=5000){
  const rng=rngFor(seed),diff=[];let wins=0,ties=0;
  for(let i=0;i<n;i++){const x=sampleTeam(a,rng),y=sampleTeam(b,rng);diff.push(x-y);if(x>y)wins++;else if(x===y)ties++;}
  return {n,win:(wins+ties*.5)/n,medianMargin:qtile(diff,.5),p10Margin:qtile(diff,.1),p90Margin:qtile(diff,.9)};
}

function fixedLineupModel(starters){
  const parts=(starters||[]).map(p=>({p,...playerDistribution(p)})),mu=parts.reduce((s,x)=>s+x.mu,0),variance=parts.reduce((s,x)=>s+x.sd*x.sd,0),teams={};
  for(const x of parts){const t=String(x.p.team||'FA');(teams[t]??=[]).push(x);}let corrVar=0;for(const xs of Object.values(teams))if(xs.length>1)corrVar+=Math.pow(xs.reduce((s,x)=>s+x.sd*.12,0),2);
  return {pool:starters,starters,parts,mu,sd:Math.sqrt(Math.max(1,variance+corrVar)),method:'fixed legal lineup'};
}
function lineupSearch(pool,opponentModel,seed){
  let fp={};try{fp=window.formatProfile?.()||{};}catch{}if(fp.bestBall)return {best:null,candidates:[],automatic:true};
  const opt=window.optimizePoolByValue||optimizePoolByValue,lambdas=[-1.0,-.7,-.45,-.25,0,.2,.4,.65,.9,1.2],seen=new Set(),candidates=[];
  for(const lambda of lambdas){let line;try{line=opt(pool,p=>{const d=playerDistribution(p);return d.mu+lambda*d.sd;});}catch{continue;}const starters=(line.starters||[]).map(x=>x.player||x).filter(Boolean),key=starters.map(playerId).sort().join('|');if(!starters.length||seen.has(key))continue;seen.add(key);const model=fixedLineupModel(starters),prob=matchupProbability(model,opponentModel,`${seed}|lambda=${lambda}`,3200);candidates.push({lambda,starters,model,prob,mean:model.mu});}
  candidates.sort((a,b)=>b.prob.win-a.prob.win||b.mean-a.mean);const best=candidates[0]||null,meanCandidate=[...candidates].sort((a,b)=>b.mean-a.mean)[0]||null;
  return {best,meanCandidate,candidates,automatic:false};
}
function lineupChanges(base,best){
  if(!base||!best)return {ins:[],outs:[]};const a=new Map(base.starters.map(p=>[playerId(p),p])),b=new Map(best.starters.map(p=>[playerId(p),p]));return {ins:[...b].filter(([id])=>!a.has(id)).map(([,p])=>p),outs:[...a].filter(([id])=>!b.has(id)).map(([,p])=>p)};
}

function leagueRegularSeasonEnd(){
  const s=state.league?.settings||{},p=Number(s.playoff_week_start);if(Number.isFinite(p)&&p>1)return p-1;
  return 14;
}
function leaguePlayoffTeams(){const n=Number(state.league?.settings?.playoff_teams);return Number.isFinite(n)&&n>=2?n:6;}
function medianWinEnabled(){const s=state.league?.settings||{};return Number(s.league_average_match||s.median_match||s.extra_matchup_against_median||0)===1;}

async function fetchMatchupWeeks(start,end){
  const lid=state.league?.league_id;if(!lid)return {};
  const weeks=Array.from({length:Math.max(0,end-start+1)},(_,i)=>start+i),out={};
  await Promise.all(weeks.map(async w=>{try{out[w]=await fetchJSON(`https://api.sleeper.app/v1/league/${lid}/matchups/${w}`);}catch{out[w]=[];}}));
  return out;
}

function baseStandings(){
  const out={};for(const r of state.rosters||[]){const st=r.settings||{},dec=(finite(st.fpts_decimal)??0)/100;out[r.roster_id]={wins:Number(st.wins)||0,losses:Number(st.losses)||0,ties:Number(st.ties)||0,points:(Number(st.fpts)||0)+dec};}return out;
}

function rankStandings(st){return Object.entries(st).map(([id,x])=>({id:Number(id),...x})).sort((a,b)=>b.wins-a.wins||b.ties-a.ties||b.points-a.points||a.id-b.id);}

function playoffChampion(seedRows,models,rng){
  let alive=seedRows.map((x,i)=>({id:x.id,seed:i+1}));if(alive.length<2)return alive[0]?.id||null;
  while(alive.length>1){
    const n=alive.length,lowerPow=2**Math.floor(Math.log2(n)),byes=n-lowerPow,ordered=[...alive].sort((a,b)=>a.seed-b.seed),bye=ordered.slice(0,byes),play=ordered.slice(byes),next=[...bye];
    for(let i=0;i<Math.floor(play.length/2);i++){
      const a=play[i],b=play[play.length-1-i],sa=sampleTeam(models[a.id],rng),sb=sampleTeam(models[b.id],rng);next.push(sa>=sb?a:b);
    }
    if(play.length%2===1)next.push(play[Math.floor(play.length/2)]);
    alive=next;
  }
  return alive[0]?.id||null;
}

function simulateRedraftSeason(matchups,models,iterations=1600){
  const start=activeWeek(),end=leagueRegularSeasonEnd(),playoffN=Math.min(leaguePlayoffTeams(),(state.rosters||[]).length),base=baseStandings(),ids=(state.rosters||[]).map(r=>Number(r.roster_id)),counts=Object.fromEntries(ids.map(id=>[id,{playoffs:0,bye:0,title:0,rankSum:0,winsSum:0}]));
  const scheduleWeeks=[];for(let w=start;w<=end;w++)if((matchups[w]||[]).length)scheduleWeeks.push(w);
  for(let it=0;it<iterations;it++){
    const rng=rngFor(`${state.league?.league_id}|season|${start}|${it}`),st={};for(const id of ids)st[id]={...base[id]};
    for(const w of scheduleWeeks){
      const rows=matchups[w]||[],scores={};for(const id of ids)scores[id]=sampleTeam(models[id],rng);
      const groups={};for(const row of rows){const mid=String(row.matchup_id??`solo-${row.roster_id}`);(groups[mid]??=[]).push(Number(row.roster_id));}
      for(const g of Object.values(groups))if(g.length>=2){const [a,b]=g;if(scores[a]>scores[b]){st[a].wins++;st[b].losses++;}else if(scores[b]>scores[a]){st[b].wins++;st[a].losses++;}else{st[a].ties++;st[b].ties++;}st[a].points+=scores[a];st[b].points+=scores[b];}
      if(medianWinEnabled()){
        const med=qtile(ids.map(id=>scores[id]),.5);for(const id of ids){if(scores[id]>med)st[id].wins++;else if(scores[id]<med)st[id].losses++;else st[id].ties++;}
      }
    }
    const ranked=rankStandings(st),seeds=ranked.slice(0,playoffN),byeN=Math.max(0,playoffN-2**Math.floor(Math.log2(playoffN)));
    ranked.forEach((r,i)=>{counts[r.id].rankSum+=i+1;counts[r.id].winsSum+=r.wins;});
    seeds.forEach((r,i)=>{counts[r.id].playoffs++;if(i<byeN)counts[r.id].bye++;});
    const champ=playoffChampion(seeds,models,rng);if(champ)counts[champ].title++;
  }
  return {iterations,startWeek:start,endWeek:end,scheduleWeeks,playoffTeams:playoffN,rows:ids.map(id=>({rosterId:id,playoff:counts[id].playoffs/iterations,bye:counts[id].bye/iterations,title:counts[id].title/iterations,expectedRank:counts[id].rankSum/iterations,expectedWins:counts[id].winsSum/iterations}))};
}

function choppedBudgetMap(){const cap=Number(state.league?.settings?.waiver_budget)||100,out={};for(const r of state.rosters||[])out[r.roster_id]=Math.max(0,cap-(Number(r.settings?.waiver_budget_used)||0));return out;}
function releasedValue(p){try{const fn=window.playerDecisionValue||(typeof playerDecisionValue==='function'?playerDecisionValue:null);if(fn){const v=finite(fn(p));if(v!==null)return v;}}catch{}return finite(p.weeklyProjection)??finite(p.seasonScore)??0;}
function topReleased(pool,n=3){return [...pool].sort((a,b)=>releasedValue(b)-releasedValue(a)).slice(0,n);}
function addReleasedPlayers(survivors,pools,budgets,released,rng){
  for(const p of released){let best=null,bestBid=-1;const pm=playerDistribution(p).mu;for(const id of survivors){const before=teamModelFromPool(pools[id]).mu,after=teamModelFromPool(pools[id].concat(p)).mu,gain=Math.max(0,after-before),budget=budgets[id]||0;if(budget<=0)continue;const willingness=clampV(Math.round((gain/Math.max(1,pm))*28+rng()*12),0,budget),bid=willingness+rng()*.5;if(bid>bestBid){bestBid=bid;best={id,bid:willingness,gain};}}if(best&&best.bid>0){pools[best.id].push(p);budgets[best.id]=Math.max(0,budgets[best.id]-best.bid);}}
}
function simulateChopped(iterations=450,initialPoolsOverride=null){
  const ids=(state.rosters||[]).map(r=>Number(r.roster_id)),elim=Math.max(1,Number(state.leagueRules?.chopped?.eliminatedPerPeriod)||1),counts=Object.fromEntries(ids.map(id=>[id,{survive:[],winner:0,elimPeriod:0}])),initialPools=initialPoolsOverride||Object.fromEntries(ids.map(id=>[id,rosterPoolFor(id)])),baseBudgets=choppedBudgetMap();
  const maxPeriods=Math.ceil((ids.length-1)/elim);
  for(let it=0;it<iterations;it++){
    const rng=rngFor(`${state.league?.league_id}|chopped|${it}`),alive=[...ids],pools=Object.fromEntries(ids.map(id=>[id,initialPools[id].slice()])),budgets={...baseBudgets};let period=0;
    while(alive.length>1&&period<maxPeriods+2){period++;const scores=alive.map(id=>({id,score:sampleTeam(teamModelFromPool(pools[id]),rng)})).sort((a,b)=>a.score-b.score),n=Math.min(elim,Math.max(1,alive.length-1)),cut=scores.slice(0,n).map(x=>x.id),survivors=alive.filter(id=>!cut.includes(id));for(const id of survivors)counts[id].survive[period]=(counts[id].survive[period]||0)+1;for(const id of cut)counts[id].elimPeriod+=period;const released=[];for(const id of cut)released.push(...topReleased(pools[id],3));addReleasedPlayers(survivors,pools,budgets,released,rng);alive=survivors;}
    if(alive[0])counts[alive[0]].winner++;
  }
  return {iterations,eliminatedPerPeriod:elim,maxPeriods,rows:ids.map(id=>({rosterId:id,winner:counts[id].winner/iterations,meanElimPeriod:counts[id].elimPeriod/Math.max(1,iterations-counts[id].winner),survival:Array.from({length:maxPeriods},(_,i)=>(counts[id].survive[i+1]||0)/iterations)})),marketModel:'released top players are reallocated via heuristic FAAB willingness based on lineup gain and remaining budget; this redistribution is not yet historically calibrated'};
}

async function runLeagueSimulation(force=false){
  if(!state.league)return null;const week=activeWeek(),lid=String(state.league.league_id);if(Engine.leagueSim.loading)return Engine.leagueSim.data;if(!force&&Engine.leagueSim.data&&Engine.leagueSim.leagueId===lid&&Engine.leagueSim.week===week)return Engine.leagueSim.data;
  Engine.leagueSim={loading:true,error:null,data:null,leagueId:lid,week};renderMatchupPanel();
  try{
    const end=leagueRegularSeasonEnd(),matchups=await fetchMatchupWeeks(week,end),models=allTeamModels(),rid=Number(document.getElementById('weeklyRosterPicker')?.value||state.selectedRoster||selectedRoster()),pair=currentMatchupPair(matchups[week],rid),names=leagueRosterNameMap();let current=null;
    if(pair&&models[rid]&&models[pair.opp.roster_id]){current={rosterId:rid,opponentId:Number(pair.opp.roster_id),...matchupProbability(models[rid],models[pair.opp.roster_id],`${lid}|${week}|matchup`),myMean:models[rid].mu,oppMean:models[pair.opp.roster_id].mu,myName:names[rid]||`Roster ${rid}`,oppName:names[pair.opp.roster_id]||`Roster ${pair.opp.roster_id}`};current.lineupSearch=lineupSearch(rosterPoolFor(rid),models[pair.opp.roster_id],`${lid}|${week}|lineup`);}
    const fp=typeof window.formatProfile==='function'?window.formatProfile():{chopped:false};
    const strategic=fp.chopped?simulateChopped():simulateRedraftSeason(matchups,models);
    Engine.leagueSim={loading:false,error:null,data:{matchups,models,current,strategic,format:fp,chopped:!!fp.chopped,generatedAt:new Date().toISOString()},leagueId:lid,week};
  }catch(e){Engine.leagueSim={loading:false,error:String(e?.message||e),data:null,leagueId:lid,week};}
  renderMatchupPanel();return Engine.leagueSim.data;
}

function ensureMatchupPanel(){
  let p=document.getElementById('matchupSimPanel');if(p)return p;p=document.createElement('div');p.id='matchupSimPanel';p.className='card intel-panel';p.innerHTML='<div id="matchupSimContent"></div>';const anchor=document.getElementById('draftAssistantPanel')||document.getElementById('mainArea');anchor?.parentNode?.insertBefore(p,anchor);return p;
}
function renderMatchupPanel(){
  const p=ensureMatchupPanel(),active=state.activeTab==='matchupsim';p.classList.toggle('active',active);p.classList.toggle('hidden',!active);if(!active)return;document.getElementById('mainArea')?.classList.add('hidden');document.getElementById('weeklyControls')?.classList.add('hidden');
  const host=document.getElementById('matchupSimContent');if(!state.league){host.innerHTML='<div class="empty">Load a Sleeper league first.</div>';return;}const ls=Engine.leagueSim;if(ls.loading){host.innerHTML='<div class="eyebrow">Decision simulation</div><h2>Matchup & season outlook</h2><div class="notice">Loading matchup schedule and running simulations…</div>';return;}if(ls.error){host.innerHTML=`<div class="eyebrow">Decision simulation</div><h2>Matchup & season outlook</h2><div class="notice">Simulation unavailable: ${escV(ls.error)}</div><button id="rerunLeagueSim" class="btn">Retry</button>`;document.getElementById('rerunLeagueSim').onclick=()=>runLeagueSimulation(true);return;}if(!ls.data){host.innerHTML='<div class="eyebrow">Decision simulation</div><h2>Matchup & season outlook</h2><div class="subtitle">Transforms weekly player distributions into matchup, playoff, championship or chopped-survival probabilities.</div><button id="runLeagueSim" class="btn primary" style="margin-top:10px">Run league simulation</button>';document.getElementById('runLeagueSim').onclick=()=>runLeagueSimulation(true);return;}
  const d=ls.data,c=d.current,names=leagueRosterNameMap(),rid=Number(document.getElementById('weeklyRosterPicker')?.value||state.selectedRoster||selectedRoster());let top='';if(c)top=`<div class="draft-assist-grid"><div class="validation-card"><span class="filter-label">Projected score</span><div class="big">${fmtV(c.myMean)}</div><div class="tiny">${escV(c.myName)}</div></div><div class="validation-card"><span class="filter-label">Opponent</span><div class="big">${fmtV(c.oppMean)}</div><div class="tiny">${escV(c.oppName)}</div></div><div class="validation-card"><span class="filter-label">Win probability</span><div class="big">${Math.round(c.win*100)}%</div></div><div class="validation-card"><span class="filter-label">Median margin</span><div class="big">${c.medianMargin>=0?'+':''}${fmtV(c.medianMargin)}</div><div class="tiny">10–90% ${fmtV(c.p10Margin)} to ${fmtV(c.p90Margin)}</div></div></div>`;else top='<div class="notice">No paired Sleeper matchup was found for the selected roster/week. Season-level simulation can still run where future schedule rows exist.</div>';
  let lineup='';if(c?.lineupSearch?.automatic)lineup='<div class="notice" style="margin-top:10px"><b>Best Ball:</b> Start/Sit is automatic, so the simulation samples legal optimal lineups rather than recommending manual starters.</div>';else if(c?.lineupSearch?.best){const ls=c.lineupSearch,b=ls.best,m=ls.meanCandidate||b,ch=lineupChanges(m,b),edge=(b.prob.win-m.prob.win)*100,lab=b.lambda<-.1?'lower-variance / floor-leaning':b.lambda>.1?'higher-variance / upside-leaning':'mean-oriented';lineup=`<h3 style="margin:18px 0 6px">Matchup-aware lineup optimization</h3><div class="subtitle">Exact legal lineups are generated across a risk continuum and evaluated by simulated win probability, not only projected points.</div><div class="draft-assist-grid" style="margin-top:10px"><div class="validation-card"><span class="filter-label">Best win-prob lineup</span><div class="big">${Math.round(b.prob.win*100)}%</div><div class="tiny">${escV(lab)}</div></div><div class="validation-card"><span class="filter-label">Mean projection</span><div class="big">${fmtV(b.mean)}</div><div class="tiny">mean-optimal ${fmtV(m.mean)}</div></div><div class="validation-card"><span class="filter-label">Win-prob edge vs mean lineup</span><div class="big ${edge>=0?'positive':''}">${edge>=0?'+':''}${fmtV(edge,1)} pp</div></div><div class="validation-card"><span class="filter-label">Lineup changes</span><div class="big">${ch.ins.length}</div><div class="tiny">${ch.ins.length?`IN ${ch.ins.map(x=>escV(x.name)).join(' / ')} · OUT ${ch.outs.map(x=>escV(x.name)).join(' / ')}`:'same starters as mean-optimal'}</div></div></div><div class="notice" style="margin-top:8px"><b>Important:</b> a riskier lineup is recommended only when its modeled distribution increases the chance of beating this opponent. This is a simulation estimate and should be treated as directional until season-long calibration exists.</div>`;}
  let strategic='';if(d.chopped){const s=d.strategic,rows=[...s.rows].sort((a,b)=>b.winner-a.winner);strategic=`<h3 style="margin:18px 0 6px">Chopped survival simulation</h3><div class="subtitle">${s.iterations} league paths with ${s.eliminatedPerPeriod} elimination(s) per period and simulated redistribution of released talent.</div><div class="scroll" style="margin-top:10px"><table><thead><tr><th>Team</th><th>Win league</th><th>Survive 1</th><th>Survive 3</th><th>Survive 5</th><th>Mean elimination period*</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${escV(names[r.rosterId]||`Roster ${r.rosterId}`)}</b></td><td>${Math.round(r.winner*100)}%</td><td>${Math.round((r.survival[0]||0)*100)}%</td><td>${Math.round((r.survival[2]||0)*100)}%</td><td>${Math.round((r.survival[4]||0)*100)}%</td><td>${fmtV(r.meanElimPeriod,2)}</td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:10px"><b>Current limitation:</b> ${escV(s.marketModel)}. The elimination mechanism itself is simulated directly; the post-chop FAAB market is intentionally labelled heuristic until league-history calibration is added.</div>`;}else{const s=d.strategic,rows=[...s.rows].sort((a,b)=>b.title-a.title),bb=!!d.format?.bestBall;strategic=`<h3 style="margin:18px 0 6px">${bb?'Best Ball season leverage':'Season leverage'}</h3><div class="subtitle">${s.iterations} current-strength season paths across Sleeper matchup weeks ${s.startWeek}–${s.endWeek}. ${bb?'Each team score is sampled from an automatically optimized Best Ball lineup distribution; ':''}Playoff ranking uses wins then points; ${medianWinEnabled()?'league-median wins are included':'no median-win rule detected'}.</div><div class="scroll" style="margin-top:10px"><table><thead><tr><th>Team</th><th>Expected wins</th><th>Expected rank</th><th>Playoffs</th><th>Bye</th><th>Championship</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${escV(names[r.rosterId]||`Roster ${r.rosterId}`)}</b></td><td>${fmtV(r.expectedWins,2)}</td><td>${fmtV(r.expectedRank,2)}</td><td>${Math.round(r.playoff*100)}%</td><td>${Math.round(r.bye*100)}%</td><td>${Math.round(r.title*100)}%</td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:10px"><b>Interpretation:</b> these are current-roster/current-strength probabilities, not yet a full rest-of-season player forecast. They are useful for measuring matchup and transaction leverage, but future injuries, byes and role changes will be added as week-specific distributions become available.</div>`;}
  host.innerHTML=`<div class="eyebrow">Decision simulation</div><h2 style="margin:4px 0 5px">Matchup & ${d.chopped?'Survival':'Playoff'} Engine <span class="badge">Beta</span></h2><div class="subtitle">Optimizes the league objective rather than only raw player points: win this matchup, survive a chopped week, make the playoffs, or win the league.</div>${top}${lineup}${strategic}<button id="rerunLeagueSim" class="btn" style="margin-top:12px">Re-run simulation</button>`;document.getElementById('rerunLeagueSim').onclick=()=>runLeagueSimulation(true);
}

function wrapGlobalRender(){const prev=window.render;if(typeof prev!=='function'||prev.__fieDecisionGlobalWrapped)return;function wrapped(){const r=prev.apply(this,arguments);try{renderMatchupPanel();renderStrategicWaiverPanel();renderCommandCenter();if(state.activeTab==='matchupsim'&&!Engine.leagueSim.data&&!Engine.leagueSim.loading)runLeagueSimulation(false);}catch(e){console.warn('FIE decision simulation layer',e);}return r;}wrapped.__fieDecisionGlobalWrapped=true;window.render=wrapped;}

function wrapDraftRenderer(){
  const prev=window.renderDraftAssistant;if(typeof prev!=='function'||prev.__fieDecisionWrapped)return;
  function wrapped(){const r=prev.apply(this,arguments);try{draftPanel();for(const tr of document.querySelectorAll('#draftAssistantSummary .draft-assistant-table tbody tr[data-player-id]')){if(tr.dataset.fiePlayerBound)continue;tr.dataset.fiePlayerBound='1';tr.style.cursor='pointer';tr.tabIndex=0;tr.setAttribute('role','button');tr.setAttribute('aria-label',`Open details for ${tr.children[1]?.textContent?.trim()||'player'}`);const open=()=>window.openDrawer?.(tr.dataset.playerId);tr.addEventListener('click',e=>{if(e.target.closest('button,input,select,a'))return;open();});tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});}}catch(e){console.warn('FIE draft simulation panel',e);}return r;}
  wrapped.__fieDecisionWrapped=true;window.renderDraftAssistant=wrapped;
}

function bind(){injectDecisionStyles();wrapDraftRenderer();wrapGlobalRender();ensureMatchupPanel();const prevDrawer=window.openDrawer;if(typeof prevDrawer==='function'&&!prevDrawer.__fieExplainWrapped){const w=function(id){const r=prevDrawer.apply(this,arguments);try{augmentDrawer(id);}catch(e){console.warn('FIE drawer explanation',e);}return r;};w.__fieExplainWrapped=true;window.openDrawer=w;}const tradeBtn=document.getElementById('evaluateTradeBtn'),baseTrade=window.evaluateTrade;if(tradeBtn&&typeof baseTrade==='function'){tradeBtn.onclick=()=>{baseTrade();appendTradeCounterparty();};}try{draftPanel();renderMatchupPanel();renderStrategicWaiverPanel();renderCommandCenter();}catch{} }
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();

Engine.commandCenterItems=commandCenterItems;Engine.portfolioSnapshot=portfolioSnapshot;Engine.runDraftMonteCarlo=runDraftMonteCarlo;Engine.runDraftMonteCarloAsync=runDraftMonteCarloAsync;Engine.cancelDraftMonteCarlo=cancelDraftMonteCarlo;Engine.renderDraftPanel=draftPanel;Engine.runLeagueSimulation=runLeagueSimulation;Engine.renderMatchupPanel=renderMatchupPanel;Engine.renderStrategicWaiverPanel=renderStrategicWaiverPanel;Engine.renderCommandCenter=renderCommandCenter;Engine.counterpartyTradeFit=counterpartyTradeFit;Engine.lineupSearch=lineupSearch;Engine.simulateRedraftSeason=simulateRedraftSeason;Engine.simulateChopped=simulateChopped;Engine.__formatInternals={monteCarloFormat,workerPlayerRecord,monteCarloWorkerContext};window.FIEDecisionEngines=Engine;
})();
