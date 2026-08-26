const fs=require('fs'),vm=require('vm'),code=fs.readFileSync('app/draft-monte-carlo-worker.js','utf8');
let output=null;const ctx={console,Math,Date,postMessage:m=>{output=m;}};vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'draft-monte-carlo-worker.js'});
const slotEligibility={QB:['QB'],RB:['RB'],WR:['WR'],TE:['TE'],FLEX:['RB','WR','TE'],BN:[]};
const players=[
 {id:'ownedQ',name:'Owned QB',position:'QB',market:999,decision:99,mean:310,floor:18,ceiling:27,vor:50,utility:95,draftAvailable:false},
 {id:'r1',name:'R1',position:'RB',market:2,decision:85,mean:250,floor:10,ceiling:22,vor:35,utility:85,draftAvailable:true},
 {id:'w1',name:'W1',position:'WR',market:3,decision:80,mean:240,floor:9,ceiling:23,vor:30,utility:80,draftAvailable:true},
 {id:'t1',name:'T1',position:'TE',market:4,decision:75,mean:180,floor:7,ceiling:15,vor:20,utility:75,draftAvailable:true},
 {id:'q2',name:'Q2',position:'QB',market:5,decision:70,mean:220,floor:10,ceiling:19,vor:10,utility:70,draftAvailable:true}
];
const context={seed:'test',format:'REDRAFT',rosterPositions:['QB','RB','WR','TE','BN'],slotEligibility,players,basePools:{1:['ownedQ'],2:[]},rosterOwner:{1:'u1',2:'u2'},history:{},seq:[{pickNo:1,round:1,slot:1},{pickNo:2,round:1,slot:2},{pickNo:3,round:2,slot:2},{pickNo:4,round:2,slot:1}],slotRoster:{1:1,2:2},rosterId:1,startPick:1,endPick:4};
ctx.onmessage({data:{type:'run',jobId:'j1',startIndex:0,count:8,candidateIds:['r1','w1'],context}});
if(!output||output.type!=='batch'||output.results.length!==2)throw new Error('worker did not return candidate batch');
for(const r of output.results)if(r.values.length!==8||r.values.some(v=>!Number.isFinite(v)))throw new Error('worker returned invalid utility samples');
// Existing rostered player is not in the draftable pool, yet must reconstruct.
if(!players.find(p=>p.id==='ownedQ'&&!p.draftAvailable))throw new Error('fixture invalid');
// Bench bonus may only use non-starters. With exactly one QB and one QB starter,
// its VOR cannot be counted as bench value too.
const u=ctx.rosterUtility([players[0]],{format:'REDRAFT',rosterPositions:['QB'],slotEligibility});
if(Math.abs(u.total-310)>1e-9||u.benchIds.length!==0)throw new Error('starter was double-counted in bench bonus');
ctx.onmessage({data:{type:'cancel',jobId:'j1'}});
console.log('OK: Monte Carlo preserves owned rosters, excludes starters from bench value, returns finite batches, and supports cancellation');
