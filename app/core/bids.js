/* FIE waiver bid ranges (UI v10 R5.1) — UI contract §7.4.
 *
 * Pure. A bid range for a waiver add, from completed FAAB claims in Sleeper transactions:
 *   1 · normalise every winning bid to a share of its league's starting budget (a $100 and a $1000 league compare);
 *   2 · rank-match instead of projecting: per league, week and position the winning bids are sorted (1st, 2nd, 3rd+
 *       most expensive WR of that week). A candidate's rank = his rank among this week's available players at his
 *       position by lineup gain. "The best WR on the wire this week" is compared with what the best WR on the wire cost in
 *       earlier weeks — no historical projections needed (most weeks have none frozen);
 *   3 · pool with weights (policy waivers.bids): your league 1.0, other leagues of the same type (chopped vs normal FAAB)
 *       0.15, other types 0.05; claims of the last recent_weeks weeks × recent_factor;
 *   4 · range = weighted quantiles low_q–high_q (p50–p80), in dollars of this league, capped at your remaining budget.
 * Fallbacks when your league has fewer than min_own comparable claims and the weighted sample is thin: same position
 * any rank, then any position at that rank. Output always names the sample (n own / n other) and the scope.
 * Also: when this league's waivers usually process (most common UTC weekday/hour of completed claims) and whether this
 * week's run has already happened (a completed claim after the previous week's last game).
 * Display only: never a claim, never an automatic bid. Pending bids are not visible through Sleeper's public API.
 */
