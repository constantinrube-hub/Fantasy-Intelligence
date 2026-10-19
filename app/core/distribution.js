/* FIE player/team outcome distributions (UI v10 R1) — UI contract §5.3/§5.7.
 *
 * Mirrors app/decision-engines.js exactly so every displayed probability uses one model:
 *   playerDistribution(p): sd from floor/ceiling as a ±1.28155σ band when available, else
 *     max(1.8, |μ|·0.34); clamped to [1.25, max(3, |μ|·0.8 + 2)]; μ floored at 0.
 *   fixedLineupModel(starters): μ = Σμ, var = Σsd² + Σ_team (Σ 0.12·sd)² for teammates.
 *   Win = P(A > B) for independent normal team totals (the engine estimates the same
 *   quantity by 5,000 seeded draws; the closed form is its exact limit, without noise).
 * Calibration of the spread is research work package WP-V1; until then the win estimate is
 * shown with an amber "estimate" dot. Parity is enforced by research/integrity_v10_core_test.js.
 */
(function(){
'use strict';
const VERSION='10.1.0',Z=1.28155;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function clamp(x,a,b){return Math.max(a,Math.min(b,x));}
function player({mu,low=null,high=null}){
  const m=num(mu)??0,lo=num(low),hi=num(high);
  let sd=(lo!==null&&hi!==null&&hi>lo)?(hi-lo)/(2*Z):Math.max(1.8,Math.abs(m)*.34);
  sd=clamp(sd,1.25,Math.max(3,Math.abs(m)*.8+2));
  return{mu:Math.max(0,m),sd};
}
/** parts: [{mu, sd, team, fixed}] — fixed (locked/actual) parts contribute no variance. */
function team(parts){
  const live=parts.filter(x=>!x.fixed),mu=parts.reduce((s,x)=>s+(num(x.mu)??0),0);
  const variance=live.reduce((s,x)=>s+x.sd*x.sd,0),byTeam={};
  for(const x of live){(byTeam[String(x.team||'FA')]??=[]).push(x);}
  let corr=0;for(const xs of Object.values(byTeam))if(xs.length>1)corr+=Math.pow(xs.reduce((s,x)=>s+x.sd*.12,0),2);
  const anyLive=live.length>0;
  return{mu,sd:anyLive?Math.sqrt(Math.max(1,variance+corr)):0};
}
function erf(x){const s=Math.sign(x),a=Math.abs(x),t=1/(1+.3275911*a);const y=1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-a*a);return s*y;}
function normCdf(z){return .5*(1+erf(z/Math.SQRT2));}
function winProbability(a,b){
  const sd=Math.sqrt((a.sd||0)**2+(b.sd||0)**2);
  if(sd===0)return a.mu>b.mu?1:a.mu<b.mu?0:.5;
  return normCdf((a.mu-b.mu)/sd);
}
window.FIEDistribution={VERSION,player,team,winProbability,normCdf};
})();
