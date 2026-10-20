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
const VERSION='10.5.0';
const TZ=(()=>{try{return Intl.DateTimeFormat().resolvedOptions().timeZone||'Europe/Berlin';}catch{return 'Europe/Berlin';}})();
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function pts(v,d=1){const n=num(v);return n===null?'–':n.toFixed(d);}
function signed(v,d=1){const n=num(v);return n===null?'–':`${n>=0?'+':'−'}${Math.abs(n).toFixed(d)}`;}
function pct(v){const n=num(v);return n===null?'–':`${Math.round(n*100)}%`;}
/** Win estimate display: a normal approximation (spread calibrated in-sample, WP-V1); tails are shown as <5% / >95%. */
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
// Human labels for the projected stat line (Advanced §5.2 item 1); other keys show raw.
const STAT_LABEL={pass_att:'pass att',pass_cmp:'cmp',pass_yd:'pass yd',pass_td:'pass TD',pass_int:'INT',rush_att:'rush att',rush_yd:'rush yd',rush_td:'rush TD',rec_tgt:'targets',rec:'rec',rec_yd:'rec yd',rec_td:'rec TD',fum_lost:'fum lost',
  fgm:'FG made',fgm_0_19:'FG 0–19',fgm_20_29:'FG 20–29',fgm_30_39:'FG 30–39',fgm_40_49:'FG 40–49',fgm_50p:'FG 50+',fgmiss:'FG miss',xpm:'XP',xpmiss:'XP miss',
  sack:'sacks',int:'INT',fum_rec:'fum rec',def_td:'def TD',pts_allow:'pts allowed',yds_allow:'yds allowed',safe:'safety',blk_kick:'blocked kicks',
  idp_tkl_solo:'solo tkl',idp_tkl_ast:'ast tkl',idp_tkl:'tackles',idp_sack:'sacks',idp_int:'INT',idp_ff:'FF',idp_pass_def:'PD',idp_qb_hit:'QB hits',idp_tkl_loss:'TFL'};
const STAT_ORDER=Object.keys(STAT_LABEL);
function statLine(stats){
  if(!stats)return '';const xs=Object.entries(stats).filter(([k,v])=>STAT_LABEL[k]&&Number(v)!==0&&Number.isFinite(Number(v)));
  xs.sort((a,b)=>STAT_ORDER.indexOf(a[0])-STAT_ORDER.indexOf(b[0]));
  return xs.length?`<div class="v10-statline">${xs.map(([k,v])=>`<span><b>${Number(v)>=10?Math.round(Number(v)):Number(v).toFixed(1)}</b> ${esc(STAT_LABEL[k])}</span>`).join('')}</div>`:'';
}
/** Name that opens the shared player reader (WP2.2). */
function playerLink(p,{leagueId=''}={}){return p?`<a class="v10-plink" href="#" data-v10-player="${esc(p.pid)}" data-v10-league="${esc(leagueId)}">${esc(p.name)}</a>`:'';}
/** Player expand body + advanced for any view (identical everywhere by construction).
 *  Advanced order (UI contract §5.2): stat line → scoring → distribution → lineup context → provenance. */
