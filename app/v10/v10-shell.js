/* FIE UI v10 shell (R1 · WP1.0 switch, WP1.1 router + context bar). UI contract §2, §4.
 *
 * Switch: `?ui=v10` turns the new interface on (remembered in this browser), `?ui=classic` turns it
 * off; otherwise config/ui-decision-policy.json › default_ui decides ("classic" until the user
 * accepts the preview). The classic application keeps running underneath, unchanged: v10 hides it
 * with one body class and never patches its functions (CHANGE_GUIDE: no monkey-patch layer).
 *
 * Routes: #/overview · #/league/<id>/<home|lineup|matchup|waivers|players|team|trades> · #/lab/<state|eval|forecasts|rankings|docs>?league=<id>
 *         · #/classic/<id>/<trades|draft|lab|waivers|weekly> (bridge)
 * The classic route is the bridge for views not rebuilt in R1: it shows the classic UI, loads that
 * league through FIELeagueController and opens the tab by clicking its real navigation.
 * A "New view" pill returns to v10. While visible, the current view re-renders on the policy cadence
 * (refresh_seconds: live game / idle / off-season, R4.6); data-client TTLs decide what is re-fetched.
 */
(function(){
'use strict';
const VERSION='10.5.0';
const KEY='fieUiMode';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
const CLASSIC_TABS={waivers:['market','waivers'],trades:['market','trades'],draft:['draft','draft'],lab:['lab',null],weekly:['weekly','startsit']};
let root=null,main=null,timer=null,current=null;
function read(k){try{return localStorage.getItem(k);}catch{return null;}}
function write(k,v){try{v===null?localStorage.removeItem(k):localStorage.setItem(k,v);}catch{}}
function mode(){
  let q=null;try{q=new URLSearchParams(location.search).get('ui');}catch{}
  if(q==='v10'||q==='classic'){write(KEY,q);return q;}
  const s=read(KEY);if(s==='v10'||s==='classic')return s;
  return window.FIE_UI_POLICY?.default_ui==='v10'?'v10':'classic';
}
function bar(){
  return `<div class="v10-bar"><a class="v10-brand" href="#/overview">FIE</a><a class="v10-nav" href="#/overview" data-nav="overview">Overview</a><a class="v10-nav" href="#/lab/state" data-nav="lab">Research Lab</a>
  <select id="v10LeagueSelect" aria-label="League"><option value="">League…</option></select>
  <span class="v10-spacer"></span><span class="v10-muted" id="v10AsOf"></span><span class="v10-muted v10-small" id="v10Next"></span>
  <button class="v10-btn" id="v10Refresh" title="Re-read Sleeper rosters, matchups and projections">Refresh</button>
  <button class="v10-btn v10-ghost" id="v10Classic" title="Switch this browser back to the classic interface">Classic view</button></div>`;
}
async function fillLeagues(){
  const sel=root.querySelector('#v10LeagueSelect');if(!sel)return;const list=await D().leagues();const k=K();
  sel.innerHTML=`<option value="">League…</option>${list.map(l=>`<option value="${k.esc(l.id)}">${k.esc(l.name||l.id)}</option>`).join('')}`;
  if(current?.id)sel.value=current.id;
}
function asOf(){const el=root?.querySelector('#v10AsOf'),t=D().lastFetch();if(el)el.textContent=t?`data ${K().clock(t)}`:'';}
function parse(){const [path,qs]=(location.hash||'').replace(/^#\/?/,'').split('?'),h=path.split('/').map(decodeURIComponent),q=new URLSearchParams(qs||'');
  const week=Number(q.get('week'))||null;
  if(h[0]==='league'&&h[1])return{view:'league',id:h[1],tab:['home','lineup','matchup','waivers','players','team','trades'].includes(h[2])?h[2]:'home',week};
  if(h[0]==='classic'&&h[1])return{view:'classic',id:h[1],tab:h[2]||'weekly'};
  if(h[0]==='lab')return{view:'lab',tab:h[1]||'state',id:q.get('league')||null,pos:q.get('pos')||null,week};
  return{view:'overview',week};}
async function route(){
  if(document.body.classList.contains('fie-v10-off'))return;
  const r=parse();current=r;
  window.FIEV10Overview?.cancel();window.FIEV10League?.cancel();window.FIEV10Lab?.cancel();
  if(r.view==='classic'){openClassic(r.id,r.tab);return;}
  show(true);
  root.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===r.view));
  const sel=root.querySelector('#v10LeagueSelect');if(sel)sel.value=r.view==='league'?r.id:'';
  try{if(r.view==='league')await window.FIEV10League.render(main,r.id,r.tab,r.week);else if(r.view==='lab')await window.FIEV10Lab.render(main,r.tab,r.id,r.pos,r.week);else await window.FIEV10Overview.render(main,{week:r.week});}
  catch(e){main.innerHTML=K().empty(`Something went wrong: ${String(e?.message||e)}`);window.FIECore?.Diagnostics?.capture?.(e,{domain:'v10-route'});}
  asOf();
}
function show(on){document.body.classList.toggle('fie-v10',on);root.hidden=!on;pill(!on);}
function pill(on){let p=document.getElementById('fieV10Back');
  if(on&&!p){p=document.createElement('a');p.id='fieV10Back';p.href='#/overview';p.textContent='← New view';p.title='Back to the new interface';document.body.appendChild(p);}
  if(p)p.hidden=!on;}
async function openClassic(id,tab){
  show(false);
  const [section,sub]=CLASSIC_TABS[tab]||CLASSIC_TABS.weekly;
  try{
    if(String(window.state?.league?.league_id||'')!==String(id)){
      const inp=document.getElementById('leagueInput'),sel=document.getElementById('savedLeagueSelect');if(inp)inp.value=String(id);if(sel)sel.value=String(id);
      const ok=await window.FIELeagueController?.switchLeague?.(String(id));if(!ok)return;}
    document.querySelector(`#primaryNav [data-section="${section}"]`)?.click();
    if(sub)setTimeout(()=>document.querySelector(`#subnav .tab[data-tab="${sub}"]`)?.click(),150);
    window.scrollTo(0,0);
  }catch(e){window.FIECore?.Diagnostics?.capture?.(e,{domain:'v10-open-classic',leagueId:id});}
}
// R4.6 · Refresh cadence (policy refresh_seconds): every 2 min while an NFL game of the schedule is live (from 10 min
// before kickoff to 4.5 h after, unless final), 15 min otherwise in season, 6 h in the off-season (Sleeper season_type
// not regular/post). No auto-refresh while a simulation runs or an Advanced panel is open; the next refresh time is
// shown in the bar. It was a fixed 2 min, which repainted the page constantly on non-game days.
let refreshMode=null,nextAt=null;
async function cadence(){
  const r=window.FIE_UI_POLICY?.refresh_seconds||{},live=(Number(r.live)||120)*1e3,idle=(Number(r.idle)||900)*1e3,off=(Number(r.offseason)||21600)*1e3;
  try{const st=await D().nflState();if(st&&!['regular','post'].includes(String(st.season_type||'regular')))return{ms:off,mode:'off-season'};
    const idx=await D().schedule(),now=Date.now();
    for(const g of new Set(idx?.games?.values?.()||[]))if(g.kickoff&&!g.final&&now>=g.kickoff-10*60e3&&now<=g.kickoff+4.5*3600e3)return{ms:live,mode:'game live'};
    return{ms:idle,mode:'no game live'};}catch{return{ms:live,mode:'game live'};}
}
function busy(){return !!document.querySelector('.v10-x[open] .v10-adv[open]')||!!document.querySelector('[data-v10-odds][disabled]');}
function showNext(){const el=root?.querySelector('#v10Next');if(el)el.textContent=nextAt?`auto-refresh ${K().clock(nextAt)} (${refreshMode})`:'';}
function tick(){clearTimeout(timer);
  cadence().then(({ms,mode:m})=>{refreshMode=m;nextAt=Date.now()+ms;showNext();
    timer=setTimeout(()=>{if(document.visibilityState==='visible'&&document.body.classList.contains('fie-v10')&&!busy())route();tick();},ms);});}
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&nextAt&&Date.now()>nextAt&&document.body.classList.contains('fie-v10')&&!busy()){route();tick();}});
function install(){
  root=document.createElement('div');root.id='fieV10';root.innerHTML=`${bar()}<main id="fieV10Main" class="v10-main"></main>`;document.body.insertBefore(root,document.body.firstChild);main=root.querySelector('#fieV10Main');
  root.querySelector('#v10Refresh').addEventListener('click',()=>{D().refresh();route();});
  root.querySelector('#v10Classic').addEventListener('click',()=>{write(KEY,'classic');show(false);pill(false);document.body.classList.add('fie-v10-off');});
  root.querySelector('#v10LeagueSelect').addEventListener('change',e=>{const id=e.target.value;location.hash=id?`#/league/${encodeURIComponent(id)}/home`:'#/overview';});
  window.addEventListener('hashchange',route);
  fillLeagues();tick();route();
}
function start(){if(mode()!=='v10')return;if(document.getElementById('fieV10'))return;install();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
window.FIEV10={VERSION,mode,route,start,openClassic};
})();
