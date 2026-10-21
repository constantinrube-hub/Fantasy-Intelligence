/* FIE v10 season simulation (UI v10 R6) — UI contract §7.2c.
 *
 * Pure Monte Carlo over the rest of the season, fed by the same inputs as the WeekModel (no classic engine, no global
 * state): every active team's roster, each player's base value per week (caller's valueFor: this week = the WeekModel's
 * status-adjusted value, published later weeks = Sleeper's projection for that week, unpublished weeks = this week's
 * projection or the season rate per game, byes = 0), the calibrated outcome spread (deciles by position × projection tier,
 * else the rule-of-thumb range as a normal), Sleeper's schedule (matchup pairs per week; a week without a published
 * schedule is paired at random each iteration), median games, playoff seeding and byes, chopped eliminations.
 *
 *   simulate(cfg) → Promise<result>   (yields to the browser every `chunk` iterations)
 *
 * Lineups: non-Best-Ball teams start the lineup that is best by base value (fixed before the week, as a manager would),
 * then each starter's score is sampled; Best Ball teams score the best lineup of the SAMPLED values (greedy assignment,
 * specific slots before flex — what Sleeper does after the games). Limits (shown in the UI): player scores are sampled
 * independently (no game or team correlation), rosters stay as they are (no waivers, trades or released-player
 * redistribution in chopped), future unpublished weeks reuse this week's projections.
 * Outputs H2H: playoff / bye / title probability, final-rank distribution, expected wins, and "why" (current record,
 * remaining games, team mean ± sd per week, average remaining opponent, wins needed for 75 % playoff odds).
 * Outputs chopped: survival per week (this week first), win-league probability, expected elimination week.
 */
