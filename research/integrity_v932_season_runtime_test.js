/* Execute the actual index.html activeSeason/currentWeek code to block Season=0 regressions. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const src=fs.readFileSync('index.html','utf8');
function extract(a,b){const i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw new Error(`cannot extract ${a}`);return src.slice(i,j);}
const elements={seasonSelect:{value:'',options:[]},weekSelect:{value:'',options:[]}};
const ctx={console,state:{league:{season:'2026'},weekly:{season:null,week:null}},document:{getElementById:id=>elements[id]||null},Date,Number,String,Math};ctx.window=ctx;ctx.$=id=>elements[id]||null;vm.createContext(ctx);
vm.runInContext(extract('function currentWeek()','function gameForTeam'),ctx);vm.runInContext(extract('function activeSeason()','function priorSeason()'),ctx);
assert.strictEqual(ctx.activeSeason(),2026,'blank season selector must not coerce to Season 0');
elements.seasonSelect.value='0';assert.strictEqual(ctx.activeSeason(),2026,'selector value 0 must not override loaded Sleeper season');
ctx.state.league=null;elements.seasonSelect.value='';ctx.state.weekly.season=2026;assert.strictEqual(ctx.activeSeason(),2026,'weekly state 2026 must survive blank selector');
elements.weekSelect.value='';ctx.state.weekly.week=1;assert.strictEqual(ctx.currentWeek(),1);elements.weekSelect.value='0';assert.strictEqual(ctx.currentWeek(),1,'Week 0 must not be selected');
console.log('PASS V9.3.2 actual index season runtime: blank/0 selector cannot turn 2026 into Season 0');