(function(){
'use strict';
const VERSION='10.5.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
const DEF={own:1,same_type:0.15,other_type:0.05,recent_weeks:3,recent_factor:2,low_q:0.5,high_q:0.8,min_own:3,rank_cap:3,min_weight:2};
function pol(p){return{...DEF,...((p||W().FIE_UI_POLICY||{}).waivers?.bids||{})};}
/** Completed, priced waiver claims of one league → [{leagueId, week, pos, rank, pct, bid, at}] (rank within week+position). */
function claims({leagueId,budget,transactions,positionOf}){
  const b=num(budget);if(!(b>0))return[];
  const won=[];for(const t of transactions||[]){if(!t||t.type!=='waiver'||t.status!=='complete')continue;const bid=num(t.settings?.waiver_bid);if(bid===null)continue;
    for(const pid of Object.keys(t.adds||{}))won.push({leagueId:String(leagueId),week:num(t.leg)??0,pos:String(positionOf(pid)||'?').toUpperCase(),pid:String(pid),bid,pct:bid/b,at:num(t.status_updated)});}
  const groups=new Map();for(const c of won){const k=`${c.week}:${c.pos}`;(groups.get(k)||groups.set(k,[]).get(k)).push(c);}
  for(const xs of groups.values()){xs.sort((a,b)=>b.bid-a.bid);xs.forEach((c,i)=>{c.rank=i+1;});}
  return won;
}
function wquantile(items,q){const xs=items.filter(x=>x.w>0).sort((a,b)=>a.v-b.v),tot=xs.reduce((s,x)=>s+x.w,0);if(!tot)return null;let c=0;for(const x of xs){c+=x.w;if(c>=q*tot-1e-9)return x.v;}return xs[xs.length-1].v;}
/**
 * estimate({position, rank, week, budget, remaining, own:[claims], others:[{claims, sameType}], policy})
 * → {low, high, pctLow, pctHigh, nOwn, nOther, scope, rank}  (null when no comparable claim exists anywhere)
 */
function estimate({position,rank,week,budget,remaining=null,own=[],others=[],policy}){
  const P=pol(policy),pos=String(position||'').toUpperCase(),r=Math.max(1,Math.min(P.rank_cap,Number(rank)||1)),b=num(budget);if(!(b>0))return null;
  const recent=c=>(week-c.week)<=P.recent_weeks&&c.week<week?P.recent_factor:1;
  const all=[...own.filter(c=>c.week<week).map(c=>({c,w:P.own*recent(c),mine:true})),...others.flatMap(o=>(o.claims||[]).filter(c=>c.week<week).map(c=>({c,w:(o.sameType?P.same_type:P.other_type)*recent(c),mine:false})))];
  const scopes=[['position and rank',x=>x.c.pos===pos&&Math.min(P.rank_cap,x.c.rank)===r],['position (any rank)',x=>x.c.pos===pos],['rank (any position)',x=>Math.min(P.rank_cap,x.c.rank)===r]];
  for(const [scope,f] of scopes){const s=all.filter(f),nOwn=s.filter(x=>x.mine).length,wt=s.reduce((t,x)=>t+x.w,0);
    if(!s.length)continue;if(nOwn<P.min_own&&wt<P.min_weight&&scope!==scopes[scopes.length-1][0])continue;
    const items=s.map(x=>({v:x.c.pct,w:x.w})),lo=wquantile(items,P.low_q),hi=wquantile(items,P.high_q);
    let low=Math.round(lo*b),high=Math.max(low,Math.round(hi*b));const cap=num(remaining);if(cap!==null){low=Math.min(low,cap);high=Math.min(high,cap);}
    return{low,high,pctLow:lo,pctHigh:hi,nOwn,nOther:s.length-nOwn,scope,rank:r,capped:cap!==null&&Math.round(hi*b)>cap};}
  return null;
}
/** Rank of each candidate among this week's candidates at his position (by horizon gain, then week gain). */
function ranks(rows){const by=new Map();for(const r of rows||[]){if(!(r.gainHorizon>0))continue;(by.get(r.position)||by.set(r.position,[]).get(r.position)).push(r);}
  const out=new Map();for(const xs of by.values()){xs.sort((a,b)=>(b.gainHorizon-a.gainHorizon)||((b.gainWeek||0)-(a.gainWeek||0)));xs.forEach((r,i)=>out.set(r.pid,i+1));}return out;}
/** When waivers usually process (UTC weekday + hour of completed claims) and whether this week's run is done. */
function schedule({transactions,since=null}){
  const done=(transactions||[]).filter(t=>t&&t.type==='waiver'&&(t.status==='complete'||t.status==='failed')&&num(t.status_updated));
  const hist=new Map();for(const t of done){const d=new Date(num(t.status_updated)),k=`${d.getUTCDay()}:${d.getUTCHours()}`;hist.set(k,(hist.get(k)||0)+1);}
  const top=[...hist.entries()].sort((a,b)=>b[1]-a[1])[0];
  const usual=top?{weekday:Number(top[0].split(':')[0]),hourUtc:Number(top[0].split(':')[1]),n:top[1]}:null;
  const ran=since!==null&&done.some(t=>num(t.status_updated)>since);
  const last=done.length?Math.max(...done.map(t=>num(t.status_updated))):null;
  return{usual,ranThisWeek:ran,lastRunAt:last};
}
/** Next occurrence of the usual run after `from` (epoch ms), or null. */
function nextRun(usual,from){if(!usual)return null;const d=new Date(from);const t=Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate(),usual.hourUtc);let x=t+((usual.weekday-d.getUTCDay()+7)%7)*864e5;if(x<=from)x+=7*864e5;return x;}
/** Waiver runs since `since`: completed and failed claims grouped by processing time (gap > 1 h = new run), main run first. */
function runs({transactions,since=0}){
  const xs=(transactions||[]).filter(t=>t&&t.type==='waiver'&&num(t.status_updated)>since).sort((a,b)=>num(a.status_updated)-num(b.status_updated));
  const out=[];for(const t of xs){const at=num(t.status_updated),cur=out[out.length-1];if(cur&&at-cur.last<=3600e3){cur.items.push(t);cur.last=at;}else out.push({at,last:at,items:[t]});}
  return out.sort((a,b)=>b.items.length-a.items.length||b.at-a.at);
}
window.FIEBids={VERSION,claims,estimate,ranks,schedule,nextRun,runs,wquantile,policy:pol};
})();
