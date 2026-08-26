#!/usr/bin/env node
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),code=fs.readFileSync(path.join(root,'app/value-finder.js'),'utf8');
const document={readyState:'complete',getElementById:()=>null,createElement:()=>({id:'',textContent:'',style:{}}),head:{appendChild:()=>{}},addEventListener:()=>{}};
function P(id,name,pos,adp,proj,vor,role,fit=70){return {name,team:'T'+id,position:pos,rawPosition:pos,sleeperId:String(id),leagueEligible:true,yearsExp:3,currentOpportunity:role,futureOpportunity:role,opportunitySource:'Curated board',role:role>=88?'Starter':'Rotation',path:role>=88?'Already starting':'Meaningful rotation',tier:'starter',depthOrder:role>=88?1:2,marketADP:adp,engineSeasonProjection:proj,projectedVOR:vor,weeklyProjection:12,weeklyFloor:8,weeklyCeiling:18,ageCurveScore:80,tfgModelScore:75,pffScore:74,replacementScore:65,leagueFit:fit,marketEdge:0,seasonScore:75,injuryStatus:null};}
const players=[
 P(1,'Alpha WR','WR',20,260,28,95,82),
 P(2,'Beta RB','RB',28,245,22,94,74),
 P(3,'Gamma WR','WR',48,252,24,93,80),
 P(4,'Delta QB','QB',55,255,30,96,86),
 P(5,'Echo TE','TE',72,210,18,92,88),
 P(6,'Foxtrot WR','WR',95,220,12,88,72),
 P(7,'Replacement WR','WR',120,185,4,84,66),
 P(8,'Replacement RB','RB',115,170,1,82,62),
 {...P(9,'Excluded Star','WR',8,300,40,98,95),leagueEligible:false}
];
const state={league:{league_id:'TEST',name:'Test',season:2026,total_rosters:12},rosters:[],leagueRules:{format:'REDRAFT'},matched:true,projectionStatus:{season:true},draftIntel:{draft:null,picks:[]},selectedRoster:1,valueFinder:{band:'LT100',position:'ALL',confidence:'ALL',snap:'ALL',experience:'ALL',undervaluedOnly:false,availableOnly:true,limit:20,sortKey:'strength',sortDir:-1,top100PlanPick:24,top100NextPick:43,top100ThirdPick:62,top100SortKey:'optimizer',top100SortDir:-1}};
const SECTION_CONFIG={draft:{tabs:[['draft','Draft Board']]}};
const sandbox={console,document,state,PLAYERS:players,SECTION_CONFIG,activeFormatKey:()=> 'REDRAFT',esc:String,$:()=>null,window:null,Number,Math,Set,Map,Object,String,Array,RegExp,Date};
sandbox.window=sandbox;sandbox.FIE={VERSION:'x'};sandbox.render=()=>{};sandbox.openDrawer=()=>{};
sandbox.FIE_DRAFT_V71={draftFullEligiblePool:()=>players.filter(p=>p.leagueEligible),healthScore:()=>90};
sandbox.FIE89={survivalProbability:(adp,next)=>Math.max(1,Math.min(99,Math.round(50+(adp-next)*2)))};
sandbox.FIE_M5={getResearchBundle:()=>({format_strategy:{profiles:{REDRAFT:{draft_weights:{season_projection:.40,vor:.25,current_role:.10,weekly_shape:.10,market_edge:.05,health:.10}}}},draft_integration:{aggregate:[{position:'WR',mean_mae_improvement_vs_baseline:.149,status:'validated_candidate'},{position:'QB',mean_mae_improvement_vs_baseline:.188,status:'validated_candidate'},{position:'RB',mean_mae_improvement_vs_baseline:.065,status:'diagnostic'},{position:'TE',mean_mae_improvement_vs_baseline:.098,status:'validated_candidate'}]}}),getCurrentBundle:()=>({players:[]})};
vm.createContext(sandbox);vm.runInContext(code,sandbox,{filename:'value-finder.js'});
const rows=sandbox.FIE_VALUE_FINDER.top100Rows();
if(rows.some(x=>x.p.name==='Excluded Star'))throw new Error('excluded player leaked into Top-100 optimizer');
if(rows.some(x=>x.adp>=100))throw new Error('Top-100 optimizer contains ADP >=100');
if(!rows.length)throw new Error('Top-100 optimizer returned no candidates');
for(const x of rows){for(const k of ['tierRisk','reachCost','waitCost','pathDelta','optimizerScore'])if(!Number.isFinite(Number(x[k])))throw new Error(`${k} missing for ${x.p.name}`);}
const gamma=rows.find(x=>x.p.name==='Gamma WR');
if(!gamma||!Number.isFinite(gamma.valueCapture))throw new Error('value capture missing');
if(!gamma.replacement)throw new Error('same-position replacement not identified');
if(!['TAKE NOW','TARGET','WAIT','CONSIDER','PASS AT ADP'].includes(gamma.optimizerAction))throw new Error('invalid optimizer action');
if(!rows.context||rows.context.planPick!==24||rows.context.nextPick!==43||rows.context.thirdPick!==62)throw new Error('manual planning picks not respected');
console.log('OK: Top-100 optimizer eligible pool, capture, tier cost, survival, replacement and path proxy');
