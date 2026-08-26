const fs=require('fs'),vm=require('vm');
const P=[
 {sleeperId:'q1',name:'QB1',position:'QB',marketADP:20,projectedVOR:35,weeklyProjection:20,weeklyFloor:15,weeklyCeiling:27,engineSeasonProjection:330,targetScore:55},
 {sleeperId:'q2',name:'QB2',position:'QB',marketADP:60,projectedVOR:10,weeklyProjection:17,weeklyFloor:12,weeklyCeiling:23,engineSeasonProjection:285,targetScore:50},
 {sleeperId:'r1',name:'RB1',position:'RB',marketADP:15,projectedVOR:45,weeklyProjection:18,weeklyFloor:10,weeklyCeiling:28,engineSeasonProjection:300,targetScore:60},
 {sleeperId:'r2',name:'RB2',position:'RB',marketADP:45,projectedVOR:12,weeklyProjection:13,weeklyFloor:7,weeklyCeiling:21,engineSeasonProjection:220,targetScore:50},
 {sleeperId:'w1',name:'WR1',position:'WR',marketADP:25,projectedVOR:32,weeklyProjection:16,weeklyFloor:9,weeklyCeiling:25,engineSeasonProjection:270,targetScore:58},
 {sleeperId:'t1',name:'TE1',position:'TE',marketADP:80,projectedVOR:8,weeklyProjection:11,weeklyFloor:7,weeklyCeiling:16,engineSeasonProjection:185,targetScore:50}
];
const state={league:{league_id:'1',roster_positions:['QB','RB','RB','WR','WR','TE','FLEX','BN'],settings:{},total_rosters:2},draftIntel:{picks:[],draft:{type:'snake',settings:{teams:2,rounds:4},slot_to_roster_id:{1:1,2:2}}},rosters:[{roster_id:1,players:['q2','r2']},{roster_id:2,players:[]}],selectedRoster:1,modelHealth:{recomputeCount:1},projectedReplacementLevels:{QB:{cutoff:2},RB:{cutoff:3},WR:{cutoff:3},TE:{cutoff:2}}};
const ctx={console,Date,Math,JSON,state,PLAYERS:P,addEventListener:()=>{},document:{getElementById:()=>null},FIELeagueProfileResolver:{resolveFor:()=>({format:'REDRAFT'})},FIEDraftSequence:{sequence:()=>[{pickNo:1,round:1,slot:1},{pickNo:2,round:1,slot:2},{pickNo:3,round:2,slot:2},{pickNo:4,round:2,slot:1}]},survivalProbability:()=>50,FIECurrentFeatures:{summary:()=>[],signalLineage:()=>[]},FIE_M5:{getCurrentBundle:()=>null}};ctx.window=ctx;
vm.createContext(ctx);
for(const f of ['app/generated/runtime-contracts.js','app/generated/model-config.js','app/core/core-services.js'])vm.runInContext(fs.readFileSync(f,'utf8'),ctx,{filename:f});
ctx.FIE_DRAFT_V71={draftFullEligiblePool:()=>P,draftRosterPool:(rid)=>P.filter(p=>(state.rosters.find(r=>r.roster_id===rid)?.players||[]).includes(p.sleeperId)),archiveManagerModel:()=>({}),managerPressure:()=>({adj:0,n:0}),earlyWeeksFor:p=>({mean:p.weeklyProjection,floor:p.weeklyFloor,ceiling:p.weeklyCeiling}),healthScore:()=>100};
vm.runInContext(fs.readFileSync('app/decision-model-v9.js','utf8'),ctx,{filename:'decision-model-v9.js'});
if(ctx.FIEModelV9.buildDraftValueRows(1)!==null)throw new Error('unpromoted V9 candidate leaked into production draft rows');
const rows=ctx.FIEModelV9.buildDiagnosticRows(1);if(!rows.length)throw new Error('no V9 diagnostic rows');
if(rows.some(r=>!['league','roster','timing'].every(k=>k in r.components)))throw new Error('three-part architecture missing');
const q1=rows.find(r=>r.p.sleeperId==='q1'),r1=rows.find(r=>r.p.sleeperId==='r1');if(!(r1.leagueUtility>q1.leagueUtility))throw new Error('redraft league utility not VOR-led');
const rankBefore=new Map(rows.map(r=>[r.p.sleeperId,r.leagueRank]));state.rosters[0].players=['q1','r1','w1'];ctx.FIEModelV9.invalidate();const rows2=ctx.FIEModelV9.buildDiagnosticRows(1);for(const r of rows2)if(rankBefore.get(r.p.sleeperId)!==r.leagueRank)throw new Error('league rank changed with roster construction');
// replacement service must scale league-wide rather than use personal demand.
const cut=ctx.FIECore.ReplacementService.cutoff('QB',{league:{roster_positions:['QB','BN'],total_rosters:18},players:Array.from({length:30},(_,i)=>({sleeperId:`q${i}`,position:'QB',engineSeasonProjection:300-i})),state:{}});if(cut<18)throw new Error(`league-wide replacement cutoff too shallow: ${cut}`);
console.log('OK: V9 is fail-closed, diagnostic architecture is stable, exact roster marginal is available, and replacement is league-wide');
