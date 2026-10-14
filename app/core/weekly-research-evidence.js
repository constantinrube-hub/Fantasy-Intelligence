/* Read-only lazy research view. No projection, rank or advice mutations. */
(function(){
'use strict';
let epoch=0;
const flags=['activation_eligible','forecast_eligible','ranking_eligible','recommendation_eligible','transaction_eligible'];
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=x=>x===null||x===undefined||x===''||typeof x==='boolean'?null:Number.isFinite(Number(x))?Number(x):null;
const context=()=>{const s=window.state||{},m=window.FIE_M5?.getCurrentBundle?.();return{leagueId:String(window.FIELeagueContext?.current?.()?.leagueId||s.league?.league_id||''),season:number(m?.season),week:number(m?.week),signature:String(m?.scoring_signature||''),scoring:JSON.stringify(s.league?.scoring_settings||{})};};
const key=c=>JSON.stringify(c);
const sameScoring=(a,b)=>JSON.stringify(Object.entries(a||{}).sort())===JSON.stringify(Object.entries(b||{}).sort());
function reset(){epoch++;const host=document.getElementById('weeklyResearchEvidence');if(host)host.innerHTML='';}
function time(x){if(typeof x!=='string'||!/(Z|[+-]\d\d:\d\d)$/.test(x)||!Number.isFinite(Date.parse(x)))throw new Error('Research timestamp unavailable');return Date.parse(x);}
function validate(value,c,core){
 if(c.week>16)throw new Error('A complete same-season three-week horizon is unavailable');
 if(value?.schema!=='fie-weekly-research-view-v1'||value.pointer_replaceable!==true||value.season!==c.season||value.week!==c.week||JSON.stringify(value.target_weeks)!==JSON.stringify([c.week,c.week+1,c.week+2]))throw new Error('Research week or horizon mismatch');
 if(flags.some(k=>value[k]!==false))throw new Error('Research authority mismatch');
 const generated=time(value.generated_at);if(generated>Date.now()+60000)throw new Error('Future research view');
 if(!sameScoring(core?.sleeper?.league?.scoring_settings,window.state?.league?.scoring_settings))throw new Error('Current scoring settings changed');
 if(String(core?.league_id)!==c.leagueId||String(core?.scoring_signature||'')!==c.signature)throw new Error('Research scoring context mismatch');
 for(const ref of Object.values(value.bindings||{})){if(!/^[a-f0-9]{64}$/.test(ref.sha256)||typeof ref.path!=='string'||!ref.path.startsWith('data/research/prospective/')||ref.path.split('/').includes('..')||time(ref.observed_at)>generated)throw new Error('Research source binding mismatch');}
 const matches=(value.leagues||[]).filter(l=>String(l.league_id)===c.leagueId);if(matches.length!==1)throw new Error('Research league unavailable');
 const l=matches[0];if(l.scoring_signature!==c.signature||l.season!==c.season||l.week!==c.week||flags.some(k=>l[k]!==false)||time(l.observed_at)>generated||l.sleeper_comparison!==false||l.baseline_id!=='SAME_CUTOFF_FP_PRIOR_4')throw new Error('Research league boundary mismatch');
 if(l.forecast_observed_at!==null&&(time(l.forecast_observed_at)>generated||time(l.forecast_observed_at)>=time(l.first_kickoff)))throw new Error('Research forecast timing mismatch');
 const seen=new Set();for(const r of l.forecasts||[]){const id=String(r.canonical_player_id)+':'+r.position;if(seen.has(id)||!r.canonical_player_id||!['QB','RB','WR','TE'].includes(r.position))throw new Error('Research identity mismatch');seen.add(id);if(r.confidence!==null||['forecast_mean','baseline_mean'].some(k=>r[k]!==null&&number(r[k])===null))throw new Error('Research value unavailable');}
 return l;
}
function render(l){const fmt=x=>number(x)===null?'—':number(x).toFixed(2);return `<p>Research only · ${esc(l.status)} · Weeks ${l.week}–${l.week+2}</p><p>Capture: ${esc(l.forecast_observed_at||'Unavailable')}. Scope: ${esc(l.forecast_scope||'Unavailable')}. Scoring profile observed: ${esc(l.observed_at)}.</p><p>Baseline: recent production. Eligibility remains blocked. Actual adoption: ${esc(l.actual_adoption)}.</p><table><thead><tr><th>Player identity</th><th>Position</th><th>Three-week mean</th><th>Recent production</th><th>State</th></tr></thead><tbody>${(l.forecasts||[]).map(r=>`<tr><td>${esc(r.canonical_player_id)}</td><td>${esc(r.position)}</td><td>${fmt(r.forecast_mean)}</td><td>${fmt(r.baseline_mean)}</td><td>${esc(r.status)}</td></tr>`).join('')}</tbody></table>`;}
async function load(){const host=document.getElementById('weeklyResearchEvidence');if(!host)return null;const c=context(),token=++epoch;if(!c.leagueId||!c.signature||!c.season||!c.week){host.textContent='Load a current league snapshot to inspect evidence.';return null;}host.textContent='Loading research evidence…';try{const client=window.FIEDataClient;if(!client?.json)throw new Error('Research transport unavailable');const opts={cache:'no-store',persist:false,sourceId:'weekly-research-evidence'};const [core,value]=await Promise.all([client.json(`data/research/leagues/${encodeURIComponent(c.leagueId)}/app/core.json`,opts),client.json(`data/research/prospective/weekly-research-view/${c.season}/week_${String(c.week).padStart(2,'0')}.json`,opts)]);if(token!==epoch||key(c)!==key(context()))return null;const league=validate(value,c,core);host.innerHTML=render(league);return league;}catch(error){if(token===epoch&&key(c)===key(context()))host.textContent=`Research evidence unavailable: ${error.message}`;return null;}}
window.addEventListener?.('fie:league-changing',reset);window.addEventListener?.('fie:league-loaded',reset);window.addEventListener?.('fie:league-live-update',reset);
document.addEventListener?.('click',e=>{if(e.target.closest?.('[data-weekly-research-evidence]'))load();});
window.FIEWeeklyResearchEvidence=Object.freeze({load,validate,render,invalidate:reset});
})();
