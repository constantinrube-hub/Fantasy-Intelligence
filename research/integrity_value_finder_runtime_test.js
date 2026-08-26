#!/usr/bin/env node
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),code=fs.readFileSync(path.join(root,'app/value-finder.js'),'utf8');
const document={readyState:'complete',getElementById:()=>null,createElement:()=>({id:'',textContent:'',style:{}}),head:{appendChild:()=>{}},addEventListener:()=>{}};
const players=[
 {name:'Alpha WR',team:'AAA',position:'WR',rawPosition:'WR',sleeperId:'1',leagueEligible:true,yearsExp:0,currentOpportunity:92,futureOpportunity:93,opportunitySource:'Curated Y1/Y2 board',role:'Starter',path:'Already starting',tier:'starter',depthOrder:1,marketADP:225,engineSeasonProjection:180,projectedVOR:20,weeklyProjection:12,weeklyFloor:7,weeklyCeiling:20,ageCurveScore:90,tfgModelScore:80,pffScore:75,replacementScore:65,leagueFit:80,marketEdge:20,seasonScore:80,injuryStatus:null},
 {name:'Beta WR',team:'BBB',position:'WR',rawPosition:'WR',sleeperId:'2',leagueEligible:true,yearsExp:4,currentOpportunity:52,futureOpportunity:55,opportunitySource:'Sleeper auto depth estimate',role:'#3 depth',path:'Needs competition win',tier:'backup',depthOrder:3,marketADP:205,engineSeasonProjection:140,projectedVOR:5,weeklyProjection:7,weeklyFloor:3,weeklyCeiling:12,ageCurveScore:75,tfgModelScore:55,pffScore:60,replacementScore:50,leagueFit:55,marketEdge:-5,seasonScore:55,injuryStatus:null},
 {name:'Gamma WR',team:'CCC',position:'WR',rawPosition:'WR',sleeperId:'3',leagueEligible:true,yearsExp:1,currentOpportunity:85,futureOpportunity:90,opportunitySource:'Curated Y1/Y2 board',role:'WR2',path:'Competing for regular snaps',tier:'rotation',depthOrder:2,marketADP:150,engineSeasonProjection:170,projectedVOR:15,weeklyProjection:10,weeklyFloor:6,weeklyCeiling:18,ageCurveScore:88,tfgModelScore:78,pffScore:70,replacementScore:60,leagueFit:75,marketEdge:10,seasonScore:75,injuryStatus:null},
 {name:'Excluded Vet',team:'DDD',position:'WR',rawPosition:'WR',sleeperId:'4',leagueEligible:false,yearsExp:6,currentOpportunity:95,futureOpportunity:80,opportunitySource:'Sleeper auto depth estimate',role:'Starter',path:'Starting',tier:'starter',depthOrder:1,marketADP:50,engineSeasonProjection:220,projectedVOR:30,weeklyProjection:14,weeklyFloor:9,weeklyCeiling:22,ageCurveScore:65,tfgModelScore:85,pffScore:80,replacementScore:70,leagueFit:80,marketEdge:20,seasonScore:90,injuryStatus:null}
];
const state={league:{league_id:'TEST',name:'Test',season:2026},leagueRules:{format:'DYNASTY'},matched:true,projectionStatus:{season:true},draftIntel:{draft:null,picks:[]},selectedRoster:1};
const SECTION_CONFIG={draft:{tabs:[['draft','Draft Board']]}};
const sandbox={console,document,state,PLAYERS:players,SECTION_CONFIG,activeFormatKey:()=> 'DYNASTY',esc:String,$:()=>null,window:null,Number,Math,Set,Map,Object,String,Array,RegExp,Date};
sandbox.window=sandbox;sandbox.FIE={VERSION:'x'};sandbox.render=()=>{};
sandbox.FIE_DRAFT_V71={draftFullEligiblePool:()=>players.filter(p=>p.leagueEligible),healthScore:()=>90};
sandbox.FIE_M5={getResearchBundle:()=>({format_strategy:{profiles:{DYNASTY:{draft_weights:{season_projection:.32,vor:.13,future_role:.25,age_curve:.12,talent:.08,market_edge:.10}}}},draft_integration:{aggregate:[{position:'WR',mean_mae_improvement_vs_baseline:.149,status:'validated_candidate'}]}}),getCurrentBundle:()=>({players:[{sleeper_id:'1',young_role_probability:.92},{sleeper_id:'3',young_role_probability:.88}]})};
vm.createContext(sandbox);vm.runInContext(code,sandbox,{filename:'value-finder.js'});
const rows=sandbox.FIE_VALUE_FINDER.buildRows();
if(rows.some(x=>x.p.name==='Excluded Vet'))throw new Error('hard-excluded player leaked into eligible ranking pool');
const alpha=rows.find(x=>x.p.name==='Alpha WR'),beta=rows.find(x=>x.p.name==='Beta WR');
if(!(alpha.snap.score>beta.snap.score))throw new Error('snap-path score does not reward clear starting path');
state.valueFinder.band='200_PLUS';state.valueFinder.snap='CLEAR';state.valueFinder.undervaluedOnly=false;state.valueFinder.availableOnly=true;
const deep=sandbox.FIE_VALUE_FINDER.filteredRows();
if(deep.some(x=>x.p.name==='Beta WR'))throw new Error('weak role leaked into clear ADP 200+ screen');
if(!deep.some(x=>x.p.name==='Alpha WR'))throw new Error('clear ADP 200+ role was incorrectly filtered');
if(!SECTION_CONFIG.draft.tabs.some(x=>x[0]==='valuefinder'))throw new Error('Draft navigation route not installed');
console.log('OK: Value Finder runtime eligibility, same-position market ranking and role-first 200+ filter');
