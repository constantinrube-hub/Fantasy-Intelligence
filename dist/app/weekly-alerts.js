/* FIE Weekly starter alert (R0 · WP0.5) — UI contract §5.4 / §5.8.
 *
 * Classic Weekly shows an *optimal* lineup, not what is actually submitted in
 * Sleeper. This module reads the submitted starters for the selected roster and
 * week and raises one red alert when a starter cannot play (Doubtful, Out, IR,
 * Suspended, PUP, NA, verified BYE) or a starting slot is empty.
 *
 * Read-only: it renders a notice; it never changes projections, lineups or
 * recommendations. Best Ball leagues are skipped (no manual lineup).
 * Requests go through FIEDataClient (CHANGE_GUIDE rule 4).
 */
(function(){
'use strict';
const VERSION='10.0.0-r0';
const S=()=>window.state||{};
let token=0,timer=null;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function week(){const w=Number(window.currentWeek?.()||S().weekly?.week);return Number.isFinite(w)&&w>=1&&w<=18?w:null;}
function isBestBall(){try{return !!window.formatProfile?.()?.bestBall;}catch{return false;}}
function starterSlots(){
  const pos=S().league?.roster_positions||[];
  try{const slots=window.FIECore?.PositionRegistry?.starterSlots?.(pos);if(Array.isArray(slots)&&slots.length)return slots;}catch{}
  return pos.filter(x=>!['BN','IR','TAXI','RES'].includes(String(x).toUpperCase()));
}
function host(){
  let el=document.getElementById('fieStarterAlert');
  if(!el){
    const main=document.getElementById('mainArea');if(!main)return null;
    el=document.createElement('div');el.id='fieStarterAlert';el.setAttribute('role','alert');el.hidden=true;
    el.style.cssText='margin:0 0 10px;padding:10px 12px;border:1px solid #b4232f;border-left-width:4px;border-radius:10px;background:rgba(180,35,47,.12);font-size:13px;line-height:1.45';
    const anchor=document.getElementById('fie93WeeklyPanel')||document.getElementById('filters');
    if(anchor&&anchor.parentElement===main)main.insertBefore(el,anchor);else main.insertBefore(el,main.firstChild);
  }
  return el;
}
function hide(){const el=document.getElementById('fieStarterAlert');if(el){el.hidden=true;el.innerHTML='';}}
async function evaluate(){
  const st=S(),league=st.league,rid=Number(st.selectedRoster),w=week();
  if(st.activeTab!=='startsit'||!league?.league_id||!rid||!w||isBestBall()){hide();return;}
  const my=++token,lid=String(league.league_id);
  let matchups;
  try{matchups=await window.FIEDataClient.json(`https://api.sleeper.app/v1/league/${lid}/matchups/${w}`,{sourceId:'weekly-starter-alert',ttlMs:120000});}
  catch{if(my===token)hide();return;}
  if(my!==token||String(S().league?.league_id||'')!==lid||Number(S().selectedRoster)!==rid||week()!==w)return; // stale response
  const mine=(Array.isArray(matchups)?matchups:[]).find(m=>Number(m.roster_id)===rid);
  if(!mine||!Array.isArray(mine.starters)){hide();return;}
  const slots=starterSlots(),byId=new Map((window.PLAYERS||[]).map(p=>[String(p.sleeperId||''),p]));
  const out=[],empty=[];let doubtful=false;
  mine.starters.forEach((pid,i)=>{
    const slot=slots[i]||'Starter',id=String(pid??'');
    if(!id||id==='0'){empty.push(slot);return;}
    const p=byId.get(id);if(!p)return;
    const s=window.FIEStatus?.resolve?.(p,{week:w})||null;
    if(s?.unavailable){out.push({p,slot,s});if(s.code==='Doubtful')doubtful=true;}
  });
  const el=host();if(!el)return;
  if(!out.length&&!empty.length){hide();return;}
  const parts=[];
  if(out.length)parts.push(`<b>${out.length} submitted starter${out.length>1?'s':''} can't play this week:</b> ${out.map(x=>`${esc(x.p.name)} (${esc(x.slot)} · ${esc(x.s.code)})`).join(', ')}.`);
  if(empty.length)parts.push(`<b>Empty starting slot${empty.length>1?'s':''}:</b> ${empty.map(esc).join(', ')}.`);
  parts.push(`Your Sleeper lineup for Week ${w}. Check the bench below and change the lineup in Sleeper before lock.`);
  if(doubtful)parts.push('Doubtful is treated as out; inactives are announced about 90 minutes before kickoff.');
  el.innerHTML=parts.join(' ');el.hidden=false;
}
function schedule(ms=250){clearTimeout(timer);timer=setTimeout(()=>{evaluate().catch(()=>{});},ms);}
['fie:weekly-fast-path-ready','fie:league-loaded','fie:league-live-update'].forEach(n=>window.addEventListener(n,()=>schedule(400)));
window.addEventListener('fie:league-changing',()=>{token++;hide();});
document.addEventListener('click',e=>{if(e.target?.closest?.('[data-tab],[data-section],#portfolioHomeBtn'))schedule(350);},true);
document.addEventListener('change',e=>{if(['weekSelect','weeklyRosterPicker','rosterPicker'].includes(e?.target?.id))schedule(300);},true);
window.FIEWeeklyAlerts={VERSION,refresh:()=>schedule(0)};
})();
