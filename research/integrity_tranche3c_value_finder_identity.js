/* Permanent Tranche 3C Value Finder governed current-identity join. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const players=[
 {name:'Alpha WR',team:'AAA',position:'WR',sleeperId:'1',leagueEligible:true,futureOpportunity:20,seasonScore:50,marketADP:100},
 {name:'Beta WR',team:'BBB',position:'WR',sleeperId:'2',leagueEligible:true,futureOpportunity:30,seasonScore:50,marketADP:110},
];
const document={readyState:'complete',getElementById:()=>null,createElement:()=>({}),head:{appendChild(){}},addEventListener(){}};
const state={league:{league_id:'fixture'},leagueRules:{allowedExperience:[],experienceCaps:{}},draftIntel:{picks:[]},selectedRoster:1,rosters:[]};
const ctx={console,window:null,document,state,PLAYERS:players,SECTION_CONFIG:{draft:{tabs:[['draft','Draft Board']]}},Date,Math,Map,Set,WeakMap,Promise,Number,Object,String,Array,RegExp,performance:{now:()=>0}};
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.render=()=>{};ctx.FIE={VERSION:'x'};
ctx.FIE_DRAFT_V71={draftFullEligiblePool:()=>players,healthScore:()=>90};
ctx.FIE_M5={
 getResearchBundle:()=>({format_strategy:{profiles:{REDRAFT:{draft_weights:{future_role:1}}}},draft_integration:{aggregate:[]}}),
 getCurrentBundle:()=>({players:[
   {sleeper_id:'1',young_role_probability:.9},
   {full_name:'Beta WR',young_role_probability:.99}
 ]})
};
ctx.activeFormatKey=()=> 'REDRAFT';
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/generated/runtime-contracts.js','utf8'),ctx,{filename:'runtime-contracts.js'});
vm.runInContext(fs.readFileSync('app/core/core-services.js','utf8'),ctx,{filename:'core-services.js'});
vm.runInContext(fs.readFileSync('app/value-finder.js','utf8'),ctx,{filename:'value-finder.js'});
const alpha=ctx.FIE_VALUE_FINDER.policyScore(players[0]);
const beta=ctx.FIE_VALUE_FINDER.policyScore(players[1]);
assert.strictEqual(alpha.score,90,'Sleeper-ID governed row must contribute');
assert.strictEqual(beta.score,30,'display-name-only current row must not contribute');
console.log('PASS Tranche 3C Value Finder governed identity join without display-name fallback');
