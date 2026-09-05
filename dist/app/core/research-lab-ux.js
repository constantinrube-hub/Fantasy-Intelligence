/* FIE Research/Lab navigation and freshness presentation. Display-only. */
(function(){
'use strict';
const contract={"schema":"fie-research-lab-ux-v1","version":"1.0.0","navigation_groups":[{"id":"evidence","label":"Evidence & validation","routes":["validation","research","research2","research3","research4"]},{"id":"decision_evidence","label":"Decision evidence","routes":["research5"]},{"id":"production_data","label":"Production & data","routes":["research6","features","model"]}],"freshness_states":{"current":"Available evidence is within the configured maximum age.","aging":"Available evidence is within the configured maximum age but approaching it.","stale":"Evidence is older than the configured maximum age and must not be presented as current.","unavailable":"The source explicitly reports no available evidence.","unknown":"No trustworthy as-of timestamp is available."},"invariants":["Freshness is display-only and never changes evidence availability, scores, ranks, recommendations, or promotion decisions.","All milestone and diagnostics routes remain addressable by their existing route IDs.","The League Research Report remains league-scoped evidence and never owns canonical ranking.","Future or invalid timestamps are shown as unknown rather than current."]};
function deepFreeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.values(value).forEach(deepFreeze);Object.freeze(value);}return value;}
deepFreeze(contract);
const finite=v=>v===null||v===undefined||String(v).trim()===''?null:(Number.isFinite(Number(v))?Number(v):null);
function describe({asOf=null,available=true,maxAgeHours=24,now=Date.now()}={}){
 const max=finite(maxAgeHours),at=Date.parse(String(asOf||'')),clock=finite(now);
 if(available===false)return Object.freeze({state:'unavailable',label:'Unavailable',className:'unavailable',asOf:null,ageHours:null,maxAgeHours:max});
 if(!Number.isFinite(at)||clock===null||at>clock+60000)return Object.freeze({state:'unknown',label:'Freshness unknown',className:'unknown',asOf:null,ageHours:null,maxAgeHours:max});
 const ageHours=Math.max(0,(clock-at)/36e5),limit=max!==null&&max>0?max:24;
 const state=ageHours>limit?'stale':ageHours>=limit*.75?'aging':'current';
 const labels={current:'Current',aging:'Aging',stale:'Needs refresh'};
 return Object.freeze({state,label:labels[state],className:state,asOf:new Date(at).toISOString(),ageHours,maxAgeHours:limit});
}
function isFresh(input){const x=describe(input);return x.state==='current'||x.state==='aging';}
function ageLabel(hours){if(!Number.isFinite(hours))return'';if(hours<1)return`${Math.max(0,Math.round(hours*60))}m old`;if(hours<48)return`${Math.round(hours)}h old`;return`${Math.round(hours/24)}d old`;}
function timestampLabel(input){const x=describe(input);if(!x.asOf)return x.label;return`${x.label} · ${ageLabel(x.ageHours)} · as of ${x.asOf.replace('T',' ').replace('.000Z','Z')}`;}
function weeklyLabel({season=null,week=null,...input}={}){
 const context=[finite(season)!==null?`Season ${Number(season)}`:null,finite(week)!==null?`Week ${Number(week)}`:null].filter(Boolean).join(' · ');
 return`${context?context+' · ':''}${timestampLabel(input)}`;
}
function overviewFreshness(){
 const host=document.getElementById('labFreshnessSummary');if(!host)return;
 const current=window.FIE_M5?.getCurrentBundle?.()||null,governance=window.FIE_M6_GOVERNANCE_STATE||null,cur=governance?.current_snapshot||{},asOf=current?.generated_at||cur.generated_at||null,maxAgeHours=cur.max_age_hours||18,available=!!current||!!cur.generated_at;
 const x=describe({asOf,available,maxAgeHours});host.className=`lab-freshness ${x.className}`;
 host.innerHTML=`<b>${weeklyLabel({season:current?.season||cur.season,week:current?.week||cur.week,asOf,available,maxAgeHours})}</b><span>Freshness is evidence context only; activation and recommendations keep their existing fail-closed gates.</span>`;
}
function clearOverview(){const host=document.getElementById('labFreshnessSummary');if(host){host.className='lab-freshness unknown';host.innerHTML='<b>Switching league…</b><span>Waiting for league-scoped research evidence.</span>';}}
window.FIEFreshness=Object.freeze({VERSION:'1.0.0',contract,describe,isFresh,ageLabel,timestampLabel,weeklyLabel});
window.FIEResearchLabUX=Object.freeze({VERSION:'1.0.0',contract,renderOverview:overviewFreshness});
window.addEventListener?.('fie:league-changing',clearOverview);window.addEventListener?.('fie:league-loaded',overviewFreshness);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',overviewFreshness,{once:true});else overviewFreshness();
})();
