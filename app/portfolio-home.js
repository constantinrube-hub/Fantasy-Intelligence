/* Fantasy Intelligence Engine: multi-league Portfolio Home
 * Global launch surface for saved leagues. Deep recommendations are cached
 * per League ID from the normal League Workspace. Lightweight Sleeper status
 * refreshes never mutate the active league state.
 */
(function(){
'use strict';

const SAVED_KEY='fieSavedLeaguesV71';
const SNAP_KEY='fiePortfolioSnapshotsV1';
const META_KEY='fiePortfolioMetaV1';
const Portfolio={version:'1.0.0',mode:true,refreshing:false,snapshots:{},meta:{}};
let BASE_RENDER=null,BASE_LOAD=null;

function escP(s){return typeof window.esc==='function'?window.esc(s):String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
function readJSON(key,fallback){try{const x=JSON.parse(localStorage.getItem(key)||'null');return x&&typeof x==='object'?x:fallback;}catch{return fallback;}}
function writeJSON(key,x){try{localStorage.setItem(key,JSON.stringify(x));}catch(e){console.warn('Portfolio cache write skipped',e);}}
function savedLeagues(){const x=readJSON(SAVED_KEY,[]);return Array.isArray(x)?x:[];}
function loadCaches(){Portfolio.snapshots=readJSON(SNAP_KEY,{});Portfolio.meta=readJSON(META_KEY,{});}
function formatName(e,s){return s?.format||({REDRAFT:'Redraft',DYNASTY:'Dynasty',CHOPPED:'Chopped',REDRAFT_BESTBALL:'Redraft + Best Ball',DYNASTY_BESTBALL:'Dynasty + Best Ball'}[e?.formatOverride]||'Auto-detect');}
function ageMs(ts){const t=Date.parse(ts||'');return Number.isFinite(t)?Math.max(0,Date.now()-t):Infinity;}
function relativeAge(ts){const ms=ageMs(ts);if(!Number.isFinite(ms))return 'Never analyzed';const min=Math.floor(ms/60000);if(min<2)return 'Updated now';if(min<60)return `Updated ${min}m ago`;const h=Math.floor(min/60);if(h<48)return `Updated ${h}h ago`;const d=Math.floor(h/24);return `Updated ${d}d ago`;}
function freshness(ts){const ms=ageMs(ts);if(ms<=24*3600e3)return {label:'Current',cls:'fresh'};if(ms<=7*24*3600e3)return {label:'Recent',cls:'recent'};return {label:'Needs refresh',cls:'stale'};}
function activeSavedId(){return String(state?.league?.league_id||'');}

function captureCurrentLeague(snapshot=null){
  snapshot=snapshot||window.FIEDecisionEngines?.portfolioSnapshot?.();
  if(!snapshot?.leagueId)return null;
  Portfolio.snapshots[String(snapshot.leagueId)]={...snapshot,leagueId:String(snapshot.leagueId),generatedAt:snapshot.generatedAt||new Date().toISOString()};
  writeJSON(SNAP_KEY,Portfolio.snapshots);
  if(Portfolio.mode)renderPortfolio();
  return snapshot;
}

function ensureStyles(){if(document.getElementById('fiePortfolioStyles'))return;const s=document.createElement('style');s.id='fiePortfolioStyles';s.textContent=`
.fie-portfolio-launch{width:100%;border:1px solid #31547a;background:linear-gradient(135deg,#102a45,#17253e);color:#e7f4ff;display:flex;align-items:center;gap:9px;padding:9px;border-radius:10px;text-align:left;cursor:pointer;font-size:12px;font-weight:900;margin:0 0 8px}.fie-portfolio-launch:hover,.fie-portfolio-launch.active{border-color:#67e8f9;box-shadow:inset 0 0 0 1px rgba(103,232,249,.18)}
#portfolioPanel{display:none;padding:0;background:transparent;border:0;box-shadow:none}#portfolioPanel.active{display:block}.portfolio-toolbar{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:10px}.portfolio-toolbar .subtitle{max-width:720px}.portfolio-actions{display:flex;gap:7px;flex-wrap:wrap}
.portfolio-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:10px 0}.portfolio-kpi{padding:12px;border:1px solid var(--line);border-radius:12px;background:#101e31}.portfolio-kpi b{font-size:21px;display:block;margin-top:3px}.portfolio-kpi small{color:var(--muted)}
.portfolio-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.league-portfolio-card{position:relative;padding:14px;border:1px solid var(--line);border-radius:15px;background:linear-gradient(150deg,rgba(15,30,49,.98),rgba(9,20,36,.98));box-shadow:var(--shadow);cursor:pointer;transition:transform .12s ease,border-color .12s ease}.league-portfolio-card:hover{transform:translateY(-1px);border-color:#3f648d}.league-portfolio-card.active-league{border-color:#3c8b7b}.league-card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.league-card-title{font-size:16px;font-weight:950}.league-card-sub{font-size:10px;color:var(--muted);margin-top:3px}.league-card-badges{display:flex;justify-content:flex-end;gap:5px;flex-wrap:wrap}.portfolio-pill{display:inline-flex;border:1px solid #31547a;border-radius:999px;padding:3px 6px;font-size:9px;font-weight:850;color:#b8cbe2}.portfolio-pill.fresh{color:#86efac;border-color:#1c6a45}.portfolio-pill.recent{color:#fde68a;border-color:#74520f}.portfolio-pill.stale{color:#fda4af;border-color:#7a2938}.portfolio-pill.live{color:#67e8f9;border-color:#236a79}
.league-ranks{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin:11px 0}.league-rank{padding:8px;border:1px solid #203650;border-radius:9px;background:#0b1728}.league-rank span{display:block;font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}.league-rank b{font-size:14px}.league-todos{display:grid;gap:6px;margin-top:9px}.league-todo{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;padding:8px;border:1px solid #203650;border-radius:9px;background:rgba(7,18,34,.72)}.league-todo .tag{font-size:8px;font-weight:900;letter-spacing:.06em;border:1px solid #31547a;border-radius:999px;padding:3px 5px;color:#9fb8d4}.league-todo b{font-size:11px}.league-todo small{display:block;color:var(--muted);font-size:9px;margin-top:2px;line-height:1.35}.league-todo strong{font-size:11px;white-space:nowrap}.league-card-foot{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:10px;color:var(--muted);font-size:9px}.league-open{color:#9bdff2;font-weight:850}.portfolio-empty{padding:24px;border:1px dashed #31547a;border-radius:14px;text-align:center;background:rgba(12,23,40,.7)}
.portfolio-refreshing{opacity:.65;pointer-events:none}.league-home-label{white-space:nowrap}
@media(max-width:1000px){.portfolio-grid{grid-template-columns:1fr}.portfolio-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){.portfolio-toolbar{display:block}.portfolio-actions{margin-top:9px}.portfolio-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.league-ranks{grid-template-columns:repeat(2,minmax(0,1fr))}.league-todo{grid-template-columns:auto 1fr}.league-todo strong{grid-column:2}.fie-portfolio-launch{min-width:max-content;width:auto;margin-right:5px}}
`;document.head.appendChild(s);}

function ensureUI(){
  ensureStyles();
  const sidebar=document.querySelector('.sidebar');const nav=document.getElementById('primaryNav');
  if(sidebar&&nav&&!document.getElementById('portfolioHomeBtn')){const b=document.createElement('button');b.id='portfolioHomeBtn';b.className='fie-portfolio-launch';b.innerHTML='<span class="nav-icon">◎</span><span>All Leagues</span>';nav.insertAdjacentElement('beforebegin',b);b.onclick=showPortfolio;}
  const leagueHome=document.querySelector('#primaryNav .primary-tab[data-section="home"] span:last-child');if(leagueHome){leagueHome.textContent='League Home';leagueHome.classList.add('league-home-label');}
  const workspace=document.querySelector('.workspace');const home=document.getElementById('homePanel');
  if(workspace&&home&&!document.getElementById('portfolioPanel')){const p=document.createElement('div');p.id='portfolioPanel';p.className='card intel-panel';p.innerHTML='<div id="portfolioSummary"></div>';home.insertAdjacentElement('beforebegin',p);}
}

function hideForPortfolio(){
  document.querySelectorAll('.intel-panel').forEach(x=>x.classList.remove('active'));
  document.getElementById('mainArea')?.classList.add('hidden');document.getElementById('weeklyControls')?.classList.add('hidden');
  const p=document.getElementById('portfolioPanel');if(p)p.classList.add('active');
  const sub=document.getElementById('subnav');if(sub)sub.innerHTML='';
  document.getElementById('portfolioHomeBtn')?.classList.add('active');
  document.querySelectorAll('#primaryNav .primary-tab').forEach(x=>x.classList.remove('active'));
  const hero=document.getElementById('sectionHero');if(hero)hero.className='section-hero hero-home';
  const ey=document.getElementById('sectionEyebrow'),title=document.getElementById('sectionTitle'),desc=document.getElementById('sectionDesc'),badge=document.getElementById('sectionFormatBadge');
  if(ey)ey.textContent='Fantasy portfolio';if(title)title.textContent='All Leagues';if(desc)desc.textContent='Your prioritized to-do list across every saved league. Open a league for its complete analysis.';if(badge)badge.textContent=`${savedLeagues().length} saved`;
}

function metaAction(e,m){
  const drafts=Array.isArray(m?.drafts)?m.drafts:[],live=drafts.find(d=>['drafting','in_progress'].includes(String(d.status).toLowerCase())),pre=drafts.find(d=>String(d.status).toLowerCase()==='pre_draft');
  if(live)return {priority:110,route:'draftassistant',tag:'LIVE DRAFT',title:'Draft is in progress',note:'Open the league and refresh the Draft Assistant before the next selection.',metric:'Open'};
  if(pre||String(m?.league?.status||'').toLowerCase()==='pre_draft')return {priority:72,route:'draft',tag:'PRE-DRAFT',title:'Draft preparation available',note:'Review league-specific ranks, roster construction and opponent draft tendencies.',metric:'Prepare'};
  return null;
}
function cardActions(e,s,m){const xs=[];const ma=metaAction(e,m);if(ma)xs.push(ma);for(const x of s?.items||[])if(!xs.some(y=>y.tag===x.tag))xs.push(x);if(!xs.length){const status=String(m?.league?.status||'').toLowerCase();xs.push({priority:20,route:'home',tag:status==='in_season'?'REFRESH':'OPEN',title:s?'Refresh league recommendations':'Build league recommendations',note:s?'Open this league to refresh weekly, waiver, trade and roster decisions.':'This league has not yet produced a Portfolio snapshot on this device.',metric:'Open'});}return xs.sort((a,b)=>(b.priority||0)-(a.priority||0)).slice(0,3);}
function urgentCount(rows){return rows.reduce((n,{e,s,m})=>n+cardActions(e,s,m).filter(x=>(x.priority||0)>=80).length,0);}
function staleCount(rows){return rows.filter(x=>freshness(x.s?.generatedAt).cls==='stale').length;}
function formatCount(rows){return new Set(rows.map(x=>formatName(x.e,x.s))).size;}
function rankText(v){const n=Number(v);return Number.isFinite(n)&&n>0?`#${Math.round(n)}`:'—';}

function renderLeagueCard(e){
  const id=String(e.id),s=Portfolio.snapshots[id],m=Portfolio.meta[id],fresh=freshness(s?.generatedAt),acts=cardActions(e,s,m),active=activeSavedId()===id;
  const season=s?.season||e.season||m?.league?.season||'—',teams=s?.teams||m?.league?.total_rosters||'—',status=m?.league?.status?String(m.league.status).replaceAll('_',' '):null;
  return `<article class="league-portfolio-card ${active?'active-league':''}" data-league-id="${escP(id)}"><div class="league-card-head"><div><div class="league-card-title">${escP(s?.leagueName||e.name||m?.league?.name||id)}</div><div class="league-card-sub">${escP(s?.rosterName||'Your roster not cached')} · ${escP(season)} · ${escP(teams)} teams</div></div><div class="league-card-badges"><span class="portfolio-pill">${escP(formatName(e,s))}</span>${status?`<span class="portfolio-pill live">${escP(status)}</span>`:''}<span class="portfolio-pill ${fresh.cls}">${escP(fresh.label)}</span></div></div><div class="league-ranks"><div class="league-rank"><span>Power</span><b>${rankText(s?.powerRank)}</b></div><div class="league-rank"><span>Contender</span><b>${rankText(s?.contenderRank)}</b></div><div class="league-rank"><span>Weekly</span><b>${rankText(s?.weeklyRank)}</b></div><div class="league-rank"><span>${String(s?.formatKey||'').includes('DYNASTY')?'Dynasty':'Depth'}</span><b>${rankText(String(s?.formatKey||'').includes('DYNASTY')?s?.dynastyRank:s?.depthRank)}</b></div></div><div class="league-todos">${acts.map(a=>`<button class="league-todo" type="button" data-route="${escP(a.route||'home')}"><span class="tag">${escP(a.tag||'TODO')}</span><span><b>${escP(a.title)}</b><small>${escP(a.note||'')}</small></span><strong>${escP(a.metric||'')}</strong></button>`).join('')}</div>${s?.violations?.length?`<div class="notice" style="margin-top:8px"><b>Roster rule:</b> ${escP(s.violations[0])}${s.violations.length>1?` +${s.violations.length-1} more`:''}</div>`:''}<div class="league-card-foot"><span>${escP(relativeAge(s?.generatedAt))}${m?.checkedAt?` · status checked ${escP(relativeAge(m.checkedAt).replace('Updated ','').toLowerCase())}`:''}</span><span class="league-open">Open league →</span></div></article>`;
}

function renderPortfolio(){
  ensureUI();loadCaches();hideForPortfolio();const box=document.getElementById('portfolioSummary');if(!box)return;
  const saved=savedLeagues(),ids=new Set(saved.map(x=>String(x.id)));for(const id of Object.keys(Portfolio.snapshots))if(!ids.has(String(id)))delete Portfolio.snapshots[id];
  const rows=saved.map(e=>({e,s:Portfolio.snapshots[String(e.id)],m:Portfolio.meta[String(e.id)]}));
  rows.sort((a,b)=>{const ap=cardActions(a.e,a.s,a.m)[0]?.priority||0,bp=cardActions(b.e,b.s,b.m)[0]?.priority||0;return bp-ap||String(a.e.name||a.e.id).localeCompare(String(b.e.name||b.e.id));});
  box.innerHTML=`<div class="portfolio-toolbar"><div><div class="eyebrow">Multi-league command center</div><h2 style="margin:4px 0 4px">What needs your attention?</h2><div class="subtitle">League cards combine live Sleeper status with the last full League-ID-specific decision snapshot. Deep recommendations are never calculated by borrowing the currently loaded league's state.</div></div><div class="portfolio-actions"><button id="portfolioRefreshBtn" class="btn primary" ${Portfolio.refreshing?'disabled':''}>${Portfolio.refreshing?'Refreshing…':'Refresh statuses'}</button><button id="portfolioAddBtn" class="btn ghost">Load / save another league</button></div></div><div class="portfolio-kpis"><div class="portfolio-kpi"><span class="filter-label">Saved leagues</span><b>${rows.length}</b><small>portfolio workspaces</small></div><div class="portfolio-kpi"><span class="filter-label">High-priority actions</span><b>${urgentCount(rows)}</b><small>draft / weekly / waiver items</small></div><div class="portfolio-kpi"><span class="filter-label">Needs deep refresh</span><b>${staleCount(rows)}</b><small>snapshot older than 7 days or missing</small></div><div class="portfolio-kpi"><span class="filter-label">Formats</span><b>${formatCount(rows)}</b><small>distinct strategic profiles</small></div></div>${rows.length?`<div class="portfolio-grid">${rows.map(x=>renderLeagueCard(x.e)).join('')}</div>`:`<div class="portfolio-empty"><h3>No saved leagues yet</h3><div class="subtitle">Load a Sleeper league above, save it, then it will appear here with its own isolated recommendations.</div><button id="portfolioEmptyAdd" class="btn primary" style="margin-top:12px">Load first league</button></div>`}<div class="notice" style="margin-top:10px"><b>Freshness model:</b> “Refresh statuses” checks lightweight Sleeper league/draft state for every saved league. Full player, waiver, matchup and simulation recommendations refresh when that league is opened, which preserves League-ID isolation and avoids silently mixing model state across leagues.</div>`;
  document.getElementById('portfolioRefreshBtn')?.addEventListener('click',()=>refreshStatuses(true));
  const focus=()=>{document.querySelector('.connect')?.scrollIntoView({behavior:'smooth',block:'start'});document.getElementById('leagueInput')?.focus();};document.getElementById('portfolioAddBtn')?.addEventListener('click',focus);document.getElementById('portfolioEmptyAdd')?.addEventListener('click',focus);
  for(const card of box.querySelectorAll('.league-portfolio-card')){card.addEventListener('click',e=>{const route=e.target.closest('[data-route]')?.dataset.route||'home';openLeague(card.dataset.leagueId,route);});}
}

async function sleeperJSON(url){if(typeof window.fetchJSON==='function')return window.fetchJSON(url);const c=new AbortController(),t=setTimeout(()=>c.abort(),9000);try{const r=await fetch(url,{signal:c.signal});if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}finally{clearTimeout(t);}}
async function refreshOne(e){const id=String(e.id);try{const [league,drafts]=await Promise.all([sleeperJSON(`https://api.sleeper.app/v1/league/${id}`),sleeperJSON(`https://api.sleeper.app/v1/league/${id}/drafts`).catch(()=>[])]);Portfolio.meta[id]={league:{league_id:String(league?.league_id||id),name:league?.name||e.name||id,season:league?.season||e.season||'',status:league?.status||'',total_rosters:Number(league?.total_rosters)||null},drafts:(drafts||[]).map(d=>({draft_id:String(d.draft_id||''),status:d.status||'',season:d.season||'',type:d.type||''})),checkedAt:new Date().toISOString(),error:null};}catch(err){Portfolio.meta[id]={...(Portfolio.meta[id]||{}),checkedAt:new Date().toISOString(),error:String(err?.message||err)};}}
async function refreshStatuses(force=false){if(Portfolio.refreshing)return;const xs=savedLeagues();if(!xs.length)return;Portfolio.refreshing=true;renderPortfolio();let next=0;async function worker(){while(next<xs.length){const i=next++;const e=xs[i],old=Portfolio.meta[String(e.id)];if(!force&&old&&ageMs(old.checkedAt)<30*60e3)continue;await refreshOne(e);}}await Promise.all(Array.from({length:Math.min(3,xs.length)},worker));Portfolio.refreshing=false;writeJSON(META_KEY,Portfolio.meta);renderPortfolio();}

function showPortfolio(){
  try{captureCurrentLeague();}catch{}
  Portfolio.mode=true;state.portfolioMode=true;renderPortfolio();if(!Portfolio.refreshing)refreshStatuses(false);
}
function leavePortfolio(){Portfolio.mode=false;state.portfolioMode=false;document.getElementById('portfolioHomeBtn')?.classList.remove('active');document.getElementById('portfolioPanel')?.classList.remove('active');}
async function openLeague(id,route='home'){
  const e=savedLeagues().find(x=>String(x.id)===String(id));if(!e)return;leavePortfolio();const inp=document.getElementById('leagueInput'),sel=document.getElementById('savedLeagueSelect'),fmt=document.getElementById('savedLeagueFormat');if(inp)inp.value=String(id);if(sel)sel.value=String(id);if(fmt)fmt.value=e.formatOverride||'AUTO';state.activeTab=route||'home';
  const status=document.getElementById('status');if(status)status.textContent=`Opening ${e.name||id}…`;
  try{await BASE_LOAD?.();state.activeTab=route||'home';captureCurrentLeague();BASE_RENDER?.();}catch(err){console.error(err);if(status)status.textContent=`Could not open ${e.name||id}: ${err?.message||err}`;}
}

function bind(){
  ensureUI();loadCaches();BASE_RENDER=window.render;BASE_LOAD=window.loadLeague;
  if(typeof BASE_RENDER==='function'){const guarded=function(){if(Portfolio.mode||state.portfolioMode)return renderPortfolio();const r=BASE_RENDER.apply(this,arguments);try{captureCurrentLeague();}catch{}return r;};guarded.__fiePortfolioWrapped=true;window.render=guarded;}
  if(typeof BASE_LOAD==='function'){const loader=async function(){leavePortfolio();state.activeTab='home';const r=await BASE_LOAD.apply(this,arguments);state.activeTab='home';try{captureCurrentLeague();}catch{}BASE_RENDER?.();return r;};loader.__fiePortfolioWrapped=true;window.loadLeague=loader;const lb=document.getElementById('loadBtn');if(lb)lb.onclick=loader;}
  const nav=document.getElementById('primaryNav');if(nav)nav.addEventListener('click',e=>{const b=e.target.closest('.primary-tab');if(!b)return;if(!state.league&&b.dataset.section==='home'){e.preventDefault();e.stopImmediatePropagation();showPortfolio();return;}leavePortfolio();},true);
  const sub=document.getElementById('subnav');if(sub)sub.addEventListener('click',()=>leavePortfolio(),true);
  const homeBtn=document.querySelector('#primaryNav .primary-tab[data-section="home"]');if(homeBtn&&!state.league)homeBtn.title='Open a saved league first';
  Portfolio.mode=true;state.portfolioMode=true;renderPortfolio();refreshStatuses(false);
}

Portfolio.captureCurrentLeague=captureCurrentLeague;Portfolio.render=renderPortfolio;Portfolio.show=showPortfolio;Portfolio.openLeague=openLeague;Portfolio.refreshStatuses=refreshStatuses;window.FIEPortfolio=Portfolio;
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
})();
