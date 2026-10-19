/* FIE UI v10 kit (R1 · WP1.2) — small rendering helpers shared by every v10 view.
 *
 * Layering (UI contract §3): Basic is the always-visible row; Expand is a native <details> on
 * that row (several can be open at once); Advanced is a nested <details class="v10-adv"> that
 * only exists inside an Expand. Labels for projection sources appear only in Expand/Advanced;
 * Basic shows the active value as the number, plus at most one governance dot.
 * Dots: none = active value is the primary source and fresh; green = better than primary;
 * amber = weaker than primary, stale, or an uncalibrated estimate (e.g. win estimate).
 * Pure string builders; no state, no network.
 */
(function(){
'use strict';
const VERSION='10.1.0';
const TZ=(()=>{try{return Intl.DateTimeFormat().resolvedOptions().timeZone||'Europe/Berlin';}catch{return 'Europe/Berlin';}})();
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function pts(v,d=1){const n=num(v);return n===null?'–':n.toFixed(d);}
function signed(v,d=1){const n=num(v);return n===null?'–':`${n>=0?'+':'−'}${Math.abs(n).toFixed(d)}`;}
function pct(v){const n=num(v);return n===null?'–':`${Math.round(n*100)}%`;}
/** Win estimate display: the spread is not calibrated yet (WP-V1), so tails are shown as <5% / >95%. */
function winPct(v){const n=num(v);if(n===null)return '–';if(n<.05)return '<5%';if(n>.95)return '>95%';return `${Math.round(n*100)}%`;}
function time(ms,{weekday=true}={}){if(!ms)return '–';try{return new Intl.DateTimeFormat(undefined,{timeZone:TZ,weekday:weekday?'short':undefined,hour:'2-digit',minute:'2-digit'}).format(new Date(ms));}catch{return new Date(ms).toISOString().slice(0,16).replace('T',' ');}}
function clock(ms){if(!ms)return '–';try{return new Intl.DateTimeFormat(undefined,{timeZone:TZ,hour:'2-digit',minute:'2-digit'}).format(new Date(ms));}catch{return '';}}
function until(ms,now=Date.now()){if(!ms)return '';const d=ms-now;if(d<=0)return 'locked';const m=Math.round(d/60000);if(m<60)return `in ${m} min`;const h=Math.floor(m/60);if(h<48)return `in ${h} h ${m%60} min`;return `in ${Math.floor(h/24)} d ${h%24} h`;}
const DOT_TITLE={green:'Stronger than the primary source',amber:'Weaker than the primary source, stale, or an uncalibrated estimate'};
function dot(color,title){return color?`<span class="v10-dot v10-dot-${esc(color)}" title="${esc(title||DOT_TITLE[color]||'')}" aria-label="${esc(title||DOT_TITLE[color]||'')}"></span>`:'';}
const TIER_LABEL={urgent:'Urgent',recommended:'Recommended',monitor:'Monitor',close:'Close call'};
function tierChip(tier){return `<span class="v10-chip v10-tier-${esc(tier)}">${esc(TIER_LABEL[tier]||tier)}</span>`;}
function statusChip(status){if(!status||!status.code)return '';const cls=status.unavailable?'out':status.monitor?'q':'info';return `<span class="v10-chip v10-st-${cls}" title="${esc(status.label||status.code)}${status.source?` · ${esc(status.source)}`:''}">${esc(status.short||status.code)}</span>`;}
const FORMAT_SHORT={REDRAFT:'Redraft',DYNASTY:'Dynasty',CHOPPED:'Chopped',REDRAFT_BESTBALL:'Best Ball',DYNASTY_BESTBALL:'Dynasty BB',CHOPPED_BESTBALL:'Chopped BB'};
function formatChip(key){return `<span class="v10-chip v10-fmt">${esc(FORMAT_SHORT[key]||key||'')}</span>`;}
function gameText(g){if(!g)return '';if(g.bye)return 'BYE';const opp=g.opp?`${g.homeAway||'vs'} ${g.opp}`:'';const st=g.state==='final'?'Final':g.state==='live'?'Live':g.state==='ended_unconfirmed'?'Ended':g.kickoff?time(g.kickoff):'';return [opp,st].filter(Boolean).join(' · ');}
/** Expand row: summary = Basic content (string), body = Expand content, adv = Advanced content (optional).
 *  key = stable identity so repaint() can keep the row open across live re-renders. */
function expand(summary,body,{adv='',cls='',open=false,attrs='',key=''}={}){
  const k=key?` data-k="${esc(key)}"`:'',ka=key?` data-k="${esc(key)}:adv"`:'';
  return `<details class="v10-x ${esc(cls)}"${k}${open?' open':''} ${attrs}><summary>${summary}</summary><div class="v10-xbody">${body}${adv?`<details class="v10-adv"${ka}><summary>Advanced</summary><div class="v10-advbody">${adv}</div></details>`:''}</div></details>`;
}
/** Replace root's content, keeping every keyed <details> that was open still open. */
function repaint(root,html){
  const open=new Set([...root.querySelectorAll('details[data-k][open]')].map(d=>d.dataset.k));
  const y=window.scrollY;root.innerHTML=html;
  for(const d of root.querySelectorAll('details[data-k]'))if(open.has(d.dataset.k))d.open=true;
  if(Math.abs(window.scrollY-y)>2)window.scrollTo(0,y);
}
function kv(rows){return `<dl class="v10-kv">${rows.filter(r=>r&&r[1]!==undefined&&r[1]!==null&&r[1]!=='').map(([k,v])=>`<dt>${esc(k)}</dt><dd>${v}</dd>`).join('')}</dl>`;}
function empty(text){return `<div class="v10-empty">${esc(text)}</div>`;}
function sourceLabel(active){const m={SLEEPER:'Sleeper weekly projection (league scoring)',FIE_GOVERNED:'FIE governed projection',FIE_WEEKLY:'FIE weekly model',BYE:'Verified bye week (schedule)',ESTIMATE:'Labelled estimate',UNAVAILABLE:'No projection available'};return m[active?.tier]||active?.tier||'–';}
/** Player expand body + advanced for any view (identical everywhere by construction). */
function playerDetail(p,wm){
  if(!p)return{body:'',adv:''};
  const body=kv([['Game',esc(gameText(p.game))||'–'],['Status',p.status?.code?`${esc(p.status.label||p.status.code)}${p.status.unavailable?' — not counted':''}`:'Active'],
    ['Typical range',p.range?`${pts(p.range.low)}–${pts(p.range.high)} <span class="v10-muted">(rule-of-thumb, not calibrated)</span>`:'–'],
    ['Source',`${esc(sourceLabel(p.active))}${p.active?.dot?' '+dot(p.active.dot):''}`],
    ...(p.alternatives||[]).map(a=>[a.label,`${pts(a.value)} <span class="v10-muted">(inactive)</span>`])]);
  const rows=(window.FIEScoringCore?.breakdown?.(p.stats,wm?.league?.scoring||{},p.position)||[]).slice(0,8);
  const adv=kv([['Projection age',p.active?.ageMin!==null&&p.active?.ageMin!==undefined?`${p.active.ageMin} min`:'–'],['Primary source',esc(p.active?.primary||'–')],['Status source',esc(p.status?.source||'–')],['Sleeper ID',esc(p.pid)],['Lock',p.game?.locked?'locked':esc(until(p.game?.kickoff))]])+
    (rows.length?`<table class="v10-mini"><thead><tr><th>Scoring rule</th><th>Stat</th><th>×</th><th>Pts</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.key)}</td><td>${pts(r.stat,2)}</td><td>${esc(r.weight)}</td><td>${pts(r.points,2)}</td></tr>`).join('')}</tbody></table>`:'');
  return{body,adv};
}
window.FIEV10Kit={VERSION,TZ,esc,num,pts,signed,pct,winPct,time,clock,until,dot,tierChip,statusChip,formatChip,gameText,expand,repaint,kv,empty,sourceLabel,playerDetail,TIER_LABEL};
})();
