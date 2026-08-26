/* V9.3 authoritative LeagueContext + preferred-owner runtime integrity. */
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
global.window={};global.CustomEvent=function(){};
const els={};global.document={getElementById:id=>els[id]||null};
window.addEventListener=()=>{};window.dispatchEvent=()=>{};
window.state={
  league:{league_id:'1316165875291668480',total_rosters:16,roster_positions:['QB','RB','WR','WR','TE','FLEX','FLEX','WRRB_FLEX','REC_FLEX','SUPER_FLEX','K','DEF','BN','BN']},
  users:[{user_id:'owner-me',username:'C0nstant1n',display_name:'Constantin'},{user_id:'other',username:'Other'}],
  rosters:[{roster_id:7,owner_id:'other',players:[]},{roster_id:12,owner_id:'owner-me',players:[]}],selectedRoster:null
};
window.FIEPortfolioConfig={config:{sleeper_username:'C0nstant1n'}};
for(const rel of ['app/generated/runtime-contracts.js','app/core/core-services.js'])vm.runInThisContext(fs.readFileSync(path.join(ROOT,rel),'utf8'),{filename:rel});
vm.runInThisContext(fs.readFileSync(path.join(ROOT,'app/league-context.js'),'utf8'),{filename:'app/league-context.js'});
const c=window.FIELeagueContext.current();
if(!c)throw new Error('LeagueContext did not build');
for(const [k,v] of [['hasK',true],['hasDST',true],['hasSuperflex',true],['hasQB',true],['hasTE',true]])if(c[k]!==v)throw new Error(`${k} expected ${v}, got ${c[k]}`);
if(!window.FIELeagueContext.positionAllowed('K')||!window.FIELeagueContext.positionAllowed('DST')||window.FIELeagueContext.positionAllowed('LB'))throw new Error('League-position legality is not centralized/canonical');
const found=window.FIELeagueContext.rosterForUsername();if(!found||found.rosterId!==12)throw new Error(`Preferred owner did not resolve C0nstant1n -> roster 12: ${JSON.stringify(found)}`);
window.FIELeagueContext.selectPreferredRoster();if(window.state.selectedRoster!==12)throw new Error(`Preferred roster was not auto-selected: ${window.state.selectedRoster}`);
console.log(`PASS V9.3 LeagueContext: preferred roster ${found.rosterId}, K=${c.hasK}, DST=${c.hasDST}, SF=${c.hasSuperflex}`);