function playerDetail(p,wm){
  if(!p)return{body:'',adv:''};
  const body=kv([['Game',esc(gameText(p.game))||'–'],['Status',p.status?.code?`${esc(p.status.label||p.status.code)}${p.status.unavailable?' — not counted':''}`:'Active'],
    [p.range?.calibrated?'P10–P90':'Typical range',p.range?`${pts(p.range.low)}–${pts(p.range.high)} <span class="v10-muted">${p.range.calibrated?`(calibrated, n=${esc(p.range.n)})`:'(rule-of-thumb, not calibrated)'}</span>`:'–'],
    ['Source',`${esc(sourceLabel(p.active))}${p.active?.dot?' '+dot(p.active.dot):''}`],
    ...(p.alternatives||[]).map(a=>[a.label,`${pts(a.value)} <span class="v10-muted">(inactive)</span>`])])+(p.alternatives?.length?'':'<div class="v10-muted">No alternative projection differs.</div>');
  const rows=(window.FIEScoringCore?.breakdown?.(p.stats,wm?.league?.scoring||{},p.position)||[]).slice(0,10);
  const d=p.active?.value!==null&&p.active?.value!==undefined?window.FIEDistribution?.player?.({mu:p.active.value,low:p.range?.low,high:p.range?.high}):null;
  const ctx=wm?.lineupContext?.(p.pid)||null;
  const ctxTxt=!ctx?'–':ctx.role==='starter'?`In your best lineup: losing him costs ${pts(-ctx.delta)} pts this week${ctx.nextBest?` (next best: ${esc(ctx.nextBest)})`:''}`:`Not in your best lineup: starting him ${ctx.delta>=0?'adds':'costs'} ${pts(Math.abs(ctx.delta))} pts${ctx.slot?` (best slot ${esc(ctx.slot)})`:''}`;
  const adv=`<h4>Projected stat line</h4>${statLine(p.stats)||'<div class="v10-muted">No stat line in the projection.</div>'}`+
    (rows.length?`<h4>Scoring under your league rules</h4><table class="v10-mini"><thead><tr><th>Rule</th><th class="v10-num">Stat</th><th class="v10-num">×</th><th class="v10-num">Pts</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(STAT_LABEL[r.key]||r.key)}</td><td class="v10-num">${pts(r.stat,2)}</td><td class="v10-num">${esc(r.weight)}</td><td class="v10-num">${pts(r.points,2)}</td></tr>`).join('')}</tbody></table>`:'')+
    `<h4>Distribution</h4>`+kv([['Mean',pts(p.active?.value)],['Spread (sd)',d?pts(d.sd):'–'],[p.range?.calibrated?'P10–P90':'Typical range',p.range?`${pts(p.range.low)}–${pts(p.range.high)}${p.range.median!==undefined?` · median ${pts(p.range.median)}`:''}`:'–'],['Calibration',p.range?.calibrated?`WP-V1 (2026 W1–W5, n=${esc(p.range.n)}, in-sample)`:'not calibrated yet (WP-V1) '+dot('amber','Spread is a rule of thumb')]])+
    `<h4>Lineup context</h4><div>${ctxTxt}</div>`+
    `<h4>Provenance</h4>`+kv([['Projection',esc(sourceLabel(p.active))],['Projection age',p.active?.ageMin!==null&&p.active?.ageMin!==undefined?`${p.active.ageMin} min`:'–'],['Primary source',esc(p.active?.primary||'–')],['Status source',esc(p.status?.source||'–')],['Kickoff (UTC)',p.game?.kickoff?esc(new Date(p.game.kickoff).toISOString().slice(0,16).replace('T',' ')):'–'],['Lock',p.game?.locked?'locked':esc(until(p.game?.kickoff))],['Sleeper ID',esc(p.pid)]]);
  return{body,adv};
}
// R5.5 · Opponent lineup mode. auto = WeekModel's policy mode (optimal until Thursday 18:00 UTC, as set after); the viewer
// can pin "optimal" or "asSet" (this browser only). opp(wm) returns the effective view used by Overview, Matchup and Field.
const OPP_KEY='fieV10OppMode';
function oppPref(){try{const v=localStorage.getItem(OPP_KEY);return ['optimal','asSet'].includes(v)?v:'auto';}catch{return 'auto';}}
function setOppPref(v){try{v==='auto'?localStorage.removeItem(OPP_KEY):localStorage.setItem(OPP_KEY,v);}catch{}}
function opp(wm){const pref=oppPref(),mode=pref==='auto'?(wm?.opponentMode?.mode||'asSet'):pref,o=wm?.opponent,w=wm?.winEstimate,f=wm?.field;
  return{pref,mode,auto:wm?.opponentMode?.mode||'asSet',cutoff:wm?.opponentMode?.cutoff??null,
    oppProjected:o?(mode==='optimal'?o.optimal?.totals?.projected:o.totals.projected):null,win:w?(mode==='optimal'?w.vsOptimal:w.asSet)??w.value:null,
    winRec:w?(mode==='optimal'?w.withRecommendedVsOptimal:w.withRecommendedAsSet)??w.withRecommended:null,field:f?(f[mode]||f):null};}
function oppToggle(wm){const x=opp(wm),b=(v,l)=>`<button class="v10-chip${x.pref===v?' v10-chip-on':''}" data-v10-opp="${v}">${l}</button>`;
  return `<span class="v10-row v10-small">Opponents: ${b('auto',`auto (${x.auto==='optimal'?'optimal':'as set'}${x.cutoff?` until ${esc(time(x.cutoff))}`:''})`)} ${b('optimal','optimal')} ${b('asSet','as set')}</span>`;}
window.FIEV10Kit={VERSION,opp,oppPref,setOppPref,oppToggle,TZ,esc,num,pts,signed,pct,winPct,time,clock,until,dot,tierChip,statusChip,formatChip,gameText,expand,repaint,kv,empty,sourceLabel,playerDetail,playerLink,statLine,TIER_LABEL};
})();