(function(){
'use strict';
const VERSION='10.6.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function hash(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
function mulberry(seed){let a=seed>>>0;return()=>{a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function normal(r){let u=0,v=0;while(u===0)u=r();while(v===0)v=r();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);}
/** Outcome sampler for a base value v: ratio knots from the player's deciles (relative to his current projection) with
 *  linear tails (P0 = max(0, 2·P10 − P20), P100 = P90 + 1.5·(P90 − P80)); otherwise a normal from the range. */
function samplerFor(p,v){
  if(!(v>0))return null;
  const cur=num(p?.active?.value),dq=p?.range?.deciles?.q;
  if(dq&&cur>0){const r=dq.map(x=>x/cur),k=[Math.max(0,2*r[0]-r[1]),...r,r[8]+1.5*(r[8]-r[7])];return{knots:k.map(x=>x*v),kind:'deciles'};}
  const lo=num(p?.range?.low),hi=num(p?.range?.high),rel=cur>0&&lo!==null&&hi!==null?Math.max(0.05,(hi-lo)/cur/2.563):0.17;return{sd:v*rel,mu:v,kind:'normal'};
}
function draw(s,r){if(!s)return 0;if(s.knots){const u=r()*10,i=Math.min(9,Math.floor(u)),f=u-i;return s.knots[i]+(s.knots[i+1]-s.knots[i])*f;}return Math.max(0,s.mu+normal(r)*s.sd);}
function meanOf(s){if(!s)return 0;if(s.knots){let m=0;for(let i=0;i<10;i++)m+=(s.knots[i]+s.knots[i+1])/2;return m/10;}return s.mu;}
const SLOT_ORDER=['QB','RB','WR','TE','K','DEF','DL','LB','DB','WRRB_FLEX','REC_FLEX','FLEX','SUPER_FLEX','IDP_FLEX'];
/** Slot indices a position may fill, specific slots before flex (precomputed per league). */
function slotPlan(slots){const PR=W().FIECore.PositionRegistry,order=slots.map((s,i)=>({s,i})).sort((a,b)=>(SLOT_ORDER.indexOf(a.s)+99)%99-(SLOT_ORDER.indexOf(b.s)+99)%99),cache=new Map();
  return pos=>{if(!cache.has(pos))cache.set(pos,order.filter(o=>PR.eligible(pos,o.s)).map(o=>o.i));return cache.get(pos);};}
function greedy(slots,cands,plan=slotPlan(slots)){ // cands: [{pos, v, el?}] → total of a greedy best lineup (specific slots first)
  const open=new Uint8Array(slots.length).fill(1);let left=slots.length,t=0;
  for(const c of cands.slice().sort((a,b)=>b.v-a.v)){if(!left)break;for(const i of (c.el||plan(c.pos)))if(open[i]){open[i]=0;left--;t+=c.v;break;}}
  return t;
}
const tick=()=>new Promise(r=>setTimeout(r,0));
/**
 * cfg: {teams:[{rosterId,name,me,pool:[pid],wins,losses,ties,pf}], player(pid), valueFor(pid,week), slots, bestBall,
 *       weeks:[w...] (regular season weeks still to play), pairs:{[w]:[[a,b],...]|null}, median, playoffTeams,
 *       playoffWeeks:[w...], chopped:{perWeek}|null, iterations, seed, chunk, onProgress(done,total)}
 */
async function simulate(cfg){
  const {teams,player,valueFor,slots,bestBall=false,weeks=[],pairs={},median=false,playoffTeams=0,playoffWeeks=[],chopped=null,iterations=3000,seed=1,chunk=250,onProgress=null}=cfg;
  const O=W().FIECore.LineupOptimizer,PR=W().FIECore.PositionRegistry,allWeeks=[...weeks,...playoffWeeks];
  // Precompute per team and week: samplers of the starters (non-Best-Ball) or of the whole eligible pool (Best Ball).
  const prep=new Map(),plan=slotPlan(slots);
  for(const t of teams){const per={};
    for(const w of allWeeks){const ps=t.pool.map(pid=>player(pid)).filter(p=>p&&slots.some(s=>PR.eligible(p.position,s)));
      const base=new Map(ps.map(p=>[p.pid,num(valueFor(p.pid,w))??0]));
      if(bestBall){per[w]={bb:ps.map(p=>({pos:p.position,el:plan(p.position),s:samplerFor(p,base.get(p.pid))})).filter(x=>x.s)};}
      else{const o=O.optimize(ps,slots,p=>base.get(p.pid)||0),st=(o.assignment||[]).map(a=>player(a.playerId)).filter(Boolean);per[w]={st:st.map(p=>samplerFor(p,base.get(p.pid))).filter(Boolean)};}
      const x=per[w];x.mean=x.st?x.st.reduce((s,q)=>s+meanOf(q),0):null;}
    prep.set(t.rosterId,per);}
  const scoreOf=(rid,w,r)=>{const x=prep.get(rid)[w];if(x.st){let s=0;for(const q of x.st)s+=draw(q,r);return s;}return greedy(slots,x.bb.map(c=>({pos:c.pos,el:c.el,v:draw(c.s,r)})),plan);};
  const r=mulberry(seed),ids=teams.map(t=>t.rosterId),N=ids.length;
  // Team means per week (Best Ball by sampling 200 draws once) and sd, for the "why" panel.
  const stats={};for(const t of teams){const ms=[],sds=[];for(const w of weeks){const xs=[];for(let i=0;i<200;i++)xs.push(scoreOf(t.rosterId,w,r));const m=xs.reduce((a,b)=>a+b,0)/xs.length;ms.push(m);sds.push(Math.sqrt(xs.reduce((a,b)=>a+(b-m)**2,0)/xs.length));}
    stats[t.rosterId]={mean:ms.length?ms.reduce((a,b)=>a+b,0)/ms.length:null,sd:sds.length?sds.reduce((a,b)=>a+b,0)/sds.length:null,perWeek:ms};}
  if(chopped)return simChopped();
  const out=Object.fromEntries(ids.map(id=>[id,{playoffs:0,bye:0,title:0,wins:0,ranks:new Array(N).fill(0),winsHist:new Map()}]));
  const randomPairs=list=>{const a=list.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]];}const p=[];for(let i=0;i+1<a.length;i+=2)p.push([a[i],a[i+1]]);return p;};
  const byeN=playoffTeams>0?playoffTeams-2**Math.floor(Math.log2(playoffTeams)):0;
  for(let it=0;it<iterations;it++){
    const st=Object.fromEntries(teams.map(t=>[t.rosterId,{w:t.wins,l:t.losses,t:t.ties,pf:t.pf}]));
    for(const w of weeks){const sc={};for(const id of ids)sc[id]=scoreOf(id,w,r);
      for(const [a,b] of (pairs[w]||randomPairs(ids))){if(!(a in sc)||!(b in sc))continue;if(sc[a]>sc[b]){st[a].w++;st[b].l++;}else if(sc[b]>sc[a]){st[b].w++;st[a].l++;}else{st[a].t++;st[b].t++;}}
      if(median){const v=ids.map(id=>sc[id]).sort((x,y)=>x-y),m=N%2?v[(N-1)/2]:(v[N/2-1]+v[N/2])/2;for(const id of ids){if(sc[id]>m)st[id].w++;else if(sc[id]<m)st[id].l++;else st[id].t++;}}
      for(const id of ids)st[id].pf+=sc[id];}
    const ranked=ids.slice().sort((a,b)=>(st[b].w+st[b].t/2)-(st[a].w+st[a].t/2)||st[b].pf-st[a].pf);
    ranked.forEach((id,i)=>{const o=out[id];o.ranks[i]++;o.wins+=st[id].w;o.winsHist.set(st[id].w,(o.winsHist.get(st[id].w)||[0,0]));const h=o.winsHist.get(st[id].w);h[0]++;if(i<playoffTeams)h[1]++;});
    if(playoffTeams>0){const seeds=ranked.slice(0,playoffTeams);seeds.forEach((id,i)=>{out[id].playoffs++;if(i<byeN)out[id].bye++;});
      let alive=seeds.map((id,i)=>({id,seed:i+1})),k=0;
      while(alive.length>1){const w=playoffWeeks[Math.min(k,playoffWeeks.length-1)]??weeks[weeks.length-1],n=alive.length,low=2**Math.floor(Math.log2(n)),byes=n===low?0:n-low,ord=alive.slice().sort((a,b)=>a.seed-b.seed),next=ord.slice(0,byes),play=ord.slice(byes);
        for(let i=0;i<Math.floor(play.length/2);i++){const a=play[i],b=play[play.length-1-i],sa=w!==undefined?scoreOf(a.id,w,r):r(),sb=w!==undefined?scoreOf(b.id,w,r):r();next.push(sa>=sb?a:b);}
        if(play.length%2)next.push(play[Math.floor(play.length/2)]);alive=next;k++;}
      if(alive[0])out[alive[0].id].title++;}
    if(onProgress&&(it+1)%chunk===0){onProgress(it+1,iterations);await tick();}
  }
  const remaining=weeks.length+(median?weeks.length:0);
  const rows=teams.map(t=>{const o=out[t.rosterId],oppMeans=[];for(const w of weeks){const pr=pairs[w];if(!pr)continue;const pp=pr.find(p=>p.includes(t.rosterId));if(pp){const opp=pp[0]===t.rosterId?pp[1]:pp[0];const om=stats[opp]?.perWeek?.[weeks.indexOf(w)];if(om!==undefined)oppMeans.push(om);}}
    let need=null;const hist=[...o.winsHist.entries()].sort((a,b)=>a[0]-b[0]);for(const [wins,[n,po]] of hist)if(n>=Math.max(20,iterations*0.01)&&po/n>=0.75){need=wins;break;}
    return{rosterId:t.rosterId,name:t.name,me:!!t.me,playoff:playoffTeams?o.playoffs/iterations:null,bye:playoffTeams?o.bye/iterations:null,title:playoffTeams?o.title/iterations:null,
      expectedWins:o.wins/iterations,ranks:o.ranks.map(x=>x/iterations),
      why:{wins:t.wins,losses:t.losses,ties:t.ties,pf:t.pf,remainingGames:remaining,teamMean:stats[t.rosterId].mean,teamSd:stats[t.rosterId].sd,oppMean:oppMeans.length?oppMeans.reduce((a,b)=>a+b,0)/oppMeans.length:null,oppKnownWeeks:oppMeans.length,winsFor75:need}};});
  return{VERSION,kind:'h2h',iterations,weeks,playoffWeeks,playoffTeams,median,scheduleKnown:weeks.filter(w=>pairs[w]).length,rows,limits:LIMITS,at:Date.now()};

  async function simChopped(){
    const per=Math.max(1,Number(chopped.perWeek)||1),cw=allWeeks.length?allWeeks:weeks,o=Object.fromEntries(ids.map(id=>[id,{surv:new Array(cw.length).fill(0),win:0,elim:0,elimN:0}]));
    for(let it=0;it<iterations;it++){let alive=ids.slice();
      for(let k=0;k<cw.length&&alive.length>1;k++){const w=cw[k],sc=alive.map(id=>({id,s:scoreOf(id,w,r)})).sort((a,b)=>a.s-b.s),cut=new Set(sc.slice(0,Math.min(per,alive.length-1)).map(x=>x.id));
        for(const id of cut){o[id].elim+=k;o[id].elimN++;}alive=alive.filter(id=>!cut.has(id));for(const id of alive)o[id].surv[k]++;}
      if(alive.length===1)o[alive[0]].win++;
      if(onProgress&&(it+1)%chunk===0){onProgress(it+1,iterations);await tick();}}
    const rows=teams.map(t=>{const x=o[t.rosterId];return{rosterId:t.rosterId,name:t.name,me:!!t.me,survival:x.surv.map(v=>v/iterations),winner:x.win/iterations,expectedElimWeek:x.elimN?cw[0]+x.elim/x.elimN:null,
      why:{pf:t.pf,teamMean:stats[t.rosterId].mean,teamSd:stats[t.rosterId].sd}};});
    return{VERSION,kind:'chopped',iterations,weeks:cw,perWeek:per,rows,limits:LIMITS,at:Date.now()};
  }
}
const LIMITS=['player scores sampled independently (no game or team correlation)','rosters as they are today (no waivers, trades or chopped redistribution)','unpublished weeks reuse this week\'s projections (byes from the schedule)'];
window.FIESeasonSim={VERSION,simulate,samplerFor,draw,meanOf,greedy,mulberry,hash};
})();
