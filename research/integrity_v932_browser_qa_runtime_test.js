/* V9.3.2 browser-QA semantic runtime regression. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const elements={};
function el(id){return elements[id]||(elements[id]={id,value:'',options:[],classList:{s:new Set(),add(x){this.s.add(x)},remove(x){this.s.delete(x)},contains(x){return this.s.has(x)}},dataset:{},appendChild(o){this.options.push(o)}});}
const document={
  getElementById:el,
  documentElement:{dataset:{}},
  createElement(tag){return {tagName:tag.toUpperCase(),value:'',textContent:'',options:[],classList:{add(){},remove(){}}};}
};
const ctx={console,window:null,document,state:{league:{league_id:'L1',season:'2026',total_rosters:12,roster_positions:['QB','RB','WR','TE','FLEX','BN']},rosters:Array.from({length:12},(_,i)=>({roster_id:i+1})),weekly:{season:null,schedule:[]},draftIntel:{loaded:true,draft:{draft_id:'D1'},picks:[{player_id:'P2'}]}},PLAYERS:[],Date,Math,Map,Set,Promise,Number,String,Array,Object,JSON,RegExp,setTimeout,clearTimeout};
ctx.window=ctx;ctx.activeFormatKey=()=> 'REDRAFT';ctx.isLeagueEligible=()=>true;ctx.currentWeek=()=>1;ctx.addEventListener=()=>{};
vm.createContext(ctx);
for(const f of ['app/core/core-services.js','app/core/numeric.js','app/core/projection-service.js','app/core/draft-state-service.js','app/core/surface-router.js','app/core/special-teams-series.js','app/core/draft-value-service.js'])vm.runInContext(fs.readFileSync(f,'utf8'),ctx,{filename:f});
const N=ctx.FIECore.Numeric;
assert.strictEqual(N.finiteOrNull(null),null);assert.strictEqual(N.finiteOrNull(undefined),null);assert.strictEqual(N.finiteOrNull(''),null);assert.strictEqual(N.finiteOrNull('  '),null);assert.strictEqual(N.finiteOrNull(0),0);assert.strictEqual(N.finiteOrNull('0'),0);
assert.strictEqual(N.optionalCap(null),null);assert.strictEqual(N.optionalCap(''),null);assert.strictEqual(N.optionalCap(0),0);assert.strictEqual(N.optionalCap('5'),5);
// Season 0 regression: blank selector can never outrank loaded Sleeper season.
el('seasonSelect').value='';assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);el('seasonSelect').value='0';assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);
ctx.state.league=null;el('seasonSelect').value='';ctx.state.weekly.season=2026;assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);ctx.state.league={league_id:'L1',season:'2026',total_rosters:12,roster_positions:['QB','RB','WR','TE','FLEX','BN']};
// Missing governed/direct projection falls through to Sleeper, never zero.
const p={sleeperId:'P1',name:'One',team:'A',position:'WR',weeklyProjection:null,sleeperWeeklyProjection:18.2,engineSeasonProjection:250,projectedVOR:40,weeklyFloor:null,weeklyCeiling:null};
assert.strictEqual(ctx.FIEProjectionResolver.week(p).value,18.2);assert.strictEqual(ctx.FIEProjectionResolver.week(p).source,'Sleeper weekly');
const r=ctx.FIEProjectionResolver.range(p);assert.ok(r.low>0&&r.high>r.low&&r.estimate===true);
// A real scheduled bye is exactly zero; unknown schedule is not a fake bye.
ctx.state.weekly.schedule=[{season:2026,week:2,game_type:'REG',home_team:'B',away_team:'C'}];
const bye={sleeperId:'P3',name:'Bye',team:'A',position:'WR',weeklyProjection:null,sleeperWeeklyProjection:null,engineSeasonProjection:170};
let bw=ctx.FIEProjectionResolver.week(bye,{week:2,season:2026});assert.strictEqual(bw.value,0);assert.strictEqual(bw.isBye,true);
ctx.state.weekly.schedule=[];bw=ctx.FIEProjectionResolver.week(bye,{week:2,season:2026});assert.ok(bw.value>0);assert.strictEqual(bw.isBye,false);
// Future special-teams schedule absence cannot become a fake zero/bye.
let series=ctx.FIESpecialTeamsSeries.weeks({team:'A',currentWeek:1,season:2026,projection:8,low:null,high:null,replacement:7});assert.strictEqual(series[1].opponent,'—');assert.strictEqual(series[1].projection,8);assert.strictEqual(series[1].bye,false);
ctx.state.weekly.schedule=[{season:2026,week:2,game_type:'REG',home_team:'B',away_team:'C'}];series=ctx.FIESpecialTeamsSeries.weeks({team:'A',currentWeek:1,season:2026,projection:8,replacement:7});assert.strictEqual(series[1].opponent,'BYE');assert.strictEqual(series[1].projection,0);assert.strictEqual(series[1].bye,true);
// Live draft state is single-source and immediately excludes picked IDs.
assert.strictEqual(ctx.FIEDraftStateService.isDrafted('P2'),true);assert.strictEqual(ctx.FIEDraftStateService.isDrafted('P1'),false);assert.ok(ctx.FIEDraftStateService.label().includes('1 picks synced'));
// Matchup panel must be cleaned up as soon as a non-matchup surface activates.
const m=el('matchupSimPanel');m.classList.add('active');ctx.FIESurfaceRouter.activate('waivers');assert.strictEqual(m.classList.contains('active'),false);assert.strictEqual(m.classList.contains('hidden'),true);
// Canonical ranks are market independent and missing-data rows cannot dominate.
ctx.FIECore.ReplacementService.profile=()=>({teams:12,perTeam:1,benchShare:.2});
function player(id,name,proj,vor,adp){return{sleeperId:id,name,team:'A',position:'WR',engineSeasonProjection:proj,sleeperSeasonProjection:proj,projectedVOR:vor,marketADP:adp,weeklyProjection:proj?proj/17:null,weeklyFloor:proj?proj/22:null,weeklyCeiling:proj?proj/13:null,currentOpportunity:60,pffScore:70,leagueEligible:true};}
const a=player('A','Elite',300,100,200),b=player('B','Good',250,70,1),c=player('C','Missing',null,null,2);ctx.PLAYERS=[a,b,c];
let rows=ctx.FIEDraftBaseValueService.compute(ctx.PLAYERS,'REDRAFT');let A=rows.find(x=>x.id==='A'),B=rows.find(x=>x.id==='B'),C=rows.find(x=>x.id==='C');assert.strictEqual(A.overallRank,1);assert.ok(C.overallRank>1);assert.strictEqual(C.lowData,true);
a.marketADP=1;b.marketADP=200;rows=ctx.FIEDraftBaseValueService.compute(ctx.PLAYERS,'REDRAFT');assert.strictEqual(rows.find(x=>x.id==='A').overallRank,1,'market price must not alter FIE player-quality rank');
// Tier 1 must stay useful, not expand to 70+ players in a 12-team test.
ctx.PLAYERS=Array.from({length:80},(_,i)=>player(String(i),`P${i}`,300-i*1.5,100-i*.8,i+1));rows=ctx.FIEDraftBaseValueService.compute(ctx.PLAYERS,'REDRAFT');assert.ok(rows.filter(x=>x.tier===1).length<=24,'Tier 1 exceeded 2x league team count');
console.log('PASS V9.3.2 browser-QA runtime: null semantics, Season 2026, projection fallback, byes, draft state, panel cleanup, canonical ranks and tier sanity');
